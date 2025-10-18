"""
Data models for F1 race strategy system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class TireCompound(str, Enum):
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"
    WET = "wet"


class WeatherCondition(str, Enum):
    DRY = "dry"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"


class RaceConditions(BaseModel):
    """Current race conditions"""
    lap: int = Field(..., description="Current lap number")
    total_laps: int = Field(..., description="Total race laps")
    weather: WeatherCondition = Field(default=WeatherCondition.DRY)
    track_temp: float = Field(..., description="Track temperature in Celsius")
    air_temp: float = Field(..., description="Air temperature in Celsius")
    safety_car: bool = Field(default=False, description="Is safety car deployed")


class CarState(BaseModel):
    """Current state of the car"""
    position: int = Field(..., description="Current position in race")
    tire_compound: TireCompound
    tire_age: int = Field(..., description="Tire age in laps")
    fuel_load: float = Field(..., description="Current fuel in kg")
    lap_time: float = Field(..., description="Last lap time in seconds")
    gap_to_leader: float = Field(..., description="Gap to leader in seconds")
    gap_to_next: float = Field(..., description="Gap to car ahead in seconds")


class PitStopStrategy(BaseModel):
    """Pit stop strategy recommendation"""
    lap: int = Field(..., description="Recommended pit stop lap")
    tire_compound: TireCompound
    expected_position_after_stop: int
    expected_time_loss: float = Field(..., description="Expected time loss in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class SimulationScenario(BaseModel):
    """A single race scenario for simulation"""
    scenario_id: str
    pit_stops: List[PitStopStrategy]
    estimated_finish_position: int
    estimated_race_time: float = Field(..., description="Estimated race time in seconds")
    fuel_critical: bool = Field(default=False)
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment")


class StrategyRecommendation(BaseModel):
    """Final strategy recommendation with multiple scenarios"""
    current_conditions: RaceConditions
    car_state: CarState
    optimal_strategy: SimulationScenario
    alternative_strategies: List[SimulationScenario]
    reasoning: str = Field(..., description="Human-readable explanation")
    computation_time_ms: float = Field(..., description="Time taken for computation")


class SimulationRequest(BaseModel):
    """Request for running race simulations"""
    race_conditions: RaceConditions
    car_state: CarState
    competitor_positions: List[int] = Field(default_factory=list)
    num_scenarios: int = Field(default=1000, description="Number of scenarios to simulate")
