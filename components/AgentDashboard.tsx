import React, { useState, useEffect, useCallback } from "react";
import { AgentCard } from "./AgentCard";
import { AgentState, AgentStatusValue, AgentName } from "../types";
import { Activity, Zap, RotateCcw } from "lucide-react";

interface AgentDashboardProps {
  sessionId: string | null;
  onStreamStart?: (sessionId: string) => void;
}

const AGENT_TYPES: AgentName[] = [
  AgentName.SUMMARIZER,
  AgentName.LINKER,
  AgentName.VISUALIZER,
];

export const AgentDashboard: React.FC<AgentDashboardProps> = ({
  sessionId,
  onStreamStart,
}) => {
  const [agents, setAgents] = useState<AgentState[]>(
    AGENT_TYPES.map((name) => ({
      id: `agent-${name.toLowerCase()}`,
      name,
      status: AgentStatusValue.IDLE,
      details: `Ready to analyze content`,
      progress: 0,
      findings: [],
    }))
  );

  const [isStreaming, setIsStreaming] = useState(false);
  const [wsMessages, setWsMessages] = useState<number>(0);
  const [connectionStatus, setConnectionStatus] = useState<
    "idle" | "connecting" | "connected" | "error"
  >("idle");

  const initializeWebSocket = useCallback(() => {
    if (!sessionId) {
      setConnectionStatus("error");
      return;
    }

    setConnectionStatus("connecting");

    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/api/v1/navigate/stream?session_id=${sessionId}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus("connected");
        setIsStreaming(true);
        onStreamStart?.(sessionId);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle stream event and update agents
          handleStreamEvent(data);
          setWsMessages((prev) => prev + 1);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.onerror = () => {
        setConnectionStatus("error");
        setIsStreaming(false);
      };

      ws.onclose = () => {
        setConnectionStatus("idle");
        setIsStreaming(false);
      };

      return ws;
    } catch (err) {
      console.error("WebSocket initialization failed:", err);
      setConnectionStatus("error");
      setIsStreaming(false);
    }
  }, [sessionId, onStreamStart]);

  const handleStreamEvent = (event: any) => {
    // Map backend event format to agent state
    const agentName = event.agent as AgentName;
    const statusMap: Record<string, AgentStatusValue> = {
      queued: AgentStatusValue.QUEUED,
      processing: AgentStatusValue.PROCESSING,
      complete: AgentStatusValue.DONE,
      error: AgentStatusValue.ERROR,
    };

    setAgents((prev) =>
      prev.map((agent) => {
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
              if (
                event.payload.metrics.duration !== undefined &&
                event.payload.metrics.processingTime !== undefined
              ) {
                updatedAgent.progress = Math.min(
                  100,
                  (event.payload.metrics.processingTime /
                    event.payload.metrics.duration) *
                    100
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
      initializeWebSocket();
    }
  };

  const resetAnalysis = () => {
    setIsStreaming(false);
    setWsMessages(0);
    setConnectionStatus("idle");
    setAgents((prev) =>
      prev.map((agent) => ({
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
              {sessionId ? `Session: ${sessionId}` : "No active session"}
            </p>
            {connectionStatus !== "idle" && (
              <p className="text-sm mt-2">
                Status:{" "}
                <span
                  className={`font-semibold ${
                    connectionStatus === "connected"
                      ? "text-green-400"
                      : connectionStatus === "error"
                        ? "text-red-400"
                        : "text-yellow-400"
                  }`}
                >
                  {connectionStatus}
                </span>
                {wsMessages > 0 && (
                  <span className="text-gray-400"> ({wsMessages} events)</span>
                )}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={startAnalysis}
              disabled={isStreaming || !sessionId}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors flex items-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Start Analysis
            </button>
            <button
              onClick={resetAnalysis}
              disabled={!isStreaming && agents.every((a) => a.status === AgentStatusValue.IDLE)}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map((agent) => (
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
            <p className="text-white capitalize">{connectionStatus}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Events Received</p>
            <p className="text-white">{wsMessages}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Agents</p>
            <p className="text-white">
              {agents.filter((a) => a.status !== AgentStatusValue.IDLE).length}/
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
