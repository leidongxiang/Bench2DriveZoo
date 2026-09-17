#!/usr/bin/env python3
"""Publish read-only progress snapshots for the currently running player server."""

import argparse
import fcntl
import json
import math
import os
import re
import time
from pathlib import Path

ACTIVE = {"queued", "running", "finalizing"}
STEP_RE = re.compile(rb'"(\d+)":\s*\{')
LOCATION_RE = re.compile(rb'"location":\s*(\[[^\]]+\])')


def latest_location(path):
    """Read only the tail of metric_info.json after the initial full scan."""
    try:
        with path.open("rb") as stream:
            size = path.stat().st_size
            stream.seek(max(0, size - 8192))
            tail = stream.read()
        if path.stat().st_size != size:
            return None
        locations = list(LOCATION_RE.finditer(tail))
        if not locations:
            return None
        match = locations[-1]
        steps = list(STEP_RE.finditer(tail, 0, match.start()))
        if not steps:
            return None
        point = json.loads(match.group(1))
        if len(point) != 3:
            return None
        return int(steps[-1].group(1)), point
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def initial_distance(path):
    try:
        data = json.loads(path.read_text())
        samples = sorted((int(step), value["location"]) for step, value in data.items()
                         if isinstance(value, dict) and "location" in value)
        if not samples:
            return None
        distance = sum(math.dist(first[1], second[1]) for first, second in zip(samples, samples[1:]))
        return {"step": samples[-1][0], "location": samples[-1][1], "distance": distance}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def collect(output_root, distances):
    runs = {}
    for manifest in (output_root / ".player").glob("*/run.json"):
        try:
            job = json.loads(manifest.read_text())
            if job.get("status") not in ACTIVE:
                continue
            run_id, run_name = job["id"], job["runName"]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id) or not re.fullmatch(r"[A-Za-z0-9_.-]+", run_name):
                continue
            sensor_root = output_root / run_name / "sensors"
            route_dirs = [path for path in sensor_root.glob("*") if path.is_dir()]
            route_dir = max(route_dirs, key=lambda path: path.stat().st_mtime) if route_dirs else None
            frame_count = sum(1 for _ in (route_dir / "meta").glob("*.json")) if route_dir else 0
            entry = {"frameCount": frame_count, "simSeconds": max(0, (frame_count - 1) / 2)}
            if route_dir:
                metric = route_dir / "metric_info.json"
                cached = distances.get(run_id)
                if cached is None and metric.exists():
                    cached = initial_distance(metric)
                elif cached is not None:
                    current = latest_location(metric)
                    if current and current[0] > cached["step"]:
                        cached["distance"] += math.dist(cached["location"], current[1])
                        cached["step"], cached["location"] = current
                if cached is not None:
                    distances[run_id] = cached
                    entry["distanceMeters"] = round(cached["distance"])
            runs[run_id] = entry
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    for run_id in set(distances) - set(runs):
        distances.pop(run_id, None)
    return {"updatedAt": time.time(), "runs": runs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--static", required=True, type=Path)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.static.mkdir(parents=True, exist_ok=True)
    lock_path = args.output / ".player" / "progress.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        distances = {}
        target = args.static / "progress.json"
        while True:
            payload = collect(args.output, distances)
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            os.replace(temporary, target)
            if args.once:
                return
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
