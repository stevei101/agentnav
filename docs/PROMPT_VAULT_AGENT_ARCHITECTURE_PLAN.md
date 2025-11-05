# Prompt Vault Agent Architecture Plan

**Feature:** Multi-Agent Architecture for Prompt Vault  
**Status:** Planning  
**Created:** November 2025  
**Related Issues:** TBD

---

## Overview

This document outlines the plan for implementing a **multi-agent architecture** for Prompt Vault using **Google's Agent Development Kit (ADK)** and the **Agent2Agent (A2A) Protocol**. This will enable intelligent prompt management, optimization, testing, and suggestion capabilities.

---

## Architecture Vision

### Current State
- **Frontend:** React/TypeScript with Supabase client
- **Backend:** Optional FastAPI backend (currently empty)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Google OAuth via Supabase

### Target State
- **Frontend:** React/TypeScript with Supabase client (unchanged)
- **Backend:** FastAPI with ADK multi-agent orchestration
- **Agents:** Specialized agents for prompt management tasks
- **Database:** Supabase (PostgreSQL) + Firestore (for agent state/session memory)
- **A2A Protocol:** Agent-to-agent communication for coordinated workflows
- **Model Integration:** Gemini API for agent reasoning

---

## Agent Architecture

### Proposed Agents

| Agent | Role | Responsibilities |
| :--- | :--- | :--- |
| **Prompt Optimizer Agent** | Enhancement specialist | Analyzes prompts for clarity, specificity, and effectiveness. Suggests improvements based on best practices. |
| **Prompt Tester Agent** | Quality assurance | Tests prompts against sample inputs/outputs. Validates prompt behavior and identifies edge cases. |
| **Prompt Analyzer Agent** | Content analyst | Analyzes prompt structure, identifies variables, dependencies, and patterns. Extracts metadata. |
| **Version Comparison Agent** | Change tracker | Compares prompt versions, highlights differences, and suggests which version performs better. |
| **Prompt Suggestion Agent** | Recommendation engine | Suggests similar prompts, alternative phrasings, or related prompts based on user's prompt library. |
| **Orchestrator Agent** | Workflow coordinator | Receives user requests, determines which agents to invoke, coordinates A2A Protocol communication. |

---

## Use Cases

### 1. Prompt Optimization Workflow

**User Action:** Clicks "Optimize Prompt" button

**Agent Flow:**
```
User → Orchestrator Agent
  ↓
Orchestrator → Prompt Analyzer Agent (via A2A)
  ↓
Analyzer → Prompt Optimizer Agent (via A2A, shares analysis)
  ↓
Optimizer → Returns optimized prompt + suggestions
  ↓
Orchestrator → Returns result to user
```

**Data Flow:**
1. Prompt Analyzer extracts structure, variables, intent
2. Prompt Optimizer uses analysis + best practices → generates improved version
3. Results stored in Supabase (prompt history)
4. Agent state stored in Firestore (session memory)

---

### 2. Prompt Testing Workflow

**User Action:** Clicks "Test Prompt" with sample inputs

**Agent Flow:**
```
User → Orchestrator Agent
  ↓
Orchestrator → Prompt Tester Agent (via A2A)
  ↓
Tester → Calls Gemini API with test inputs
  ↓
Tester → Analyzes outputs, identifies issues
  ↓
Tester → Returns test results + recommendations
  ↓
Orchestrator → Returns results to user
```

**Data Flow:**
1. Prompt Tester executes prompt against test cases
2. Results stored in Supabase (`test_results` table)
3. Agent state stored in Firestore

---

### 3. Version Comparison Workflow

**User Action:** Selects two prompt versions to compare

**Agent Flow:**
```
User → Orchestrator Agent
  ↓
Orchestrator → Version Comparison Agent (via A2A)
  ↓
Comparison Agent → Analyzes both versions
  ↓
Comparison Agent → Identifies differences, similarities
  ↓
Comparison Agent → (Optional) Runs both through Tester Agent
  ↓
Comparison Agent → Returns comparison report
  ↓
Orchestrator → Returns results to user
```

---

### 4. Prompt Suggestion Workflow

**User Action:** Views prompt, wants similar suggestions

**Agent Flow:**
```
User → Orchestrator Agent
  ↓
Orchestrator → Prompt Analyzer Agent (via A2A)
  ↓
Analyzer → Extracts prompt features, intent, tags
  ↓
Analyzer → Prompt Suggestion Agent (via A2A, shares analysis)
  ↓
Suggestion Agent → Queries Supabase for similar prompts
  ↓
Suggestion Agent → Uses Gemini to rank/refine suggestions
  ↓
Suggestion Agent → Returns ranked list of similar prompts
  ↓
Orchestrator → Returns results to user
```

