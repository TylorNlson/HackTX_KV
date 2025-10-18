import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type Tire = "SOFT" | "MEDIUM" | "HARD";
type Stint = { compound: Tire; laps: number };
type Plan = { stints: Stint[] };

type Summary = {
  type: "summary";
  timestamp: number;
  bestPlan?: Plan;
  topPlans?: Array<{ plan: Plan; meanTimeMs: number; p95TimeMs: number }>;
};

export default function App() {
  const [socketState, setSocketState] = useState<string>("connecting");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [laps, setLaps] = useState(58);
  const [scProb, setScProb] = useState(0.18);
  const [deg, setDeg] = useState(1.0);

  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/ws`;
    const ws = new WebSocket(url);
    ws.onopen = () => setSocketState("connected");
    ws.onclose = () => setSocketState("disconnected");
    ws.onerror = () => setSocketState("error");
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "summary") setSummary(data);
      } catch {}
    };
    return () => ws.close();
  }, []);

  const chartData = useMemo(() => {
    if (!summary?.topPlans) return [];
    return summary.topPlans.map((t, i) => ({ name: `Plan ${i + 1}`, mean: t.meanTimeMs / 1000, p95: t.p95TimeMs / 1000 }));
  }, [summary]);

  const best = summary?.topPlans?.[0];

  async function applyConfig() {
    const payload = {
      race: { laps, lapLengthKm: 5.8, stintOptions: ["SOFT", "MEDIUM", "HARD"] },
      track: { tempC: 32, scProbabilityPer10Min: scProb, degradationFactor: deg },
      car: { baseLapTimeMs: 82000, pitStopLossMs: 21000, fuelPerLapKg: 1.6, fuelWeightPenaltyMsPerKg: 1.6 },
    };
    await fetch("/api/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  }

  return (
    <div style={{ fontFamily: "Inter, system-ui, Arial", padding: 16, maxWidth: 1200, margin: "0 auto" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <h1 style={{ margin: 0 }}>F1 Strategy Copilot</h1>
        <div>
          <span
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              background: socketState === "connected" ? "#16a34a" : socketState === "connecting" ? "#fbbf24" : "#ef4444",
              color: "white",
              fontSize: 12,
            }}
          >
            {socketState}
          </span>
        </div>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: "#0b1220", color: "#e5e7eb", borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>Top Strategies (lower is faster)</h2>
          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" label={{ value: "Total Time (s)", angle: -90, position: "insideLeft", fill: "#9ca3af" }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="mean" stroke="#60a5fa" strokeWidth={2} />
                <Line type="monotone" dataKey="p95" stroke="#f97316" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {best && (
            <div style={{ marginTop: 12 }}>
              <h3 style={{ margin: "8px 0" }}>Recommended Plan</h3>
              <p style={{ margin: 0 }}>Mean: {(best.meanTimeMs / 1000).toFixed(2)}s · P95: {(best.p95TimeMs / 1000).toFixed(2)}s</p>
              <ol>
                {best.plan.stints.map((s, idx) => (
                  <li key={idx}>
                    {s.laps} laps on {s.compound}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>

        <div style={{ background: "#0b1220", color: "#e5e7eb", borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>Controls</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label>
              Laps
              <input type="number" value={laps} onChange={(e) => setLaps(parseInt(e.target.value || "0"))} min={10} max={80} style={inputStyle} />
            </label>
            <label>
              SC prob/10min
              <input type="number" step="0.01" value={scProb} onChange={(e) => setScProb(parseFloat(e.target.value || "0"))} min={0} max={1} style={inputStyle} />
            </label>
            <label>
              Degradation x
              <input type="number" step="0.1" value={deg} onChange={(e) => setDeg(parseFloat(e.target.value || "0"))} min={0.5} max={2} style={inputStyle} />
            </label>
          </div>
          <button onClick={applyConfig} style={buttonStyle}>Apply</button>
          <p style={{ fontSize: 12, color: "#9ca3af" }}>The chart updates automatically every 2 seconds.</p>
        </div>
      </section>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: 8,
  borderRadius: 8,
  border: "1px solid #374151",
  background: "#111827",
  color: "#e5e7eb",
  marginTop: 4,
};

const buttonStyle: React.CSSProperties = {
  marginTop: 12,
  padding: "10px 14px",
  background: "#2563eb",
  color: "white",
  border: 0,
  borderRadius: 8,
  cursor: "pointer",
};
