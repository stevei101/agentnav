
import React from "react";
import { AgentState, AgentStatusValue } from "../types";
import {
  Bot,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  Link2,
  Eye,
} from "lucide-react";

interface AgentCardProps {
  agent: AgentState;
}

const agentIcons = {
  Summarizer: FileText,
  Linker: Link2,
  Visualizer: Eye,
  Orchestrator: Bot,
};

const agentColors = {
  Summarizer: "from-blue-500 to-cyan-500",
  Linker: "from-purple-500 to-pink-500",
  Visualizer: "from-orange-500 to-red-500",
  Orchestrator: "from-indigo-500 to-blue-500",
};

const statusConfig = {
  [AgentStatusValue.IDLE]: {
    color: "bg-gray-700 text-gray-400",
    icon: Bot,
  },
  [AgentStatusValue.QUEUED]: {
    color: "bg-slate-900/30 text-slate-300 border border-slate-500/30",
    icon: Bot,
  },
  [AgentStatusValue.PROCESSING]: {
    color: "bg-yellow-900/30 text-yellow-500 border border-yellow-500/30",
    icon: Loader2,
  },
  [AgentStatusValue.DONE]: {
    color: "bg-green-900/30 text-green-500 border border-green-500/30",
    icon: CheckCircle,
  },
  [AgentStatusValue.ERROR]: {
    color: "bg-red-900/30 text-red-500 border border-red-500/30",
    icon: AlertCircle,
  },
};

export const AgentCard: React.FC<AgentCardProps> = ({ agent }) => {
  const Icon =
    agentIcons[agent.name as keyof typeof agentIcons] || Bot;
  const colorGradient =
    agentColors[agent.name as keyof typeof agentColors] ||
    "from-gray-500 to-gray-600";
  const config = statusConfig[agent.status];
  const StatusIcon = config.icon;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-12 h-12 bg-gradient-to-br ${colorGradient} rounded-lg flex items-center justify-center`}
          >
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold">{agent.name}</h3>
            <p className="text-sm text-gray-400">{agent.details}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div className={`px-3 py-1 rounded-full text-xs flex items-center gap-1.5 ${config.color}`}>
          <StatusIcon
            className={`w-3.5 h-3.5 ${
              agent.status === AgentStatusValue.PROCESSING
                ? "animate-spin"
                : ""
            }`}
          />
          <span className="capitalize">{agent.status}</span>
        </div>
      </div>

      {/* Current Task */}
      {agent.currentTask && (
        <div className="mb-4">
          <p className="text-sm text-gray-300">{agent.currentTask}</p>
        </div>
      )}

      {/* Progress Bar */}
      {agent.status === AgentStatusValue.PROCESSING &&
        agent.progress !== undefined && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Progress</span>
              <span className="text-sm text-gray-300">{agent.progress}%</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${colorGradient} transition-all duration-500`}
                style={{ width: `${agent.progress}%` }}
              />
            </div>
          </div>
        )}

      {/* Findings */}
      {agent.findings && agent.findings.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-400">Findings:</p>
          <ul className="space-y-1">
            {agent.findings.map((finding, idx) => (
              <li
                key={idx}
                className="text-sm text-gray-300 flex items-start gap-2"
              >
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metrics */}
      {agent.metrics && (
        <div className="mt-4 pt-4 border-t border-gray-800 space-y-1">
          {agent.metrics.duration !== undefined && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Duration:</span>
              <span className="text-gray-300">
                {(agent.metrics.duration / 1000).toFixed(2)}s
              </span>
            </div>
          )}
          {agent.metrics.tokensProcessed !== undefined && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Tokens:</span>
              <span className="text-gray-300">
                {agent.metrics.tokensProcessed.toLocaleString()}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
