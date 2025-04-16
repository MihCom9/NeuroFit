from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from vector import compute_deltas, compare_deltas, ACTUAL_DELTA_FILE, REFERENCE_DELTA_FILE
from helpers import calculate_score, movement_amplitude, normalize, cosine_similarity, vertical_angle
import pandas as pd
import numpy as np
from dtaidistance import dtw

# === Load raw movement data ===
def process_data(exercise_type):
    actual_df = pd.read_csv("data.csv")
    ideal_df = pd.read_csv(f"ideal_{exercise_type}.csv")

    sensor_vector = actual_df[['X', 'Y', 'Z', 'Height']].iloc[-1].values
    ideal_vector = ideal_df[['X', 'Y', 'Z', 'Height']].iloc[min(len(actual_df)-1, len(ideal_df)-1)].values
    path = actual_df[['X', 'Y', 'Z', 'Height']].values[-10:]
    ideal_path = ideal_df[['X', 'Y', 'Z', 'Height']].values


    results = calculate_score(sensor_vector, ideal_vector, path, ideal_path)
    score, cos_sim, dist, height_diff, angle, amplitude = results[:6]

    # === Load delta comparison for detailed LLM summary ===
    actual_deltas = compute_deltas("data.csv", ACTUAL_DELTA_FILE)
    reference_deltas = compute_deltas("ideal_movement.csv", REFERENCE_DELTA_FILE)

    avg_diffs, (cos_sim_x, cos_sim_y, cos_sim_z, _) = compare_deltas(actual_deltas, reference_deltas)

    # === Movement deviation summary ===
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
            movement_context.append(f"- At {seconds}s, high deviation on axis: {', '.join(axes)}.")

    movement_context = "\n".join(movement_context) if movement_context else "No major deviations were detected during the exercise."

    # === Extra metrics from utility functions ===
    normalized_sensor = normalize(sensor_vector[:3])
    cosine_to_ideal = cosine_similarity(sensor_vector[:3], ideal_vector[:3])
    angle_to_vertical = vertical_angle(sensor_vector)
    amplitude_from_path = movement_amplitude(path)
    point_count = len(actual_df)

    # === LLM interface ===
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

    summary_chain = summary_template | model
    summary = summary_chain.invoke({
        "exercise_type": exercise_type,
        "cos_sim_x": cos_sim_x,
        "cos_sim_y": cos_sim_y,
        "cos_sim_z": cos_sim_z,
        "avg_dx": avg_diffs[0],
        "avg_dy": avg_diffs[1],
        "avg_dz": avg_diffs[2],
        "point_count": point_count
    })

    print(f"\n✅ Final Score: {score:.2f}")
    print("\n🧠 LLM Evaluation:")
    print(summary)

    qa_chain = qa_template | model

    while True:
        print("\n💬 Ask a question about the movement or type 'q' to quit:")
        question = input("> ")
        if question.lower().strip() in ["q", "quit", "exit"]:
            break

        answer = qa_chain.invoke({
            "exercise_type": exercise_type,
            "cos_sim_x": cos_sim_x,
            "cos_sim_y": cos_sim_y,
            "cos_sim_z": cos_sim_z,
            "avg_dx": avg_diffs[0],
            "avg_dy": avg_diffs[1],
            "avg_dz": avg_diffs[2],
            "movement_context": movement_context,
            "point_count": point_count,
            "question": question
        })

        print("\n🤖 Answer:")
        print(answer)