import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

// Mock leaflet before importing LiveDisasterMap
vi.mock('leaflet', () => {
  const mockMap = {
    setView: vi.fn().mockReturnThis(),
    remove: vi.fn()
  };
  const mockLayerGroup = {
    addTo: vi.fn().mockReturnThis(),
    clearLayers: vi.fn().mockReturnThis(),
    addLayer: vi.fn().mockReturnThis()
  };
  return {
    default: {
      map: vi.fn(() => mockMap),
      tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
      layerGroup: vi.fn(() => mockLayerGroup),
      divIcon: vi.fn(() => ({})),
      marker: vi.fn(() => ({ bindPopup: vi.fn(() => ({})) })),
      polygon: vi.fn(() => ({ bindPopup: vi.fn(() => ({})) }))
    }
  };
});

import LiveDisasterMap from '../components/LiveDisasterMap';

describe('LiveDisasterMap Component', () => {
  it('renders map container with GIS legend', () => {
    render(
      <LiveDisasterMap
        telemetry={null}
        activeAlert={null}
        activeIncident={null}
      />
    );

    expect(screen.getByText(/Interactive Disaster GIS Map/i)).toBeInTheDocument();
    expect(screen.getByText(/Normal/i)).toBeInTheDocument();
    expect(screen.getByText(/Warning/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirmed SOS/i)).toBeInTheDocument();
  });
});
