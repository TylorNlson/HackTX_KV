# 🏎️ F1 Race Strategy System

**From Simulation to Strategy — Real-Time Insights for the Fastest Decisions on Track**

A high-performance computing (HPC) powered system that bridges complex race simulations with real-time decision-making for F1 race engineers. Simulate thousands of race scenarios in milliseconds, considering tire strategy, fuel management, and aerodynamic setups to deliver optimal pit stop recommendations during live races.

## 🚀 Features

- **HPC Simulation Engine**: Run 1000+ race scenarios in under a second
- **Multi-Factor Analysis**: Tire degradation, fuel management, weather conditions, and aerodynamics
- **Real-Time Recommendations**: Instant strategy updates as race conditions change
- **Multiple Interfaces**:
  - 🖥️ Web Dashboard - Visual interface for race engineers
  - 🔌 REST API - Integration with telemetry systems
  - 💬 CLI Tool - Quick command-line analysis
  - 📡 WebSocket - Real-time push updates
- **Race Engineer Optimized**: Radio messages and concise recommendations
- **Risk Assessment**: Quantified risk scores for each strategy option

## 📋 Problem Statement

F1 races are won and lost in milliseconds. Teams run complex simulations for tire strategy, fuel management, and aerodynamic setups while the race unfolds in real-time. Current HPC systems can model thousands of race scenarios, but race engineers struggle to quickly interpret results and communicate optimal strategies to drivers during the 2-hour race window.

This solution bridges that gap by:
1. Running HPC simulations of race scenarios (tire, fuel, aero)
2. Analyzing results in real-time
3. Providing clear, actionable recommendations
4. Delivering concise radio messages for driver communication

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/TylorNlson/HackTX_KV.git
cd HackTX_KV

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Usage

### 1. Web Dashboard (Recommended)

Start the server:
```bash
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

Access the dashboard:
```
http://localhost:8000/dashboard
```

The dashboard provides an intuitive interface to:
- Input current race conditions and car state
- Run HPC simulations
- View optimal strategy with alternatives
- See risk assessments and radio messages

### 2. Command Line Interface

Quick analysis from terminal:

```bash
# Basic usage
python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12

# Safety car scenario
python cli.py --lap 30 --total-laps 58 --position 3 --tire soft --tire-age 8 --safety-car

# Wet weather analysis
python cli.py --lap 15 --total-laps 58 --position 7 --tire intermediate --tire-age 5 --weather light_rain

# Radio message only
python cli.py --lap 40 --total-laps 58 --position 2 --tire hard --tire-age 18 --radio

# JSON output for integration
python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12 --json
```

### 3. REST API

#### Get Strategy Recommendation

```bash
curl -X POST http://localhost:8000/api/strategy/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "race_conditions": {
      "lap": 25,
      "total_laps": 58,
      "weather": "dry",
      "track_temp": 45.0,
      "air_temp": 28.0,
      "safety_car": false
    },
    "car_state": {
      "position": 5,
      "tire_compound": "medium",
      "tire_age": 12,
      "fuel_load": 45.0,
      "lap_time": 78.5,
      "gap_to_leader": 15.2,
      "gap_to_next": 2.8
    },
    "num_scenarios": 1000
  }'
```

#### Get Radio Message

```bash
curl -X POST http://localhost:8000/api/strategy/radio-message \
  -H "Content-Type: application/json" \
  -d '{ ... same payload ... }'
```

#### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Race Engineers                        │
│              (Dashboard / CLI / Radio)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Server                          │
│         (REST API + WebSocket Updates)                   │
└────────────┬───────────────────────┬────────────────────┘
             │                       │
             ▼                       ▼
┌────────────────────────┐  ┌──────────────────────────┐
│   HPC Simulator        │  │  Strategy Analyzer       │
│                        │  │                          │
│ • Tire degradation     │  │ • Result interpretation  │
│ • Fuel management      │  │ • Risk assessment        │
│ • Weather effects      │  │ • Radio message gen      │
│ • 1000+ scenarios      │  │ • Alternative ranking    │
└────────────────────────┘  └──────────────────────────┘
```

### Components

1. **HPC Simulator** (`src/hpc_simulator/simulator.py`)
   - Simulates thousands of race scenarios in parallel
   - Models tire degradation, fuel consumption, weather effects
   - Generates diverse pit stop strategies

2. **Strategy Analyzer** (`src/strategy_engine/analyzer.py`)
   - Analyzes simulation results
   - Generates human-readable recommendations
   - Creates concise radio messages for drivers

3. **API Server** (`src/api/server.py`)
   - FastAPI-based REST API
   - WebSocket support for real-time updates
   - Serves dashboard interface

4. **Data Models** (`src/models/race_models.py`)
   - Pydantic models for type safety
   - Race conditions, car state, strategies

## 📊 Example Output

```
🏎️  F1 Race Strategy Analysis
============================================================
Running 1000 HPC simulations...

📊 ANALYSIS
------------------------------------------------------------
LAP 25/58: P5 - 33 laps remaining | Current tires: MEDIUM (12 laps old) | 
✅ OPTIMAL: ONE-STOP strategy - Pit lap 38 for HARD tires | 
Expected finish: P4 (Race time: 1:25:34.250) | ✓ LOW RISK (15%)

✅ OPTIMAL STRATEGY
------------------------------------------------------------
Expected Position: P4
Estimated Race Time: 1:25:34.250
Risk Score: 15.0%
Fuel Status: ✓ OK

Pit Stop Plan:
  🔧 Lap 38: HARD (Confidence: 83%)

📻 RADIO MESSAGE
------------------------------------------------------------
Plan to box in 13 laps. HARD compound. Target P4.
```

## 🎮 Use Cases

### Race Day Strategy
- Real-time pit stop recommendations
- Safety car strategy decisions
- Weather change adaptations
- Undercut/overcut timing

### Pre-Race Planning
- Optimal tire allocation
- Fuel load calculations
- Risk assessment for different strategies
- Alternative scenario planning

### Post-Race Analysis
- Strategy effectiveness review
- What-if scenario analysis
- Performance optimization

## 🔧 Configuration

Key parameters in the simulator:

```python
# Tire degradation rates (seconds per lap)
TIRE_DEGRADATION = {
    SOFT: 0.08,
    MEDIUM: 0.05,
    HARD: 0.03
}

# Pit stop time loss
PIT_STOP_TIME = 25.0  # seconds

# Fuel effect
FUEL_EFFECT = 0.03  # seconds per kg
```

## 🧪 Testing

Run tests (if implemented):
```bash
pytest tests/
```

## 📈 Performance

- **Simulation Speed**: 1000 scenarios in ~100-500ms
- **API Response**: < 1 second for full analysis
- **Scalability**: Handles concurrent requests
- **Accuracy**: Based on realistic F1 physics models

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Machine learning for tire degradation prediction
- Historical data integration
- Multi-car race simulation
- DRS and overtaking modeling
- Real telemetry data integration

## 📄 License

This project is part of HackTX and is provided as-is for educational and demonstration purposes.

## 🏁 Acknowledgments

Built for HackTX to demonstrate bridging HPC simulations with real-time race decision-making.

---

**Made with ❤️ for F1 Race Engineers**
