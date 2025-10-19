import { CarParams, StrategyInput, StrategyPlan, TireCompound } from "./types.js";

type SampleOptions = { random: () => number };

const tireBaseDelta: Record<TireCompound, number> = {
  SOFT: 0,
  MEDIUM: 400,
  HARD: 900,
};

const tireWearPerLapMs: Record<TireCompound, number> = {
  SOFT: 80,
  MEDIUM: 60,
  HARD: 40,
};

export function randomStrategyCandidates(laps: number, compounds: TireCompound[], maxStops = 3): StrategyPlan[] {
  const plans: StrategyPlan[] = [];
  const stopsOptions = [0, 1, 2, 3].filter((s) => s <= maxStops);
  for (let i = 0; i < 40; i++) {
    const stops = stopsOptions[Math.floor(Math.random() * stopsOptions.length)];
    const stintCount = stops + 1;
    const splits = randomPositiveIntegersSummingTo(laps, stintCount);
    const stints = splits.map((n) => ({ compound: compounds[Math.floor(Math.random() * compounds.length)], laps: n }));
    plans.push({ stints });
  }
  return dedupePlans(plans).slice(0, 40);
}

function dedupePlans(plans: StrategyPlan[]): StrategyPlan[] {
  const seen = new Set<string>();
  const out: StrategyPlan[] = [];
  for (const p of plans) {
    const key = p.stints.map((s) => `${s.compound}-${s.laps}`).join("|");
    if (!seen.has(key)) {
      seen.add(key);
      out.push(p);
    }
  }
  return out;
}

function randomPositiveIntegersSummingTo(total: number, parts: number): number[] {
  const cuts = new Set<number>();
  while (cuts.size < parts - 1) {
    cuts.add(1 + Math.floor(Math.random() * (total - 1)));
  }
  const arr = [0, ...Array.from(cuts).sort((a, b) => a - b), total];
  const diffs: number[] = [];
  for (let i = 1; i < arr.length; i++) diffs.push(arr[i] - arr[i - 1]);
  return diffs;
}

export function simulatePlanOnce(input: StrategyInput, plan: StrategyPlan, opt?: SampleOptions): number {
  const rnd = opt?.random ?? Math.random;
  const car = input.car;
  const track = input.track;

  const scChancePerLap = Math.min(0.5, track.scProbabilityPer10Min * 0.1);
  let underSC = false;
  let totalMs = 0;
  let fuelKg = input.race.laps * car.fuelPerLapKg;

  for (const stint of plan.stints) {
    const compound = stint.compound;
    const baseDelta = tireBaseDelta[compound];
    const wearMsPerLap = tireWearPerLapMs[compound] * track.degradationFactor;
    for (let lap = 0; lap < stint.laps; lap++) {
      if (!underSC && rnd() < scChancePerLap) underSC = true;
      else if (underSC && rnd() < 0.15) underSC = false;

      const fuelPenalty = fuelKg * car.fuelWeightPenaltyMsPerKg;
      const wearPenalty = wearMsPerLap * lap;
      let lapMs = car.baseLapTimeMs + baseDelta + fuelPenalty + wearPenalty;
      lapMs *= 1 + (rnd() - 0.5) * 0.01; // +/-0.5%
      if (underSC) lapMs *= 1.1;
      totalMs += lapMs;
      fuelKg = Math.max(0, fuelKg - car.fuelPerLapKg);
    }
    if (stint !== plan.stints[plan.stints.length - 1]) {
      let pitLoss = car.pitStopLossMs;
      if (underSC) pitLoss *= 0.65;
      totalMs += pitLoss;
    }
  }
  return totalMs;
}

export function evaluatePlanMonteCarlo(input: StrategyInput, plan: StrategyPlan, samples = 200) {
  const results: number[] = [];
  for (let i = 0; i < samples; i++) results.push(simulatePlanOnce(input, plan));
  results.sort((a, b) => a - b);
  const mean = results.reduce((a, b) => a + b, 0) / results.length;
  const p95 = results[Math.min(results.length - 1, Math.floor(results.length * 0.95))];
  return { mean, p95 };
}

export function bestPlans(input: StrategyInput, candidates: StrategyPlan[], samples = 200) {
  const scored = candidates.map((plan) => {
    const { mean, p95 } = evaluatePlanMonteCarlo(input, plan, samples);
    return { plan, mean, p95 };
  });
  scored.sort((a, b) => a.mean - b.mean);
  return scored.slice(0, 5);
}

export function defaultCar(): CarParams {
  return {
    baseLapTimeMs: 82000,
    pitStopLossMs: 21000,
    fuelPerLapKg: 1.6,
    fuelWeightPenaltyMsPerKg: 1.6,
  };
}
