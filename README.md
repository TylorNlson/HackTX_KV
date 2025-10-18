# HackTX_KV - F1 Race Decision System

From Simulation to Strategy — Real-Time Insights for the Fastest Decisions on Track.

## 🏁 Overview

The F1 Race Decision System bridges High-Performance Computing (HPC) with real-time race decision-making. F1 races are won and lost in milliseconds, with teams running complex simulations for tire strategy, fuel management, and aerodynamic setups while the race unfolds in real-time. 

This solution enables race engineers to:
- **Run parallel HPC simulations** of thousands of race scenarios in milliseconds
- **Get instant strategic recommendations** based on current race context
- **Visualize complex data** through an intuitive web dashboard
- **Make data-driven decisions** during the 2-hour race window

## 🚀 Features

### HPC Simulation Engine
- **Tire Strategy Simulation**: Model different tire compound strategies (Soft, Medium, Hard)
- **Fuel Management**: Optimize fuel consumption and saving strategies
- **Aerodynamic Setup**: Test drag coefficient and downforce configurations
- **Parallel Processing**: Evaluate multiple strategies simultaneously

### Real-Time Decision Support
- **Context-Aware Recommendations**: Provides actionable decisions based on current race state
- **Risk Assessment**: Evaluates strategy risks and alternatives
- **Predictive Analysis**: Forecasts race outcomes based on current trajectory
- **Critical Window Detection**: Identifies key decision points during the race

### Web Dashboard
- **Real-Time Interface**: Monitor race context and get instant recommendations
- **Strategy Visualization**: Compare multiple strategies side-by-side
- **Performance Metrics**: Track simulation performance and optimization results
- **Responsive Design**: Access from any device, anywhere

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- Modern web browser

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/TylorNlson/HackTX_KV.git
cd HackTX_KV
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## ⚙️ Configuration

The system uses the following default ports:
- **API Server**: Port 5000 (configurable via `FLASK_PORT` environment variable)
- **Web Dashboard**: Port 8000 (or any HTTP server port)

The frontend automatically detects the API endpoint based on its own hostname and port. If the frontend runs on port 8001, it will connect to API on port 5001 (useful for development). Otherwise, it defaults to port 5000.

## 🏃 Quick Start

### Start the API Server

```bash
python src/api/app.py
```

The API will be available at `http://localhost:5000`

### Open the Dashboard

Open `index.html` in your web browser, or serve it with a simple HTTP server:

```bash
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

## 📖 Usage

### Web Dashboard

1. **Race Context Panel**: Input current race conditions
   - Current lap, position, tire age
   - Fuel remaining, gaps to competitors
   - Track temperature and weather

2. **Get Real-Time Decision**: Click to receive instant strategic recommendations
   - Pit stop timing
   - Tire compound selection
   - Fuel saving modes
   - Push/conserve recommendations

3. **Strategy Simulation**: Run HPC simulations for different weather conditions
   - Evaluates multiple tire strategies
   - Compares pit stop scenarios
   - Shows optimal race time

4. **Aerodynamic Setup**: Test different aero configurations
   - Adjust drag coefficient and downforce
   - See impact on lap time
   - Balance top speed vs cornering

### API Endpoints

#### Run Strategy Simulations
```bash
POST /api/simulate/strategies
Content-Type: application/json

{
  "weather": "dry",
  "track_config": {
    "track_length": 5.5,
    "total_laps": 60,
    "fuel_capacity": 110.0
  }
}
```

#### Get Real-Time Decision
```bash
POST /api/decision/realtime
Content-Type: application/json

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
```

#### Simulate Tire Strategy
```bash
POST /api/simulate/tire-strategy
Content-Type: application/json

{
  "strategy": [
    ["soft", 20],
    ["medium", 40]
  ]
}
```

#### Simulate Aero Setup
```bash
POST /api/simulate/aero-setup
Content-Type: application/json

