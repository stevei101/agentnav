# Copilot Agent Usage Guide

This guide explains how to use the **agentnav-copilot-agent**, a custom GitHub Copilot agent specifically trained on the Agentic Navigator system architecture and conventions.

## Overview

The `agentnav-copilot-agent` (also known as `@agentnav-gh-copilot-agent` on GitHub) is a context-aware AI assistant that has been loaded with the complete **Agentic Navigator System Instruction**. This agent serves as your immediate, always-available development assistant that understands:

- The complete technology stack (FastAPI, ADK, React, Bun, uv)
- Deployment architecture (Cloud Run, GPU, Terraform, WIF/WI)
- Quality policies (70% code coverage requirement)
- Security best practices (WIF over static keys, WI for runtime auth)
- Multi-agent architecture patterns (A2A Protocol)
- Project conventions (RORO pattern, MUST use `0.0.0.0` host binding)

## Why Use the Custom Agent?

Unlike general-purpose AI assistants, the agentnav-copilot-agent:

✅ **Enforces Project Policies:** Automatically checks for 70% test coverage, PORT environment variable usage, and `0.0.0.0` host binding  
✅ **Provides Context-Aware Answers:** Understands the full multi-agent architecture and can explain how components interact  
✅ **Generates Compliant Code:** Produces code that follows project conventions (RORO, TypeScript patterns, ADK best practices)  
✅ **Accelerates Onboarding:** Instantly transfers architectural knowledge to new contributors  
✅ **Reduces Review Cycles:** Catches policy violations before code review  

## How to Invoke the Agent

### In GitHub Comments

The agent can be invoked directly in:
- **Pull Request comments**
- **Issue comments**
- **Code review comments**

**Syntax:**
```
@agentnav-gh-copilot-agent [your question or request]
```

**Examples:**
```
@agentnav-gh-copilot-agent Review this code for Cloud Run compatibility
```
```
@agentnav-gh-copilot-agent How do I implement a new ADK agent?
```
```
@agentnav-gh-copilot-agent Generate a React component for displaying agent status
```

### In Your IDE (GitHub Copilot Extension)

If you have the GitHub Copilot extension installed:

1. Open the Copilot chat panel
2. Type `@agentnav-gh-copilot-agent` followed by your question
3. The agent will respond with context-aware guidance

## Common Use Cases

### 1. Code Generation

**Task:** Generate new code following project conventions

**Query:**
```
@agentnav-gh-copilot-agent Generate a React component for the AgentCard that displays agent name, status, and progress
```

**Expected Response:**
- TypeScript code with proper type annotations
- React functional component (not class-based)
- RORO pattern for props
- Tailwind CSS styling
- Early guard clauses
- Named export

---

### 2. Policy Enforcement / Code Review

**Task:** Check if code follows Cloud Run requirements

**Query:**
```
@agentnav-gh-copilot-agent Review this FastAPI application for Cloud Run compatibility:

[paste your code]
```

**Expected Response:**
- ✅ Checks if `PORT` environment variable is read
- ✅ Checks if host binding is `0.0.0.0` (not `127.0.0.1`)
- ✅ Checks if `/healthz` endpoint exists
- ✅ Warns about any missing Cloud Run best practices

---

### 3. Architectural Guidance

**Task:** Understand how components interact

**Query:**
```
@agentnav-gh-copilot-agent How does the Linker Agent get its embeddings from the Gemma GPU Service?
```

**Expected Response:**
- Explanation of the Linker Agent's role in the multi-agent architecture
- Details on the secure HTTP client call to the Gemma GPU Service
- Information about the A2A Protocol communication
- Reference to relevant environment variables (e.g., `GEMMA_SERVICE_URL`)
- Mention of authentication via Workload Identity (WI)

---

### 4. Tooling Guidance

**Task:** Confirm which tools to use for dependencies

**Query:**
```
@agentnav-gh-copilot-agent Which tool should I use to install Python dependencies?
```

**Expected Response:**
- **uv** is the mandated tool for Python dependency management
- Explanation: `uv` provides fast package resolution and installation
- Example command: `uv pip install -r requirements.txt`
- Warning: Do not use `pip` directly unless in PyTorch base image context (Gemma service)

---

### 5. Testing Requirements

**Task:** Understand testing policies

**Query:**
```
@agentnav-gh-copilot-agent What is the required test coverage for new code?
```

