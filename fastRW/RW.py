import csv
import matplotlib.pyplot as plt
import subprocess
import numpy as np
import math
import time

# Parameters
deltaT = 0.1
timeConst = 10
diffCon = 1
bSpin = 0.15
gamma = 0
numParticles = 100000

coresToUse = 12

increments = int (timeConst / deltaT)
moveDistance = round(math.sqrt(2 * diffCon * deltaT), 3)

runProgram = ['./RWoperation.exe', str(deltaT), str(timeConst), str(diffCon), str(bSpin), str(gamma), str(numParticles), str(coresToUse)]

runTime = time.perf_counter()
result = subprocess.run(runProgram, capture_output=False)
runTime = time.perf_counter() - runTime

print(f"Simulation ran in {runTime:.2f} seconds.\n")

def load_csv_data(filepath):
    x_top, x_bottom = [], []
    with open(filepath, mode='r') as file:
        reader = csv.DictReader(file)  # Automatically handles the header row
        for row in reader:
            x_val = float(row['x'])
            y_val = int(row['y'])
            if y_val == 1:
                x_top.append(x_val)
            else:
                x_bottom.append(x_val)
    return x_top, x_bottom

# Separate the x-values based on y-values for prob and step data
topValsProb, bottomValsProb = load_csv_data("sims/probSim.csv")
topValsStep, bottomValsStep = load_csv_data("sims/stepSim.csv")


# Create the figure
plt.figure(figsize=(10, 6))

# Step 1: Compute histograms for y = 1 (top)
hist_topProb, bin_edges_prob = np.histogram(topValsProb, bins=200, density=True)
hist_topStep, bin_edges_step = np.histogram(topValsStep, bins=200, density=True)

# Compute bin centers
bin_centers_prob = 0.5 * (bin_edges_prob[1:] + bin_edges_prob[:-1])
bin_centers_step = 0.5 * (bin_edges_step[1:] + bin_edges_step[:-1])

# Step 2: Plot bar charts for y = 1 (top)
plt.bar(bin_centers_prob, hist_topProb, width=np.diff(bin_edges_prob), alpha=0.5, color='green', label='Probability')
plt.bar(bin_centers_step, hist_topStep, width=np.diff(bin_edges_step), alpha=0.5, color='purple', label='Step')

# Step 3: Compute and plot inverted histograms for y = 0 (bottom)
hist_bottomProb, bin_edges_bottom_prob = np.histogram(bottomValsProb, bins=200, density=True)
hist_bottomStep, bin_edges_bottom_step = np.histogram(bottomValsStep, bins=200, density=True)

# Compute bin centers for the inverted histograms
bin_centers_bottom_prob = 0.5 * (bin_edges_bottom_prob[1:] + bin_edges_bottom_prob[:-1])
bin_centers_bottom_step = 0.5 * (bin_edges_bottom_step[1:] + bin_edges_bottom_step[:-1])

# Plot inverted bar charts for y = 0 (bottom)
plt.bar(bin_centers_bottom_prob, -hist_bottomProb, width=np.diff(bin_edges_bottom_prob), alpha=0.5, color='green')
plt.bar(bin_centers_bottom_step, -hist_bottomStep, width=np.diff(bin_edges_bottom_step), alpha=0.5, color='purple')


def analyticSolution(x, t, v, D=1):    
    lead = 1 / math.sqrt(4 * math.pi * D * t)
    exponent = -1 * ((x - (v * t)) ** 2)/(4 * D * t)
    return lead * (math.e ** exponent)

# top max
if max(topValsProb) < max(topValsStep):
    topMax = max(topValsStep)
else:
    topMax = max(topValsProb)
# top min
if min(topValsProb) > min(topValsStep):
    topMin = min(topValsStep)
else:
    topMin = min(topValsProb)
# bottom max
if max(bottomValsProb) > max(bottomValsStep):
    bottomMax = max(bottomValsStep)
else:
    bottomMax = max(bottomValsProb)
# bottom min
if min(bottomValsProb) > min(bottomValsStep):
    bottomMin = min(bottomValsStep)
else:
    bottomMin = min(bottomValsProb)


xRangeTop = np.linspace(topMin, topMax, num=int(topMax - topMin))
xRangeBottom = np.linspace(bottomMin, bottomMax, num=int(bottomMax - bottomMin))
                        
yRangeTop = []
yRangeBottom = []

for xVal in xRangeTop:
    yRangeTop.append(analyticSolution(xVal, timeConst, bSpin, diffCon))

for xVal in xRangeBottom:
    yRangeBottom.append(-analyticSolution(xVal, timeConst, -bSpin, diffCon))



plt.plot(xRangeTop, yRangeTop, color='black')
plt.plot(xRangeBottom, yRangeBottom, color='black')
# Step 4: Formatting the plot
plt.title(f"{numParticles} Walkers taking {int(timeConst/deltaT)} steps")
plt.xlabel('X Coordinate')
plt.ylabel('Frequency')
plt.axhline(0, color='black', linewidth=0.8)  # Add a horizontal line at y=0
plt.legend()
plt.grid(True)

# Show the plot
plt.tight_layout()
plt.show()
