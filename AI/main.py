from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from vector import compute_deltas, compare_deltas, ACTUAL_DELTA_FILE, REFERENCE_DELTA_FILE
import pandas as pd
import numpy as np

# --- Rating based on cosine similarity and movement deltas ---
def rate_performance(cos_sim_x, cos_sim_y, cos_sim_z, avg_diffs):
    avg_cos_sim = (cos_sim_x + cos_sim_y + cos_sim_z) / 3
    avg_delta_error = sum(avg_diffs) / 3

    if avg_cos_sim > 0.995 and avg_delta_error < 0.1:
        return "Excellent"
    elif avg_cos_sim > 0.98 and avg_delta_error < 0.2:
        return "Great"
    elif avg_cos_sim > 0.95 and avg_delta_error < 0.4:
        return "Good"
    elif avg_cos_sim > 0.90 and avg_delta_error < 0.6:
        return "Fair"
    else:
        return "Needs Improvement"

# --- Deviation analysis to generate context for LLM ---
def diagnose_deviations(actual_deltas, reference_deltas, sample_rate_hz=5):
    threshold = 0.1  # deviation threshold
    diff = np.abs(actual_deltas - reference_deltas)
    time_stamps = []
    axis_flags = []

    for i, (dx, dy, dz) in enumerate(diff):
        if dx > threshold or dy > threshold or dz > threshold:
            seconds = round(i / sample_rate_hz, 2)
            axis_flags.append((seconds, dx > threshold, dy > threshold, dz > threshold))

    if not axis_flags:
        return "No major deviations were detected during the exercise."

    summary_lines = ["Movement deviation summary:"]
    for t, x_flag, y_flag, z_flag in axis_flags:
        axes = []
        if x_flag: axes.append("X")
        if y_flag: axes.append("Y")
        if z_flag: axes.append("Z")
        summary_lines.append(f"- At {t}s, high deviation on axis: {', '.join(axes)}.")

    return "\n".join(summary_lines)

# --- Load and compare delta patterns ---
actual_deltas = compute_deltas("data.csv", ACTUAL_DELTA_FILE)
reference_deltas = compute_deltas("reference.csv", REFERENCE_DELTA_FILE)

avg_diffs, (cos_sim_x, cos_sim_y, cos_sim_z) = compare_deltas(actual_deltas, reference_deltas)

# Generate movement context
movement_context = diagnose_deviations(actual_deltas, reference_deltas)

# Load exercise type (optional)
try:
    actual_df = pd.read_csv("data.csv")
    exercise_type = actual_df["Exercise"].iloc[0]
except Exception:
    exercise_type = "Unknown Exercise"

# --- Set up the LLM ---
model = OllamaLLM(model="gemma:2b")

# --- Summary prompt ---
summary_template = ChatPromptTemplate.from_template("""
You are a movement analysis expert.

The person performed the following exercise (details in data.csv): {exercise_type}
The correct movement is in reference.csv.

Here are the per-axis similarity values and average difference magnitudes:
- Cosine similarity: X={cos_sim_x:.4f}, Y={cos_sim_y:.4f}, Z={cos_sim_z:.4f}
- Average differences: ΔX={avg_dx:.4f}, ΔY={avg_dy:.4f}, ΔZ={avg_dz:.4f}

Start by printing only these values. Then, give a short, 1-2 sentence summary of what they suggest about the movement's quality. Be concise and avoid repetition.
""")

# --- Q&A prompt using context ---
qa_template = ChatPromptTemplate.from_template("""
You are a friendly and supportive movement coach helping someone improve their form.

The person performed the following exercise: {exercise_type}

Movement accuracy summary:
- Cosine similarity: X={cos_sim_x:.4f}, Y={cos_sim_y:.4f}, Z={cos_sim_z:.4f}
- Average differences: ΔX={avg_dx:.4f}, ΔY={avg_dy:.4f}, ΔZ={avg_dz:.4f}

Movement deviation report:
{movement_context}

Based on this information, determine how well the person did. If they mostly did it right, be encouraging and offer small tips.  
If they didn’t do the exercise correctly, explain clearly what went wrong and how they can fix it.

Now respond to the person’s question with warmth and clarity, like a personal coach giving helpful feedback.

Question: {question}
""")



# --- Run summary once ---
summary_chain = summary_template | model

summary = summary_chain.invoke({
    "exercise_type": exercise_type,
    "cos_sim_x": cos_sim_x,
    "cos_sim_y": cos_sim_y,
    "cos_sim_z": cos_sim_z,
    "avg_dx": avg_diffs[0],
    "avg_dy": avg_diffs[1],
    "avg_dz": avg_diffs[2]
})

print("\n🧠 LLM Evaluation:")
print(summary)

# --- One-word score ---
rating = rate_performance(cos_sim_x, cos_sim_y, cos_sim_z, avg_diffs)
print(f"\n🏅 One-word evaluation: {rating}")

# --- Q&A loop ---
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
        "question": question
    })

    print("\n🤖 Answer:")
    print(answer)
