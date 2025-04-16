import numpy as np
from dtaidistance import dtw
from numpy.linalg import norm

# === Maths ===
def normalize(v):
    n = norm(v)
    return v / n if n != 0 else v

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (norm(v1) * norm(v2))

def vertical_angle(v):
    unit_z = np.array([0, 0, 1])
    angle_rad = np.arccos(np.clip(np.dot(normalize(v[:3]), unit_z), -1.0, 1.0))
    return np.degrees(angle_rad)

def movement_amplitude(path):
    return norm(path[-1][:3] - path[0][:3]) if len(path) >= 2 else 0

def dtw_distance(path1, path2):
    path1_1d = np.linalg.norm(path1, axis=1)
    path2_1d = np.linalg.norm(path2, axis=1)

    try:
        return dtw.distance_fast(path1_1d, path2_1d)  # Try C version
    except Exception:
        print("⚠️ Falling back to slower pure-Python DTW...")
        return dtw.distance(path1_1d, path2_1d)

def calculate_score(sensor_vector, ideal_vector, path, ideal_path):
    cos_sim = cosine_similarity(sensor_vector[:3], ideal_vector[:3])
    dist = dtw_distance(path, ideal_path[:len(path)]) if len(path) >= 5 else 0
    height_diff = abs(sensor_vector[3] - ideal_vector[3])
    angle = vertical_angle(sensor_vector)
    amplitude = movement_amplitude(path)

    score = (
        min(cos_sim, 1.0) * 40 +
        max(0, 20 - dist) * 2 +
        max(0, 10 - height_diff * 100) * 0.5 +
        max(0, 90 - abs(angle)) * 0.1 +
        min(amplitude, 1.0) * 10
    )
    return score, cos_sim, dist, height_diff, angle, amplitude