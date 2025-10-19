"""
Racing Strategy Monte Carlo Simulator - F1 Edition
With detailed car engineering and simplified track configuration
"""

import numpy as np
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dataclasses import asdict
from typing import List, Tuple




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

# ============================================================================
# CAR ENGINEERING (unchanged from your version)
# ============================================================================

@dataclass
class CarEngineering:
    """Detailed F1 car engineering parameters"""
    car_mass_kg: float = 798.0
    driver_mass_kg: float = 80.0
    fuel_density_kg_per_liter: float = 0.75
    weight_distribution_front: float = 0.46

    downforce_coefficient: float = 3.5
    drag_coefficient: float = 0.85
    frontal_area_m2: float = 1.5
    aero_balance: float = 0.42
    drs_drag_reduction: float = 0.15
    drs_downforce_reduction: float = 0.08

    front_ride_height_mm: float = 40.0
    rear_ride_height_mm: float = 55.0
    front_wing_angle: float = 20.0
    rear_wing_angle: float = 12.0

    max_power_kw: float = 750.0
    max_ice_power_kw: float = 550.0
    max_ers_power_kw: float = 120.0
    power_curve_peak_rpm: float = 12000.0
    max_rpm: float = 15000.0
    idle_rpm: float = 5000.0
    ers_energy_per_lap_mj: float = 4.0
    ers_recovery_efficiency: float = 0.70

    num_gears: int = 8
    final_drive_ratio: float = 3.2
    transmission_efficiency: float = 0.96
    diff_preload: float = 50.0
    diff_ramp_angle: float = 45.0

    front_spring_rate_n_per_mm: float = 150.0
    rear_spring_rate_n_per_mm: float = 180.0
    front_damper_compression: float = 8000.0
    front_damper_rebound: float = 9000.0
    rear_damper_compression: float = 9000.0
    rear_damper_rebound: float = 10000.0
    front_anti_roll_bar_stiffness: float = 50000.0
    rear_anti_roll_bar_stiffness: float = 45000.0
    front_camber_deg: float = -3.5
    rear_camber_deg: float = -2.0
    front_toe_deg: float = 0.05
    rear_toe_deg: float = 0.10

    tire_diameter_mm: float = 720.0
    tire_width_front_mm: float = 305.0
    tire_width_rear_mm: float = 405.0
    tire_pressure_front_psi: float = 23.0
    tire_pressure_rear_psi: float = 21.0
    tire_compound_base: TireCompound = TireCompound.MEDIUM

    brake_disc_diameter_mm: float = 330.0
    brake_disc_thickness_mm: float = 32.0
    brake_material_thermal_capacity: float = 1200.0
    brake_bias: float = 0.58
    brake_cooling_duct_size: float = 0.75

    radiator_size: float = 0.8
    intercooler_efficiency: float = 0.85
    oil_temperature_target_c: float = 110.0
    water_temperature_target_c: float = 90.0

    fuel_tank_capacity_kg: float = 110.0
    fuel_flow_rate_kg_per_hour: float = 100.0
    fuel_lower_heating_value_mj_per_kg: float = 43.5

    power_unit_mileage_km: float = 1500.0
    power_unit_max_mileage_km: float = 7000.0
    gearbox_mileage_km: float = 800.0
    gearbox_max_mileage_km: float = 2500.0
    reliability_factor: float = 0.95

    overall_performance_offset_s: float = 0.0

    def calculate_total_mass_kg(self, current_fuel_kg: float) -> float:
        return self.car_mass_kg + self.driver_mass_kg + current_fuel_kg

    def get_corner_speed_multiplier(self) -> float:
        baseline_downforce = 3.0
        downforce_advantage = self.downforce_coefficient / baseline_downforce
        baseline_mass = 798.0 + 80.0 + 55.0
        mass_penalty = baseline_mass / self.calculate_total_mass_kg(55.0)
        mechanical_grip = 1.0 + 0.05 * (self.front_spring_rate_n_per_mm / 150.0 - 1.0)
        return (downforce_advantage * 0.7 + mass_penalty * 0.2 + mechanical_grip * 0.1)

    def get_straight_speed_multiplier(self) -> float:
        baseline_power = 670.0
        baseline_drag = 0.85
        power_advantage = (self.max_power_kw / baseline_power)
        drag_advantage = (baseline_drag / self.drag_coefficient)
        return (power_advantage * 0.6 + drag_advantage * 0.4)

    def estimate_lap_time_delta(self, track: 'TrackConfig') -> float:
        delta = self.overall_performance_offset_s
        corner_multiplier = self.get_corner_speed_multiplier()
        corner_fraction = track.num_corners / 20.0
        corner_delta = (1.0 - corner_multiplier) * track.base_lap_time * corner_fraction * 0.6
        straight_multiplier = self.get_straight_speed_multiplier()
        straight_fraction = 1.0 - corner_fraction
        straight_delta = (1.0 - straight_multiplier) * track.base_lap_time * straight_fraction * 0.4
        delta += corner_delta + straight_delta
        # ↓ NEW: cap total delta to ±0.4 s/lap realistic range
        delta = np.clip(delta, -0.8, 0.2)
        return delta

    def get_fuel_consumption_rate(self, engine_mode: EngineMode, track_fuel_factor: float = 1.0) -> float:
        base_consumption = (self.fuel_flow_rate_kg_per_hour / 60.0) * 1.5 / 60.0
        mode_multiplier = engine_mode.value
        consumption = base_consumption * mode_multiplier * track_fuel_factor
        return consumption

    def get_reliability_dnf_probability(self, race_laps: int, base_dnf_prob: float = 0.03) -> float:
        pu_wear = self.power_unit_mileage_km / self.power_unit_max_mileage_km
        gearbox_wear = self.gearbox_mileage_km / self.gearbox_max_mileage_km
        pu_risk = np.exp(3.0 * pu_wear) - 1.0
        gearbox_risk = np.exp(2.5 * gearbox_wear) - 1.0
        component_risk = (pu_risk * 0.6 + gearbox_risk * 0.4) / self.reliability_factor
        race_length_factor = race_laps / 60.0
        total_dnf_prob = base_dnf_prob * (1.3 + component_risk) * race_length_factor
        return min(total_dnf_prob, 0.50)

