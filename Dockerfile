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


# Create nginx configuration template with runtime env injection
# Using single $ for envsubst to substitute, and $$ for literal $ in nginx config
RUN echo 'server { \
    listen $PORT; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Health check endpoint for Cloud Run \
    location /healthz { \
        access_log off; \
        return 200 "healthy\\n"; \
        add_header Content-Type text/plain; \
    } \
    \
    location / { \
        try_files $$uri $$uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf.template

# Create startup script to inject runtime env vars into HTML
RUN echo '#!/bin/sh \
set -e \
# Set default PORT if not provided by Cloud Run \
export PORT=${PORT:-80} \
echo "Starting nginx on port $PORT" \
# Replace only PORT variable in nginx config (not $uri, etc.) \
envsubst '"'"'$PORT'"'"' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf \
# Inject VITE_API_URL into index.html if set \
if [ -n "$VITE_API_URL" ]; then \
  sed -i "s|<head>|<head><script>window.VITE_API_URL=\"$VITE_API_URL\";</script>|" /usr/share/nginx/html/index.html \
fi \
# Test nginx configuration \
nginx -t \
# Start nginx in foreground \
exec nginx -g "daemon off;"' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Expose port 80 (Cloud Run will set PORT env var)
EXPOSE 80

# Use custom entrypoint for runtime configuration
ENTRYPOINT ["/docker-entrypoint.sh"]

