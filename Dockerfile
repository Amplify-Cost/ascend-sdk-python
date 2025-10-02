# Multi-stage build for production optimization
FROM node:22-alpine AS build

# Build args for cache busting
ARG VITE_API_URL
ARG BUILD_DATE
ARG COMMIT_SHA

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Clean install with no cache
RUN npm ci --cache /tmp/empty-cache && rm -rf /tmp/empty-cache

# Copy source code
COPY . .

# Clear any existing build artifacts and vite cache
RUN rm -rf dist/ node_modules/.vite .vite

# Build with explicit environment
RUN echo "Building commit: ${COMMIT_SHA} at ${BUILD_DATE}" && \
    npm run build:prod && \
    ls -lah dist/assets/ | grep index

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Add labels for tracking
LABEL commit_sha="${COMMIT_SHA}"
LABEL build_date="${BUILD_DATE}"

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
