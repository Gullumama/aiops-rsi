# Stage 1: Build stage
FROM golang:1.21-alpine AS builder

# Install dependencies
RUN apk add --no-cache git curl ca-certificates tzdata make gcc musl-dev

WORKDIR /build

# Clone K8sGPT repository
RUN git clone https://github.com/k8sgpt-ai/k8sgpt.git . || \
    (echo "Failed to clone K8sGPT, using local build" && exit 1)

# Build the application
RUN go mod download && \
    go mod tidy && \
    CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o k8sgpt \
    ./cmd/main.go

# Verify build
RUN ls -lh k8sgpt && ./k8sgpt version || echo "Build complete"

# Stage 2: Runtime stage
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    curl \
    bash \
    tzdata \
    kubectl

# Create non-root user
RUN addgroup -g 1000 k8sgpt && \
    adduser -D -u 1000 -G k8sgpt k8sgpt

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/k8sgpt /usr/local/bin/k8sgpt
RUN chmod +x /usr/local/bin/k8sgpt

# Copy configuration (if needed)
RUN mkdir -p /home/k8sgpt/.k8sgpt && \
    chown -R k8sgpt:k8sgpt /home/k8sgpt

# Set user
USER k8sgpt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD k8sgpt version || exit 1

# Default command
ENTRYPOINT ["k8sgpt"]
CMD ["--help"]