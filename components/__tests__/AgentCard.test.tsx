import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { AgentCard } from '../AgentCard';
import { AgentName, AgentStatusValue } from '../../types';

describe('AgentCard', () => {
  it('renders agent name and details correctly', () => {
    const agent = {
      id: 'test-orchestrator-001',
      name: AgentName.ORCHESTRATOR,
      status: AgentStatusValue.IDLE,
      details: 'Idle and ready',
    };

    render(<AgentCard agent={agent} />);
    expect(screen.getByText('Orchestrator')).toBeDefined();
    expect(screen.getByText('Idle and ready')).toBeDefined();
  });
});
