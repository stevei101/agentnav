import { FileText, Download, Share2 } from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  type: 'summarizer' | 'linker' | 'visualizer';
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  currentTask?: string;
  findings: string[];
}

export function ResultsPanel({ agents }: { agents: AgentStatus[] }) {
  const completedAgents = agents.filter(a => a.status === 'completed');
  const allFindings = completedAgents.flatMap(a => a.findings);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-green-500" />
          <h3 className="text-white">Analysis Results</h3>
        </div>
        {allFindings.length > 0 && (
          <div className="flex gap-2">
            <button className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors">
              <Download className="w-4 h-4" />
            </button>
            <button className="p-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors">
              <Share2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {allFindings.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No results yet</p>
            <p className="text-sm mt-1">Analysis results will appear here</p>
          </div>
        ) : (
          <>
            {/* Summary Section */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white mb-2">Executive Summary</h4>
              <p className="text-gray-300 text-sm leading-relaxed">
                Multi-agent analysis successfully completed. The system processed and analyzed
                complex documentation using three specialized agents working in coordination
                through the A2A protocol.
              </p>
            </div>

            {/* Key Insights */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white mb-3">Key Insights</h4>
              <ul className="space-y-2">
                {allFindings.map((finding, idx) => (
                  <li key={idx} className="text-gray-300 text-sm flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Agent Contributions */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white mb-3">Agent Contributions</h4>
              <div className="space-y-3">
                {completedAgents.map(agent => (
                  <div key={agent.id} className="border-l-2 border-blue-500 pl-3">
                    <p className="text-gray-300 mb-1">{agent.name}</p>
                    <p className="text-sm text-gray-400">
                      {agent.findings.length} findings • Completed
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-white mb-3">Next Steps</h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>• Review the generated knowledge graph for concept relationships</li>
                <li>• Export findings for further analysis</li>
                <li>• Share results with team members</li>
                <li>• Schedule follow-up analysis on related documents</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
