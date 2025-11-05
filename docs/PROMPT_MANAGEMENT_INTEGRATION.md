# Prompt Management Integration Guide

## Overview

This document describes the fast-track integration of the GenAI Prompt Management App into the agentnav infrastructure. The integration uses agentnav's existing Terraform, Cloud Run, and Firestore setup.

## What Was Integrated

### Backend (✅ Completed)

1. **Data Models** (`backend/models/prompt_models.py`)
   - `Prompt`, `PromptCreate`, `PromptUpdate`
   - `PromptVersion` for version history
   - `TestResult` for prompt testing
   - `UserInfo` for authentication

2. **Service Layer** (`backend/services/prompt_service.py`)
   - Firestore-based CRUD operations
   - Version history management
   - Test result tracking
   - Replaces Supabase KV store

3. **API Routes** (`backend/routes/prompt_routes.py`)
   - `GET /api/prompts` - List all prompts
   - `GET /api/prompts/{id}` - Get prompt by ID
   - `POST /api/prompts` - Create new prompt
   - `PUT /api/prompts/{id}` - Update prompt
   - `DELETE /api/prompts/{id}` - Delete prompt
   - `GET /api/prompts/{id}/versions` - Get version history
   - `POST /api/prompts/{id}/tests` - Add test result
   - `GET /api/prompts/user/info` - Get user info

### Frontend (⏳ Pending)

The frontend integration requires:
1. Adding Prompt Management UI components to agentnav frontend
2. Setting up navigation between Agent Navigator and Prompt Management
3. Updating API calls to use agentnav backend instead of Supabase
4. Implementing authentication (currently placeholder)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    agentnav Frontend                      │
│  ┌──────────────┐              ┌──────────────┐         │
│  │   Agent      │              │   Prompt     │         │
│  │  Navigator   │  ←→ Router → │ Management  │         │
│  └──────────────┘              └──────────────┘         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              agentnav Backend (FastAPI)                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  /api/prompts/* - Prompt Management Routes        │   │
│  │  /api/analyze - Agent Analysis Routes             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Firestore Database                     │
│  ┌──────────────┐              ┌──────────────┐         │
│  │   prompts    │              │   versions   │         │
│  │  collection  │              │  collection  │         │
│  └──────────────┘              └──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

## Data Migration

If you have existing prompts in Supabase, you'll need to:
1. Export prompts from Supabase KV store
2. Import them into Firestore using the `PromptService`
3. Update user IDs to match your authentication system

## Authentication

Currently, the backend uses a placeholder authentication system. For production, you should:

1. **Option A: Google OAuth** (Recommended for GCP)
   - Use Google Identity Platform
   - Verify JWT tokens in `get_user_from_header()`
   - Update `prompt_routes.py` authentication

2. **Option B: Keep Supabase Auth**
   - Keep Supabase for authentication only
   - Frontend calls Supabase for auth
   - Backend accepts user_id from frontend

3. **Option C: API Keys**
   - Simple API key authentication
   - Less secure but fastest

## Deployment

### Terraform

No changes needed! The existing Terraform configuration already supports:
- ✅ Cloud Run services
- ✅ Firestore database
- ✅ Artifact Registry
- ✅ Secret Manager

### Environment Variables

Add to Cloud Run backend service:
- `FIRESTORE_PROJECT_ID` (already set)
- `FIRESTORE_DATABASE_ID` (already set)

### CORS Configuration

Update CORS in `backend/main.py` if needed:
```python
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://agentnav.lornu.com"
).split(",")
```

## Testing

### Backend API Testing

```bash
# Test create prompt
curl -X POST http://localhost:8080/api/prompts \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Prompt", "content": "Hello world", "tags": ["test"]}'

# Test list prompts
curl http://localhost:8080/api/prompts

# Test get prompt
curl http://localhost:8080/api/prompts/{prompt_id}
```

### Frontend Testing

1. Start agentnav backend: `cd backend && uv run uvicorn main:app --reload`
2. Start agentnav frontend: `npm run dev`
3. Navigate to Prompt Management page
4. Test CRUD operations

## Next Steps

1. **Frontend Integration**
   - [ ] Copy Prompt Management components to agentnav/components
   - [ ] Add routing/navigation in App.tsx
   - [ ] Update API service to call agentnav backend
   - [ ] Install missing UI dependencies (shadcn/ui or alternatives)

2. **Authentication**
   - [ ] Implement Google OAuth or chosen auth method
   - [ ] Update `get_user_from_header()` in prompt_routes.py
   - [ ] Test authentication flow

3. **Deployment**
   - [ ] Build and push backend container
   - [ ] Deploy to Cloud Run
   - [ ] Test in production environment

4. **Data Migration** (if needed)
   - [ ] Export from Supabase
   - [ ] Import to Firestore

## Files Modified/Created

### Backend
- ✅ `backend/models/prompt_models.py` (new)
- ✅ `backend/services/prompt_service.py` (new)
- ✅ `backend/routes/prompt_routes.py` (new)
- ✅ `backend/main.py` (updated - added router)
- ✅ `backend/models/__init__.py` (updated - exports)

### Frontend
- ⏳ `components/PromptManagement/` (to be created)
- ⏳ `App.tsx` (to be updated - add routing)
- ⏳ `services/promptService.ts` (to be created)

## API Compatibility

The new API endpoints are compatible with the Prompt Management App's expected API shape. The main differences:

1. **Base URL**: Changed from Supabase Edge Functions to agentnav backend
   - Old: `https://{project}.supabase.co/functions/v1/make-server-1e807e45`
   - New: `https://{agentnav-backend}/api/prompts`

2. **Authentication**: Currently placeholder, needs implementation

3. **Response Format**: Same structure, just using Firestore instead of KV store

## Troubleshooting

### Backend Errors

**"Firestore client not initialized"**
- Check `FIRESTORE_PROJECT_ID` and `FIRESTORE_DATABASE_ID` environment variables
- Verify Firestore is enabled in GCP project

**"Prompt not found"**
- Check Firestore collection name matches `prompts_collection` in `prompt_service.py`
- Verify document ID format

### Frontend Errors

**"CORS error"**
- Update CORS_ORIGINS in backend/main.py
- Check Cloud Run CORS settings

**"Authentication failed"**
- Implement proper authentication (currently placeholder)
- Check Authorization header format

## Support

For issues or questions:
1. Check backend logs in Cloud Run
2. Check Firestore console for data
3. Review API documentation at `/docs` endpoint

