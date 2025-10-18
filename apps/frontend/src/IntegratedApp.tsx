import React from "react";
import App from "./App";
import SettingsLegacy from "./legacy/SettingsLegacy";
import SummaryLegacy from "./legacy/SummaryLegacy";
import GalaxyLegacy from "./legacy/GalaxyLegacy";
import "./legacy/summary.css";
import "./legacy/settings.css";
import "./legacy/galaxy.css";

/**
 * IntegratedApp renders the modern Vite/TS frontend (App)
 * alongside the legacy frontend components in a side-by-side layout.
 *
 * The legacy folder contains the old components re-used as-is so
 * we can incrementally port functionality into App.
 */
export default function IntegratedApp() {
  return (
    <div style={{ display: "flex", gap: 20, padding: 16, alignItems: "flex-start" }}>
      <main style={{ flex: 1, minWidth: 700 }}>
        <App />
      </main>

      <aside style={{ width: 360, display: "flex", flexDirection: "column", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Legacy Frontend (from frontend/)</h2>
        <SettingsLegacy />
        <SummaryLegacy />
        <GalaxyLegacy />
      </aside>
    </div>
  );
}