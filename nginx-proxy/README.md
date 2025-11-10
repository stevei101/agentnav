# Nginx Proxy for Agentnav

Thin reverse proxy layer deployed on Cloud Run for request routing and load balancing.

## Overview

This nginx proxy acts as a single entry point for all agentnav services, routing requests to the appropriate backend service:

- `/api/*` → Backend service (FastAPI)
- `/ws/*` → Backend service (WebSocket streaming)
- `/gemma/*` → Gemma GPU service
- `/docs` → Backend service (FastAPI docs)
- `/` → Frontend service (React SPA)

## Architecture

```
User Request
    ↓
Nginx Proxy (Cloud Run)
    ↓
    ├─→ Frontend Service (React)
    ├─→ Backend Service (FastAPI)
    └─→ Gemma GPU Service
```

## Features

- ✅ **Request Routing**: Routes requests to appropriate services
- ✅ **WebSocket Support**: Handles WebSocket connections for streaming
- ✅ **Health Checks**: `/healthz` endpoint for Cloud Run
- ✅ **Gzip Compression**: Reduces response sizes
- ✅ **SPA Routing**: Handles React Router client-side routing
- ✅ **Performance Optimized**: Tuned for Cloud Run

## Configuration

### Environment Variables

The proxy requires these environment variables (set by Terraform):

- `PORT`: Container port (default: 8080)
- `BACKEND_SERVICE_URL`: Backend service URL
- `FRONTEND_SERVICE_URL`: Frontend service URL
- `GEMMA_SERVICE_URL`: Gemma GPU service URL

### Routing Rules

| Path       | Destination | Purpose             |
| ---------- | ----------- | ------------------- |
| `/healthz` | Proxy       | Health check        |
| `/api/*`   | Backend     | API endpoints       |
| `/ws/*`    | Backend     | WebSocket streaming |
| `/gemma/*` | Gemma       | GPU service         |
| `/docs`    | Backend     | FastAPI docs        |
| `/`        | Frontend    | React SPA           |

## Deployment

### Build Image

```bash
cd nginx-proxy
podman build -t agentnav-proxy:latest .
```

### Deploy to Cloud Run

Deployment is handled automatically via:

1. **Terraform**: Creates Cloud Run service
2. **GitHub Actions**: Builds and pushes image
3. **CI/CD**: Updates service with new image

### Manual Deployment

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/agentnav-proxy:latest

# Deploy to Cloud Run
gcloud run deploy agentnav-proxy \
  --image gcr.io/PROJECT_ID/agentnav-proxy:latest \
  --region us-central1 \
  --platform managed \
  --port 8080 \
  --set-env-vars \
    BACKEND_SERVICE_URL=https://agentnav-backend-PROJECT_ID.run.app,\
    FRONTEND_SERVICE_URL=https://agentnav-frontend-PROJECT_ID.run.app,\
    GEMMA_SERVICE_URL=https://gemma-service-PROJECT_ID.run.app \
  --allow-unauthenticated
```

## Testing

### Health Check

```bash
curl https://agentnav-proxy-PROJECT_ID.run.app/healthz
# Should return: healthy
```

### Test Routing

```bash
# Test API routing
curl https://agentnav-proxy-PROJECT_ID.run.app/api/healthz

# Test frontend
curl https://agentnav-proxy-PROJECT_ID.run.app/

# Test docs
curl https://agentnav-proxy-PROJECT_ID.run.app/docs
```

## Local Development

### Run Locally

```bash
# Set environment variables
export PORT=8080
export BACKEND_SERVICE_URL=http://localhost:8080
export FRONTEND_SERVICE_URL=http://localhost:3000
export GEMMA_SERVICE_URL=http://localhost:8081

# Build and run
podman build -t agentnav-proxy:local .
podman run -p 8080:8080 \
  -e PORT=8080 \
  -e BACKEND_SERVICE_URL=http://host.containers.internal:8080 \
  -e FRONTEND_SERVICE_URL=http://host.containers.internal:3000 \
  -e GEMMA_SERVICE_URL=http://host.containers.internal:8081 \
  agentnav-proxy:local
```

## Performance

- **Memory**: 256Mi (lightweight)
- **CPU**: 1 vCPU
- **Startup Time**: <5 seconds
- **Latency Overhead**: <10ms per request

## Security

- ✅ **Public Access**: Proxy is public (gateway)
- ✅ **Backend Services**: Can be private (accessed via proxy)
- ✅ **Headers**: Preserves X-Forwarded-\* headers
- ✅ **HTTPS**: Cloud Run provides TLS termination

## Troubleshooting

### Check Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentnav-proxy" --limit 50
```

### Verify Environment Variables

```bash
gcloud run services describe agentnav-proxy \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### Test Configuration

```bash
# Check if nginx config is valid
podman run --rm agentnav-proxy:latest nginx -t
```

## Integration with Hackathon

This proxy provides:

- ✅ **Single Entry Point**: One URL for all services
- ✅ **Clean Routing**: Organized URL structure
- ✅ **Production Ready**: Suitable for demo
- ✅ **Cloud Run Native**: Fully serverless

---

**For Hackathon Submission:**

- Use proxy URL as "Try it Out" link
- All services accessible through single endpoint
- Cleaner architecture presentation
