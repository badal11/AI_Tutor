import matplotlib.pyplot as plt
import numpy as np

def create_radar_chart(categories, data_sllm, data_gemini, title, ax):
    # Number of variables
    N = len(categories)

    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1] # Close the loop to complete the shape

    # Initialise the spider plot
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw one axe per variable + add labels
    plt.xticks(angles[:-1], categories)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=7)
    plt.ylim(0, 5.5)

    # Plot data
    # SLLM Data
    values_sllm = data_sllm + data_sllm[:1] # Close the loop
    ax.plot(angles, values_sllm, linewidth=1, linestyle='solid', label="SLLM")
    ax.fill(angles, values_sllm, 'b', alpha=0.1)

    # Gemini Data
    values_gemini = data_gemini + data_gemini[:1] # Close the loop
    ax.plot(angles, values_gemini, linewidth=1, linestyle='solid', label="Gemini-2.5-Flash")
    ax.fill(angles, values_gemini, 'r', alpha=0.1)

    # Add title
    plt.title(title, size=11, color='black', y=1.1)

# --- Data Setup ---

# 1. Tutor Agent (Llama-3.2:3b vs Gemini)
tutor_cats = ['Socratic\nQuestioning', 'Scaffolding', 'Adaptivity', 'Context\nRetention', 'Hallucination\nSafety']
tutor_sllm = [2, 2, 2, 2, 4] 
tutor_gemini = [5, 5, 5, 5, 5]

# 2. Quiz Generator (Gemma-2:2b vs Gemini)
quiz_cats = ['Relevance', 'Uniqueness', 'Distractors', 'Clarity']
quiz_sllm = [5, 1, 2, 4] 
quiz_gemini = [5, 5, 5, 5]

# 3. Code Analyzer (Qwen-2.5:3b vs Gemini)
code_cats = ['Bug\nDetection', 'False\nPositive', 'Concept\nExplanation', 'Refactoring', 'Context\nHandling']
code_sllm = [1, 1, 2, 2, 2] 
code_gemini = [4, 5, 5, 5, 5]

# --- Plotting ---

# Create figure with 3 subplots
fig = plt.figure(figsize=(18, 6))

# Plot 1: Tutor
ax1 = plt.subplot(131, polar=True)
create_radar_chart(tutor_cats, tutor_sllm, tutor_gemini, "Tutor Agent\n(Llama-3.2:3b vs Gemini)", ax1)
# Add legend to the first plot
ax1.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

# Plot 2: Quiz
ax2 = plt.subplot(132, polar=True)
create_radar_chart(quiz_cats, quiz_sllm, quiz_gemini, "Quiz Generator\n(Gemma-2:2b vs Gemini)", ax2)

# Plot 3: Code
ax3 = plt.subplot(133, polar=True)
create_radar_chart(code_cats, code_sllm, code_gemini, "Code Analyzer\n(Qwen-2.5:3b vs Gemini)", ax3)

plt.tight_layout()

# Save the plot
plt.savefig('evaluations/sllm_vs_gemini_radar_comparison.png', dpi=300)
print("Chart saved as 'sllm_vs_gemini_radar_comparison.png'")