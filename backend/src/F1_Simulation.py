"""
Racing Strategy Monte Carlo Simulator - F1 Edition
With JSON track configuration support
"""

import numpy as np
import json
from pathlib import Path
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
    INTERMEDIATE = "intermediate"
    WET = "wet"

class Weather(Enum):
    DRY = "dry"
    MIXED = "mixed"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"

class EngineMode(Enum):
    ECO = 0.98
    NORMAL = 1.0
    PUSH = 1.02
    OVERTAKE = 1.04

@dataclass
class TrackConfig:
    """F1 Track configuration - now loaded from JSON"""
    name: str
    lap_length_km: float
    base_lap_time: float  # seconds - calculated from avg_lap_time_ms in JSON
    num_corners: int

    # F1-specific
    drs_zones: int = 2
    pit_loss_time: float = 22.0  # From pit_stop_time_s in JSON
    pit_lane_delta: float = 18.0
    pit_service_time: float = 2.0

    # Track characteristics (from JSON)
    tire_stress: float = 1.0
    fuel_usage: float = 1.0  # Derived from fuel_usage_per_lap_l
    overtaking_difficulty: float = 0.5

    # Metadata
    track_id: str = ""
    full_name: str = ""
    track_type: str = ""
    direction: str = ""

    @classmethod
    def from_json(cls, track_data: Dict, target_lap_time: float = None) -> 'TrackConfig':
        """
        Create TrackConfig from JSON track data.

        Args:
            track_data: Dictionary from track_configs.json
            target_lap_time: Override lap time (if None, uses avg_lap_time_ms from JSON)
        """
        # Extract lap time
        if target_lap_time is not None:
            base_lap_time = target_lap_time
        elif track_data.get('avg_lap_time_ms'):
            base_lap_time = track_data['avg_lap_time_ms'] / 1000.0  # Convert ms to seconds
        else:
            # Improved fallback: slower for twisty tracks, faster for straights
            avg_speed_kmh = 190.0 - 5.0 * (track_data['num_turns'] / 10.0)
            avg_speed_kmh = max(150.0, avg_speed_kmh)  # never too low
            base_lap_time = (track_data['length_km'] / avg_speed_kmh) * 3600.0
            print(f"  ⚠️  No lap time data for {track_data['name']}, estimated: {base_lap_time:.1f}s (speed={avg_speed_kmh:.1f} km/h)")

        # Fuel usage normalization (1.0 = baseline ~2.5L/lap)
        fuel_per_lap = track_data.get('fuel_usage_per_lap_l', 2.5)
        fuel_kg_per_lap = track_data.get('fuel_usage_per_lap_l', 2.5) * 0.75
        fuel_usage_normalized = fuel_kg_per_lap / 2.0  # baseline = 2 kg/lap average


        # Pit stop time
        pit_stop_time = track_data.get('pit_stop_time_s', 22.0)
        # Break down total pit loss into service + travel components
        pit_service_time = 2.3  # seconds stationary
        pit_lane_delta = max(pit_stop_time - pit_service_time, 10.0)

        return cls(
            name=track_data['name'],
            lap_length_km=track_data['length_km'],
            base_lap_time=base_lap_time,
            num_corners=track_data['num_turns'],
            pit_loss_time=pit_stop_time,
            pit_service_time=pit_service_time,
            pit_lane_delta=pit_lane_delta,
            tire_stress=track_data.get('tire_stress', 1.0),
            fuel_usage=fuel_usage_normalized,
            overtaking_difficulty=track_data.get('overtaking_difficulty', 0.5),
            track_id=track_data['id'],
            full_name=track_data.get('fullName', track_data['name']),
            track_type=track_data.get('type', 'UNKNOWN'),
            direction=track_data.get('direction', 'CLOCKWISE'),
        )

@dataclass
class CarSetup:
    """F1 Car setup"""
    downforce: float = 0.5
    engine_mode: EngineMode = EngineMode.NORMAL
    fuel_start: float = 110.0
    tire_compound: TireCompound = TireCompound.MEDIUM
    initial_tire_wear: float = 0.0
    car_performance: float = 0.0

