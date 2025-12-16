// Package authz implements the Envoy ext_authz Authorization service.
//
// FAIL SECURE DESIGN:
//   - All errors result in request denial
//   - Only explicitly approved actions proceed
//   - Circuit breaker prevents cascade failures
//
// Author: ASCEND Platform Engineering
package authz

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	corev3 "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	authv3 "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"
	typev3 "github.com/envoyproxy/go-control-plane/envoy/type/v3"
	"google.golang.org/genproto/googleapis/rpc/status"
	"google.golang.org/grpc/codes"

	"github.com/owkai/ascend-envoy-authz/internal/ascend"
	"github.com/owkai/ascend-envoy-authz/internal/config"
	"github.com/owkai/ascend-envoy-authz/internal/logger"
	"github.com/owkai/ascend-envoy-authz/internal/mapper"
)

// Handler implements the Envoy ext_authz Authorization service.
type Handler struct {
	authv3.UnimplementedAuthorizationServer

	client   *ascend.Client
	config   *config.Config
	logger   *logger.Logger

	// Decision cache (approved only)
	cache   map[string]*cacheEntry
	cacheMu sync.RWMutex
}

type cacheEntry struct {
	decision  *ascend.Decision
	expiresAt time.Time
}

// NewHandler creates a new authorization handler.
func NewHandler(cfg *config.Config, client *ascend.Client) *Handler {
	h := &Handler{
		client: client,
		config: cfg,
		logger: logger.Default().WithField("component", "authz_handler"),
		cache:  make(map[string]*cacheEntry),
	}

	// Start cache cleanup goroutine
	go h.cleanupCache()

	h.logger.Info("Authorization handler initialized",
		"fail_open", cfg.FailOpen,
		"cache_ttl", cfg.CacheTTL.String(),
		"agent_id_header", cfg.AgentIDHeader,
	)

	return h
}

// Check implements the Authorization.Check RPC.
// This is the main entry point for Envoy external authorization.
func (h *Handler) Check(ctx context.Context, req *authv3.CheckRequest) (*authv3.CheckResponse, error) {
	startTime := time.Now()

	// Extract HTTP request attributes
	httpReq := req.GetAttributes().GetRequest().GetHttp()
	if httpReq == nil {
		h.logger.Error("Invalid request: missing HTTP attributes")
		return h.denyResponse("Invalid request: missing HTTP attributes", codes.InvalidArgument, nil), nil
	}

	path := httpReq.GetPath()
	method := httpReq.GetMethod()

	// Remove query string for path matching
	if idx := strings.Index(path, "?"); idx != -1 {
		path = path[:idx]
	}

	// Check path exclusions
	if mapper.IsPathExcluded(path, h.config.ExcludedPaths) {
		h.logger.Debug("Path excluded from governance", "path", path)
		return h.allowResponse(nil), nil
	}

	// Extract agent ID from headers
	agentID := h.extractAgentID(httpReq.GetHeaders())
	if agentID == "" {
		if h.config.RequireAgentID {
			h.logger.Warn("Missing agent ID header",
				"header", h.config.AgentIDHeader,
				"path", path,
			)
			return h.denyResponse(
				fmt.Sprintf("Missing required header: %s", h.config.AgentIDHeader),
				codes.Unauthenticated,
				nil,
			), nil
		}
		// Not required, skip governance
		h.logger.Debug("No agent ID, skipping governance", "path", path)
		return h.allowResponse(nil), nil
	}

	// Map request to ASCEND action
	action := mapper.MapCheckRequest(req, agentID, h.config.Environment, h.config.DataSensitivity)

	// Check cache first
	cacheKey := mapper.GenerateCacheKey(agentID, method, path)
	if h.config.CacheTTL > 0 {
		if cached := h.getFromCache(cacheKey); cached != nil {
			h.logger.Debug("Cache hit",
				"agent_id", agentID,
				"cache_key", cacheKey,
			)
			return h.buildResponse(cached), nil
		}
	}

	// Call ASCEND API
	decision, err := h.client.EvaluateAction(ctx, action)
	if err != nil {
		h.logger.Error("ASCEND API error",
			"error", err,
			"agent_id", agentID,
			"path", path,
		)

		// FAIL SECURE: Deny on error unless fail_open is configured
		if h.config.FailOpen {
			h.logger.Warn("Fail open enabled, allowing request despite error")
			return h.allowResponse(map[string]string{
				"x-ascend-status": "error-allowed",
				"x-ascend-error":  err.Error(),
			}), nil
		}

		return h.denyResponse(
			"Governance service unavailable",
			codes.Unavailable,
			map[string]string{"x-ascend-error": "service_unavailable"},
		), nil
	}

	// Cache approved decisions only
	if decision.IsApproved() && h.config.CacheTTL > 0 {
		h.setCache(cacheKey, decision)
	}

	// Log decision
	latencyMs := float64(time.Since(startTime).Microseconds()) / 1000
	if h.config.LogDecisions {
		h.logger.Info("Authorization decision",
			"agent_id", agentID,
			"action_type", action.ActionType,
			"status", decision.Status,
			"risk_score", decision.RiskScore,
			"risk_level", decision.RiskLevel,
			"action_id", decision.ActionID,
			"latency_ms", latencyMs,
			"cached", false,
		)
	}

	return h.buildResponse(decision), nil
}

