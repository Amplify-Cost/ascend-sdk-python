ARG CACHE_BUST=1759976341
# Multi-stage build for production optimization
FROM node:22-alpine AS build

# Accept build arguments from GitHub Actions
ARG VITE_API_URL
ARG BUILD_DATE="unknown"
ARG COMMIT_SHA="unknown"

# Convert ARG to ENV so Vite can access during build
# Vite requires VITE_* environment variables at build time
ENV VITE_API_URL=${VITE_API_URL}

WORKDIR /app

# Cache bust - this changes with every commit
RUN echo "Build: ${COMMIT_SHA} at ${BUILD_DATE}"

COPY package.json package-lock.json ./
RUN npm ci --cache /tmp/empty-cache && rm -rf /tmp/empty-cache

COPY . .

# Enterprise-grade build process with explicit error checking
# No silent failures - fail fast if build errors occur
RUN echo "========================================" && \
    echo "Building frontend application" && \
    echo "API URL: ${VITE_API_URL}" && \
    echo "Commit: ${COMMIT_SHA}" && \
    echo "Date: ${BUILD_DATE}" && \
    echo "========================================" && \
    npm run build && \
    echo "========================================" && \
    echo "Verifying build output..." && \
    echo "========================================" && \
    test -d dist/ || (echo "ERROR: dist/ directory not created" && exit 1) && \
    test -f dist/index.html || (echo "ERROR: dist/index.html not found" && exit 1) && \
    ls -lah dist/ && \
    echo "✅ Build verification successful"

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

LABEL commit_sha="${COMMIT_SHA}"
LABEL build_date="${BUILD_DATE}"

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
