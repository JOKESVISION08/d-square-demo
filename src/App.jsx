import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/AppShell';
import DashboardPage from './pages/DashboardPage';
import MLFusionPage from './pages/MLFusionPage';
import DSquareGptPage from './pages/DSquareGptPage';
import RescueGptPage from './pages/RescueGptPage';
import DSquareAlertCenterPage from './pages/DSquareAlertCenterPage';
import DiagnosticsPage from './pages/DiagnosticsPage';
import MobileNisarPage from './pages/MobileNisarPage';
import LoginPage from './pages/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';
import TriggerSosConfirmationModal from './components/TriggerSosConfirmationModal';
import {
  subscribeToTelemetry,
  subscribeToHardwareAlert,
  subscribeToIncidents,
  createVerifiedIncident
} from './firebase/realtime';
import { subscribeToSatelliteData } from './services/satelliteAdapter';
import { subscribeToAuth } from './firebase/auth';

export default function App() {
  const [user, setUser] = useState(null);
  const [currentNode, setCurrentNode] = useState("D-SQUARE_NODE_01");
  const [telemetry, setTelemetry] = useState(null);
  const [activeAlert, setActiveAlert] = useState(null);
  const [satelliteData, setSatelliteData] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("connecting");
  const [isSosModalOpen, setIsSosModalOpen] = useState(false);

  // Subscribe to Auth
  useEffect(() => {
    const unsubscribeAuth = subscribeToAuth((usr) => {
      setUser(usr);
    });
    return () => unsubscribeAuth();
  }, []);

  // Subscribe to Real Production Firebase Data (Telemetry, Hardware Alert, Satellite, Incidents)
  useEffect(() => {
    setConnectionStatus("connecting");

    const unsubTelemetry = subscribeToTelemetry(currentNode, (data) => {
      setTelemetry(data);
      setConnectionStatus(data ? "online" : "cached");
    });

    const unsubAlert = subscribeToHardwareAlert(currentNode, (alertData) => {
      setActiveAlert(alertData);
    });

    const unsubSatellite = subscribeToSatelliteData((satData) => {
      setSatelliteData(satData);
    });

    const unsubIncidents = subscribeToIncidents((incList) => {
      setIncidents(incList);
    });

    return () => {
      unsubTelemetry();
      unsubAlert();
      unsubSatellite();
      unsubIncidents();
    };
  }, [currentNode]);

  const handleConfirmSos = async (incidentPayload) => {
    await createVerifiedIncident(incidentPayload);
  };

  const hasActiveAlert = activeAlert && activeAlert.event_status === "ACTIVE";

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<LoginPage setUser={setUser} />}
        />

        <Route
          path="/*"
          element={
            <AppShell
              connectionStatus={connectionStatus}
              currentNode={currentNode}
              onSelectNode={setCurrentNode}
              onOpenSosModal={() => setIsSosModalOpen(true)}
              hasActiveAlert={hasActiveAlert}
              user={user}
            >
              <Routes>
                <Route
                  path="/"
                  element={
                    <DashboardPage
                      telemetry={telemetry}
                      activeAlert={activeAlert}
                      incidents={incidents}
                      alertHistory={activeAlert ? [activeAlert] : []}
                      currentNode={currentNode}
                      onOpenSosModal={() => setIsSosModalOpen(true)}
                      satelliteData={satelliteData}
                    />
                  }
                />

                <Route
                  path="/ml-fusion"
                  element={<MLFusionPage />}
                />

                <Route
                  path="/alert-center"
                  element={
                    <DSquareAlertCenterPage
                      telemetry={telemetry}
                      activeAlert={activeAlert}
                      incidents={incidents}
                      onOpenSosModal={() => setIsSosModalOpen(true)}
                    />
                  }
                />

                <Route
                  path="/dsquare-gpt"
                  element={<DSquareGptPage incidents={incidents} telemetry={telemetry} />}
                />

                <Route
                  path="/rescue-gpt"
                  element={<RescueGptPage incidents={incidents} telemetry={telemetry} activeAlert={activeAlert} />}
                />

                <Route
                  path="/diagnostics"
                  element={<DiagnosticsPage currentNode={currentNode} />}
                />

                <Route
                  path="/mobile-nisar"
                  element={<MobileNisarPage />}
                />
              </Routes>

              {/* Authorized Operator Trigger SOS Verification Modal */}
              <TriggerSosConfirmationModal
                isOpen={isSosModalOpen}
                onClose={() => setIsSosModalOpen(false)}
                activeAlert={activeAlert}
                telemetry={telemetry}
                onConfirmSos={handleConfirmSos}
                user={user}
              />
            </AppShell>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
