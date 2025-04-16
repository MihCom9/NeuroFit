import pandas as pd
import numpy as np
from numpy.linalg import norm
import os

ACTUAL_DELTA_FILE = "actual_deltas.npy"
REFERENCE_DELTA_FILE = "reference_deltas.npy"

def compute_deltas(csv_path, cache_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_abs = os.path.join(script_dir, csv_path)
    cache_abs = os.path.join(script_dir, cache_path)

    if os.path.exists(cache_abs):
        csv_mtime = os.path.getmtime(csv_abs)
        cache_mtime = os.path.getmtime(cache_abs)
        if cache_mtime >= csv_mtime:
            print(f"✅ Using cached deltas from {cache_abs}")
            return np.load(cache_abs)

    print(f"📥 Recalculating deltas from {csv_abs}")
    df = pd.read_csv(csv_abs)

    # Select only position columns regardless of capitalization
    coord_cols = [col for col in df.columns if col.upper() in ["X", "Y", "Z", "HEIGHT"]]
    if len(coord_cols) != 4:
        raise ValueError("CSV must contain exactly 4 columns: X, Y, Z, Height")

    deltas = df[coord_cols].diff().dropna().to_numpy()
    np.save(cache_abs, deltas)
    return deltas

def compare_deltas(actual_deltas, reference_deltas):
    if actual_deltas.shape != reference_deltas.shape:
        raise ValueError("Delta arrays must have the same shape to compare movement patterns.")

    diff = np.abs(actual_deltas - reference_deltas)
    avg_diff_per_axis = np.mean(diff, axis=0)

    cos_sim = np.array([
        np.dot(actual_deltas[:, i], reference_deltas[:, i]) / (norm(actual_deltas[:, i]) * norm(reference_deltas[:, i]))
        for i in range(4)
    ])

    return avg_diff_per_axis, tuple(cos_sim)

if __name__ == "__main__":
    actual_deltas = compute_deltas("data.csv", ACTUAL_DELTA_FILE)
    reference_deltas = compute_deltas("ideal_movement.csv", REFERENCE_DELTA_FILE)
    avg_diffs, (cos_sim_x, cos_sim_y, cos_sim_z, cos_sim_h) = compare_deltas(actual_deltas, reference_deltas)

    print("\n📊 Movement Pattern Comparison (Delta-based):")
    print(f"Average \u0394X: {avg_diffs[0]:.4f}")
    print(f"Average \u0394Y: {avg_diffs[1]:.4f}")
    print(f"Average \u0394Z: {avg_diffs[2]:.4f}")
    print(f"Average \u0394Height: {avg_diffs[3]:.4f}")

    print("\n🎯 Cosine Similarity per Axis:")
    print(f"X-axis: {cos_sim_x:.4f}")
    print(f"Y-axis: {cos_sim_y:.4f}")
    print(f"Z-axis: {cos_sim_z:.4f}")
    print(f"Height: {cos_sim_h:.4f}")
