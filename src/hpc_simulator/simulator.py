"""
HPC Simulator for F1 race scenarios
Simulates thousands of race scenarios considering tire strategy, fuel management, and aerodynamics
"""
import numpy as np
from typing import List, Tuple, Dict
from ..models.race_models import (
    TireCompound, WeatherCondition, RaceConditions, 
    CarState, SimulationScenario, PitStopStrategy
)
from concurrent.futures import ProcessPoolExecutor, as_completed
import time


class F1RaceSimulator:
    """High-performance race simulator"""
    
    # Tire degradation rates (seconds per lap) - compound dependent
    TIRE_DEGRADATION = {
        "soft": 0.08,
        "medium": 0.05,
        "hard": 0.03,
        "intermediate": 0.06,
        "wet": 0.07,
    }
    
    # Base lap times for each compound (relative to medium = 0)
    TIRE_LAP_TIME_BASE = {
        "soft": -0.5,
        "medium": 0.0,
        "hard": 0.3,
        "intermediate": 2.0,
        "wet": 4.0,
    }
    
    # Pit stop time loss
    PIT_STOP_TIME = 25.0  # seconds
    
    # Fuel effect (seconds per kg)
    FUEL_EFFECT = 0.03
    
    def __init__(self):
        self.rng = np.random.default_rng()
    
    def calculate_lap_time(
        self, 
        base_lap_time: float,
        tire_compound: TireCompound,
        tire_age: int,
        fuel_load: float,
        weather: WeatherCondition
    ) -> float:
        """Calculate lap time based on various factors"""
        lap_time = base_lap_time
        
        # Convert to string for dict lookup
        if isinstance(tire_compound, TireCompound):
            compound_str = tire_compound.value
        elif isinstance(tire_compound, str):
            compound_str = tire_compound
        else:
            compound_str = str(tire_compound)
            
        if isinstance(weather, WeatherCondition):
            weather_str = weather.value
        elif isinstance(weather, str):
            weather_str = weather
        else:
            weather_str = str(weather)
        
        # Tire compound base difference
        lap_time += self.TIRE_LAP_TIME_BASE.get(compound_str, 0.0)
        
        # Tire degradation
        lap_time += tire_age * self.TIRE_DEGRADATION.get(compound_str, 0.05)
        
        # Fuel weight effect
        lap_time += fuel_load * self.FUEL_EFFECT
        
        # Weather effects
        if weather_str == "light_rain":
            if compound_str in ["soft", "medium", "hard"]:
                lap_time += 5.0  # Slicks in rain are much slower
            else:
                lap_time += 0.5
        elif weather_str == "heavy_rain":
            if compound_str in ["soft", "medium", "hard"]:
                lap_time += 15.0
            elif compound_str == "intermediate":
                lap_time += 3.0
        
        # Add some randomness (traffic, driver performance)
        lap_time += self.rng.normal(0, 0.2)
        
        return lap_time
    
    def simulate_race_scenario(
        self,
        race_conditions: RaceConditions,
        car_state: CarState,
        pit_strategy: List[Tuple[int, TireCompound]]
    ) -> Tuple[float, int, float]:
        """
        Simulate a single race scenario
        Returns: (total_race_time, final_position, risk_score)
        """
        current_lap = race_conditions.lap
        total_laps = race_conditions.total_laps
        
        tire_compound = car_state.tire_compound
        tire_age = car_state.tire_age
        fuel_load = car_state.fuel_load
        base_lap_time = car_state.lap_time
        
        total_time = 0.0
        pit_stops_taken = 0
        fuel_per_lap = fuel_load / (total_laps - current_lap + 1)
        
        # Sort pit strategy by lap
        pit_strategy_sorted = sorted(pit_strategy, key=lambda x: x[0])
        pit_index = 0
        
        for lap in range(current_lap, total_laps + 1):
            # Check if we should pit this lap
            if pit_index < len(pit_strategy_sorted) and pit_strategy_sorted[pit_index][0] == lap:
                total_time += self.PIT_STOP_TIME
                tire_compound = pit_strategy_sorted[pit_index][1]
                tire_age = 0
                pit_stops_taken += 1
                pit_index += 1
            
            # Calculate lap time
            lap_time = self.calculate_lap_time(
                base_lap_time,
                tire_compound,
                tire_age,
                fuel_load,
                race_conditions.weather
            )
            
            total_time += lap_time
            tire_age += 1
            fuel_load -= fuel_per_lap
            
            # Ensure fuel doesn't go negative
            if fuel_load < 0:
                fuel_load = 0
        
        # Calculate risk score
        risk_score = 0.0
        
        # Fuel risk
        if fuel_load < 2.0:
            risk_score += 0.3
        
        # Tire age risk (very old tires)
        if tire_age > 25:
            risk_score += 0.3
        
        # Not enough pit stops risk (need at least 1 in most races)
        if pit_stops_taken < 1 and total_laps > 20:
            risk_score += 0.4
        
        risk_score = min(risk_score, 1.0)
        
        # Estimate position (simplified - based on total time relative to baseline)
        # This is a simplified model; in reality, you'd track all cars
        position_delta = int((total_time - (base_lap_time * (total_laps - current_lap + 1))) / 20)
        estimated_position = max(1, min(20, car_state.position + position_delta))
        
        return total_time, estimated_position, risk_score
    
    def generate_pit_strategies(
        self,
        race_conditions: RaceConditions,
        num_strategies: int = 1000
    ) -> List[List[Tuple[int, TireCompound]]]:
        """Generate diverse pit stop strategies"""
        strategies = []
        current_lap = race_conditions.lap
        total_laps = race_conditions.total_laps
        remaining_laps = total_laps - current_lap
        
        # Weather-appropriate compounds
        weather_str = race_conditions.weather.value if isinstance(race_conditions.weather, WeatherCondition) else race_conditions.weather
        if weather_str == "dry":
            compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
        elif weather_str == "light_rain":
            compounds = [TireCompound.INTERMEDIATE, TireCompound.MEDIUM]
        else:
            compounds = [TireCompound.WET, TireCompound.INTERMEDIATE]
        
        for _ in range(num_strategies):
            # Decide number of pit stops (0-2 typically)
            num_stops = self.rng.choice([0, 1, 2], p=[0.1, 0.7, 0.2])
            
            if num_stops == 0:
                strategies.append([])
            else:
                pit_laps = sorted(
                    self.rng.choice(
                        range(current_lap + 3, total_laps - 2),
                        size=num_stops,
                        replace=False
                    )
                )
                
                strategy = [
                    (int(lap), compounds[self.rng.integers(0, len(compounds))])
                    for lap in pit_laps
                ]
                strategies.append(strategy)
        
        return strategies
    
    def simulate_parallel(
        self,
        race_conditions: RaceConditions,
        car_state: CarState,
        num_scenarios: int = 1000
    ) -> List[SimulationScenario]:
        """Run parallel simulations and return ranked scenarios"""
        start_time = time.time()
        
        # Generate pit strategies
        strategies = self.generate_pit_strategies(race_conditions, num_scenarios)
        
        # Run simulations
        results = []
        
        for idx, strategy in enumerate(strategies):
            total_time, position, risk = self.simulate_race_scenario(
                race_conditions, car_state, strategy
            )
            
            # Convert strategy to PitStopStrategy objects
            pit_stops = []
            for lap, compound in strategy:
                pit_stops.append(PitStopStrategy(
                    lap=lap,
                    tire_compound=compound,
                    expected_position_after_stop=position,
                    expected_time_loss=self.PIT_STOP_TIME,
                    confidence=0.85 - risk * 0.2
                ))
            
            scenario = SimulationScenario(
                scenario_id=f"scenario_{idx}",
                pit_stops=pit_stops,
                estimated_finish_position=position,
                estimated_race_time=total_time,
                fuel_critical=risk > 0.5,
                risk_score=risk
            )
            results.append(scenario)
        
        # Sort by position (lower is better), then by race time
        results.sort(key=lambda x: (x.estimated_finish_position, x.estimated_race_time))
        
        computation_time = (time.time() - start_time) * 1000  # ms
        print(f"Simulated {num_scenarios} scenarios in {computation_time:.2f}ms")
        
        return results
