# FR#020: Interactive Agent Collaboration Dashboard - Usage Guide

## Quick Start

### 1. Start Backend Server

```bash
cd backend
uv venv
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Start Frontend Dev Server

```bash
cd /workspaces/agentnav
bun run dev
```

### 3. Open Dashboard

Navigate to `http://localhost:5173` in your browser.

---

## Using the Dashboard

### Step 1: Upload Document

1. Click **"New Analysis"** tab
2. Select document type:
   - **Research Paper** - Academic articles, reports
   - **Technical Doc** - API docs, guides, specifications
   - **Codebase** - Source code, scripts, configuration
3. Upload one or more files via:
   - Click **"Browse Files"** button
   - Drag and drop files directly
4. Review selected files
5. Click **"Start Multi-Agent Analysis"**

### Step 2: View Real-Time Streaming

The dashboard automatically switches to the **"Dashboard"** tab showing:

- **Agent Cards** - Status of each agent (Summarizer, Linker, Visualizer)
- **Progress Indicators** - Real-time processing progress
- **Event Stream** - Raw events received from backend
- **Statistics Panel** - Connection status, event count, findings

### Step 3: Analyze Results

Once agents complete:
- **Summarizer Agent** displays key themes and summaries
- **Linker Agent** shows identified entities and relationships
- **Visualizer Agent** renders knowledge graph visualization

---

## Component Architecture

```
StreamingDashboard
├── DocumentUpload
│   ├── File input / drag-drop
│   ├── Document type selector
│   └── Agent pipeline info
│
└── AgentDashboard
    ├── WebSocket Connection (useAgentStream hook)
    ├── AgentCard (x3)
    │   ├── Status badge
    │   ├── Progress bar
    │   ├── Findings list
    │   └── Metrics display
    │
    ├── A2ACommunication
    │   └── Agent message log
    │
    ├── KnowledgeGraph
    │   └── Canvas visualization
    │
    ├── ResultsPanel
    │   ├── Summary export
    │   ├── Findings aggregation
    │   └── Share functionality
    │
    └── Statistics Panel
        ├── Connection status
        ├── Events received
        ├── Active agents
        └── Total findings
```

---

## WebSocket Event Flow

```
┌─ Client ──────────────┐
│                       │
│ 1. Connect WebSocket  │
│ 2. Send document      │
│    {document,         │
│     content_type}     │
└───────────┬───────────┘
            │
            ▼
    ┌─────────────────────┐
    │  Backend/FastAPI    │
    │                     │
    │  1. Accept conn     │
    │  2. Create emitter  │
    │  3. Start workflow  │
    │  4. Queue agents    │
    └─────────┬───────────┘
              │
              ├─ Orchestrator
              │  ├─ QUEUED (evt)
              │  ├─ PROCESSING (evt)
              │  └─ COMPLETE (evt)
              │
              ├─ Summarizer
              │  ├─ QUEUED (evt)
              │  ├─ PROCESSING (evt)
              │  ├─ COMPLETE (evt+findings)
              │  └─ emit_event()
              │
              ├─ Linker
              │  ├─ PROCESSING (evt)
              │  ├─ COMPLETE (evt+entities)
              │  └─ emit_event()
              │
              └─ Visualizer
                 ├─ PROCESSING (evt)
                 ├─ COMPLETE (evt+graph)
                 └─ emit_event()
              │
            Events stream back to frontend
            ▼
    ┌─────────────────────┐
    │   Frontend React    │
    │                     │
    │ - useAgentStream    │
    │ - Parse events      │
    │ - Update state      │
    │ - Render cards      │
    │ - Display results   │
    └─────────────────────┘
```

---

## Code Examples

### Example 1: Basic Document Analysis

```typescript
// User uploads a research paper
const document = `# Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence...`;

// Frontend sends to backend
const ws = new WebSocket('ws://localhost:8080/api/v1/navigate/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    document,
    content_type: "document",
    include_metadata: true
  }));
};

// Receive events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.agent === "summarizer") {
    if (data.status === "complete") {
      console.log("Summary:", data.payload.summary);
    }
  }
  
  if (data.agent === "linker") {
    if (data.status === "complete") {
      console.log("Entities:", data.payload.entities);
    }
  }
};
```

### Example 2: Using React Hook

```typescript
import { useAgentStream } from '../hooks/useAgentStream';

export function Dashboard() {
  const { events, isConnected, send, connect } = useAgentStream({
    sessionId: "session-123",
    autoConnect: false,
    onEvent: (event) => {
      console.log(`${event.agent}: ${event.status}`);
    }
  });

  const analyze = (doc: string) => {
    connect();
    
    setTimeout(() => {
      send({
        document: doc,
        content_type: "document"
      });
    }, 100);
  };

  return (
    <div>
      <button onClick={() => analyze(documentContent)}>
        Start Analysis
      </button>
      
      <p>Events: {events.length}</p>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
    </div>
  );
}
```

### Example 3: Error Handling

```typescript
const ws = new WebSocket('ws://localhost:8080/api/v1/navigate/stream');

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
  showErrorNotification("Connection failed");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.status === "error") {
    console.error(
      `Agent ${data.agent} failed: ${data.payload.error_message}`
    );
    
    showErrorNotification(
      `${data.agent} error: ${data.payload.error_message}`
    );
  }
};

