from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import csv
import os
from dtaidistance import dtw
from numpy.linalg import norm
from analysis import process_data

from helpers import calculate_score

app = Flask(__name__)
DATA_FILE = "./data.csv"
REFERENCE_FILE = "./ideal_movement.csv"

# === Loading ideal values ===
if not os.path.exists(REFERENCE_FILE):
    raise FileNotFoundError(f"Missing required reference file: {REFERENCE_FILE}")
ideal_df = pd.read_csv(REFERENCE_FILE)
ideal_vectors = ideal_df[['X', 'Y', 'Z', 'Height']].values

real_path = []

def fix_corrupted_csv(file_path):
    cleaned_rows = []
    with open(file_path, 'r') as f:
        for line in f:
            # Split by comma and clean extra spaces/newlines
            parts = [part.strip() for part in line.strip().split(',')]
            while len(parts) >= 5:
                cleaned_rows.append(parts[:5])
                parts = parts[5:]

    # Rewrite the cleaned file
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['X', 'Y', 'Z', 'Height', 'Score'])
        for row in cleaned_rows[1:] if cleaned_rows[0] == ['X', 'Y', 'Z', 'Height', 'Score'] else cleaned_rows:
            writer.writerow(row)

    print(f"✅ CSV file '{file_path}' was checked and fixed if needed.")

exercise = 'movement'

# === Accepting POST requests from ESP32 ===
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    try:
        # Extracting data from ESP32
        x = float(data['acceleration_x'])
        y = float(data['acceleration_y'])
        z = float(data['acceleration_z'])
        height = float(data.get('altitude', 0.0))

        # Add to a local array for comparison
        sensor_vector = np.array([x, y, z, height])

        # Always reset path history for consistent scoring (stateless mode)
        real_path.clear()

        real_path.append(sensor_vector)

        # Comparison with ideal coordinates
        ideal_vector = ideal_vectors[len(real_path) % len(ideal_vectors)]

        score, cos_sim, dist, h_diff, angle, amp = calculate_score(
            sensor_vector, ideal_vector, real_path, ideal_vectors
        )

        # ✅ Clean corrupted rows if needed
        fix_corrupted_csv(DATA_FILE)

        # ✅ Save to a file
        file_exists = os.path.exists(DATA_FILE)
        with open(DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['X', 'Y', 'Z', 'Height', 'Score'])
            writer.writerow([x, y, z, height, round(score)])

        print(f"[✓] Score: {score:.1f} | Cos: {cos_sim:.2f} | DTW: {dist:.2f} | Δh: {h_diff:.2f} | Angle: {angle:.1f}° | Amp: {amp:.2f}")

        return jsonify({
            "status": "ok",
            "score": score,
            "cosine_similarity": round(cos_sim, 4),
            "dtw": round(dist, 4),
            "height_diff": round(h_diff, 2),
            "angle": round(angle, 2),
            "amplitude": round(amp, 2)
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/start', methods=['POST'])
def start_exercise():
    global exercise
    data = request.json
    exercise = data['exercise']
    return jsonify({"status": "ok" }), 200

@app.route('/end', methods=['POST'])
def end_exercise():
    process_data(exercise)
    return jsonify({"status": "ok" }), 200

if __name__ == '__main__':
    # This is for the graph(visualising the person coordinates):
    # subprocess.Popen(["python", "realtime_plot.py"])
    app.run(host='127.0.0.1', port=8080)
