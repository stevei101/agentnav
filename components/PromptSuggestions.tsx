/**
 * Prompt Suggestions Component (FR#201)
 *
 * React component for displaying AI-driven prompt suggestions
 * from the Suggestion Agent. Designed for integration with
 * the Prompt Vault application.
 *
 * Features:
 * - Analyze prompt text and get optimization suggestions
 * - Display structured output schema suggestions
 * - Show function calling hints
 * - Quality scoring with visual feedback
 * - Real-time analysis with loading states
 */

import React, { useState } from 'react';
import {
  analyzePrompt,
  checkSuggestionAgentHealth,
  formatQualityScore,
  getQualityScoreColor,
  type PromptSuggestionRequest,
  type PromptSuggestionResponse,
  type SuggestionHealthResponse,
} from '../services/suggestionService';

interface PromptSuggestionsProps {
  promptText: string;
  userContext?: string;
  onSuggestionApplied?: (suggestion: string) => void;
  className?: string;
}

export const PromptSuggestions: React.FC<PromptSuggestionsProps> = ({
  promptText,
  userContext,
  onSuggestionApplied,
  className = '',
}) => {
  const [suggestions, setSuggestions] =
    useState<PromptSuggestionResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentHealth, setAgentHealth] =
    useState<SuggestionHealthResponse | null>(null);

  // Check agent health on mount
  React.useEffect(() => {
    const checkHealth = async () => {
      const health = await checkSuggestionAgentHealth();
      setAgentHealth(health);
    };
    checkHealth();
  }, []);

  const handleAnalyze = async () => {
    if (!promptText.trim()) {
      setError('Please enter a prompt to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const request: PromptSuggestionRequest = {
        prompt_text: promptText,
        user_context: userContext,
      };

      const response = await analyzePrompt(request);
      setSuggestions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze prompt');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApplySuggestion = (suggestion: string) => {
    if (onSuggestionApplied) {
      onSuggestionApplied(suggestion);
    }
  };

  return (
    <div className={`prompt-suggestions ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          AI Prompt Suggestions
        </h3>

        {/* Agent Health Indicator */}
        {agentHealth && (
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                agentHealth.available ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-gray-600">
              {agentHealth.available ? 'Agent Ready' : 'Agent Unavailable'}
            </span>
          </div>
        )}
      </div>

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={isAnalyzing || !agentHealth?.available}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors mb-4"
      >
        {isAnalyzing ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Analyzing...
          </span>
        ) : (
          'Get AI Suggestions'
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Suggestions Display */}
      {suggestions && (
        <div className="space-y-6">
          {/* Quality Score */}
          <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                Prompt Quality Score
              </span>
              <span
                className={`text-2xl font-bold ${getQualityScoreColor(
                  suggestions.quality_score
                )}`}
              >
                {formatQualityScore(suggestions.quality_score)}
              </span>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${suggestions.quality_score * 10}%` }}
              />
            </div>
          </div>

          {/* Optimization Suggestions */}
          {suggestions.optimization_suggestions.length > 0 && (
            <div className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">
                💡 Optimization Suggestions
              </h4>
              <ul className="space-y-2">
                {suggestions.optimization_suggestions.map(
                  (suggestion, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span className="flex-1">{suggestion}</span>
                      <button
                        onClick={() => handleApplySuggestion(suggestion)}
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                      >
                        Apply
                      </button>
                    </li>
                  )
                )}
              </ul>
            </div>
          )}

          {/* Strengths and Weaknesses */}
          <div className="grid grid-cols-2 gap-4">
            {/* Strengths */}
            {suggestions.strengths.length > 0 && (
              <div className="border border-green-200 bg-green-50 rounded-lg p-4">
                <h4 className="font-semibold text-green-900 mb-2 text-sm">
                  ✓ Strengths
                </h4>
                <ul className="space-y-1">
                  {suggestions.strengths.map((strength, index) => (
                    <li key={index} className="text-xs text-green-800">
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weaknesses */}
            {suggestions.weaknesses.length > 0 && (
              <div className="border border-orange-200 bg-orange-50 rounded-lg p-4">
                <h4 className="font-semibold text-orange-900 mb-2 text-sm">
                  ⚠ Weaknesses
                </h4>
                <ul className="space-y-1">
                  {suggestions.weaknesses.map((weakness, index) => (
                    <li key={index} className="text-xs text-orange-800">
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Structured Output Schema */}
          {suggestions.structured_output_schema && (
            <div className="border border-purple-200 bg-purple-50 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-3">
                📋 Suggested Structured Output Schema
              </h4>
              <pre className="text-xs bg-white p-3 rounded border border-purple-200 overflow-x-auto">
                {JSON.stringify(suggestions.structured_output_schema, null, 2)}
              </pre>
              <button
                onClick={() =>
                  navigator.clipboard.writeText(
                    JSON.stringify(
                      suggestions.structured_output_schema,
                      null,
                      2
                    )
                  )
                }
                className="mt-2 text-xs text-purple-600 hover:text-purple-800 underline"
              >
                Copy Schema
              </button>
            </div>
          )}

          {/* Function Calling Hint */}
          {suggestions.function_calling_hint && (
            <div className="border border-indigo-200 bg-indigo-50 rounded-lg p-4">
              <h4 className="font-semibold text-indigo-900 mb-3">
                🔧 Function Calling Suggestion
              </h4>
              {suggestions.function_calling_hint.name && (
                <p className="text-sm text-indigo-800 mb-2">
                  <strong>Function:</strong>{' '}
                  {suggestions.function_calling_hint.name}
                </p>
              )}
              {suggestions.function_calling_hint.description && (
                <p className="text-sm text-indigo-800 mb-2">
                  {suggestions.function_calling_hint.description}
                </p>
              )}
              {suggestions.function_calling_hint.rationale && (
                <p className="text-xs text-indigo-700 italic mt-2">
                  {suggestions.function_calling_hint.rationale}
                </p>
              )}
              {suggestions.function_calling_hint.parameters && (
                <pre className="text-xs bg-white p-3 rounded border border-indigo-200 overflow-x-auto mt-3">
                  {JSON.stringify(
                    suggestions.function_calling_hint.parameters,
                    null,
                    2
                  )}
                </pre>
              )}
            </div>
          )}

          {/* Actionable Improvements */}
          {suggestions.actionable_improvements.length > 0 && (
            <div className="border border-blue-200 bg-blue-50 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-3">
                🎯 Actionable Improvements
              </h4>
              <ul className="space-y-2">
                {suggestions.actionable_improvements.map(
                  (improvement, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-blue-800"
                    >
                      <span className="text-blue-600 mt-0.5">{index + 1}.</span>
                      <span>{improvement}</span>
                    </li>
                  )
                )}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PromptSuggestions;
