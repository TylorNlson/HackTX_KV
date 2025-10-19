# build_track_from_baseline.py
# Usage:
#   python build_track_from_baseline.py --tracks track_configs.json --baseline baseline_configs.json --out track_configs.updated.json

import json
import argparse
from collections import defaultdict
import numpy as np

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compute_avg_times(baselines):
    """
    baselines: list of dicts with keys: track_id, baseline_lap_time_ms
    Returns dict: track_id -> avg_lap_time_ms
    """
    times = defaultdict(list)
    for b in baselines:
        tid = b.get("track_id")
        t = b.get("baseline_lap_time_ms")
        if tid is not None and t is not None:
            try:
                times[tid].append(float(t))
            except ValueError:
                pass

    avg_times = {tid: float(np.mean(vals)) for tid, vals in times.items() if vals}
    return avg_times

def merge_into_tracks(tracks, avg_times):
    out = []
    for t in tracks:
        tid = t.get("id")
        avg_ms = avg_times.get(tid)
        t2 = dict(t)
        if avg_ms:
            t2["avg_lap_time_ms"] = int(round(avg_ms))
            t2["avg_lap_time_s"] = round(avg_ms / 1000.0, 3)
            t2["avg_lap_time_source"] = "baseline_configs.json average"
        else:
            t2["avg_lap_time_source"] = "no baseline data"
        out.append(t2)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracks", required=True, help="path to track_configs.json")
    parser.add_argument("--baseline", required=True, help="path to baseline_configs.json")
    parser.add_argument("--out", required=True, help="output path for updated track configs")
    args = parser.parse_args()

    tracks = load_json(args.tracks)
    baselines = load_json(args.baseline)
    avg_times = compute_avg_times(baselines)
    merged = merge_into_tracks(tracks, avg_times)
    save_json(args.out, merged)

    print(f"✅ Done. Wrote {args.out}")
    print(f"   Found averages for {len(avg_times)} tracks out of {len(tracks)} total.")

if __name__ == "__main__":
    main()
