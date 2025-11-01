## Agentic Navigator — Copilot / AI Agent Instructions

This file gives focused, actionable knowledge for an AI coding agent to be productive in this repo.
Keep guidance short and concrete: commands, file locations, patterns, and gotchas.

1) Quick context (big picture)
- Frontend: React + TypeScript SPA (Vite) in the repo root. Key files: `App.tsx`, `index.tsx`, `components/*`, `services/geminiService.ts`.
- Backend: FastAPI service in `backend/` (entry: `backend/main.py`). Gemma GPU support lives under `backend/gemma_service` and agents under `backend/agents/`.
- Local infra: Podman-based containers driven by the `Makefile` and `docker-compose.*.yml`. Firestore emulator for local persistence.

2) How to run (developer workflows)
- Recommended (local): `make setup` (builds and starts frontend, backend, Firestore emulator). See `docs/local-development.md` for troubleshooting.
- Dev servers:
  - Frontend: `npm run dev` (or `vite`) — port 3000
  - Backend: `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080` — port 8080
- Tests: frontend uses `vitest` (`npm run test`). Backend tests use pytest (see `backend/pyproject.toml`); `make test` may orchestrate both.

3) Integration / runtime conventions
- API keys: Do NOT store secrets in the frontend. The repo contains a legacy frontend-based `GEMINI_API_KEY` check in `services/geminiService.ts` but the secure pattern is: frontend → backend API → backend calls external models.
- Backend endpoints (important):
  - `/api/generate` (FastAPI) — calls Gemma GPU service client `services/gemma_service` (expects `GEMMA_SERVICE_URL`). See `backend/main.py`.
  - `/api/visualize` — runs Visualizer Agent (`agents/visualizer_agent.py`) and returns graph data.
- CORS: Backend allows `http://localhost:3000` and `http://localhost:5173` for local dev (see `backend/main.py`).

4) Agent & response contract (critical)
- The frontend calls `runAgenticNavigator(documentText)` in `services/geminiService.ts`. The prompt asks the model to *return a single JSON object* matching `analysisSchema`.
- Required top-level fields: `summary` (string) and `visualization` (object).
- `visualization` must include:
  - `type`: `'MIND_MAP'` or `'DEPENDENCY_GRAPH'`
  - `title`: string
  - `nodes`: array of objects with required keys `id` (string) and `label` (string). Optional `group` for styling.
  - `edges`: array of objects with required keys `from` and `to` (both must match node `id`s). Optional `label`.
- Example node/edge (follow exactly):
  - node: {"id":"concept_1","label":"Core Concept","group":"Core"}
  - edge: {"from":"concept_1","to":"concept_2","label":"relates_to"}
- The frontend expects valid JSON. The existing service strips surrounding markdown code fences, but prefer to return raw JSON with no Markdown wrapper.

5) Common patterns & gotchas
- Do not assume secrets in the frontend. If you see `window.GEMINI_API_KEY` in `services/geminiService.ts`, prefer migrating the call to the backend endpoint `http://localhost:8080/api/analyze` (TODO placeholder exists in the file).
- The frontend simulates agent progress visually (see `App.tsx` initialAgents and `AgentCard`), but real coordination is done via the model prompt and backend agents.
- Backend expects `GEMMA_SERVICE_URL` for GPU model calls; if missing, endpoints raise 503 with guidance in `backend/main.py`.
- When adding or changing the analysis schema, update both `services/geminiService.ts` (frontend expectations) and any backend validation/parsers to keep contracts aligned.

6) Files to inspect first (high ROI)
- `README.md` and `docs/local-development.md` — local setup, Makefile commands, architecture diagrams.
- `services/geminiService.ts` — prompt, schema, and the exact JSON contract the frontend expects.
- `App.tsx` — how the UI triggers analysis and how results are rendered (`ResultsDisplay` and `InteractiveGraph`).
- `backend/main.py` — available backend endpoints, CORS, and error behaviors.
- `backend/pyproject.toml` — Python dependency list and dev/test extras.

7) If you modify agents or schema
- Add/update unit tests where feasible: frontend (Vitest) and backend (pytest). Run `make test` and verify both pass.
- Keep contracts backward compatible: prefer adding optional fields rather than renaming required ones.

8) When in doubt — useful checks
- Start services locally (`make setup`) and call endpoints:
  - Health: `http://localhost:8080/healthz`
  - API docs: `http://localhost:8080/docs`
- Reproduce UI behavior: paste a short document into the frontend and click "Run Navigator" to exercise the whole stack.

If anything here is unclear or you want more examples (e.g., a sample valid JSON output for a small code snippet), tell me which part to expand and I'll iterate.
