
# Agentic Navigator

**A multi-agent knowledge explorer for complex documents and codebases.**

This project is a submission for the **Google Cloud Run Hackathon** on Devpost. It demonstrates an AI agent-based application built with the Google Gemini API and deployed in a modern web environment.

## Core Concept

Agentic Navigator is a multi-agent AI system designed to analyze and visualize complex information. It simulates a team of specialized AI agents, each with a distinct role, that collaborate to break down, summarize, and map out the relationships within a given text or source code.

The core idea is to move beyond monolithic AI responses and leverage a cooperative, agentic workflow to produce richer, more structured insights.

The system consists of the following agents:

-   **Orchestrator Agent**: The team lead. It receives the user's input, determines the content type (natural language document or codebase), and delegates tasks to the other agents.
-   **Summarizer Agent**: Responsible for reading the entire content and generating a concise, comprehensive summary.
-   **Visualizer Agent (with Linker capabilities)**: This agent identifies key entities (concepts, functions, classes) and the relationships between them. It then structures this information into a graph format suitable for visualization.

## Features

-   **Multi-Agent System**: Utilizes a prompt-based simulation of multiple AI agents collaborating on a single task.
-   **Content-Aware Analysis**: Intelligently distinguishes between documents and code to provide the most relevant type of analysis.
-   **Interactive Visualizations**:
    -   Generates **Mind Maps** for documents to show relationships between key concepts.
    -   Generates **Dependency Graphs** for codebases to visualize function calls, imports, and class interactions.
-   **Dynamic UI**: The web dashboard allows users to pan, zoom, and hover over the graph to explore connections in real-time.
-   **Real-time Status Updates**: The UI shows the status of each agent as it works, providing transparency into the analysis process.

## Technology Stack

-   **AI Model**: **Google Gemini 2.5 Pro** is used for its advanced reasoning, instruction-following, and JSON output capabilities.
-   **Frontend Framework**: **React** with **TypeScript** for a robust and scalable user interface.
-   **Styling**: **Tailwind CSS** for rapid and modern UI development.
-   **Visualization**: A custom-built interactive graph component using **SVG**, providing full control over rendering and user interactions without heavy library dependencies.

## How It Works

1.  **Input**: The user pastes a document or code snippet into the text area or uploads a file.
2.  **Orchestration**: The user clicks "Run Navigator," and the frontend sends the content to the Gemini API with a detailed prompt that defines the roles of each agent and the desired JSON output schema.
3.  **Collaborative Analysis (in a single API call)**: The Gemini model acts as the orchestrator, internally performing the tasks of the summarizer and visualizer. It analyzes the text, creates the summary, identifies the nodes and edges for the graph, and formats everything according to the predefined `responseSchema`.
4.  **Structured Output**: The API returns a single, clean JSON object containing the summary and the complete data for the visualization (type, title, nodes, and edges).
5.  **Rendering**: The React application parses the JSON response and dynamically renders the summary and the interactive graph, allowing the user to explore the results.

## Deployment & Automation

This project is configured for automated deployment to Google Cloud Run using Cloud Build.

### Prerequisites

1.  A Google Cloud Project with the **Cloud Build API** and **Cloud Run API** enabled.
2.  Your Gemini API key stored in **Secret Manager** as a secret named `GEMINI_API_KEY`.
3.  The Cloud Build service account granted the "Secret Manager Secret Accessor" role on the secret.

### Containerization (`Dockerfile`)

A `Dockerfile` is included to package the application as a lightweight container image using Nginx to serve the static files.

To build the image locally:

```sh
docker build -t agentic-navigator .
```

To run the container locally:

```sh
docker run -p 8080:80 agentic-navigator
```

You can then access the app at `http://localhost:8080`.

### Continuous Deployment (`cloudbuild.yaml`)

The `cloudbuild.yaml` file defines a CI/CD pipeline with the following steps:

1.  **Build**: Builds the Docker container image.
2.  **Push**: Pushes the image to Google Container Registry (GCR).
3.  **Deploy**: Deploys the new image to a Cloud Run service named `agentic-navigator`. It also securely injects the `GEMINI_API_KEY` from Secret Manager as an environment variable.

#### Setting up the Trigger

To automate this pipeline:

1.  Push this repository to a source control provider (like GitHub or Cloud Source Repositories).
2.  In the Google Cloud Console, navigate to **Cloud Build** > **Triggers**.
3.  Create a new trigger that connects to your repository.
4.  Configure the trigger to run on pushes to your main branch.
5.  Set the configuration type to **Cloud Build configuration file (yaml or json)** and point it to `cloudbuild.yaml`.

Now, every push to your main branch will automatically build and deploy the latest version of the application to Cloud Run.