---

## Technical Architecture

### Backend Structure

```
prompt-vault/backend/
├── main.py                 # FastAPI app entry point
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Base Agent class (ADK-compatible)
│   ├── orchestrator_agent.py
│   ├── prompt_optimizer_agent.py
│   ├── prompt_tester_agent.py
│   ├── prompt_analyzer_agent.py
│   ├── version_comparison_agent.py
│   └── prompt_suggestion_agent.py
├── routes/
│   ├── __init__.py
│   ├── prompt_routes.py    # CRUD operations (existing)
│   └── agent_routes.py     # NEW: Agent workflow endpoints
├── services/
│   ├── __init__.py
│   ├── supabase_client.py # Supabase connection
│   ├── firestore_client.py # Firestore for agent state
│   ├── gemini_service.py   # Gemini API client
│   └── a2a_protocol.py    # A2A Protocol implementation
├── models/
│   ├── __init__.py
│   ├── prompt_models.py   # Existing prompt models
│   └── agent_models.py    # NEW: Agent request/response models
└── requirements.txt
```

---

## Integration Points

### 1. Supabase (Primary Database)
- **Purpose:** Store prompts, versions, test results, user data
- **Collections/Tables:**
  - `prompts` - Prompt documents
  - `prompt_versions` - Version history
  - `test_results` - Test execution results
  - `users` - User authentication

### 2. Firestore (Agent State)
- **Purpose:** Store agent session state, workflow context, A2A Protocol messages
- **Collections:**
  - `agent_sessions/` - Active agent workflows per user
  - `agent_context/` - Shared context between agents
  - `a2a_messages/` - A2A Protocol message history

### 3. Gemini API
- **Purpose:** Agent reasoning, prompt optimization, testing, analysis
- **Integration:** Via `gemini_service.py` client
- **Usage:** Each agent calls Gemini for its specific task

---

## API Endpoints

### Agent Workflow Endpoints

**Base URL:** `/api/agents`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/agents/optimize` | POST | Optimize a prompt using Optimizer Agent |
| `/api/agents/test` | POST | Test a prompt using Tester Agent |
| `/api/agents/analyze` | POST | Analyze prompt structure using Analyzer Agent |
| `/api/agents/compare` | POST | Compare two prompt versions using Comparison Agent |
| `/api/agents/suggest` | POST | Get prompt suggestions using Suggestion Agent |
| `/api/agents/workflow/{workflow_id}` | GET | Get workflow status (A2A Protocol state) |

### Request/Response Examples

**Optimize Prompt:**
```json
POST /api/agents/optimize
{
  "prompt_id": "prompt-123",
  "prompt_text": "Write a blog post about {topic}",
  "optimization_goals": ["clarity", "specificity"]
}

Response:
{
  "workflow_id": "workflow-abc",
  "optimized_prompt": "Write a comprehensive, engaging blog post about {topic} that...",
  "suggestions": [
    "Consider adding length requirement",
    "Specify target audience"
  ],
  "status": "completed"
}
```

**Test Prompt:**
```json
POST /api/agents/test
{
  "prompt_id": "prompt-123",
  "test_cases": [
    {"input": {"topic": "AI"}, "expected_output": "..."}
  ]
}

Response:
{
  "workflow_id": "workflow-xyz",
  "test_results": [
    {
      "test_case": 1,
      "status": "passed",
      "output": "...",
      "issues": []
    }
  ],
  "overall_status": "passed",
  "recommendations": []
}
```

---

## A2A Protocol Implementation

### Message Structure

```python
class A2AMessage:
    sender: str  # Agent name
    recipient: str  # Agent name or "orchestrator"
    message_type: str  # "request", "response", "notification"
    payload: dict  # Agent-specific data
    workflow_id: str  # Tracks workflow session
    timestamp: datetime
