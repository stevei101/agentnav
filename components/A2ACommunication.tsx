import React, { useEffect, useRef } from 'react';
import { MessageSquare, ArrowRight, Radio } from 'lucide-react';

interface A2AMessage {
  id: string;
  from: string;
  to: string;
  type: 'request' | 'response' | 'broadcast';
  content: string;
  timestamp: Date;
}

interface A2ACommunicationProps {
  messages: A2AMessage[];
}

const messageTypeColors = {
  request: 'border-blue-500/50 bg-blue-900/20',
  response: 'border-green-500/50 bg-green-900/20',
  broadcast: 'border-purple-500/50 bg-purple-900/20',
};

const messageTypeIcons = {
  request: ArrowRight,
  response: ArrowRight,
  broadcast: Radio,
};

export const A2ACommunication: React.FC<A2ACommunicationProps> = ({
  messages,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare className="w-5 h-5 text-blue-500" />
        <h3 className="text-white">A2A Protocol Communication</h3>
        <span className="ml-auto text-sm text-gray-400">
          {messages.length} messages
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No agent communications yet</p>
            <p className="text-sm mt-1">
              Start an analysis to see A2A protocol in action
            </p>
          </div>
        ) : (
          messages.map(message => {
            const Icon =
              messageTypeIcons[message.type as keyof typeof messageTypeIcons];
            return (
              <div
                key={message.id}
                className={`border rounded-lg p-4 ${
                  messageTypeColors[
                    message.type as keyof typeof messageTypeColors
                  ]
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">
                      <span className="text-white">{message.from}</span>
                      {' → '}
                      <span className="text-white">{message.to}</span>
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 uppercase px-2 py-0.5 bg-gray-800 rounded">
                    {message.type}
                  </span>
                </div>
                <p className="text-gray-300 text-sm">{message.content}</p>
                <p className="text-xs text-gray-500 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};
