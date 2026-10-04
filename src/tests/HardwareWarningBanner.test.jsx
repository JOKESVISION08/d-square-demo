import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import HardwareWarningBanner from '../components/HardwareWarningBanner';

describe('HardwareWarningBanner Component', () => {
  it('renders nothing when there is no active alert', () => {
    const { container } = render(
      <MemoryRouter>
        <HardwareWarningBanner alert={null} onOpenSosModal={() => {}} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders warning banner silently when active alert exists', () => {
    const mockAlert = {
      alert_id: 'ALERT_123',
      node_id: 'D-SQUARE_NODE_01',
      disaster_type: 'fire',
      confidence: 0.945,
      timestamp: new Date().toISOString(),
      event_status: 'ACTIVE'
    };

    render(
      <MemoryRouter>
        <HardwareWarningBanner alert={mockAlert} onOpenSosModal={() => {}} />
      </MemoryRouter>
    );

    // Must show visual warning and link to Alert Center
    expect(screen.getByText(/SILENT HARDWARE WARNING/i)).toBeInTheDocument();
    expect(screen.getByText(/FIRE ANOMALY INGESTED/i)).toBeInTheDocument();
    expect(screen.getByText(/D-SQUARE_NODE_01/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /OPEN ALERT CENTER & DISPATCH/i })).toBeInTheDocument();
  });
});
