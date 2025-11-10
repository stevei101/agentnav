# Nginx Proxy for Agentnav Cloud Run
# Thin reverse proxy layer for request routing

FROM nginx:1.25-alpine

# Install envsubst for environment variable substitution and wget for health checks
RUN apk add --no-cache gettext wget

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

# Copy landing page
COPY landing/ /usr/share/nginx/html/landing/

# Create entrypoint script for environment variable substitution
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo 'export PORT=${PORT:-8080}' >> /docker-entrypoint.sh && \
    echo 'export AGENTNAV_BACKEND_URL=${AGENTNAV_BACKEND_URL:-${BACKEND_SERVICE_URL:-}}' >> /docker-entrypoint.sh && \
    echo 'export AGENTNAV_FRONTEND_URL=${AGENTNAV_FRONTEND_URL:-${FRONTEND_SERVICE_URL:-}}' >> /docker-entrypoint.sh && \
        echo 'export AGENTNAV_GEMMA_URL=${AGENTNAV_GEMMA_URL:-${GEMMA_SERVICE_URL:-_disabled_}}' >> /docker-entrypoint.sh && \
    echo 'export CURSOR_IDE_BACKEND_URL=${CURSOR_IDE_BACKEND_URL:-_disabled_}' >> /docker-entrypoint.sh && \
    echo 'export CURSOR_IDE_FRONTEND_URL=${CURSOR_IDE_FRONTEND_URL:-_disabled_}' >> /docker-entrypoint.sh && \
    echo 'envsubst '"'"'$$PORT $$AGENTNAV_BACKEND_URL $$AGENTNAV_FRONTEND_URL $$AGENTNAV_GEMMA_URL $$CURSOR_IDE_BACKEND_URL $$CURSOR_IDE_FRONTEND_URL'"'"' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf' >> /docker-entrypoint.sh && \
    echo 'echo "✅ Nginx config generated"' >> /docker-entrypoint.sh && \
    echo 'echo "  PORT=${PORT}"' >> /docker-entrypoint.sh && \
    echo 'echo "  AGENTNAV_BACKEND_URL=${AGENTNAV_BACKEND_URL}"' >> /docker-entrypoint.sh && \
    echo 'echo "  AGENTNAV_FRONTEND_URL=${AGENTNAV_FRONTEND_URL}"' >> /docker-entrypoint.sh && \
    echo 'nginx -t' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/healthz || exit 1

# Start nginx
ENTRYPOINT ["/docker-entrypoint.sh"]

