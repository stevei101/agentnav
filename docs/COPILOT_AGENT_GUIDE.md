# Copilot Agent Guide: Using the agentnav-copilot-agent

**Feature:** Custom GitHub Copilot Agent Integration  
**Status:** Active  
**Agent Name:** `agentnav-copilot-agent`  
**Last Updated:** 2024-11-02

---

## Overview

The **agentnav-copilot-agent** is a custom GitHub Copilot agent specifically trained on the complete Agentic Navigator system architecture, policies, and best practices. This agent serves as your immediate, context-aware development assistant, ensuring all code contributions comply with project standards.

### What Makes This Agent Special?

Unlike general-purpose AI coding assistants, the agentnav-copilot-agent has deep, authoritative knowledge of:

- **Multi-Agent Architecture**: ADK (Agent Development Kit), A2A Protocol, and agent communication patterns
- **Cloud Run Deployment**: GPU support, container configuration, environment variables, health checks
- **Infrastructure as Code**: Terraform Cloud patterns, Workload Identity Federation (WIF), Workload Identity (WI)
- **Quality Policies**: **Mandatory 70% test coverage** for all new code
- **Technology Stack**: React/TypeScript/Vite/Tailwind (frontend), FastAPI/Python/ADK (backend)
- **Security Best Practices**: WIF over static keys, Secret Manager, least-privilege IAM
- **Development Tooling**: bun (frontend), uv (backend), Podman (containers)

---

## How to Invoke the Agent

### In GitHub Issues and Pull Requests

Mention the agent in comments to get assistance:

```markdown
@agentnav-copilot-agent Can you review this code for Cloud Run compatibility?
```

```markdown
@agentnav-copilot-agent How should I implement the Linker Agent's call to the Gemma GPU Service?
```

### In GitHub Copilot Chat (IDE)

If using GitHub Copilot in your IDE (VS Code, etc.), you can reference the agent's knowledge:

```
@agentnav-copilot-agent Generate a React component for AgentCard following the RORO pattern
```

```
@agentnav-copilot-agent What environment variables are required for the Backend Service?
```

---

## Common Use Cases

### 1. Code Generation

**Example Query:**
```
@agentnav-copilot-agent Generate a FastAPI route for analyzing a document with Pydantic DTOs
```

**What the Agent Will Do:**
- Generate code using the RORO (Receive Object, Return Object) pattern
- Include proper Pydantic models for validation
- Use async handlers
- Follow FastAPI best practices

---

### 2. Policy Enforcement

**Example Query:**
```
@agentnav-copilot-agent Review this Python file for Cloud Run readiness
```

**What the Agent Will Check:**
- Does the code read the `PORT` environment variable?
- Is the host binding set to `0.0.0.0` (not `127.0.0.1`)?
- Is there a `/healthz` endpoint implemented?
- Does the code log to stdout/stderr?
- Does the code handle SIGTERM gracefully?

---

### 3. Architectural Guidance

**Example Query:**
```
@agentnav-copilot-agent How does the Linker Agent get its embeddings?
```

**Expected Response:**
The agent will explain that the Linker Agent calls the **Gemma GPU Service** via the secure HTTP client located in `backend/services/`, and that embeddings are generated using the Gemma model running on Cloud Run with NVIDIA L4 GPU in the `europe-west1` region.

---

### 4. Testing and Coverage

**Example Query:**
```
@agentnav-copilot-agent What is the test coverage requirement for this PR?
```

**Expected Response:**
The agent will cite the **mandatory 70% test coverage** requirement and explain that all new or modified code must meet this threshold before merging.

---

### 5. Tooling Guidance

**Example Query:**
```
@agentnav-copilot-agent Which tool should I use to install Python dependencies?
```

**Expected Response:**
The agent will mandate the use of **`uv`** for Python dependency resolution and installation, explaining that `pip` is only used for the PyTorch base image in the Gemma GPU service.

---

### 6. Security and Authentication

