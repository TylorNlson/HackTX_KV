export type TireCompound = "SOFT" | "MEDIUM" | "HARD";

export interface TrackConditions {
  tempC: number;
  scProbabilityPer10Min: number;
  degradationFactor: number;
}

export interface CarParams {
  baseLapTimeMs: number;
  pitStopLossMs: number;
  fuelPerLapKg: number;
  fuelWeightPenaltyMsPerKg: number;
}

export interface RaceConfig {
  laps: number;
  lapLengthKm: number;
  stintOptions: TireCompound[];
}

export interface StrategyInput {
  race: RaceConfig;
  track: TrackConditions;
  car: CarParams;
}

export interface StintPlan {
  compound: TireCompound;
  laps: number;
}

export interface StrategyPlan {
  stints: StintPlan[];
}

export interface LiveSimUpdate {
  type: "snapshot" | "tick" | "summary";
  timestamp: number;
  bestPlan?: StrategyPlan;
  topPlans?: Array<{ plan: StrategyPlan; meanTimeMs: number; p95TimeMs: number }>;
  tick?: {
    planIndex: number;
    sampleIndex: number;
    currentLap: number;
    etaMs: number;
  };
}
