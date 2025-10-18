#!/usr/bin/env python3
"""
F1 Race Strategy CLI
Command-line interface for race engineers
"""
import sys
import json
import argparse
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, '/home/runner/work/HackTX_KV/HackTX_KV')

from src.models.race_models import (
    RaceConditions, CarState, SimulationRequest,
    TireCompound, WeatherCondition
)
from src.hpc_simulator.simulator import F1RaceSimulator
from src.strategy_engine.analyzer import StrategyAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description='F1 Race Strategy Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick analysis with current conditions
  python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12
  
  # Safety car scenario
  python cli.py --lap 30 --total-laps 58 --position 3 --tire soft --tire-age 8 --safety-car
  
  # Wet weather analysis
  python cli.py --lap 15 --total-laps 58 --position 7 --tire intermediate --tire-age 5 --weather light_rain
        """
    )
    
    # Race conditions
    parser.add_argument('--lap', type=int, required=True, help='Current lap number')
    parser.add_argument('--total-laps', type=int, required=True, help='Total race laps')
    parser.add_argument('--weather', choices=['dry', 'light_rain', 'heavy_rain'], 
                       default='dry', help='Weather conditions')
    parser.add_argument('--track-temp', type=float, default=45.0, 
                       help='Track temperature in Celsius')
    parser.add_argument('--air-temp', type=float, default=28.0, 
                       help='Air temperature in Celsius')
    parser.add_argument('--safety-car', action='store_true', 
                       help='Safety car is deployed')
    
    # Car state
    parser.add_argument('--position', type=int, required=True, 
                       help='Current race position')
    parser.add_argument('--tire', choices=['soft', 'medium', 'hard', 'intermediate', 'wet'],
                       required=True, help='Current tire compound')
    parser.add_argument('--tire-age', type=int, required=True, 
                       help='Tire age in laps')
    parser.add_argument('--fuel', type=float, default=45.0, 
                       help='Current fuel load in kg')
    parser.add_argument('--lap-time', type=float, default=78.5, 
                       help='Last lap time in seconds')
    parser.add_argument('--gap-leader', type=float, default=15.0, 
                       help='Gap to leader in seconds')
    parser.add_argument('--gap-next', type=float, default=2.0, 
                       help='Gap to car ahead in seconds')
    
    # Simulation
    parser.add_argument('--scenarios', type=int, default=1000, 
                       help='Number of scenarios to simulate')
    parser.add_argument('--json', action='store_true', 
                       help='Output in JSON format')
    parser.add_argument('--radio', action='store_true',
                       help='Show only radio message')
    
    args = parser.parse_args()
    
    # Create request
    race_conditions = RaceConditions(
        lap=args.lap,
        total_laps=args.total_laps,
        weather=WeatherCondition(args.weather),
        track_temp=args.track_temp,
        air_temp=args.air_temp,
        safety_car=args.safety_car
    )
    
    car_state = CarState(
        position=args.position,
        tire_compound=TireCompound(args.tire),
        tire_age=args.tire_age,
        fuel_load=args.fuel,
        lap_time=args.lap_time,
        gap_to_leader=args.gap_leader,
        gap_to_next=args.gap_next
    )
    
    # Run simulation
    if not args.json:
        print("🏎️  F1 Race Strategy Analysis")
        print("=" * 60)
        print(f"Running {args.scenarios} HPC simulations...")
        print()
    
    simulator = F1RaceSimulator()
    analyzer = StrategyAnalyzer()
    
    simulation_results = simulator.simulate_parallel(
        race_conditions,
        car_state,
        args.scenarios
    )
    
    recommendation = analyzer.analyze_and_recommend(
        race_conditions,
        car_state,
        simulation_results,
        0.0
    )
    
    # Output results
    if args.json:
        print(json.dumps(recommendation.model_dump(mode='json'), indent=2))
    elif args.radio:
        radio_msg = analyzer.generate_radio_message(recommendation)
        print(f"📻 RADIO: {radio_msg}")
    else:
        print_recommendation(recommendation)


def print_recommendation(rec):
    """Print recommendation in human-readable format"""
    print("📊 ANALYSIS")
    print("-" * 60)
    print(rec.reasoning)
    print()
    
    print("✅ OPTIMAL STRATEGY")
    print("-" * 60)
    optimal = rec.optimal_strategy
    print(f"Expected Position: P{optimal.estimated_finish_position}")
    print(f"Estimated Race Time: {format_time(optimal.estimated_race_time)}")
    print(f"Risk Score: {optimal.risk_score:.1%}")
    print(f"Fuel Status: {'⚠️  CRITICAL' if optimal.fuel_critical else '✓ OK'}")
    print()
    
    if optimal.pit_stops:
        print("Pit Stop Plan:")
        for pit in optimal.pit_stops:
            print(f"  🔧 Lap {pit.lap}: {pit.tire_compound.value.upper()} "
                  f"(Confidence: {pit.confidence:.0%})")
    else:
        print("🏁 No-Stop Strategy")
    print()
    
    print("📻 RADIO MESSAGE")
    print("-" * 60)
    radio_msg = StrategyAnalyzer().generate_radio_message(rec)
    print(radio_msg)
    print()
    
    if rec.alternative_strategies:
        print(f"📋 TOP {min(3, len(rec.alternative_strategies))} ALTERNATIVES")
        print("-" * 60)
        for idx, alt in enumerate(rec.alternative_strategies[:3], 1):
            print(f"{idx}. P{alt.estimated_finish_position} | "
                  f"Time: {format_time(alt.estimated_race_time)} | "
                  f"Stops: {len(alt.pit_stops)} | "
                  f"Risk: {alt.risk_score:.0%}")
        print()


def format_time(seconds: float) -> str:
    """Format race time"""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:06.3f}"


if __name__ == '__main__':
    main()
