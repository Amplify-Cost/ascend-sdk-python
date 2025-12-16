# ASCEND Envoy External Authorization Server
# Multi-stage build for minimal image size
#
# Author: ASCEND Platform Engineering

# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Copy go mod files first for better caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -X main.version=1.0.0" \
    -o /server \
    ./cmd/server

# Runtime stage
FROM alpine:3.19

# Install ca-certificates for HTTPS
RUN apk add --no-cache ca-certificates tzdata

# Create non-root user
RUN adduser -D -g '' -u 1000 appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder /server /app/server

# Use non-root user
USER appuser

# Expose ports
EXPOSE 50051 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://localhost:8080/health"]

# Run the server
ENTRYPOINT ["/app/server"]
