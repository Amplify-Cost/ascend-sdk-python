// Package ascend provides the ASCEND Platform API client.
//
// Features:
//   - HTTP client with connection pooling
//   - Retry with exponential backoff
//   - Circuit breaker pattern
//   - Timeout handling
//
// FAIL SECURE: All errors return nil + error
//
// Author: ASCEND Platform Engineering
package ascend

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/owkai/ascend-envoy-authz/internal/logger"
)

// ClientConfig holds configuration for the ASCEND client.
type ClientConfig struct {
	BaseURL        string
	APIKey         string
	Timeout        time.Duration
	RetryCount     int
	RetryDelay     time.Duration
	CircuitBreaker CircuitBreakerConfig
}

// CircuitBreakerConfig holds circuit breaker configuration.
type CircuitBreakerConfig struct {
	Enabled      bool
	Threshold    int
	ResetTimeout time.Duration
}

// Client is the ASCEND API client.
type Client struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
	retryCount int
	retryDelay time.Duration
	cb         *circuitBreaker
	logger     *logger.Logger
}

// NewClient creates a new ASCEND API client.
func NewClient(cfg ClientConfig) *Client {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 100,
		IdleConnTimeout:     90 * time.Second,
	}

	client := &Client{
		baseURL: cfg.BaseURL,
		apiKey:  cfg.APIKey,
		httpClient: &http.Client{
			Timeout:   cfg.Timeout,
			Transport: transport,
		},
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
		logger:     logger.Default().WithField("component", "ascend_client"),
	}

	if cfg.CircuitBreaker.Enabled {
		client.cb = newCircuitBreaker(cfg.CircuitBreaker.Threshold, cfg.CircuitBreaker.ResetTimeout)
	}

	client.logger.Info("ASCEND client initialized",
		"base_url", maskURL(cfg.BaseURL),
		"timeout", cfg.Timeout.String(),
		"retry_count", cfg.RetryCount,
		"circuit_breaker", cfg.CircuitBreaker.Enabled,
	)

	return client
}

// EvaluateAction submits an action to ASCEND for governance evaluation.
func (c *Client) EvaluateAction(ctx context.Context, action *Action) (*Decision, error) {
	// Check circuit breaker
	if c.cb != nil && c.cb.IsOpen() {
		c.logger.Warn("Circuit breaker open, rejecting request")
		return nil, errors.New("circuit breaker open - ASCEND API temporarily unavailable")
	}

	var lastErr error

	for attempt := 0; attempt <= c.retryCount; attempt++ {
		if attempt > 0 {
			// Exponential backoff: delay * 2^(attempt-1)
			backoff := c.retryDelay * time.Duration(1<<(attempt-1))
			c.logger.Debug("Retrying request",
				"attempt", attempt,
				"backoff", backoff.String(),
			)

			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(backoff):
			}
		}

		decision, err := c.doRequest(ctx, action)
		if err == nil {
			// Success - reset circuit breaker
			if c.cb != nil {
				c.cb.RecordSuccess()
			}
			return decision, nil
		}

		lastErr = err

		// Don't retry authentication errors
		var authErr *AuthError
		if errors.As(err, &authErr) {
			c.logger.Error("Authentication error, not retrying", "error", err)
			break
		}

		c.logger.Warn("Request failed",
			"attempt", attempt+1,
			"error", err,
		)
	}

	// All retries failed - record failure in circuit breaker
	if c.cb != nil {
		c.cb.RecordFailure()
	}

	return nil, lastErr
}

func (c *Client) doRequest(ctx context.Context, action *Action) (*Decision, error) {
	url := c.baseURL + "/api/v1/actions/submit"

	body, err := json.Marshal(action)
	if err != nil {
		return nil, fmt.Errorf("marshal error: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("request error: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", c.apiKey)
	req.Header.Set("User-Agent", "ASCEND-Envoy-Authz/1.0.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("connection error: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read error: %w", err)
	}

	// Handle error status codes
	switch resp.StatusCode {
	case http.StatusUnauthorized:
		return nil, &AuthError{StatusCode: 401, Message: "invalid API key"}
	case http.StatusForbidden:
		return nil, &AuthError{StatusCode: 403, Message: "API key lacks permission"}
	case http.StatusTooManyRequests:
		return nil, errors.New("rate limited by ASCEND API")
	}

	if resp.StatusCode >= 500 {
		return nil, fmt.Errorf("server error: %d", resp.StatusCode)
	}

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
	}

	var decision Decision
	if err := json.Unmarshal(respBody, &decision); err != nil {
		return nil, fmt.Errorf("decode error: %w", err)
	}

	c.logger.Debug("Action evaluated",
		"action_id", decision.ActionID,
		"status", decision.Status,
		"risk_score", decision.RiskScore,
	)

	return &decision, nil
}

// GetCircuitState returns the current circuit breaker state.
func (c *Client) GetCircuitState() string {
	if c.cb == nil {
		return "disabled"
	}
	return c.cb.State()
}

// AuthError represents an authentication error.
type AuthError struct {
	StatusCode int
	Message    string
}

func (e *AuthError) Error() string {
	return fmt.Sprintf("authentication error (%d): %s", e.StatusCode, e.Message)
}

// Circuit breaker implementation

type circuitBreaker struct {
	mu            sync.RWMutex
	failures      int32
	lastFailure   time.Time
	open          bool
	threshold     int
	resetTimeout  time.Duration
}

func newCircuitBreaker(threshold int, resetTimeout time.Duration) *circuitBreaker {
	return &circuitBreaker{
		threshold:    threshold,
		resetTimeout: resetTimeout,
	}
}

func (cb *circuitBreaker) IsOpen() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	if !cb.open {
		return false
	}

	// Check if we should transition to half-open
	if time.Since(cb.lastFailure) > cb.resetTimeout {
		return false // Allow one request through
	}

	return true
}

func (cb *circuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	atomic.StoreInt32(&cb.failures, 0)
	cb.open = false
}

func (cb *circuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	failures := atomic.AddInt32(&cb.failures, 1)
	cb.lastFailure = time.Now()

	if int(failures) >= cb.threshold {
		cb.open = true
		atomic.StoreInt32(&cb.failures, 0) // Reset for next cycle
		logger.Warn("Circuit breaker OPEN",
			"failures", failures,
			"threshold", cb.threshold,
			"reset_timeout", cb.resetTimeout.String(),
		)
	}
}

func (cb *circuitBreaker) State() string {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	if !cb.open {
		return "closed"
	}

	if time.Since(cb.lastFailure) > cb.resetTimeout {
		return "half-open"
	}

	return "open"
}

// Helper to mask URL for logging (hide path details)
func maskURL(url string) string {
	if len(url) > 30 {
		return url[:30] + "..."
	}
	return url
}
