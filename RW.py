import RWfunctions
import time
import matplotlib.pyplot as plt

# This is a function that calculates the probability that a particle will move either left or right
# A sucess is a move right, a failure is a move left. Probabilities are compliment for each line. Top = P Bottom = 1 - P
# Takes the diffusion constant, b, which is spin, and delta t4
# When b is zero the dr4ift automatically becomes 0.5, however D or b must be nonzero

# Clock time to record when the program starts
startTime = time.perf_counter()


''' Initialization stage '''

# Parameters
deltaT = 0.1
timeConst = 2
diffCon = 20
bSpin = -5.1
gamma = 0
numParticles = 100000

# Behavior of the simulation
# Number of iterations the simulation will move the particles through
# this is sent to int, so if the output is not a whole number it will go to the next smallest integer
increments = int (timeConst / deltaT)

# Distance each particle will move left or right
moveDistance = RWfunctions.particleMoveDistance(deltaT, diffCon)
# Probability a particle will jump to another line
jumpProb = deltaT * gamma
# Probability a particle will move either left or right
moveProb = RWfunctions.moveCalculation(diffCon, bSpin, deltaT)

# List for the particles to be stored in
particleList = []

# Time it took to complete all the above code, will be subtracted from the start time last since it will be needed in other calculations
initTime = time.perf_counter()


''' Run Stage '''

# Create particles
for i in range(numParticles // 2):
    particleList.append((0, 1)) # Half the particles start on the top line
for i in range(numParticles // 2):
    particleList.append((0, 0)) # Other half start on the bottom line

# Time it took to create these particles, can change based on parameters. Will be subtracted from initTime second to last
createTime = time.perf_counter()

# Run simulation through each iteration
for i in range(int(increments)):
    particleList = RWfunctions.moveParticles(particleList, moveProb, jumpProb, moveDistance) # Change each particle

# Time it took to move the partilces through simulation. This should be the bottleneck for speed. Same operations for timing
moveTime = time.perf_counter()

''' Graph Stage '''

# Initialize lists for x-values and particle counts
particleRange = [i * moveDistance for i in range(-increments, increments + 1)]
particlesTop = [0] * len(particleRange)
particlesBottom = [0] * len(particleRange)

# Count the particles on the top and bottom lines
for particle in particleList:
    index = int((particle[0] / moveDistance) + increments)  # Calculate index for x-value
    if particle[1] == 1:
        particlesTop[index] += 1
    elif particle[1] == 0:
        particlesBottom[index] += 1

# Calculate total particles for normalization
topAmount = sum(particlesTop)
bottomAmount = sum(particlesBottom)

# Normalize counts to proportions
particlesTop = [count / topAmount for count in particlesTop]
particlesBottom = [-count / bottomAmount for count in particlesBottom]

plt.bar(particleRange, particlesTop, label="Top Line Particles", color="blue")
plt.bar(particleRange, particlesBottom, label="Bottom Line Particles", color="purple")
plt.legend()
plt.title("Concurrent Flow of Particles on Two Discrete Lines")
plt.xlabel("X-Axis Location")
plt.ylabel("Particle Frequency")
plt.grid(True)

# Time it took to graph the data. Will be the first thing subtracted from the start time to get the total time

graphTime = time.perf_counter()

plt.show()



RWfunctions.timing(initTime, createTime, moveTime, graphTime, startTime)


print("\n\n\n---------------------Behavior---------------------")
print(f"         Move Distance: {moveDistance}")
print(f"            Increments: {increments}")
print(f"                 Drift: {moveProb:.2f}")
print(f"                  Jump: {jumpProb}")
print("--------------------------------------------------")
#print(particlesTop)
#print(particlesBottom)