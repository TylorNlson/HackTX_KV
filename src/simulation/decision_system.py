"""
Real-time Decision Support System
Analyzes simulation results and provides actionable recommendations
"""
from typing import Dict, List, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class RaceContext:
    """Current race context for decision making"""
    current_lap: int
    total_laps: int
    current_position: int
    tire_age: int
    tire_compound: str
    fuel_remaining: float
    gap_to_leader: float  # seconds
    gap_to_next: float  # seconds
    track_temp: float
    weather_forecast: str


class DecisionSupportSystem:
    """
    Provides real-time decision support for race engineers.
    Analyzes HPC simulation results and race context to recommend optimal actions.
    """
    
    def __init__(self):
        self.decision_history = []
        
    def analyze_simulation_results(self, simulation_results: Dict) -> Dict:
        """
        Analyze simulation results and extract key insights.
        
        Args:
            simulation_results: Results from HPC simulation engine
            
        Returns:
            Analysis with key insights and recommendations
        """
        results = simulation_results['results']
        best_strategy = results[0]
        
        insights = {
            'best_strategy': {
                'strategy': best_strategy['strategy'],
                'expected_time': best_strategy['total_time'],
                'pit_stops': best_strategy['num_pit_stops']
            },
            'time_differences': [],
            'strategy_comparison': []
        }
        
        # Compare top 3 strategies
        for i, result in enumerate(results[:3]):
            insights['strategy_comparison'].append({
                'rank': i + 1,
                'strategy': result['strategy'],
                'total_time': result['total_time'],
                'time_delta': result['time_delta'],
                'advantage': self._describe_strategy_advantage(result['strategy'])
            })
            
        # Identify critical decision windows
        insights['critical_windows'] = self._identify_critical_windows(best_strategy)
        
        return insights
    
    def _describe_strategy_advantage(self, strategy: List) -> str:
        """Describe the advantage of a strategy"""
        num_stops = len(strategy) - 1
        compounds = [s[0] for s in strategy]
        
        if num_stops == 0:
            return "No stops - track position advantage but tire degradation risk"
        elif num_stops == 1:
            if 'soft' in compounds:
                return "One stop with soft - good pace early, conservative finish"
            else:
                return "One stop medium/hard - consistent pace, lower risk"
        else:
            return f"{num_stops} stops - flexible strategy, can react to race conditions"
    
    def _identify_critical_windows(self, strategy_result: Dict) -> List[Dict]:
        """Identify critical decision windows in the race"""
        windows = []
        tire_states = strategy_result['tire_states']
        
        # Find tire change points
        current_compound = tire_states[0]['compound']
        for state in tire_states:
            if state['compound'] != current_compound:
                windows.append({
                    'lap': state['lap'],
                    'type': 'pit_stop',
                    'action': f"Change to {state['compound']} tires",
                    'criticality': 'high'
                })
                current_compound = state['compound']
        
        # Find high degradation points
        for state in tire_states:
            if state['grip'] < 0.7 and state['lap'] not in [w['lap'] for w in windows]:
                windows.append({
                    'lap': state['lap'],
                    'type': 'degradation_warning',
                    'action': f"Monitor tire performance - grip at {state['grip']:.1%}",
                    'criticality': 'medium'
                })
                
        return sorted(windows, key=lambda x: x['lap'])
    
    def make_realtime_decision(self, race_context: RaceContext, 
                               simulation_results: Dict) -> Dict:
        """
        Make a real-time decision based on current race context.
        
        Args:
            race_context: Current race situation
            simulation_results: Latest simulation results
            
        Returns:
            Decision recommendation with rationale
        """
        decision = {
            'timestamp': race_context.current_lap,
            'recommended_action': '',
            'rationale': [],
            'urgency': 'normal',
            'alternatives': []
        }
        
        # Check if pit stop is needed
        if self._should_pit_now(race_context, simulation_results):
            decision['recommended_action'] = 'PIT NOW'
            decision['urgency'] = 'high'
            decision['rationale'].append(
                f"Tire age {race_context.tire_age} laps - degradation critical"
            )
            
            # Recommend tire compound
            best_compound = self._select_tire_compound(race_context, simulation_results)
            decision['rationale'].append(f"Switch to {best_compound} compound")
            decision['recommended_action'] += f" - {best_compound.upper()} TIRES"
            
        # Check fuel strategy
        elif self._should_save_fuel(race_context):
            decision['recommended_action'] = 'FUEL SAVING MODE'
            decision['urgency'] = 'medium'
            decision['rationale'].append(
                f"Fuel remaining: {race_context.fuel_remaining:.1f}kg - conserve for {self.config.total_laps - race_context.current_lap} laps"
            )
            
        # Check if we should push
        elif self._should_push(race_context):
            decision['recommended_action'] = 'PUSH FOR POSITION'
            decision['urgency'] = 'medium'
            decision['rationale'].append(
                f"Gap to next car: {race_context.gap_to_next:.1f}s - within DRS range"
            )
            
        else:
            decision['recommended_action'] = 'MAINTAIN PACE'
            decision['urgency'] = 'low'
            decision['rationale'].append('Current strategy on track')
            
        # Add context-aware information
        decision['context'] = {
            'lap': race_context.current_lap,
            'position': race_context.current_position,
            'tire_compound': race_context.tire_compound,
            'tire_age': race_context.tire_age,
            'fuel': race_context.fuel_remaining
        }
        
        self.decision_history.append(decision)
        return decision
    
    def _should_pit_now(self, context: RaceContext, simulation_results: Dict) -> bool:
        """Determine if car should pit now"""
        # Check tire age
        if context.tire_age > 25:  # Critical age
            return True
            
        # Check if we're in a pit window from strategy
        results = simulation_results['results'][0]
        for window in results.get('tire_states', []):
            if window.get('lap') == context.current_lap and window.get('age') == 0:
                return True
                
        return False
    
    def _should_save_fuel(self, context: RaceContext) -> bool:
        """Determine if fuel saving is needed"""
        laps_remaining = context.total_laps - context.current_lap
        fuel_per_lap_needed = context.fuel_remaining / laps_remaining if laps_remaining > 0 else 0
        
        # If we need more than 1.5kg per lap, we should save fuel
        return fuel_per_lap_needed < 1.3
    
    def _should_push(self, context: RaceContext) -> bool:
        """Determine if driver should push for position"""
        # Within DRS range (1 second)
        if 0 < context.gap_to_next < 1.0:
            return True
            
        # Tire is fresh (less than 5 laps old)
        if context.tire_age < 5:
            return True
            
        return False
    
    def _select_tire_compound(self, context: RaceContext, 
                              simulation_results: Dict) -> str:
        """Select optimal tire compound for next stint"""
        laps_remaining = context.total_laps - context.current_lap
        
        # If less than 15 laps, go aggressive with soft
        if laps_remaining < 15:
            return 'soft'
        # If more than 30 laps, use hard
        elif laps_remaining > 30:
            return 'hard'
        # Otherwise medium
        else:
            return 'medium'
    
    def generate_strategy_summary(self, simulation_results: Dict, 
                                  race_context: RaceContext = None) -> Dict:
        """
        Generate a comprehensive strategy summary for race engineers.
        
        Args:
            simulation_results: Results from simulations
            race_context: Optional current race context
            
        Returns:
            Easy-to-digest strategy summary
        """
        analysis = self.analyze_simulation_results(simulation_results)
        
        summary = {
            'executive_summary': '',
            'recommended_strategy': analysis['best_strategy'],
            'key_insights': [],
            'risk_assessment': {},
            'communication_notes': []
        }
        
        # Executive summary
        best = analysis['best_strategy']
        summary['executive_summary'] = (
            f"Recommend {best['pit_stops']}-stop strategy with "
            f"{', then '.join([s[0] for s in best['strategy']])} compounds. "
            f"Expected race time: {best['expected_time']:.1f}s"
        )
        
        # Key insights
        for i, comp in enumerate(analysis['strategy_comparison'][:3]):
            time_diff = comp['time_delta']
            summary['key_insights'].append(
                f"Option {i+1}: {time_diff:.1f}s slower - {comp['advantage']}"
            )
        
        # Risk assessment
        summary['risk_assessment'] = {
            'safety_car_impact': 'Medium - one-stop strategies benefit most',
            'tire_degradation_risk': 'Low to Medium',
            'fuel_margin': 'Adequate with normal consumption',
            'weather_sensitivity': 'Monitor track temperature'
        }
        
        # Communication notes for driver
        summary['communication_notes'] = [
            f"Target {best['pit_stops']} stop(s)",
            "Push hard on fresh tires",
            "Manage fuel in middle stint",
            "Watch for undercut opportunities"
        ]
        
        return summary
    
    def predict_race_outcome(self, current_context: RaceContext, 
                           simulation_results: Dict) -> Dict:
        """
        Predict race outcome based on current position and strategy.
        
        Args:
            current_context: Current race state
            simulation_results: Strategy simulations
            
        Returns:
            Outcome prediction
        """
        laps_remaining = current_context.total_laps - current_context.current_lap
        best_strategy = simulation_results['results'][0]
        
        # Estimate position changes
        gap_to_leader = current_context.gap_to_leader
        expected_lap_time = best_strategy['average_lap_time']
        
        # Simple prediction model
        time_remaining = laps_remaining * expected_lap_time
        positions_gain_potential = int(abs(gap_to_leader) / 20)  # ~20s per position
        
        prediction = {
            'predicted_position': max(1, current_context.current_position - positions_gain_potential),
            'confidence': 'medium',
            'key_factors': [
                f"{laps_remaining} laps remaining",
                f"Strategy advantage: {best_strategy['time_delta']:.1f}s",
                f"Current gap: {gap_to_leader:.1f}s"
            ],
            'scenarios': {
                'best_case': max(1, current_context.current_position - positions_gain_potential - 1),
                'likely': current_context.current_position,
                'worst_case': current_context.current_position + 1
            }
        }
        
        return prediction
