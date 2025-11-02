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

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx configuration template
# This template will be processed to replace $PORT with actual port from environment
RUN echo 'server { \
    listen ${PORT}; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf.template

# Expose port 80 (default, Cloud Run may override with PORT env var)
EXPOSE 80

# Start nginx with environment variable substitution
# Default PORT to 80 if not set, then replace ${PORT} in template
CMD ["/bin/sh", "-c", "export PORT=${PORT:-80} && envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]

