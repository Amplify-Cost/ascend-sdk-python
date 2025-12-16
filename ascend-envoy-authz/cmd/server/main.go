// ASCEND Envoy External Authorization Server
//
// gRPC service implementing Envoy's ext_authz API for AI agent governance.
//
// FAIL SECURE DESIGN:
//   - All errors result in request denial (unless fail_open=true)
//   - Only explicitly approved actions proceed
//   - Circuit breaker prevents cascade failures
//
// Usage:
//
//	ASCEND_API_URL=https://api.ascend.owkai.app \
//	ASCEND_API_KEY=your_api_key \
//	./server
//
// Author: ASCEND Platform Engineering
// Version: 1.0.0
package main

import (
	"context"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	authv3 "github.com/envoyproxy/go-control-plane/envoy/service/auth/v3"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/reflection"

	"github.com/owkai/ascend-envoy-authz/internal/ascend"
	"github.com/owkai/ascend-envoy-authz/internal/authz"
	"github.com/owkai/ascend-envoy-authz/internal/config"
	"github.com/owkai/ascend-envoy-authz/internal/logger"
)

const (
	version   = "1.0.0"
	userAgent = "ASCEND-Envoy-Authz/" + version
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		logger.Fatal("Failed to load configuration", "error", err)
	}

	// Configure logger
	logger.Configure(cfg.LogLevel, cfg.LogFormat)

	logger.Info("Starting ASCEND ext_authz server",
		"version", version,
		"port", cfg.Port,
		"environment", cfg.Environment,
		"fail_open", cfg.FailOpen,
	)

	// Initialize ASCEND client
	ascendClient := ascend.NewClient(ascend.ClientConfig{
		BaseURL:    cfg.AscendAPIURL,
		APIKey:     cfg.AscendAPIKey,
		Timeout:    cfg.Timeout,
		RetryCount: cfg.RetryCount,
		RetryDelay: cfg.RetryDelay,
		CircuitBreaker: ascend.CircuitBreakerConfig{
			Enabled:      cfg.CircuitBreakerEnabled,
			Threshold:    cfg.CircuitBreakerThreshold,
			ResetTimeout: cfg.CircuitBreakerTimeout,
		},
	})

	// Initialize authorization handler
	handler := authz.NewHandler(cfg, ascendClient)

	// Create gRPC server with keepalive settings
	grpcServer := grpc.NewServer(
		grpc.MaxConcurrentStreams(1000),
		grpc.KeepaliveParams(keepalive.ServerParameters{
			MaxConnectionIdle:     5 * time.Minute,
			MaxConnectionAge:      30 * time.Minute,
			MaxConnectionAgeGrace: 5 * time.Second,
			Time:                  1 * time.Minute,
			Timeout:               20 * time.Second,
		}),
		grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
			MinTime:             30 * time.Second,
			PermitWithoutStream: true,
		}),
		grpc.ChainUnaryInterceptor(
			loggingInterceptor,
			recoveryInterceptor,
		),
	)

	// Register authorization service
	authv3.RegisterAuthorizationServer(grpcServer, handler)

	// Register health service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	healthServer.SetServingStatus("envoy.service.auth.v3.Authorization", grpc_health_v1.HealthCheckResponse_SERVING)

	// Enable reflection for debugging (grpcurl, grpcui)
	reflection.Register(grpcServer)

	// Start listening
	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", cfg.Port))
	if err != nil {
		logger.Fatal("Failed to listen", "port", cfg.Port, "error", err)
	}

	// Graceful shutdown handler
	shutdownCh := make(chan os.Signal, 1)
	signal.Notify(shutdownCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-shutdownCh
		logger.Info("Received shutdown signal", "signal", sig)

		// Mark unhealthy
		healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
		healthServer.SetServingStatus("envoy.service.auth.v3.Authorization", grpc_health_v1.HealthCheckResponse_NOT_SERVING)

		// Give time for health check to propagate
		time.Sleep(5 * time.Second)

		// Graceful stop
		logger.Info("Initiating graceful shutdown...")
		grpcServer.GracefulStop()
	}()

	// Start serving
	logger.Info("ASCEND ext_authz server ready",
		"address", listener.Addr().String(),
		"circuit_breaker", ascendClient.GetCircuitState(),
	)

	if err := grpcServer.Serve(listener); err != nil {
		logger.Fatal("Server failed", "error", err)
	}

	logger.Info("Server shutdown complete")
}

// loggingInterceptor logs gRPC requests (excluding health checks).
func loggingInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	// Skip logging for health checks
	if info.FullMethod == "/grpc.health.v1.Health/Check" {
		return handler(ctx, req)
	}

	start := time.Now()
	resp, err := handler(ctx, req)
	latency := time.Since(start)

	if err != nil {
		logger.Error("gRPC request failed",
			"method", info.FullMethod,
			"latency_ms", latency.Milliseconds(),
			"error", err,
		)
	} else {
		logger.Debug("gRPC request completed",
			"method", info.FullMethod,
			"latency_ms", latency.Milliseconds(),
		)
	}

	return resp, err
}

// recoveryInterceptor recovers from panics and returns an error.
func recoveryInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (resp interface{}, err error) {
	defer func() {
		if r := recover(); r != nil {
			logger.Error("Panic recovered",
				"method", info.FullMethod,
				"panic", r,
			)
			err = fmt.Errorf("internal server error")
		}
	}()

	return handler(ctx, req)
}