@dataclass
class CarSetup:
    """F1 Car setup"""
    engineering: CarEngineering = field(default_factory=CarEngineering)
    downforce_level: float = 0.5
    engine_mode: EngineMode = EngineMode.NORMAL
    fuel_start: float = 110.0
    tire_compound: TireCompound = TireCompound.MEDIUM
    initial_tire_wear: float = 0.0

    def __post_init__(self):
        baseline_downforce = 3.5
        baseline_drag = 0.85
        self.engineering.downforce_coefficient = baseline_downforce * (0.7 + 0.6 * self.downforce_level)
        self.engineering.drag_coefficient = baseline_drag * (0.7 + 0.5 * self.downforce_level)
        self.engineering.front_wing_angle = 15.0 + 10.0 * self.downforce_level
        self.engineering.rear_wing_angle = 8.0 + 8.0 * self.downforce_level

    def get_performance_offset(self, track: 'TrackConfig') -> float:
        return self.engineering.estimate_lap_time_delta(track)

# ============================================================================
# TRACK CONFIGURATION - SIMPLIFIED FOR NEW JSON FORMAT
# ============================================================================

@dataclass
class TrackConfig:
    """F1 Track configuration - now using track_configs.updated.json"""
    name: str
    lap_length_km: float
    base_lap_time: float  # seconds
    num_corners: int
    drs_zones: int = 2
    pit_loss_time: float = 22.0
    pit_lane_delta: float = 18.0
    pit_service_time: float = 2.0
    tire_stress: float = 1.0
    fuel_usage: float = 1.0
    overtaking_difficulty: float = 0.5
    track_id: str = ""
    full_name: str = ""
    track_type: str = ""
    direction: str = ""
    avg_speed_kmh: float = 200.0
    longest_straight_m: float = 800.0
    slowest_corner_kmh: float = 80.0

    @classmethod
    def from_json(cls, track_data: Dict) -> 'TrackConfig':
        """
        Create TrackConfig from track_configs.updated.json
        This new format already has avg_lap_time_s calculated!
        """
        # Use the pre-calculated avg_lap_time_s from the JSON
        base_lap_time = track_data.get('avg_lap_time_s')

        if base_lap_time is None:
            # Fallback: try avg_lap_time_ms
            if track_data.get('avg_lap_time_ms'):
                base_lap_time = track_data['avg_lap_time_ms'] / 1000.0
            else:
                # Last resort: estimate
                avg_speed_kmh = 190.0
                base_lap_time = (track_data['length_km'] / avg_speed_kmh) * 3600.0
                print(f"  ⚠️  No lap time for {track_data['name']}, estimated: {base_lap_time:.1f}s")

        # Fuel usage: convert liters to kg, then normalize
        fuel_liters_per_lap = track_data.get('fuel_usage_per_lap_l', 2.5)
        fuel_kg_per_lap = fuel_liters_per_lap * 0.75  # F1 fuel density ~0.75 kg/L
        fuel_usage_normalized = fuel_kg_per_lap / 1.875  # Baseline: 2.5L * 0.75 = 1.875 kg

        # Pit stop time
        pit_stop_time = track_data.get('pit_stop_time_s', 22.0)
        pit_service_time = 2.3  # F1 standard stationary time
        pit_lane_delta = max(pit_stop_time - pit_service_time, 10.0)

        # Calculate average speed from lap time and length
        if base_lap_time > 0:
            avg_speed_kmh = (track_data['length_km'] / base_lap_time) * 3600.0
        else:
            avg_speed_kmh = 200.0

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
            avg_speed_kmh=avg_speed_kmh,
        )

