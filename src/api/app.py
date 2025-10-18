"""
Flask API for F1 Race Decision Support System
Provides REST endpoints for simulation and real-time decision making
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulation.hpc_engine import HPCSimulationEngine, SimulationConfig
from simulation.decision_system import DecisionSupportSystem, RaceContext

app = Flask(__name__)
CORS(app)

# Initialize systems
default_config = SimulationConfig(
    track_length=5.5,
    total_laps=60,
    fuel_capacity=110.0,
    fuel_consumption_rate=1.6,
    drag_coefficient=0.30,
    downforce_level=0.50
)

simulation_engine = HPCSimulationEngine(default_config)
decision_system = DecisionSupportSystem()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'F1 Race Decision System'})


@app.route('/api/simulate/strategies', methods=['POST'])
def simulate_strategies():
    """
    Run HPC simulations for multiple tire strategies.
    
    Request body:
    {
        "weather": "dry|wet|mixed",
        "track_config": {
            "track_length": 5.5,
            "total_laps": 60,
            ...
        }
    }
    """
    try:
        data = request.get_json()
        weather = data.get('weather', 'dry')
        
        # Update config if provided
        if 'track_config' in data:
            config = SimulationConfig(**data['track_config'])
            engine = HPCSimulationEngine(config)
        else:
            engine = simulation_engine
            
        # Generate optimal strategies
        strategies = engine.generate_optimal_strategies(weather)
        
        # Run parallel simulations
        results = engine.run_parallel_simulations(strategies)
        
        # Analyze results
        analysis = decision_system.analyze_simulation_results(results)
        
        return jsonify({
            'success': True,
            'simulation_results': results,
            'analysis': analysis,
            'weather': weather
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/simulate/tire-strategy', methods=['POST'])
def simulate_tire_strategy():
    """
    Simulate a specific tire strategy.
    
    Request body:
    {
        "strategy": [["soft", 20], ["medium", 40]]
    }
    """
    try:
        data = request.get_json()
        strategy = data.get('strategy', [])
        
        if not strategy:
            return jsonify({'success': False, 'error': 'Strategy required'}), 400
            
        # Convert to tuples
        strategy = [(s[0], s[1]) for s in strategy]
        
        result = simulation_engine.simulate_tire_strategy(strategy)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/simulate/fuel-strategy', methods=['POST'])
def simulate_fuel_strategy():
    """
    Simulate fuel-saving strategy.
    
    Request body:
    {
        "fuel_save_laps": [10, 11, 12, 35, 36]
    }
    """
    try:
        data = request.get_json()
        fuel_save_laps = data.get('fuel_save_laps', [])
        
        result = simulation_engine.simulate_fuel_strategy(fuel_save_laps)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/simulate/aero-setup', methods=['POST'])
def simulate_aero_setup():
    """
    Simulate aerodynamic setup.
    
    Request body:
    {
        "drag_coefficient": 0.30,
        "downforce_level": 0.50
    }
    """
    try:
        data = request.get_json()
        drag_coef = data.get('drag_coefficient', 0.30)
        downforce = data.get('downforce_level', 0.50)
        
        result = simulation_engine.simulate_aero_setup(drag_coef, downforce)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/decision/realtime', methods=['POST'])
def make_realtime_decision():
    """
    Get real-time decision recommendation.
    
    Request body:
    {
        "race_context": {
            "current_lap": 25,
            "total_laps": 60,
            "current_position": 3,
            "tire_age": 12,
            "tire_compound": "medium",
            "fuel_remaining": 55.0,
            "gap_to_leader": 8.5,
            "gap_to_next": 1.2,
            "track_temp": 42.0,
            "weather_forecast": "dry"
        }
    }
    """
    try:
        data = request.get_json()
        context_data = data.get('race_context', {})
        
        # Create race context
        race_context = RaceContext(**context_data)
        
        # Get latest simulation results
        strategies = simulation_engine.generate_optimal_strategies('dry')
        simulation_results = simulation_engine.run_parallel_simulations(strategies)
        
        # Make decision
        decision = decision_system.make_realtime_decision(race_context, simulation_results)
        
        # Generate summary
        summary = decision_system.generate_strategy_summary(simulation_results, race_context)
        
        # Predict outcome
        prediction = decision_system.predict_race_outcome(race_context, simulation_results)
        
        return jsonify({
            'success': True,
            'decision': decision,
            'summary': summary,
            'prediction': prediction
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/strategy/summary', methods=['POST'])
def get_strategy_summary():
    """
    Get comprehensive strategy summary.
    
    Request body:
    {
        "weather": "dry"
    }
    """
    try:
        data = request.get_json()
        weather = data.get('weather', 'dry')
        
        # Generate and simulate strategies
        strategies = simulation_engine.generate_optimal_strategies(weather)
        simulation_results = simulation_engine.run_parallel_simulations(strategies)
        
        # Generate summary
        summary = decision_system.generate_strategy_summary(simulation_results)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'top_strategies': simulation_results['results'][:3]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current simulation configuration"""
    return jsonify({
        'success': True,
        'config': {
            'track_length': default_config.track_length,
            'total_laps': default_config.total_laps,
            'fuel_capacity': default_config.fuel_capacity,
            'fuel_consumption_rate': default_config.fuel_consumption_rate,
            'drag_coefficient': default_config.drag_coefficient,
            'downforce_level': default_config.downforce_level
        }
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update simulation configuration"""
    try:
        data = request.get_json()
        
        global default_config, simulation_engine
        default_config = SimulationConfig(**data)
        simulation_engine = HPCSimulationEngine(default_config)
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated',
            'config': data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
