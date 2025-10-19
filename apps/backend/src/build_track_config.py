import json
from statistics import mean


def generate_track_config(circuits, qualifying_results, race_results, practice_results, pit_stops, race_metadata):
    track_configs = []

    for circuit in circuits:
        track_id = circuit["id"]
        race_to_circuit = {race['id']: race['circuitId'] for race in race_metadata}

        # Filter laps for this circuit
        laps_ms = []
        for results in [qualifying_results, race_results, practice_results]:
            for lap in results:
                if lap["raceId"] == track_id or lap.get("circuitId") == track_id:
                    if lap["timeMillis"]:
                        laps_ms.append(lap["timeMillis"])

        avg_lap_time_ms = int(mean(laps_ms)) if laps_ms else None

        # Simplified estimations
        #pit_stop_time_s = 22  # generic average
        tire_stress = 0.85 if circuit["type"] == "STREET" else 0.7
        fuel_usage_per_lap_l = circuit["length"] * 0.7  # roughly liters per km
        overtaking_difficulty = 0.9 if circuit["type"] == "STREET" else 0.5

        track_pit_stops = [ps for ps in pit_stops if race_to_circuit.get(ps['raceId']) == track_id and ps['timeMillis'] is not None]
        avg_pit_time_s = (sum(ps['timeMillis'] for ps in track_pit_stops) / len(
            track_pit_stops) / 1000) if track_pit_stops else 22
        print(sum(ps['timeMillis'] for ps in track_pit_stops))

        track_configs.append({
            "id": track_id,
            "name": circuit["name"],
            "fullName": circuit["fullName"],
            "type": circuit["type"],
            "direction": circuit["direction"],
            "length_km": circuit["length"],
            "num_turns": circuit["turns"],
            "avg_lap_time_ms": avg_lap_time_ms,
            "pit_stop_time_s": avg_pit_time_s,
            "tire_stress": tire_stress,
            "fuel_usage_per_lap_l": fuel_usage_per_lap_l,
            "overtaking_difficulty": overtaking_difficulty
        })

    return track_configs

def extract_configs(races, circuits, race_results, fastest_laps, engines):
    tracks = []
    cars = []
    baselines = []

    for race in races:
        # --- Track Info ---
        circuit = next((c for c in circuits if c["id"] == race["circuitId"]), None)
        if not circuit:
            continue

        track_info = {
            "track_id": circuit["id"],
            "name": circuit["name"],
            "type": circuit["type"],
            "direction": circuit["direction"],
            "length_km": circuit["length"],
            "turns": circuit["turns"],
            "laps": race.get("laps"),
            "total_distance_km": race.get("distance"),
            "country": circuit.get("countryId")
        }
        tracks.append(track_info)

        # --- Car + Lap Time Info ---
        results = [r for r in race_results if r["raceId"] == race["id"]]
        for res in results:
            engine = next((e for e in engines if e["engineManufacturerId"] == res["engineManufacturerId"]), None)
            car_info = {
                "car_id": f"{res['constructorId']}_{res['driverId']}_{race['year']}",
                "constructor": res["constructorId"],
                "driver": res["driverId"],
                "engine": engine["name"] if engine else res["engineManufacturerId"],
                "tyres": res["tyreManufacturerId"],
                "race_id": race["id"],
                "year": race["year"]
            }
            cars.append(car_info)

            # --- Baseline Lap Time ---
            fastest = next(
                (f for f in fastest_laps if f["raceId"] == race["id"] and f["driverId"] == res["driverId"]),
                None
            )
            if fastest and fastest.get("timeMillis"):
                baselines.append({
                    "race_id": race["id"],
                    "track_id": circuit["id"],
                    "car_id": car_info["car_id"],
                    "baseline_lap_time_ms": fastest["timeMillis"]
                })

    return {
        "tracks": tracks,
        "cars": cars,
        "baselines": baselines
    }


# Example usage
with open("./data/circuits.json") as f:
    circuits = json.load(f)

with open("./data/qualifying-results.json") as f:
    qualifying_results = json.load(f)

with open("./data/race-results.json") as f:
    race_results = json.load(f)

with open("./data/practice-4-results.json") as f:
    practice_results = json.load(f)

with open("./data/pit-stops.json") as f:
    pit_stops = json.load(f)

with open("./data/races.json") as f:
    race_metadata = json.load(f)

with open("./data/fastest-laps.json") as f:
    fastest_laps = json.load(f)

with open("./data/engines.json") as f:
    engine_metadata = json.load(f)

#track_configs = generate_track_config(circuits, qualifying_results, race_results, practice_results, pit_stops, race_metadata)
track_configs = extract_configs(race_metadata, circuits, race_results, fastest_laps, engine_metadata)

with open("./data/track_configs_2.json", "w") as f:
    json.dump(track_configs["tracks"], f, indent=2)

with open("./data/car_configs.json", "w") as f:
    json.dump(track_configs["cars"], f, indent=2)

with open("./data/baseline_configs.json", "w") as f:
    json.dump(track_configs["baselines"], f, indent=2)
