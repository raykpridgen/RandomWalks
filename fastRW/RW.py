import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import numpy as np

# Parameters
deltaT = 0.1
timeConst = 1000
diffCon = 1
bSpin = 0.25
gamma = 0
numParticles = 100000

runProgram = ['./RWoperation', str(deltaT), str(timeConst), str(diffCon), str(bSpin), str(gamma), str(numParticles), '1']
result = subprocess.run(runProgram, capture_output=False)

# Load the CSV data
dataProb = pd.read_csv("sims/probSim.csv")
dataStep = pd.read_csv("sims/stepSim.csv")

# Separate the x-values based on y-values for prob data
topValsProb = dataProb[dataProb['y'] == 1]['x']
bottomValsProb = dataProb[dataProb['y'] == 0]['x']

# Separate the x-values based on y-values for step data
topValsStep = dataStep[dataStep['y'] == 1]['x']
bottomValsStep = dataStep[dataStep['y'] == 0]['x']

# Create the figure
plt.figure(figsize=(10, 6))

# Step 1: Compute histograms for y = 1 (top)
hist_topProb, bin_edges_prob = np.histogram(topValsProb, bins=200, density=True)
hist_topStep, bin_edges_step = np.histogram(topValsStep, bins=200, density=True)

# Compute bin centers
bin_centers_prob = 0.5 * (bin_edges_prob[1:] + bin_edges_prob[:-1])
bin_centers_step = 0.5 * (bin_edges_step[1:] + bin_edges_step[:-1])

# Step 2: Plot bar charts for y = 1 (top)
plt.bar(bin_centers_prob, hist_topProb, width=np.diff(bin_edges_prob), alpha=0.5, color='red', label='Probability y=1')
plt.bar(bin_centers_step, hist_topStep, width=np.diff(bin_edges_step), alpha=0.5, color='blue', label='Step y=1')

# Step 3: Compute and plot inverted histograms for y = 0 (bottom)
hist_bottomProb, bin_edges_bottom_prob = np.histogram(bottomValsProb, bins=200, density=True)
hist_bottomStep, bin_edges_bottom_step = np.histogram(bottomValsStep, bins=200, density=True)

# Compute bin centers for the inverted histograms
bin_centers_bottom_prob = 0.5 * (bin_edges_bottom_prob[1:] + bin_edges_bottom_prob[:-1])
bin_centers_bottom_step = 0.5 * (bin_edges_bottom_step[1:] + bin_edges_bottom_step[:-1])

# Plot inverted bar charts for y = 0 (bottom)
plt.bar(bin_centers_bottom_prob, -hist_bottomProb, width=np.diff(bin_edges_bottom_prob), alpha=0.5, color='red', edgecolor='black', label='Probability y=0 (Inverted)')
plt.bar(bin_centers_bottom_step, -hist_bottomStep, width=np.diff(bin_edges_bottom_step), alpha=0.5, color='blue', edgecolor='black', label='Step y=0 (Inverted)')

# Step 4: Formatting the plot
plt.title(f"{numParticles} Walkers taking {timeConst/deltaT} steps")
plt.xlabel('X Coordinate')
plt.ylabel('Frequency')
plt.axhline(0, color='black', linewidth=0.8)  # Add a horizontal line at y=0
plt.legend()
plt.grid(True)

# Show the plot
plt.tight_layout()
plt.show()