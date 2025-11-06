# Starting All Services for Nginx Proxy Testing

## Current Port Status

Based on `lsof -i -P | grep LISTEN`:

### ✅ Currently Running
- **cursor-ide frontend**: Port 5173 (node 19003)
- **cursor-ide backend**: Port 8188 (python3.1 34719)
- **gvproxy (Podman)**: Ports 8080, 8081 (system service - don't use these)

### ⚠️ Port Conflicts to Consider

1. **Port 5173**: Both cursor-ide and agentnav want to use this
   - **Solution**: Only run one at a time, OR change agentnav to 5174
   
2. **Port 8081**: gvproxy (Podman) is using this
   - **Solution**: Agentnav backend should use a different port (e.g., 8083)

## Recommended Startup Sequence

### Option 1: Run All Services (Recommended)

**Terminal 1: Agentnav Frontend (use port 5174 to avoid conflict)**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav
# Temporarily change port to 5174
export PORT=5174
bun run dev --port 5174
```

**Terminal 2: Agentnav Backend (use port 8083 to avoid gvproxy)**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/backend
PORT=8083 uvicorn main:app --host 0.0.0.0 --port 8083 --reload
```

**Terminal 3: Prompt-vault (ports already configured)**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/prompt-vault
./start-local.sh
# This starts:
#   - Frontend on 5176
#   - Backend on 8001
```

**Terminal 4: Cursor-ide (already running)**
- Frontend: Already on 5173 ✅
- Backend: Already on 8188 ✅

**Terminal 5: Nginx Proxy**
```bash
cd /Users/stevenirvin/Documents/GitHub/stevei101/agentnav/nginx-proxy
# Update ports in test script or set env vars:
export AGENTNAV_FRONTEND_PORT=5174
export AGENTNAV_BACKEND_PORT=8083
./test-local.sh
```

### Option 2: Run Without Cursor-ide (Simpler)

If you don't need cursor-ide running simultaneously:

**Terminal 1: Agentnav Frontend**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav
bun run dev  # Uses port 5173 (cursor-ide not running)
```

**Terminal 2: Agentnav Backend**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/backend
PORT=8083 uvicorn main:app --host 0.0.0.0 --port 8083 --reload
```

**Terminal 3: Prompt-vault**
```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/prompt-vault
./start-local.sh
```

**Terminal 4: Nginx Proxy**
```bash
cd /Users/stevenirvin/Documents/GitHub/stevei101/agentnav/nginx-proxy
export AGENTNAV_FRONTEND_PORT=5173
export AGENTNAV_BACKEND_PORT=8083
./test-local.sh
```

## Updated Port Configuration

| App | Service | Port | Notes |
|-----|---------|------|-------|
| **cursor-ide** | Frontend | 5173 | ✅ Running |
| **cursor-ide** | Backend | 8188 | ✅ Running |
| **agentnav** | Frontend | 5174 | Use this if cursor-ide is running |
| **agentnav** | Backend | 8083 | Avoids gvproxy on 8081 |
| **prompt-vault** | Frontend | 5176 | ✅ Available |
| **prompt-vault** | Backend | 8001 | ✅ Available |
| **nginx-proxy** | Proxy | 8082 | ✅ Available (avoids gvproxy on 8080) |

## Quick Test Commands

After starting all services:

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

## Troubleshooting

### Port Already in Use

```bash
# Check what's using a port
lsof -i :5173
lsof -i :8083

# Kill if needed (be careful!)
lsof -ti :PORT | xargs kill -9
```

### Services Not Responding

1. Verify service is running:
   ```bash
   curl http://localhost:5174  # agentnav frontend
   curl http://localhost:8083/healthz  # agentnav backend
   ```

2. Check proxy logs:
   ```bash
   podman logs -f agentnav-proxy-local
   ```

3. Verify environment variables:
   ```bash
   podman exec agentnav-proxy-local env | grep URL
   ```

