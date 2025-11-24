ARG CACHE_BUST
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

# CRITICAL: Clear Vite cache to ensure fresh build with latest source code
RUN rm -rf node_modules/.vite dist

# Build with error output visible
RUN echo "Building with VITE_API_URL=${VITE_API_URL}" && npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

LABEL commit_sha="${COMMIT_SHA}"
LABEL build_date="${BUILD_DATE}"

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