ws.onclose = () => {
  // Implement reconnection logic
  setTimeout(() => {
    ws = new WebSocket('ws://localhost:8080/api/v1/navigate/stream');
  }, 3000);
};
```

### Example 4: Processing Multiple Files

```typescript
async function analyzeMultipleFiles(files: File[]) {
  const contents: string[] = [];

  for (const file of files) {
    const text = await file.text();
    contents.push(`--- File: ${file.name} ---\n${text}`);
  }

  const combinedDocument = contents.join("\n\n");

  const ws = new WebSocket('ws://localhost:8080/api/v1/navigate/stream');

  ws.onopen = () => {
    ws.send(JSON.stringify({
      document: combinedDocument,
      content_type: "codebase",  // Multiple code files
      include_metadata: true
    }));
  };
}
```

---

## Performance Tips

### 1. Optimize Document Size

```typescript
// ✅ GOOD: Reasonable size (< 50KB)
const document = largeText.substring(0, 50000);

// ❌ BAD: Too large (> 1MB)
const document = entireBookText;
```

### 2. Handle Events Efficiently

```typescript
// ✅ GOOD: Use event handler
useAgentStream({
  onEvent: (event) => {
    // Only process needed events
    if (event.status === "complete") {
      updateResults(event);
    }
  }
});

// ❌ BAD: Process all events
events.forEach(processEveryEvent);
```

### 3. Manage Memory

```typescript
// ✅ GOOD: Cleanup on unmount
useEffect(() => {
  return () => {
    disconnect();
  };
}, []);

// ❌ BAD: Leave connections open
// WebSocket will persist in memory
```

### 4. Use Appropriate Content Type

```typescript
// Document analysis
send({ 
  document,
  content_type: "document"
});

// Code analysis (enables syntax-aware parsing)
send({
  document: codeContent,
  content_type: "codebase"
});
```

---

## Troubleshooting

### Issue: WebSocket Connection Refused

**Symptom:** "Connection refused" or "Failed to construct 'WebSocket'"

**Solution:**
1. Verify backend is running: `curl http://localhost:8080/health`
2. Check correct URL format: `ws://` not `http://`
3. Verify CORS if running on different ports

### Issue: No Events After Connection

**Symptom:** Connected but no events received

**Solution:**
1. Check browser console for JavaScript errors
2. Verify document field is not empty
3. Check backend logs: `tail -f /var/log/agentnav.log`
4. Try with smaller document first

### Issue: Intermittent Disconnections

**Symptom:** Connection drops randomly during processing

**Solution:**
1. Increase backend timeout
2. Check network stability (ping backend)
3. Verify firewall/proxy not blocking WebSocket
4. Check server resource usage

### Issue: High Memory Usage

**Symptom:** Browser tab memory grows over time

**Solution:**
1. Clear events periodically: `events = events.slice(-100)`
2. Disconnect when not analyzing
3. Use browser dev tools to find memory leaks

---

## Advanced Configurations

### Custom Event Filtering

```typescript
const { events, onEvent } = useAgentStream({
  sessionId: "session-123",
  onEvent: (event) => {
    // Only process certain agents
    const targetAgents = ["summarizer", "visualizer"];
    if (targetAgents.includes(event.agent)) {
      handleEvent(event);
    }
  }
});
```

### Batch Processing

```typescript
const agentResults = {};

useAgentStream({
  onEvent: (event) => {
    if (!agentResults[event.agent]) {
      agentResults[event.agent] = [];
    }
    
    if (event.status === "complete") {
      agentResults[event.agent].push(event.payload);
    }
  }
});
```

### Export Results

```typescript
const exportResults = () => {
  const summary = {
    sessionId,
    timestamp: new Date().toISOString(),
    events: events.filter(e => e.status === "complete"),
    agents: agentStates
  };

  const json = JSON.stringify(summary, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis-${sessionId}.json`;
  link.click();
};
```

---

## Deployment Checklist

- [ ] Backend deployed to Cloud Run
- [ ] Frontend built and deployed to Cloud Run/Firebase
- [ ] WebSocket endpoint accessible: `wss://agentnav.lornu.com/api/v1/navigate/stream`
- [ ] CORS headers configured
- [ ] SSL/TLS certificates valid
- [ ] Rate limiting configured
- [ ] Monitoring and logging active
- [ ] Error handling tested
- [ ] Load testing completed

---

## Additional Resources

- **System Instruction:** `/docs/SYSTEM_INSTRUCTION.md`
- **API Documentation:** `/docs/STREAMING_API_GUIDE.md`
- **Backend Code:** `/backend/routes/stream_routes.py`
- **Frontend Components:** `/components/`
- **Test Suite:** `/backend/tests/test_stream_routes.py`

---

**Version:** 1.0  
**Last Updated:** 2024-01-15  
**Maintained By:** Agentic Navigator Team
