"""Project VAD detections and CARLA actors onto saved player frames."""

import numpy as np


CAMERAS = {
    "CAM_FRONT_LEFT": "rgb_front_left",
    "CAM_FRONT": "rgb_front",
    "CAM_FRONT_RIGHT": "rgb_front_right",
    "CAM_BACK_LEFT": "rgb_back_left",
    "CAM_BACK": "rgb_back",
    "CAM_BACK_RIGHT": "rgb_back_right",
}


def _project_box(corners, matrix, width, height):
    points = np.concatenate((corners, np.ones((len(corners), 1))), axis=1)
    projected = points @ matrix.T
    if np.any(projected[:, 2] <= 0.1):
        return None
    xy = projected[:, :2] / projected[:, 2:3]
    if not np.isfinite(xy).all():
        return None
    left, top = xy.min(axis=0)
    right, bottom = xy.max(axis=0)
    if right <= 0 or bottom <= 0 or left >= width or top >= height:
        return None
    box = [max(0, left), max(0, top), min(width, right), min(height, bottom)]
    if box[2] - box[0] < 3 or box[3] - box[1] < 3:
        return None
    return {"box": [round(float(value), 1) for value in box],
            "corners": [round(float(value), 1) for value in xy.reshape(-1)]}


def _ordered_corners(corners):
    """Put the four lower corners first, then their matching upper corners."""
    lower_indices = np.argsort(corners[:, 2])[:4]
    lower = corners[lower_indices]
    center = lower[:, :2].mean(axis=0)
    lower = lower[np.argsort(np.arctan2(lower[:, 1] - center[1],
                                       lower[:, 0] - center[0]))]
    upper = corners[np.argsort(corners[:, 2])[4:]]
    remaining = list(range(4))
    matched = []
    for point in lower:
        nearest = min(remaining, key=lambda index: np.linalg.norm(
            upper[index, :2] - point[:2]))
        matched.append(upper[nearest])
        remaining.remove(nearest)
    return np.concatenate((lower, np.asarray(matched)))


def _actor_label(type_id):
    if type_id.startswith("walker.pedestrian"):
        return "pedestrian"
    if not type_id.startswith("vehicle."):
        return None
    if any(word in type_id for word in ("bike", "bicycle", "motorcycle")):
        return "bicycle"
    if any(word in type_id for word in ("truck", "firetruck", "bus")):
        return "truck"
    if "van" in type_id:
        return "van"
    return "car"


def build_overlays(pts_bbox, actors, hero_id, world_to_ego, lidar2ego,
                   lidar2img, coor2topdown, class_names):
    """Return clipped pixel boxes. All prediction corners are in LiDAR coordinates."""
    output = {"cameras": {name: {"pred": [], "gt": []} for name in CAMERAS.values()},
              "bev": {"pred": [], "gt": []}, "map": [],
              "vectorBev": True, "actorCount": len(actors)}
    lidar_to_bev = np.asarray(coor2topdown) @ np.asarray(lidar2ego)

    def add(kind, corners, label, score=None, traj=None):
        if not np.isfinite(corners).all():
            return
        corners = _ordered_corners(corners)
        for camera, channel in CAMERAS.items():
            projected = _project_box(corners, np.asarray(lidar2img[camera]), 1600, 900)
            if projected is not None:
                entry = {**projected, "label": label}
                if score is not None:
                    entry["score"] = round(float(score), 3)
                output["cameras"][channel][kind].append(entry)
        # Keep the original LiDAR XY geometry for the vector BEV. The top-down
        # camera projection remains only for compatibility with older frames.
        entry = {"xy": [[round(float(x), 2), round(float(y), 2)]
                        for x, y in corners[:4, :2]], "label": label}
        projected = _project_box(corners, lidar_to_bev, 512, 512)
        if projected is not None:
            entry["box"] = projected["box"]
            entry["corners"] = projected["corners"][:8]
        if score is not None:
            entry["score"] = round(float(score), 3)
        if traj is not None:
            try:
                offsets = np.asarray(traj).reshape(-1, 6, 2)[:6]
                if np.isfinite(offsets).all():
                    center = corners[:, :2].mean(axis=0)
                    modes = np.cumsum(offsets, axis=1) + center
                    entry["traj"] = np.round(modes, 2).tolist()
            except ValueError:
                pass
        output["bev"][kind].append(entry)

    boxes = pts_bbox["boxes_3d"].corners.detach().cpu().numpy()
    scores = pts_bbox["scores_3d"].detach().cpu().numpy()
    labels = pts_bbox["labels_3d"].detach().cpu().numpy()
    trajectories = pts_bbox.get("trajs_3d")
    trajectories = trajectories.detach().cpu().numpy() if trajectories is not None else [None] * len(boxes)
    for corners, score, label_id, traj in zip(boxes, scores, labels, trajectories):
        if score < 0.25:
            continue
        label_id = int(label_id)
        label = class_names[label_id] if 0 <= label_id < len(class_names) else str(label_id)
        add("pred", corners, label, score, traj if label_id in (0, 1, 2, 3, 7) else None)

    map_pts = pts_bbox.get("map_pts_3d")
    map_scores = pts_bbox.get("map_scores_3d")
    map_labels = pts_bbox.get("map_labels_3d")
    if map_pts is not None and map_scores is not None and map_labels is not None:
        for points, score, label_id in zip(map_pts.detach().cpu().numpy(),
                                           map_scores.detach().cpu().numpy(),
                                           map_labels.detach().cpu().numpy()):
            if score < 0.6 or len(points) < 2 or not np.isfinite(points).all():
                continue
            output["map"].append({"label": int(label_id),
                                  "score": round(float(score), 3),
                                  "points": np.round(points[:, :2], 2).tolist()})

    # CARLA actor vertices and hero pose are in the same Unreal world frame.
    # Convert CARLA's right-positive ego Y to the model's left-positive ego Y.
    # The model's GPS pose belongs to a GNSS sensor 1.4 m behind the hero and
    # must not be used as the ego origin for these boxes.
    carla_to_model_ego = np.diag([1.0, -1.0, 1.0, 1.0])
    world_to_lidar = (np.linalg.inv(np.asarray(lidar2ego)) @
                      carla_to_model_ego @ np.asarray(world_to_ego))
    for actor in actors:
        if actor.id == hero_id:
            continue
        label = _actor_label(actor.type_id)
        if label is None:
            continue
        try:
            vertices = actor.bounding_box.get_world_vertices(actor.get_transform())
            world = np.array([[vertex.x, vertex.y, vertex.z, 1.0]
                              for vertex in vertices])
            corners = (world @ world_to_lidar.T)[:, :3]
            if np.linalg.norm(corners.mean(axis=0)[:2]) > 80:
                continue
            add("gt", corners, label)
        except RuntimeError:
            continue  # Actor may disappear between listing and reading its transform.
    return output