**Example Query:**
```
@agentnav-copilot-agent What's the difference between WIF and WI?
```

**Expected Response:**
The agent will explain:
- **Workload Identity Federation (WIF)**: Used for GitHub Actions CI/CD to authenticate to GCP without static keys
- **Workload Identity (WI)**: Used for Cloud Run services to access GCP resources (Firestore, Secret Manager) at runtime using their Service Account

---

## Agent Responsibilities Summary

| Task | What the Agent Does |
|:-----|:--------------------|
| **Code Generation** | Generates code adhering to React/TypeScript/Tailwind/RORO patterns (frontend) or FastAPI/Pydantic/ADK patterns (backend) |
| **Policy Enforcement** | Warns if `PORT` env var is ignored, host is not `0.0.0.0`, or 70% coverage is not met |
| **Architectural Guidance** | Explains ADK agents, A2A Protocol, Firestore schema, deployment architecture |
| **Tooling Guidance** | Directs to use `bun` (frontend), `uv` (backend), Podman (containers), Terraform Cloud (IaC) |
| **Security Review** | Enforces WIF/WI patterns, Secret Manager usage, least-privilege IAM |
| **Code Review** | Reviews PRs for compliance with system standards, quality gates, and best practices |

---

## Testing the Agent

To verify the agent is working correctly, try these test queries:

### Test 1: Environment Variable Query
```
@agentnav-copilot-agent What environment variable is used to configure the Gemma Service URL?
```

**Expected Response:**  
The agent should identify `GEMMA_SERVICE_URL` as the environment variable used by the Backend Service to communicate with the Gemma GPU Service.

---

### Test 2: Coverage Policy Query
```
@agentnav-copilot-agent What is the test coverage requirement?
```

**Expected Response:**  
The agent should cite the **70% test coverage** requirement as a mandatory quality gate for all new or modified code.

---

### Test 3: Deployment Region Query
```
@agentnav-copilot-agent Which region is used for the Gemma GPU service and why?
```

**Expected Response:**  
The agent should explain that the Gemma GPU service is deployed in the **`europe-west1`** region because it supports NVIDIA L4 GPU instances on Cloud Run.

---

## Integration with Development Workflow

### During Development

1. **Before Writing Code**: Ask the agent for architectural guidance or code examples
2. **While Writing Code**: Use the agent to generate boilerplate or check patterns
3. **Before Committing**: Ask the agent to review your changes for compliance

### During Code Review

1. **Self-Review**: Ask the agent to review your PR before requesting human review
2. **Reviewer Assistance**: Reviewers can invoke the agent to verify compliance with policies
3. **Clarification**: Use the agent to answer questions about architecture or patterns

### During Debugging

1. **Cloud Run Issues**: Ask the agent about Cloud Run compatibility requirements
2. **Agent Communication**: Ask about A2A Protocol message formats
3. **Firestore Queries**: Ask about the Firestore schema and query patterns

---

## Agent Knowledge Base

The agent's knowledge is sourced from the authoritative **System Instruction** document located at `docs/SYSTEM_INSTRUCTION.md`. This document is kept in sync with the agent's training data to ensure consistency.

### Key Knowledge Areas

1. **Infrastructure Components**
   - Google Cloud Run (serverless, GPU support)
   - Google Artifact Registry (GAR)
   - Firestore (session memory, knowledge caching)
   - Secret Manager (credentials storage)
   - Cloud DNS & TLS (domain management)

2. **Application Components**
   - Frontend: React, TypeScript, Vite, Tailwind CSS
   - Backend: FastAPI, Python, ADK, A2A Protocol
   - Gemma GPU Service: PyTorch, Transformers, CUDA

3. **Multi-Agent Architecture**
   - Orchestrator Agent (team lead)
   - Summarizer Agent (content analyst)
   - Linker Agent (relationship mapper)
   - Visualizer Agent (graph generator)

