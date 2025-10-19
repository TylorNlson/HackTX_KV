from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import F1_Simulation

from fastapi.middleware.cors import CORSMiddleware

# --- FastAPI App ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, etc.
    allow_headers=["*"],
)

class SimInput(BaseModel):
    track_id: str
    driver_mass: float
    car_mass: float
    max_power: float
    downforce: float
    drag: float
    reliability: float
    mileage: float
    # front_wing_angle: float
    # rear_wing_angle: float
    # air_roll_balance: float
    # front_spring_rate: float
    # rear_spring_rate: float
    # tire_preasure_front: float
    # tire_preasure_back: float
    runs: int = 5000

@app.post("/simulate")
def simulate(data: SimInput):
    result = F1_Simulation.main(
        data.track_id,
        data.driver_mass,
        data.car_mass,
        data.max_power,
        data.downforce,
        data.drag,
        data.reliability,
        data.mileage,
        # data.front_wing_angle,
        # data.rear_wing_angle,
        # data.air_roll_balance,
        # data.front_spring_rate,
        # data.rear_spring_rate,
        # data.tire_preasure_front,
        # data.tire_preasure_back,
        data.runs)
    return {"status": "ok", "result": result}

# For running backend independently:
if __name__ == "__main__":
    uvicorn.run("backend.src.api:app", host="127.0.0.1", port=8000, reload=True)
