"""
FastAPI server for F1 Race Strategy System
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from typing import List
import json

from ..models.race_models import (
    SimulationRequest, StrategyRecommendation,
    RaceConditions, CarState, TireCompound, WeatherCondition
)
from ..hpc_simulator.simulator import F1RaceSimulator
from ..strategy_engine.analyzer import StrategyAnalyzer


app = FastAPI(
    title="F1 Race Strategy API",
    description="Real-time HPC-powered race strategy recommendations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
simulator = F1RaceSimulator()
analyzer = StrategyAnalyzer()

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "F1 Race Strategy System",
        "status": "operational",
        "message": "Real-time HPC-powered race strategy recommendations"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "simulator": "ready",
        "analyzer": "ready"
    }


@app.post("/api/strategy/recommend", response_model=StrategyRecommendation)
async def get_strategy_recommendation(request: SimulationRequest):
    """
    Get optimal race strategy recommendation based on current conditions
    
    This endpoint:
    1. Runs HPC simulations of thousands of race scenarios
    2. Analyzes results considering tire deg, fuel, and aero
    3. Returns optimal strategy with alternatives
    """
    try:
        start_time = time.time()
        
        # Run HPC simulations
        simulation_results = simulator.simulate_parallel(
            request.race_conditions,
            request.car_state,
            request.num_scenarios
        )
        
        computation_time_ms = (time.time() - start_time) * 1000
        
        # Analyze results and generate recommendations
        recommendation = analyzer.analyze_and_recommend(
            request.race_conditions,
            request.car_state,
            simulation_results,
            computation_time_ms
        )
        
        # Broadcast to WebSocket clients
        await broadcast_update(recommendation)
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy/radio-message")
async def get_radio_message(request: SimulationRequest):
    """
    Get concise radio message for driver communication
    """
    try:
        # Get recommendation
        simulation_results = simulator.simulate_parallel(
            request.race_conditions,
            request.car_state,
            min(500, request.num_scenarios)  # Faster for radio messages
        )
        
        computation_time_ms = 0
        recommendation = analyzer.analyze_and_recommend(
            request.race_conditions,
            request.car_state,
            simulation_results,
            computation_time_ms
        )
        
        # Generate radio message
        radio_message = analyzer.generate_radio_message(recommendation)
        
        return {
            "radio_message": radio_message,
            "optimal_strategy": recommendation.optimal_strategy,
            "computation_time_ms": computation_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/example/race-conditions")
async def get_example_race_conditions():
    """Get example race conditions for testing"""
    return {
        "race_conditions": {
            "lap": 25,
            "total_laps": 58,
            "weather": "dry",
            "track_temp": 45.0,
            "air_temp": 28.0,
            "safety_car": False
        },
        "car_state": {
            "position": 5,
            "tire_compound": "medium",
            "tire_age": 12,
            "fuel_load": 45.0,
            "lap_time": 78.5,
            "gap_to_leader": 15.2,
            "gap_to_next": 2.8
        }
    }


@app.websocket("/ws/strategy-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time strategy updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for keepalive
            await websocket.send_text(json.dumps({"status": "connected"}))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_update(recommendation: StrategyRecommendation):
    """Broadcast strategy update to all connected WebSocket clients"""
    message = {
        "type": "strategy_update",
        "data": recommendation.model_dump(mode='json')
    }
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(message))
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


# Mount static files for dashboard
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard():
        """Serve the dashboard HTML"""
        try:
            return FileResponse("static/dashboard.html")
        except:
            return HTMLResponse("<h1>Dashboard coming soon</h1>")
except:
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
