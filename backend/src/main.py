
import numpy as np

def run_trial(config, rng):
    # Unpack key variables
    env = config["environment"]
    car = config["car_setup"]
    strat = config["strategy"]
    phys = config["physics_constants"]

    L = env["L"]
    laps = env["race_laps"]
    grip = env["grip"]

    downforce = car["downforce"]
    fuel = car["fuel_start"]
    compound = car["tire_compound"]
    pit_laps = set(strat["pit_laps"])

    # Constants
    base_wear_rate = {
        "soft": phys["base_wear_rate_soft"],
        "medium": phys["base_wear_rate_medium"],
        "hard": phys["base_wear_rate_hard"]
    }[compound]

    bonus = phys["compound_speed_bonus"][compound]

    # State variables
    tire_wear = 0.0
    total_time = 0.0
    pit_count = 0
    DNF = False

    for lap in range(1, laps + 1):
        # --- Fuel burn & wear update ---
        fuel -= phys["burn_rate_base"]
        fuel_fraction = max(fuel / phys["fuel_ref"], 0)

        tire_wear += base_wear_rate * (1.0 + rng.normal(0, 0.05))
        tire_wear = min(tire_wear, 1.0)

        # --- Lap time model ---
        tau = (
            phys["tau0"]
            + phys["k_fuel"] * fuel_fraction
            + phys["k_wear"] * tire_wear
            + phys["k_downforce"] * (1.0 - downforce)
            + bonus
        ) / grip

        # Small random noise
        tau += rng.normal(0, phys["lap_time_noise_sigma"])

        total_time += tau

        # --- DNF check ---
        p_fail = phys["DNF_base_prob"] * (1 + phys["alpha_wear"] * tire_wear)
        if rng.random() < p_fail:
            DNF = True
            break

        # --- Pit stop logic ---
        if lap in pit_laps:
            total_time += phys["pit_delta"]
            pit_count += 1
            tire_wear = 0.0  # new tires

    return {
        "total_time": total_time,
        "DNF": DNF,
        "pit_count": pit_count
    }


config = {
    "environment": {
        "track": "Silverstone",
        "L": 5.891,               # km
        "race_laps": 52,
        "T_track": 35,            # °C
        "weather": "dry",
        "grip": 1.0
    },

    "car_setup": {
        "downforce": 0.78,        # aerodynamic setup [0–1]
        "fuel_start": 110,        # kg
        "fuel_capacity": 110,
        "tire_compound": "medium" # soft | medium | hard
    },

    "strategy": {
        "pit_laps": [18, 38]      # planned stops
    },

    "physics_constants": {
        "tau0": 75.0,             # baseline lap time [s]
        "burn_rate_base": 1.6,    # kg/lap
        "k_fuel": 1.2,            # s per fuel_fraction
        "k_wear": 5.0,            # s per wear_fraction
        "k_downforce": 2.0,       # s per (1 - downforce)
        "base_wear_rate_soft": 0.02,
        "base_wear_rate_medium": 0.01,
        "base_wear_rate_hard": 0.005,
        "compound_speed_bonus": {
            "soft": -0.8,
            "medium": 0.0,
            "hard": +0.6
        },
        "pit_delta": 21.0,        # total pit time lost [s]
        "fuel_ref": 110,          # normalization
        "DNF_base_prob": 0.0005,  # per-lap
        "alpha_wear": 3.0,        # failure multiplier per wear
        "lap_time_noise_sigma": 0.25
    }
}

# Optional RNG for testing:
rng = np.random.default_rng()

print(run_trial(config, rng))