
import React from 'react';
import { AgentState, AgentStatusValue } from '../types';
import { LoaderIcon, CheckCircleIcon, XCircleIcon } from './icons';

interface AgentCardProps {
  agent: AgentState;
}

const statusConfig = {
  [AgentStatusValue.IDLE]: { icon: null, color: 'text-slate-500', bgColor: 'bg-slate-800' },
  [AgentStatusValue.PROCESSING]: { icon: <LoaderIcon className="w-5 h-5 text-sky-400" />, color: 'text-sky-400', bgColor: 'bg-sky-900/50' },
  [AgentStatusValue.DONE]: { icon: <CheckCircleIcon className="w-5 h-5 text-emerald-400" />, color: 'text-emerald-400', bgColor: 'bg-emerald-900/50' },
  [AgentStatusValue.ERROR]: { icon: <XCircleIcon className="w-5 h-5 text-rose-400" />, color: 'text-rose-400', bgColor: 'bg-rose-900/50' },
};


export const AgentCard: React.FC<AgentCardProps> = ({ agent }) => {
  const config = statusConfig[agent.status];

  return (
    <div className={`flex items-center p-3 rounded-lg transition-all duration-300 ${config.bgColor}`}>
      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
        {config.icon}
      </div>
      <div className="ml-3">
        <p className="font-semibold text-slate-200">{agent.name}</p>
        <p className={`text-sm ${config.color}`}>{agent.details}</p>
      </div>
    </div>
  );
};
