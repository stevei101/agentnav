/* eslint-disable @typescript-eslint/no-duplicate-enum-values */
export enum AgentName {
  ORCHESTRATOR = 'Orchestrator',
  SUMMARIZER = 'Summarizer',
  LINKER = 'Linker',
  VISUALIZER = 'Visualizer',
}

export enum AgentStatusValue {
  IDLE = 'Idle',
  QUEUED = 'Queued',
  PROCESSING = 'Processing',
  DONE = 'Done',
  ERROR = 'Error',
}

export interface AgentState {
  id: string;
  name: AgentName;
  status: AgentStatusValue;
  details: string;
  progress?: number; // 0-100 for progress tracking
  currentTask?: string;
  findings?: string[];
  metrics?: {
    startTime?: number;
    endTime?: number;
    duration?: number;
    tokensProcessed?: number;
  };
}

// New types for interactive graph visualization
export enum VisualizationType {
  MIND_MAP = 'MIND_MAP',
  DEPENDENCY_GRAPH = 'DEPENDENCY_GRAPH',
}

export interface GraphNode {
  id: string; // Unique identifier for the node
  label: string; // Display text for the node
  group?: string; // For coloring or grouping nodes (e.g., 'function', 'class', 'concept')
}

export interface GraphEdge {
  from: string; // ID of the source node
  to: string; // ID of the target node
  label?: string; // Optional label for the edge/relationship
}

export interface AnalysisResult {
  summary: string;
  visualization: {
    type: VisualizationType;
    title: string;
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

// WebSocket Event Types for Real-time Agent Streaming
export enum AgentEventType {
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETE = 'complete',
  ERROR = 'error',
}

export interface EventPayload {
  summary?: string;
  entities?: Array<{ name: string; type: string; confidence?: number }>;
  relationships?: Array<{ source: string; target: string; type: string }>;
  visualization?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  errorMessage?: string;
  errorDetails?: Record<string, unknown>;
  metrics?: {
    processingTime?: number;
    tokensProcessed?: number;
    confidence?: number;
  };
}

export interface AgentStreamEvent {
  id: string;
  agent: AgentName;
  status: AgentEventType;
  timestamp: string;
  metadata?: {
    sessionId?: string;
    userId?: string;
    contentHash?: string;
    contentType?: 'document' | 'codebase';
  };
  payload?: EventPayload;
}