@dataclass
class RaceConditions:
    """F1 Race conditions"""
    race_laps: int
    track: TrackConfig
    track_temp: float = 25.0
    weather: Weather = Weather.DRY
    safety_car_prob: float = 0.015
    vsc_prob: float = 0.008
    red_flag_prob: float = 0.0002
    num_competitors: int = 19
    field_spread: float = 2.5
    min_compounds_required: int = 2
    max_fuel_kg: float = 110.0
    refueling_allowed: bool = False

@dataclass
class SimulationConfig:
    """Monte Carlo configuration - F1 calibrated"""
    num_runs: int = 10000
    random_seed: Optional[int] = 42
    k_wear_lap_time: float = 12.0
    k_fuel_lap_time: float = 0.03
    k_downforce_lap_time: float = 1.2

    tire_properties: Dict[TireCompound, Tuple[float, float, float]] = field(default_factory=lambda: {
        TireCompound.SOFT:   (-0.8, 0.030, 25.0),
        TireCompound.MEDIUM: ( 0.0, 0.015, 20.0),
        TireCompound.HARD:   ( 0.6, 0.008, 15.0),
        TireCompound.INTERMEDIATE: (2.0, 0.020, 10.0),
        TireCompound.WET:   (5.0, 0.015, 8.0),
    })

    lap_time_noise_std: float = 0.15
    wear_rate_noise_std: float = 0.20
    fuel_burn_noise_std: float = 0.05
    base_fuel_burn_rate: float = 1.3
    base_puncture_prob: float = 0.0003
    puncture_wear_multiplier: float = 5.0
    rain_slowdown_factor: float = 0.10
    rain_wear_reduction: float = 0.7
    safety_car_duration_laps: int = 3
    safety_car_lap_time_factor: float = 1.45
    vsc_duration_laps: int = 2
    vsc_lap_time_factor: float = 1.30

@dataclass
class Strategy:
    """Pit strategy with fuel management"""
    name: str
    pit_laps: List[int]
    tire_compounds: List[TireCompound]
    starting_fuel: float
    engine_modes: Optional[List[EngineMode]] = None

    def __post_init__(self):
        if len(self.tire_compounds) != len(self.pit_laps) + 1:
            raise ValueError(f"Need {len(self.pit_laps) + 1} compounds for {len(self.pit_laps)} stops")
        if self.engine_modes is None:
            self.engine_modes = [EngineMode.NORMAL] * (len(self.pit_laps) + 1)
        if self.starting_fuel > 110.0:
            raise ValueError(f"F1 max fuel is 110kg, got {self.starting_fuel}kg")
        if self.starting_fuel < 80.0:
            raise ValueError(f"Starting fuel too low: {self.starting_fuel}kg (min ~80kg for race)")

    def estimate_fuel_needed(self, race_laps: int, burn_rate: float = 1.4) -> float:
        return race_laps * burn_rate

    def is_fuel_feasible(self, race_laps: int, burn_rate: float = 1.4) -> bool:
        needed = self.estimate_fuel_needed(race_laps, burn_rate)
        return self.starting_fuel >= needed * 0.95

# ============================================================================
# TRACK LOADER
# ============================================================================

class TrackDatabase:
    """Loads and manages track configurations from JSON"""

    def __init__(self, json_path: str = "track_configs.json"):
        self.json_path = Path(json_path)
        self.tracks: Dict[str, Dict] = {}
        self.load_tracks()

    def load_tracks(self):
        """Load all tracks from JSON file"""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Track configuration file not found: {self.json_path}")

        with open(self.json_path, 'r') as f:
            tracks_list = json.load(f)

        # Convert list to dictionary keyed by track ID
        self.tracks = {track['id']: track for track in tracks_list}
        print(f"📁 Loaded {len(self.tracks)} tracks from {self.json_path}")

    def get_track(self, track_id: str, target_lap_time: float = None) -> TrackConfig:
        """
        Get a TrackConfig for a specific track.

        Args:
            track_id: Track identifier (e.g., 'monaco', 'adelaide')
            target_lap_time: Override lap time in seconds (optional)
        """
        if track_id not in self.tracks:
            available = ', '.join(list(self.tracks.keys())[:10])
            raise ValueError(f"Track '{track_id}' not found. Available: {available}...")

        track_data = self.tracks[track_id]
        return TrackConfig.from_json(track_data, target_lap_time)

    def list_tracks(self) -> List[str]:
        """Return list of all available track IDs"""
        return list(self.tracks.keys())

    def print_tracks(self):
        """Print formatted list of all tracks"""
        print("\n" + "="*80)
        print("AVAILABLE TRACKS")
        print("="*80)
        print(f"{'ID':<20} {'Name':<30} {'Length':<10} {'Turns':<8} {'Type':<12}")
        print("-"*80)
        for track_id, track_data in sorted(self.tracks.items()):
            print(f"{track_id:<20} {track_data['name']:<30} "
                  f"{track_data['length_km']:>6.2f} km  {track_data['num_turns']:>4}   "
                  f"{track_data.get('type', 'N/A'):<12}")

