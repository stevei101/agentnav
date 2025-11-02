import { useState } from 'react';
import { AgentDashboard } from './components/AgentDashboard';
import { DocumentUpload } from './components/DocumentUpload';
import { SessionHistory } from './components/SessionHistory';

export default function App() {
  const [activeView, setActiveView] = useState<'dashboard' | 'upload' | 'history'>('dashboard');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white">AN</span>
              </div>
              <div>
                <h1 className="text-white">Agentic Navigator</h1>
                <p className="text-sm text-gray-400">Multi-Agent Knowledge Explorer</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveView('upload')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'upload'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                New Analysis
              </button>
              <button
                onClick={() => setActiveView('dashboard')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveView('history')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeView === 'history'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                History
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {activeView === 'dashboard' && (
          <AgentDashboard sessionId={currentSessionId} />
        )}
        {activeView === 'upload' && (
          <DocumentUpload onSessionStart={(sessionId) => {
            setCurrentSessionId(sessionId);
            setActiveView('dashboard');
          }} />
        )}
        {activeView === 'history' && (
          <SessionHistory onSessionSelect={(sessionId) => {
            setCurrentSessionId(sessionId);
            setActiveView('dashboard');
          }} />
        )}
      </main>
    </div>
  );
}
