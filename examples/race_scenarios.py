#!/usr/bin/env python3
"""
Example: Race scenario analysis
Demonstrates different race scenarios and strategy recommendations
"""
import sys
sys.path.insert(0, '/home/runner/work/HackTX_KV/HackTX_KV')

from src.models.race_models import (
    RaceConditions, CarState, TireCompound, WeatherCondition
)
from src.hpc_simulator.simulator import F1RaceSimulator
from src.strategy_engine.analyzer import StrategyAnalyzer


def example_1_normal_race():
    """Example 1: Normal dry race, mid-race strategy decision"""
    print("=" * 70)
    print("EXAMPLE 1: Normal Dry Race - Mid-Race Decision")
    print("=" * 70)
    
    race_conditions = RaceConditions(
        lap=25,
        total_laps=58,
        weather=WeatherCondition.DRY,
        track_temp=45.0,
        air_temp=28.0,
        safety_car=False
    )
    
    car_state = CarState(
        position=5,
        tire_compound=TireCompound.MEDIUM,
        tire_age=12,
        fuel_load=45.0,
        lap_time=78.5,
        gap_to_leader=15.2,
        gap_to_next=2.8
    )
    
    simulator = F1RaceSimulator()
    analyzer = StrategyAnalyzer()
    
    results = simulator.simulate_parallel(race_conditions, car_state, 1000)
    recommendation = analyzer.analyze_and_recommend(
        race_conditions, car_state, results, 0.0
    )
    
    print(f"\n{recommendation.reasoning}")
    print(f"\n📻 Radio: {analyzer.generate_radio_message(recommendation)}")
    print()


if __name__ == '__main__':
    print("\n🏎️  F1 RACE STRATEGY EXAMPLE\n")
    example_1_normal_race()
