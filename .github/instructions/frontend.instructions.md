---
applies_to:
  - "*.tsx"
  - "*.ts"
  - components/**/*
  - hooks/**/*
  - services/**/*
  - "App.tsx"
  - "index.tsx"
  - "types.ts"
---

# Frontend Development Instructions (React/TypeScript)

## Technology Stack
- **React** with functional components
- **TypeScript** for type safety
- **Vite** for fast builds and dev server
- **Tailwind CSS** for styling (utility classes only)
- **bun** for package management (fast JS runtime)
- **Three.js** (r128) for 3D visualizations

## Development Setup

### Environment Setup
```bash
bun install              # Install dependencies
bun run dev              # Start dev server (port 5173)
bun run build            # Production build
bun run test             # Run tests
bun run lint             # Lint code
```

**Important:** Always use `bun`, not npm/yarn. Bun is significantly faster for this codebase.

## Code Conventions

### React Components
- Use pure functional components only
- Named exports (not default exports)
- TypeScript interfaces for all props
- Guard early with data validation
- Implement Error Boundaries for graceful error handling

**Example:**
```typescript
interface VisualizationProps {
  data: GraphData;
  onError?: (error: Error) => void;
}

export function Visualization({ data, onError }: VisualizationProps) {
  if (!data?.nodes) {
    return <div>No data available</div>;
  }
  // Component logic...
}
```

### State Management
- Use React hooks: `useState`, `useReducer`, `useContext`
- **NEVER use localStorage/sessionStorage** (not supported in artifacts/Claude.ai)
- Use in-memory state for session data
- Implement proper state lifting when needed

### Type Safety
- Use TypeScript for all type safety
- Define interfaces for all data structures
- Avoid `any` type - use proper types or `unknown`
- Use strict type checking

### Styling
- **Tailwind utility classes ONLY** (no custom CSS)
- No access to CSS/SCSS compilers
- Use Tailwind's built-in utilities for all styling
- Keep styling inline with JSX using className

**Example:**
```tsx
<div className="flex flex-col gap-4 p-6 bg-gray-100 rounded-lg shadow-md">
  <h2 className="text-2xl font-bold text-gray-800">Title</h2>
  <p className="text-gray-600">Content</p>
</div>
```

## API Integration

### Error Handling
- Validate user input before API calls
- Parse backend errors into user-friendly messages
- Expect error shape: `{ code: string, message: string, details?: object }`
- Use Error Boundaries to catch rendering errors

**Example:**
```typescript
try {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, content_type })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'API request failed');
  }
  
  const data = await response.json();
  return data;
} catch (error) {
  console.error('Analysis failed:', error);
  throw error;
}
```

## Visualization Components

### Three.js Constraints
- **NEVER use THREE.CapsuleGeometry** (requires r142+, we use r128)
- Use CylinderGeometry, SphereGeometry, or custom geometry instead
- Lazy load visualization components for performance
- Handle WebGL context loss gracefully

### Graph Rendering
- Support Mind Maps for documents
- Support Dependency Graphs for codebases
- Implement pan, zoom, and hover interactions
- Show real-time agent status updates

## Performance Optimization

### Code Splitting
- Leverage Vite's automatic code splitting
- Lazy load visualization components
- Use `React.lazy()` and `Suspense` for heavy components

**Example:**
```typescript
const Visualization = React.lazy(() => import('./components/Visualization'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Visualization data={data} />
    </Suspense>
  );
}
```

### Asset Optimization
- Minimize bundle size
- Compress static assets
- Leverage Cloud Run CDN caching
- Optimize images and icons

## Testing Requirements

### Running Tests
```bash
bun test                                                      # Run tests
bun test --coverage                                          # With coverage
bun test --coverage --coverageThreshold='{"global":{"lines":70}}'
```

### Coverage Requirement
**MANDATORY:** All new code must achieve ≥70% test coverage before merge.

### Test Organization
- Unit tests with Jest + React Testing Library
- Test components with different prop combinations
- Test error handling and edge cases
- Test user interactions (clicks, inputs, etc.)
- Test API integration with mocked responses

**Example:**
```typescript
import { render, screen } from '@testing-library/react';
import { Visualization } from './Visualization';

test('renders no data message when data is empty', () => {
  render(<Visualization data={{ nodes: [] }} />);
  expect(screen.getByText('No data available')).toBeInTheDocument();
});
```

## Common Pitfalls

❌ **Mistake:** Using localStorage in artifacts
✅ **Solution:** Use React state (useState, useReducer) for in-memory storage

❌ **Mistake:** Using THREE.CapsuleGeometry
✅ **Solution:** Use CylinderGeometry, SphereGeometry, or custom geometry

❌ **Mistake:** Not handling API errors gracefully
✅ **Solution:** Implement Error Boundaries and show user-friendly messages

❌ **Mistake:** Not validating props/data early
✅ **Solution:** Guard at component entry with early returns

## Deployment

### Container Build
Frontend is served via Nginx on Cloud Run:
```bash
podman build -t agentnav-frontend:latest -f frontend/Containerfile frontend/
```

### Cloud Run Deployment
- Region: us-central1
- Port: 80 (Nginx)
- Static assets served with CDN caching
- Timeout: 300s

## RORO Pattern
Use Receive an Object, Return an Object pattern for all functions and components:
```typescript
// Good
function analyzeContent(params: AnalyzeParams): AnalyzeResult {
  const { content, contentType } = params;
  // ...
  return { summary, visualization };
}

// Avoid
function analyzeContent(content: string, contentType: string): string {
  // ...
  return summary;
}
```

## Security
- Validate and sanitize all user inputs before API calls
- Never expose API keys in frontend code
- Implement proper CORS handling
- Use HTTPS only (enforced by Cloud Run)