# ============================================================================
# COMPETITOR FIELD MODEL
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
        top_teams = 6
        midfield = min(8, n - top_teams)
        backmarkers = n - top_teams - midfield

        pace = np.zeros(n)
        pace[:top_teams] = self.rng.uniform(-0.8, -0.2, top_teams)
        pace[top_teams:top_teams + midfield] = self.rng.uniform(-0.2, 0.8, midfield)
        if backmarkers > 0:
            pace[top_teams + midfield:] = self.rng.uniform(0.8, 2.0, backmarkers)
        pace += self.rng.normal(0, 0.1, n)
        return pace

    def _assign_competitor_strategies(self) -> List[Strategy]:
        """Assign diverse strategies to competitors"""
        strategies = []
        n = self.rc.num_competitors

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
            start_fuel = float(self.rng.uniform(100.0, 110.0))

            if self.rng.random() < 0.65:
                pit_lap = self.rng.randint(
                    max(self.rc.race_laps // 3, 15),
                    min(2 * self.rc.race_laps // 3, self.rc.race_laps - 10)
                )
                compounds, code = one_stop_options[self.rng.randint(0, len(one_stop_options))]
                strategies.append(Strategy(
                    name=f"Comp{i}_1stop_{code}_L{pit_lap}",
                    pit_laps=[pit_lap],
                    tire_compounds=compounds,
                    starting_fuel=start_fuel
                ))
            else:
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
                    tire_compounds=compounds,
                    starting_fuel=start_fuel
                ))

        return strategies

# ============================================================================
# MAIN SIMULATOR (same as before, just keeping it complete)
# ============================================================================

