import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './styles/globals.css';

import { WorkspaceShell } from './App';
import { Landing } from './screens/Landing';
import { IntakeScreen } from './screens/IntakeScreen';
import { LotsScreen } from './screens/LotsScreen';
import { LotContextScreen } from './screens/LotContextScreen';
import { ComplianceScreen } from './screens/ComplianceScreen';
import { SchematicScreen } from './screens/SchematicScreen';
import { PacketScreen } from './screens/PacketScreen';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/workspace" element={<WorkspaceShell />}>
          <Route index element={<Navigate to="intake" replace />} />
          <Route path="intake"      element={<IntakeScreen />} />
          <Route path="lots"        element={<LotsScreen />} />
          <Route path="lot-context" element={<LotContextScreen />} />
          <Route path="compliance"  element={<ComplianceScreen />} />
          <Route path="schematic"   element={<SchematicScreen />} />
          <Route path="packet"      element={<PacketScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
