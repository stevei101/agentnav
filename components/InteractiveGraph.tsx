import React, { useState, useEffect, useMemo, useRef } from 'react';
import { GraphNode, GraphEdge } from '../types';
import { SearchPlusIcon, SearchMinusIcon } from './icons';

interface InteractiveGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const COLOR_PALETTE: { [key: string]: string } = {
  default: '#38bdf8', // sky-400
  concept: '#818cf8', // indigo-400
  function: '#34d399', // emerald-400
  class: '#f472b6', // pink-400
  module: '#fb923c', // orange-400
};

const getGroupColor = (group?: string) => {
  if (group && COLOR_PALETTE[group.toLowerCase()]) {
    return COLOR_PALETTE[group.toLowerCase()];
  }
  return COLOR_PALETTE.default;
};

export const InteractiveGraph: React.FC<InteractiveGraphProps> = ({
  nodes,
  edges,
}) => {
  const [viewBox, setViewBox] = useState({
    x: -500,
    y: -500,
    width: 1000,
    height: 1000,
  });
  const [isDragging, setIsDragging] = useState(false);
  const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const svgRef = useRef<SVGSVGElement>(null);

  const nodePositions = useMemo(() => {
    const positions = new Map<string, { x: number; y: number }>();
    const count = nodes.length;
    if (count === 0) return positions;

    const radius = Math.min(400, 25 * count);
    nodes.forEach((node, i) => {
      const angle = (i / count) * 2 * Math.PI;
      positions.set(node.id, {
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
      });
    });
    return positions;
  }, [nodes]);

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (e.target !== svgRef.current) return;
    setIsDragging(true);
    setStartPoint({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDragging) return;
    const dx = e.clientX - startPoint.x;
    const dy = e.clientY - startPoint.y;
    const scale = viewBox.width / (svgRef.current?.clientWidth || 1);
    setViewBox(prev => ({
      ...prev,
      x: prev.x - dx * scale,
      y: prev.y - dy * scale,
    }));
    setStartPoint({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 1.1 : 0.9;
    const svg = svgRef.current;
    if (!svg) return;

    const rect = svg.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const newWidth = viewBox.width * scaleFactor;
    const newHeight = viewBox.height * scaleFactor;

    const dx = (mouseX / svg.clientWidth) * (viewBox.width - newWidth);
    const dy = (mouseY / svg.clientHeight) * (viewBox.height - newHeight);

    setViewBox(prev => ({
      width: newWidth,
      height: newHeight,
      x: prev.x + dx,
      y: prev.y + dy,
    }));
  };

  const zoom = (factor: number) => {
    const newWidth = viewBox.width * factor;
    const newHeight = viewBox.height * factor;
    setViewBox(prev => ({
      width: newWidth,
      height: newHeight,
      x: prev.x + (prev.width - newWidth) / 2,
      y: prev.y + (prev.height - newHeight) / 2,
    }));
  };

  const connectedEdges = useMemo(() => {
    if (!hoveredNode) return new Set();
    const connections = new Set<string>();
    edges.forEach(edge => {
      if (edge.from === hoveredNode) connections.add(edge.to);
      if (edge.to === hoveredNode) connections.add(edge.from);
    });
    return connections;
  }, [hoveredNode, edges]);

  return (
    <div
      className="relative w-full h-full cursor-grab active:cursor-grabbing"
      onMouseUp={handleMouseUp}
    >
      <svg
        ref={svgRef}
        className="w-full h-full rounded-md bg-slate-900/50"
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onWheel={handleWheel}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
          </marker>
        </defs>

        {/* Edges */}
        <g>
          {edges.map((edge, i) => {
            const fromPos = nodePositions.get(edge.from);
            const toPos = nodePositions.get(edge.to);
            if (!fromPos || !toPos) return null;

            const isHighlighted =
              hoveredNode === edge.from || hoveredNode === edge.to;

            return (
              <g key={`edge-${i}`}>
                <line
                  x1={fromPos.x}
                  y1={fromPos.y}
                  x2={toPos.x}
                  y2={toPos.y}
                  stroke={isHighlighted ? '#f8fafc' : '#475569'}
                  strokeWidth={isHighlighted ? 2 : 1}
                  markerEnd="url(#arrowhead)"
                  className="transition-all"
                />
                {edge.label && (
                  <text
                    x={(fromPos.x + toPos.x) / 2}
                    y={(fromPos.y + toPos.y) / 2}
                    fill={isHighlighted ? '#cbd5e1' : '#64748b'}
                    fontSize="10"
                    textAnchor="middle"
                    className="pointer-events-none transition-all"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* Nodes */}
        <g>
          {nodes.map(node => {
            const pos = nodePositions.get(node.id);
            if (!pos) return null;
            const isHovered = hoveredNode === node.id;
            const isConnected = connectedEdges.has(node.id);
            const isDimmed = hoveredNode !== null && !isHovered && !isConnected;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                opacity={isDimmed ? 0.3 : 1}
              >
                <circle
                  r={isHovered ? 12 : 10}
                  fill={getGroupColor(node.group)}
                  stroke="#f8fafc"
                  strokeWidth={isHovered ? 2 : 0}
                />
                <text
                  y="-18"
                  textAnchor="middle"
                  fill="#e2e8f0"
                  fontSize={isHovered ? 14 : 12}
                  className="font-semibold pointer-events-none"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
        <button
          onClick={() => zoom(0.8)}
          className="bg-slate-700/80 p-2 rounded-md hover:bg-slate-600 text-slate-300 transition"
          aria-label="Zoom in"
        >
          <SearchPlusIcon className="w-5 h-5" />
        </button>
        <button
          onClick={() => zoom(1.25)}
          className="bg-slate-700/80 p-2 rounded-md hover:bg-slate-600 text-slate-300 transition"
          aria-label="Zoom out"
        >
          <SearchMinusIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
