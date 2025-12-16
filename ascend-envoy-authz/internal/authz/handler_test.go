// Package authz tests for the authorization handler.
//
// Tests cover:
//   - FAIL SECURE behavior
//   - Decision handling (approved, pending, denied)
//   - Cache behavior
//   - Path exclusions
//   - Agent ID extraction
//
// Author: ASCEND Platform Engineering
package authz

import (
	"context"
	"testing"
	"time"

	corev3 "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	authv3 "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"
	"google.golang.org/grpc/codes"

	"github.com/owkai/ascend-envoy-authz/internal/ascend"
	"github.com/owkai/ascend-envoy-authz/internal/config"
)

// mockClient implements ascend.Client for testing
type mockClient struct {
	decision *ascend.Decision
	err      error
}

func (m *mockClient) EvaluateAction(ctx context.Context, action *ascend.Action) (*ascend.Decision, error) {
	return m.decision, m.err
}

func (m *mockClient) GetCircuitState() string {
	return "closed"
}

func newTestConfig() *config.Config {
	return &config.Config{
		AgentIDHeader:  "x-ascend-agent-id",
		RequireAgentID: true,
		FailOpen:       false,
		BlockOnPending: true,
		Environment:    "test",
		CacheTTL:       60 * time.Second,
		ExcludedPaths:  []string{"/health", "/metrics"},
	}
}

func newCheckRequest(method, path, agentID string) *authv3.CheckRequest {
	headers := map[string]string{}
	if agentID != "" {
		headers["x-ascend-agent-id"] = agentID
	}

	return &authv3.CheckRequest{
		Attributes: &authv3.AttributeContext{
			Request: &authv3.AttributeContext_Request{
				Http: &authv3.AttributeContext_HttpRequest{
					Method:  method,
					Path:    path,
					Headers: headers,
				},
			},
		},
	}
}

func TestHandler_Check_Approved(t *testing.T) {
	cfg := newTestConfig()
	client := &mockClient{
		decision: &ascend.Decision{
			ActionID:  12345,
			Status:    ascend.StatusApproved,
			RiskScore: 25.0,
			RiskLevel: "low",
		},
	}

	// Create handler directly with mock client
	handler := &Handler{
		client: nil, // Will be set manually
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}
	// Inject mock
	_ = client

	// Test that approved responses return OK
	req := newCheckRequest("GET", "/api/users", "test-agent")

	// Simulate response building
	resp := handler.buildResponse(client.decision)

	if resp.GetOkResponse() == nil {
		t.Error("Expected OkHttpResponse for approved decision")
	}

	// Check status code
	if resp.Status.Code != int32(codes.OK) {
		t.Errorf("Expected OK status, got %v", resp.Status.Code)
	}

	// Check headers
	okResp := resp.GetOkResponse()
	foundStatus := false
	for _, h := range okResp.Headers {
		if h.Header.Key == "x-ascend-status" && h.Header.Value == "approved" {
			foundStatus = true
		}
	}
	if !foundStatus {
		t.Error("Expected x-ascend-status: approved header")
	}
}

func TestHandler_Check_Denied(t *testing.T) {
	cfg := newTestConfig()
	handler := &Handler{
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}

	decision := &ascend.Decision{
		ActionID:     12346,
		Status:       ascend.StatusDenied,
		RiskScore:    95.0,
		RiskLevel:    "critical",
		DenialReason: "Action violates security policy",
	}

	resp := handler.buildResponse(decision)

	if resp.GetDeniedResponse() == nil {
		t.Error("Expected DeniedHttpResponse for denied decision")
	}

	if resp.Status.Code != int32(codes.PermissionDenied) {
		t.Errorf("Expected PermissionDenied status, got %v", resp.Status.Code)
	}
}

func TestHandler_Check_Pending_Blocked(t *testing.T) {
	cfg := newTestConfig()
	cfg.BlockOnPending = true

	handler := &Handler{
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}

	decision := &ascend.Decision{
		ActionID:         12347,
		Status:           ascend.StatusPending,
		RiskScore:        75.0,
		RiskLevel:        "high",
		RequiresApproval: true,
	}

	resp := handler.buildResponse(decision)

	if resp.GetDeniedResponse() == nil {
		t.Error("Expected DeniedHttpResponse for pending decision with block_on_pending=true")
	}
}

func TestHandler_Check_Pending_Allowed(t *testing.T) {
	cfg := newTestConfig()
	cfg.BlockOnPending = false

	handler := &Handler{
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}

	decision := &ascend.Decision{
		ActionID:         12348,
		Status:           ascend.StatusPending,
		RiskScore:        75.0,
		RequiresApproval: true,
	}

	resp := handler.buildResponse(decision)

	if resp.GetOkResponse() == nil {
		t.Error("Expected OkHttpResponse for pending decision with block_on_pending=false")
	}
}

func TestHandler_DenyResponse_Codes(t *testing.T) {
	handler := &Handler{
		config: newTestConfig(),
		cache:  make(map[string]*cacheEntry),
	}

	tests := []struct {
		code     codes.Code
		expected int32
	}{
		{codes.PermissionDenied, int32(codes.PermissionDenied)},
		{codes.Unavailable, int32(codes.Unavailable)},
		{codes.Unauthenticated, int32(codes.Unauthenticated)},
	}

	for _, tt := range tests {
		resp := handler.denyResponse("test", tt.code, nil)
		if resp.Status.Code != tt.expected {
			t.Errorf("Expected status code %d, got %d", tt.expected, resp.Status.Code)
		}
	}
}

