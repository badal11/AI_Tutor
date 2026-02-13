import matplotlib.pyplot as plt
import numpy as np

# Data from screenshots
roles = ['Tutor\n(llama3.2:3b)', 'Generator\n(gemma2:2b)', 'Explainer\n(llama3.2:3b)', 'Coder\n(qwen2.5:3b)']
local_latency = [1.6934, 9.1571, 1.7313, 15.8890]
gemini_latency = [5.8054, 5.8054, 3.7967, 25.2665]

x = np.arange(len(roles))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

# Define colors (Modern/Dark theme compliant)
color_local = '#4ade80' # Bright Green
color_gemini = '#60a5fa' # Blue

rects1 = ax.bar(x - width/2, local_latency, width, label='Local Model', color=color_local)
rects2 = ax.bar(x + width/2, gemini_latency, width, label='Gemini-2.5-Flash', color=color_gemini)

# Add text labels
ax.set_ylabel('Mean Latency (Seconds)')
ax.set_title('Latency Comparison: Local Models vs Cloud Baseline')
ax.set_xticks(x)
ax.set_xticklabels(roles)
ax.legend()

ax.grid(axis='y', linestyle='--', alpha=0.3)

# Add value labels on top of bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}s',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')

autolabel(rects1)
autolabel(rects2)

# Save the figure
plt.tight_layout()
plt.savefig('evaluations/latency_comparison.png')