"""
F1 Race Decision System - Demo Script
Demonstrates the key features and capabilities of the system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from simulation.hpc_engine import HPCSimulationEngine, SimulationConfig
from simulation.decision_system import DecisionSupportSystem, RaceContext
import time


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_strategy_simulation():
    """Demonstrate HPC strategy simulation"""
    print_section("1. HPC STRATEGY SIMULATION")
    
    # Configure race
    config = SimulationConfig(
        track_length=5.5,        # Monaco-like circuit
        total_laps=60,
        fuel_capacity=110.0,
        fuel_consumption_rate=1.6,
        drag_coefficient=0.30,
        downforce_level=0.50
    )
    
    print("Race Configuration:")
    print(f"  Track: {config.track_length}km circuit")
    print(f"  Total Laps: {config.total_laps}")
    print(f"  Fuel Capacity: {config.fuel_capacity}kg")
    print(f"  Drag Coefficient: {config.drag_coefficient}")
    print(f"  Downforce Level: {config.downforce_level}")
    
    # Initialize engine
    engine = HPCSimulationEngine(config)
    
    # Generate optimal strategies
    print("\n⚙️  Generating optimal strategies for dry conditions...")
    strategies = engine.generate_optimal_strategies('dry')
    print(f"✓ Generated {len(strategies)} strategy variants")
    
    # Run parallel simulations
    print("\n🚀 Running parallel HPC simulations...")
    start_time = time.time()
    results = engine.run_parallel_simulations(strategies)
    processing_time = time.time() - start_time
    
    print(f"✓ Simulated {results['strategies_evaluated']} strategies in {processing_time*1000:.1f}ms")
    
    # Display top 3 strategies
    print("\n📊 Top 3 Strategies:")
    for i, result in enumerate(results['results'][:3], 1):
        print(f"\n  Strategy #{i} (Rank {result['rank']})")
        print(f"    Tire Strategy: {' → '.join([f'{s[0].upper()}({s[1]} laps)' for s in result['strategy']])}")
        print(f"    Total Race Time: {result['total_time']:.1f}s")
        print(f"    Average Lap Time: {result['average_lap_time']:.2f}s")
        print(f"    Pit Stops: {result['num_pit_stops']}")
        if result['time_delta'] > 0:
            print(f"    Time Delta: +{result['time_delta']:.1f}s")
    
    return engine, results


def demo_realtime_decision(engine, simulation_results):
    """Demonstrate real-time decision making"""
    print_section("2. REAL-TIME DECISION MAKING")
    
    # Simulate race context at lap 25
    race_context = RaceContext(
        current_lap=25,
        total_laps=60,
        current_position=3,
        tire_age=12,
        tire_compound='medium',
        fuel_remaining=55.0,
        gap_to_leader=8.5,
        gap_to_next=1.2,
        track_temp=42.0,
        weather_forecast='dry'
    )
    
    print("Current Race Context:")
    print(f"  Lap: {race_context.current_lap}/{race_context.total_laps}")
    print(f"  Position: P{race_context.current_position}")
    print(f"  Tire: {race_context.tire_compound.upper()} ({race_context.tire_age} laps old)")
    print(f"  Fuel: {race_context.fuel_remaining:.1f}kg")
    print(f"  Gap to Leader: {race_context.gap_to_leader:.1f}s")
    print(f"  Gap to Next: {race_context.gap_to_next:.1f}s")
    print(f"  Track Temperature: {race_context.track_temp}°C")
    
    # Make decision
    decision_system = DecisionSupportSystem()
    print("\n🤖 Analyzing race context and simulation data...")
    decision = decision_system.make_realtime_decision(race_context, simulation_results)
    
    print(f"\n🎯 RECOMMENDED ACTION: {decision['recommended_action']}")
    print(f"   Urgency: {decision['urgency'].upper()}")
    
    print("\n📋 Rationale:")
    for reason in decision['rationale']:
        print(f"   • {reason}")
    
    # Generate strategy summary
    print("\n📊 Generating comprehensive strategy summary...")
    summary = decision_system.generate_strategy_summary(simulation_results, race_context)
    
    print(f"\n💡 Executive Summary:")
    print(f"   {summary['executive_summary']}")
    
    print(f"\n🔑 Key Insights:")
    for insight in summary['key_insights']:
        print(f"   • {insight}")
    
    print(f"\n📢 Communication Notes for Driver:")
    for note in summary['communication_notes']:
        print(f"   • {note}")
    
    # Predict race outcome
    print("\n🔮 Predicting race outcome...")
    prediction = decision_system.predict_race_outcome(race_context, simulation_results)
    
    print(f"\n   Predicted Finish: P{prediction['predicted_position']}")
    print(f"   Confidence: {prediction['confidence']}")
    print(f"   Scenarios:")
    print(f"     Best Case: P{prediction['scenarios']['best_case']}")
    print(f"     Likely: P{prediction['scenarios']['likely']}")
    print(f"     Worst Case: P{prediction['scenarios']['worst_case']}")


def demo_fuel_strategy(engine):
    """Demonstrate fuel strategy simulation"""
    print_section("3. FUEL STRATEGY OPTIMIZATION")
    
    print("Testing fuel-saving strategy for specific laps...")
    
    # Fuel-save on laps 15-20 and 45-50
    fuel_save_laps = list(range(15, 21)) + list(range(45, 51))
    
    print(f"\nFuel-saving laps: {fuel_save_laps}")
    
    result = engine.simulate_fuel_strategy(fuel_save_laps)
    
    print(f"\n📊 Fuel Strategy Results:")
    print(f"   Total Fuel Saved: {result['fuel_savings']:.2f}kg")
    print(f"   Final Fuel: {result['final_fuel']:.2f}kg")
    print(f"   Fuel Safe: {'✓ Yes' if result['fuel_safe'] else '✗ No - CRITICAL'}")
    
    print(f"\n   Sample Lap Data:")
    for lap_data in result['lap_data'][14:21]:  # Show laps 15-21
        mode_indicator = "💾" if lap_data['mode'] == 'saving' else "⚡"
        print(f"     Lap {lap_data['lap']}: {mode_indicator} {lap_data['fuel_remaining']:.1f}kg remaining")


def demo_aero_setup(engine):
    """Demonstrate aerodynamic setup simulation"""
    print_section("4. AERODYNAMIC SETUP ANALYSIS")
    
    print("Comparing different aerodynamic configurations:\n")
    
    configs = [
        (0.28, 0.55, "High Downforce"),
        (0.30, 0.50, "Balanced"),
        (0.32, 0.45, "Low Drag")
    ]
    
    for drag, downforce, name in configs:
        result = engine.simulate_aero_setup(drag, downforce)
        
        print(f"  {name} Setup:")
        print(f"    Drag: {result['drag_coefficient']:.3f} | Downforce: {result['downforce_level']:.3f}")
        print(f"    Top Speed Gain: {result['top_speed_gain']:+.1f} km/h")
        print(f"    Corner Speed Gain: {result['corner_speed_gain']:+.1f} km/h")
        print(f"    Lap Time Impact: {result['lap_time_delta']:+.3f}s")
        print(f"    Balance: {result['balance'].replace('_', ' ').upper()}")
        print()


def main():
    """Run complete demonstration"""
    print("\n" + "=" * 70)
    print("  🏁 F1 RACE DECISION SYSTEM - DEMONSTRATION")
    print("  Bridging HPC with Real-Time Race Decision-Making")
    print("=" * 70)
    
    try:
        # Run demonstrations
        engine, sim_results = demo_strategy_simulation()
        demo_realtime_decision(engine, sim_results)
        demo_fuel_strategy(engine)
        demo_aero_setup(engine)
        
        # Final summary
        print_section("DEMONSTRATION COMPLETE")
        print("✅ All systems operational!")
        print("\nKey Capabilities Demonstrated:")
        print("  1. ⚡ Fast HPC strategy simulations (milliseconds)")
        print("  2. 🎯 Real-time decision recommendations")
        print("  3. 💾 Fuel strategy optimization")
        print("  4. 🏎️  Aerodynamic setup analysis")
        print("  5. 🔮 Race outcome prediction")
        print("\nThe system is ready to support race engineers with")
        print("real-time, data-driven decisions during the race.")
        print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
