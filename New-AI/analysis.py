import pandas as pd
import numpy as np
from dtaidistance import dtw

# === Load raw data files ===
actual_df = pd.read_csv("data.csv")
ideal_df = pd.read_csv("ideal_shoulder_press.csv")

# Convert to native Python lists
sensor_sequence = actual_df[['X', 'Y', 'Z', 'Height']].values.tolist()
ideal_sequence = ideal_df[['X', 'Y', 'Z', 'Height']].values.tolist()

# === Local scoring function ===
def compute_score(sensor_sequence, ideal_sequence):
    sensor = np.array(sensor_sequence)
    ideal = np.array(ideal_sequence)
    
    # Truncate to ideal_sequence length
    sensor = sensor[:len(ideal)]
    
    scores = []
    for s, i in zip(sensor, ideal):
        cos_sim = np.dot(s[:3], i[:3]) / (np.linalg.norm(s[:3]) * np.linalg.norm(i[:3]) + 1e-8)
        dtw_dist = dtw.distance(s[:3], i[:3])
        height_diff = abs(s[3] - i[3])
        z_similarity = s[2] / (i[2] + 1e-8)
        amplitude = np.linalg.norm(s[:3]) / (np.linalg.norm(i[:3]) + 1e-8)
        
        frame_score = (
            40 * cos_sim
            + 2 * max(0, 20 - dtw_dist)
            + 0.5 * max(0, 10 - 100 * height_diff)
            + 9 * min(z_similarity, 1)
            + 10 * min(amplitude, 1)
        )
        scores.append(frame_score)
    
    avg_score = np.mean(scores) if scores else 0.0
    return max(0, min(100, avg_score))

# Score each 20-frame chunk
chunk_size = len(ideal_sequence)
scores = []
for i in range(0, len(sensor_sequence), chunk_size):
    chunk = sensor_sequence[i:i + chunk_size]
    if len(chunk) == chunk_size:  # Only score full chunks
        score = compute_score(chunk, ideal_sequence)
        scores.append(score)
        print(f"Chunk {i // chunk_size + 1} score: {score}")

# Average scores
avg_score = np.mean(scores) if scores else 0.0
print("Average score across chunks:", avg_score)