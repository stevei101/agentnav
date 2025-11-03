import React, { useState } from 'react';
import { AgentCard } from './AgentCard';
import {
  AgentState,
  AgentStatusValue,
  AgentName,
  AgentStreamEvent,
} from '../types';
import { Activity, Zap, RotateCcw } from 'lucide-react';
import { useAgentStream } from '../hooks/useAgentStream';

interface AgentDashboardProps {
  sessionId: string | null;
  documentContent?: string | null;
  contentType?: 'document' | 'codebase';
  onStreamStart?: (sessionId: string) => void;
}

const AGENT_TYPES: AgentName[] = [
  AgentName.SUMMARIZER,
  AgentName.LINKER,
  AgentName.VISUALIZER,
];

export const AgentDashboard: React.FC<AgentDashboardProps> = ({
  sessionId,
  documentContent,
  contentType = 'document',
  onStreamStart,
}) => {
  const [agents, setAgents] = useState<AgentState[]>(
    AGENT_TYPES.map(name => ({
      id: `agent-${name.toLowerCase()}`,
      name,
      status: AgentStatusValue.IDLE,
      details: `Ready to analyze content`,
      progress: 0,
      findings: [],
    }))
  );

  const {
    events,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    send,
  } = useAgentStream({
    sessionId,
    onEvent: (event: AgentStreamEvent) => {
      handleStreamEvent(event);
    },
    onError: (err: Error) => {
      console.error('Stream error:', err);
    },
    autoConnect: false, // Manual control
  });

  const handleStreamEvent = (event: AgentStreamEvent) => {
    // Map backend event format to agent state
    const agentName = event.agent as AgentName;
    const statusMap: Record<string, AgentStatusValue> = {
      queued: AgentStatusValue.QUEUED,
      processing: AgentStatusValue.PROCESSING,
      complete: AgentStatusValue.DONE,
      error: AgentStatusValue.ERROR,
    };

    setAgents(prev =>
      prev.map(agent => {
        if (agent.name === agentName) {
          const updatedAgent = { ...agent };
          updatedAgent.status = statusMap[event.status] || agent.status;

          if (event.payload) {
            if (event.payload.summary) {
              updatedAgent.findings = [
                ...(updatedAgent.findings || []),
                event.payload.summary,
              ];
            }
            if (event.payload.metrics) {
              updatedAgent.metrics = event.payload.metrics;
              // Calculate progress based on processing time if available
              if (event.payload.metrics.processingTime !== undefined) {
                updatedAgent.progress = Math.min(
                  100,
                  Math.floor((event.payload.metrics.processingTime / 1000) * 10)
                );
              }
            }
            if (event.payload.errorMessage) {
              updatedAgent.details = event.payload.errorMessage;
            }
          }

          return updatedAgent;
        }
        return agent;
      })
    );
  };

  const startAnalysis = () => {
    if (sessionId) {
      connect();

      // Send document content after connection is established
      // We'll use a small delay to ensure connection is ready
      setTimeout(() => {
        if (send && documentContent) {
          send({
            document: documentContent,
            content_type: contentType,
            include_metadata: true,
            include_partial_results: true,
          });
        }
      }, 100);

      onStreamStart?.(sessionId);
    }
  };

  const resetAnalysis = () => {
    disconnect();
    setAgents(prev =>
      prev.map(agent => ({
        ...agent,
        status: AgentStatusValue.IDLE,
        progress: 0,
        findings: [],
        details: `Ready to analyze content`,
        metrics: undefined,
      }))
    );
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl text-white mb-2">Analysis Control</h2>
            <p className="text-gray-400">
              {sessionId ? `Session: ${sessionId}` : 'No active session'}
            </p>
            {!isConnecting && !isConnected && error && (
              <p className="text-sm mt-2">
                Status:{' '}
                <span className="font-semibold text-red-400">error</span>
              </p>
            )}
            {isConnecting && (
              <p className="text-sm mt-2">
                Status:{' '}
                <span className="font-semibold text-yellow-400">
                  connecting
                </span>
              </p>
            )}
            {isConnected && (
              <p className="text-sm mt-2">
                Status:{' '}
                <span className="font-semibold text-green-400">connected</span>
                {events.length > 0 && (
                  <span className="text-gray-400">
                    {' '}
                    ({events.length} events)
                  </span>
                )}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={startAnalysis}
              disabled={isConnected || isConnecting || !sessionId}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors flex items-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Start Analysis
            </button>
            <button
              onClick={resetAnalysis}
              disabled={
                !isConnected &&
                agents.every(a => a.status === AgentStatusValue.IDLE)
              }
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
              aria-label="Reset analysis"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* Stats Panel */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-purple-500" />
          <h3 className="text-white">Stream Statistics</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Status</p>
            <p className="text-white capitalize">
              {isConnected
                ? 'connected'
                : isConnecting
                  ? 'connecting'
                  : error
                    ? 'error'
                    : 'idle'}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Events Received</p>
            <p className="text-white">{events.length}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Agents</p>
            <p className="text-white">
              {agents.filter(a => a.status !== AgentStatusValue.IDLE).length}/
              {agents.length}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Total Findings</p>
            <p className="text-white">
              {agents.reduce((sum, a) => sum + (a.findings?.length || 0), 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
