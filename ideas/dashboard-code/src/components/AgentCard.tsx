import { Bot, CheckCircle, AlertCircle, Loader2, FileText, Link2, Eye } from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  type: 'summarizer' | 'linker' | 'visualizer';
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  currentTask?: string;
  findings: string[];
}

const agentIcons = {
  summarizer: FileText,
  linker: Link2,
  visualizer: Eye
};

const agentColors = {
  summarizer: 'from-blue-500 to-cyan-500',
  linker: 'from-purple-500 to-pink-500',
  visualizer: 'from-orange-500 to-red-500'
};

const statusColors = {
  idle: 'bg-gray-700 text-gray-400',
  processing: 'bg-yellow-900/30 text-yellow-500 border border-yellow-500/30',
  completed: 'bg-green-900/30 text-green-500 border border-green-500/30',
  error: 'bg-red-900/30 text-red-500 border border-red-500/30'
};

export function AgentCard({ agent }: { agent: AgentStatus }) {
  const Icon = agentIcons[agent.type];
  const colorGradient = agentColors[agent.type];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 bg-gradient-to-br ${colorGradient} rounded-lg flex items-center justify-center`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-white">{agent.name}</h3>
            <p className="text-sm text-gray-400 capitalize">{agent.type}</p>
          </div>
        </div>
        <StatusBadge status={agent.status} />
      </div>

      {/* Current Task */}
      {agent.currentTask && (
        <div className="mb-4">
          <p className="text-sm text-gray-300">{agent.currentTask}</p>
        </div>
      )}

      {/* Progress Bar */}
      {agent.status === 'processing' && (
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
      {agent.findings.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-400">Findings:</p>
          <ul className="space-y-1">
            {agent.findings.map((finding, idx) => (
              <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: AgentStatus['status'] }) {
  const statusIcons = {
    idle: Bot,
    processing: Loader2,
    completed: CheckCircle,
    error: AlertCircle
  };

  const Icon = statusIcons[status];

  return (
    <div className={`px-3 py-1 rounded-full text-xs flex items-center gap-1.5 ${statusColors[status]}`}>
      <Icon className={`w-3.5 h-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
      <span className="capitalize">{status}</span>
    </div>
  );
}
