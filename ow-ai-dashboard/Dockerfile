# Multi-stage build - first stage builds the app, second serves it
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first (optimization)
COPY package*.json ./
COPY yarn.lock* ./

# Install dependencies
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    else npm ci; fi

# Copy source code
COPY . .

# Build argument for API URL (will be provided by GitHub Actions)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the React application for production
RUN if [ -f yarn.lock ]; then yarn build; \
    else npm run build; fi

# Production stage - serves the built app with nginx
FROM nginx:alpine

# Copy built app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx configuration for single-page applications
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass $VITE_API_URL; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