// extractAgentID extracts the agent ID from request headers.
func (h *Handler) extractAgentID(headers map[string]string) string {
	// Try exact match first
	if agentID, ok := headers[h.config.AgentIDHeader]; ok {
		return agentID
	}

	// Try case-insensitive match
	headerLower := strings.ToLower(h.config.AgentIDHeader)
	for k, v := range headers {
		if strings.ToLower(k) == headerLower {
			return v
		}
	}

	// Use default if configured
	return h.config.DefaultAgentID
}

// buildResponse converts an ASCEND decision to a CheckResponse.
func (h *Handler) buildResponse(decision *ascend.Decision) *authv3.CheckResponse {
	switch decision.Status {
	case ascend.StatusApproved:
		return h.allowResponse(map[string]string{
			"x-ascend-status":     "approved",
			"x-ascend-action-id":  fmt.Sprintf("%d", decision.ActionID),
			"x-ascend-risk-score": fmt.Sprintf("%.1f", decision.RiskScore),
			"x-ascend-risk-level": decision.RiskLevel,
		})

	case ascend.StatusPending:
		if h.config.BlockOnPending {
			return h.denyResponse(
				"Action requires human approval",
				codes.PermissionDenied,
				map[string]string{
					"x-ascend-status":     "pending_approval",
					"x-ascend-action-id":  fmt.Sprintf("%d", decision.ActionID),
					"x-ascend-risk-score": fmt.Sprintf("%.1f", decision.RiskScore),
				},
			)
		}
		// Allow but flag as pending
		return h.allowResponse(map[string]string{
			"x-ascend-status":    "pending_approval",
			"x-ascend-action-id": fmt.Sprintf("%d", decision.ActionID),
		})

	default: // denied or unknown
		message := "Action denied by governance policy"
		if decision.DenialReason != "" {
			message = decision.DenialReason
		}
		return h.denyResponse(
			message,
			codes.PermissionDenied,
			map[string]string{
				"x-ascend-status":     "denied",
				"x-ascend-action-id":  fmt.Sprintf("%d", decision.ActionID),
				"x-ascend-risk-score": fmt.Sprintf("%.1f", decision.RiskScore),
			},
		)
	}
}

// allowResponse creates an OkHttpResponse (allow the request).
func (h *Handler) allowResponse(headers map[string]string) *authv3.CheckResponse {
	var headersList []*corev3.HeaderValueOption
	for k, v := range headers {
		headersList = append(headersList, &corev3.HeaderValueOption{
			Header: &corev3.HeaderValue{Key: k, Value: v},
		})
	}

	return &authv3.CheckResponse{
		Status: &status.Status{Code: int32(codes.OK)},
		HttpResponse: &authv3.CheckResponse_OkResponse{
			OkResponse: &authv3.OkHttpResponse{
				Headers: headersList,
			},
		},
	}
}

// denyResponse creates a DeniedHttpResponse (block the request).
func (h *Handler) denyResponse(message string, code codes.Code, headers map[string]string) *authv3.CheckResponse {
	var headersList []*corev3.HeaderValueOption
	for k, v := range headers {
		headersList = append(headersList, &corev3.HeaderValueOption{
			Header: &corev3.HeaderValue{Key: k, Value: v},
		})
	}

	// Determine HTTP status code
	httpStatus := typev3.StatusCode_Forbidden
	if code == codes.Unavailable {
		httpStatus = typev3.StatusCode_ServiceUnavailable
	} else if code == codes.Unauthenticated {
		httpStatus = typev3.StatusCode_Unauthorized
	}

	return &authv3.CheckResponse{
		Status: &status.Status{
			Code:    int32(code),
			Message: message,
		},
		HttpResponse: &authv3.CheckResponse_DeniedResponse{
			DeniedResponse: &authv3.DeniedHttpResponse{
				Status: &typev3.HttpStatus{
					Code: httpStatus,
				},
				Headers: headersList,
				Body:    fmt.Sprintf(`{"error":"%s","message":"%s"}`, code.String(), message),
			},
		},
	}
}

// Cache methods

func (h *Handler) getFromCache(key string) *ascend.Decision {
	h.cacheMu.RLock()
	defer h.cacheMu.RUnlock()

	entry, ok := h.cache[key]
	if !ok || time.Now().After(entry.expiresAt) {
		return nil
	}
	return entry.decision
}

func (h *Handler) setCache(key string, decision *ascend.Decision) {
	h.cacheMu.Lock()
	defer h.cacheMu.Unlock()

	h.cache[key] = &cacheEntry{
		decision:  decision,
		expiresAt: time.Now().Add(h.config.CacheTTL),
	}
}

func (h *Handler) cleanupCache() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		h.cacheMu.Lock()
		now := time.Now()
		for k, v := range h.cache {
			if now.After(v.expiresAt) {
				delete(h.cache, k)
			}
		}
		h.cacheMu.Unlock()
	}
}