{
  "drag_coefficient": 0.30,
  "downforce_level": 0.50
}
```

### Python Examples

```python
from src.simulation.hpc_engine import HPCSimulationEngine, SimulationConfig
from src.simulation.decision_system import DecisionSupportSystem, RaceContext

# Initialize simulation engine
config = SimulationConfig(
    track_length=5.5,
    total_laps=60,
    fuel_capacity=110.0,
    fuel_consumption_rate=1.6,
    drag_coefficient=0.30,
    downforce_level=0.50
)

engine = HPCSimulationEngine(config)

# Generate and simulate strategies
strategies = engine.generate_optimal_strategies('dry')
results = engine.run_parallel_simulations(strategies)

print(f"Best strategy: {results['results'][0]['strategy']}")
print(f"Expected time: {results['results'][0]['total_time']:.1f}s")

# Make real-time decision
decision_system = DecisionSupportSystem()
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

decision = decision_system.make_realtime_decision(race_context, results)
print(f"Recommendation: {decision['recommended_action']}")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Dashboard                          │
│              (Real-Time Visualization)                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ REST API
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Flask API Layer                         │
│            (Request Routing & Response)                  │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼──────────┐
│ HPC Simulation │  │ Decision Support  │
│     Engine     │  │      System       │
│                │  │                   │
│ • Tire Models  │  │ • Context Analysis│
│ • Fuel Calc    │  │ • Recommendations │
│ • Aero Setup   │  │ • Risk Assessment │
│ • Parallel Sim │  │ • Predictions     │
└────────────────┘  └───────────────────┘
```

## 🧪 Testing

Run basic functionality test:

```bash
python -c "
from src.simulation.hpc_engine import HPCSimulationEngine, SimulationConfig

config = SimulationConfig(
    track_length=5.5,
    total_laps=60,
    fuel_capacity=110.0,
    fuel_consumption_rate=1.6,
    drag_coefficient=0.30,
    downforce_level=0.50
)

engine = HPCSimulationEngine(config)
strategies = engine.generate_optimal_strategies('dry')
results = engine.run_parallel_simulations(strategies)

print('✓ Simulation engine working')
print(f'✓ Evaluated {results[\"strategies_evaluated\"]} strategies')
print(f'✓ Processing time: {results[\"processing_time\"]*1000:.0f}ms')
"
```

## 🎯 Key Benefits

1. **Speed**: HPC-powered simulations complete in milliseconds, not minutes
2. **Accuracy**: Physics-based models for tire degradation, fuel consumption, and aerodynamics
3. **Real-Time**: Instant recommendations that adapt to changing race conditions
4. **User-Friendly**: Intuitive dashboard for non-technical race engineers
5. **Comprehensive**: Covers all major strategy aspects (tires, fuel, aero)
6. **Scalable**: Easily extend with more simulation parameters

## 🔬 Technical Details

### Simulation Models

**Tire Degradation Model**:
- Compound-specific grip levels and degradation rates
- Temperature sensitivity
- Age-based performance decline

**Fuel Management**:
- Lap-by-lap consumption tracking
- Weight effect on lap times
- Fuel-saving mode simulation

**Aerodynamics**:
- Drag vs downforce trade-offs
- Speed impact on straights and corners
- Balance optimization

### Performance

- **Simulation Speed**: ~10-50ms for 7 parallel strategies
- **API Response Time**: <100ms for most endpoints
- **Decision Latency**: <200ms end-to-end

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Machine learning for strategy optimization
- Weather change modeling
- Safety car scenario handling
- Historical race data integration
- Multi-driver strategy coordination

## 📄 License

MIT License - see LICENSE file for details

## 👥 Authors

Built for HackTX 2024

## 🙏 Acknowledgments

- Inspired by real F1 race engineering challenges
- Built with modern web technologies and Python scientific stack
- Designed for the pressure of real-time decision-making in motorsport
