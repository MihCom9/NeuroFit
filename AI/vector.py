import pandas as pd
import numpy as np
from numpy.linalg import norm
import os

# Just filenames (no slashes)
ACTUAL_DELTA_FILE = "actual_deltas.npy"
REFERENCE_DELTA_FILE = "reference_deltas.npy"

# --- Compute deltas or load if up-to-date ---
def compute_deltas(csv_path, cache_path):
    # Get absolute paths
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

    if list(df.columns) != ['X', 'Y', 'Z']:
        raise ValueError(f"Expected columns ['X', 'Y', 'Z'], but got {list(df.columns)}")

    deltas = df.diff().dropna().to_numpy()
    np.save(cache_abs, deltas)
    return deltas


# --- Compare delta patterns ---
def compare_deltas(actual_deltas, reference_deltas):
    if actual_deltas.shape != reference_deltas.shape:
        raise ValueError("Delta arrays must have the same shape to compare movement patterns.")

    diff = np.abs(actual_deltas - reference_deltas)
    avg_diff_per_axis = diff.mean(axis=0)

    cosine_sim_x = np.dot(actual_deltas[:,0], reference_deltas[:,0]) / (norm(actual_deltas[:,0]) * norm(reference_deltas[:,0]))
    cosine_sim_y = np.dot(actual_deltas[:,1], reference_deltas[:,1]) / (norm(actual_deltas[:,1]) * norm(reference_deltas[:,1]))
    cosine_sim_z = np.dot(actual_deltas[:,2], reference_deltas[:,2]) / (norm(actual_deltas[:,2]) * norm(reference_deltas[:,2]))

    return avg_diff_per_axis, (cosine_sim_x, cosine_sim_y, cosine_sim_z)

# --- Main function for standalone usage ---
def main():
    actual_deltas = compute_deltas("data.csv", ACTUAL_DELTA_FILE)
    reference_deltas = compute_deltas("reference.csv", REFERENCE_DELTA_FILE)

    avg_diffs, (cos_sim_x, cos_sim_y, cos_sim_z) = compare_deltas(actual_deltas, reference_deltas)

    print("\n📊 Movement Pattern Comparison (Delta-based):")
    print(f"Average ΔX: {avg_diffs[0]:.4f}")
    print(f"Average ΔY: {avg_diffs[1]:.4f}")
    print(f"Average ΔZ: {avg_diffs[2]:.4f}")

    print("\n🎯 Cosine Similarity per Axis:")
    print(f"X-axis: {cos_sim_x:.4f}")
    print(f"Y-axis: {cos_sim_y:.4f}")
    print(f"Z-axis: {cos_sim_z:.4f}")

if __name__ == "__main__":
    main()
