# Multi-stage build for production optimization
FROM node:22-alpine AS build

ARG VITE_API_URL
ARG BUILD_DATE
ARG COMMIT_SHA

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --cache /tmp/empty-cache && rm -rf /tmp/empty-cache

COPY . .
RUN rm -rf dist/ node_modules/.vite .vite

RUN echo "Building commit: ${COMMIT_SHA} at ${BUILD_DATE}" && \
    npm run build:prod && \
    ls -lah dist/assets/ | grep index

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

LABEL commit_sha="${COMMIT_SHA}"
LABEL build_date="${BUILD_DATE}"

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
