# Feature Request #013: Comprehensive Testing Strategy - Implementation Guide

This document provides setup instructions and usage guidance for the multi-layered testing and security scanning strategy implemented for the Agentic Navigator project.

## Overview

The testing strategy covers:
- **Frontend Unit Tests** (Vitest + Testing Library)
- **Backend Integration Tests** (pytest + Firestore emulator)
- **Infrastructure Security Scans** (tfsec for Terraform)
- **Dependency Vulnerability Scans** (OSV-scanner)
- **Code Quality Gates** (ESLint, Prettier, Black, isort, ruff, mypy)
- **Automated Dependency Updates** (Dependabot)

## Quick Start

### Local Development

1. **Run all tests:**
   ```bash
   make test
   ```

2. **Run frontend tests only:**
   ```bash
   bun run test
   # Or with the Makefile:
   make test-frontend
   ```

3. **Run backend tests only:**
   ```bash
   make test-backend
   ```

4. **Run code quality checks:**
   ```bash
   # Frontend linting and formatting
   bun run lint
   bun run format:check
   
   # Backend linting and formatting
   black --check backend/
   isort --check-only --profile black backend/
   ruff check backend/
   mypy backend/ --ignore-missing-imports
   ```

### CI/CD Pipeline

The GitHub Actions CI workflow (`.github/workflows/ci.yml`) automatically runs:

1. **Code Quality Job** - Linting and formatting checks
2. **Frontend Tests Job** - Vitest unit tests
3. **Backend Tests Job** - pytest with Firestore emulator
4. **TFSec Scan Job** - Terraform security analysis
5. **OSV Scanner Job** - Dependency vulnerability scanning

## Frontend Testing

### Technology Stack
- **Test Runner:** Vitest
- **Testing Library:** @testing-library/react
- **Test Environment:** jsdom

### Configuration Files
- `vitest.config.ts` - Vitest configuration
- `vitest.setup.ts` - Test setup (imports jest-dom)
- `components/__tests__/` - Component test files

### Example Test
```typescript
// components/__tests__/AgentCard.test.tsx
import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AgentCard } from '../AgentCard'
import { AgentName, AgentStatusValue } from '../../types'

describe('AgentCard', () => {
  it('renders agent name and details correctly', () => {
    const agent = {
      name: AgentName.ORCHESTRATOR,
      status: AgentStatusValue.IDLE,
      details: 'Idle and ready',
    }

    render(<AgentCard agent={agent} />)
    expect(screen.getByText('Orchestrator')).toBeDefined()
    expect(screen.getByText('Idle and ready')).toBeDefined()
  })
})
```

### Running Frontend Tests
```bash
# Install dependencies
bun install

# Run tests (watch mode)
bun run test

# Run tests (CI mode)
bun run test -- --run

# Run with coverage
bun run test -- --coverage
```

## Backend Testing

### Technology Stack
- **Test Runner:** pytest
- **Database:** Firestore emulator
- **Async Support:** pytest-asyncio

### Configuration
- `backend/tests/` - Test directory
- `backend/tests/test_firestore_client.py` - Firestore integration tests

### Firestore Emulator Integration
The backend tests use the Firestore emulator for isolated testing:

```python
# Environment variables for tests
FIRESTORE_EMULATOR_HOST=localhost:8081
FIRESTORE_PROJECT_ID=agentnav-dev
```

### Example Test
```python
# backend/tests/test_firestore_client.py
import os
import time
from google.cloud import firestore
from services.firestore_client import get_client

def test_can_write_and_read_document(monkeypatch):
    # Integration-style test against the emulator
    emulator = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8081")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", emulator)
    monkeypatch.setenv("FIRESTORE_PROJECT_ID", "agentnav-dev")

    db = get_client()
    coll = db.collection("test_collection")
    doc_ref = coll.document("test_doc")
    payload = {"hello": "world"}
    doc_ref.set(payload)

    # Small delay for emulator consistency
    time.sleep(0.2)

    read = doc_ref.get()
    assert read.exists
    assert read.to_dict().get("hello") == "world"
```

### Running Backend Tests
```bash
# Using Makefile (recommended - starts emulator automatically)
make test-backend

# Manual approach
make start-firestore  # Start emulator
pytest backend/tests  # Run tests
```

## Code Quality

### Pre-commit Hooks
Install pre-commit hooks for automatic code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Frontend Code Quality
- **ESLint** - TypeScript/React linting
- **Prettier** - Code formatting