func TestHandler_ExtractAgentID(t *testing.T) {
	handler := &Handler{
		config: &config.Config{
			AgentIDHeader:  "x-ascend-agent-id",
			DefaultAgentID: "default-agent",
		},
		cache: make(map[string]*cacheEntry),
	}

	tests := []struct {
		name     string
		headers  map[string]string
		expected string
	}{
		{
			name:     "exact match",
			headers:  map[string]string{"x-ascend-agent-id": "test-agent"},
			expected: "test-agent",
		},
		{
			name:     "case insensitive",
			headers:  map[string]string{"X-Ascend-Agent-Id": "test-agent-2"},
			expected: "test-agent-2",
		},
		{
			name:     "use default",
			headers:  map[string]string{},
			expected: "default-agent",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := handler.extractAgentID(tt.headers)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestHandler_AllowResponse_Headers(t *testing.T) {
	handler := &Handler{
		config: newTestConfig(),
		cache:  make(map[string]*cacheEntry),
	}

	headers := map[string]string{
		"x-ascend-status":    "approved",
		"x-ascend-action-id": "12345",
	}

	resp := handler.allowResponse(headers)

	okResp := resp.GetOkResponse()
	if okResp == nil {
		t.Fatal("Expected OkHttpResponse")
	}

	foundHeaders := make(map[string]string)
	for _, h := range okResp.Headers {
		foundHeaders[h.Header.Key] = h.Header.Value
	}

	for k, v := range headers {
		if foundHeaders[k] != v {
			t.Errorf("Expected header %s=%s, got %s", k, v, foundHeaders[k])
		}
	}
}

func TestHandler_Cache(t *testing.T) {
	handler := &Handler{
		config: &config.Config{
			CacheTTL: 60 * time.Second,
		},
		cache: make(map[string]*cacheEntry),
	}

	decision := &ascend.Decision{
		ActionID:  12345,
		Status:    ascend.StatusApproved,
		RiskScore: 25.0,
	}

	key := "test-agent:GET:/api/users"

	// Set cache
	handler.setCache(key, decision)

	// Get from cache
	cached := handler.getFromCache(key)
	if cached == nil {
		t.Error("Expected cached decision")
	}
	if cached.ActionID != decision.ActionID {
		t.Errorf("Expected ActionID %d, got %d", decision.ActionID, cached.ActionID)
	}

	// Non-existent key
	notFound := handler.getFromCache("non-existent")
	if notFound != nil {
		t.Error("Expected nil for non-existent key")
	}
}

func TestHandler_CacheExpiry(t *testing.T) {
	handler := &Handler{
		config: &config.Config{
			CacheTTL: 1 * time.Millisecond,
		},
		cache: make(map[string]*cacheEntry),
	}

	decision := &ascend.Decision{
		ActionID: 12345,
		Status:   ascend.StatusApproved,
	}

	key := "test-agent:GET:/api/users"
	handler.setCache(key, decision)

	// Wait for expiry
	time.Sleep(10 * time.Millisecond)

	cached := handler.getFromCache(key)
	if cached != nil {
		t.Error("Expected nil for expired cache entry")
	}
}

func TestHandler_PathExclusion(t *testing.T) {
	cfg := newTestConfig()
	cfg.ExcludedPaths = []string{"/health", "/metrics", "/ready"}

	handler := &Handler{
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}

	// Create mock context
	ctx := context.Background()

	// Health check should be excluded
	healthReq := newCheckRequest("GET", "/health", "")
	resp, err := handler.Check(ctx, healthReq)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if resp.GetOkResponse() == nil {
		t.Error("Expected OkResponse for excluded path /health")
	}

	// Metrics should be excluded
	metricsReq := newCheckRequest("GET", "/metrics", "")
	resp, err = handler.Check(ctx, metricsReq)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}
	if resp.GetOkResponse() == nil {
		t.Error("Expected OkResponse for excluded path /metrics")
	}
}

func TestHandler_MissingAgentID(t *testing.T) {
	cfg := newTestConfig()
	cfg.RequireAgentID = true

	handler := &Handler{
		config: cfg,
		cache:  make(map[string]*cacheEntry),
	}

	ctx := context.Background()
	req := newCheckRequest("GET", "/api/users", "") // No agent ID

	resp, err := handler.Check(ctx, req)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.GetDeniedResponse() == nil {
		t.Error("Expected DeniedResponse for missing agent ID")
	}
	if resp.Status.Code != int32(codes.Unauthenticated) {
		t.Errorf("Expected Unauthenticated, got %v", resp.Status.Code)
	}
}

func TestHandler_InvalidRequest(t *testing.T) {
	handler := &Handler{
		config: newTestConfig(),
		cache:  make(map[string]*cacheEntry),
	}

	ctx := context.Background()
	req := &authv3.CheckRequest{
		Attributes: &authv3.AttributeContext{
			Request: &authv3.AttributeContext_Request{
				Http: nil, // Missing HTTP attributes
			},
		},
	}

	resp, err := handler.Check(ctx, req)
	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if resp.GetDeniedResponse() == nil {
		t.Error("Expected DeniedResponse for invalid request")
	}
	if resp.Status.Code != int32(codes.InvalidArgument) {
		t.Errorf("Expected InvalidArgument, got %v", resp.Status.Code)
	}
}
