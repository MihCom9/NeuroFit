from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import csv
import os
import requests
from analysis import process_data
from helpers import calculate_score

app = Flask(__name__)

# === Paths and Config ===
DATA_FILE = "./New-AI/data.csv"
EXTERNAL_SCORE_URL = "http://172.20.10.3:8080/score"  # Optional external endpoint

# === Global variables ===
real_path = []
last_vector = None
comparing = False
exercise = None
ideal_vectors = None

# === CSV Cleaning ===
def fix_corrupted_csv(file_path):
    cleaned_rows = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = [part.strip() for part in line.strip().split(',')]
            while len(parts) >= 5:
                cleaned_rows.append(parts[:5])
                parts = parts[5:]

    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['X', 'Y', 'Z', 'Height', 'Score'])
        for row in cleaned_rows[1:] if cleaned_rows[0] == ['X', 'Y', 'Z', 'Height', 'Score'] else cleaned_rows:
            writer.writerow(row)

    print(f"✅ Cleaned malformed rows in {file_path}")

# === Start: load ideal CSV ===
@app.route('/start', methods=['POST'])
def start_exercise():
    global exercise, ideal_vectors, real_path

    data = request.json
    exercise = data['exercise']
    print(f"[*] Starting exercise: {exercise}")

    real_path.clear()
    reference_path = f"./New-AI/ideal_{exercise}.csv"

    if not os.path.exists(reference_path):
        return jsonify({"status": "error", "message": f"Missing ideal file for: {exercise}"}), 400

    try:
        df = pd.read_csv(reference_path)
        ideal_vectors = [np.array(v) for v in df[['X', 'Y', 'Z', 'Height']].values]
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # Reset data.csv at the beginning
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['X', 'Y', 'Z', 'Height', 'Score'])

    return jsonify({"status": "ok", "message": f"Exercise '{exercise}' started"}), 200

# === Accepting sensor data ===
@app.route('/data', methods=['POST'])
def receive_data():
    global real_path, last_vector, comparing, ideal_vectors, exercise

    if ideal_vectors is None:
        return jsonify({"status": "error", "message": "Start exercise first with /start"}), 400

    try:
        data = request.json
        x = float(data['acceleration_x'])
        y = float(data['acceleration_y'])
        z = float(data['acceleration_z'])
        height = float(data['altitude'])
        sensor_vector = np.array([x, y, z, height])

        print(f"📥 Incoming: {sensor_vector}")

        # Pause logic
        if last_vector is not None and np.allclose(sensor_vector, last_vector, atol=1e-6):
            if comparing:
                comparing = False
                print("[!] No change in movement; pausing.")
            last_vector = sensor_vector
            return jsonify({"status": "paused", "message": "No movement detected"}), 200
        else:
            if not comparing:
                comparing = True
                print("[*] Movement detected; resuming.")
            last_vector = sensor_vector

        # Reset if full rep done
        if len(real_path) == len(ideal_vectors):
            print("[*] Repetition complete.")
            real_path.clear()

        real_path.append(sensor_vector)
        frame_idx = len(real_path) - 1
        ideal_vector = ideal_vectors[frame_idx]

        # === Scoring ===
        score, cos_sim, dist, h_diff, angle, amp = calculate_score(
            sensor_vector, ideal_vector, real_path, ideal_vectors
        )

        # === Save to data.csv ===
        # Reset data.csv at the beginning
        try:
            with open(DATA_FILE, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([x, y, z, height, round(score)])
                csvfile.flush()
                os.fsync(csvfile.fileno())  # Ensure data is written to disk
            print(f"[✅] Saved to CSV: {x}, {y}, {z}, {height}, Score: {round(score)}")
        except Exception as file_error:
            print(f"[❌] Error writing to CSV: {file_error}")


        # Optional external post
        if EXTERNAL_SCORE_URL:
            try:
                requests.post(
                    EXTERNAL_SCORE_URL,
                    json={"exercise": exercise, "score": round(score, 2)},
                    timeout=5
                )
            except Exception as e:
                print("[!] Failed to POST score:", e)

        return jsonify({
            "status": "ok",
            "score": round(score, 2)
        }), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

# === End and summarize ===
@app.route('/end', methods=['POST'])
def end_exercise():
    fix_corrupted_csv(DATA_FILE)
    summary = process_data(exercise)
    return jsonify({
        "status": "complete",
        "summary": summary
    }), 200

if __name__ == '__main__':
    app.run(host='172.20.10.8', port=8080)
