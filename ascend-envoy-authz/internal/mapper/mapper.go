// Package mapper converts Envoy CheckRequest to ASCEND Action.
//
// Maps HTTP method and path to action_type for governance evaluation.
//
// Author: ASCEND Platform Engineering
package mapper

import (
	"regexp"
	"strings"

	authv3 "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"

	"github.com/owkai/ascend-envoy-authz/internal/ascend"
)

// HTTP method to action type mapping
var methodToAction = map[string]string{
	"GET":     "read",
	"HEAD":    "read",
	"OPTIONS": "read",
	"POST":    "create",
	"PUT":     "update",
	"PATCH":   "update",
	"DELETE":  "delete",
}

// ResourcePattern maps path patterns to action types
type ResourcePattern struct {
	Pattern    *regexp.Regexp
	ActionType string
}

// Built-in resource patterns (order matters - first match wins)
var resourcePatterns = []ResourcePattern{
	{regexp.MustCompile(`^/admin`), "admin_access"},
	{regexp.MustCompile(`^/export`), "data_export"},
	{regexp.MustCompile(`^/import`), "data_import"},
	{regexp.MustCompile(`^/batch`), "batch_operation"},
	{regexp.MustCompile(`^/bulk`), "bulk_operation"},
	{regexp.MustCompile(`/users?/`), "user_data_access"},
	{regexp.MustCompile(`/customers?/`), "customer_data_access"},
	{regexp.MustCompile(`/payment`), "payment_operation"},
	{regexp.MustCompile(`/billing`), "billing_operation"},
	{regexp.MustCompile(`/config`), "config_change"},
	{regexp.MustCompile(`/settings`), "settings_change"},
	{regexp.MustCompile(`/audit`), "audit_access"},
	{regexp.MustCompile(`/logs?`), "log_access"},
	{regexp.MustCompile(`/reports?`), "report_access"},
	{regexp.MustCompile(`/analytics`), "analytics_access"},
	{regexp.MustCompile(`/dashboard`), "dashboard_access"},
	{regexp.MustCompile(`/api.?keys?`), "api_key_management"},
	{regexp.MustCompile(`/tokens?`), "token_management"},
	{regexp.MustCompile(`/secrets?`), "secret_access"},
	{regexp.MustCompile(`/credentials?`), "credential_access"},
}

// Patterns for normalizing paths (replacing IDs with placeholders)
var (
	numericIDPattern = regexp.MustCompile(`/\d+(/|$)`)
	uuidPattern      = regexp.MustCompile(`/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(/|$)`)
)

// MapCheckRequest converts an Envoy CheckRequest to an ASCEND Action.
func MapCheckRequest(req *authv3.CheckRequest, agentID string, env, sensitivity string) *ascend.Action {
	attrs := req.GetAttributes()
	httpReq := attrs.GetRequest().GetHttp()

	method := httpReq.GetMethod()
	path := httpReq.GetPath()

	// Remove query string from path
	if idx := strings.Index(path, "?"); idx != -1 {
		path = path[:idx]
	}

	// Determine action type
	actionType := determineActionType(method, path)

	// Extract resource type
	resourceType := extractResourceType(path)

	// Build context
	context := map[string]interface{}{
		"http_method":      method,
		"http_path":        path,
		"source_ip":        getSourceIP(attrs),
		"integration_type": "envoy_ext_authz",
	}

	// Add host if present
	if host := httpReq.GetHost(); host != "" {
		context["host"] = host
	}

	// Add protocol
	if protocol := httpReq.GetProtocol(); protocol != "" {
		context["protocol"] = protocol
	}

	return &ascend.Action{
		AgentID:         agentID,
		ActionType:      actionType,
		ToolName:        "envoy_proxy",
		Description:     method + " " + path,
		ResourceType:    resourceType,
		Environment:     env,
		DataSensitivity: sensitivity,
		Context:         context,
	}
}

// determineActionType maps HTTP method and path to an action type.
func determineActionType(method, path string) string {
	// Check built-in resource patterns first
	for _, rp := range resourcePatterns {
		if rp.Pattern.MatchString(path) {
			return rp.ActionType
		}
	}

	// Default: method-based action with resource name
	baseAction := methodToAction[strings.ToUpper(method)]
	if baseAction == "" {
		baseAction = "execute"
	}

	// Extract first path segment as resource
	resource := extractResourceType(path)
	if resource != "" && resource != "unknown" {
		return baseAction + "_" + resource
	}

	return baseAction
}

// extractResourceType extracts the resource type from a path.
func extractResourceType(path string) string {
	// Split path and find first meaningful segment
	segments := strings.Split(strings.Trim(path, "/"), "/")

	skipPrefixes := map[string]bool{
		"api": true, "v1": true, "v2": true, "v3": true,
		"internal": true, "public": true, "private": true,
	}

	for _, seg := range segments {
		// Skip empty, version prefixes, and numeric IDs
		if seg == "" || skipPrefixes[seg] || isNumeric(seg) {
			continue
		}
		return strings.ToLower(seg)
	}

	return "unknown"
}

// getSourceIP extracts the source IP from request attributes.
func getSourceIP(attrs *authv3.AttributeContext) string {
	if source := attrs.GetSource(); source != nil {
		if addr := source.GetAddress(); addr != nil {
			if socket := addr.GetSocketAddress(); socket != nil {
				return socket.GetAddress()
			}
		}
	}
	return "unknown"
}

// isNumeric checks if a string is all digits.
func isNumeric(s string) bool {
	if s == "" {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

// NormalizePath normalizes a path by replacing IDs with placeholders.
// Used for cache key generation.
func NormalizePath(path string) string {
	// Replace numeric IDs
	normalized := numericIDPattern.ReplaceAllString(path, "/{id}$1")
	// Replace UUIDs
	normalized = uuidPattern.ReplaceAllString(normalized, "/{id}$1")
	return normalized
}

// GenerateCacheKey generates a cache key for an action.
func GenerateCacheKey(agentID, method, path string) string {
	normalizedPath := NormalizePath(path)
	return agentID + ":" + method + ":" + normalizedPath
}

// IsPathExcluded checks if a path should be excluded from governance.
func IsPathExcluded(path string, excludedPaths []string) bool {
	for _, excluded := range excludedPaths {
		if excluded == "" {
			continue
		}
		// Support both exact match and prefix match
		if path == excluded || strings.HasPrefix(path, excluded) {
			return true
		}
		// Support regex patterns (starts with ^)
		if strings.HasPrefix(excluded, "^") {
			if re, err := regexp.Compile(excluded); err == nil {
				if re.MatchString(path) {
					return true
				}
			}
		}
	}
	return false
}
