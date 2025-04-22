from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from vector import compute_deltas, compare_deltas, ACTUAL_DELTA_FILE, REFERENCE_DELTA_FILE
from helpers import calculate_score, movement_amplitude, normalize, cosine_similarity, vertical_angle
import pandas as pd
import numpy as np

# === Core processing ===
# Prompts for LLM evaluation and coaching
model = OllamaLLM(model="gemma:2b")

summary_template = ChatPromptTemplate.from_template("""
You are a movement analysis expert.

The person performed the following exercise (details in data.csv): {exercise_type}
The correct movement is in ideal_movement.csv.

Here are the per-axis similarity values and average difference magnitudes:
- Cosine similarity: X={cos_sim_x:.4f}, Y={cos_sim_y:.4f}, Z={cos_sim_z:.4f}
- Average differences: ΔX={avg_dx:.4f}, ΔY={avg_dy:.4f}, ΔZ={avg_dz:.4f}
- Total recorded points: {point_count}

Start by printing only these values. Then, give a short, 1-2 sentence summary of what they suggest about the movement's quality. Be concise and avoid repetition.
""")

qa_template = ChatPromptTemplate.from_template("""
You are a friendly and supportive movement coach helping someone improve their form.

The person performed the following exercise: {exercise_type}

Movement accuracy summary:
- Cosine similarity: X={cos_sim_x:.4f}, Y={cos_sim_y:.4f}, Z={cos_sim_z:.4f}
- Average differences: ΔX={avg_dx:.4f}, ΔY={avg_dy:.4f}, ΔZ={avg_dz:.4f}
- Total recorded points: {point_count}

Movement deviation report:
{movement_context}

Based on this information, determine how well the person did. If they mostly did it right, be encouraging and offer small tips.  
If they didn’t do the exercise correctly, explain clearly what went wrong and how they can fix it.

Now respond to the person’s question with warmth and clarity, like a personal coach giving helpful feedback.

Question: {question}
""")


def process_data(exercise_type):
    # Load logged data
    actual_df = pd.read_csv("data.csv")
    # If no data, return early
    if actual_df.empty:
        return {
            "final_score": None,
            "message": "No data points available to analyze."
        }

    # Clean and average the Score column
    if 'Score' in actual_df.columns:
        actual_df['Score'] = (
            actual_df['Score'].astype(str)
                            .str.extract(r'(\d+\.?\d*)')[0]
                            .astype(float)
        )
        avg_score = actual_df['Score'].mean()
    else:
        avg_score = None

    # Load ideal movement
    ideal_df = pd.read_csv(f"ideal_{exercise_type}.csv")
    if ideal_df.empty:
        return {
            "final_score": None,
            "message": f"No ideal data found for exercise '{exercise_type}'."
        }

    # 1) extract the very latest sensor reading
    sensor_vector = actual_df[['X', 'Y', 'Z', 'Height']].iloc[-1].values

    # 2) match server's first-reference logic
    ideal_vector  = ideal_df[['X', 'Y', 'Z', 'Height']].iloc[0].values

    # 3) single-frame path to enforce DTW=0, amplitude=0
    path       = np.array([sensor_vector])
    ideal_path = np.array([ideal_vector])

    # Raw scoring on latest frame
    score, cos_sim, dist, height_diff, angle, amplitude = calculate_score(
        sensor_vector, ideal_vector, path, ideal_path
    )

    # Load and align deltas for pattern comparison
    actual_deltas    = compute_deltas("data.csv",    ACTUAL_DELTA_FILE)
    reference_deltas = compute_deltas(f"ideal_{exercise_type}.csv", REFERENCE_DELTA_FILE)
    min_len = min(actual_deltas.shape[0], reference_deltas.shape[0])
    actual_deltas    = actual_deltas[:min_len]
    reference_deltas = reference_deltas[:min_len]
    avg_diffs, (cos_sim_x, cos_sim_y, cos_sim_z, _) = compare_deltas(
        actual_deltas, reference_deltas
    )

    # Movement deviation summary
    diff = np.abs(actual_deltas - reference_deltas)
    threshold = 0.1
    sample_rate_hz = 5
    movement_context = []
    for i, (dx, dy, dz, _) in enumerate(diff):
        if dx > threshold or dy > threshold or dz > threshold:
            seconds = round(i / sample_rate_hz, 2)
            axes = []
            if dx > threshold: axes.append("X")
            if dy > threshold: axes.append("Y")
            if dz > threshold: axes.append("Z")
            movement_context.append(
                f"- At {seconds}s, high deviation on axis: {', '.join(axes)}."
            )
    movement_context = ("\n".join(movement_context)
                        if movement_context else
                        "No major deviations were detected during the exercise.")

    # Extra metrics
    point_count = len(actual_df)

    # Generate LLM summary
    summary_chain = summary_template | model
    summary = summary_chain.invoke({
        "exercise_type": exercise_type,
        "cos_sim_x":     cos_sim_x,
        "cos_sim_y":     cos_sim_y,
        "cos_sim_z":     cos_sim_z,
        "avg_dx":        avg_diffs[0],
        "avg_dy":        avg_diffs[1],
        "avg_dz":        avg_diffs[2],
        "point_count":   point_count
    })

    # Build final result
    result = {
        "final_score":        round(avg_score, 2) if avg_score is not None else round(score, 2),
        "cosine_similarity":  round(cos_sim, 4),
        "dtw_distance":       round(dist, 4),
        "height_diff":        round(height_diff, 4),
        "vertical_angle":     round(angle, 2),
        "amplitude":          round(amplitude, 4),
        "avg_deltas":         avg_diffs.tolist(),
        "cos_sim_per_axis":   [cos_sim_x, cos_sim_y, cos_sim_z],
        "point_count":        point_count,
        "movement_context":   movement_context,
        "llm_summary":        summary
    }
    return result