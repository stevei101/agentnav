# Cloud Run Hackathon Quick Reference

## For Agentic Navigator

---

## ?? Your Category: AI Agents

**Requirements:**

- ? Built with Google ADK
- ? Multi-agent system (4 agents)
- ? Deployed to Cloud Run
- ? Agents communicate via A2A Protocol

---

## ?? Submission Requirements

### Must Have (All Required)

1. **Text Description** - Project summary, features, tech stack
2. **Demo Video** - 3 minutes max, walkthrough of project
3. **Public Code Repo** - GitHub repository (public)
4. **Architecture Diagram** - Visual representation of system
5. **Try it Out Link** - Deployed application URL

### Bonus Points (Optional)

**Google Cloud (+0.4 max):**

- ? Google AI Models (+0.2) - Using Gemini
- ? Multiple Cloud Run Services (+0.2) - Frontend + Backend

**Developer Contributions (+0.4 each):**

- Blog post/video (+0.4) - Must say "Created for Cloud Run Hackathon"
- Social media post (+0.4) - Use #CloudRunHackathon

---

## ?? Judging Criteria

1. **Technical Implementation (40%)**
   - Clean, efficient code
   - Cloud Run best practices
   - Production-ready features
   - User-friendly interface

2. **Demo & Presentation (40%)**
   - Clear problem statement
   - Effective solution presentation
   - Architecture documentation
   - Cloud Run usage explanation

3. **Innovation & Creativity (20%)**
   - Novel approach
   - Significant problem solved
   - Efficient solution

---

## ? Pre-Submission Checklist

### Code

- [ ] Repository is public
- [ ] Code is commented
- [ ] README.md complete
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Health checks working

### Deployment

- [ ] Frontend deployed to Cloud Run
- [ ] Backend deployed to Cloud Run
- [ ] Both services accessible
- [ ] API docs accessible
- [ ] Firestore configured

### Documentation

- [ ] Architecture diagram created
- [ ] Setup guide written
- [ ] API documentation available
- [ ] Submission text written

### Video

- [ ] Video recorded (3 min max)
- [ ] Shows live demo
- [ ] Explains architecture
- [ ] Demonstrates Cloud Run usage

### Bonus

- [ ] Blog post published (optional)
- [ ] Social media post (optional)
- [ ] Both include hackathon mention

---

## ?? Quick Commands

```bash
# Development
make setup    # Initial setup
make up       # Start services
make logs     # View logs
make test     # Run tests

# Deployment
gcloud run deploy agentnav-frontend --image=...
gcloud run deploy agentnav-backend --image=...

# Verification
make health   # Check service health
curl http://localhost:8080/healthz
```

---

## ?? Documentation Links

- **Full Submission Guide:** `docs/HACKATHON_SUBMISSION_GUIDE.md`
- **Architecture Diagram:** `docs/ARCHITECTURE_DIAGRAM_GUIDE.md`
- **GCP Setup:** `docs/GCP_SETUP_GUIDE.md`
- **Setup Checklist:** `docs/HACKATHON_SETUP_CHECKLIST.md`

---

## ?? Important Links

- **Devpost:** https://run.devpost.com/
- **Submission Page:** https://run.devpost.com/submissions/new
- **Resources:** https://run.devpost.com/resources
- **Rules:** https://run.devpost.com/rules

---

## ?? Key Points to Highlight

### In Your Submission Text:

1. **Problem:** Information overload, need intelligent analysis
2. **Solution:** Multi-agent collaboration mimicking human teams
3. **Technology:** Cloud Run, ADK, A2A Protocol, Gemini, Firestore
4. **Innovation:** First multi-agent system using ADK on Cloud Run

### In Your Demo Video:

1. Show agent collaboration in real-time
2. Demonstrate Cloud Run deployment
3. Show Firestore integration
4. Highlight scalability benefits

### In Your Architecture Diagram:

1. Show both Cloud Run services
2. Show all 4 agents
3. Show A2A Protocol communication
4. Show Firestore and Gemini integration

---

## ?? Common Mistakes to Avoid

- ? Forgetting to make repo public
- ? Missing architecture diagram
- ? Video over 3 minutes
- ? Not testing public URLs
- ? Forgetting #CloudRunHackathon hashtag
- ? Not mentioning hackathon in blog posts

---

**Good luck! ??**
