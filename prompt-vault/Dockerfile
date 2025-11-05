# Prompt Vault Frontend Production Dockerfile
# Multi-stage build: build stage + nginx serving stage
# Uses bun for fast dependency management and builds

FROM oven/bun:latest AS builder

WORKDIR /app

# Copy dependency files from frontend directory
COPY frontend/package.json ./
COPY frontend/bun.lock* ./

# Install dependencies with frozen lockfile for reproducible builds
RUN bun install --frozen-lockfile || bun install

# Copy frontend source code
COPY frontend/ .

# Build production bundle
# Vite builds to dist/ directory
RUN bun run build

# Production stage with nginx
FROM nginx:alpine

# Install gettext for envsubst utility and nodejs for JSON escaping
RUN apk add --no-cache gettext nodejs npm

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx configuration with runtime env injection
RUN echo 'server { \
    listen ${PORT:-80}; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf.template

# Create startup script to inject runtime env vars into HTML
# Use proper escaping to prevent injection vulnerabilities
RUN echo '#!/bin/sh \
set -e \
# Replace PORT in nginx config \
envsubst "\${PORT}" < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf \
# Inject Supabase environment variables into index.html if set \
# Use node.js for proper JSON escaping to prevent injection vulnerabilities \
if [ -n "$SUPABASE_URL" ]; then \
  ESCAPED_URL=$(node -p "JSON.stringify('$SUPABASE_URL').slice(1, -1)") \
  sed -i "s|<head>|<head><script>window.SUPABASE_URL=\"$ESCAPED_URL\";</script>|" /usr/share/nginx/html/index.html \
fi \
if [ -n "$SUPABASE_ANON_KEY" ]; then \
  ESCAPED_KEY=$(node -p "JSON.stringify('$SUPABASE_ANON_KEY').slice(1, -1)") \
  sed -i "s|<head>|<head><script>window.SUPABASE_ANON_KEY=\"$ESCAPED_KEY\";</script>|" /usr/share/nginx/html/index.html \
fi \
if [ -n "$NEXT_PUBLIC_GOOGLE_CLIENT_ID" ]; then \
  ESCAPED_CLIENT_ID=$(node -p "JSON.stringify('$NEXT_PUBLIC_GOOGLE_CLIENT_ID').slice(1, -1)") \
  sed -i "s|<head>|<head><script>window.NEXT_PUBLIC_GOOGLE_CLIENT_ID=\"$ESCAPED_CLIENT_ID\";</script>|" /usr/share/nginx/html/index.html \
fi \
# Start nginx \
exec nginx -g "daemon off;"' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Expose port 80 (Cloud Run will set PORT env var)
EXPOSE 80

# Use custom entrypoint for runtime configuration
ENTRYPOINT ["/docker-entrypoint.sh"]