class RaceSimulator:
    """F1 Monte Carlo race simulator"""

    def __init__(self, race_conditions: RaceConditions, car_setup: CarSetup, sim_config: SimulationConfig):
        self.rc = race_conditions
        self.setup = car_setup
        self.cfg = sim_config
        self.rng = np.random.RandomState(sim_config.random_seed)
        self.N_laps = race_conditions.race_laps
        self.N_runs = sim_config.num_runs
        self.competitor_field = CompetitorField(race_conditions, sim_config, self.rng)

        print(f"Competitor field generated: {self.rc.num_competitors} cars")
        print(f"  Pace range: {self.competitor_field.competitor_base_pace.min():.2f}s to "
              f"{self.competitor_field.competitor_base_pace.max():.2f}s per lap")

    def simulate_strategy(self, strategy: Strategy) -> 'SimulationResults':
        if not self.rc.refueling_allowed:
            if len(set(strategy.tire_compounds)) < self.rc.min_compounds_required:
                raise ValueError(f"F1 rules: must use {self.rc.min_compounds_required} different compounds")

        shape = (self.N_runs, self.N_laps)
        lap_times = np.zeros(shape)
        tire_wear = np.zeros(shape)
        fuel_level = np.zeros(shape)
        total_times = np.zeros(self.N_runs)
        positions = np.zeros(self.N_runs, dtype=int)
        dnf_flags = np.zeros(self.N_runs, dtype=bool)

        wear_multipliers = np.clip(self.rng.normal(1.0, self.cfg.wear_rate_noise_std, self.N_runs), 0.6, 1.4)
        fuel_multipliers = np.clip(self.rng.normal(1.0, self.cfg.fuel_burn_noise_std, self.N_runs), 0.9, 1.1)
        lap_noise_std_adj = self.cfg.lap_time_noise_std * (1 + 0.5 * self.rc.track.overtaking_difficulty)
        lap_noise = self.rng.normal(0, lap_noise_std_adj, shape)
        safety_cars = self.rng.random(shape) < self.rc.safety_car_prob

        print("  Simulating competitor field variance...")
        competitor_times_all_runs = self._simulate_competitor_field_stochastic()

        for run_idx in range(self.N_runs):
            result = self._simulate_single_run(strategy, run_idx, wear_multipliers[run_idx],
                                               fuel_multipliers[run_idx], lap_noise[run_idx],
                                               safety_cars[run_idx])
            lap_times[run_idx] = result['lap_times']
            tire_wear[run_idx] = result['tire_wear']
            fuel_level[run_idx] = result['fuel']
            total_times[run_idx] = result['total_time']
            dnf_flags[run_idx] = result['dnf']

        positions = self._compute_positions_stochastic(total_times, dnf_flags, competitor_times_all_runs)

        return SimulationResults(strategy, self.N_runs, lap_times, tire_wear, fuel_level,
                                total_times, positions, dnf_flags, self.rc, self.cfg)

    def _simulate_competitor_field_stochastic(self) -> np.ndarray:
        competitor_times = np.zeros((self.N_runs, self.rc.num_competitors))

        for comp_idx in range(self.rc.num_competitors):
            base_pace = self.competitor_field.competitor_base_pace[comp_idx]
            strategy = self.competitor_field.competitor_strategies[comp_idx]
            competitor_fuel = self.rng.uniform(105.0, 109.0)
            expected_time = self._calculate_expected_race_time(base_pace, strategy, competitor_fuel)

            for run_idx in range(self.N_runs):
                dnf_prob = 0.03 + 0.02 * max(0, base_pace / 2.0)
                if self.rng.random() < dnf_prob:
                    competitor_times[run_idx, comp_idx] = 1e9
                    continue

                lap_variance_total = self.cfg.lap_time_noise_std * np.sqrt(self.rc.race_laps)
                pit_variance = 0.5 * len(strategy.pit_laps)
                random_events = self.rng.normal(0, 2.0)
                total_std = np.sqrt(lap_variance_total ** 2 + pit_variance ** 2 + 4.0)
                run_variance = self.rng.normal(0, total_std)
                race_time = expected_time + run_variance + random_events

                if self.rng.random() < 0.05:
                    race_time += self.rng.normal(0, total_std * 2)

                competitor_times[run_idx, comp_idx] = max(race_time, expected_time * 0.92)

        return competitor_times

    def _calculate_expected_race_time(self, base_pace: float, strategy: Strategy, starting_fuel: float = None) -> float:
        if starting_fuel is None:
            starting_fuel = 107.0

        total_time = 0.0
        stint_laps = []
        prev_pit = 0
        for pit_lap in strategy.pit_laps + [self.rc.race_laps]:
            stint_laps.append(pit_lap - prev_pit)
            prev_pit = pit_lap

        current_lap = 0
        fuel = starting_fuel

        for stint_idx, stint_length in enumerate(stint_laps):
            compound = strategy.tire_compounds[stint_idx]
            compound_offset, base_wear_rate, _ = self.cfg.tire_properties[compound]

            for lap_in_stint in range(stint_length):
                lap_time = self.rc.track.base_lap_time + base_pace
                tire_wear = (lap_in_stint / max(stint_length, 1)) * base_wear_rate * stint_length
                tire_deg = self.cfg.k_wear_lap_time * (tire_wear ** 1.5)
                fuel_effect = self.cfg.k_fuel_lap_time * fuel
                lap_time += compound_offset + tire_deg + fuel_effect
                total_time += lap_time
                current_lap += 1
                burn_rate = self.cfg.base_fuel_burn_rate * self.rc.track.fuel_usage
                fuel = max(fuel - burn_rate, 0.0)

            if stint_idx < len(strategy.pit_laps):
                total_time += self.rc.track.pit_loss_time

        return total_time

    def _compute_positions_stochastic(self, our_times: np.ndarray, our_dnf_flags: np.ndarray,
                                     competitor_times: np.ndarray) -> np.ndarray:
        positions = np.zeros(len(our_times), dtype=int)

        for run_idx in range(self.N_runs):
            if our_dnf_flags[run_idx]:
                finished_competitors = np.sum(competitor_times[run_idx] < 1e8)
                positions[run_idx] = finished_competitors + 1
            else:
                our_time = our_times[run_idx]
                faster_count = np.sum(competitor_times[run_idx] < our_time)
                positions[run_idx] = faster_count + 1

        return positions

    def _simulate_single_run(self, strategy: Strategy, run_idx: int, wear_mult: float,
                            fuel_mult: float, lap_noise: np.ndarray, safety_cars: np.ndarray) -> Dict:
        W = self.setup.initial_tire_wear
        fuel = strategy.starting_fuel
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

            lap_time = self._compute_lap_time(W, fuel, current_compound, current_engine_mode, lap_noise[lap])

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

            if fuel <= 0.0 and lap < self.N_laps - 1:
                dnf = True
                break

            lap_times_out[lap] = lap_time
            tire_wear_out[lap] = W
            fuel_out[lap] = fuel

        return {'lap_times': lap_times_out, 'tire_wear': tire_wear_out, 'fuel': fuel_out,
                'total_time': total_time if not dnf else 1e9, 'dnf': dnf}

    def _compute_lap_time(self, wear: float, fuel: float, compound: TireCompound,
                         engine_mode: EngineMode, noise: float) -> float:
        tau_0 = self.rc.track.base_lap_time + self.setup.car_performance
        tau_wear = self.cfg.k_wear_lap_time * (wear ** 1.5)
        tau_fuel = self.cfg.k_fuel_lap_time * fuel
        compound_offset, _, _ = self.cfg.tire_properties[compound]
        engine_factor = engine_mode.value
        tau_aero = self.cfg.k_downforce_lap_time * (1.0 - self.setup.downforce) * 0.5
        tau = (tau_0 + tau_wear + tau_fuel + tau_aero + compound_offset) / engine_factor
        tau += noise
        return max(tau, tau_0 * 0.90)

    def _compute_wear_rate(self, compound: TireCompound) -> float:
        _, base_wear, _ = self.cfg.tire_properties[compound]
        stress_factor = 1.0 + 0.4 * (self.rc.track.tire_stress - 0.7)
        temp_factor = 1.0 + 0.02 * (self.rc.track_temp - 25)
        return base_wear * stress_factor * temp_factor

    def _compute_fuel_burn(self, engine_mode: EngineMode) -> float:
        base = self.cfg.base_fuel_burn_rate * self.rc.track.fuel_usage
        return base * engine_mode.value

