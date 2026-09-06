import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

def plot_latest_csv(folder_path=None, file_path=None):
    # Determine the path to the main project directory (one level up from utils/)
    if folder_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.join(base_dir, "logs")

    if file_path is None:
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        if not csv_files:
            print(f"[ERROR] No CSV files found in directory '{folder_path}'.")
            return
        # Find the most recently modified CSV file
        file_path = max(csv_files, key=os.path.getmtime)

    print(f"[INFO] Loading file: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"[ERROR] Failed to load CSV file: {e}")
        return

    if df.empty or len(df.columns) < 2:
        print("[ERROR] CSV file is empty or contains insufficient columns.")
        return

    time_col = df.columns[0]
    data_cols = df.columns[1:]
    num_charts = len(data_cols)

    fig, axes = plt.subplots(nrows=num_charts, ncols=1, figsize=(10, 3 * num_charts), sharex=True)
    if num_charts == 1:
        axes = [axes]

    fig.suptitle(f"Data Analysis: {os.path.basename(file_path)}", fontsize=14, fontweight='bold')
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

    for i, col in enumerate(data_cols):
        ax = axes[i]
        color = colors[i % len(colors)]
        ax.plot(df[time_col], df[col], label=col, color=color, linewidth=1.5)
        ax.set_ylabel(col, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc="upper right")

    axes[-1].set_xlabel(time_col, fontsize=11)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_latest_csv()