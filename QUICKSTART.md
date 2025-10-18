# Quick Start Guide

Get started with the F1 Race Strategy System in under 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/TylorNlson/HackTX_KV.git
cd HackTX_KV

# Install dependencies
pip install -r requirements.txt
```

## Usage Options

### Option 1: Web Dashboard (Easiest)

**Start the server:**
```bash
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

**Open in browser:**
```
http://localhost:8000/dashboard
```

**What you'll see:**
- Input fields for race conditions and car state
- "Analyze Strategy" button
- Real-time strategy recommendations
- Radio messages for drivers
- Alternative strategies

### Option 2: Command Line (Fastest)

**Basic usage:**
```bash
python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12
```

**Get just the radio message:**
```bash
python cli.py --lap 40 --total-laps 58 --position 2 --tire hard --tire-age 18 --radio
```

**Safety car scenario:**
```bash
python cli.py --lap 30 --total-laps 58 --position 3 --tire soft --tire-age 8 --safety-car
```

**Output as JSON:**
```bash
python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12 --json
```

### Option 3: REST API (Integration)

**Start the server:**
```bash
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

**Make a request:**
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

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Option 4: Python Code

**Run the example:**
```bash
python examples/race_scenarios.py
```

**Or create your own:**
```python
from src.models.race_models import (
    RaceConditions, CarState, TireCompound, WeatherCondition
)
from src.hpc_simulator.simulator import F1RaceSimulator
from src.strategy_engine.analyzer import StrategyAnalyzer

# Define race conditions
race_conditions = RaceConditions(
    lap=25,
    total_laps=58,
    weather=WeatherCondition.DRY,
    track_temp=45.0,
    air_temp=28.0,
    safety_car=False
)

# Define car state
car_state = CarState(
    position=5,
    tire_compound=TireCompound.MEDIUM,
    tire_age=12,
    fuel_load=45.0,
    lap_time=78.5,
    gap_to_leader=15.2,
    gap_to_next=2.8
)

# Run simulation
simulator = F1RaceSimulator()
analyzer = StrategyAnalyzer()

results = simulator.simulate_parallel(race_conditions, car_state, 1000)
recommendation = analyzer.analyze_and_recommend(
    race_conditions, car_state, results, 0.0
)

# Get results
print(recommendation.reasoning)
radio_msg = analyzer.generate_radio_message(recommendation)
print(f"📻 {radio_msg}")
```

## Common Scenarios

### Mid-Race Strategy Decision
```bash
python cli.py --lap 25 --total-laps 58 --position 5 --tire medium --tire-age 12
```

### Safety Car Opportunity
```bash
python cli.py --lap 30 --total-laps 58 --position 3 --tire soft --tire-age 8 --safety-car
```

### Weather Change
```bash
python cli.py --lap 15 --total-laps 58 --position 7 --tire medium --tire-age 5 --weather light_rain
```

### Late Race Push
```bash
python cli.py --lap 50 --total-laps 58 --position 2 --tire hard --tire-age 28
```

## Understanding the Output

### Strategy Recommendation Components

1. **Analysis**: Summary of current situation
   - Current lap/position
   - Tire state
   - Weather conditions
   - Optimal strategy type

2. **Optimal Strategy**: Best recommended approach
   - Expected finish position
   - Pit stop plan with lap numbers and compounds
   - Risk assessment
   - Fuel status

3. **Radio Message**: Concise driver communication
   - "Box this lap" or "Stay out"
   - Tire compound choice
   - Target position

4. **Alternative Strategies**: Backup options
   - Top 3-5 alternatives
   - Different pit windows
   - Risk/reward tradeoffs

### Risk Levels
- **Low (0-20%)**: Safe strategy
- **Moderate (20-50%)**: Some risk factors
- **High (50%+)**: Critical fuel or tire concerns

## Troubleshooting

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it or use different port
python -m uvicorn src.api.server:app --port 8001
```

### Import errors
```bash
# Make sure you're in the project root
cd /path/to/HackTX_KV
# Reinstall dependencies
pip install -r requirements.txt
```

### Slow simulations
```bash
# Reduce number of scenarios
python cli.py --scenarios 500 ...
```

## Next Steps

1. **Try the dashboard**: Most intuitive interface
2. **Experiment with CLI**: Quick testing
3. **Read ARCHITECTURE.md**: Understand the system
4. **Check API docs**: Integration options
5. **Run examples**: See different scenarios

## Support

For issues or questions:
- Check README.md for detailed documentation
- Review ARCHITECTURE.md for technical details
- See examples/ directory for code samples

---

**Ready to race! 🏎️💨**
