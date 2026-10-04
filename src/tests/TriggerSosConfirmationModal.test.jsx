import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import TriggerSosConfirmationModal from '../components/TriggerSosConfirmationModal';

describe('TriggerSosConfirmationModal Component', () => {
  it('renders null when isOpen is false', () => {
    const { container } = render(
      <TriggerSosConfirmationModal
        isOpen={false}
        onClose={() => {}}
        activeAlert={null}
        telemetry={null}
        onConfirmSos={() => {}}
        user={null}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders modal with default values when isOpen is true', () => {
    render(
      <TriggerSosConfirmationModal
        isOpen={true}
        onClose={() => {}}
        activeAlert={null}
        telemetry={null}
        onConfirmSos={() => {}}
        user={{ email: 'operator@dsquare.gov.in' }}
      />
    );

    expect(screen.getByText(/Authorized Human Operator Verification Gate/i)).toBeInTheDocument();
    expect(screen.getByText('operator@dsquare.gov.in')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /CONFIRM & TRIGGER SOS NOW/i })).toBeInTheDocument();
  });

  it('submits verified incident payload on form submission', async () => {
    const mockConfirmSos = vi.fn().mockResolvedValue({ incident_id: 'INC_001' });
    const mockOnClose = vi.fn();
    const mockAlert = {
      event_id: 'EVT_999',
      node_id: 'D-SQUARE_NODE_01',
      disaster_type: 'fire',
      confidence: 0.95,
      location_name: 'Uttarakhand Forest Sector 2'
    };

    render(
      <TriggerSosConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        activeAlert={mockAlert}
        telemetry={{ temperature: 34.5, humidity: 30 }}
        onConfirmSos={mockConfirmSos}
        user={{ email: 'commander@dsquare.gov.in' }}
      />
    );

    const submitBtn = screen.getByRole('button', { name: /CONFIRM & TRIGGER SOS NOW/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockConfirmSos).toHaveBeenCalledTimes(1);
    });

    const payload = mockConfirmSos.mock.calls[0][0];
    expect(payload.verified_by).toBe('commander@dsquare.gov.in');
    expect(payload.source_node_id).toBe('D-SQUARE_NODE_01');
    expect(payload.disaster_type).toBe('fire');
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
