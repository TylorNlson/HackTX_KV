"""
Racing Strategy Monte Carlo Simulator - F1 Edition (FIXED)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

class TireCompound(Enum):
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"  # F1 has inters
    WET = "wet"

class Weather(Enum):
    DRY = "dry"
    MIXED = "mixed"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"

class EngineMode(Enum):
    ECO = 0.98        # Fuel/engine saving
    NORMAL = 1.0      # Standard race pace
    PUSH = 1.02       # Attacking mode
    OVERTAKE = 1.04   # DRS/overtake button (limited use)

@dataclass
class TrackConfig:
    """F1 Track configuration"""
    name: str
    lap_length_km: float
    base_lap_time: float  # seconds - for midfield car
    num_corners: int

    # F1-specific
    drs_zones: int = 2
    pit_loss_time: float = 22.0  # Total time loss (enter + service + exit)
    pit_lane_delta: float = 18.0  # Just pit lane transit
    pit_service_time: float = 2.0  # Stationary time (F1 is ~2s)

    # Track characteristics
    tire_stress: float = 1.0      # How hard on tires (Monaco=1.2, Spa=0.8)
    fuel_usage: float = 1.0       # How fuel-heavy (Monza=1.1, Monaco=0.85)
    overtaking_difficulty: float = 0.5  # 0=easy (Monza), 1=impossible (Monaco)

@dataclass
class CarSetup:
    """F1 Car setup"""
    downforce: float = 0.5  # 0=low (Monza) to 1=high (Monaco)
    engine_mode: EngineMode = EngineMode.NORMAL
    fuel_start: float = 110.0  # kg (F1 max is 110kg)
    tire_compound: TireCompound = TireCompound.MEDIUM
    initial_tire_wear: float = 0.0

    # Performance characteristics (relative to field)
    car_performance: float = 0.0  # seconds per lap advantage (-1.5 to +1.5)
                                   # -1.0 = top team, +1.0 = backmarker

@dataclass
class RaceConditions:
    """F1 Race conditions"""
    race_laps: int
    track: TrackConfig
    track_temp: float = 25.0
    weather: Weather = Weather.DRY

    # F1 safety car probabilities (empirical data)
    safety_car_prob: float = 0.015  # ~1.5% per lap (realistic F1 average)
    vsc_prob: float = 0.008         # Virtual safety car
    red_flag_prob: float = 0.0002   # Very rare

    # Competition
    num_competitors: int = 19  # F1 has 20 cars total
    field_spread: float = 2.5  # Seconds between P1 and P10 pace (realistic F1)

    # Rules
    min_compounds_required: int = 2  # F1 rule: must use 2 different compounds (dry race)
    max_fuel_kg: float = 110.0
    refueling_allowed: bool = False  # F1 doesn't allow refueling

@dataclass
class SimulationConfig:
    """Monte Carlo configuration - F1 calibrated"""
    num_runs: int = 10000
    random_seed: Optional[int] = 42

    # F1-calibrated physics constants
    k_wear_lap_time: float = 12.0      # F1: heavily worn tires = ~12s slower
    k_fuel_lap_time: float = 0.03     # F1: ~0.035s per kg of fuel
    k_downforce_lap_time: float = 1.2  # Setup impact

    # Tire compound properties: (speed_offset_seconds, base_wear_per_lap, operating_window)
    # F1 2024 approximate values
    tire_properties: Dict[TireCompound, Tuple[float, float, float]] = field(default_factory=lambda: {
        TireCompound.SOFT:   (-0.8, 0.030, 25.0),  # Fast, high wear, narrow window
        TireCompound.MEDIUM: ( 0.0, 0.015, 20.0),  # Baseline
        TireCompound.HARD:   ( 0.6, 0.008, 15.0),  # Slow, durable, wide window
        TireCompound.INTERMEDIATE: (2.0, 0.020, 10.0),  # Wet weather
        TireCompound.WET:   (5.0, 0.015, 8.0),   # Heavy rain
    })

    # Stochastic parameters
    lap_time_noise_std: float = 0.15   # F1 drivers are consistent
    wear_rate_noise_std: float = 0.20
    fuel_burn_noise_std: float = 0.05

    # Base rates
    base_fuel_burn_rate: float = 1.4   # kg per lap (F1: ~1.3-1.5 kg/lap)
    base_puncture_prob: float = 0.0003 # Very rare in modern F1
    puncture_wear_multiplier: float = 5.0

    # Weather effects
    rain_slowdown_factor: float = 0.10  # 10% slower in rain
    rain_wear_reduction: float = 0.7    # Less tire wear in rain

    # Safety car
    safety_car_duration_laps: int = 3
    safety_car_lap_time_factor: float = 1.45
    vsc_duration_laps: int = 2
    vsc_lap_time_factor: float = 1.30  # VSC is faster than full SC

@dataclass
class Strategy:
    """Pit strategy"""
    name: str
    pit_laps: List[int]
    tire_compounds: List[TireCompound]
    engine_modes: Optional[List[EngineMode]] = None

    def __post_init__(self):
        if len(self.tire_compounds) != len(self.pit_laps) + 1:
            raise ValueError(f"Need {len(self.pit_laps)+1} compounds for {len(self.pit_laps)} stops")
        if self.engine_modes is None:
            self.engine_modes = [EngineMode.NORMAL] * (len(self.pit_laps) + 1)

# ============================================================================
# COMPETITOR FIELD MODEL (NEW - PROPER IMPLEMENTATION)
# ============================================================================

class CompetitorField:
    """Models the F1 field with realistic pace distribution and strategy diversity."""

    def __init__(self, race_conditions: RaceConditions, sim_config: SimulationConfig, rng: np.random.RandomState):
        self.rc = race_conditions
        self.cfg = sim_config
        self.rng = rng

        self.competitor_base_pace = self._generate_realistic_field()
        self.competitor_strategies = self._assign_competitor_strategies()

    def _generate_realistic_field(self) -> np.ndarray:
        """Generate F1-realistic pace distribution"""
        n = self.rc.num_competitors

        # F1 field structure
        top_teams = 6
        midfield = min(8, n - top_teams)
        backmarkers = n - top_teams - midfield

        pace = np.zeros(n)

        # Top teams: -0.8 to -0.2 seconds
        pace[:top_teams] = self.rng.uniform(-0.8, -0.2, top_teams)

        # Midfield: -0.2 to +0.8 seconds
        pace[top_teams:top_teams + midfield] = self.rng.uniform(-0.2, 0.8, midfield)

        # Backmarkers: +0.8 to +2.0 seconds
        if backmarkers > 0:
            pace[top_teams + midfield:] = self.rng.uniform(0.8, 2.0, backmarkers)

        pace += self.rng.normal(0, 0.1, n)

        return pace

    def _assign_competitor_strategies(self) -> List[Strategy]:
        """Assign diverse strategies to competitors"""
        strategies = []
        n = self.rc.num_competitors

        # Define strategy templates
        one_stop_options = [
            ([TireCompound.MEDIUM, TireCompound.HARD], "MH"),
            ([TireCompound.SOFT, TireCompound.HARD], "SH"),
            ([TireCompound.HARD, TireCompound.MEDIUM], "HM"),
            ([TireCompound.SOFT, TireCompound.MEDIUM], "SM"),
        ]

        two_stop_options = [
            ([TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.MEDIUM], "SMM"),
            ([TireCompound.MEDIUM, TireCompound.MEDIUM, TireCompound.SOFT], "MMS"),
            ([TireCompound.SOFT, TireCompound.SOFT, TireCompound.MEDIUM], "SSM"),
            ([TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD], "SMH"),
            ([TireCompound.MEDIUM, TireCompound.SOFT, TireCompound.MEDIUM], "MSM"),
        ]

        for i in range(n):
            if self.rng.random() < 0.65:  # 65% try 1-stop (more realistic for modern F1)
                # Random pit window for 1-stop
                pit_lap = self.rng.randint(
                    max(self.rc.race_laps // 3, 15),
                    min(2 * self.rc.race_laps // 3, self.rc.race_laps - 10)
                )

                compounds, code = one_stop_options[self.rng.randint(0, len(one_stop_options))]

                strategies.append(Strategy(
                    name=f"Comp{i}_1stop_{code}_L{pit_lap}",
                    pit_laps=[pit_lap],
                    tire_compounds=compounds
                ))
            else:  # 35% do 2-stop
                # Random pit windows for 2-stop
                pit1 = self.rng.randint(
                    max(self.rc.race_laps // 5, 10),
                    max(self.rc.race_laps // 3, 20)
                )
                pit2 = self.rng.randint(
                    pit1 + 12,
                    min(3 * self.rc.race_laps // 4, self.rc.race_laps - 8)
                )

                compounds, code = two_stop_options[self.rng.randint(0, len(two_stop_options))]

                strategies.append(Strategy(
                    name=f"Comp{i}_2stop_{code}_L{pit1}L{pit2}",
                    pit_laps=[pit1, pit2],
                    tire_compounds=compounds
                ))

        return strategies

    def simulate_competitors(self, num_runs: int) -> np.ndarray:
        """
        Simulate competitors using a COPY of our car's simulation logic.
        This ensures perfect apples-to-apples comparison.
        """
        from copy import deepcopy

        competitor_times = np.zeros((num_runs, self.rc.num_competitors))

        print("Simulating competitor field (this may take a moment)...")

        for comp_idx in range(self.rc.num_competitors):
            if comp_idx % 5 == 0:
                print(f"  Competitor {comp_idx + 1}/{self.rc.num_competitors}...", end='\r')

            # Create a "virtual car setup" for this competitor
            comp_setup = CarSetup(
                downforce=self.rng.uniform(0.7, 0.9),  # Random setup
                car_performance=self.competitor_base_pace[comp_idx],
                fuel_start=self.rng.uniform(100, 110),
                tire_compound=self.competitor_strategies[comp_idx].tire_compounds[0],
            )

            strategy = self.competitor_strategies[comp_idx]

            # Simplified single-run simulation for each competitor
            for run_idx in range(num_runs):
                # DNF check
                dnf_prob = 0.03 + 0.02 * max(0, comp_setup.car_performance / 2.0)
                if self.rng.random() < dnf_prob:
                    competitor_times[run_idx, comp_idx] = 1e9
                    continue

                # Simulate race (simplified - not lap by lap for speed)
                total_time = 0.0

                laps_per_stint = self.rc.race_laps / (len(strategy.pit_laps) + 1)

                for stint_idx, compound in enumerate(strategy.tire_compounds):
                    compound_offset, base_wear, _ = self.cfg.tire_properties[compound]

                    # Simulate stint
                    for lap_in_stint in range(int(laps_per_stint)):
                        # Base lap
                        lap_time = self.rc.track.base_lap_time + comp_setup.car_performance

                        # Tire wear
                        wear = (lap_in_stint / laps_per_stint) * base_wear * laps_per_stint
                        lap_time += self.cfg.k_wear_lap_time * (wear ** 1.5)

                        # Fuel (decreasing)
                        laps_done = stint_idx * laps_per_stint + lap_in_stint
                        fuel_frac = 1.0 - (laps_done / self.rc.race_laps)
                        lap_time += self.cfg.k_fuel_lap_time * fuel_frac * 50

                        # Compound
                        lap_time += compound_offset

                        # Noise
                        lap_time += self.rng.normal(0, self.cfg.lap_time_noise_std)

                        total_time += lap_time

                    # Pit stop (except after last stint)
                    if stint_idx < len(strategy.pit_laps):
                        total_time += self.rc.track.pit_loss_time + self.rng.normal(0, 0.3)

                competitor_times[run_idx, comp_idx] = total_time

        print("\nCompetitor simulation complete!")
        return competitor_times
# ============================================================================
# MAIN SIMULATOR (UPDATED)
# ============================================================================

class RaceSimulator:
    """F1 Monte Carlo race simulator - FIXED competitor model"""

    def __init__(
            self,
            race_conditions: RaceConditions,
            car_setup: CarSetup,
            sim_config: SimulationConfig
    ):
        self.rc = race_conditions
        self.setup = car_setup
        self.cfg = sim_config
        self.rng = np.random.RandomState(sim_config.random_seed)

        self.N_laps = race_conditions.race_laps
        self.N_runs = sim_config.num_runs

        # Generate competitor characteristics (ONCE)
        self.competitor_field = CompetitorField(race_conditions, sim_config, self.rng)

        # DO NOT pre-simulate - we'll do it per-run now
        print(f"Competitor field generated: {self.rc.num_competitors} cars")
        print(f"  Pace range: {self.competitor_field.competitor_base_pace.min():.2f}s to "
              f"{self.competitor_field.competitor_base_pace.max():.2f}s per lap")

    def simulate_strategy(self, strategy: Strategy) -> 'SimulationResults':
        """Run Monte Carlo simulation for our car's strategy"""

        # Validate F1 rules
        if not self.rc.refueling_allowed:
            if len(set(strategy.tire_compounds)) < self.rc.min_compounds_required:
                raise ValueError(f"F1 rules: must use {self.rc.min_compounds_required} different compounds")

        # Pre-allocate arrays
        shape = (self.N_runs, self.N_laps)

        lap_times = np.zeros(shape)
        tire_wear = np.zeros(shape)
        fuel_level = np.zeros(shape)
        total_times = np.zeros(self.N_runs)
        positions = np.zeros(self.N_runs, dtype=int)
        dnf_flags = np.zeros(self.N_runs, dtype=bool)

        # Sample stochastic factors for OUR car
        wear_multipliers = np.clip(
            self.rng.normal(1.0, self.cfg.wear_rate_noise_std, self.N_runs),
            0.6, 1.4
        )
        fuel_multipliers = np.clip(
            self.rng.normal(1.0, self.cfg.fuel_burn_noise_std, self.N_runs),
            0.9, 1.1
        )

        # Per-lap events
        lap_noise = self.rng.normal(0, self.cfg.lap_time_noise_std, shape)
        safety_cars = self.rng.random(shape) < self.rc.safety_car_prob

        # NEW: Generate competitor times WITH VARIANCE per run
        print("  Simulating competitor field variance...")
        competitor_times_all_runs = self._simulate_competitor_field_stochastic()

        # Simulate each run for OUR car
        for run_idx in range(self.N_runs):
            result = self._simulate_single_run(
                strategy=strategy,
                run_idx=run_idx,
                wear_mult=wear_multipliers[run_idx],
                fuel_mult=fuel_multipliers[run_idx],
                lap_noise=lap_noise[run_idx],
                safety_cars=safety_cars[run_idx]
            )

            lap_times[run_idx] = result['lap_times']
            tire_wear[run_idx] = result['tire_wear']
            fuel_level[run_idx] = result['fuel']
            total_times[run_idx] = result['total_time']
            dnf_flags[run_idx] = result['dnf']

        # Compute positions against stochastic competitor field
        positions = self._compute_positions_stochastic(total_times, dnf_flags, competitor_times_all_runs)

        return SimulationResults(
            strategy=strategy,
            num_runs=self.N_runs,
            lap_times=lap_times,
            tire_wear=tire_wear,
            fuel_level=fuel_level,
            total_times=total_times,
            positions=positions,
            dnf_flags=dnf_flags,
            race_conditions=self.rc,
            sim_config=self.cfg
        )

    def _simulate_competitor_field_stochastic(self) -> np.ndarray:
        """
        Simulate competitor times WITH RUN-TO-RUN VARIANCE.
        Returns: (N_runs, N_competitors) array of total race times
        """
        competitor_times = np.zeros((self.N_runs, self.rc.num_competitors))

        for comp_idx in range(self.rc.num_competitors):
            base_pace = self.competitor_field.competitor_base_pace[comp_idx]
            strategy = self.competitor_field.competitor_strategies[comp_idx]

            # Calculate EXPECTED race time (deterministic part)
            expected_time = self._calculate_expected_race_time(base_pace, strategy)

            # Add per-run stochastic variance
            for run_idx in range(self.N_runs):
                # DNF check
                dnf_prob = 0.03 + 0.02 * max(0, base_pace / 2.0)
                if self.rng.random() < dnf_prob:
                    competitor_times[run_idx, comp_idx] = 1e9
                    continue

                # THIS IS THE KEY: Each run gets independent noise
                # Lap-to-lap variance accumulates (central limit theorem)
                lap_variance_total = self.cfg.lap_time_noise_std * np.sqrt(self.rc.race_laps)

                # Strategy execution variance
                pit_variance = 0.5 * len(strategy.pit_laps)  # 0.5s per pit stop

                # Traffic and random events
                random_events = self.rng.normal(0, 2.0)  # ±2s random luck

                # Total variance
                total_std = np.sqrt(lap_variance_total ** 2 + pit_variance ** 2 + 4.0)

                # Sample this run's time
                run_variance = self.rng.normal(0, total_std)

                race_time = expected_time + run_variance + random_events

                # Occasional outliers (5% chance of major incident/advantage)
                if self.rng.random() < 0.05:
                    race_time += self.rng.normal(0, total_std * 2)

                # Clamp to reasonable bounds
                competitor_times[run_idx, comp_idx] = max(race_time, expected_time * 0.92)

        return competitor_times

    def _calculate_expected_race_time(self, base_pace: float, strategy: Strategy) -> float:
        """
        Calculate expected race time for a given pace and strategy.
        Uses same physics model as our car (deterministic part only).
        """
        total_time = 0.0

        # Stint lengths
        stint_laps = []
        prev_pit = 0
        for pit_lap in strategy.pit_laps + [self.rc.race_laps]:
            stint_laps.append(pit_lap - prev_pit)
            prev_pit = pit_lap

        current_lap = 0

        for stint_idx, stint_length in enumerate(stint_laps):
            compound = strategy.tire_compounds[stint_idx]
            compound_offset, base_wear_rate, _ = self.cfg.tire_properties[compound]

            # Simulate each lap in stint (deterministic average)
            for lap_in_stint in range(stint_length):
                # Base lap time
                lap_time = self.rc.track.base_lap_time + base_pace

                # Tire degradation (progressive)
                tire_wear = (lap_in_stint / max(stint_length, 1)) * base_wear_rate * stint_length
                tire_deg = self.cfg.k_wear_lap_time * (tire_wear ** 1.5)

                # Fuel effect (decreasing through race)
                fuel_fraction = 1.0 - (current_lap / self.rc.race_laps)
                fuel_effect = self.cfg.k_fuel_lap_time * fuel_fraction * 50

                # Compound offset
                lap_time += compound_offset + tire_deg + fuel_effect

                total_time += lap_time
                current_lap += 1

            # Pit stop (except after last stint)
            if stint_idx < len(strategy.pit_laps):
                total_time += self.rc.track.pit_loss_time

        return total_time

    def _compute_positions_stochastic(
            self,
            our_times: np.ndarray,
            our_dnf_flags: np.ndarray,
            competitor_times: np.ndarray
    ) -> np.ndarray:
        """
        Compute positions using per-run competitor times.
        competitor_times shape: (N_runs, N_competitors)
        """
        positions = np.zeros(len(our_times), dtype=int)

        for run_idx in range(self.N_runs):
            if our_dnf_flags[run_idx]:
                # Count non-DNF competitors
                finished_competitors = np.sum(competitor_times[run_idx] < 1e8)
                positions[run_idx] = finished_competitors + 1
            else:
                our_time = our_times[run_idx]
                # Count how many competitors finished faster
                faster_count = np.sum(competitor_times[run_idx] < our_time)
                positions[run_idx] = faster_count + 1

        return positions

    # Keep all other methods (_simulate_single_run, _compute_lap_time, etc.) UNCHANGED
    # Just copy them from the previous version

    def _simulate_single_run(
            self,
            strategy: Strategy,
            run_idx: int,
            wear_mult: float,
            fuel_mult: float,
            lap_noise: np.ndarray,
            safety_cars: np.ndarray
    ) -> Dict:
        """Simulate single race - UNCHANGED from before"""

        W = self.setup.initial_tire_wear
        fuel = self.setup.fuel_start
        total_time = 0.0
        dnf = False

        stint_idx = 0
        current_compound = strategy.tire_compounds[0]
        current_engine_mode = strategy.engine_modes[0]
        next_pit_lap = strategy.pit_laps[0] if strategy.pit_laps else 9999

        lap_times_out = np.zeros(self.N_laps)
        tire_wear_out = np.zeros(self.N_laps)
        fuel_out = np.zeros(self.N_laps)

        for lap in range(self.N_laps):
            if lap + 1 == next_pit_lap:
                total_time += self.rc.track.pit_loss_time
                W = 0.0
                stint_idx += 1
                if stint_idx < len(strategy.tire_compounds):
                    current_compound = strategy.tire_compounds[stint_idx]
                    current_engine_mode = strategy.engine_modes[stint_idx]

                if stint_idx < len(strategy.pit_laps):
                    next_pit_lap = strategy.pit_laps[stint_idx]
                else:
                    next_pit_lap = 9999

            lap_time = self._compute_lap_time(
                wear=W,
                fuel=fuel,
                compound=current_compound,
                engine_mode=current_engine_mode,
                noise=lap_noise[lap]
            )

            if safety_cars[lap]:
                lap_time = self.rc.track.base_lap_time * self.cfg.safety_car_lap_time_factor

            puncture_prob = self.cfg.base_puncture_prob * (1 + self.cfg.puncture_wear_multiplier * W)
            if self.rng.random() < puncture_prob:
                dnf = True
                break

            total_time += lap_time

            wear_rate = self._compute_wear_rate(current_compound) * wear_mult
            W = min(W + wear_rate, 1.0)

            burn_rate = self._compute_fuel_burn(current_engine_mode) * fuel_mult
            fuel = max(fuel - burn_rate, 0.0)

            lap_times_out[lap] = lap_time
            tire_wear_out[lap] = W
            fuel_out[lap] = fuel

        return {
            'lap_times': lap_times_out,
            'tire_wear': tire_wear_out,
            'fuel': fuel_out,
            'total_time': total_time if not dnf else 1e9,
            'dnf': dnf
        }

    def _compute_lap_time(
            self,
            wear: float,
            fuel: float,
            compound: TireCompound,
            engine_mode: EngineMode,
            noise: float
    ) -> float:
        """F1 lap time model"""

        tau_0 = self.rc.track.base_lap_time + self.setup.car_performance

        tau_wear = self.cfg.k_wear_lap_time * (wear ** 1.5)

        fuel_fraction = fuel / self.setup.fuel_start
        tau_fuel = self.cfg.k_fuel_lap_time * fuel_fraction * 50

        compound_offset, _, _ = self.cfg.tire_properties[compound]

        engine_factor = engine_mode.value

        tau_aero = self.cfg.k_downforce_lap_time * (1.0 - self.setup.downforce) * 0.5

        tau = (tau_0 + tau_wear + tau_fuel + tau_aero + compound_offset) / engine_factor
        tau += noise

        return max(tau, tau_0 * 0.90)

    def _compute_wear_rate(self, compound: TireCompound) -> float:
        """Tire wear per lap"""
        _, base_wear, _ = self.cfg.tire_properties[compound]
        wear = base_wear * self.rc.track.tire_stress
        temp_factor = 1.0 + 0.015 * (self.rc.track_temp - 25)
        return wear * temp_factor

    def _compute_fuel_burn(self, engine_mode: EngineMode) -> float:
        """Fuel per lap"""
        base = self.cfg.base_fuel_burn_rate * self.rc.track.fuel_usage
        return base * engine_mode.value

