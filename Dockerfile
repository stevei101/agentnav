# Frontend Production Dockerfile
# Multi-stage build: build stage + nginx serving stage
FROM oven/bun:latest AS builder

WORKDIR /app

# Copy dependency files
COPY package.json bun.lockb* ./

# Install dependencies with frozen lockfile for reproducible builds
RUN bun install --frozen-lockfile || bun install

# Copy source code
COPY . .

# Build production bundle
RUN bun run build

# Production stage with nginx
FROM nginx:alpine

# Install gettext for envsubst utility
RUN apk add --no-cache gettext

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html


# Create nginx configuration with runtime env injection
RUN echo 'server { \
    listen ${PORT:-80}; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    # Health check endpoint for Cloud Run readiness \
    location /healthz { \
        add_header Content-Type text/plain; \
        return 200 "OK"; \
    } \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf.template

# Create startup script to inject runtime env vars into HTML
RUN echo '#!/bin/sh \
set -e \
# Replace PORT in nginx config \
envsubst "\${PORT}" < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf \
# Inject VITE_API_URL into index.html if set \
if [ -n "$VITE_API_URL" ]; then \
  sed -i "s|<head>|<head><script>window.VITE_API_URL=\"$VITE_API_URL\";</script>|" /usr/share/nginx/html/index.html \
fi \
# Start nginx \
exec nginx -g "daemon off;"' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Expose port 80 (Cloud Run will set PORT env var)
EXPOSE 80

# Use custom entrypoint for runtime configuration
ENTRYPOINT ["/docker-entrypoint.sh"]

