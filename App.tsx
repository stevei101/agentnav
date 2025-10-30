
import React, { useState, useCallback, useRef } from 'react';
import { AgentState, AgentName, AgentStatusValue, AnalysisResult } from './types';
import { runAgenticNavigator } from './services/geminiService';
import { AgentCard } from './components/AgentCard';
import { ResultsDisplay } from './components/ResultsDisplay';
import { UploadIcon, BrainCircuitIcon } from './components/icons';

const initialAgents: AgentState[] = [
  { name: AgentName.ORCHESTRATOR, status: AgentStatusValue.IDLE, details: 'Awaiting instructions' },
  { name: AgentName.SUMMARIZER, status: AgentStatusValue.IDLE, details: 'Ready to summarize' },
  { name: AgentName.LINKER, status: AgentStatusValue.IDLE, details: 'Ready to find connections' },
  { name: AgentName.VISUALIZER, status: AgentStatusValue.IDLE, details: 'Ready to visualize data' },
];

const App: React.FC = () => {
  const [documentText, setDocumentText] = useState<string>('');
  const [agents, setAgents] = useState<AgentState[]>(initialAgents);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setDocumentText(e.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const simulateAgentActivity = () => {
    const agentNames = [AgentName.ORCHESTRATOR, AgentName.SUMMARIZER, AgentName.LINKER, AgentName.VISUALIZER];
    let delay = 0;

    agentNames.forEach((name, index) => {
        setTimeout(() => {
            setAgents(prev => prev.map(a => a.name === name ? { ...a, status: AgentStatusValue.PROCESSING, details: 'Analyzing document...' } : a));
        }, delay);
        delay += 500;
    });
  };

  const handleSubmit = useCallback(async () => {
    if (!documentText.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setAgents(initialAgents);
    
    simulateAgentActivity();

    try {
      const analysisResult = await runAgenticNavigator(documentText);
      setResult(analysisResult);
      setAgents(prev => prev.map(a => ({ ...a, status: AgentStatusValue.DONE, details: 'Analysis complete' })));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(errorMessage);
      setAgents(prev => prev.map(a => ({ ...a, status: AgentStatusValue.ERROR, details: 'Failed' })));
    } finally {
      setIsLoading(false);
    }
  }, [documentText, isLoading]);


  return (
    <div className="min-h-screen bg-slate-900 font-sans flex flex-col">
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center">
          <BrainCircuitIcon className="w-8 h-8 text-sky-400" />
          <h1 className="text-2xl font-bold ml-3 bg-gradient-to-r from-sky-400 to-indigo-400 text-transparent bg-clip-text">
            Agentic Navigator
          </h1>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Panel: Input & Agents */}
          <aside className="lg:col-span-4 xl:col-span-3">
            <div className="sticky top-24 space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-2 text-slate-300">Input Document</h2>
                <div className="bg-slate-800 rounded-lg p-4 space-y-4">
                  <textarea
                    value={documentText}
                    onChange={(e) => setDocumentText(e.target.value)}
                    placeholder="Paste your document or code here..."
                    className="w-full h-48 bg-slate-900 border border-slate-700 rounded-md p-3 text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none transition resize-none"
                    disabled={isLoading}
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={triggerFileUpload}
                      className="flex-1 flex items-center justify-center bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold py-2 px-4 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={isLoading}
                    >
                      <UploadIcon className="w-5 h-5 mr-2" />
                      Upload File
                    </button>
                    <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".txt,.md,.js,.py,.html,.css,.json, .ts, .tsx"/>
                  </div>
                  <button
                    onClick={handleSubmit}
                    className="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold py-3 px-4 rounded-md transition duration-200 flex items-center justify-center disabled:opacity-50 disabled:bg-sky-800 disabled:cursor-wait"
                    disabled={!documentText.trim() || isLoading}
                  >
                    {isLoading ? 'Analyzing...' : 'Run Navigator'}
                  </button>
                </div>
              </div>
              
              <div>
                <h2 className="text-lg font-semibold mb-2 text-slate-300">Agent Status</h2>
                <div className="space-y-2">
                  {agents.map(agent => (
                    <AgentCard key={agent.name} agent={agent} />
                  ))}
                </div>
              </div>

            </div>
          </aside>
          
          {/* Right Panel: Results */}
          <section className="lg:col-span-8 xl:col-span-9 bg-slate-800/20 rounded-lg p-6 min-h-[60vh]">
            {isLoading && !result && (
              <div className="flex flex-col items-center justify-center h-full text-slate-400">
                <BrainCircuitIcon className="w-16 h-16 mb-4 animate-pulse text-sky-500" />
                <p className="text-xl font-semibold">Agents are collaborating...</p>
                <p>Analyzing document to extract insights.</p>
              </div>
            )}
            {error && (
              <div className="flex flex-col items-center justify-center h-full text-rose-400 bg-rose-900/20 rounded-lg p-4">
                <p className="font-bold text-lg">Analysis Failed</p>
                <p className="text-sm text-rose-300 text-center">{error}</p>
              </div>
            )}
            {!isLoading && !result && !error && (
                <div className="flex flex-col items-center justify-center h-full text-slate-500">
                  <div className="text-center p-8 border-2 border-dashed border-slate-700 rounded-lg">
                      <h3 className="text-xl font-semibold text-slate-400">Welcome to Agentic Navigator</h3>
                      <p className="mt-2 max-w-md">Provide a document or code snippet on the left and click "Run Navigator" to begin the multi-agent analysis.</p>
                  </div>
                </div>
            )}
            {result && <ResultsDisplay result={result} />}
          </section>

        </div>
      </main>
    </div>
  );
};

export default App;