```

### Example A2A Flow

**Prompt Optimization Workflow:**

1. **Orchestrator → Analyzer:**
   ```python
   {
     "sender": "orchestrator",
     "recipient": "analyzer",
     "message_type": "request",
     "payload": {
       "prompt_text": "Write a blog post about {topic}",
       "action": "analyze_structure"
     },
     "workflow_id": "workflow-abc"
   }
   ```

2. **Analyzer → Optimizer:**
   ```python
   {
     "sender": "analyzer",
     "recipient": "optimizer",
     "message_type": "response",
     "payload": {
       "prompt_structure": {
         "variables": ["topic"],
         "intent": "content_generation",
         "style": "informal"
       },
       "original_prompt": "..."
     },
     "workflow_id": "workflow-abc"
   }
   ```

3. **Optimizer → Orchestrator:**
   ```python
   {
     "sender": "optimizer",
     "recipient": "orchestrator",
     "message_type": "response",
     "payload": {
       "optimized_prompt": "...",
       "suggestions": [...],
       "analysis": {...}
     },
     "workflow_id": "workflow-abc"
   }
   ```

---

## Infrastructure Requirements

### Cloud Run Services

**New Service: `prompt-vault-backend`**
- **Region:** `europe-west1` (for Gemini API proximity)
- **CPU:** 2 vCPU
- **Memory:** 4Gi
- **Port:** 8080
- **Environment Variables:**
  - `PORT=8080`
  - `GEMINI_API_KEY` (from Secret Manager)
  - `SUPABASE_URL` (from Secret Manager)
  - `SUPABASE_SERVICE_KEY` (from Secret Manager)
  - `FIRESTORE_PROJECT_ID` (for agent state)
  - `FIRESTORE_DATABASE_ID`
  - `ADK_AGENT_CONFIG_PATH`
  - `A2A_PROTOCOL_ENABLED=true`

### Service Accounts

**New Service Account: `prompt-vault-backend@${PROJECT_ID}.iam.gserviceaccount.com`**
- **IAM Roles:**
  - `roles/secretmanager.secretAccessor` (Supabase secrets, Gemini API key)
  - `roles/datastore.user` (Firestore access for agent state)
  - `roles/aiplatform.user` (Gemini API access, if needed)

### Firestore Database

**New Firestore Instance (or use existing agentnav Firestore):**
- **Collections:**
  - `agent_sessions/` - Active workflows
  - `agent_context/` - Shared context
  - `a2a_messages/` - Message history

**Note:** Can share Firestore with agentnav (different collections) or use separate instance for isolation.

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up FastAPI backend structure
- [ ] Implement base Agent class (ADK-compatible)
- [ ] Set up Firestore client for agent state
- [ ] Set up Gemini service client
- [ ] Implement basic A2A Protocol message passing
- [ ] Create Orchestrator Agent skeleton

### Phase 2: Core Agents (Week 2)
- [ ] Implement Prompt Analyzer Agent
- [ ] Implement Prompt Optimizer Agent
- [ ] Implement Prompt Tester Agent
- [ ] Test agent-to-agent communication via A2A Protocol

### Phase 3: Advanced Agents (Week 3)
- [ ] Implement Version Comparison Agent
- [ ] Implement Prompt Suggestion Agent
- [ ] Add agent workflow orchestration logic
- [ ] Implement workflow status tracking

### Phase 4: API Integration (Week 4)
- [ ] Create agent workflow API endpoints
- [ ] Integrate with existing prompt CRUD routes
- [ ] Add workflow status endpoints
- [ ] Implement error handling and retries

### Phase 5: Frontend Integration (Week 5)
- [ ] Add "Optimize Prompt" UI button
- [ ] Add "Test Prompt" UI button
- [ ] Add "Compare Versions" UI
- [ ] Add "Suggest Similar" UI
- [ ] Display agent workflow status

### Phase 6: Testing & Deployment (Week 6)
- [ ] Write unit tests for agents (70% coverage requirement)
- [ ] Integration tests for A2A Protocol
- [ ] End-to-end workflow tests
- [ ] Deploy to Cloud Run
- [ ] Monitor agent performance

---

## Testing Strategy

### Unit Tests
- **Agent Tests:** Test each agent's core logic independently
- **A2A Protocol Tests:** Test message passing, routing, error handling
- **Service Tests:** Test Supabase, Firestore, Gemini clients

### Integration Tests
- **Workflow Tests:** Test complete workflows end-to-end
- **API Tests:** Test agent endpoints with mock data
- **Database Tests:** Test agent state persistence

### Coverage Requirement
- **Minimum:** 70% code coverage for all new code (mandatory)
- **Target:** 80%+ coverage for critical agent logic

---

## Security Considerations

### Authentication
- **User Authentication:** Use Supabase authentication (existing)
- **API Authentication:** Validate user tokens in agent endpoints
- **Service Account:** Use Workload Identity for GCP services

### Data Isolation
- **User Data:** Filter prompts/test results by user_id
- **Agent State:** Store agent sessions per user in Firestore
- **A2A Messages:** Include user_id in workflow_id for isolation

### API Keys
- **Gemini API Key:** Store in Secret Manager, inject via Cloud Run
- **Supabase Keys:** Store in Secret Manager
- **Firestore Credentials:** Use Workload Identity (no keys needed)

---

## Performance Considerations

### Caching Strategy
- **Prompt Cache:** Cache analyzed prompt structures (5min TTL)
- **Gemini Responses:** Cache optimization/test results (10min TTL)
- **Agent State:** Cache agent context in memory (per-request)

### Async Processing
- **Long Workflows:** Support async processing for complex workflows
- **Webhook Callbacks:** Optional webhook notifications when workflows complete
- **Queue System:** Consider Cloud Tasks for long-running workflows

### Rate Limiting
- **Gemini API:** Implement rate limiting per user
- **Agent Endpoints:** Rate limit agent API calls
- **Cost Control:** Monitor Gemini API usage per user

---

## Cost Estimation

### Gemini API Costs
- **Optimization:** ~$0.001-0.01 per prompt (depending on model)
- **Testing:** ~$0.01-0.05 per test run (multiple API calls)
- **Analysis:** ~$0.001-0.005 per prompt

### Firestore Costs
- **Agent State:** ~$0.06 per 100K reads, $0.18 per 100K writes
- **A2A Messages:** Minimal storage cost

### Cloud Run Costs
- **Backend Service:** ~$0.10-0.50 per hour (depending on traffic)
- **Cold Start:** First request may take 2-5 seconds

---

## Monitoring & Observability

### Metrics to Track
- **Agent Execution Time:** Per-agent performance
- **Workflow Completion Rate:** Success/failure rates
- **Gemini API Usage:** API calls, costs per user
- **A2A Message Count:** Protocol message volume
- **Error Rates:** Agent failures, API errors

### Logging
- **Agent Logs:** Log all agent decisions and A2A messages
- **Workflow Logs:** Track workflow execution paths
- **Error Logs:** Detailed error logging for debugging

### Alerts
- **High Error Rate:** Alert if agent failures > 5%
- **API Cost Spike:** Alert if Gemini usage exceeds threshold
- **Workflow Timeout:** Alert if workflows take > 60 seconds

---

## Future Enhancements

### Phase 2 Features
- [ ] **Prompt Templates:** Agent-generated prompt templates
- [ ] **A/B Testing:** Agent-managed prompt A/B tests
- [ ] **Auto-Optimization:** Continuous prompt improvement based on test results
- [ ] **Prompt Marketplace:** Agent-curated prompt library
- [ ] **Multi-Model Testing:** Test prompts against multiple models (Gemini, GPT-4, Claude)

### Advanced Capabilities
- [ ] **Prompt Chains:** Agent-managed multi-step prompt workflows
- [ ] **Prompt Versioning AI:** Agent suggests when to create new versions
- [ ] **Collaborative Prompting:** Multi-user prompt development with agent coordination
- [ ] **Prompt Analytics:** Agent-generated insights on prompt performance

---

## Related Documentation

- [PROMPT_VAULT_ISOLATION_PLAN.md](./PROMPT_VAULT_ISOLATION_PLAN.md) - Infrastructure isolation
- [A2A_PROTOCOL_INTEGRATION.md](./A2A_PROTOCOL_INTEGRATION.md) - A2A Protocol details
- [SYSTEM_INSTRUCTION.md](./SYSTEM_INSTRUCTION.md) - Overall system architecture
- [PROMPT_MANAGEMENT_GUIDE.md](./PROMPT_MANAGEMENT_GUIDE.md) - Prompt management in agentnav

---

## Open Questions

1. **Firestore Sharing:** Should prompt-vault use the same Firestore instance as agentnav, or separate?
   - **Recommendation:** Same instance, different collections (cost-efficient, easier management)

2. **Agent State Persistence:** How long should agent sessions persist in Firestore?
   - **Recommendation:** 24-hour TTL, auto-cleanup

3. **Workflow Timeout:** Maximum time for agent workflows?
   - **Recommendation:** 60 seconds for synchronous, 5 minutes for async

4. **Gemini Model Selection:** Which Gemini model to use per agent?
   - **Recommendation:** Start with `gemini-pro`, upgrade to `gemini-ultra` for optimization tasks

5. **A2A Protocol Storage:** Should A2A messages be stored permanently or ephemeral?
   - **Recommendation:** Store for 7 days for debugging, then auto-delete

---

## Success Criteria

### Phase 1 Success
- ✅ Backend structure created
- ✅ Base Agent class implemented
- ✅ A2A Protocol message passing works
- ✅ Orchestrator Agent can route requests

### Phase 2 Success
- ✅ Optimize, Test, and Analyze agents functional
- ✅ Agents can communicate via A2A Protocol
- ✅ Results stored in Supabase correctly

### Phase 3 Success
- ✅ All agents implemented and tested
- ✅ Workflow orchestration handles complex flows
- ✅ Frontend can trigger agent workflows

### Final Success
- ✅ 70%+ test coverage achieved
- ✅ All workflows functional in production
- ✅ Performance meets SLA (< 10s for simple workflows)
- ✅ Cost per workflow < $0.10

---

**Status:** Ready for review and implementation  
**Next Steps:** Review plan, create GitHub issues for each phase, start Phase 1 implementation