4. **Deployment Pipeline**
   - GitHub Actions (CI/CD triggers)
   - Workload Identity Federation (secure authentication)
   - Terraform Cloud (IaC state management)
   - Podman (container builds)
   - Cloud Run (serverless deployment)

5. **Quality Policies**
   - **70% test coverage** (mandatory)
   - Cloud Run compatibility (PORT, 0.0.0.0, /healthz)
   - RORO pattern (Receive Object, Return Object)
   - Type safety (TypeScript, Pydantic)
   - Security (WIF, WI, Secret Manager)

---

## Limitations and Best Practices

### What the Agent Can Do

✅ Answer questions about the Agentic Navigator architecture  
✅ Generate code snippets following project patterns  
✅ Review code for compliance with policies  
✅ Explain deployment configurations and environment variables  
✅ Guide on tooling choices (bun, uv, Podman, Terraform)  

### What the Agent Cannot Do

❌ Execute code or run tests  
❌ Deploy infrastructure or services  
❌ Access live systems or production data  
❌ Modify repository files directly (requires human approval)  

### Best Practices

1. **Be Specific**: Provide context and code snippets when asking questions
2. **Ask Focused Questions**: Break complex questions into smaller, focused queries
3. **Verify Responses**: Always verify the agent's responses, especially for critical decisions
4. **Provide Feedback**: If the agent's response is incorrect, provide feedback to improve future responses
5. **Use for Review**: Use the agent as a first-pass reviewer before requesting human review

---

## Troubleshooting

### Agent Not Responding

- Ensure you're using the correct mention format: `@agentnav-copilot-agent`
- Check that you're in a GitHub issue, PR, or Copilot Chat context where the agent is available

### Agent Gives Incorrect Information

- Verify the agent's knowledge is up-to-date by checking `docs/SYSTEM_INSTRUCTION.md`
- Report discrepancies by creating an issue with the label `documentation`

### Agent Doesn't Understand Query

- Rephrase your question with more context
- Break complex queries into smaller, focused questions
- Reference specific files or components by path

---

## Updating the Agent

The agent's knowledge base is stored in `.github/agents/agentnav-gh-copilot-agent.md` and should be kept in sync with `docs/SYSTEM_INSTRUCTION.md`.

### When to Update

- When system architecture changes significantly
- When new policies or requirements are added (e.g., coverage thresholds)
- When new components or services are introduced
- When deployment patterns or tooling changes

### How to Update

1. Update `docs/SYSTEM_INSTRUCTION.md` with the new information
2. Regenerate `.github/agents/agentnav-gh-copilot-agent.md` from the updated system instruction
3. Test the agent with sample queries to verify the updates are reflected
4. Commit both files together to maintain consistency

---

## Success Criteria

The agent is considered successful if it can:

- ✅ Correctly identify `GEMMA_SERVICE_URL` as a backend environment variable
- ✅ Quote the **70% test coverage** requirement when asked about testing
- ✅ Explain the difference between WIF (CI/CD) and WI (runtime authentication)
- ✅ Generate code that follows project patterns (RORO, TypeScript types, Pydantic models)
- ✅ Identify Cloud Run compatibility issues (PORT, 0.0.0.0, /healthz)

---

## Additional Resources

- **System Instruction**: `docs/SYSTEM_INSTRUCTION.md` (authoritative architecture reference)
- **Contribution Guide**: `docs/CONTRIBUTION_GUIDE_PR_DISCIPLINE.md` (PR standards)
- **Testing Strategy**: `docs/TESTING_STRATEGY.md` (testing and quality gates)
- **A2A Protocol**: `docs/A2A_PROTOCOL_INTEGRATION.md` (agent communication)
- **GPU Setup**: `docs/GPU_SETUP_GUIDE.md` (Gemma GPU service deployment)

---

**Questions or Feedback?**

If you have questions about using the agentnav-copilot-agent or suggestions for improvement, please create an issue with the label `documentation` or `developer-experience`.
