# Prompt Management Guide

## Agentic Navigator - Externalized Prompt Management

**Feature:** FR #003 - Externalized Prompt Management via Firestore & AI Studio Compliance  
**Status:** ✅ Implemented

---

## 📋 Overview

Agentic Navigator uses **externalized prompt management** to store all agent system instructions and complex prompts in Firestore. This enables:

- ✅ **Live Iteration** - Update prompts without code changes or redeploys
- ✅ **AI Studio Compliance** - Share prompts for hackathon submission
- ✅ **Single Source of Truth** - Centralized prompt configuration
- ✅ **Version Tracking** - Track prompt changes over time
- ✅ **Environment Isolation** - Separate prompts for dev/staging/prod

---

## 🏗️ Architecture

### Components

1. **Firestore Collection:** `agent_prompts/`
2. **PromptLoaderService:** Loading & caching service
3. **FirestoreClient:** Database connection management
4. **Agent Integration:** Agents load prompts dynamically

### Data Flow

```
┌─────────────────┐
│  Agent Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  PromptLoaderService            │
│  ├─ Check Cache (5min TTL)      │
│  ├─ Load from Firestore         │
│  └─ Cache Result                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Agent Uses     │
│  Prompt Template│
└─────────────────┘
```

---

## 📝 Firestore Schema

### Collection: `agent_prompts/`

**Document Structure:**

```json
{
  "prompt_text": "Generate a {viz_type} visualization...\nContent:\n{content}\n...",
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-11-01T00:00:00Z",
  "version": 1,
  "metadata": {
    "agent_name": "visualizer",
    "prompt_type": "graph_generation"
  }
}
```

**Document IDs:**

- `visualizer_graph_generation` - Visualizer Agent prompt
- `orchestrator_system_instruction` - Orchestrator Agent prompt
- `summarizer_system_instruction` - Summarizer Agent prompt
- `linker_system_instruction` - Linker Agent prompt

### Naming Convention

**Format:** `{agent_name}_{prompt_type}`

- `agent_name`: Lowercase agent name (e.g., `visualizer`, `orchestrator`)
- `prompt_type`: Snake case description (e.g., `graph_generation`, `system_instruction`)

---

## 🔧 Local Development

### Prerequisites

1. Firestore emulator running (`make up`)
2. Python environment with dependencies installed

### Initial Setup

```bash
# Start services (includes Firestore emulator)
make up

# Set environment variables for emulator
export FIRESTORE_EMULATOR_HOST="localhost:8081"
export FIRESTORE_PROJECT_ID="agentnav-dev"
export FIRESTORE_DATABASE_ID="default"

# Seed prompts into Firestore
cd backend
source .venv/bin/activate
python scripts/seed_prompts.py
```

### Verify Setup

```bash
# Run tests
python test_prompt_loading.py

# Test API endpoint
curl -X POST http://localhost:8080/api/visualize \
  -H "Content-Type: application/json" \
  -d '{"document": "Test content"}'
```

---

## 🚀 Production Deployment

### Environment Variables

```bash
# Required
FIRESTORE_PROJECT_ID=your-gcp-project-id
FIRESTORE_DATABASE_ID=default

# Optional
FIRESTORE_EMULATOR_HOST=""  # Leave empty for production
ENVIRONMENT=production       # Enforces prompt loading
```

### Seed Prompts

Before deploying, ensure prompts are seeded in production Firestore:

```bash
# Set production environment variables
export FIRESTORE_PROJECT_ID="your-production-project"
unset FIRESTORE_EMULATOR_HOST  # Use production Firestore

# Seed prompts
python scripts/seed_prompts.py
```

### Critical: Production Safety

In production/staging environments, the system **enforces prompt loading**:

- ✅ Prompts **must** load from Firestore
- ❌ Fallback to hard-coded prompts **will raise RuntimeError**
- 🔒 Ensures prompt management discipline

---

## 🔄 Updating Prompts

### Via Firestore Console

1. Navigate to GCP Console → Firestore
2. Open `agent_prompts` collection
3. Click on the prompt document to edit
4. Update `prompt_text` field
5. Update `version` field (increment)
6. Click Save

**Result:** Changes reflected within 5 minutes (cache TTL)

### Via Seed Script

```bash
# Edit prompts in seed_prompts.py
vim backend/scripts/seed_prompts.py

# Re-run seed script (idempotent)
python scripts/seed_prompts.py
```

### Force Cache Refresh

```python
from services.prompt_loader import get_prompt_loader

# Reload specific prompt
loader = get_prompt_loader()
loader.reload_prompt("visualizer_graph_generation")

# Clear all cached prompts
loader.clear_cache()
```

---

## 🎓 Prompts Template Variables

Prompts use Python `.format()` string formatting:

