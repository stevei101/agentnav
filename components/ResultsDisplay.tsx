import React from 'react';
import { AnalysisResult } from '../types';
import { InteractiveGraph } from './InteractiveGraph';

export const ResultsDisplay: React.FC<{ result: AnalysisResult }> = ({
  result,
}) => {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Summary Section */}
      <div>
        <h2 className="text-2xl font-bold text-sky-400 mb-4 border-b-2 border-slate-700 pb-2">
          Summary
        </h2>
        <div className="bg-slate-800/50 p-6 rounded-lg prose prose-invert prose-p:text-slate-300 prose-strong:text-slate-100 max-w-none">
          <p>{result.summary}</p>
        </div>
      </div>

      {/* Interactive Visualization Section */}
      <div>
        <h2 className="text-2xl font-bold text-indigo-400 mb-4 border-b-2 border-slate-700 pb-2">
          {result.visualization.title}
        </h2>
        <div className="bg-slate-800/50 p-4 rounded-lg h-[60vh] min-h-[500px] w-full">
          {result.visualization.nodes.length > 0 ? (
            <InteractiveGraph
              nodes={result.visualization.nodes}
              edges={result.visualization.edges}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500">
              <p>No visual data was generated for this document.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
