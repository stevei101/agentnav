import { useState, useEffect } from 'react';
import { AgentCard } from './AgentCard';
import { A2ACommunication } from './A2ACommunication';
import { KnowledgeGraph } from './KnowledgeGraph';
import { ResultsPanel } from './ResultsPanel';
import { Activity, Network, Eye, Zap } from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  type: 'summarizer' | 'linker' | 'visualizer';
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  currentTask?: string;
  findings: string[];
}

interface A2AMessage {
  id: string;
  from: string;
  to: string;
  type: 'request' | 'response' | 'broadcast';
  content: string;
  timestamp: Date;
}

export function AgentDashboard({ sessionId }: { sessionId: string | null }) {
  const [agents, setAgents] = useState<AgentStatus[]>([
    {
      id: 'agent-summarizer',
      name: 'Summarizer Agent',
      type: 'summarizer',
      status: 'idle',
      progress: 0,
      findings: []
    },
    {
      id: 'agent-linker',
      name: 'Linker Agent',
      type: 'linker',
      status: 'idle',
      progress: 0,
      findings: []
    },
    {
      id: 'agent-visualizer',
      name: 'Visualizer Agent',
      type: 'visualizer',
      status: 'idle',
      progress: 0,
      findings: []
    }
  ]);

  const [messages, setMessages] = useState<A2AMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  // Simulate agent activity
  useEffect(() => {
    if (!isRunning || !sessionId) return;

    const interval = setInterval(() => {
      simulateAgentActivity();
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning, sessionId]);

  const simulateAgentActivity = () => {
    setAgents(prev => {
      const updated = [...prev];
      const activeAgent = updated.find(a => a.status === 'processing');
      
      if (activeAgent) {
        activeAgent.progress = Math.min(100, activeAgent.progress + 15);
        
        if (activeAgent.progress >= 100) {
          activeAgent.status = 'completed';
          
          // Add findings based on agent type
          if (activeAgent.type === 'summarizer') {
            activeAgent.findings = [
              'Identified 5 key themes across 127 pages',
              'Extracted 23 critical insights',
              'Generated executive summary (850 words)'
            ];
          } else if (activeAgent.type === 'linker') {
            activeAgent.findings = [
              'Found 47 cross-references between sections',
              'Identified 12 external citations',
              'Mapped 8 concept relationships'
            ];
          } else if (activeAgent.type === 'visualizer') {
            activeAgent.findings = [
              'Generated knowledge graph with 156 nodes',
              'Created 3 timeline visualizations',
              'Built concept hierarchy tree'
            ];
          }

          // Send A2A message
          const newMessage: A2AMessage = {
            id: `msg-${Date.now()}`,
            from: activeAgent.name,
            to: 'All Agents',
            type: 'broadcast',
            content: `Completed analysis: ${activeAgent.findings[0]}`,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, newMessage]);

          // Start next agent
          const nextAgent = updated.find(a => a.status === 'idle');
          if (nextAgent) {
            nextAgent.status = 'processing';
            nextAgent.currentTask = `Processing ${nextAgent.type} analysis...`;
          } else {
            setIsRunning(false);
          }
        }
      }
      
      return updated;
    });
  };

  const startAnalysis = () => {
    setIsRunning(true);
    setMessages([]);
    setAgents(prev => {
      const updated = prev.map(agent => ({
        ...agent,
        status: 'idle' as const,
        progress: 0,
        findings: []
      }));
      // Start first agent
      updated[0].status = 'processing';
      updated[0].currentTask = 'Analyzing document structure...';
      return updated;
    });

    // Initial A2A message
    const initMessage: A2AMessage = {
      id: `msg-init`,
      from: 'Orchestrator',
      to: 'All Agents',
      type: 'broadcast',
      content: 'Initiating multi-agent analysis session',
      timestamp: new Date()
    };
    setMessages([initMessage]);
  };

  const resetAnalysis = () => {
    setIsRunning(false);
    setAgents(prev => prev.map(agent => ({
      ...agent,
      status: 'idle' as const,
      progress: 0,
      findings: [],
      currentTask: undefined
    })));
    setMessages([]);
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
          </div>
          <div className="flex gap-3">
            <button
              onClick={startAnalysis}
              disabled={isRunning || !sessionId}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors flex items-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Start Analysis
            </button>
            <button
              onClick={resetAnalysis}
              disabled={!isRunning && agents.every(a => a.status === 'idle')}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* A2A Communication */}
      <A2ACommunication messages={messages} />

      {/* Knowledge Graph and Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <KnowledgeGraph agents={agents} />
        <ResultsPanel agents={agents} />
      </div>

      {/* GPU Stats */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-purple-500" />
          <h3 className="text-white">GPU Acceleration Stats</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Model</p>
            <p className="text-white">Gemini 1.5 Pro</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">GPU Utilization</p>
            <p className="text-white">{isRunning ? '87%' : '0%'}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Tokens Processed</p>
            <p className="text-white">{isRunning ? '47.2K' : '0'}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Avg Response Time</p>
            <p className="text-white">{isRunning ? '1.2s' : '-'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