**Expected Response:**
- **70% or higher code coverage** is mandatory for all new code
- Coverage is enforced in the CI/CD pipeline via pytest (backend) and vitest (frontend)
- Explanation of how to run tests locally:
  - Frontend: `bun run test` or `make test-frontend`
  - Backend: `pytest --cov=. --cov-report=term` or `make test-backend`
- Reference to `docs/TESTING_STRATEGY.md` for detailed testing guidelines

---

### 6. Identity & Authentication

**Task:** Understand WIF vs WI

**Query:**
```
@agentnav-gh-copilot-agent What's the difference between Workload Identity Federation and Workload Identity?
```

**Expected Response:**
- **Workload Identity Federation (WIF):** Used for CI/CD (GitHub Actions → GCP authentication)
  - Eliminates static Service Account keys
  - Temporary, scoped access for deployments
- **Workload Identity (WI):** Used for runtime (Cloud Run services → GCP services authentication)
  - Automatic authentication via Cloud Run Service Accounts
  - No credentials in container images
- Both are mandatory security best practices for this project

---

### 7. Environment Configuration

**Task:** Understand required environment variables

**Query:**
```
@agentnav-gh-copilot-agent What environment variables are required for the backend service?
```

**Expected Response:**
List of required environment variables for the backend:
- `PORT` - Set automatically by Cloud Run (defaults to 8080)
- `GEMINI_API_KEY` - API key for Google Gemini models (from Secret Manager)
- `GEMMA_SERVICE_URL` - URL of the Gemma GPU service
- `FIRESTORE_PROJECT_ID` - GCP project ID for Firestore
- `FIRESTORE_DATABASE_ID` - Firestore database ID
- `ADK_AGENT_CONFIG_PATH` - Path to ADK agent configurations
- `A2A_PROTOCOL_ENABLED` - Set to `true` to enable A2A Protocol

---

## Best Practices for Using the Agent

### 1. Be Specific in Your Queries

❌ **Bad:** "How do I deploy?"  
✅ **Good:** "How do I deploy the backend service to Cloud Run with GPU support in europe-west1?"

### 2. Provide Context When Needed

When asking about specific code:
```
@agentnav-gh-copilot-agent Review this Python function for Cloud Run compatibility:

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8080)
```

### 3. Use the Agent for Pre-Commit Checks

Before submitting a PR, ask the agent to review your changes:
```
@agentnav-gh-copilot-agent Review these changes for compliance with project policies:

[paste your diff or describe your changes]
```

### 4. Combine with Documentation

The agent complements (not replaces) the documentation:
- Use the agent for **quick questions** and **real-time guidance**
- Refer to full documentation for **comprehensive references** and **detailed examples**

### 5. Learn from the Responses

The agent's responses are educational. They often include:
- **Why** certain patterns are used
- **Alternatives** that were considered
- **References** to relevant documentation

---

## Agent Limitations

### What the Agent CAN Do:

✅ Answer questions about the architecture  
✅ Generate code following project conventions  
✅ Review code for policy compliance  
✅ Explain deployment patterns and requirements  
✅ Provide tooling and dependency guidance  
✅ Explain the multi-agent architecture (ADK, A2A Protocol)  

### What the Agent CANNOT Do:

