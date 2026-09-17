#!/usr/bin/env python3
import argparse
import copy
import json
import math
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
STATIC_ROOT = ROOT / "static"
DEFAULT_ROUTES = Path("/home/leidx/workspace/projects/Bench2Drive/leaderboard/data/bench2drive_0.0.4_val.xml")
DEFAULT_OUTPUT = Path("/home/leidx/workspace/outputs/bench2drive-zoo/eval")
DEFAULT_CARLA_MAPS = Path("/home/leidx/workspace/carla/CarlaUE4/Content/Carla/Maps")
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
CHANNELS = (
    "rgb_front",
    "rgb_front_left",
    "rgb_front_right",
    "rgb_back",
    "rgb_back_left",
    "rgb_back_right",
    "bev",
)
LANE_GRID_SIZE = 25.0


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def safe_child(root, relative):
    candidate = (root / relative).resolve()
    return candidate if candidate == root.resolve() or root.resolve() in candidate.parents else None


def route_summary(route):
    waypoints = route.find("waypoints")
    scenarios = route.find("scenarios")
    scenario_nodes = list(scenarios) if scenarios is not None else []
    return {
        "id": route.get("id", ""),
        "town": route.get("town", ""),
        "roadId": route.get("road_id", ""),
        "waypointCount": len(list(waypoints)) if waypoints is not None else 0,
        "scenarios": [node.get("type", node.get("name", "")) for node in scenario_nodes],
    }


