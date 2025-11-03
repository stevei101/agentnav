import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentStreamEvent, AgentEventType, AgentName } from '../types';

interface UseAgentStreamOptions {
  sessionId: string | null;
  onEvent?: (event: AgentStreamEvent) => void;
  onError?: (error: Error) => void;
  autoConnect?: boolean;
}

interface UseAgentStreamReturn {
  events: AgentStreamEvent[];
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  send: (message: Record<string, unknown>) => void;
}

export const useAgentStream = ({
  sessionId,
  onEvent,
  onError,
  autoConnect = true,
}: UseAgentStreamOptions): UseAgentStreamReturn => {
  const [events, setEvents] = useState<AgentStreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const connect = useCallback(() => {
    if (!sessionId) {
      const err = new Error('Session ID is required to connect');
      setError(err);
      onError?.(err);
      return;
    }

    if (
      isConnected ||
      isConnecting ||
      wsRef.current?.readyState === WebSocket.OPEN
    ) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/navigate/stream?session_id=${sessionId}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.info('✅ WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = event => {
        try {
          const data = JSON.parse(event.data);

          // Validate event structure
          if (data.id && data.agent && data.status && data.timestamp) {
            const streamEvent: AgentStreamEvent = {
              id: data.id,
              agent: data.agent as AgentName,
              status: data.status as AgentEventType,
              timestamp: data.timestamp,
              metadata: data.metadata,
              payload: data.payload,
            };

            setEvents(prev => [...prev, streamEvent]);
            onEvent?.(streamEvent);
          } else {
            console.warn('Invalid event structure:', data);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = event => {
        const err = new Error(`WebSocket error: ${event.type}`);
        console.error('❌ WebSocket error:', err);
        setError(err);
        onError?.(err);
      };

      ws.onclose = () => {
        console.info('❌ WebSocket disconnected');
        setIsConnected(false);
        setIsConnecting(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.info(
            `Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else {
          const err = new Error('Max reconnection attempts reached');
          setError(err);
          onError?.(err);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('Failed to create WebSocket:', error);
      setError(error);
      setIsConnecting(false);
      onError?.(error);
    }
  }, [sessionId, isConnected, isConnecting, onEvent, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Auto-connect on mount or when sessionId changes
  useEffect(() => {
    if (autoConnect && sessionId && !isConnected && !isConnecting) {
      connect();
    }

    return () => {
      // Optional: uncomment to disconnect on unmount
      // disconnect();
    };
  }, [sessionId, autoConnect, isConnected, isConnecting, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    events,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    send,
  };
};
