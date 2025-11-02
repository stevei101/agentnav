import { AnalysisResult, VisualizationType } from '../types';

// Backend API URL - can be configured via environment variable
// Use window for browser environment compatibility
const BACKEND_API_URL =
  (typeof window !== 'undefined' && (window as any).VITE_API_URL) ||
  'http://localhost:8080';

interface AnalyzeRequest {
  document: string;
  content_type?: string;
}

interface AnalyzeResponse {
  summary: string;
  visualization: {
    type: 'MIND_MAP' | 'DEPENDENCY_GRAPH';
    title: string;
    nodes: Array<{
      id: string;
      label: string;
      group: string;
      type?: string;
      metadata?: any;
    }>;
    edges: Array<{
      from: string;
      to: string;
      label?: string;
      type?: string;
      confidence?: string;
    }>;
  };
  agent_workflow: {
    orchestration: any;
    agent_status: any;
    total_agents: number;
    successful_agents: number;
  };
  processing_time: number;
  generated_by: string;
}

/**
 * Run Agentic Navigator analysis using the backend ADK multi-agent system
 * This replaces direct Gemini API calls with backend orchestration
 */
export const runAgenticNavigator = async (
  documentText: string
): Promise<AnalysisResult> => {
  const request: AnalyzeRequest = {
    document: documentText,
    content_type: undefined, // Let the backend auto-detect
  };

  try {
    console.log('🎬 Starting ADK Multi-Agent Analysis via backend API');

    const response = await fetch(`${BACKEND_API_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        `Backend API error (${response.status}): ${errorData.detail || response.statusText}`
      );
    }

    const data: AnalyzeResponse = await response.json();

    console.log(
      `✅ ADK Analysis completed in ${data.processing_time.toFixed(2)}s`
    );
    console.log(
      `📊 Agent workflow: ${data.agent_workflow.successful_agents}/${data.agent_workflow.total_agents} agents successful`
    );

    // Convert backend response to frontend AnalysisResult format
    const result: AnalysisResult = {
      summary: data.summary,
      visualization: {
        type: data.visualization.type as VisualizationType,
        title: data.visualization.title,
        nodes: data.visualization.nodes,
        edges: data.visualization.edges,
      },
    };

    return result;
  } catch (error) {
    console.error('Error calling backend API:', error);

    // If backend is unavailable, fall back to legacy Gemini service
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.warn(
        '🔄 Backend unavailable, falling back to legacy Gemini service'
      );
      try {
        const { runAgenticNavigator: legacyRunner } = await import(
          './geminiService'
        );
        return await legacyRunner(documentText);
      } catch (legacyError) {
        console.error('Legacy fallback also failed:', legacyError);
        throw new Error(
          'Both backend API and legacy Gemini service are unavailable. Please check your connection and try again.'
        );
      }
    }

    throw new Error(
      `Failed to get analysis from Agentic Navigator: ${error.message}`
    );
  }
};

/**
 * Get agent status from the backend
 */
export const getAgentStatus = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/api/agents/status`);

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting agent status:', error);
    return {
      total_agents: 0,
      agents: {},
      adk_system: 'unavailable',
      error: error.message,
    };
  }
};

/**
 * Health check for the backend API
 */
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/healthz`);
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
};
