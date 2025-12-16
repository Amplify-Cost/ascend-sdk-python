// Package mapper tests for request mapping.
//
// Author: ASCEND Platform Engineering
package mapper

import (
	"testing"

	authv3 "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"
)

func newTestCheckRequest(method, path string) *authv3.CheckRequest {
	return &authv3.CheckRequest{
		Attributes: &authv3.AttributeContext{
			Request: &authv3.AttributeContext_Request{
				Http: &authv3.AttributeContext_HttpRequest{
					Method: method,
					Path:   path,
				},
			},
		},
	}
}

func TestMapCheckRequest(t *testing.T) {
	tests := []struct {
		name           string
		method         string
		path           string
		agentID        string
		expectedAction string
	}{
		{
			name:           "GET users",
			method:         "GET",
			path:           "/api/v1/users",
			agentID:        "test-agent",
			expectedAction: "user_data_access",
		},
		{
			name:           "POST users",
			method:         "POST",
			path:           "/api/v1/users",
			agentID:        "test-agent",
			expectedAction: "user_data_access",
		},
		{
			name:           "DELETE users",
			method:         "DELETE",
			path:           "/api/v1/users/123",
			agentID:        "test-agent",
			expectedAction: "user_data_access",
		},
		{
			name:           "admin access",
			method:         "GET",
			path:           "/admin/settings",
			agentID:        "test-agent",
			expectedAction: "admin_access",
		},
		{
			name:           "data export",
			method:         "GET",
			path:           "/export/report",
			agentID:        "test-agent",
			expectedAction: "data_export",
		},
		{
			name:           "payment operation",
			method:         "POST",
			path:           "/api/v1/payments/process",
			agentID:        "test-agent",
			expectedAction: "payment_operation",
		},
		{
			name:           "generic GET orders",
			method:         "GET",
			path:           "/api/v1/orders",
			agentID:        "test-agent",
			expectedAction: "read_orders",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := newTestCheckRequest(tt.method, tt.path)
			action := MapCheckRequest(req, tt.agentID, "test", "standard")

			if action.ActionType != tt.expectedAction {
				t.Errorf("Expected action %s, got %s", tt.expectedAction, action.ActionType)
			}
			if action.AgentID != tt.agentID {
				t.Errorf("Expected agent ID %s, got %s", tt.agentID, action.AgentID)
			}
		})
	}
}

func TestDetermineActionType(t *testing.T) {
	tests := []struct {
		method   string
		path     string
		expected string
	}{
		{"GET", "/api/users", "user_data_access"},
		{"POST", "/api/customers", "customer_data_access"},
		{"GET", "/admin/config", "admin_access"},
		{"GET", "/export/data", "data_export"},
		{"POST", "/import/data", "data_import"},
		{"GET", "/batch/process", "batch_operation"},
		{"GET", "/api/orders", "read_orders"},
		{"POST", "/api/items", "create_items"},
		{"PUT", "/api/items/1", "update_items"},
		{"DELETE", "/api/items/1", "delete_items"},
	}

	for _, tt := range tests {
		t.Run(tt.method+" "+tt.path, func(t *testing.T) {
			result := determineActionType(tt.method, tt.path)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestExtractResourceType(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"/api/v1/users", "users"},
		{"/api/v1/users/123", "users"},
		{"/users", "users"},
		{"/api/orders", "orders"},
		{"/v2/items", "items"},
		{"/", "unknown"},
		{"/api/v1", "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			result := extractResourceType(tt.path)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestNormalizePath(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"/api/users/123", "/api/users/{id}"},
		{"/api/users/123/orders/456", "/api/users/{id}/orders/{id}"},
		{"/api/users/550e8400-e29b-41d4-a716-446655440000", "/api/users/{id}"},
		{"/api/users", "/api/users"},
		{"/health", "/health"},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			result := NormalizePath(tt.path)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestGenerateCacheKey(t *testing.T) {
	tests := []struct {
		agentID  string
		method   string
		path     string
		expected string
	}{
		{"agent-1", "GET", "/api/users", "agent-1:GET:/api/users"},
		{"agent-1", "GET", "/api/users/123", "agent-1:GET:/api/users/{id}"},
		{"agent-2", "POST", "/api/items", "agent-2:POST:/api/items"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			result := GenerateCacheKey(tt.agentID, tt.method, tt.path)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}

func TestIsPathExcluded(t *testing.T) {
	excludedPaths := []string{"/health", "/metrics", "/ready", "^/internal/"}

	tests := []struct {
		path     string
		expected bool
	}{
		{"/health", true},
		{"/metrics", true},
		{"/ready", true},
		{"/internal/status", true},
		{"/api/users", false},
		{"/healthcheck", false},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			result := IsPathExcluded(tt.path, excludedPaths)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

func TestIsNumeric(t *testing.T) {
	tests := []struct {
		input    string
		expected bool
	}{
		{"123", true},
		{"0", true},
		{"999999", true},
		{"", false},
		{"abc", false},
		{"12a", false},
		{"a12", false},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := isNumeric(tt.input)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}
