# WebSocket Streaming API Documentation

## Overview

The WebSocket Streaming API provides real-time, event-driven communication between frontend clients and the multi-agent backend system. This API enables the Interactive Agent Collaboration Dashboard (FR#020) to display live agent processing updates as documents are analyzed.

**Endpoint:** `ws://localhost:8000/api/v1/navigate/stream` (or `wss://` for HTTPS)

**Protocol:** WebSocket with JSON message format  
**Authentication:** None (development) / API Key or OAuth2 (production)

---

## Architecture

```
┌──────────────────┐
│  Frontend Client │
│  (DocumentUpload│
│   + Dashboard)   │
└────────┬─────────┘
         │ WebSocket
         │ Connect
         ▼
┌──────────────────────┐
│  FastAPI Server      │
│  /api/v1/navigate/   │
│    stream            │
└────────┬─────────────┘
         │
         ├─► Orchestrator Agent
         │   (queued event)
         │
         ├─► Summarizer Agent
         │   (processing event)
         │   (complete event)
         │
         ├─► Linker Agent
         │   (processing event)
         │   (complete event)
         │
         └─► Visualizer Agent
             (processing event)
             (complete event)

Events stream back to frontend in real-time
```

---

## Connection Lifecycle

### 1. Client Initiates Connection

```typescript
const ws = new WebSocket(
  'ws://localhost:8000/api/v1/navigate/stream?session_id=session-123456'
);

ws.onopen = () => {
  console.log('✅ Connected to streaming server');

  // Send analysis request
  ws.send(
    JSON.stringify({
      document: 'Document content to analyze...',
      content_type: 'document',
      include_metadata: true,
      include_partial_results: true,
    })
  );
};
```

### 2. Server Accepts Connection

- Generates or receives session ID
- Creates event emitter for the session
- Registers client for event streaming
- Initializes orchestrator workflow

### 3. Events Stream Continuously

- Agents process document
- Each status change emits an event
- Events queued for client delivery
- Client receives JSON messages

### 4. Client Disconnects

- Connection closes
- Server cleans up emitter and resources
- Events for closed connections discarded

---

## Message Format

### Client → Server

**Initial Request (required, sent once after connection)**

```json
{
  "document": "string (required) - Content to analyze",
  "content_type": "document | codebase (required) - Type of input",
  "include_metadata": "boolean (optional, default: true) - Include metadata in events",
  "include_partial_results": "boolean (optional, default: true) - Stream partial results"
}
```

**Example:**

```json
{
  "document": "# Machine Learning Overview\n\nML is a subset of AI...",
  "content_type": "document",
  "include_metadata": true,
  "include_partial_results": true
}
```

**Client Commands (optional, ongoing)**

```json
{
  "command": "pause | resume | cancel | get_status"
}
```

### Server → Client

**Agent Stream Event**

```json
{
  "id": "string - Unique event ID",
  "agent": "orchestrator | summarizer | linker | visualizer",
  "status": "queued | processing | complete | error",
  "timestamp": "ISO 8601 timestamp",
  "metadata": {
    "session_id": "string",
    "agent_type": "string",
    "event_sequence": "number"
  },
  "payload": {
    "summary": "string (optional) - Key summary or findings",
    "entities": ["string (optional) - Identified entities"],
    "relationships": [
      {
        "source": "string",
        "target": "string",
        "type": "string"
      }
    ],
    "visualization": {
      "nodes": ["object (optional) - Graph nodes"],
      "edges": ["object (optional) - Graph edges"]
    },
    "metrics": {
      "processingTime": "number - Time in ms",
      "tokensProcessed": "number",
      "entitiesFound": "number",
      "relationshipsFound": "number"
    },
    "error_message": "string (optional, only in error status)",
    "error_type": "string (optional, only in error status)"
  }
}
```

---

## Event Types & Status Codes

### Status: `queued`

**Emitted:** When agent is queued for processing

```json
{
  "id": "evt-001",
  "agent": "summarizer",
  "status": "queued",
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "session_id": "session-123456",
    "agent_type": "content_analyzer"
  }
}
```

### Status: `processing`

**Emitted:** When agent begins active processing

```json
{
  "id": "evt-002",
  "agent": "summarizer",
  "status": "processing",
  "timestamp": "2024-01-15T10:30:01Z",
  "metadata": {
    "session_id": "session-123456"
  },
  "payload": {
    "summary": "Extracting key themes..."
  }
}
```

### Status: `complete`

**Emitted:** When agent successfully completes

```json
{
  "id": "evt-003",
  "agent": "summarizer",
  "status": "complete",
  "timestamp": "2024-01-15T10:30:05Z",
  "metadata": {
    "session_id": "session-123456"
  },
  "payload": {
    "summary": "Document covers three main topics: A, B, and C.",
    "entities": ["Topic A", "Topic B", "Topic C"],
    "metrics": {
      "processingTime": 4000,
      "tokensProcessed": 1250,
      "entitiesFound": 3
    }
  }
}
```

### Status: `error`

**Emitted:** When agent encounters an error

```json
{
  "id": "evt-004",
  "agent": "visualizer",
  "status": "error",
  "timestamp": "2024-01-15T10:30:10Z",
  "metadata": {
    "session_id": "session-123456"
  },
  "payload": {
    "error_message": "Insufficient entities to create visualization",
    "error_type": "ValidationError",
    "metrics": {
      "processingTime": 2000
    }
  }
}
```

---

## Agent Types

### Orchestrator Agent

- **Role:** Task coordinator
- **Events:** Workflow initialization, agent delegation
- **Typical Flow:** `queued` → `processing` → `complete`

### Summarizer Agent

- **Role:** Content analysis and summarization
- **Events:** Content extraction, theme identification
- **Key Metrics:** tokensProcessed, entitiesFound
- **Payload:** summary, entities[]

```json
{
  "payload": {
    "summary": "Main conclusions and key points",
    "entities": ["Concept1", "Concept2", "Concept3"],
    "metrics": {
      "processingTime": 3500,
      "tokensProcessed": 2000,
      "entitiesFound": 15
    }
  }
}
```

### Linker Agent

- **Role:** Relationship mapping and knowledge linking
- **Events:** Entity linking, relationship discovery
- **Key Metrics:** entitiesFound, relationshipsFound
- **Payload:** entities[], relationships[]

```json
{
  "payload": {
    "entities": ["Entity1", "Entity2", "Entity3"],
    "relationships": [
      {
        "source": "Entity1",
        "target": "Entity2",
        "type": "references"
      }
    ],
    "metrics": {
      "processingTime": 2800,
      "entitiesFound": 12,
      "relationshipsFound": 8
    }
  }
}
```

### Visualizer Agent

- **Role:** Knowledge graph visualization
- **Events:** Graph generation, visual structure creation
- **Key Metrics:** processingTime, nodes/edges count
- **Payload:** visualization (nodes[], edges[])

```json
{
  "payload": {
    "visualization": {
      "nodes": [
        { "id": "n1", "label": "Concept", "type": "theme" },
        { "id": "n2", "label": "Related", "type": "entity" }
      ],
      "edges": [{ "source": "n1", "target": "n2", "type": "related_to" }]
    },
    "metrics": {
      "processingTime": 4200,
      "nodeCount": 25,
      "edgeCount": 18
    }
  }
}
```

---

## Client Integration Examples

### React Hook Usage

```typescript
import { useAgentStream } from '../hooks/useAgentStream';

function AnalysisDashboard() {
  const { events, isConnected, connect, disconnect, send } = useAgentStream({
    sessionId: "session-123",
    onEvent: (event) => {
      console.log(`Agent ${event.agent} - ${event.status}`);
    },
    autoConnect: false
  });

  const startAnalysis = (document: string) => {
    connect();

    // Send document after connection
    setTimeout(() => {
      send({
        document,
        content_type: "document",
        include_metadata: true
      });
    }, 100);
  };

  return (
    <div>
      <button onClick={() => startAnalysis(docContent)}>
        Start Analysis
      </button>
      <div>Connected: {isConnected ? "Yes" : "No"}</div>
      <div>Events: {events.length}</div>
    </div>
  );
}
```

### Vanilla JavaScript

```javascript
// Connect to stream
const ws = new WebSocket('ws://localhost:8000/api/v1/navigate/stream');

// Track connection state
let isConnected = false;
let eventCount = 0;

ws.onopen = () => {
  console.log('Connected');
  isConnected = true;

  // Send initial request
  ws.send(
    JSON.stringify({
      document: 'Your document content...',
      content_type: 'document',
    })
  );
};

// Handle events
ws.onmessage = event => {
  const data = JSON.parse(event.data);
  eventCount++;

  console.log(`Event ${eventCount}:`, {
    agent: data.agent,
    status: data.status,
    timestamp: data.timestamp,
  });

  // Update UI based on agent and status
  switch (data.status) {
    case 'queued':
      updateAgentStatus(data.agent, 'Queued...');
      break;
    case 'processing':
      updateAgentStatus(data.agent, 'Processing...');
      break;
    case 'complete':
      updateAgentStatus(data.agent, 'Complete ✓');
      displayResults(data.payload);
      break;
    case 'error':
      updateAgentStatus(data.agent, `Error: ${data.payload.error_message}`);
      break;
  }
};

ws.onerror = error => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
  isConnected = false;
};
```

---

## Response Codes & Error Handling

### Connection Errors

| Error              | Code | Description           | Recovery                       |
| ------------------ | ---- | --------------------- | ------------------------------ |
| Connection Refused | -    | Server not running    | Retry connection               |
| Invalid Session    | 400  | Bad session format    | Validate session ID            |
| Unauthorized       | 401  | Authentication failed | Check API key                  |
| Server Error       | 500  | Internal server error | Retry with exponential backoff |

### Message Errors

```json
{
  "status": "error",
  "payload": {
    "error": "ValidationError",
    "error_details": "Missing required field: document",
    "recoverable": true
  }
}
```

### Reconnection Strategy

The client should implement exponential backoff:

```typescript
const reconnect = (attempt: number) => {
  const delay = Math.min(1000 * Math.pow(2, attempt), 32000);
  setTimeout(() => {
    ws = new WebSocket(wsUrl);
  }, delay);
};
```

---

## Performance Considerations

### Message Throughput

- **Event Rate:** ~10-50 events per document analysis
- **Event Size:** 500 bytes - 5KB depending on payload
- **Total Stream Duration:** 5-30 seconds per document

### Optimizations

1. **Partial Results:** Enable with `include_partial_results: true` for faster feedback
2. **Metadata:** Disable with `include_metadata: false` to reduce message size
3. **Batching:** Server may batch multiple events in high-throughput scenarios
4. **Compression:** Consider WebSocket permessage-deflate for large payloads

---

## Monitoring & Debugging

### Enable Debug Logging

**Backend:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("stream_routes")
```

**Frontend:**

```javascript
window.DEBUG_STREAMS = true;
// In useAgentStream hook, will log all events
```

### Metrics to Track

- Connection establishment time
- Event latency (timestamp to reception)
- Error rate per agent
- Session completion time
- Memory usage under load

### Common Issues

| Issue              | Cause                      | Solution                                 |
| ------------------ | -------------------------- | ---------------------------------------- |
| No events received | Connection not established | Check WebSocket URL, port, CORS          |
| Partial events     | Network interruption       | Reconnection logic will retry            |
| Memory leak        | Events not cleared         | Call disconnect() on unmount             |
| Slow processing    | Large document             | Reduce document size or increase timeout |

---

## Deployment Notes

### Cloud Run Configuration

```bash
gcloud run deploy agentnav-backend \
  --region europe-west1 \
  --timeout 300s \
  --set-env-vars PORT=8080,ENABLE_STREAMING=true
```

### CORS Configuration

For frontend served from different origin:

```python
CORSMiddleware(
  allow_origins=["https://agentnav.lornu.com"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
```

### WebSocket Proxy Configuration (Nginx)

```nginx
location /api/v1/navigate/stream {
  proxy_pass http://backend:8080;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;
}
```

---

## API Versioning

**Current Version:** `1.0` (v1)

**Compatibility:** Breaking changes will increment major version (v2, v3, etc.)

**Future Enhancements:**

- Message compression
- Selective event filtering
- Client-side event caching
- Multi-document batch processing
- GPU acceleration metrics

---

## Security

### Development

- No authentication required
- CORS allows localhost origins
- WebSocket unencrypted (ws://)

### Production

- Require API key or OAuth2 token
- Use secure WebSocket (wss://)
- Implement rate limiting per session
- Log all connections for audit trail

---

## Troubleshooting

### WebSocket Won't Connect

1. Check server is running: `curl http://localhost:8000/health`
2. Verify URL format: `ws://` not `http://`
3. Check CORS headers if cross-origin
4. Verify firewall allows WebSocket traffic

### No Events After Connection

1. Ensure valid JSON in initial request
2. Check `document` field is not empty
3. Verify backend logs for processing errors
4. Try with simpler content first

### Intermittent Disconnections

1. Increase `--timeout` in Cloud Run deployment
2. Check network stability
3. Implement client-side reconnection logic
4. Monitor server resource usage

---

## Support & Examples

- **Frontend Examples:** `/docs/examples/streaming-dashboard.tsx`
- **Backend Examples:** `/backend/routes/stream_routes.py`
- **Test Suite:** `/backend/tests/test_stream_routes.py`
- **Issue Tracker:** GitHub Issues for agentnav repository

---

**Last Updated:** 2024-01-15  
**Maintained By:** Agentic Navigator Team  
**Status:** Stable (v1.0)