Configuration files:
- `.eslintrc.json` - ESLint rules
- `.prettierrc.json` - Prettier settings

### Backend Code Quality  
- **Black** - Code formatting
- **isort** - Import sorting
- **ruff** - Fast Python linter
- **mypy** - Type checking

## Security Scanning

### Infrastructure Security (tfsec)
Scans Terraform files for security misconfigurations:

```bash
# Install tfsec
brew install tfsec  # or download from GitHub

# Run scan
tfsec terraform/
```

### Dependency Vulnerability Scanning (OSV-scanner)
Scans for known vulnerabilities in dependencies:

```bash
# Install OSV-scanner
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Run scan
osv-scanner -r --skip-git ./
```

### GitHub Secret Scanning
**Manual Setup Required:**

1. Go to repository Settings → Security & analysis
2. Enable "Secret scanning" 
3. Enable "Push protection" (recommended)

## Dependabot Configuration

Automatic dependency updates are configured in `.github/dependabot.yml`:

- **Frontend dependencies** (npm) - Weekly checks
- **Backend dependencies** (pip) - Weekly checks

Dependabot will create PRs for:
- Security updates (immediate)
- Version updates (weekly)

## CI/CD Workflow Details

### Workflow Jobs

1. **code-quality** - Runs linting and formatting checks
2. **frontend-tests** - Runs Vitest unit tests with bun
3. **backend-tests** - Runs pytest with Firestore emulator in Docker
4. **tfsec-scan** - Scans Terraform for security issues
5. **osv-scanner** - Scans dependencies for vulnerabilities

### Environment Variables (CI)
```yaml
# Backend tests
FIRESTORE_EMULATOR_HOST: "localhost:8081"
FIRESTORE_PROJECT_ID: "agentnav-dev"
```

### Workflow Triggers
- **Pull requests** to `main` branch
- **Pushes** to `main` branch

## Expanding the Test Suite

### Adding Frontend Tests
1. Create test files in `components/__tests__/`
2. Follow the naming convention: `ComponentName.test.tsx`
3. Use Vitest + Testing Library patterns

### Adding Backend Tests
1. Create test files in `backend/tests/`
2. Follow the naming convention: `test_module_name.py`
3. Use pytest fixtures and async patterns
4. Mock external services (Gemini API, etc.)

### A2A Protocol Testing (Future)
For testing the Agent2Agent protocol:

```python
# Example structure for A2A tests
async def test_orchestrator_to_summarizer_flow():
    # Mock agent communication
    # Test A2A message passing
    # Verify agent state transitions
    pass
```

### API Route Testing (Future)
For testing FastAPI endpoints:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_endpoint():
    response = client.post("/analyze", json={"content": "test"})
    assert response.status_code == 200
```

## Troubleshooting

### Common Issues

**Frontend tests failing:**
- Ensure bun is installed: `curl -fsSL https://bun.sh/install | bash`
- Check dependencies: `bun install`

**Backend tests failing:**
- Ensure Firestore emulator is running: `make start-firestore`
- Check Python dependencies: `pip install -r backend/requirements.txt`

**Pre-commit hooks failing:**
- Install hooks: `pre-commit install`
- Update hooks: `pre-commit autoupdate`

**CI workflow failing:**
- Check GitHub Actions logs
- Verify secrets are configured
- Ensure all dependencies are in package.json/requirements.txt

## Coverage Goals

Per Feature Request #013 acceptance criteria:
- **Target:** 80% coverage for core utilities and API routes
- **Current:** Basic test scaffolding implemented
- **Next Steps:** Expand test coverage for:
  - All FastAPI routes
  - ADK agent logic
  - A2A Protocol workflows
  - Firestore operations
  - Utility functions

## Performance Considerations

### Local Development
- Firestore emulator provides fast, isolated testing
- Vitest provides fast frontend test execution
- Pre-commit hooks catch issues early

### CI/CD
- Parallel job execution reduces total pipeline time
- Docker-based Firestore emulator for consistent CI environment
- Soft-fail on some security scans to avoid blocking deployments

## References

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library React](https://testing-library.com/docs/react-testing-library/intro/)
- [pytest Documentation](https://docs.pytest.org/)
- [Firestore Emulator](https://firebase.google.com/docs/emulator-suite/connect_firestore)
- [TFSec Documentation](https://aquasecurity.github.io/tfsec/)
- [OSV-Scanner](https://osv.dev/docs/)
- [Pre-commit](https://pre-commit.com/)