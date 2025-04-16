import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd
import numpy as np
import os

DATA_FILE = "data.csv"
REFERENCE_FILE = "ideal_movement.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return np.array([]), np.array([]), np.array([])
    try:
        df = pd.read_csv(DATA_FILE)
        if not all(col in df.columns for col in ['X', 'Y', 'Z']):
            return np.array([]), np.array([]), np.array([])
        return df['X'].values, df['Y'].values, df['Z'].values
    except Exception:
        return np.array([]), np.array([]), np.array([])

def load_reference():
    if not os.path.exists(REFERENCE_FILE):
        return None
    try:
        ref_df = pd.read_csv(REFERENCE_FILE)
        if not all(col in ref_df.columns for col in ['X', 'Y', 'Z']):
            return None
        return ref_df[['X', 'Y', 'Z']].values
    except Exception:
        return None

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
plt.title("📡 Real-time Movement Tracking")

def update_plot():
    while True:
        ax.clear()
        x, y, z = load_data()
        reference = load_reference()

        if len(x) > 1:
            points = np.array([x, y, z]).T
            color_values = np.linspace(0, 1, len(points))
            colors = cm.plasma(color_values)

            for i in range(len(points) - 1):
                ax.plot(points[i:i+2, 0], points[i:i+2, 1], points[i:i+2, 2],
                        color=colors[i], linewidth=2)

        if reference is not None and len(reference) > 1:
            ax.plot(reference[:, 0], reference[:, 1], reference[:, 2],
                    linestyle='dashed', color='gray', label='Reference')

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title("Real-time Movement Tracking")
        ax.legend()
        plt.pause(1)

if __name__ == "__main__":
    plt.ion()
    update_plot()