❌ Execute code or run tests  
❌ Access your local environment or repository  
❌ Make commits or open PRs directly  
❌ Access secrets or sensitive information  
❌ Replace human code review (it's a pre-review assistant)  

---

## Example Conversation Flow

Here's a realistic example of how you might use the agent during development:

**Developer:** I'm adding a new endpoint to the backend. What do I need to ensure for Cloud Run compatibility?

**Agent:** For Cloud Run compatibility, your FastAPI endpoint should:
1. Be accessible via the `PORT` environment variable (Cloud Run sets this automatically)
2. Use `0.0.0.0` host binding (not `127.0.0.1`) for uvicorn
3. Include a `/healthz` health check endpoint
4. Handle SIGTERM for graceful shutdowns
5. Log to stdout/stderr (Cloud Run captures these)

Example:
```python
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**Developer:** Thanks! How do I test this locally?

**Agent:** To test locally:
```bash
# Set PORT environment variable
export PORT=8080

# Run the application
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# In another terminal, test the health check
curl http://localhost:8080/healthz
```

For full local development setup, see `docs/local-development.md`.

---

## Troubleshooting

### Agent Doesn't Respond

**Possible Causes:**
- Incorrect mention format (should be `@agentnav-gh-copilot-agent`)
- Agent invocation in unsupported context
- GitHub Copilot extension not enabled

**Solution:** Verify the mention format and ensure you're invoking the agent in a supported context (PR comment, issue comment, IDE chat).

### Agent Gives Generic Answers

**Possible Causes:**
- Query too vague
- Missing context

**Solution:** Be more specific and provide code snippets or detailed descriptions of what you're trying to accomplish.

### Agent Response Seems Outdated

**Possible Causes:**
- System instruction may have been updated recently

**Solution:** The agent is loaded with the current system instruction from `.github/agents/agentnav-gh-copilot-agent.md`. If the instruction has been updated, the agent should reflect those changes. If not, mention this in the issue tracker.

---

## Integration with CI/CD

The agent complements (but does not replace) the automated CI/CD checks:

| Check | CI/CD | Agent |
|-------|-------|-------|
| **Linting** | ✅ Automated (ESLint, Ruff) | ✅ Can review code style |
| **Testing** | ✅ Automated (pytest, vitest) | ✅ Can suggest test cases |
| **Coverage** | ✅ Enforced (70% minimum) | ✅ Reminds about requirement |
| **Security** | ✅ Automated (tfsec, OSV) | ✅ Can explain vulnerabilities |
| **Terraform** | ✅ Automated (plan/validate) | ✅ Can review IaC patterns |

**Best Practice:** Use the agent as a **pre-CI check** to catch issues before pushing code.

---

## Advanced Use Cases

### 1. Understanding Complex Workflows

**Query:**
```
@agentnav-gh-copilot-agent Explain the full workflow from user input to visualization in the multi-agent system
```

**Expected Response:**
A detailed explanation of:
1. User submits document or codebase via frontend
2. Orchestrator Agent receives input and determines content type
3. Summarizer Agent processes content and stores results in Firestore
4. Linker Agent identifies entities and relationships (calls Gemma GPU service for embeddings)
5. Visualizer Agent generates graph structure (Mind Map or Dependency Graph)
6. Results returned to frontend for rendering
7. Session state persisted in Firestore via A2A Protocol

### 2. Debugging Deployment Issues

**Query:**
```
@agentnav-gh-copilot-agent My Cloud Run backend is failing to start. Here's the error:

Error: Address already in use

What could be wrong?
```

**Expected Response:**
Common causes:
- Backend not reading `PORT` environment variable
- Hardcoded port (e.g., `port=8080` instead of `port=int(os.getenv("PORT", 8080))`)
- Multiple uvicorn instances running

Solution: Ensure your backend reads `PORT` from environment:
```python
port = int(os.getenv("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=port)
```

### 3. Planning New Features

**Query:**
```
@agentnav-gh-copilot-agent I want to add a new agent that performs sentiment analysis. What do I need to consider?
```

**Expected Response:**
To add a new ADK agent:

1. **Agent Definition:**
   - Create agent file in `backend/agents/`
   - Inherit from ADK `Agent` base class
   - Implement `process()` method

2. **A2A Protocol Integration:**
   - Register agent with Orchestrator
   - Define message types for communication
   - Store agent state in Firestore

3. **Testing:**
   - Unit tests for agent logic
   - Integration tests for A2A Protocol communication
   - Achieve 70% code coverage

4. **Configuration:**
   - Add agent config to `ADK_AGENT_CONFIG_PATH`
   - Update environment variables if needed

5. **Documentation:**
   - Update `docs/A2A_PROTOCOL_INTEGRATION.md`
   - Document agent role and responsibilities

---

## Feedback and Improvements

The agentnav-copilot-agent is continuously improved based on user feedback.

### How to Provide Feedback:

1. **Open an issue** with the label `copilot-agent` if you encounter:
   - Incorrect responses
   - Outdated information
   - Missing context

2. **Suggest improvements** to the system instruction at `.github/agents/agentnav-gh-copilot-agent.md`

3. **Share success stories** of how the agent helped you solve a problem

---

## Summary

The **agentnav-copilot-agent** is your context-aware development assistant for the Agentic Navigator project. Use it to:

- ✅ Generate compliant code
- ✅ Understand the architecture
- ✅ Enforce quality policies
- ✅ Learn best practices
- ✅ Accelerate your development workflow

**Quick Start:**
```
@agentnav-gh-copilot-agent [your question]
```

**Related Documentation:**
- [System Instruction](SYSTEM_INSTRUCTION.md) - Complete architectural reference
- [Contribution Guide](../CONTRIBUTING.md) - How to contribute
- [Testing Strategy](TESTING_STRATEGY.md) - Testing requirements and guidelines
- [Local Development](local-development.md) - Setting up your environment

---

**Happy Coding! 🚀**