# ============================================================================
# RESULTS CLASS (unchanged, just copy from before)
# ============================================================================

@dataclass
class SimulationResults:
    """Results container"""
    strategy: Strategy
    num_runs: int
    lap_times: np.ndarray
    tire_wear: np.ndarray
    fuel_level: np.ndarray
    total_times: np.ndarray
    positions: np.ndarray
    dnf_flags: np.ndarray
    race_conditions: RaceConditions
    sim_config: SimulationConfig
    _stats: Dict = field(default_factory=dict, init=False, repr=False)

    def get_statistics(self) -> Dict:
        if self._stats:
            return self._stats

        valid_mask = ~self.dnf_flags
        valid_times = self.total_times[valid_mask]
        valid_positions = self.positions[valid_mask]

        if len(valid_times) == 0:
            # All DNF - return dummy stats
            return {
                'mean_time': np.inf,
                'win_probability': 0.0,
                'podium_probability': 0.0,
                'dnf_probability': 1.0,
            }

        stats = {
            'mean_time': np.mean(valid_times),
            'median_time': np.median(valid_times),
            'std_time': np.std(valid_times),
            'min_time': np.min(valid_times),
            'max_time': np.max(valid_times),

            'mean_position': np.mean(valid_positions),
            'median_position': np.median(valid_positions),
            'win_probability': np.mean(valid_positions == 1),
            'podium_probability': np.mean(valid_positions <= 3),
            'top5_probability': np.mean(valid_positions <= 5),
            'top10_probability': np.mean(valid_positions <= 10),

            'dnf_probability': np.mean(self.dnf_flags),
            'cvar_10': np.mean(np.sort(self.total_times)[-int(0.1*len(self.total_times)):]),
            'cvar_5': np.mean(np.sort(self.total_times)[-int(0.05*len(self.total_times)):]),

            'position_distribution': np.bincount(valid_positions, minlength=22),
            'time_percentiles': np.percentile(valid_times, [5, 25, 50, 75, 95]),

            'mean_lap_times': np.mean(self.lap_times, axis=0),
            'std_lap_times': np.std(self.lap_times, axis=0),
            'mean_tire_wear': np.mean(self.tire_wear, axis=0),
            'mean_fuel': np.mean(self.fuel_level, axis=0),
        }

        self._stats = stats
        return stats

    def compute_utility(self, risk_tolerance: float = 0.5) -> float:
        stats = self.get_statistics()

        conservative_score = (1 - stats['dnf_probability']) * 0.6 + \
                            (1 / (1 + stats['std_time'] / max(stats['mean_time'], 1))) * 0.4

        aggressive_score = stats['win_probability'] * 0.7 + \
                          stats['podium_probability'] * 0.3

        utility = (1 - risk_tolerance) * conservative_score + \
                  risk_tolerance * aggressive_score

        return utility

    def print_summary(self):
        stats = self.get_statistics()
        print(f"\n{'='*60}")
        print(f"Strategy: {self.strategy.name}")
        print(f"Pit stops: {self.strategy.pit_laps}")
        print(f"Compounds: {[c.value for c in self.strategy.tire_compounds]}")
        print(f"{'='*60}")
        print(f"\nRace Time:")
        print(f"  Mean:   {stats['mean_time']:.2f}s ({stats['mean_time']/60:.1f} min)")
        print(f"  Median: {stats['median_time']:.2f}s")
        print(f"  Std:    {stats['std_time']:.2f}s")
        print(f"\nFinishing Position:")
        print(f"  Mean:   P{stats['mean_position']:.1f}")
        print(f"  Median: P{stats['median_position']:.0f}")
        print(f"\nProbabilities:")
        print(f"  Win (P1):  {stats['win_probability']*100:.1f}%")
        print(f"  Podium:    {stats['podium_probability']*100:.1f}%")
        print(f"  Top 5:     {stats['top5_probability']*100:.1f}%")
        print(f"  DNF:       {stats['dnf_probability']*100:.2f}%")

