"""
HPC Simulation Engine for F1 Race Strategy
Simulates tire strategy, fuel management, and aerodynamic scenarios
"""
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import time


@dataclass
class TireCompound:
    """Represents a tire compound with its characteristics"""
    name: str
    grip_level: float  # 0-1 scale
    degradation_rate: float  # per lap
    optimal_temp_range: Tuple[float, float]  # degrees Celsius
    

@dataclass
class SimulationConfig:
    """Configuration for race simulation"""
    track_length: float  # km
    total_laps: int
    fuel_capacity: float  # kg
    fuel_consumption_rate: float  # kg per lap
    drag_coefficient: float
    downforce_level: float


class HPCSimulationEngine:
    """
    High-Performance Computing simulation engine for F1 race scenarios.
    Runs parallel simulations for different strategies.
    """
    
    TIRE_COMPOUNDS = {
        'soft': TireCompound('Soft', 1.0, 0.08, (90, 110)),
        'medium': TireCompound('Medium', 0.95, 0.05, (85, 105)),
        'hard': TireCompound('Hard', 0.90, 0.03, (80, 100)),
    }
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.simulation_cache = {}
        
    def simulate_tire_strategy(self, strategy: List[Tuple[str, int]]) -> Dict:
        """
        Simulate a tire strategy for the race.
        
        Args:
            strategy: List of (compound, laps) tuples
            
        Returns:
            Dictionary with simulation results
        """
        total_time = 0.0
        lap_times = []
        tire_states = []
        current_lap = 0
        fuel_remaining = self.config.fuel_capacity
        
        for compound_name, stint_laps in strategy:
            compound = self.TIRE_COMPOUNDS[compound_name]
            tire_age = 0
            
            for lap in range(stint_laps):
                # Base lap time (seconds)
                base_time = 90.0  # ~1:30 for average F1 circuit
                
                # Tire degradation effect
                tire_deg_effect = tire_age * compound.degradation_rate * 0.5
                
                # Grip level effect
                grip_effect = (1.0 - compound.grip_level) * 2.0
                
                # Fuel weight effect (lighter = faster)
                fuel_effect = (fuel_remaining / self.config.fuel_capacity) * 1.5
                
                # Aerodynamic effect
                aero_effect = (self.config.drag_coefficient - 0.3) * 2.0 - \
                             (self.config.downforce_level - 0.5) * 1.0
                
                # Calculate lap time
                lap_time = base_time + tire_deg_effect + grip_effect + fuel_effect + aero_effect
                
                # Add some realistic variance
                lap_time += np.random.normal(0, 0.3)
                
                lap_times.append(lap_time)
                tire_states.append({
                    'lap': current_lap + 1,
                    'compound': compound_name,
                    'age': tire_age,
                    'grip': max(0, compound.grip_level - tire_age * compound.degradation_rate)
                })
                
                total_time += lap_time
                tire_age += 1
                current_lap += 1
                fuel_remaining -= self.config.fuel_consumption_rate
                
                if current_lap >= self.config.total_laps:
                    break
                    
            if current_lap >= self.config.total_laps:
                break
                
        # Add pit stop time (assuming 2.5 seconds per stop)
        num_stops = len(strategy) - 1
        total_time += num_stops * 2.5
        
        return {
            'strategy': strategy,
            'total_time': total_time,
            'average_lap_time': np.mean(lap_times),
            'lap_times': lap_times,
            'tire_states': tire_states,
            'num_pit_stops': num_stops,
            'fuel_remaining': fuel_remaining
        }
    
    def simulate_fuel_strategy(self, fuel_save_laps: List[int]) -> Dict:
        """
        Simulate fuel-saving strategy for specific laps.
        
        Args:
            fuel_save_laps: List of lap numbers to conserve fuel
            
        Returns:
            Fuel consumption analysis
        """
        fuel_remaining = self.config.fuel_capacity
        fuel_savings = 0.0
        lap_fuel_data = []
        
        for lap in range(1, self.config.total_laps + 1):
            if lap in fuel_save_laps:
                # Fuel saving mode (10% reduction)
                consumption = self.config.fuel_consumption_rate * 0.9
                fuel_savings += self.config.fuel_consumption_rate * 0.1
                mode = 'saving'
            else:
                consumption = self.config.fuel_consumption_rate
                mode = 'normal'
                
            fuel_remaining -= consumption
            lap_fuel_data.append({
                'lap': lap,
                'fuel_remaining': fuel_remaining,
                'consumption': consumption,
                'mode': mode
            })
            
        return {
            'fuel_savings': fuel_savings,
            'final_fuel': fuel_remaining,
            'fuel_safe': fuel_remaining > 0,
            'lap_data': lap_fuel_data
        }
    
    def simulate_aero_setup(self, drag_coef: float, downforce: float) -> Dict:
        """
        Simulate different aerodynamic setups.
        
        Args:
            drag_coef: Drag coefficient (0.25 - 0.35)
            downforce: Downforce level (0.4 - 0.6)
            
        Returns:
            Performance analysis for the aero setup
        """
        # High downforce = better cornering, worse top speed
        # Low drag = better top speed, worse cornering
        
        top_speed_gain = (0.35 - drag_coef) * 20  # km/h
        corner_speed_gain = (downforce - 0.4) * 15  # km/h
        
        # Estimate lap time impact
        # Assuming 60% corners, 40% straights
        straight_time_saved = (top_speed_gain / 300) * 30 * 0.4  # seconds
        corner_time_saved = (corner_speed_gain / 150) * 30 * 0.6  # seconds
        
        lap_time_delta = -(straight_time_saved + corner_time_saved)
        
        return {
            'drag_coefficient': drag_coef,
            'downforce_level': downforce,
            'top_speed_gain': top_speed_gain,
            'corner_speed_gain': corner_speed_gain,
            'lap_time_delta': lap_time_delta,
            'balance': 'high_downforce' if downforce > 0.5 else 'low_drag'
        }
    
    def run_parallel_simulations(self, strategies: List[List[Tuple[str, int]]]) -> List[Dict]:
        """
        Run multiple strategy simulations in parallel (simulated HPC behavior).
        
        Args:
            strategies: List of tire strategies to simulate
            
        Returns:
            List of simulation results sorted by total time
        """
        results = []
        
        # Simulate parallel processing with numpy vectorization
        start_time = time.time()
        
        for i, strategy in enumerate(strategies):
            result = self.simulate_tire_strategy(strategy)
            result['strategy_id'] = i
            results.append(result)
            
        processing_time = time.time() - start_time
        
        # Sort by total time (fastest first)
        results.sort(key=lambda x: x['total_time'])
        
        # Add performance metadata
        for i, result in enumerate(results):
            result['rank'] = i + 1
            result['time_delta'] = result['total_time'] - results[0]['total_time']
            
        return {
            'results': results,
            'processing_time': processing_time,
            'strategies_evaluated': len(strategies)
        }
    
    def generate_optimal_strategies(self, weather_condition: str = 'dry') -> List[List[Tuple[str, int]]]:
        """
        Generate a set of optimal tire strategies based on conditions.
        
        Args:
            weather_condition: 'dry', 'wet', or 'mixed'
            
        Returns:
            List of recommended strategies
        """
        strategies = []
        total_laps = self.config.total_laps
        
        if weather_condition == 'dry':
            # One-stop strategies
            strategies.append([('medium', total_laps // 2), ('hard', total_laps - total_laps // 2)])
            strategies.append([('soft', total_laps // 3), ('medium', total_laps - total_laps // 3)])
            strategies.append([('soft', total_laps // 4), ('hard', total_laps - total_laps // 4)])
            
            # Two-stop strategies
            lap_third = total_laps // 3
            strategies.append([('soft', lap_third), ('medium', lap_third), ('soft', total_laps - 2 * lap_third)])
            strategies.append([('soft', lap_third), ('soft', lap_third), ('medium', total_laps - 2 * lap_third)])
            
            # Aggressive strategy
            strategies.append([('soft', total_laps // 5), ('soft', total_laps // 5), ('medium', total_laps - 2 * (total_laps // 5))])
            
            # Conservative strategy
            strategies.append([('hard', total_laps)])
            
        return strategies
