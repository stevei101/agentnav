# Frontend Production Dockerfile
# Multi-stage build: build stage + nginx serving stage
# Uses Bun v2 for fast dependency management and building
FROM oven/bun:latest AS builder

WORKDIR /app

# Copy dependency files
COPY package.json bun.lock* ./

# Install dependencies using Bun v2
# Note: bun.lock is used automatically for reproducible builds
RUN bun install

# Copy source code
COPY . .

# Build production bundle
RUN bun run build

# Production stage with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration (optional, nginx default works for SPA)
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80 (Cloud Run will set PORT env var, but nginx defaults to 80)
EXPOSE 80

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

