import express, { Request, Response } from "express";
import cors from "cors";
import { WebSocketServer, WebSocket } from "ws";
import { z } from "zod";
import { bestPlans, defaultCar, randomStrategyCandidates } from "./simEngine.js";
import { StrategyInput, TireCompound } from "./types.js";

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT ? Number(process.env.PORT) : 4000;

const inputSchema = z.object({
  race: z.object({
    laps: z.number().int().positive(),
    lapLengthKm: z.number().positive(),
    stintOptions: z.array(z.enum(["SOFT", "MEDIUM", "HARD"] as const)),
  }),
  track: z.object({
    tempC: z.number(),
    scProbabilityPer10Min: z.number().min(0).max(1),
    degradationFactor: z.number().min(0.5).max(2),
  }),
  car: z.object({
    baseLapTimeMs: z.number().positive(),
    pitStopLossMs: z.number().positive(),
    fuelPerLapKg: z.number().positive(),
    fuelWeightPenaltyMsPerKg: z.number().positive(),
  }),
});

let latestInput: StrategyInput = {
  race: { laps: 58, lapLengthKm: 5.8, stintOptions: ["SOFT", "MEDIUM", "HARD"] as TireCompound[] },
  track: { tempC: 32, scProbabilityPer10Min: 0.18, degradationFactor: 1.0 },
  car: defaultCar(),
};

app.get("/api/config", (_req: Request, res: Response) => {
  res.json(latestInput);
});

app.post("/api/config", (req: Request, res: Response) => {
  const parsed = inputSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  latestInput = parsed.data;
  res.json({ ok: true });
});

app.get("/api/plans", (_req: Request, res: Response) => {
  const candidates = randomStrategyCandidates(latestInput.race.laps, latestInput.race.stintOptions);
  const top = bestPlans(latestInput, candidates, 200);
  res.json(top);
});

const server = app.listen(PORT, () => {
  console.log(`Backend listening on http://localhost:${PORT}`);
});

const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws: WebSocket) => {
  ws.send(JSON.stringify({ type: "snapshot", timestamp: Date.now(), message: "connected" }));
  const timer = setInterval(() => {
    const candidates = randomStrategyCandidates(latestInput.race.laps, latestInput.race.stintOptions);
    const top = bestPlans(latestInput, candidates, 150);
    ws.send(
      JSON.stringify({
        type: "summary",
        timestamp: Date.now(),
        bestPlan: top[0]?.plan,
        topPlans: top.map((t) => ({ plan: t.plan, meanTimeMs: t.mean, p95TimeMs: t.p95 })),
      })
    );
  }, 2000);
  ws.on("close", () => clearInterval(timer));
});
