# Auto-Scaling Metrics Demo Plan

**Created:** [Current Date]  
**Purpose:** Plan for showcasing Cloud Run auto-scaling in demo video  
**Related:** Agent Navigator Gap Analysis - Priority 1 Item 3  
**Effort:** Low (1 day)

---

## Objective

Demonstrate Cloud Run's auto-scaling capabilities in the hackathon submission demo video to showcase this key Cloud Run feature.

---

## Current Auto-Scaling Configuration

### Backend Service
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 10
- **Concurrency:** 80 requests per instance
- **Region:** europe-west1

### Frontend Service
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 10
- **Concurrency:** 80 requests per instance
- **Region:** us-central1

### Gemma GPU Service
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 2
- **Concurrency:** 1 request per instance
- **Region:** europe-west1

**Configuration Location:** `terraform/cloud_run.tf`

---

## Demo Video Script Section

### Auto-Scaling Demonstration (30-45 seconds)

**Narration:**
> "Agent Navigator leverages Cloud Run's automatic scaling capabilities. Let me show you how it responds to traffic."

**Visuals:**
1. **Cloud Console - Cloud Run Service Page** (5 seconds)
   - Show services: `agentnav-backend`, `agentnav-frontend`, `gemma-service`
   - Highlight current instance count (likely 0 or 1)

2. **Load Test Execution** (10 seconds)
   - Use `curl` or load testing tool to send multiple requests
   - Show terminal/command executing:
     ```bash
     # Send 50 concurrent requests
     for i in {1..50}; do
       curl -X POST https://agentnav-backend.run.app/api/analyze \
         -H "Content-Type: application/json" \
         -d '{"content": "Test document for scaling demo"}' &
     done
     ```

3. **Cloud Console - Metrics Dashboard** (15 seconds)
   - Show Cloud Run metrics page
   - Highlight:
     - **Instance Count** graph (showing scale-up)
     - **Request Count** graph (showing traffic spike)
     - **CPU Utilization** graph
     - **Request Latency** graph
   - Point out: "Notice how instances scale up automatically as traffic increases"

4. **Scale-Down Demonstration** (10 seconds)
   - Wait for traffic to subside
   - Show instance count decreasing back to 0 (or min)
   - Highlight: "And it scales back down to zero when idle, saving costs"

5. **Summary** (5 seconds)
   - Show final metrics snapshot
   - Highlight: "Automatic scaling with zero configuration - this is Cloud Run"

---

## Metrics to Capture

### Key Metrics to Show in Demo

1. **Instance Count**
   - Shows: 0 → 2-3 → 0 (scale up and down)
   - Time range: 2-3 minutes

2. **Request Count**
   - Shows: Spike in requests
   - Correlates with instance scaling

3. **CPU Utilization**
   - Shows: Resource usage per instance
   - Demonstrates efficient resource allocation

4. **Request Latency**
   - Shows: Consistent latency despite scaling
   - Demonstrates Cloud Run's load balancing

### Cloud Console Metrics Path

1. Navigate to: **Cloud Run** → **agentnav-backend** → **Metrics** tab
2. Select time range: **Last 5 minutes**
3. Enable graphs:
   - Instance count
   - Request count
   - CPU utilization
   - Request latency

---

## Tools for Load Testing

### Option 1: Simple curl Loop (Recommended for Demo)
```bash
# Simple concurrent requests
for i in {1..50}; do
  curl -X POST $BACKEND_URL/api/analyze \
    -H "Content-Type: application/json" \
    -d '{"content": "Test document"}' &
done
wait
```

### Option 2: Apache Bench (ab)
```bash
ab -n 100 -c 10 -p payload.json -T 'application/json' \
  https://agentnav-backend.run.app/api/analyze
```

### Option 3: Siege
```bash
siege -c 10 -t 30s -H 'Content-Type: application/json' \
  -f urls.txt
```

### Option 4: Custom Script
```python
import asyncio
import httpx

async def send_request():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://agentnav-backend.run.app/api/analyze",
            json={"content": "Test document"}
        )
        return response.status_code

async def load_test(concurrent=50):
    tasks = [send_request() for _ in range(concurrent)]
    results = await asyncio.gather(*tasks)
    print(f"Completed {len(results)} requests")

asyncio.run(load_test())
```

---

## Recording Tips

### Best Practices

1. **Prepare Script First**
   - Write narration script
   - Prepare command sequences
   - Test load generation locally

2. **Use Screen Recording**
   - OBS Studio (free)
   - QuickTime (macOS)
   - Windows Screen Recorder
   - Cloud Console screen recording

3. **Timing**
   - Start recording before executing load test
   - Keep Cloud Console metrics visible
   - Show real-time scaling happening

4. **Highlight Key Points**
   - Use mouse cursor or annotation to point out metrics
   - Add text overlays if needed
   - Keep narration clear and concise

5. **Edit for Clarity**
   - Speed up waiting periods (traffic spike)
   - Add arrows/annotations to highlight metrics
   - Keep total demo section under 45 seconds

---

## Integration with Full Demo Video

### Placement in Demo

**Suggested Order:**
1. Problem statement (30s)
2. Solution overview (30s)
3. Live demo of application (60s)
4. **Auto-scaling demonstration (45s)** ← This section
5. Architecture overview (30s)
6. Cloud Run features summary (15s)
7. Closing (15s)

**Total Video Length:** ~3.5 minutes (within 3-minute recommendation, slightly over is acceptable)

---

## Success Criteria

- [ ] Auto-scaling demonstrated clearly in video
- [ ] Instance count scaling shown (0 → multiple → 0)
- [ ] Metrics dashboard visible with key graphs
- [ ] Narration explains scaling behavior
- [ ] Total demo section under 45 seconds
- [ ] Clear visual demonstration of Cloud Run feature

---

## Alternative: Static Screenshots

If live demo is not feasible, use static screenshots:

1. **Before:** Show service with 0 instances
2. **During:** Show metrics during load (multiple instances)
3. **After:** Show scale-down back to 0
4. **Annotate:** Add arrows and text to explain scaling

**Pros:** More controlled, easier to edit  
**Cons:** Less dynamic, less impressive

---

## Next Steps

1. **Test Load Generation**
   - Choose load testing tool
   - Test with actual backend URL
   - Verify scaling behavior

2. **Prepare Recording Environment**
   - Set up screen recording software
   - Prepare Cloud Console dashboard
   - Write narration script

3. **Record Demo Section**
   - Execute load test
   - Record Cloud Console metrics
   - Capture scaling behavior

4. **Edit and Integrate**
   - Edit recording for clarity
   - Integrate into full demo video
   - Add annotations if needed

---

**Last Updated:** [Current Date]  
**Status:** Ready for Implementation  
**Estimated Time:** 1 day (4-6 hours)

