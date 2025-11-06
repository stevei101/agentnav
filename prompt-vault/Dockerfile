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
# Inject Supabase environment variables via a separate config.js file for better security \
# This approach generates a separate config file at runtime rather than modifying HTML with sed \
if [ -n "$SUPABASE_URL" ] || [ -n "$SUPABASE_ANON_KEY" ] || [ -n "$NEXT_PUBLIC_GOOGLE_CLIENT_ID" ]; then \
  # Use node.js for proper JSON escaping to prevent injection vulnerabilities \
  node -e " \
    const fs = require('fs'); \
    const config = { \
      SUPABASE_URL: process.env.SUPABASE_URL || null, \
      SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY || null, \
      NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || null \
    }; \
    const configScript = 'window.APP_CONFIG=' + JSON.stringify(config) + ';'; \
    fs.writeFileSync('/usr/share/nginx/html/config.js', configScript); \
  " \
  # Inject script tag to load config.js in index.html \
  sed -i 's|<head>|<head><script src="/config.js"></script>|' /usr/share/nginx/html/index.html \
fi \
# Start nginx \
exec nginx -g "daemon off;"' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Expose port 80 (Cloud Run will set PORT env var)
EXPOSE 80

# Use custom entrypoint for runtime configuration
ENTRYPOINT ["/docker-entrypoint.sh"]

