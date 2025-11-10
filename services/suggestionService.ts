/**
 * Suggestion Service - Client for Prompt Vault Intelligence (FR#201)
 * 
 * Provides TypeScript client for calling the Suggestion Agent API
 * from the Prompt Vault frontend application.
 * 
 * This service integrates the agentnav backend's Suggestion Agent
 * with the Prompt Vault application via secure HTTP calls.
 */

// API Configuration
const API_BASE_URL = import.meta.env.VITE_AGENTNAV_API_URL || 'http://localhost:8080';
const SUGGESTIONS_ENDPOINT = `${API_BASE_URL}/api/v1/suggestions`;

/**
 * Request payload for prompt analysis
 */
export interface PromptSuggestionRequest {
  prompt_text: string;
  user_context?: string;
  existing_schema?: Record<string, any>;
}

/**
 * Structured output schema suggestion
 */
export interface StructuredOutputSchema {
  type: string;
  properties?: Record<string, any>;
  required?: string[];
  description?: string;
}

/**
 * Function calling hint suggestion
 */
export interface FunctionCallingHint {
  name?: string;
  description?: string;
  parameters?: Record<string, any>;
  rationale?: string;
}

/**
 * Response from prompt analysis
 */
export interface PromptSuggestionResponse {
  agent: string;
  prompt_analyzed: string;
  optimization_suggestions: string[];
  structured_output_schema: StructuredOutputSchema | null;
  function_calling_hint: FunctionCallingHint | null;
  quality_score: number;
  strengths: string[];
  weaknesses: string[];
  actionable_improvements: string[];
  processing_complete: boolean;
  timestamp: number;
}

/**
 * Error response from API
 */
export interface SuggestionError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

/**
 * Health check response
 */
export interface SuggestionHealthResponse {
  status: string;
  agent: string;
  available: boolean;
  state?: string;
  message?: string;
  error?: string;
}

/**
 * Analyze a prompt and get AI-driven suggestions
 * 
 * @param request - Prompt analysis request
 * @returns Promise with suggestion response
 * @throws Error if API call fails
 */
export async function analyzePrompt(
  request: PromptSuggestionRequest
): Promise<PromptSuggestionResponse> {
  try {
    const response = await fetch(`${SUGGESTIONS_ENDPOINT}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData: SuggestionError = await response.json();
      throw new Error(errorData.message || `API error: ${response.status}`);
    }

    const data: PromptSuggestionResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to analyze prompt: ${error.message}`);
    }
    throw new Error('Failed to analyze prompt: Unknown error');
  }
}

/**
 * Check if the Suggestion Agent is available and healthy
 * 
 * @returns Promise with health status
 */
export async function checkSuggestionAgentHealth(): Promise<SuggestionHealthResponse> {
  try {
    const response = await fetch(`${SUGGESTIONS_ENDPOINT}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return {
        status: 'error',
        agent: 'suggestion',
        available: false,
        message: `Health check failed: ${response.status}`,
      };
    }

    const data: SuggestionHealthResponse = await response.json();
    return data;
  } catch (error) {
    return {
      status: 'error',
      agent: 'suggestion',
      available: false,
      message: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Get example prompts for testing
 * 
 * @returns Promise with example prompts
 */
export async function getExamplePrompts(): Promise<{
  examples: Array<{
    name: string;
    prompt_text: string;
    user_context: string;
    expected_suggestions: string[];
  }>;
  usage_tips: string[];
}> {
  try {
    const response = await fetch(`${SUGGESTIONS_ENDPOINT}/examples`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch examples: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch example prompts:', error);
    // Return fallback examples
    return {
      examples: [
        {
          name: 'Simple Task',
          prompt_text: 'Write a function that calculates the factorial of a number',
          user_context: 'Educational coding tutorial',
          expected_suggestions: [
            'Specify programming language',
            'Add input validation requirements',
          ],
        },
      ],
      usage_tips: [
        'Provide context about the intended use case',
        'Be specific about expected output format',
      ],
    };
  }
}

/**
 * Format quality score as a percentage
 * 
 * @param score - Quality score (1-10)
 * @returns Formatted percentage string
 */
export function formatQualityScore(score: number): string {
  return `${(score * 10).toFixed(0)}%`;
}

/**
 * Get quality score color based on score value
 * 
 * @param score - Quality score (1-10)
 * @returns Tailwind CSS color class
 */
export function getQualityScoreColor(score: number): string {
  if (score >= 8) return 'text-green-600';
  if (score >= 6) return 'text-yellow-600';
  if (score >= 4) return 'text-orange-600';
  return 'text-red-600';
}

/**
 * Export all types and functions
 */
export default {
  analyzePrompt,
  checkSuggestionAgentHealth,
  getExamplePrompts,
  formatQualityScore,
  getQualityScoreColor,
};
