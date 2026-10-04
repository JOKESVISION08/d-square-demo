import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SOSDispatchPanel from '../components/SOSDispatchPanel';

describe('SOSDispatchPanel Component', () => {
  it('renders standby message when no active incident exists', () => {
    render(<SOSDispatchPanel activeIncident={null} />);
    expect(screen.getByText(/Parallel GPT Dispatch Channels on Standby/i)).toBeInTheDocument();
  });

  it('renders standby message when incident status is not SOS_ACTIVE', () => {
    const mockIncident = {
      incident_id: 'INC_001',
      status: 'RESOLVED'
    };
    render(<SOSDispatchPanel activeIncident={mockIncident} />);
    expect(screen.getByText(/Parallel GPT Dispatch Channels on Standby/i)).toBeInTheDocument();
  });

  it('renders active parallel GPT dispatch cards when SOS is active', () => {
    const mockActiveIncident = {
      incident_id: 'INC_777',
      status: 'SOS_ACTIVE',
      disaster_type: 'fire',
      severity: 'CRITICAL',
      location_name: 'Dehradun Forest Edge',
      dispatch: {
        dsquare_gpt: 'DISPATCHED',
        rescue_gpt: 'DISPATCHED'
      }
    };

    render(<SOSDispatchPanel activeIncident={mockActiveIncident} />);

    expect(screen.getByText(/Parallel Multi-Agent GPT Dispatch Channels/i)).toBeInTheDocument();
    expect(screen.getAllByText(/INC_777/i).length).toBeGreaterThan(0);
  });
});
