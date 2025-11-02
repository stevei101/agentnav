import React, { useState } from "react";
import { AgentDashboard } from "./AgentDashboard";
import { DocumentUpload } from "./DocumentUpload";
import { BrainCircuitIcon } from "./icons";

export const StreamingDashboard: React.FC = () => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [documentContent, setDocumentContent] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"dashboard" | "upload">(
    "upload"
  );

  const handleSessionStart = (sessionId: string, content: string) => {
    setCurrentSessionId(sessionId);
    setDocumentContent(content);
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
        {activeView === "dashboard" && currentSessionId && (
          <AgentDashboard
            sessionId={currentSessionId}
            documentContent={documentContent}
            contentType={documentContent ? "document" : undefined}
            onStreamStart={() => {
              // Optional: add custom handling when stream starts
            }}
          />
        )}
        {activeView === "upload" && (
          <DocumentUpload
            onSessionStart={handleSessionStart}
            isLoading={false}
          />
        )}
      </main>
    </div>
  );
};
