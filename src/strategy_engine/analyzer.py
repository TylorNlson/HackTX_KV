"""
Strategy Engine - Analyzes simulation results and provides actionable recommendations
"""
from typing import List
from ..models.race_models import (
    RaceConditions, CarState, SimulationScenario, 
    StrategyRecommendation
)
import time


class StrategyAnalyzer:
    """Analyzes simulation results and generates human-readable recommendations"""
    
    def analyze_and_recommend(
        self,
        race_conditions: RaceConditions,
        car_state: CarState,
        simulation_results: List[SimulationScenario],
        computation_time_ms: float
    ) -> StrategyRecommendation:
        """
        Analyze simulation results and provide strategic recommendations
        """
        if not simulation_results:
            raise ValueError("No simulation results to analyze")
        
        # Get optimal and alternative strategies
        optimal = simulation_results[0]
        alternatives = simulation_results[1:6]  # Top 5 alternatives
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            race_conditions,
            car_state,
            optimal,
            alternatives
        )
        
        return StrategyRecommendation(
            current_conditions=race_conditions,
            car_state=car_state,
            optimal_strategy=optimal,
            alternative_strategies=alternatives,
            reasoning=reasoning,
            computation_time_ms=computation_time_ms
        )
    
    def _generate_reasoning(
        self,
        race_conditions: RaceConditions,
        car_state: CarState,
        optimal: SimulationScenario,
        alternatives: List[SimulationScenario]
    ) -> str:
        """Generate human-readable reasoning for the strategy"""
        reasoning_parts = []
        
        # Current situation
        remaining_laps = race_conditions.total_laps - race_conditions.lap
        reasoning_parts.append(
            f"LAP {race_conditions.lap}/{race_conditions.total_laps}: "
            f"P{car_state.position} - {remaining_laps} laps remaining"
        )
        
        # Tire status
        reasoning_parts.append(
            f"Current tires: {car_state.tire_compound.value.upper()} "
            f"({car_state.tire_age} laps old)"
        )
        
        # Weather consideration
        if race_conditions.weather.value != "dry":
            reasoning_parts.append(
                f"⚠️ Weather: {race_conditions.weather.value.replace('_', ' ').upper()}"
            )
        
        # Safety car
        if race_conditions.safety_car:
            reasoning_parts.append("🚨 SAFETY CAR DEPLOYED - Consider pit opportunity")
        
        # Optimal strategy
        if len(optimal.pit_stops) == 0:
            reasoning_parts.append(
                "✅ OPTIMAL: NO-STOP strategy - Stay out and push"
            )
        elif len(optimal.pit_stops) == 1:
            pit = optimal.pit_stops[0]
            reasoning_parts.append(
                f"✅ OPTIMAL: ONE-STOP strategy - Pit lap {pit.lap} "
                f"for {pit.tire_compound.value.upper()} tires"
            )
        else:
            pits = ", ".join([
                f"Lap {p.lap} ({p.tire_compound.value.upper()})"
                for p in optimal.pit_stops
            ])
            reasoning_parts.append(
                f"✅ OPTIMAL: TWO-STOP strategy - {pits}"
            )
        
        # Position expectation
        reasoning_parts.append(
            f"Expected finish: P{optimal.estimated_finish_position} "
            f"(Race time: {self._format_time(optimal.estimated_race_time)})"
        )
        
        # Risk assessment
        if optimal.risk_score > 0.5:
            reasoning_parts.append(
                f"⚠️ HIGH RISK ({optimal.risk_score:.0%}) - "
                f"{'Fuel critical' if optimal.fuel_critical else 'Tire degradation concern'}"
            )
        elif optimal.risk_score > 0.2:
            reasoning_parts.append(
                f"⚡ MODERATE RISK ({optimal.risk_score:.0%})"
            )
        else:
            reasoning_parts.append(
                f"✓ LOW RISK ({optimal.risk_score:.0%})"
            )
        
        # Alternative strategies
        if alternatives:
            reasoning_parts.append(
                f"\n📊 {len(alternatives)} alternative strategies available"
            )
        
        return " | ".join(reasoning_parts)
    
    def _format_time(self, seconds: float) -> str:
        """Format race time as MM:SS.mmm"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def generate_radio_message(self, recommendation: StrategyRecommendation) -> str:
        """Generate concise radio message for driver"""
        optimal = recommendation.optimal_strategy
        car_state = recommendation.car_state
        
        messages = []
        
        if len(optimal.pit_stops) == 0:
            messages.append("Box negative. Stay out and push.")
        elif len(optimal.pit_stops) == 1:
            pit = optimal.pit_stops[0]
            laps_until_pit = pit.lap - recommendation.current_conditions.lap
            if laps_until_pit <= 3:
                messages.append(
                    f"Box this lap or next. {pit.tire_compound.value.upper()} compound."
                )
            else:
                messages.append(
                    f"Plan to box in {laps_until_pit} laps. "
                    f"{pit.tire_compound.value.upper()} compound."
                )
        else:
            next_pit = optimal.pit_stops[0]
            laps_until_pit = next_pit.lap - recommendation.current_conditions.lap
            messages.append(
                f"Two-stop strategy. Next box in {laps_until_pit} laps."
            )
        
        # Position info
        messages.append(f"Target: P{optimal.estimated_finish_position}.")
        
        # Urgency
        if optimal.risk_score > 0.5:
            messages.append("⚠️ Critical - adjust if needed.")
        
        return " ".join(messages)