# ============================================================================
# TRACK DATABASE - UPDATED FOR NEW FILE
# ============================================================================

class TrackDatabase:
    """Loads and manages tracks from track_configs.updated.json"""

    def __init__(self, json_path: str = "./data/track_configs.updated.json"):
        self.json_path = Path(json_path)
        self.tracks: Dict[str, Dict] = {}
        self.load_tracks()

    def load_tracks(self):
        """Load all tracks from JSON file"""
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"❌ Track configuration file not found: {self.json_path}\n"
                f"   Make sure 'track_configs.updated.json' is in the same directory as this script."
            )

        with open(self.json_path, 'r', encoding='utf-8') as f:
            tracks_list = json.load(f)

        # Convert list to dictionary keyed by track ID
        self.tracks = {track['id']: track for track in tracks_list}

        print(f"📁 Loaded {len(self.tracks)} tracks from {self.json_path.name}")

        # Show sample of available tracks
        sample_tracks = list(self.tracks.keys())[:5]
        print(f"   Sample tracks: {', '.join(sample_tracks)}...")

    def get_track(self, track_id: str) -> TrackConfig:
        """Get a TrackConfig for a specific track"""
        if track_id not in self.tracks:
            available = ', '.join(sorted(self.tracks.keys())[:10])
            raise ValueError(
                f"❌ Track '{track_id}' not found!\n"
                f"   Available tracks: {available}...\n"
                f"   Use track_db.list_tracks() to see all {len(self.tracks)} tracks."
            )

        track_data = self.tracks[track_id]
        return TrackConfig.from_json(track_data)

    def list_tracks(self) -> List[str]:
        """Return list of all available track IDs"""
        return sorted(self.tracks.keys())

    def print_tracks(self, detailed: bool = False):
        """Print formatted list of all tracks"""
        print("\n" + "="*90)
        print("AVAILABLE TRACKS")
        print("="*90)

        if detailed:
            print(f"{'ID':<20} {'Name':<30} {'Length':<10} {'Turns':<6} {'Lap Time':<10} {'Type':<12}")
            print("-"*90)
            for track_id in sorted(self.tracks.keys()):
                track_data = self.tracks[track_id]
                lap_time_s = track_data.get('avg_lap_time_s', 0)
                lap_time_str = f"{lap_time_s:.2f}s" if lap_time_s else "N/A"
                print(f"{track_id:<20} {track_data['name']:<30} "
                      f"{track_data['length_km']:>6.2f} km  {track_data['num_turns']:>4}   "
                      f"{lap_time_str:<10} {track_data.get('type', 'N/A'):<12}")
        else:
            # Simple list
            tracks_sorted = sorted(self.tracks.keys())
            for i in range(0, len(tracks_sorted), 4):
                row = tracks_sorted[i:i+4]
                print("  " + "   ".join(f"{t:<20}" for t in row))

        print("="*90)
        print(f"Total: {len(self.tracks)} tracks")

