# Multi-stage build for production optimization
FROM node:22-alpine AS build

ARG VITE_API_URL
ARG CACHE_BUST=unknown

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json ./

# Install ALL dependencies (including devDependencies needed for build)
RUN npm ci --cache /tmp/empty-cache

# Copy source code
COPY . .

# Build production application with explicit clean
RUN rm -rf dist/ node_modules/.vite && npm run build:prod

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
