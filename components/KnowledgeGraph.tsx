import React, { useEffect, useRef } from 'react';
import { Network } from 'lucide-react';
import type { AgentState } from '../types';

interface KnowledgeGraphProps {
  agents: AgentState[];
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ agents }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Check if any agent has completed
    const hasCompleted = agents.some(a => a.status === 'Done');
    if (!hasCompleted) return;

    // Draw knowledge graph
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const radius = Math.min(rect.width, rect.height) / 3;

    // Draw central node
    ctx.beginPath();
    ctx.arc(centerX, centerY, 30, 0, Math.PI * 2);
    ctx.fillStyle = '#3b82f6';
    ctx.fill();
    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw concept nodes
    const concepts = 8;
    for (let i = 0; i < concepts; i++) {
      const angle = (i / concepts) * Math.PI * 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;

      // Draw connection
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.strokeStyle = '#374151';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Draw node
      ctx.beginPath();
      ctx.arc(x, y, 20, 0, Math.PI * 2);
      ctx.fillStyle = '#1f2937';
      ctx.fill();
      ctx.strokeStyle = '#4b5563';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw sub-nodes
    const subConcepts = 16;
    for (let i = 0; i < subConcepts; i++) {
      const angle = (i / subConcepts) * Math.PI * 2;
      const subRadius = radius * 1.5;
      const x = centerX + Math.cos(angle) * subRadius;
      const y = centerY + Math.sin(angle) * subRadius;

      // Find nearest main node
      const mainAngle =
        Math.floor(i / (subConcepts / concepts)) * ((Math.PI * 2) / concepts);
      const mainX = centerX + Math.cos(mainAngle) * radius;
      const mainY = centerY + Math.sin(mainAngle) * radius;

      // Draw connection to main node
      ctx.beginPath();
      ctx.moveTo(mainX, mainY);
      ctx.lineTo(x, y);
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Draw small node
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fillStyle = '#111827';
      ctx.fill();
      ctx.strokeStyle = '#374151';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Add animation for active agents
    const processingAgents = agents.filter(a => a.status === 'Processing');
    if (processingAgents.length > 0) {
      // Add pulse effect to central node
      const time = Date.now() / 1000;
      const pulseRadius = 30 + Math.sin(time * 3) * 5;
      ctx.beginPath();
      ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.5;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }, [agents]);

  const completedAgents = agents.filter(a => a.status === 'Done').length;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5 text-orange-500" />
        <h3 className="text-white">Knowledge Graph</h3>
        <span className="ml-auto text-sm text-gray-400">
          {completedAgents > 0
            ? `${completedAgents * 52} nodes`
            : 'Waiting for analysis'}
        </span>
      </div>

      <div
        className="relative bg-gray-950 rounded-lg overflow-hidden"
        style={{ height: '400px' }}
      >
        <canvas ref={canvasRef} className="w-full h-full" />
        {completedAgents === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <Network className="w-16 h-16 mx-auto mb-3 opacity-30" />
              <p>Graph will appear after agents complete analysis</p>
            </div>
          </div>
        )}
      </div>

      {completedAgents > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Concepts</p>
            <p className="text-white">{completedAgents * 52}</p>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Relations</p>
            <p className="text-white">{completedAgents * 87}</p>
          </div>
          <div className="bg-gray-800 rounded p-3">
            <p className="text-xs text-gray-400 mb-1">Clusters</p>
            <p className="text-white">{completedAgents * 3}</p>
          </div>
        </div>
      )}
    </div>
  );
};
