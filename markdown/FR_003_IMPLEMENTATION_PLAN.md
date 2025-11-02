# Feature Request #003: Implementation Plan

## Externalized Prompt Management via Firestore & AI Studio Compliance

**Status:** Planning  
**Started:** November 1, 2025

---

## 📋 Current State Analysis

### Current Agents Implemented

- ✅ **Visualizer Agent** - Fully implemented with hard-coded prompt
- ⏳ **Orchestrator Agent** - Not yet implemented (planned)
- ⏳ **Summarizer Agent** - Not yet implemented (planned)
- ⏳ **Linker Agent** - Not yet implemented (planned)

### Hard-Coded Prompt Identified

**Location:** `backend/agents/visualizer_agent.py` (lines 48-57)

```python
graph_prompt = f"""Generate a {viz_type} visualization for the following content.

Content:
{document[:MAX_PROMPT_LENGTH]}

Return a JSON structure with:
- nodes: array of {id, label, group}
- edges: array of {from, to, label}

Focus on key concepts and their relationships."""
```

### Firestore Setup

- ✅ Firestore dependency in `requirements.txt` (`google-cloud-firestore>=2.13.0`)
- ⏳ No Firestore client implementation yet
- ✅ Firestore schema documented in `docs/SYSTEM_INSTRUCTION.md`
- ❌ No `agent_prompts` collection yet

---

## 🎯 Implementation Strategy

### Phase 1: Foundation (Foundation)

1. Create Firestore client service
2. Design `agent_prompts` schema
3. Seed initial prompts from Visualizer Agent

### Phase 2: Core Feature (Externalization)

4. Create PromptLoaderService with caching
5. Update Visualizer Agent to use externalized prompts
6. Test with Firestore emulator

### Phase 3: Documentation & Compliance (Completion)

7. Document Firestore schema
8. Create AI Studio Share App link
9. Update documentation

---

## 📝 Detailed Implementation Steps

### Step 1: Create Firestore Client Service

**File:** `backend/services/firestore_client.py`

**Purpose:** Reusable Firestore client for all Firestore operations

**Features:**

- Singleton pattern
- Async/await support
- Emulator detection for local dev
- Environment-based configuration

**Dependencies:**

- `google-cloud-firestore`
- Environment variables: `FIRESTORE_PROJECT_ID`, `FIRESTORE_DATABASE_ID`, `FIRESTORE_EMULATOR_HOST`

### Step 2: Design agent_prompts Collection Schema

**Collection:** `agent_prompts`

**Document Structure:**

```json
{
  "prompt_text": "Generate a {viz_type} visualization for the following content.\n\nContent:\n{content}\n\nReturn a JSON structure...",
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-11-01T00:00:00Z",
  "version": 1,
  "metadata": {
    "agent_name": "visualizer",
    "prompt_type": "system_instruction"
  }
}
```

**Document IDs:**

- `visualizer_graph_generation`
- `orchestrator_system_instruction` (future)
- `summarizer_system_instruction` (future)
- `linker_system_instruction` (future)

### Step 3: Create PromptLoaderService

**File:** `backend/services/prompt_loader.py`

**Features:**

- Load prompts from Firestore by ID
- In-memory caching with TTL (e.g., 5 minutes)
- Fallback to default prompts if Firestore unavailable
- Logging and error handling

**Methods:**

- `get_prompt(prompt_id: str) -> str`
- `reload_prompt(prompt_id: str)` - Force reload from Firestore
- `clear_cache()` - Clear all cached prompts

### Step 4: Extract and Seed Prompts

**File:** `backend/scripts/seed_prompts.py` (new script)

**Purpose:** Initial data seeding script

**Action:**

1. Extract current Visualizer Agent prompt
2. Upload to Firestore `agent_prompts` collection
3. Verify successful upload

### Step 5: Update Visualizer Agent

**File:** `backend/agents/visualizer_agent.py`

**Changes:**

- Import PromptLoaderService
- Load prompt from Firestore on initialization
- Cache in agent instance
- Use prompt_template with dynamic variables

**Backward Compatibility:**

- Keep fallback to hard-coded prompt if Firestore unavailable
- Log warnings when using fallback

### Step 6: Local Testing Setup

**Requirements:**

- Firestore emulator running (`make up` should include it)
- Test prompt loading
- Test prompt updates
- Test caching behavior
- Test fallback mechanism