class PlayerState:
    def __init__(self, routes_file, output_root, launch_script):
        self.routes_file = routes_file.resolve()
        self.output_root = output_root.resolve()
        self.launch_script = launch_script.resolve()
        self.jobs_root = self.output_root / ".player"
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.lane_build_lock = threading.Lock()
        self.map_cache = {}
        self.lane_cache = {}
        self.active = None
        self.jobs = {}
        self._load_jobs()

    def _load_jobs(self):
        for manifest in self.jobs_root.glob("*/run.json"):
            try:
                job = json.loads(manifest.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if job.get("status") in {"queued", "running", "finalizing"}:
                job["status"] = "interrupted"
                job["message"] = "播放器服务重启，无法确认原任务状态"
                self._write_job(job)
            self.jobs[job["id"]] = job

    def _write_job(self, job):
        job_dir = self.jobs_root / job["id"]
        job_dir.mkdir(parents=True, exist_ok=True)
        target = job_dir / "run.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2))
        temporary.replace(target)

    def list_routes(self):
        root = ET.parse(self.routes_file).getroot()
        return [route_summary(route) for route in root.findall("route")]

    def route_geometry(self, route_id):
        root = ET.parse(self.routes_file).getroot()
        route = next((node for node in root.findall("route") if node.get("id") == route_id), None)
        if route is None:
            raise ValueError("找不到指定预置路线")
        points = []
        waypoints = route.find("waypoints")
        for node in list(waypoints) if waypoints is not None else []:
            try:
                points.append([float(node.get(axis, "0")) for axis in ("x", "y", "z")])
            except ValueError:
                continue
        if len(points) < 2:
            raise ValueError("预置路线没有足够的路径点")
        return {
            "route": route_summary(route),
            "points": points,
            "map": self.town_map(route.get("town", "")),
        }

    def town_map(self, town):
        if not re.fullmatch(r"Town\d+(?:HD)?", town):
            raise ValueError("Town 名称非法")
        root = ET.parse(self.routes_file).getroot()
        route_points = []
        for route in root.findall("route"):
            if route.get("town") != town:
                continue
            waypoints = route.find("waypoints")
            for node in list(waypoints) if waypoints is not None else []:
                try:
                    point = [float(node.get(axis, "0")) for axis in ("x", "y", "z")]
                except ValueError:
                    continue
                route_points.append(point)
        if not route_points:
            raise ValueError("该 Town 没有可绘制路线")
        with self.lock:
            cached = self.map_cache.get(town)
        if cached:
            return cached
        polylines = self._opendrive_polylines(town)
        all_points = [point for line in polylines for point in line["points"]]
        xs = [point[0] for point in all_points]
        ys = [point[1] for point in all_points]
        result = {
            "town": town,
            "bounds": {"minX": min(xs), "maxX": max(xs), "minY": min(ys), "maxY": max(ys)},
            "polylines": polylines,
            "elevationPoints": route_points,
        }
        with self.lock:
            self.map_cache[town] = result
        threading.Thread(target=self._warm_lane_network, args=(town,), daemon=True).start()
        return result

    def _warm_lane_network(self, town):
        try:
            self._lane_network(town)
        except (OSError, ValueError, ET.ParseError) as error:
            print(f"WARNING: failed to prepare lane index for {town}: {error}")

    def _opendrive_polylines(self, town):
        candidates = [
            DEFAULT_CARLA_MAPS / "OpenDrive" / f"{town}.xodr",
            DEFAULT_CARLA_MAPS / town / "OpenDrive" / f"{town}.xodr",
        ]
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise ValueError(f"找不到 {town} 的 OpenDRIVE 地图")
        root = ET.parse(source).getroot()
        roads = []
        for road in root.findall("road"):
            points = []
            plan_view = road.find("planView")
            for geometry in list(plan_view) if plan_view is not None else []:
                points.extend(self._sample_geometry(geometry))
            if len(points) >= 2:
                roads.append({"roadId": road.get("id", ""), "points": points})
        if not roads:
            raise ValueError(f"{town} 的 OpenDRIVE 没有道路几何")
        return roads

    def validate_custom_route(self, town, points):
        if not re.fullmatch(r"Town\d+(?:HD)?", town) or not isinstance(points, list) or not points:
            raise ValueError("道路吸附需要有效 Town 和至少一个 waypoint")
        lanes, graph, grid, road_lanes = self._lane_network(town)
        snapped = []
        for index, point in enumerate(points):
            try:
                x, y = float(point["x"]), float(point["y"])
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"第 {index + 1} 个 waypoint 缺少有效 x、y") from None
            cell_x, cell_y = math.floor(x / LANE_GRID_SIZE), math.floor(y / LANE_GRID_SIZE)
            candidates = [lane for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                          for lane in grid.get((cell_x + dx, cell_y + dy), ())]
            if not candidates:
                candidates = lanes
            nearest = min(candidates, key=lambda lane: (lane["x"] - x) ** 2 + (lane["y"] - y) ** 2)
            distance = math.hypot(nearest["x"] - x, nearest["y"] - y)
            snapped.append({
                "x": nearest["x"], "y": nearest["y"], "z": nearest["z"],
                "roadId": nearest["roadId"], "sectionId": nearest["sectionId"],
                "laneId": nearest["laneId"], "distance": round(distance, 2),
            })
        segments = []
        valid = True
        path = []
        for index, (start, end) in enumerate(zip(snapped, snapped[1:])):
            road_path = self._road_path(start["roadId"], end["roadId"], graph)
            connected = bool(road_path)
            valid = valid and connected
            segments.append({"from": index, "to": index + 1, "connected": connected})
            if connected:
                segment_path = self._lane_curve_path(start, end, road_path, road_lanes)
                path.extend(segment_path[1:] if path and segment_path else segment_path)
        path_parts = self._split_continuous_path(path)
        return {"town": town, "valid": valid, "points": snapped, "segments": segments,
            "path": path, "pathParts": path_parts}

    def _lane_network(self, town):
        with self.lock:
            cached = self.lane_cache.get(town)
        if cached:
            return cached
        with self.lane_build_lock:
            with self.lock:
                cached = self.lane_cache.get(town)
            if cached:
                return cached
            result = self._build_lane_network(town)
            with self.lock:
                self.lane_cache[town] = result
            return result

    def _build_lane_network(self, town):
        root = ET.parse(self._opendrive_source(town)).getroot()
        samples, grid, road_lanes = [], {}, {}
        graph = {}
        roads = {road.get("id", ""): road for road in root.findall("road")}
        for road_id, road in roads.items():
            graph.setdefault(road_id, set())
            link = road.find("link")
            for tag in ("predecessor", "successor"):
                node = link.find(tag) if link is not None else None
                if node is not None and node.get("elementType") == "road" and node.get("elementId") in roads:
                    graph[road_id].add(node.get("elementId"))
                    graph.setdefault(node.get("elementId"), set()).add(road_id)
        for junction in root.findall("junction"):
            for connection in junction.findall("connection"):
                incoming, connecting = connection.get("incomingRoad"), connection.get("connectingRoad")
                if incoming in roads and connecting in roads:
                    graph[incoming].add(connecting)
                    graph[connecting].add(incoming)
        for road_id, road in roads.items():
            references = self._road_reference_samples(road)
            lanes_node = road.find("lanes")
            sections = list(lanes_node.findall("laneSection")) if lanes_node is not None else []
            if not sections:
                continue
            offsets = list(lanes_node.findall("laneOffset"))
            elevation_profile = road.find("elevationProfile")
            elevations = list(elevation_profile.findall("elevation")) if elevation_profile is not None else []
            for reference in references:
                section_index = max((i for i, node in enumerate(sections) if float(node.get("s", "0")) <= reference["s"]), default=0)
                section = sections[section_index]
                local_s = reference["s"] - float(section.get("s", "0"))
                base_offset = self._poly_value(offsets, reference["s"])
                for side_name, sign in (("left", 1), ("right", -1)):
                    side = section.find(side_name)
                    running = base_offset
                    lane_nodes = sorted(list(side) if side is not None else [], key=lambda node: abs(int(node.get("id", "0"))))
                    for lane in lane_nodes:
                        lane_id = int(lane.get("id", "0"))
                        width = self._poly_value(list(lane.findall("width")), local_s)
                        center_offset = running + sign * width / 2
                        running += sign * width
                        if lane.get("type") != "driving" or width <= 0:
                            continue
                        x = reference["x"] - math.sin(reference["heading"]) * center_offset
                        open_drive_y = reference["y"] + math.cos(reference["heading"]) * center_offset
                        sample = {"x": round(x, 2), "y": round(-open_drive_y, 2),
                                  "z": round(self._poly_value(elevations, reference["s"]), 2),
                                  "roadId": road_id, "sectionId": section_index, "laneId": lane_id,
                                  "s": round(reference["s"], 2)}
                        samples.append(sample)
                        road_lanes.setdefault(road_id, {}).setdefault((section_index, lane_id), []).append(sample)
                        cell = (math.floor(sample["x"] / LANE_GRID_SIZE), math.floor(sample["y"] / LANE_GRID_SIZE))
                        grid.setdefault(cell, []).append(sample)
        if not samples:
            raise ValueError(f"{town} 没有可吸附的 driving lane")
        return samples, graph, grid, road_lanes

    def _opendrive_source(self, town):
        candidates = [DEFAULT_CARLA_MAPS / "OpenDrive" / f"{town}.xodr",
                      DEFAULT_CARLA_MAPS / town / "OpenDrive" / f"{town}.xodr"]
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise ValueError(f"找不到 {town} 的 OpenDRIVE 地图")
        return source

    def _road_reference_samples(self, road):
        result = []
        plan_view = road.find("planView")
        for geometry in list(plan_view) if plan_view is not None else []:
            x, y = float(geometry.get("x", "0")), float(geometry.get("y", "0"))
            heading, length, start_s = (float(geometry.get(name, "0")) for name in ("hdg", "length", "s"))
            count = max(2, int(length / 4) + 1)
            child = next(iter(geometry), None)
            spiral_x, spiral_y, previous_distance = x, y, 0.0
            for index in range(count):
                distance = length * index / (count - 1)
                angle = heading
                if child is not None and child.tag == "arc" and abs(float(child.get("curvature", "0"))) > 1e-9:
                    curvature = float(child.get("curvature"))
                    px = x + (math.sin(heading + curvature * distance) - math.sin(heading)) / curvature
                    py = y - (math.cos(heading + curvature * distance) - math.cos(heading)) / curvature
                    angle += curvature * distance
                elif child is not None and child.tag == "spiral":
                    curvature_start = float(child.get("curvStart", "0"))
                    curvature_end = float(child.get("curvEnd", "0"))
                    step = distance - previous_distance
                    midpoint = (distance + previous_distance) / 2
                    midpoint_curvature = curvature_start + (curvature_end - curvature_start) * midpoint / max(length, 1e-9)
                    midpoint_angle = heading + curvature_start * midpoint + (curvature_end - curvature_start) * midpoint ** 2 / (2 * max(length, 1e-9))
                    spiral_x += step * math.cos(midpoint_angle)
                    spiral_y += step * math.sin(midpoint_angle)
                    px, py = spiral_x, spiral_y
                    angle += curvature_start * distance + (curvature_end - curvature_start) * distance ** 2 / (2 * max(length, 1e-9))
                    previous_distance = distance
                elif child is not None and child.tag in {"poly3", "paramPoly3"}:
                    normalized = child.tag == "paramPoly3" and child.get("pRange", "normalized") == "normalized"
                    parameter = distance / max(length, 1e-9) if normalized else distance
                    if child.tag == "poly3":
                        u = distance
                        v = sum(float(child.get(name, "0")) * u ** power for power, name in enumerate(("a", "b", "c", "d")))
                        du, dv = 1.0, sum(power * float(child.get(name, "0")) * u ** (power - 1) for power, name in enumerate(("a", "b", "c", "d")) if power)
                    else:
                        u = sum(float(child.get(name, "0")) * parameter ** power for power, name in enumerate(("aU", "bU", "cU", "dU")))
                        v = sum(float(child.get(name, "0")) * parameter ** power for power, name in enumerate(("aV", "bV", "cV", "dV")))
                        du = sum(power * float(child.get(name, "0")) * parameter ** (power - 1) for power, name in enumerate(("aU", "bU", "cU", "dU")) if power)
                        dv = sum(power * float(child.get(name, "0")) * parameter ** (power - 1) for power, name in enumerate(("aV", "bV", "cV", "dV")) if power)
                    px = x + u * math.cos(heading) - v * math.sin(heading)
                    py = y + u * math.sin(heading) + v * math.cos(heading)
                    angle += math.atan2(dv, du)
                else:
                    px, py = x + distance * math.cos(heading), y + distance * math.sin(heading)
                result.append({"x": px, "y": py, "heading": angle, "s": start_s + distance})
        return result

    @staticmethod
    def _poly_value(nodes, position):
        if not nodes:
            return 0.0
        eligible = [item for item in nodes if float(item.get("s", item.get("sOffset", "0"))) <= position]
        node = max(eligible, key=lambda item: float(item.get("s", item.get("sOffset", "0")))) if eligible else nodes[0]
        origin = float(node.get("s", node.get("sOffset", "0")))
        delta = position - origin
        return sum(float(node.get(name, "0")) * delta ** power for power, name in enumerate(("a", "b", "c", "d")))

    @staticmethod
    def _road_path(start, end, graph):
        if start == end:
            return [start]
        parents, pending = {start: None}, [start]
        while pending:
            current = pending.pop(0)
            for neighbor in graph.get(current, ()):
                if neighbor == end:
                    parents[neighbor] = current
                    path = [end]
                    while parents[path[-1]] is not None:
                        path.append(parents[path[-1]])
                    return list(reversed(path))
                if neighbor not in parents:
                    parents[neighbor] = current
                    pending.append(neighbor)
        return []

    @staticmethod
    def _lane_curve_path(start, end, road_path, road_lanes):
        result = []
        current = start
        for road_index, road_id in enumerate(road_path):
            curves = list(road_lanes.get(road_id, {}).values())
            if not curves:
                continue
            if road_index == 0:
                matching = [curve for key, curve in road_lanes[road_id].items()
                            if key == (start["sectionId"], start["laneId"])]
                if matching:
                    curves = matching
            curve = min(curves, key=lambda item: min((point["x"] - current["x"]) ** 2 +
                                                     (point["y"] - current["y"]) ** 2 for point in item))
            start_index = min(range(len(curve)), key=lambda i: (curve[i]["x"] - current["x"]) ** 2 +
                                                        (curve[i]["y"] - current["y"]) ** 2)
            if road_index == len(road_path) - 1:
                end_index = min(range(len(curve)), key=lambda i: (curve[i]["x"] - end["x"]) ** 2 +
                                                          (curve[i]["y"] - end["y"]) ** 2)
                step = 1 if end_index >= start_index else -1
                selected = curve[start_index:end_index + step:step]
            else:
                forward_gap = (curve[-1]["x"] - current["x"]) ** 2 + (curve[-1]["y"] - current["y"]) ** 2
                backward_gap = (curve[0]["x"] - current["x"]) ** 2 + (curve[0]["y"] - current["y"]) ** 2
                selected = curve[start_index:] if forward_gap >= backward_gap else list(reversed(curve[:start_index + 1]))
            if selected:
                result.extend([[point["x"], point["y"], point["z"]] for point in selected])
                current = selected[-1]
        if not result:
            return [[start["x"], start["y"], start["z"]], [end["x"], end["y"], end["z"]]]
        result[0] = [start["x"], start["y"], start["z"]]
        result[-1] = [end["x"], end["y"], end["z"]]
        return result

    @staticmethod
    def _split_continuous_path(path, max_gap=12.0):
        if not path:
            return []
        parts = [[path[0]]]
        for previous, point in zip(path, path[1:]):
            if math.hypot(point[0] - previous[0], point[1] - previous[1]) > max_gap:
                parts.append([point])
            else:
                parts[-1].append(point)
        return [part for part in parts if len(part) >= 2]

    @staticmethod
    def _sample_geometry(geometry):
        x = float(geometry.get("x", "0"))
        y = float(geometry.get("y", "0"))
        heading = float(geometry.get("hdg", "0"))
        length = float(geometry.get("length", "0"))
        count = max(2, int(length / 8) + 1)
        child = next(iter(geometry), None)
        points = []
        for index in range(count):
            distance = length * index / (count - 1)
            if child is not None and child.tag == "arc":
                curvature = float(child.get("curvature", "0"))
                if abs(curvature) > 1e-9:
                    px = x + (math.sin(heading + curvature * distance) - math.sin(heading)) / curvature
                    py = y - (math.cos(heading + curvature * distance) - math.cos(heading)) / curvature
                else:
                    px, py = x + distance * math.cos(heading), y + distance * math.sin(heading)
            else:
                px, py = x + distance * math.cos(heading), y + distance * math.sin(heading)
            points.append([round(px, 2), round(-py, 2)])
        return points

    def system_info(self):
        usage = shutil.disk_usage(self.output_root)
        return {
            "web": {"port": 8070, "purpose": "网页与播放器"},
            "carla": {"port": int(os.environ.get("CARLA_PORT", "30000")), "purpose": "CARLA RPC"},
            "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
            "routesFile": str(self.routes_file),
            "routeCount": len(self.list_routes()),
        }

    def list_trash(self):
        trash_root = self.output_root / ".trash"
        if not trash_root.exists():
            return []
        entries = []
        for path in trash_root.iterdir():
            if not path.is_dir() or path.name.startswith("manifest-"):
                continue
            entries.append({
                "id": path.name,
                "name": re.sub(r"-\d{8}-\d{6}$", "", path.name),
                "deletedAt": path.stat().st_mtime,
                "sizeBytes": self._directory_size(path),
            })
        return sorted(entries, key=lambda item: item["deletedAt"], reverse=True)

    def list_runs(self):
        with self.lock:
            jobs = [copy.deepcopy(job) for job in self.jobs.values()]
        known_names = {job["runName"] for job in jobs}
        for run_dir in self.output_root.iterdir():
            if not run_dir.is_dir() or run_dir.name.startswith(".") or run_dir.name in known_names:
                continue
            discovered = self._discover_run(run_dir)
            if discovered:
                jobs.append(discovered)
        return sorted(jobs, key=lambda job: job.get("createdAt", 0), reverse=True)

    def _discover_run(self, run_dir):
        sensor_root = run_dir / "sensors"
        route_dirs = [path for path in sensor_root.glob("*") if path.is_dir()]
        if not route_dirs:
            return None
        newest = max(route_dirs, key=lambda path: path.stat().st_mtime)
        frame_count = self._frame_count(newest)
        complete = self._checkpoint_complete(run_dir / "results.json")
        active = time.time() - self._latest_mtime(run_dir) < 120 and self._external_evaluator_running()
        return {
            "id": f"existing-{run_dir.name}",
            "runName": run_dir.name,
            "label": run_dir.name,
            "status": "ready" if complete and frame_count else "running" if active else "incomplete",
            "createdAt": run_dir.stat().st_mtime,
            "frameCount": frame_count,
            "routeDir": newest.name,
            "managed": False,
            "sizeBytes": self._directory_size(run_dir),
        }

    def create_job(self, payload):
        mode = payload.get("mode")
        if mode not in {"preset", "custom", "xml"}:
            raise ValueError("mode 必须是 preset、custom 或 xml")
        job_id = uuid.uuid4().hex[:12]
        run_name = f"player-{time.strftime('%Y%m%d-%H%M%S')}-{job_id[:4]}"
        job_dir = self.jobs_root / job_id
        job_dir.mkdir(parents=True)
        route_file = job_dir / "route.xml"
        label = self._write_route(mode, payload, route_file)
        job = {
            "id": job_id,
            "runName": run_name,
            "label": label,
            "mode": mode,
            "status": "queued",
            "message": "等待推理资源",
            "createdAt": time.time(),
            "routeFile": str(route_file),
            "managed": True,
        }
        with self.lock:
            if self.active:
                raise RuntimeError("已有播放器推理任务正在运行")
            if self._external_evaluator_running():
                raise RuntimeError("检测到现有 leaderboard_evaluator，当前任务结束后再启动")
            self.jobs[job_id] = job
            self.active = job_id
            self._write_job(job)
        threading.Thread(target=self._run_job, args=(job_id,), daemon=True).start()
        return copy.deepcopy(job)

    def _write_route(self, mode, payload, target):
        if mode == "preset":
            route_id = str(payload.get("routeId", ""))
            source_root = ET.parse(self.routes_file).getroot()
            selected = next((node for node in source_root.findall("route") if node.get("id") == route_id), None)
            if selected is None:
                raise ValueError("找不到指定预置路线")
            root = ET.Element("routes")
            root.append(copy.deepcopy(selected))
            label = f"{selected.get('town')} · Route {route_id}"
        elif mode == "custom":
            town = str(payload.get("town", "")).strip()
            points = payload.get("waypoints")
            if not isinstance(points, list) or len(points) < 2:
                raise ValueError("自定义路线需要至少两个 waypoint")
            validation = self.validate_custom_route(town, points)
            if not validation["valid"]:
                raise ValueError("自定义路线包含道路网络不连通的分段")
            root = ET.Element("routes")
            route = ET.SubElement(root, "route", id=str(int(time.time())), town=town)
            waypoints = ET.SubElement(route, "waypoints")
            for point in validation["points"]:
                values = {axis: str(point[axis]) for axis in ("x", "y", "z")}
                ET.SubElement(waypoints, "position", **values)
            ET.SubElement(route, "scenarios")
            weathers = ET.SubElement(route, "weathers")
            ET.SubElement(weathers, "weather", route_percentage="0", cloudiness="0", precipitation="0", precipitation_deposits="0", wind_intensity="0", sun_azimuth_angle="0", sun_altitude_angle="70", fog_density="0", wetness="0")
            label = f"{town} · 自定义路线"
        else:
            xml_text = payload.get("xml")
            if not isinstance(xml_text, str) or len(xml_text) > 2_000_000:
                raise ValueError("XML 为空或超过 2 MB")
            root = ET.fromstring(xml_text)
            if root.tag != "routes" or len(root.findall("route")) != 1:
                raise ValueError("XML 必须包含一个 routes 根节点和一条 route")
            route = root.find("route")
            if route is None or route.find("waypoints") is None:
                raise ValueError("route 缺少 waypoints")
            label = f"{route.get('town', 'Unknown')} · 导入路线 {route.get('id', '')}"
        ET.indent(root)
        ET.ElementTree(root).write(target, encoding="utf-8", xml_declaration=True)
        return label

    def _run_job(self, job_id):
        with self.lock:
            job = self.jobs[job_id]
            job.update(status="running", message="CARLA 与 VAD 推理中", startedAt=time.time())
            self._write_job(job)
        job_dir = self.jobs_root / job_id
        log_file = job_dir / "inference.log"
        environment = os.environ.copy()
        environment.update(ROUTES=job["routeFile"], RUN_NAME=job["runName"])
        try:
            with log_file.open("wb") as stream:
                process = subprocess.Popen(
                    [str(self.launch_script)], cwd=REPO_ROOT, env=environment,
                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True,
                )
                with self.lock:
                    job["pid"] = process.pid
                    self._write_job(job)
                return_code = process.wait()
            with self.lock:
                job.update(status="finalizing", message="检查推理产物", returnCode=return_code)
                self._write_job(job)
            self._finalize(job)
        except Exception as error:
            with self.lock:
                job.update(status="failed", message=str(error), finishedAt=time.time())
                self._write_job(job)
        finally:
            with self.lock:
                self.active = None

    def _finalize(self, job):
        run_dir = self.output_root / job["runName"]
        route_dirs = [path for path in (run_dir / "sensors").glob("*") if path.is_dir()]
        route_dir = max(route_dirs, key=lambda path: path.stat().st_mtime) if route_dirs else None
        frame_count = self._frame_count(route_dir) if route_dir else 0
        status = "ready" if job.get("returnCode") == 0 and frame_count else "failed"
        message = "推理完成，可以播放" if status == "ready" else "推理未生成完整可播放结果"
        with self.lock:
            job.update(
                status=status,
                message=message,
                finishedAt=time.time(),
                frameCount=frame_count,
                routeDir=route_dir.name if route_dir else None,
                sizeBytes=self._directory_size(run_dir),
            )
            self._write_job(job)

    def stop_job(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or job.get("status") != "running" or not job.get("pid"):
                raise ValueError("任务不在运行")
            os.killpg(job["pid"], signal.SIGTERM)
            job["message"] = "正在停止"
            self._write_job(job)

    def delete_run(self, run_id):
        with self.lock:
            job = self.jobs.get(run_id)
            if job and job.get("status") in {"queued", "running", "finalizing"}:
                raise RuntimeError("运行中的任务不能删除")
        if job:
            run_name = job["runName"]
        elif run_id.startswith("existing-"):
            run_name = run_id.removeprefix("existing-")
            discovered = next((item for item in self.list_runs() if item["id"] == run_id), None)
            if not discovered:
                raise ValueError("找不到运行记录")
            if discovered.get("status") == "running":
                raise RuntimeError("运行中的任务不能删除")
            if discovered.get("status") == "incomplete" and self._external_evaluator_running():
                raise RuntimeError("检测到外部评测进程，暂不允许删除未完成结果")
        else:
            raise ValueError("找不到运行记录")
        if not SAFE_ID.fullmatch(run_name):
            raise ValueError("运行名称非法")
        run_dir = safe_child(self.output_root, run_name)
        trash_root = self.output_root / ".trash"
        trash_root.mkdir(exist_ok=True)
        trash_name = f"{run_name}-{time.strftime('%Y%m%d-%H%M%S')}"
        trash_dir = safe_child(trash_root, trash_name)
        if run_dir and run_dir.is_dir():
            run_dir.replace(trash_dir)
        if job:
            manifest_dir = self.jobs_root / run_id
            if manifest_dir.is_dir():
                manifest_dir.replace(trash_root / f"manifest-{run_id}-{int(time.time())}")
            with self.lock:
                self.jobs.pop(run_id, None)
        return str(trash_dir) if trash_dir else None

    def restore_trash(self, trash_id):
        source = self._trash_item(trash_id)
        name = re.sub(r"-\d{8}-\d{6}$", "", trash_id)
        if not SAFE_ID.fullmatch(name):
            raise ValueError("回收站条目名称非法")
        destination = safe_child(self.output_root, name)
        if not destination or destination.exists():
            raise RuntimeError("原位置已存在同名结果，无法恢复")
        source.replace(destination)
        return str(destination)

    def purge_trash(self, trash_id):
        source = self._trash_item(trash_id)
        shutil.rmtree(source)

    def _trash_item(self, trash_id):
        if not SAFE_ID.fullmatch(trash_id):
            raise ValueError("回收站条目非法")
        trash_root = self.output_root / ".trash"
        source = safe_child(trash_root, trash_id)
        if not source or not source.is_dir() or source.name.startswith("manifest-"):
            raise ValueError("找不到回收站条目")
        return source

    def playback_index(self, run_id):
        job, route_dir, run_dir = self._resolve_run(run_id)
        if job.get("status") != "ready":
            raise ValueError("该任务尚未完成，不能播放")
        frame_count = self._frame_count(route_dir)
        result = self._result_record(run_dir / "results.json")
        return {
            "id": run_id,
            "label": job.get("label", job["runName"]),
            "frameCount": frame_count,
            "fps": 2,
            "channels": list(CHANNELS),
            "result": result,
        }

    def playback_file(self, run_id, relative):
        _, route_dir, _ = self._resolve_run(run_id)
        target = safe_child(route_dir, relative)
        if not target or not target.is_file():
            raise FileNotFoundError(relative)
        return target

    def _resolve_run(self, run_id):
        jobs = {job["id"]: job for job in self.list_runs()}
        job = jobs.get(run_id)
        if not job:
            raise ValueError("找不到运行记录")
        run_dir = self.output_root / job["runName"]
        route_name = job.get("routeDir")
        route_dir = safe_child(run_dir / "sensors", route_name or "")
        if not route_dir or not route_dir.is_dir():
            raise ValueError("找不到路线产物")
        return job, route_dir, run_dir

    @staticmethod
    def _frame_count(route_dir):
        if not route_dir:
            return 0
        sets = []
        for channel in (*CHANNELS, "meta"):
            suffix = ".json" if channel == "meta" else ".png"
            sets.append({path.stem for path in (route_dir / channel).glob(f"*{suffix}")})
        return len(set.intersection(*sets)) if sets and all(sets) else 0

    @staticmethod
    def _directory_size(path):
        if not path.exists():
            return 0
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())

    @staticmethod
    def _latest_mtime(path):
        mtimes = [item.stat().st_mtime for item in path.rglob("*") if item.is_file()]
        return max(mtimes, default=path.stat().st_mtime)

    @staticmethod
    def _result_record(path):
        try:
            records = json.loads(path.read_text()).get("_checkpoint", {}).get("records", [])
            return records[-1] if records else None
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _checkpoint_complete(path):
        try:
            progress = json.loads(path.read_text()).get("_checkpoint", {}).get("progress", [])
            return len(progress) == 2 and int(progress[0]) >= int(progress[1]) > 0
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False

    @staticmethod
    def _external_evaluator_running():
        result = subprocess.run(["pgrep", "-f", "[l]eaderboard_evaluator.py"], capture_output=True)
        return result.returncode == 0


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    state = None

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/routes":
                return self.send_json({"routes": self.state.list_routes()})
            match = re.fullmatch(r"/api/routes/([^/]+)/geometry", path)
            if match:
                return self.send_json(self.state.route_geometry(match.group(1)))
            if path == "/api/runs":
                return self.send_json({"runs": self.state.list_runs()})
            if path == "/api/system":
                return self.send_json(self.state.system_info())
            if path == "/api/trash":
                return self.send_json({"trash": self.state.list_trash()})
            match = re.fullmatch(r"/api/maps/(Town\d+(?:HD)?)", path)
            if match:
                return self.send_json(self.state.town_map(match.group(1)))
            match = re.fullmatch(r"/api/runs/([^/]+)/index", path)
            if match:
                return self.send_json(self.state.playback_index(match.group(1)), cache="no-store")
            match = re.fullmatch(r"/api/runs/([^/]+)/frame/(\d+)\.json", path)
            if match:
                frame = f"{int(match.group(2)):04d}.json"
                return self.send_file(self.state.playback_file(match.group(1), f"meta/{frame}"), "no-store")
            match = re.fullmatch(r"/api/runs/([^/]+)/image/([a-z_]+)/(\d+)\.png", path)
            if match and match.group(2) in CHANNELS:
                frame = f"{int(match.group(3)):04d}.png"
                return self.send_file(self.state.playback_file(match.group(1), f"{match.group(2)}/{frame}"), "public, max-age=31536000, immutable")
            return self.send_static(path)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, OSError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_HEAD(self):
        path = unquote(urlparse(self.path).path)
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = safe_child(STATIC_ROOT, relative)
        if not target or not target.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(target.stat().st_size))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/runs":
                return self.send_json(self.state.create_job(payload), HTTPStatus.CREATED)
            if path == "/api/routes/validate-custom":
                return self.send_json(self.state.validate_custom_route(str(payload.get("town", "")), payload.get("waypoints")))
            match = re.fullmatch(r"/api/runs/([^/]+)/stop", path)
            if match:
                self.state.stop_job(match.group(1))
                return self.send_json({"ok": True})
            match = re.fullmatch(r"/api/trash/([^/]+)/restore", path)
            if match:
                restored_path = self.state.restore_trash(match.group(1))
                return self.send_json({"ok": True, "restoredPath": restored_path})
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError, ET.ParseError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.CONFLICT)

    def do_DELETE(self):
        path = urlparse(self.path).path
        try:
            run_match = re.fullmatch(r"/api/runs/([^/]+)", path)
            if run_match:
                trash_path = self.state.delete_run(run_match.group(1))
                return self.send_json({"ok": True, "trashPath": trash_path})
            trash_match = re.fullmatch(r"/api/trash/([^/]+)", path)
            if trash_match:
                self.state.purge_trash(trash_match.group(1))
                return self.send_json({"ok": True})
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError, OSError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.CONFLICT)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_100_000:
            raise ValueError("请求体过大")
        return json.loads(self.rfile.read(length) or b"{}")

    def send_json(self, value, status=HTTPStatus.OK, cache="no-store"):
        self.send_body(json_bytes(value), "application/json; charset=utf-8", status, cache)

    def send_file(self, path, cache):
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_body(body, content_type, HTTPStatus.OK, cache)

    def send_static(self, path):
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = safe_child(STATIC_ROOT, relative)
        if not target or not target.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        self.send_file(target, "no-cache")

    def send_body(self, body, content_type, status, cache):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Bench2Drive PNG + JSON result player")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8070, type=int)
    parser.add_argument("--routes", type=Path, default=DEFAULT_ROUTES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--launch-script", type=Path, default=REPO_ROOT / "scripts/run_vad_simulation.sh")
    args = parser.parse_args()
    for path in (args.routes, args.launch_script):
        if not path.exists():
            parser.error(f"找不到 {path}")
    Handler.state = PlayerState(args.routes, args.output, args.launch_script)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Bench2Drive player: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()