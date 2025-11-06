# Agentic Navigator

**A multi-agent knowledge explorer for complex documents and codebases.**

This project is a submission for the **Google Cloud Run Hackathon** on Devpost (**AI Agents + GPU Categories**). It demonstrates a multi-agent AI system using Gemini models, Gemma GPU service, and deployed on Cloud Run.

?? **Hackathon Categories:** AI Agents + GPU  
?? **Devpost:** https://run.devpost.com/

## Core Concept

Agentic Navigator is a multi-agent AI system designed to analyze and visualize complex information. It simulates a team of specialized AI agents, each with a distinct role, that collaborate to break down, summarize, and map out the relationships within a given text or source code.

The core idea is to move beyond monolithic AI responses and leverage a cooperative, agentic workflow to produce richer, more structured insights.

The system consists of the following agents:

- **Orchestrator Agent**: The team lead. It receives the user's input, determines the content type (natural language document or codebase), and delegates tasks to the other agents.
- **Summarizer Agent**: Responsible for reading the entire content and generating a concise, comprehensive summary.
- **Visualizer Agent (with Linker capabilities)**: This agent identifies key entities (concepts, functions, classes) and the relationships between them. It then structures this information into a graph format suitable for visualization.

## Features

- **Multi-Agent System**: Utilizes a prompt-based simulation of multiple AI agents collaborating on a single task.
- **Content-Aware Analysis**: Intelligently distinguishes between documents and code to provide the most relevant type of analysis.
- **Interactive Visualizations**:
  - Generates **Mind Maps** for documents to show relationships between key concepts.
  - Generates **Dependency Graphs** for codebases to visualize function calls, imports, and class interactions.
- **Dynamic UI**: The web dashboard allows users to pan, zoom, and hover over the graph to explore connections in real-time.
- **Real-time Status Updates**: The UI shows the status of each agent as it works, providing transparency into the analysis process.

## ?? Built With

**Languages & Frameworks**

- ?? **Python** ? core backend logic, FastAPI orchestrator
- ?? **React + TypeScript** ? responsive web dashboard for visualization
- ?? **Tailwind CSS** ? modern UI styling (via CDN)

**AI & ML**

- ?? **Google Gemini 1.5 Pro** ? reasoning, summarization, and JSON generation
- ?? **Gemma** ? GPU-accelerated open-source model for embeddings and visualization
- ?? **Recharts** ? interactive data visualization library

**Cloud Infrastructure**

- ?? **Google Cloud Run** ? fully serverless hosting for orchestrator and web dashboard
- ??? **Google Firestore** ? session memory and persistent agent state
- ?? **Google Cloud GPUs (NVIDIA L4)** ? model inference acceleration in europe-west1
- ?? **Google Artifact Registry (GAR)** ? container image storage
- ?? **Google Secret Manager** ? secure credential storage

**Developer Tools & DevOps**

- ?? **Podman** ? containerization for reproducible deployments
- ?? **Vite** ? fast frontend build tool and dev server
- ?? **uv** ? fast Python package management
- ?? **GitHub Actions** ? automated testing and Cloud Run deployment
- ??? **Terraform Cloud** ? infrastructure as code provisioning
- ?? **Workload Identity Federation (WIF)** ? secure GitHub Actions authentication
- ?? **Workload Identity (WI)** ? secure Cloud Run service-to-service authentication

**Other Utilities**

- ?? **Markdown** ? documentation and knowledge representation
- ?? **OpenAPI / FastAPI Docs** ? API endpoints and interface documentation

### Hackathon Requirements Met

**AI Agents Category:**
? Multi-agent system (4 agents: Orchestrator, Summarizer, Linker, Visualizer)  
? Deployed to Cloud Run  
? Uses Google AI models (Gemini + Gemma)

**GPU Category:**
? Gemma model deployed on Cloud Run with NVIDIA L4 GPU  
? GPU service in europe-west1 region  
? Open-source model (Gemma) running on GPU  
? GPU acceleration for complex visualization tasks

**Bonus Points:**
? Multiple Cloud Run services (Frontend + Backend + Gemma GPU Service)  
? Google AI models (Gemini + Gemma)

## How It Works

