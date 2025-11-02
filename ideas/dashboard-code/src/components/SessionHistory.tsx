import { Clock, FileText, CheckCircle, TrendingUp } from 'lucide-react';

interface Session {
  id: string;
  name: string;
  type: 'research' | 'technical' | 'codebase';
  date: Date;
  filesCount: number;
  status: 'completed' | 'in-progress' | 'failed';
  agents: number;
  insights: number;
}

interface SessionHistoryProps {
  onSessionSelect: (sessionId: string) => void;
}

const mockSessions: Session[] = [
  {
    id: 'session-1',
    name: 'Neural Networks Research Papers',
    type: 'research',
    date: new Date('2025-10-28'),
    filesCount: 5,
    status: 'completed',
    agents: 3,
    insights: 47
  },
  {
    id: 'session-2',
    name: 'API Documentation Analysis',
    type: 'technical',
    date: new Date('2025-10-25'),
    filesCount: 12,
    status: 'completed',
    agents: 3,
    insights: 63
  },
  {
    id: 'session-3',
    name: 'React Codebase Review',
    type: 'codebase',
    date: new Date('2025-10-22'),
    filesCount: 87,
    status: 'completed',
    agents: 3,
    insights: 129
  }
];

const typeColors = {
  research: 'bg-blue-900/30 text-blue-400 border-blue-500/30',
  technical: 'bg-purple-900/30 text-purple-400 border-purple-500/30',
  codebase: 'bg-orange-900/30 text-orange-400 border-orange-500/30'
};

const statusColors = {
  completed: 'bg-green-900/30 text-green-400',
  'in-progress': 'bg-yellow-900/30 text-yellow-400',
  failed: 'bg-red-900/30 text-red-400'
};

export function SessionHistory({ onSessionSelect }: SessionHistoryProps) {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl text-white mb-2">Session History</h2>
        <p className="text-gray-400">
          View and manage your previous analysis sessions
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-900/30 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl text-white">12</p>
              <p className="text-sm text-gray-400">Total Sessions</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-900/30 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl text-white">347</p>
              <p className="text-sm text-gray-400">Files Analyzed</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-900/30 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl text-white">892</p>
              <p className="text-sm text-gray-400">Insights Found</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-orange-900/30 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="text-2xl text-white">47h</p>
              <p className="text-sm text-gray-400">Processing Time</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="space-y-4">
        {mockSessions.map(session => (
          <div
            key={session.id}
            onClick={() => onSessionSelect(session.id)}
            className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-white text-lg">{session.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs border ${typeColors[session.type]}`}>
                    {session.type}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${statusColors[session.status]}`}>
                    {session.status}
                  </span>
                </div>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{session.date.toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    <span>{session.filesCount} files</span>
                  </div>
                  <div>
                    <span>{session.agents} agents</span>
                  </div>
                  <div>
                    <span>{session.insights} insights</span>
                  </div>
                </div>
              </div>
              <button className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors">
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State (if no sessions) */}
      {mockSessions.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-white text-xl mb-2">No sessions yet</h3>
          <p className="text-gray-400 mb-6">
            Start your first analysis to see your session history
          </p>
          <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Start New Analysis
          </button>
        </div>
      )}
    </div>
  );
}