# ============================================================================
# STRATEGY OPTIMIZER (updated)
# ============================================================================

class StrategyOptimizer:
    def __init__(self, simulator: RaceSimulator):
        self.sim = simulator

    def generate_strategies(self) -> List[Strategy]:
        """Generate F1-realistic strategies"""
        strategies = []
        N = self.sim.N_laps

        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]

        # 1-stop strategies
        for early_pit in [N//3, N//2, 2*N//3]:
            for start_compound in compounds:
                for end_compound in compounds:
                    if start_compound != end_compound:  # F1 rule
                        strategies.append(Strategy(
                            name=f"1-stop L{early_pit}: {start_compound.value[0].upper()}-{end_compound.value[0].upper()}",
                            pit_laps=[early_pit],
                            tire_compounds=[start_compound, end_compound]
                        ))

        # 2-stop strategies
        for pit1 in [N//4, N//3]:
            for pit2 in [N//2, 2*N//3]:
                for c1, c2, c3 in [
                    (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD),
                    (TireCompound.MEDIUM, TireCompound.SOFT, TireCompound.MEDIUM),
                    (TireCompound.SOFT, TireCompound.SOFT, TireCompound.MEDIUM),
                ]:
                    strategies.append(Strategy(
                        name=f"2-stop L{pit1},L{pit2}: {c1.value[0].upper()}-{c2.value[0].upper()}-{c3.value[0].upper()}",
                        pit_laps=[pit1, pit2],
                        tire_compounds=[c1, c2, c3]
                    ))

        return strategies

    def evaluate_all(
        self,
        strategies: List[Strategy],
        risk_tolerance: float = 0.5
    ) -> List[Tuple[Strategy, SimulationResults, float]]:
        results = []

        for i, strategy in enumerate(strategies):
            print(f"Evaluating {i+1}/{len(strategies)}: {strategy.name}...", end='\r')
            try:
                sim_results = self.sim.simulate_strategy(strategy)
                utility = sim_results.compute_utility(risk_tolerance)
                results.append((strategy, sim_results, utility))
            except Exception as e:
                print(f"\nSkipping {strategy.name}: {e}")
                continue

        results.sort(key=lambda x: x[2], reverse=True)

        print("\n" + "="*70)
        print("TOP 10 STRATEGIES")
        print("="*70)
        for i, (strat, res, util) in enumerate(results[:10]):
            stats = res.get_statistics()
            print(f"{i+1:2d}. {strat.name:40s} | U:{util:.3f} | "
                  f"W:{stats['win_probability']*100:5.1f}% | "
                  f"Pod:{stats['podium_probability']*100:5.1f}% | "
                  f"Avg:P{stats['mean_position']:.1f}")

        return results

# ============================================================================
# EXAMPLE - F1 MONACO GP
# ============================================================================

class F1Team(Enum):
    """2024 F1 team performance levels"""
    RED_BULL = -1.0  # Dominant pace
    FERRARI = -0.8  # Top team
    MERCEDES = -0.7  # Top team
    MCLAREN = -0.5  # Strong midfield
    ASTON_MARTIN = -0.3  # Midfield
    ALPINE = 0.0  # Midfield
    WILLIAMS = 0.3  # Lower midfield
    HAAS = 0.5  # Lower midfield
    ALPHA_TAURI = 0.6  # Back of grid
    ALFA_ROMEO = 0.8  # Back of grid


def create_monaco_gp(our_team: F1Team = F1Team.FERRARI):
    """
    Monaco GP 2024

    Args:
        our_team: Which F1 team we're driving for (affects car performance)
    """

    track = TrackConfig(
        name="Monaco",
        lap_length_km=3.337,
        base_lap_time=74.5,
        num_corners=19,
        pit_loss_time=23.5,
        tire_stress=1.15,
        fuel_usage=0.85,
        overtaking_difficulty=0.95
    )

    conditions = RaceConditions(
        race_laps=78,
        track=track,
        track_temp=26.0,
        safety_car_prob=0.025,
        num_competitors=19,
        field_spread=2.0,
    )

    car_setup = CarSetup(
        downforce=0.85,
        car_performance=our_team.value,  # ← Use team preset
        fuel_start=105.0,
        tire_compound=TireCompound.MEDIUM,
    )

    sim_config = SimulationConfig(
        num_runs=5000,
        random_seed=42,
    )

    return track, conditions, car_setup, sim_config


def main():
    print("=" * 70)
    print("F1 MONACO GP STRATEGY SIMULATOR")
    print("=" * 70)

    # SELECT YOUR TEAM HERE
    our_team = F1Team.FERRARI  # ← Change this!

    print(f"\n🏎️  Team: {our_team.name}")
    print(f"   Car Performance: {our_team.value:+.1f}s per lap")

    track, conditions, car_setup, sim_config = create_monaco_gp(our_team)

    print(f"\n📊 Simulation Setup:")
    print(f"   Track: {track.name}")
    print(f"   Laps: {conditions.race_laps}")
    print(f"   Monte Carlo runs: {sim_config.num_runs:,}")
    print(f"   Competitors: {conditions.num_competitors}")

    simulator = RaceSimulator(conditions, car_setup, sim_config)
    optimizer = StrategyOptimizer(simulator)

    print("\n🔧 Generating strategies...")
    strategies = optimizer.generate_strategies()
    print(f"   Generated {len(strategies)} candidate strategies")

    strategies = strategies[:30]

    print(f"\n⚡ Evaluating top {len(strategies)} strategies...")
    results = optimizer.evaluate_all(strategies, risk_tolerance=0.6)

    print("\n" + "=" * 70)
    print("🏆 DETAILED RESULTS - TOP 3 STRATEGIES")
    print("=" * 70)
    for i in range(min(3, len(results))):
        results[i][1].print_summary()

    # Print performance summary
    best_strategy_stats = results[0][1].get_statistics()
    print("\n" + "=" * 70)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Best Strategy: {results[0][0].name}")
    print(f"  Win Rate:     {best_strategy_stats['win_probability'] * 100:.1f}%")
    print(f"  Podium Rate:  {best_strategy_stats['podium_probability'] * 100:.1f}%")
    print(f"  Avg Position: P{best_strategy_stats['mean_position']:.1f}")
    print(f"  DNF Rate:     {best_strategy_stats['dnf_probability'] * 100:.2f}%")

    return results

if __name__ == "__main__":
    results = main()