# ============================================================================
# RACE CONDITIONS, SIMULATION CONFIG, STRATEGY (unchanged)
# ============================================================================

@dataclass
class RaceConditions:
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

    lap_time_noise_std = 0.35  # was 0.15
    wear_rate_noise_std = 0.25
    fuel_burn_noise_std = 0.08
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
            raise ValueError(f"Starting fuel too low: {self.starting_fuel}kg")

    def estimate_fuel_needed(self, race_laps: int, burn_rate: float = 1.4) -> float:
        return race_laps * burn_rate

    def is_fuel_feasible(self, race_laps: int, burn_rate: float = 1.4) -> bool:
        needed = self.estimate_fuel_needed(race_laps, burn_rate)
        return self.starting_fuel >= needed * 0.95

# ============================================================================
# CAR PRESETS
# ============================================================================

def create_custom_car(
    name: str = "Custom F1 Car",
    mass_kg: float = 798.0,
    driver_mass_kg: float = 80.0,
    max_power_kw: float = 750.0,
    downforce_coeff: float = 3.5,
    drag_coeff: float = 0.85,
    reliability: float = 0.95,
    pu_mileage_km: float = 1500.0,
    **kwargs
) -> CarEngineering:
    car = CarEngineering(
        car_mass_kg=mass_kg,
        driver_mass_kg=driver_mass_kg,
        max_power_kw=max_power_kw,
        downforce_coefficient=downforce_coeff,
        drag_coefficient=drag_coeff,
        reliability_factor=reliability,
        power_unit_mileage_km=pu_mileage_km,
    )
    for key, value in kwargs.items():
        if hasattr(car, key):
            setattr(car, key, value)
    return car

F1_CAR_PRESETS = {
    "red_bull_rb20": create_custom_car(
        name="Red Bull RB20",
        mass_kg=796.0,
        max_power_kw=780.0,
        downforce_coeff=3.8,
        drag_coeff=0.82,
        reliability=0.97,
    ),
    "ferrari_sf24": create_custom_car(
        name="Ferrari SF-24",
        mass_kg=798.0,
        max_power_kw=760.0,
        downforce_coeff=3.55,
        drag_coeff=0.85,
        reliability=0.95,
    ),
    "mercedes_w15": create_custom_car(
        name="Mercedes W15",
        mass_kg=799.0,
        max_power_kw=765.0,
        downforce_coeff=3.5,
        drag_coeff=0.86,
        reliability=0.96,
    ),
    "williams_fw46": create_custom_car(
        name="Williams FW46",
        mass_kg=802.0,
        max_power_kw=740.0,
        downforce_coeff=3.2,
        drag_coeff=0.88,
        reliability=0.92,
    ),
}

# ============================================================================
# COMPETITOR FIELD (simplified - no historical data dependency)
# ============================================================================

