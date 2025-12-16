// Package config provides configuration management for the ASCEND ext_authz service.
//
// Configuration is loaded from environment variables with sensible defaults.
// All sensitive values (API keys) should be provided via Kubernetes secrets.
//
// Author: ASCEND Platform Engineering
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// Config holds all configuration for the ext_authz service.
type Config struct {
	// Server settings
	Port        int
	MetricsPort int

	// ASCEND API settings
	AscendAPIURL string
	AscendAPIKey string

	// Agent ID settings
	AgentIDHeader  string
	DefaultAgentID string
	RequireAgentID bool

	// Behavior settings
	FailOpen       bool
	BlockOnPending bool

	// Context settings
	Environment     string
	DataSensitivity string
	OrganizationID  string

	// Performance settings
	Timeout    time.Duration
	RetryCount int
	RetryDelay time.Duration
	CacheTTL   time.Duration

	// Circuit breaker settings
	CircuitBreakerEnabled   bool
	CircuitBreakerThreshold int
	CircuitBreakerTimeout   time.Duration

	// Logging settings
	LogLevel      string
	LogFormat     string
	LogDecisions  bool

	// Path exclusions
	ExcludedPaths []string
}

// Load reads configuration from environment variables.
func Load() (*Config, error) {
	cfg := &Config{
		// Server defaults
		Port:        getEnvInt("PORT", 50051),
		MetricsPort: getEnvInt("METRICS_PORT", 8080),

		// ASCEND API (required)
		AscendAPIURL: os.Getenv("ASCEND_API_URL"),
		AscendAPIKey: os.Getenv("ASCEND_API_KEY"),

		// Agent ID settings
		AgentIDHeader:  getEnv("AGENT_ID_HEADER", "x-ascend-agent-id"),
		DefaultAgentID: os.Getenv("DEFAULT_AGENT_ID"),
		RequireAgentID: getEnvBool("REQUIRE_AGENT_ID", true),

		// Behavior settings
		FailOpen:       getEnvBool("FAIL_OPEN", false), // FAIL SECURE by default
		BlockOnPending: getEnvBool("BLOCK_ON_PENDING", true),

		// Context settings
		Environment:     getEnv("ENVIRONMENT", "production"),
		DataSensitivity: getEnv("DATA_SENSITIVITY", "standard"),
		OrganizationID:  os.Getenv("ORGANIZATION_ID"),

		// Performance settings
		Timeout:    getEnvDuration("TIMEOUT", 5*time.Second),
		RetryCount: getEnvInt("RETRY_COUNT", 2),
		RetryDelay: getEnvDuration("RETRY_DELAY", 100*time.Millisecond),
		CacheTTL:   getEnvDuration("CACHE_TTL", 60*time.Second),

		// Circuit breaker settings
		CircuitBreakerEnabled:   getEnvBool("CIRCUIT_BREAKER_ENABLED", true),
		CircuitBreakerThreshold: getEnvInt("CIRCUIT_BREAKER_THRESHOLD", 5),
		CircuitBreakerTimeout:   getEnvDuration("CIRCUIT_BREAKER_TIMEOUT", 30*time.Second),

		// Logging settings
		LogLevel:     getEnv("LOG_LEVEL", "info"),
		LogFormat:    getEnv("LOG_FORMAT", "json"),
		LogDecisions: getEnvBool("LOG_DECISIONS", true),

		// Path exclusions
		ExcludedPaths: getEnvList("EXCLUDED_PATHS", []string{"/health", "/ready", "/metrics"}),
	}

	// Validate required fields
	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	return cfg, nil
}

// Validate checks that all required configuration is present.
func (c *Config) Validate() error {
	if c.AscendAPIURL == "" {
		return fmt.Errorf("ASCEND_API_URL is required")
	}

	if !strings.HasPrefix(c.AscendAPIURL, "https://") {
		return fmt.Errorf("ASCEND_API_URL must use HTTPS")
	}

	if c.AscendAPIKey == "" {
		return fmt.Errorf("ASCEND_API_KEY is required")
	}

	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("PORT must be between 1 and 65535")
	}

	if c.Timeout < 100*time.Millisecond || c.Timeout > 30*time.Second {
		return fmt.Errorf("TIMEOUT must be between 100ms and 30s")
	}

	if c.RetryCount < 0 || c.RetryCount > 5 {
		return fmt.Errorf("RETRY_COUNT must be between 0 and 5")
	}

	if c.CircuitBreakerThreshold < 1 || c.CircuitBreakerThreshold > 100 {
		return fmt.Errorf("CIRCUIT_BREAKER_THRESHOLD must be between 1 and 100")
	}

	// Warn about fail_open
	if c.FailOpen {
		fmt.Println("WARNING: FAIL_OPEN=true is enabled - NOT RECOMMENDED for production")
	}

	return nil
}

// Helper functions for environment variable parsing

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if i, err := strconv.Atoi(value); err == nil {
			return i
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		return strings.ToLower(value) == "true" || value == "1"
	}
	return defaultValue
}

func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if d, err := time.ParseDuration(value); err == nil {
			return d
		}
	}
	return defaultValue
}

func getEnvList(key string, defaultValue []string) []string {
	if value := os.Getenv(key); value != "" {
		return strings.Split(value, ",")
	}
	return defaultValue
}
