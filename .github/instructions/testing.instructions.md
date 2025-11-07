---
applies_to:
  - "**/*test*.py"
  - "**/*test*.ts"
  - "**/*test*.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
  - tests/**/*
  - backend/tests/**/*
  - pytest.ini
  - vitest.config.ts
  - vitest.setup.ts
---

# Testing & Quality Standards Instructions

## Coverage Mandate

**MANDATORY:** All new or modified code must achieve ≥70% test coverage before merge.

This is a non-negotiable quality gate for this project. Code without adequate test coverage will not be accepted.

## Backend Testing (Python/pytest)

### Running Tests
```bash
cd backend
pytest tests/ --cov=. --cov-report=term-missing      # With coverage
pytest tests/ --cov=. --cov-report=term --cov-fail-under=70  # Enforce 70%
```

### Test Organization
```
backend/tests/
├── __init__.py
├── conftest.py              # pytest fixtures
├── test_routes.py           # FastAPI route tests
├── test_agents.py           # ADK agent tests
├── test_a2a_protocol.py     # A2A Protocol tests
├── test_firestore.py        # Firestore operations
└── test_integration.py      # Integration tests
```

### Writing Backend Tests

#### FastAPI Route Tests
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_analyze_endpoint():
    response = client.post("/analyze", json={
        "content": "Test document",
        "content_type": "document"
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "visualization" in data
```

#### ADK Agent Tests
```python
import pytest
from agents.summarizer import SummarizerAgent

@pytest.mark.asyncio
async def test_summarizer_agent():
    agent = SummarizerAgent()
    context = {"document": "Long test document..."}
    
    result = await agent.process(context)
    
    assert "summary" in result
    assert len(result["summary"]) > 0
```

#### Firestore Tests (with mocks)
```python
from unittest.mock import Mock, AsyncMock
import pytest

@pytest.mark.asyncio
async def test_firestore_session_save(mock_firestore):
    # Arrange
    mock_firestore.collection.return_value.document.return_value.set = AsyncMock()
    
    # Act
    await save_session(mock_firestore, "session_123", {"data": "test"})
    
    # Assert
    mock_firestore.collection.assert_called_with("sessions")
```

#### A2A Protocol Tests
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_a2a_message_passing():
    agent = SummarizerAgent()
    agent.a2a.send_message = AsyncMock()
    
    await agent.process({"document": "Test"})
    
    agent.a2a.send_message.assert_called_once()
    call_args = agent.a2a.send_message.call_args[0][0]
    assert call_args["agent"] == "visualizer"
    assert call_args["type"] == "summary_complete"
```

### pytest Fixtures
```python
# conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_firestore():
    """Mock Firestore client for testing."""
    return Mock()

@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API client for testing."""
    mock = Mock()
    mock.generate_content.return_value = Mock(text="Test response")
    return mock
```

## Frontend Testing (TypeScript/Vitest/React Testing Library)

### Running Tests
```bash
bun test                                                          # Run tests
bun test --coverage                                              # With coverage
bun test --coverage --coverageThreshold='{"global":{"lines":70}}'  # Enforce 70%
```

### Test Organization
```
src/
├── __tests__/
│   ├── App.test.tsx
│   ├── Visualization.test.tsx
│   └── utils.test.ts
├── components/
│   └── __tests__/
│       └── ComponentName.test.tsx
```

### Writing Frontend Tests

#### Component Tests
```typescript
import { render, screen } from '@testing-library/react';
import { Visualization } from './Visualization';

describe('Visualization', () => {
  it('renders no data message when data is empty', () => {
    render(<Visualization data={{ nodes: [] }} />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });
  
  it('renders graph when data is provided', () => {
    const data = {
      nodes: [{ id: '1', label: 'Node 1' }],
      edges: [{ source: '1', target: '2' }]
    };
    render(<Visualization data={data} />);
    expect(screen.getByTestId('graph-container')).toBeInTheDocument();
  });
});
```

#### User Interaction Tests
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('AnalyzeButton', () => {
  it('calls onAnalyze when clicked', async () => {
    const onAnalyze = jest.fn();
    render(<AnalyzeButton onAnalyze={onAnalyze} />);
    
    const button = screen.getByRole('button', { name: /analyze/i });
    await userEvent.click(button);
    
    expect(onAnalyze).toHaveBeenCalledTimes(1);
  });
});
```

#### API Integration Tests (with mocks)
```typescript
import { render, waitFor } from '@testing-library/react';
import { analyzeContent } from './services/api';

global.fetch = jest.fn();

describe('API Integration', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });
  
  it('fetches analysis results', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ summary: 'Test summary', visualization: {} })
    });
    
    const result = await analyzeContent({ content: 'test', content_type: 'document' });
    
    expect(fetch).toHaveBeenCalledWith('/api/analyze', expect.any(Object));
    expect(result.summary).toBe('Test summary');
  });
  
  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ code: 'ERROR', message: 'API failed' })
    });
    
    await expect(analyzeContent({ content: 'test', content_type: 'document' }))
      .rejects.toThrow('API failed');
  });
});
```

#### Error Boundary Tests
```typescript
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

