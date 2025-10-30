
export enum AgentName {
  ORCHESTRATOR = 'Orchestrator',
  SUMMARIZER = 'Summarizer',
  LINKER = 'Linker',
  VISUALIZER = 'Visualizer',
}

export enum AgentStatusValue {
  IDLE = 'Idle',
  PROCESSING = 'Processing',
  DONE = 'Done',
  ERROR = 'Error',
}

export interface AgentState {
  name: AgentName;
  status: AgentStatusValue;
  details: string;
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
