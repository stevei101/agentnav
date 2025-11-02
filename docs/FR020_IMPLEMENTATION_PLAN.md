# FR#020: Interactive Agent Collaboration Dashboard - Implementation Plan

**Feature Request:** #020  
**Status:** Implementation & Planning  
**Timeline:** 3 Weeks  
**Priority:** Foundational / Highest

---

## Executive Summary

Transform the agentic navigator from a static "black box" form into an interactive "mission control" dashboard that streams real-time updates as the multi-agent team collaborates. Users will watch agents work in real-time, seeing the Summarizer handoff to the Linker, relationships discovered, and visualization generated—bringing the core project vision to life.

---

## Problem Statement

Current State Issues:
- ❌ Users see only a loading spinner—no transparency into agent work
- ❌ Backend orchestration is invisible; A2A Protocol magic is hidden
- ❌ No feedback on bottlenecks or failures
- ❌ Frontend is disconnected from the real multi-agent workflow (FR#005)

**Impact:** The UX betrays the project's core vision of an "intelligent research team in the cloud."

---

## Solution Architecture

### 1. Backend WebSocket Streaming API

**Endpoint:** `WebSocket /api/v1/navigate/stream`

**Flow:**
1. Client connects to WebSocket endpoint with document content
2. Backend initializes orchestrator workflow (from FR#005)
3. As each agent processes, backend emits status events to client
4. When workflow completes, client receives final results
5. Connection closes or client disconnects

**Event Message Schema:**

```json
{
  "id": "event_123",
  "agent": "summarizer | linker | visualizer | orchestrator",
  "status": "queued | processing | complete | error",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "metadata": {
    "elapsed_ms": 2345,
    "step": 2,
    "total_steps": 4
  },
  "payload": {
    "summary": "...",
    "entities": [...],
    "relationships": [...],
    "visualization": {...},
    "error": null,
    "error_details": null
  }
}
```

### 2. Pydantic Models (Backend)

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class AgentStatusEnum(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class AgentEventMetadata(BaseModel):
    """Metadata about event timing and progress"""
    elapsed_ms: int  # Milliseconds since workflow start
    step: int  # Current step (1-4)
    total_steps: int = 4
    agent_sequence: List[str] = ["orchestrator", "summarizer", "linker", "visualizer"]

class AgentEventPayload(BaseModel):
    """Payload data from agent processing"""
    summary: Optional[str] = None
    entities: Optional[List[str]] = None
    relationships: Optional[List[Dict[str, Any]]] = None
    visualization: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[str] = None
    partial_results: Optional[Dict[str, Any]] = None  # For streaming chunks

class AgentStreamEvent(BaseModel):
    """Complete WebSocket event message"""
    id: str  # Unique event ID
    agent: str  # Which agent generated this
    status: AgentStatusEnum
    timestamp: str  # ISO 8601 format
    metadata: AgentEventMetadata
    payload: AgentEventPayload
```

### 3. Frontend WebSocket Client Hook

**React Hook: `useAgentStream`**

```typescript
interface StreamEvent {
  id: string;
  agent: string;
  status: "queued" | "processing" | "complete" | "error";
  timestamp: string;
  metadata: EventMetadata;
  payload: EventPayload;
}

interface EventMetadata {
  elapsed_ms: number;
  step: number;
  total_steps: number;
  agent_sequence: string[];
}

interface EventPayload {
  summary?: string;
  entities?: string[];
  relationships?: any[];
  visualization?: any;
  error?: string;
  error_details?: string;
}

// Hook returns:
// - events: StreamEvent[] - all received events
// - isConnected: boolean - WebSocket connection state
// - error: string | null - connection or streaming error
// - connect: (document: string) => void - start streaming
// - disconnect: () => void - stop streaming
```

### 4. Interactive Dashboard Component

**Component Hierarchy:**

```
<InteractiveAgentDashboard>
  ├── <AgentTimeline>          # Visual timeline of agents
  │   ├── <AgentStep>          # Individual agent step
  │   ├── <AgentStep>
  │   └── ...
  ├── <EventStreamViewer>      # Real-time event log
  │   └── <EventItem>[] | <StreamingMetrics>
  └── <ResultsPreview>         # Live results as they arrive
      ├── <PartialSummary>
      ├── <EntitiesPreview>
      ├── <RelationshipsPreview>
      └── <VisualizationPreview>
```

**Key Features:**
- **Agent Timeline:** Visual representation of 4 agents with progress indicators
- **Live Event Log:** Scrollable list of all WebSocket events received
- **Streaming Metrics:** Duration, throughput, step timings
- **Results Preview:** Shows partial results as they arrive (summary chunk, entities list, etc.)
- **Error Handling:** Clear error messaging if any step fails

### 5. Integration with FR#005

**Modified Workflow:**

1. **Orchestrator** emits `queued` → `processing` → `complete` with metadata
2. **Summarizer** receives context, emits events:
   - `processing` when starting
   - `complete` with summary_text payload
3. **Linker** receives context, emits events:
   - `processing` when starting
   - `complete` with entities + relationships payload
4. **Visualizer** receives context, emits events:
   - `processing` when starting
   - `complete` with graph_json payload
5. **Final Event** combines all results, signals completion

---

## Implementation Phases

### Phase 1: Backend Infrastructure (Days 1-2)

- [ ] Create Pydantic models for WebSocket events
- [ ] Implement WebSocket endpoint with event queue
- [ ] Create EventEmitter class for workflow integration
- [ ] Add event emission to orchestrator_agent.py
- [ ] Add event emission to each agent (summarizer, linker, visualizer)
- [ ] Unit tests for event models

### Phase 2: Frontend WebSocket Client (Day 3)

- [ ] Implement `useAgentStream` React hook
- [ ] WebSocket connection management
- [ ] Event buffering and state management
- [ ] Error handling and reconnection logic

### Phase 3: Interactive Dashboard UI (Days 4-5)

- [ ] Create `InteractiveAgentDashboard` component
- [ ] Implement `AgentTimeline` sub-component
- [ ] Implement `EventStreamViewer` sub-component
- [ ] Implement `ResultsPreview` sub-component
- [ ] Styling with Tailwind CSS

### Phase 4: Integration & Testing (Days 6-7)

- [ ] Integration tests for full stream
- [ ] Update App.tsx to use new dashboard
- [ ] End-to-end testing (manual)
- [ ] Error scenarios (network failure, agent timeout, etc.)
- [ ] Performance testing (event throughput)

### Phase 5: Documentation & Polish (Days 8+)

- [ ] API documentation
- [ ] WebSocket protocol guide
- [ ] Frontend component docs
- [ ] Troubleshooting guide
- [ ] Demo/example code

---

## Technical Specifications

### WebSocket Endpoint Details

**Path:** `/api/v1/navigate/stream`

**Connection Parameters:**
```typescript
{
  document: string;
  content_type?: "document" | "codebase";
  include_metadata?: boolean;
  include_partial_results?: boolean;
}
```

**Server → Client Event Structure:**
```json
{
  "id": "evt_abc123",
  "agent": "summarizer",
  "status": "complete",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "metadata": {
    "elapsed_ms": 2345,
    "step": 2,
    "total_steps": 4,
    "agent_sequence": ["orchestrator", "summarizer", "linker", "visualizer"]
  },
  "payload": {
    "summary": "...",
    "entities": null,
    "relationships": null,
    "visualization": null,
    "error": null
  }
}
```

**Client → Server Commands:**
```json
{
  "action": "cancel" | "pause" | "resume"
}
```

### Error Handling

**Error Event Structure:**
```json
{
  "status": "error",
  "payload": {
    "error": "SummarizationError",
    "error_details": "Gemma service timeout after 30s",
    "agent": "summarizer",
    "recoverable": false
  }
}
```

**Error Types:**
- `ServiceUnavailable` - Backend service down
- `TimeoutError` - Agent exceeded time limit
- `ValidationError` - Invalid document input
- `WorkflowError` - Inter-agent communication failed

---

## File Changes Summary

### Backend Files (New/Modified)

**New Files:**
- `backend/models/stream_event_model.py` - Pydantic models for WebSocket events
- `backend/services/event_emitter.py` - EventEmitter service
- `backend/routes/stream_routes.py` - WebSocket endpoint

**Modified Files:**
- `backend/main.py` - Add WebSocket endpoint
- `backend/agents/orchestrator_agent.py` - Add event emission
- `backend/agents/summarizer_agent.py` - Add event emission
- `backend/agents/linker_agent.py` - Add event emission
- `backend/agents/visualizer_agent.py` - Add event emission

### Frontend Files (New/Modified)

**New Files:**
- `hooks/useAgentStream.ts` - WebSocket client hook
- `components/InteractiveAgentDashboard.tsx` - Main dashboard
- `components/AgentTimeline.tsx` - Agent progress visualization
- `components/EventStreamViewer.tsx` - Event log viewer
- `components/ResultsPreview.tsx` - Live results display

**Modified Files:**
- `App.tsx` - Route to new dashboard on stream trigger
- `services/backendService.ts` - Add stream endpoint helper

### Documentation Files

- `docs/FR020_IMPLEMENTATION.md` - Implementation details
- `docs/WEBSOCKET_PROTOCOL.md` - WebSocket protocol reference
- `docs/INTERACTIVE_DASHBOARD_GUIDE.md` - User guide

---

## Success Criteria

✅ **Functional Requirements:**
- [ ] WebSocket endpoint successfully streams events
- [ ] All 4 agents emit status events
- [ ] Events contain complete metadata and payload
- [ ] Frontend receives and displays events in real-time
- [ ] Dashboard updates as events arrive

✅ **Performance Requirements:**
- [ ] Event latency < 100ms
- [ ] Can handle 1000+ events per session
- [ ] No memory leaks in long-running streams

✅ **Reliability Requirements:**
- [ ] WebSocket connection recovery on disconnect
- [ ] Graceful error handling for failed agents
- [ ] Timeout handling (agent takes > 30s)
- [ ] Proper cleanup on client disconnect

✅ **User Experience Requirements:**
- [ ] Dashboard is visually engaging and interactive
- [ ] Timeline clearly shows agent progression
- [ ] Results update live as they become available
- [ ] Error messages are clear and actionable

---

## Dependencies & Compatibility

**Backend:**
- `fastapi` (already installed)
- `websockets` (need to add)
- `pydantic` (already installed)
- `asyncio` (standard library)

**Frontend:**
- `react` (already installed)
- `react-hooks` (standard with React)
- No additional external dependencies required

---

## Deployment Considerations

1. **WebSocket Support:** Cloud Run supports WebSocket via gRPC or custom HTTP/2 streaming
   - Use native WebSocket support (available in Cloud Run)
   - Max idle connection timeout: 1 hour

2. **Scaling:** WebSocket connections are stateful
   - Load balancer affinity required
   - Consider connection limits per instance
   - Monitor concurrent connection count

3. **Security:**
   - Validate document size (max 10MB)
   - Rate limit connections per IP
   - Use `wss://` for production
   - Validate session tokens if auth added later

---

## Future Enhancements

1. **Historical Event Playback** - Replay past workflows
2. **Export Workflow** - Download event transcript
3. **Workflow Comparison** - Compare multiple runs
4. **Custom Prompts** - Let users modify agent prompts in real-time
5. **Parallel Execution** - Show parallel agent execution
6. **Retry Logic** - Allow retrying failed agents
7. **Agent Insights** - Show reasoning/thinking from agents

---

## Acceptance Criteria (for PR)

- [ ] Backend WebSocket endpoint fully functional
- [ ] All agents emit status events
- [ ] Frontend dashboard displays real-time updates
- [ ] All tests passing
- [ ] Documentation complete
- [ ] No regressions in existing features
- [ ] Performance benchmarks met

---

## References

- **GitHub Issue:** #22 (FR#020)
- **Related Feature:** FR#005 (Sequential Workflow)
- **ADK/A2A Documentation:** docs/SYSTEM_INSTRUCTION.md
- **FastAPI WebSocket Guide:** https://fastapi.tiangolo.com/advanced/websockets/