```python
template = "Generate {viz_type} for {content}"
formatted = template.format(viz_type="MIND_MAP", content="text here")
```

### Example Prompt Structure

```python
FALLBACK_PROMPT = """Generate a {viz_type} visualization for the following content.

Content:
{content}

Return a JSON structure with:
- nodes: array of {{id, label, group}}
- edges: array of {{from, to, label}}

Focus on key concepts and their relationships."""
```

**Note:** Use `{{` and `}}` for literal braces in format strings.

---

## 🧪 Testing

### Unit Tests

```bash
# Run prompt loading tests
python test_prompt_loading.py

# Expected output:
# ✅ All tests passed (4/4)
```

### Manual Testing

```bash
# Test fallback behavior (no Firestore)
unset FIRESTORE_EMULATOR_HOST
python test_prompt_loading.py

# Test production safety
export ENVIRONMENT=production
python test_prompt_loading.py

# Should fail gracefully if Firestore unavailable
```

---

## 📊 Caching Strategy

### Cache Configuration

- **TTL:** 5 minutes
- **Storage:** In-memory (per-process)
- **Invalidation:** Automatic on TTL expiry

### Cache Behavior

1. **First Request:** Load from Firestore, cache result
2. **Subsequent Requests:** Serve from cache
3. **After TTL:** Next request reloads from Firestore
4. **Manual Invalidation:** Call `reload_prompt()` or `clear_cache()`

### Performance

- **Cache Hit:** < 1ms
- **Cache Miss:** < 500ms (Firestore read)
- **Firestore Read Cost:** Reduced by ~99% with caching

---

## 🔗 AI Studio Integration

### AI Studio Share App Setup

1. Create Google AI Studio project
2. Add system instructions for each agent
3. Create Share App
4. Store link in Secret Manager: `AI_STUDIO_SHARE_LINK`

### Sharing Prompts

Prompts in Firestore can be directly copied to AI Studio:

```bash
# View current prompts
# Use gcloud CLI or Firestore console
gcloud firestore documents get agent_prompts/visualizer_graph_generation \
  --project=agentnav-dev
```

---

## 🐛 Troubleshooting

### Prompt Not Loading

**Symptoms:** Fallback prompt used in development

**Diagnosis:**

```bash
# Check logs
make logs-backend

# Look for:
# ⚠️  Could not load prompt from Firestore: <error>
```

**Solutions:**

1. Verify Firestore emulator running: `make ps`
2. Check environment variables: `echo $FIRESTORE_EMULATOR_HOST`
3. Re-seed prompts: `python scripts/seed_prompts.py`

### Production Error

**Symptoms:** RuntimeError in production/staging

**Error Message:**

```
CRITICAL: Failed to load prompt from Firestore in production environment
```

**Solutions:**

1. Verify Firestore project ID correct
2. Check service account permissions
3. Ensure prompts are seeded in production
4. Review Cloud Run logs

### Cache Not Updating

**Symptoms:** Prompt changes not reflected after 5 minutes

**Solutions:**

1. Wait longer (TTL may not have expired)
2. Force reload: `loader.reload_prompt(prompt_id)`
3. Clear all cache: `loader.clear_cache()`
4. Restart service (forces full reload)

---

## 📚 Code Examples

### Using PromptLoaderService

```python
from services.prompt_loader import get_prompt

# Load a prompt
prompt = get_prompt("visualizer_graph_generation")

# Format with variables
formatted = prompt.format(
    viz_type="MIND_MAP",
    content="Document content here"
)
```

### Agent Integration

```python
class VisualizerAgent:
    def __init__(self):
        self._prompt_template = None

    def _get_prompt_template(self):
        if self._prompt_template:
            return self._prompt_template

        try:
            from services.prompt_loader import get_prompt
            self._prompt_template = get_prompt("visualizer_graph_generation")
            return self._prompt_template
        except Exception as e:
            # Fallback for development only
            if os.getenv("ENVIRONMENT") in ["production", "staging"]:
                raise RuntimeError(f"CRITICAL: Failed to load prompt: {e}")
            return FALLBACK_PROMPT
```

---

## ✅ Best Practices

1. **Always Version Prompts** - Increment version field on updates
2. **Test Changes Locally** - Use emulator before production
3. **Document Changes** - Note what changed and why
4. **Monitor Cache** - Watch for cache misses in logs
5. **Production Safety** - Never use fallback in production
6. **Backup Prompts** - Keep copies in version control

---

## 📈 Future Enhancements

- [ ] Prompt version history in Firestore
- [ ] Prompt A/B testing support
- [ ] Prompts UI for non-technical users
- [ ] Automated prompt validation
- [ ] Prompt analytics and usage tracking

---

**Last Updated:** November 1, 2025  
**Maintained By:** Agentic Navigator Team