class CompetitorField:
    def __init__(self, race_conditions: RaceConditions, sim_config: SimulationConfig, rng: np.random.RandomState):
        self.rc = race_conditions
        self.cfg = sim_config
        self.rng = rng
        self.competitor_base_pace = self._generate_realistic_field()
        self.competitor_strategies = self._assign_competitor_strategies()

    def _generate_realistic_field(self) -> np.ndarray:
        n = self.rc.num_competitors
        top_teams = 6
        midfield = min(8, n - top_teams)
        backmarkers = n - top_teams - midfield
        pace = np.zeros(n)
        pace[:top_teams] = self.rng.uniform(-0.3, 0.4, top_teams)
        pace[top_teams:top_teams + midfield] = self.rng.uniform(0.4, 1.2, midfield)
        if backmarkers > 0:
            pace[top_teams + midfield:] = self.rng.uniform(1.2, 2.5, backmarkers)
        pace += self.rng.normal(0, 0.1, n)
        return pace

    def _assign_competitor_strategies(self) -> List[Strategy]:
        strategies = []
        one_stop_options = [
            ([TireCompound.MEDIUM, TireCompound.HARD], "MH"),
            ([TireCompound.SOFT, TireCompound.HARD], "SH"),
        ]
        two_stop_options = [
            ([TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.MEDIUM], "SMM"),
        ]
        for i in range(self.rc.num_competitors):
            start_fuel = float(self.rng.uniform(100.0, 110.0))
            if self.rng.random() < 0.65:
                pit_lap = self.rng.randint(
                    max(self.rc.race_laps // 3, 15),
                    min(2 * self.rc.race_laps // 3, self.rc.race_laps - 10)
                )
                compounds, code = one_stop_options[self.rng.randint(0, len(one_stop_options))]
                strategies.append(Strategy(
                    name=f"Comp{i}_1stop_{code}",
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
                compounds, code = two_stop_options[0]
                strategies.append(Strategy(
                    name=f"Comp{i}_2stop_{code}",
                    pit_laps=[pit1, pit2],
                    tire_compounds=compounds,
                    starting_fuel=start_fuel
                ))
        return strategies

# ============================================================================
# RACE SIMULATOR (same as before)
# ============================================================================

# ============================================================================
# RACE SIMULATOR - FIXED VERSION
# ============================================================================

class RaceSimulator:
    def __init__(self, race_conditions: RaceConditions, car_setup: CarSetup, sim_config: SimulationConfig):
        self.rc = race_conditions
        self.setup = car_setup
        self.cfg = sim_config
        self.rng = np.random.RandomState(sim_config.random_seed)
        self.N_laps = race_conditions.race_laps
        self.N_runs = sim_config.num_runs
        self.competitor_field = CompetitorField(race_conditions, sim_config, self.rng)
        self.our_car_performance_offset = self.setup.get_performance_offset(race_conditions.track)

        print(f"\n🏎️  Our Car Engineering:")
        print(
            f"   Mass: {self.setup.engineering.car_mass_kg:.1f} kg (+ {self.setup.engineering.driver_mass_kg:.1f} kg driver)")
        print(
            f"   Power: {self.setup.engineering.max_power_kw:.0f} kW ({self.setup.engineering.max_power_kw * 1.34:.0f} HP)")
        print(f"   Downforce CL: {self.setup.engineering.downforce_coefficient:.2f}")
        print(f"   Drag CD: {self.setup.engineering.drag_coefficient:.2f}")
        print(
            f"   L/D Ratio: {self.setup.engineering.downforce_coefficient / self.setup.engineering.drag_coefficient:.2f}")
        print(f"   Performance offset: {self.our_car_performance_offset:+.3f}s per lap")
        print(f"\n👥 Competitor Field:")
        print(f"   {self.rc.num_competitors} competitors")
        print(f"   Pace range: {self.competitor_field.competitor_base_pace.min():.2f}s to "
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
        lap_noise = self.rng.normal(0, self.cfg.lap_time_noise_std * 1.3, shape)
        safety_cars = self.rng.random(shape) < self.rc.safety_car_prob

        competitor_times_all_runs = self._simulate_competitor_field_stochastic()

        for run_idx in range(self.N_runs):
            result = self._simulate_single_run(strategy, run_idx, wear_multipliers[run_idx],
                                               fuel_multipliers[run_idx], lap_noise[run_idx], safety_cars[run_idx])
            lap_times[run_idx] = result['lap_times']
            tire_wear[run_idx] = result['tire_wear']
            fuel_level[run_idx] = result['fuel']
            total_times[run_idx] = result['total_time']
            dnf_flags[run_idx] = result['dnf']

        positions = self._compute_positions_stochastic(total_times, dnf_flags, competitor_times_all_runs)

        return SimulationResults(strategy, self.N_runs, lap_times, tire_wear, fuel_level,
                                 total_times, positions, dnf_flags, self.rc, self.cfg)

    def _simulate_competitor_field_stochastic(self) -> np.ndarray:
        """
        FIXED: Properly simulate competitor field with correct DNF logic and variance
        """
        competitor_times = np.zeros((self.N_runs, self.rc.num_competitors))

        for comp_idx in range(self.rc.num_competitors):
            base_pace = self.competitor_field.competitor_base_pace[comp_idx]
            strategy = self.competitor_field.competitor_strategies[comp_idx]

            # Competitor uses random fuel load
            competitor_fuel = self.rng.uniform(105.0, 109.0)

            # Calculate expected race time
            expected_time = self._calculate_expected_race_time(base_pace, strategy, competitor_fuel)

            # DNF probability for this competitor (based on their pace/reliability)
            # Better teams (negative base_pace) have lower DNF rates
            base_dnf_prob = 0.03
            pace_dnf_modifier = max(0, base_pace / 2.0)  # Slower cars more likely to DNF
            comp_dnf_prob = base_dnf_prob * (1.0 + pace_dnf_modifier)

            for run_idx in range(self.N_runs):
                # FIX: Check DNF per competitor per run (not global!)
                if self.rng.random() < comp_dnf_prob:
                    competitor_times[run_idx, comp_idx] = 1e9
                    continue

                # Variance components (same as before)
                lap_variance_total = self.cfg.lap_time_noise_std * np.sqrt(self.rc.race_laps)
                pit_variance = 0.5 * len(strategy.pit_laps)
                random_events = self.rng.normal(0, 2.0)

                # FIX: Increase total variance to allow more competitive spread
                total_std = np.sqrt(lap_variance_total ** 2 + pit_variance ** 2 + 16.0)  # ← Changed from 4.0

                run_variance = self.rng.normal(0, total_std)
                race_time = expected_time + run_variance + random_events

                # Outliers
                if self.rng.random() < 0.08:  # ← Increased from 0.05 for more chaos
                    race_time += self.rng.normal(0, total_std * 1.5)

                competitor_times[run_idx, comp_idx] = max(race_time, expected_time * 0.88)  # ← Loosened from 0.92

        return competitor_times

    def _calculate_expected_race_time(self, base_pace: float, strategy: Strategy, starting_fuel: float = None) -> float:
        """
        Calculate expected race time - same physics for everyone
        """
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
                # Base lap time WITH competitor's pace offset
                lap_time = self.rc.track.base_lap_time + base_pace

                # Tire degradation
                tire_wear = (lap_in_stint / max(stint_length, 1)) * base_wear_rate * stint_length
                tire_deg = self.cfg.k_wear_lap_time * (tire_wear ** 1.5)

                # Fuel effect
                fuel_effect = self.cfg.k_fuel_lap_time * fuel

                # Compound offset
                lap_time += compound_offset + tire_deg + fuel_effect

                total_time += lap_time
                current_lap += 1

                # Burn fuel
                burn_rate = self.cfg.base_fuel_burn_rate * self.rc.track.fuel_usage
                fuel = max(fuel - burn_rate, 0.0)

            # Pit stop
            if stint_idx < len(strategy.pit_laps):
                total_time += self.rc.track.pit_loss_time

        return total_time

    def _compute_positions_stochastic(self, our_times: np.ndarray, our_dnf_flags: np.ndarray,
                                      competitor_times: np.ndarray) -> np.ndarray:
        """Compute finishing positions"""
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
        """Simulate single race for our car"""
        W = self.setup.initial_tire_wear
        fuel = strategy.starting_fuel
        total_time = 0.0

        # DNF check for our car (using engineering reliability model)
        dnf_prob = self.setup.engineering.get_reliability_dnf_probability(self.N_laps)
        dnf = self.rng.random() < dnf_prob

        if dnf:
            return {'lap_times': np.zeros(self.N_laps), 'tire_wear': np.zeros(self.N_laps),
                    'fuel': np.zeros(self.N_laps), 'total_time': 1e9, 'dnf': True}

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

            total_time += lap_time
            wear_rate = self._compute_wear_rate(current_compound) * wear_mult
            W = min(W + wear_rate, 1.0)
            burn_rate = self.setup.engineering.get_fuel_consumption_rate(current_engine_mode,
                                                                         self.rc.track.fuel_usage) * fuel_mult
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
        """Compute single lap time for our car"""
        tau_0 = self.rc.track.base_lap_time + self.our_car_performance_offset
        tau_wear = self.cfg.k_wear_lap_time * (wear ** 1.5)
        tau_fuel = self.cfg.k_fuel_lap_time * fuel
        compound_offset, _, _ = self.cfg.tire_properties[compound]
        engine_factor = engine_mode.value
        tau = (tau_0 + tau_wear + tau_fuel + compound_offset) / engine_factor
        tau += noise
        return max(tau, tau_0 * 0.90)

    def _compute_wear_rate(self, compound: TireCompound) -> float:
        """Tire wear rate"""
        _, base_wear, _ = self.cfg.tire_properties[compound]
        wear = base_wear * self.rc.track.tire_stress
        temp_factor = 1.0 + 0.015 * (self.rc.track_temp - 25)
        return wear * temp_factor

# ============================================================================
# RESULTS & OPTIMIZER (unchanged from before)
# ============================================================================

@dataclass
class SimulationResults:
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
        print(f"{'='*60}")
        print(f"\n⏱️  Race Time:")
        print(f"  Mean:   {stats['mean_time']:.2f}s ({stats['mean_time']/60:.1f} min)")
        print(f"  Median: {stats['median_time']:.2f}s")
        print(f"\n🏁 Finishing Position:")
        print(f"  Mean:   P{stats['mean_position']:.1f}")
        print(f"  Median: P{stats['median_position']:.0f}")
        print(f"\n📊 Probabilities:")
        print(f"  Win (P1):  {stats['win_probability']*100:5.1f}%")
        print(f"  Podium:    {stats['podium_probability']*100:5.1f}%")
        print(f"  Top 5:     {stats['top5_probability']*100:5.1f}%")
        print(f"  DNF:       {stats['dnf_probability']*100:5.2f}%")

class StrategyOptimizer:
    def __init__(self, simulator: RaceSimulator):
        self.sim = simulator

    def generate_strategies(self) -> List[Strategy]:
        strategies = []
        N = self.sim.N_laps
        compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
        fuel_options = [105.0, 107.0]
        for pit_lap in [N // 3, N // 2, 2 * N // 3]:
            for start_compound in compounds:
                for end_compound in compounds:
                    if start_compound != end_compound:
                        for fuel in fuel_options:
                            strategies.append(Strategy(
                                name=f"1stop_L{pit_lap}_{start_compound.value[0].upper()}{end_compound.value[0].upper()}",
                                pit_laps=[pit_lap],
                                tire_compounds=[start_compound, end_compound],
                                starting_fuel=fuel
                            ))
        return strategies[:20]

    def evaluate_all(self, strategies: List[Strategy], risk_tolerance: float = 0.5):
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
        print("🏆 TOP 5 STRATEGIES")
        print("="*80)
        for i, (strat, res, util) in enumerate(results[:5]):
            stats = res.get_statistics()
            print(f"{i+1}. {strat.name:40s} | Win: {stats['win_probability']*100:5.1f}% | "
                  f"Pod: {stats['podium_probability']*100:5.1f}% | Avg: P{stats['mean_position']:.1f}")
        return results



def to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):  # e.g., np.float64
        return obj.item()
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_serializable(x) for x in obj]
    else:
        return obj

def serialize_strategy(strategy):
    d = asdict(strategy)
    # Convert enums to strings if needed
    d['tire_compounds'] = [str(tc) for tc in d['tire_compounds']]
    d['engine_modes'] = [str(em) for em in d['engine_modes']]
    return d

def serialize_sim_results(sim_result: SimulationResults):
    stats = sim_result.get_statistics()  # get all the calculated stats

    def to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):  # e.g., np.float64
            return obj.item()
        elif hasattr(obj, "__dict__"):
            # For nested objects like RaceConditions or SimulationConfig
            return {k: to_serializable(v) for k, v in vars(obj).items()}
        elif isinstance(obj, dict):
            return {k: to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [to_serializable(v) for v in obj]
        else:
            return obj

    clean_stats = to_serializable(stats)
    return clean_stats

def serialize_results(results: list[tuple[Strategy, SimulationResults, float]]):
    serialized = []
    for strategy, sim_result, score in results:
        serialized.append([
            serialize_strategy(strategy),  # as before
            serialize_sim_results(sim_result),
            score
        ])
    return serialized


# ============================================================================
# MAIN - UPDATED FOR NEW TRACK DATABASE
# ============================================================================

def main():
    print("="*80)
    print(" F1 STRATEGY SIMULATOR - ENGINEERING MODE")
    print("="*80)

    # Load track database
    track_db = TrackDatabase("./data/track_configs.updated.json")

    # Optionally show all tracks
    # track_db.print_tracks()

    # ========================================================================
    # CONFIGURE YOUR RACE HERE
    # ========================================================================

    # SELECT TRACK (use any ID from track_configs.updated.json)
    track_id = "monaco"  # ← CHANGE THIS
    race_laps = 78

    # SELECT CAR
    # Option 1: Use preset
    my_car = F1_CAR_PRESETS["red_bull_rb20"]

    # Option 2: Create custom car
    # my_car = create_custom_car(
    #     name="My Custom Car",
    #     mass_kg=796.0,
    #     max_power_kw=780.0,
    #     downforce_coeff=3.8,
    #     drag_coeff=0.82,
    #     reliability=0.96,
    #     pu_mileage_km=1000.0,
    # )

    # ========================================================================

    print(f"\n🏁 Loading race configuration...")
    print(f"   Track: {track_id}")
    print(f"   Laps: {race_laps}")

    # Load track
    track = track_db.get_track(track_id)

    print(f"\n📍 Track Details:")
    print(f"   Name: {track.full_name}")
    print(f"   Type: {track.track_type}")
    print(f"   Length: {track.lap_length_km:.2f} km")
    print(f"   Turns: {track.num_corners}")
    print(f"   Base Lap Time: {track.base_lap_time:.2f}s (≈ {track.base_lap_time/60:.2f} min)")
    print(f"   Avg Speed: {track.avg_speed_kmh:.1f} km/h")
    print(f"   Pit Loss: {track.pit_loss_time:.1f}s")
    print(f"   Tire Stress: {track.tire_stress:.2f}x")
    print(f"   Fuel Usage: {track.fuel_usage:.2f}x")
    print(f"   Overtaking: {track.overtaking_difficulty:.2f} (0=easy, 1=hard)")

    # Create race conditions
    conditions = RaceConditions(
        race_laps=race_laps,
        track=track,
        track_temp=26.0,
        safety_car_prob=0.020 if track.track_type == "STREET" else 0.015,
        num_competitors=19,
    )

    # Create car setup
    downforce_level = 0.85 if track.track_type == "STREET" else 0.5
    car_setup = CarSetup(
        engineering=my_car,
        downforce_level=downforce_level,
        fuel_start=105.0,
    )

    sim_config = SimulationConfig(num_runs=3000, random_seed=42)

    print(f"\n⚙️  Simulation: {sim_config.num_runs:,} Monte Carlo runs")

    # Run simulation
    simulator = RaceSimulator(conditions, car_setup, sim_config)
    optimizer = StrategyOptimizer(simulator)

    print(f"\n🔧 Generating strategies...")
    strategies = optimizer.generate_strategies()

    print(f"\n⚡ Evaluating {len(strategies)} strategies...")
    results = optimizer.evaluate_all(strategies, risk_tolerance=0.6)

    print("\n" + "="*80)
    print("🏆 BEST STRATEGY - DETAILED REPORT")
    print("="*80)
    results[0][1].print_summary()

    print("\n" + "="*80)
    print("📈 SIMULATION SUMMARY")
    print("="*80)
    best_stats = results[0][1].get_statistics()
    print(f"Track: {track.full_name}")
    print(f"Car: Ferrari SF-24")
    print(f"Best Strategy: {results[0][0].name}")
    print(f"Expected Result: P{best_stats['mean_position']:.1f} (Win: {best_stats['win_probability']*100:.1f}%)")

    print("Type of result:", type(results))
    print("Example content:", str(results)[:500])

    clean_results = serialize_results(results)
    return JSONResponse(content=clean_results)


if __name__ == "__main__":
    results = main()