const ThrowError = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  it('catches and displays errors', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    consoleSpy.mockRestore();
  });
});
```

## Integration Testing

### Full Workflow Tests
Test complete user workflows end-to-end:
- User input → API call → Agent processing → Visualization rendering
- Multi-agent collaboration scenarios
- A2A Protocol message passing
- Firestore session persistence

### Example Integration Test
```python
@pytest.mark.asyncio
async def test_full_analysis_workflow():
    # Setup
    client = TestClient(app)
    
    # User submits document
    response = client.post("/analyze", json={
        "content": "Sample document for analysis",
        "content_type": "document"
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Verify orchestrator delegated to agents
    assert "summary" in data
    assert "visualization" in data
    
    # Verify visualization structure
    viz = data["visualization"]
    assert viz["type"] == "mind_map"
    assert len(viz["nodes"]) > 0
    assert len(viz["edges"]) > 0
```

## Test Fixtures and Mocks

### Backend Fixtures
```python
# conftest.py
import pytest

@pytest.fixture
def sample_document():
    return "This is a long document for testing purposes..."

@pytest.fixture
def sample_codebase():
    return """
    def process_data(input_data):
        result = transform(input_data)
        return result
    """

@pytest.fixture
def mock_gemini_response():
    return {
        "summary": "Test summary",
        "visualization": {
            "type": "mind_map",
            "nodes": [{"id": "1", "label": "Test"}],
            "edges": []
        }
    }
```

### Frontend Fixtures
```typescript
// test-utils.ts
export const mockGraphData = {
  nodes: [
    { id: '1', label: 'Node 1', group: 'concept' },
    { id: '2', label: 'Node 2', group: 'concept' }
  ],
  edges: [
    { source: '1', target: '2', label: 'relates to' }
  ]
};

export const mockApiResponse = {
  summary: 'Test summary of the content',
  visualization: mockGraphData
};
```

## What to Test

### Backend
✅ All FastAPI route handlers
✅ Pydantic request/response validation
✅ ADK agent logic and A2A Protocol handlers
✅ Firestore CRUD operations (with mocks)
✅ Error handling and edge cases
✅ Integration workflows

### Frontend
✅ React components with different prop combinations
✅ User interactions (clicks, inputs, form submissions)
✅ API integration with mocked responses
✅ Error handling (Error Boundaries)
✅ Data validation and guards
✅ Edge cases (empty data, invalid inputs)

## Common Testing Pitfalls

❌ **Mistake:** Not mocking external dependencies (Firestore, APIs)
✅ **Solution:** Use pytest fixtures and unittest.mock for clean tests

❌ **Mistake:** Testing implementation details instead of behavior
✅ **Solution:** Test the public API and user-facing behavior

❌ **Mistake:** Not testing error cases
✅ **Solution:** Always test both happy path and error scenarios

❌ **Mistake:** Forgetting to test async code properly
✅ **Solution:** Use `@pytest.mark.asyncio` and `AsyncMock` for async tests

❌ **Mistake:** Tests that depend on external services
✅ **Solution:** Mock all external dependencies

## Quality Gates

Before merging code:
1. ✅ All tests pass
2. ✅ Coverage ≥70% for new/modified code
3. ✅ No linting errors
4. ✅ No security vulnerabilities (CodeQL)
5. ✅ Code review approved

## Running Quality Checks

### Backend
```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=term --cov-fail-under=70

# Run linting
ruff check .

# Run type checking
mypy .
```

### Frontend
```bash
# Run tests with coverage
bun test --coverage --coverageThreshold='{"global":{"lines":70}}'

# Run linting
bun run lint

# Run type checking
bun run type-check
```

## Continuous Testing

- Run tests on every commit (pre-commit hooks)
- Run full test suite in CI/CD (GitHub Actions)
- Fail CI/CD pipeline if coverage drops below 70%
- Automated quality reports in PR comments