# ============================================================================
# RESULTS CLASS
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
            return {'mean_time': np.inf, 'win_probability': 0.0, 'podium_probability': 0.0, 'dnf_probability': 1.0}

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
        aggressive_score = stats['win_probability'] * 0.7 + stats['podium_probability'] * 0.3
        return (1 - risk_tolerance) * conservative_score + risk_tolerance * aggressive_score

    def print_summary(self):
        stats = self.get_statistics()
        print(f"\n{'='*60}")
        print(f"Strategy: {self.strategy.name}")
        print(f"Pit stops: {self.strategy.pit_laps}")
        print(f"Stint details:")
        stint_ends = self.strategy.pit_laps + [self.race_conditions.race_laps]
        prev = 0
        for compound, end in zip(self.strategy.tire_compounds, stint_ends):
            length = end - prev
            print(f"  {compound.value.capitalize():<10} → Lap {end:<3d} (stint length: {length:2d} laps)")
            prev = end
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
# STRATEGY OPTIMIZER
# ============================================================================

class StrategyOptimizer:
    def __init__(self, simulator: RaceSimulator):
        self.sim = simulator

    def generate_strategies(self, include_fuel_variants: bool = True) -> List[Strategy]:
        strategies = []
        N = self.sim.N_laps
        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]

        if include_fuel_variants:
            fuel_options = [105.0, 107.0, 109.0]
        else:
            fuel_options = [107.0]

        estimated_burn_per_lap = self.sim.cfg.base_fuel_burn_rate * self.sim.rc.track.fuel_usage
        min_fuel_needed = N * estimated_burn_per_lap

        print(f"  Estimated fuel burn: {estimated_burn_per_lap:.2f} kg/lap")
        print(f"  Minimum fuel for {N} laps: {min_fuel_needed:.1f} kg")

        fuel_options = [f for f in fuel_options if f >= min_fuel_needed * 1.02]
        if not fuel_options:
            print(f"  ⚠️  Warning: All fuel options too low, using minimum + 5%")
            fuel_options = [min_fuel_needed * 1.05]

        print(f"  Testing {len(fuel_options)} fuel loads: {fuel_options}")

        # 1-stop strategies
        for pit_lap in [N // 3, 2 * N // 5, N // 2, 3 * N // 5, 2 * N // 3]:
            for start_compound in compounds:
                for end_compound in compounds:
                    if start_compound != end_compound:
                        for fuel in fuel_options:
                            fuel_label = ""
                            if len(fuel_options) > 1:
                                if fuel == min(fuel_options):
                                    fuel_label = "_LightFuel"
                                elif fuel == max(fuel_options):
                                    fuel_label = "_HeavyFuel"
                            strategies.append(Strategy(
                                name=f"1stop_L{pit_lap}_{start_compound.value[0].upper()}{end_compound.value[0].upper()}{fuel_label}",
                                pit_laps=[pit_lap],
                                tire_compounds=[start_compound, end_compound],
                                starting_fuel=fuel
                            ))

        # 2-stop strategies
        two_stop_configs = [(N // 4, N // 2), (N // 3, 2 * N // 3), (N // 4, 3 * N // 4)]
        two_stop_compounds = [
            (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD),
            (TireCompound.MEDIUM, TireCompound.SOFT, TireCompound.MEDIUM),
            (TireCompound.SOFT, TireCompound.SOFT, TireCompound.MEDIUM),
            (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.MEDIUM),
        ]

        for pit1, pit2 in two_stop_configs:
            for c1, c2, c3 in two_stop_compounds:
                fuel_options_2stop = [f for f in fuel_options if f <= max(fuel_options)]
                for fuel in fuel_options_2stop:
                    fuel_label = ""
                    if len(fuel_options_2stop) > 1:
                        if fuel == min(fuel_options_2stop):
                            fuel_label = "_LightFuel"
                    strategies.append(Strategy(
                        name=f"2stop_L{pit1}L{pit2}_{c1.value[0].upper()}{c2.value[0].upper()}{c3.value[0].upper()}{fuel_label}",
                        pit_laps=[pit1, pit2],
                        tire_compounds=[c1, c2, c3],
                        starting_fuel=fuel
                    ))

        print(f"  Generated {len(strategies)} total strategies")

        feasible_strategies = [s for s in strategies if s.is_fuel_feasible(N, estimated_burn_per_lap)]
        print(f"  {len(feasible_strategies)} strategies are fuel-feasible")
        return feasible_strategies

    def evaluate_all(self, strategies: List[Strategy], risk_tolerance: float = 0.5) -> List[Tuple[Strategy, SimulationResults, float]]:
        results = []
        for i, strategy in enumerate(strategies):
            print(f"Evaluating {i+1}/{len(strategies)}: {strategy.name:50s}", end='\r')
            try:
                sim_results = self.sim.simulate_strategy(strategy)
                utility = sim_results.compute_utility(risk_tolerance)
                results.append((strategy, sim_results, utility))
            except Exception as e:
                print(f"\n⚠️  Skipping {strategy.name}: {e}")
                continue

        results.sort(key=lambda x: x[2], reverse=True)

        print("\n" + "="*80)
        print("TOP 10 STRATEGIES")
        print("="*80)
        print(f"{'Rank':<5} {'Strategy':<45} {'Fuel':<6} {'Utility':<7} {'Win%':<7} {'Pod%':<7} {'Avg Pos':<8}")
        print("-"*80)
        for i, (strat, res, util) in enumerate(results[:10]):
            stats = res.get_statistics()
            print(f"{i+1:<5} {strat.name:<45} {strat.starting_fuel:>5.1f}kg {util:>6.3f} "
                  f"{stats['win_probability']*100:>6.1f}% {stats['podium_probability']*100:>6.1f}% "
                  f"P{stats['mean_position']:>5.1f}")

        return results

# ============================================================================
# F1 TEAM PRESETS
# ============================================================================

class F1Team(Enum):
    """2024 F1 team performance levels"""
    RED_BULL = -1.0
    FERRARI = -0.8
    MERCEDES = -0.7
    MCLAREN = -0.5
    ASTON_MARTIN = -0.3
    ALPINE = 0.0
    WILLIAMS = 0.3
    HAAS = 0.5
    ALPHA_TAURI = 0.6
    ALFA_ROMEO = 0.8

# ============================================================================
# MAIN FUNCTION - NOW WITH TRACK SELECTION
# ============================================================================

def main():
    print("="*70)
    print("F1 STRATEGY SIMULATOR - WITH JSON TRACK DATABASE")
    print("="*70)

    # Load track database
    track_db = TrackDatabase("data/track_configs.json")

    # Show available tracks
    track_db.print_tracks()

    print("\n" + "="*70)
    print("SELECT RACE CONFIGURATION")
    print("="*70)

    # SELECT TRACK HERE
    track_id = "adelaide"  # ← CHANGE THIS to any track ID from the JSON

    # SELECT TEAM
    our_team = F1Team.FERRARI

    # RACE LENGTH (adjust for each track)
    race_laps = 78  # Adelaide GP typical length

    print(f"\n🏁 Track: {track_id}")
    print(f"🏎️  Team: {our_team.name}")
    print(f"📊 Laps: {race_laps}")

    # Load track config
    track = track_db.get_track(track_id)

    print(f"\n📍 Track Details:")
    print(f"   Name: {track.full_name}")
    print(f"   Length: {track.lap_length_km:.2f} km")
    print(f"   Turns: {track.num_corners}")
    print(f"   Type: {track.track_type}")
    print(f"   Base Lap Time: {track.base_lap_time:.2f}s")
    print(f"   Pit Loss: {track.pit_loss_time:.2f}s")
    print(f"   Tire Stress: {track.tire_stress:.2f}x")
    print(f"   Fuel Usage: {track.fuel_usage:.2f}x")
    print(f"   Overtaking Difficulty: {track.overtaking_difficulty:.2f}")

    # Create race conditions
    conditions = RaceConditions(
        race_laps=race_laps,
        track=track,
        track_temp=26.0,
        safety_car_prob=0.015,  # Adjust based on track (street circuits higher)
        num_competitors=19,
        field_spread=2.0,
    )

    # Create car setup
    car_setup = CarSetup(
        downforce=0.75,  # Adjust per track (Monaco=0.85, Monza=0.4)
        car_performance=our_team.value,
        fuel_start=105.0,
        tire_compound=TireCompound.MEDIUM,
    )

    # Simulation config
    sim_config = SimulationConfig(
        num_runs=5000,
        random_seed=42,
    )

    print(f"\n⚙️  Simulation: {sim_config.num_runs:,} Monte Carlo runs")

    # Run simulation
    simulator = RaceSimulator(conditions, car_setup, sim_config)
    optimizer = StrategyOptimizer(simulator)

    print("\n🔧 Generating strategies...")
    strategies = optimizer.generate_strategies(include_fuel_variants=True)

    # Limit strategies for demo
    strategies = strategies[:30]

    print(f"\n⚡ Evaluating {len(strategies)} strategies...")
    results = optimizer.evaluate_all(strategies, risk_tolerance=0.6)

    print("\n" + "="*70)
    print("🏆 DETAILED RESULTS - TOP 3 STRATEGIES")
    print("="*70)
    for i in range(min(3, len(results))):
        results[i][1].print_summary()

    best_strategy_stats = results[0][1].get_statistics()
    print("\n" + "="*70)
    print("📈 PERFORMANCE SUMMARY")
    print("="*70)
    print(f"Track: {track.full_name}")
    print(f"Best Strategy: {results[0][0].name}")
    print(f"  Win Rate:     {best_strategy_stats['win_probability']*100:.1f}%")
    print(f"  Podium Rate:  {best_strategy_stats['podium_probability']*100:.1f}%")
    print(f"  Avg Position: P{best_strategy_stats['mean_position']:.1f}")
    print(f"  DNF Rate:     {best_strategy_stats['dnf_probability']*100:.2f}%")

    return results

if __name__ == "__main__":
    results = main()