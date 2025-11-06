# Prompt Vault - Local Development Setup

## Port Configuration

**Current Port Assignments:**
- **cursor-ide frontend**: Port `5173` (fixed - was using 5173, 5174, 5175)
- **prompt-vault frontend**: Port `5176` (non-conflicting)
- **prompt-vault backend**: Port `8001` (non-conflicting)
- **agentnav backend**: Port `8080` (if running)

## Quick Start

### Option 1: Use Startup Script (Recommended)

```bash
cd /Users/stevenirvin/Documents/GitHub/agentnav/prompt-vault
./start-local.sh
```

This script will:
- Check for port conflicts
- Start backend on port 8001
- Start frontend on port 5176
- Show service URLs and logs

### Option 2: Manual Start

#### Start Backend

```bash
cd prompt-vault/backend

# Create virtual environment if needed
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
PORT=8001 uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: `http://localhost:8001`

#### Start Frontend

```bash
cd prompt-vault/frontend

# Install dependencies
bun install

# Start dev server
bun run dev
```

Frontend will be available at: `http://localhost:5176`

## Environment Variables

### Backend (.env file in `backend/`)

```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Firestore
FIRESTORE_PROJECT_ID=your-gcp-project-id
FIRESTORE_DATABASE_ID=(default)

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# ADK Configuration
A2A_PROTOCOL_ENABLED=true
```

### Frontend (.env.local file in `frontend/`)

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

## Service URLs

Once running:
- **Frontend**: http://localhost:5176
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/healthz

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :5176
lsof -i :8001

# Kill process if needed
lsof -ti :5176 | xargs kill -9
lsof -ti :8001 | xargs kill -9
```

### Backend Won't Start

1. Check virtual environment is activated
2. Verify dependencies are installed: `pip list`
3. Check environment variables are set
4. Review logs: `tail -f /tmp/prompt-vault-backend.log`

### Frontend Won't Start

1. Check node_modules exists: `ls node_modules`
2. Reinstall dependencies: `bun install`
3. Check vite config port: should be 5176
4. Review logs: `tail -f /tmp/prompt-vault-frontend.log`

## Stopping Services

```bash
# Stop all prompt-vault processes
pkill -f "uvicorn.*prompt-vault"
pkill -f "bun.*prompt-vault"

# Or stop by PID (shown in startup script)
kill <BACKEND_PID> <FRONTEND_PID>
```

## Port Conflict Summary

| Service | Port | Status |
|---------|------|--------|
| cursor-ide frontend | 5173 | ✅ Fixed (was using 5173, 5174, 5175) |
| prompt-vault frontend | 5176 | ✅ Configured |
| prompt-vault backend | 8001 | ✅ Configured |
| agentnav backend | 8080 | (if running) |

All ports are now non-conflicting! ✅