### Step 7: Documentation

**Files to Update:**

- `docs/SYSTEM_INSTRUCTION.md` - Add `agent_prompts` to Firestore schema
- `docs/local-development.md` - Document prompt management workflow
- `backend/README.md` - Add prompt management section

**New Documentation:**

- `markdown/FR_003_PROMPT_MANAGEMENT_GUIDE.md` - Complete guide

### Step 8: AI Studio Share App Setup

**Action:**

1. Create Google AI Studio project
2. Add all agent prompts as system instructions
3. Create Share App link
4. Store link in Secret Manager as `AI_STUDIO_SHARE_LINK`
5. Document in README

---

## 🧪 Testing Strategy

### Unit Tests

- `test_prompt_loader.py` - Test PromptLoaderService
- `test_firestore_client.py` - Test Firestore client
- Test caching behavior
- Test fallback mechanisms

### Integration Tests

- Test Visualizer Agent with Firestore
- Test prompt updates without restart
- Test emulator vs production

### Manual Testing

```bash
# Start services
make up

# Seed prompts
python backend/scripts/seed_prompts.py

# Test visualization endpoint
curl -X POST http://localhost:8080/api/visualize \
  -H "Content-Type: application/json" \
  -d '{"document": "Test content"}'

# Update prompt in Firestore
# Verify change reflected (after cache TTL)
```

---

## 📦 Deliverables

### Code Changes

- [ ] `backend/services/firestore_client.py` - Firestore client
- [ ] `backend/services/prompt_loader.py` - Prompt loading service
- [ ] `backend/agents/visualizer_agent.py` - Updated to use externalized prompts
- [ ] `backend/scripts/seed_prompts.py` - Initial data seeding
- [ ] Tests for all new services

### Documentation

- [ ] Updated Firestore schema documentation
- [ ] Prompt management guide
- [ ] Local development workflow documentation
- [ ] AI Studio Share App setup guide

### Data

- [ ] `agent_prompts` collection in Firestore
- [ ] All prompts seeded and validated
- [ ] AI Studio Share App created and linked

---

## ⚡ Quick Start Commands

### Development Setup

```bash
# Create branch
git checkout -b feature-003

# Start services
make up

# Install backend dependencies
cd backend && source .venv/bin/activate && uv pip install -r requirements.txt

# Run seed script
python scripts/seed_prompts.py

# Test API
curl http://localhost:8080/api/visualize
```

### Local Testing

```bash
# Run tests
make test-backend

# Check health
make health

# View logs
make logs-backend
```

---

## 🔍 Key Design Decisions

### 1. Caching Strategy

**Decision:** In-memory TTL cache (5 minutes)  
**Rationale:** Reduces Firestore read costs, maintains performance, allows updates within reasonable timeframe

### 2. Fallback Mechanism

**Decision:** Fallback to hard-coded prompts if Firestore unavailable  
**Rationale:** Ensures service resilience during outages, graceful degradation

### 3. Collection Naming

**Decision:** Use `agent_prompts` collection  
**Rationale:** Clear, descriptive, follows Firestore naming conventions

### 4. Document Structure

**Decision:** Single field `prompt_text` with metadata  
**Rationale:** Simple, flexible, easy to update via Firestore console

### 5. Version Control

**Decision:** Store version numbers in metadata  
**Rationale:** Enables tracking of prompt changes over time

---

## 🎯 Success Criteria

### Functional

- ✅ Visualizer Agent loads prompt from Firestore
- ✅ Prompt updates reflected without restart (after cache TTL)
- ✅ Fallback works when Firestore unavailable
- ✅ No breaking changes to existing API

### Performance

- ✅ Prompt loading < 10ms (cached)
- ✅ First load < 500ms (uncached)
- ✅ No impact on visualization latency

### Compliance

- ✅ AI Studio Share App link documented
- ✅ All prompts accessible via Firestore
- ✅ Prompt management process documented

---

## 🚀 Next Steps

1. **Start Development:** Create `feature-003` branch
2. **Build Foundation:** Firestore client service
3. **Core Feature:** PromptLoaderService
4. **Integration:** Update Visualizer Agent
5. **Testing:** Local development and Firestore emulator
6. **Documentation:** Complete guides and schemas
7. **AI Studio:** Create Share App
8. **PR:** Submit for review

---

**Ready to begin implementation! 🎉**