1.  **Input**: The user pastes a document or code snippet into the text area or uploads a file.
2.  **Orchestration**: The user clicks "Run Navigator," and the frontend sends the content to the Gemini API with a detailed prompt that defines the roles of each agent and the desired JSON output schema.
3.  **Collaborative Analysis (in a single API call)**: The Gemini model acts as the orchestrator, internally performing the tasks of the summarizer and visualizer. It analyzes the text, creates the summary, identifies the nodes and edges for the graph, and formats everything according to the predefined `responseSchema`.
4.  **Structured Output**: The API returns a single, clean JSON object containing the summary and the complete data for the visualization (type, title, nodes, and edges).
5.  **Rendering**: The React application parses the JSON response and dynamically renders the summary and the interactive graph, allowing the user to explore the results.

## Local Development

This project includes a complete **Podman-based** local development environment with hot-reload support for both frontend and backend.

### Prerequisites

- **Podman** installed and running
  - macOS: `brew install podman` then `podman machine start`
  - Linux: See [Podman Installation](https://podman.io/getting-started/installation)
  - Windows: Use WSL2 with Podman

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd agentnav

# Copy environment template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# One command setup (builds containers and starts all services)
make setup

# View logs
make logs

# Stop services
make down

# See all available commands
make help
```

### What's Included

- **Frontend**: React + TypeScript + Vite with hot-reload (port 3000)
- **Backend**: FastAPI with hot-reload (port 8080)
- **Firestore Emulator**: Local database for development (port 8081)
- **Makefile**: Simplified commands for all operations
- **Podman Support**: Uses Podman commands directly (no docker-compose dependency)

### Access Points

Once services are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Firestore Emulator**: http://localhost:8081

### Common Commands

```bash
make setup          # Initial setup (build & start all services)
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make logs           # View all logs (Ctrl+C to exit)
make logs-frontend  # View frontend logs only
make logs-backend   # View backend logs only
make ps             # Show running containers
make build          # Rebuild containers
make test           # Run tests
make clean          # Stop and remove everything
make help           # Show all commands
```

### Development Workflow

1. **Start services**: `make setup` (first time) or `make up` (subsequent)
2. **Make code changes**: Both frontend and backend support hot-reload
   - Frontend: Edit files in root directory
   - Backend: Edit files in `backend/` directory
3. **View logs**: `make logs` or `make logs-frontend` / `make logs-backend`
4. **Stop services**: `make down` when done

For detailed local development instructions, troubleshooting, and advanced usage, see [docs/local-development.md](docs/local-development.md).

## Hackathon Documentation

### ?? Setup & Submission Guides

- **[Dual Category Strategy](docs/DUAL_CATEGORY_STRATEGY.md)** - Targeting both AI Agents + GPU categories
- **[GPU Setup Guide](docs/GPU_SETUP_GUIDE.md)** - Adding Gemma model with NVIDIA L4 GPU
- **[Quick Reference](docs/HACKATHON_QUICK_REFERENCE.md)** - Quick checklist and key points
- **[Submission Guide](docs/HACKATHON_SUBMISSION_GUIDE.md)** - Complete submission preparation guide
- **[Architecture Diagram Guide](docs/ARCHITECTURE_DIAGRAM_GUIDE.md)** - How to create your architecture diagram
- **[GCP Setup Guide](docs/GCP_SETUP_GUIDE.md)** - Step-by-step Google Cloud setup
- **[Setup Checklist](docs/HACKATHON_SETUP_CHECKLIST.md)** - Pre-hackathon setup checklist

### ?? Submission Checklist

- [ ] Text description written
- [ ] Demo video recorded (3 min max)
- [ ] Architecture diagram created
- [ ] Code repository is public
- [ ] Try it out link works
- [ ] (Optional) Blog post published
- [ ] (Optional) Social media post with #CloudRunHackathon

## Deployment & Automation

This project is configured for automated deployment to Google Cloud Run using Cloud Build.

### Prerequisites

1.  A Google Cloud Project with the **Cloud Build API** and **Cloud Run API** enabled.
2.  Your Gemini API key stored in **Secret Manager** as a secret named `GEMINI_API_KEY`.
3.  The Cloud Build service account granted the "Secret Manager Secret Accessor" role on the secret.

### Containerization

The project uses **Podman** for container builds (aligned with Cloud Run best practices):

- **Frontend**: `Dockerfile` - Production build with Nginx serving static files
- **Backend**: `backend/Dockerfile` - FastAPI application container

To build images locally with Podman:

```bash
# Build frontend
podman build -t agentnav-frontend -f Dockerfile .

# Build backend
podman build -t agentnav-backend -f backend/Dockerfile ./backend
```

For local development, use the Makefile (`make setup`) which handles building and running all services.

### Continuous Deployment

The project uses **GitHub Actions** with **Terraform Cloud** for infrastructure provisioning and **Cloud Build** for container builds. See [docs/SYSTEM_INSTRUCTION.md](docs/SYSTEM_INSTRUCTION.md) for complete architecture details.

#### Infrastructure Components

- **Google Cloud Run**: Serverless container hosting (frontend + backend)
- **Google Artifact Registry (GAR)**: Container image storage
- **Firestore**: NoSQL database for session persistence
- **Secret Manager**: Secure credential storage
- **Cloud DNS**: Domain management (`agentnav.lornu.com`)
- **Workload Identity Federation (WIF)**: Secure GitHub Actions authentication

#### Deployment Process

1. **Terraform Provisioning**: GitHub Actions triggers Terraform Cloud to provision/update GCP infrastructure
2. **Container Build**: Uses Podman to build OCI-compliant images
3. **Image Push**: Images tagged with Git SHA and pushed to GAR
4. **Cloud Run Deployment**: `gcloud` CLI deploys services to Cloud Run with:
   - Frontend: `us-central1` region (low latency)
   - Backend: `europe-west1` region (GPU support for AI inference)

For detailed deployment information, see [docs/SYSTEM_INSTRUCTION.md](docs/SYSTEM_INSTRUCTION.md).

## Project Structure

```
agentnav/
??? backend/                    # FastAPI backend with ADK agents
?   ??? agents/                 # Agent definitions (ADK) - [to be implemented]
?   ??? main.py                # FastAPI application
?   ??? Dockerfile             # Backend development container
?   ??? pyproject.toml         # Python dependencies (uv)
?   ??? requirements.txt       # Python dependencies fallback
??? components/                 # React components
?   ??? AgentCard.tsx
?   ??? InteractiveGraph.tsx
?   ??? ResultsDisplay.tsx
?   ??? icons.tsx
??? services/                   # Frontend API services
?   ??? geminiService.ts
??? docs/                       # Documentation
?   ??? local-development.md    # Local dev guide
?   ??? HACKATHON_SUBMISSION_GUIDE.md
?   ??? ARCHITECTURE_DIAGRAM_GUIDE.md
?   ??? GCP_SETUP_GUIDE.md
??? scripts/                    # Utility scripts
?   ??? podman-setup.sh        # Setup script
?   ??? podman-teardown.sh     # Cleanup script
??? Dockerfile                  # Frontend production container
??? Dockerfile.frontend         # Frontend development container
??? docker-compose.yml          # Local development stack (optional)
??? docker-compose.test.yml    # Test environment
??? docker-compose.demo.yml    # Demo environment
??? Makefile                    # Development commands (Podman-based)
??? .env.example                # Environment variables template
??? cloudbuild.yaml             # Cloud Build CI/CD
??? package.json                # Frontend dependencies
??? vite.config.ts              # Vite configuration
??? SYSTEM_INSTRUCTION.md       # System architecture guide
```

## Links

- **Live Demo:** [Coming Soon - Add your Cloud Run URL]
- **API Docs:** http://localhost:8080/docs (when running locally)
- **Architecture Diagram:** [docs/architecture-diagram.png](docs/architecture-diagram.png)
- **Devpost Submission:** https://run.devpost.com/
- **System Documentation:** [docs/SYSTEM_INSTRUCTION.md](docs/SYSTEM_INSTRUCTION.md)
- **Local Development:** [docs/local-development.md](docs/local-development.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- How to set up your development environment
- Our development workflow
- Code style guidelines
- How to submit pull requests

Please also read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

For security vulnerabilities, please see our [Security Policy](SECURITY.md).

## Troubleshooting

### Common Issues

**Podman machine not running (macOS)**

```bash
podman machine start
```

**Port already in use**

- Edit `docker-compose.yml` to change port mappings, or
- Stop the service using the port: `lsof -ti:3000 | xargs kill`

**Container build fails**

```bash
make clean
make build
```

**Environment variables not loading**

- Ensure `.env` file exists: `cp .env.example .env`
- Add your `GEMINI_API_KEY` to `.env`
- Restart services: `make restart`

For more troubleshooting, see [docs/local-development.md](docs/local-development.md).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

By contributing to this project, you agree that your contributions will be licensed under the Apache License 2.0.

## Acknowledgments

Built for the [Google Cloud Run Hackathon](https://run.devpost.com/) using:

- Google Cloud Run (Serverless)
- Google Gemini API (for agent reasoning)
- Gemma Model on NVIDIA L4 GPU (for GPU acceleration)
- Google Firestore (for session persistence)
- Podman (container builds)
- Terraform Cloud (infrastructure provisioning)
