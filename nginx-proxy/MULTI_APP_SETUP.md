# Multi-App Nginx Proxy Setup

This nginx proxy routes requests to three applications:
1. **agentnav** - Multi-agent knowledge exploration system
2. **prompt-vault** - GenAI prompt management app
3. **cursor-ide** - Cursor IDE GCS prompt storage

## Port Configuration

### Local Development Ports

| App | Service | Port | Notes |
|-----|---------|------|-------|
| **nginx-proxy** | Proxy | 8082 | Avoids conflict with gvproxy on 8080 |
| **agentnav** | Frontend | 5173 | Vite dev server |
| **agentnav** | Backend | 8081 | FastAPI |
| **prompt-vault** | Frontend | 5176 | Vite dev server (non-conflicting) |
| **prompt-vault** | Backend | 8001 | FastAPI (non-conflicting) |
| **cursor-ide** | Frontend | 5173 | Vite dev server (shared with agentnav if not running simultaneously) |
| **cursor-ide** | Backend | 8188 | Python FastAPI |

**Note:** If both agentnav and cursor-ide need to run simultaneously, one should use a different port (e.g., agentnav on 5174).

## Routing Structure

The proxy routes requests based on URL paths:

### Agentnav Routes
- `/agentnav/` → Agentnav frontend
- `/agentnav/api/*` → Agentnav backend API
- `/agentnav/ws/*` → Agentnav WebSocket streaming
- `/agentnav/gemma/*` → Agentnav Gemma GPU service
- `/agentnav/docs` → Agentnav FastAPI documentation

### Prompt-vault Routes
- `/prompt-vault/` → Prompt-vault frontend
- `/prompt-vault/api/*` → Prompt-vault backend API
- `/prompt-vault/docs` → Prompt-vault FastAPI documentation

### Cursor-ide Routes
- `/cursor-ide/` → Cursor-ide frontend
- `/cursor-ide/api/*` → Cursor-ide backend API

### Root Route
- `/` → Defaults to agentnav frontend

## Quick Start

### 1. Start All Services Locally

**Terminal 1: Agentnav Frontend**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav
bun run dev  # Runs on port 5173
```

**Terminal 2: Agentnav Backend**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/backend
PORT=8081 uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

**Terminal 3: Prompt-vault**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/prompt-vault
./start-local.sh  # Starts frontend (5176) and backend (8001)
```

**Terminal 4: Cursor-ide**
```bash
cd /Users/stevenirvin/Documents/GitHub/cursor-ide/frontend
bun run dev  # Runs on port 5173 (conflicts with agentnav if both running)
```

**Terminal 5: Nginx Proxy**
```bash
cd /Users/stevenirvin/Documents/GitHub/stevei101/agentnav/nginx-proxy
./test-local.sh  # Starts proxy on port 8082
```

### 2. Test the Proxy

```bash
# Health check
curl http://localhost:8082/healthz

# Agentnav
curl http://localhost:8082/agentnav/
curl http://localhost:8082/agentnav/api/healthz

# Prompt-vault
curl http://localhost:8082/prompt-vault/
curl http://localhost:8082/prompt-vault/api/healthz

# Cursor-ide
curl http://localhost:8082/cursor-ide/
```

## Environment Variables

The proxy uses these environment variables (set automatically by test-local.sh):

```bash
PORT=8080  # Container port
AGENTNAV_FRONTEND_URL=http://host.docker.internal:5173
AGENTNAV_BACKEND_URL=http://host.docker.internal:8081
AGENTNAV_GEMMA_URL=http://host.docker.internal:8083
PROMPT_VAULT_FRONTEND_URL=http://host.docker.internal:5176
PROMPT_VAULT_BACKEND_URL=http://host.docker.internal:8001
CURSOR_IDE_FRONTEND_URL=http://host.docker.internal:5173
CURSOR_IDE_BACKEND_URL=http://host.docker.internal:8188
```

## Port Conflict Resolution

### If Ports Conflict

1. **Check what's using a port:**
   ```bash
   lsof -i :5173
   lsof -i :5176
   lsof -i :8001
   lsof -i :8081
   ```

2. **Kill conflicting processes:**
   ```bash
   lsof -ti :5173 | xargs kill -9
   ```

3. **Or change ports in the test script:**
   ```bash
   export AGENTNAV_FRONTEND_PORT=5174
   export PROMPT_VAULT_FRONTEND_PORT=5177
   ./test-local.sh
   ```

## Production Configuration

In production (Cloud Run), the proxy will use actual service URLs:

```bash
AGENTNAV_FRONTEND_URL=https://agentnav-frontend-PROJECT_ID.run.app
AGENTNAV_BACKEND_URL=https://agentnav-backend-PROJECT_ID.run.app
PROMPT_VAULT_FRONTEND_URL=https://prompt-vault-frontend-PROJECT_ID.run.app
PROMPT_VAULT_BACKEND_URL=https://prompt-vault-backend-PROJECT_ID.run.app
CURSOR_IDE_FRONTEND_URL=https://cursor-ide-frontend-PROJECT_ID.run.app
CURSOR_IDE_BACKEND_URL=https://cursor-ide-backend-PROJECT_ID.run.app
```

## Troubleshooting

### Proxy Can't Reach Services

**macOS/Windows:** Uses `host.docker.internal` (automatic)

**Linux:** May need to use actual host IP:
```bash
HOST_ADDR=$(ip route | grep default | awk '{print $3}')
```

### Services Not Responding

1. Verify services are running:
   ```bash
   curl http://localhost:5173  # agentnav frontend
   curl http://localhost:8081/healthz  # agentnav backend
   curl http://localhost:5176  # prompt-vault frontend
   curl http://localhost:8001/healthz  # prompt-vault backend
   ```

2. Check proxy logs:
   ```bash
   podman logs -f agentnav-proxy-local
   ```

3. Verify environment variables in container:
   ```bash
   podman exec agentnav-proxy-local env | grep URL
   ```

### CORS Issues

If you see CORS errors, ensure backend services allow the proxy origin:
- Add `http://localhost:8082` to CORS_ORIGINS in backend configs

## Summary

✅ **All three apps can be accessed through a single proxy:**
- Agentnav: `http://localhost:8082/agentnav/`
- Prompt-vault: `http://localhost:8082/prompt-vault/`
- Cursor-ide: `http://localhost:8082/cursor-ide/`

✅ **Ports are configured to avoid conflicts:**
- Agentnav: 5173 (frontend), 8081 (backend)
- Prompt-vault: 5176 (frontend), 8001 (backend)
- Cursor-ide: 5173 (frontend), 8188 (backend)
- Proxy: 8082 (local), 8080 (production)

