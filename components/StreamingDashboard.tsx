import React, { useState } from "react";
import { AgentName, AgentStatusValue } from "../types";
import { AgentDashboard } from "./AgentDashboard";
import { BrainCircuitIcon } from "./icons";

export const StreamingDashboard: React.FC = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"dashboard" | "upload">(
    "dashboard"
  );

  const handleNewSession = () => {
    // Generate a new session ID
    const newSessionId = `session-${Date.now()}`;
    setCurrentSessionId(newSessionId);
    setActiveView("dashboard");
  };

  return (
    <div className="min-h-screen bg-slate-900 font-sans flex flex-col">
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/50 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <BrainCircuitIcon className="w-8 h-8 text-sky-400" />
            <h1 className="text-2xl font-bold ml-3 bg-gradient-to-r from-sky-400 to-indigo-400 text-transparent bg-clip-text">
              Agentic Navigator
            </h1>
            <span className="ml-3 text-xs px-2 py-1 bg-blue-900/50 text-blue-300 rounded-full border border-blue-500/30">
              Real-time Streaming
            </span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveView("upload")}
              className={`px-4 py-2 rounded-lg transition-colors text-sm ${
                activeView === "upload"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              New Analysis
            </button>
            <button
              onClick={() => setActiveView("dashboard")}
              className={`px-4 py-2 rounded-lg transition-colors text-sm ${
                activeView === "dashboard"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-8">
        {activeView === "dashboard" && (
          <AgentDashboard
            sessionId={currentSessionId}
            onStreamStart={() => {
              // Optional: add custom handling when stream starts
            }}
          />
        )}
        {activeView === "upload" && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
            <h2 className="text-2xl text-white mb-4">Start New Analysis</h2>
            <p className="text-gray-400 mb-6">
              Upload a document or provide text to analyze with our multi-agent system
            </p>
            <button
              onClick={handleNewSession}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Create New Session
            </button>
            {currentSessionId && (
              <p className="text-xs text-gray-500 mt-4">Session: {currentSessionId}</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
