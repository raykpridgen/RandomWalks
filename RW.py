import RWfunctions
import time
import matplotlib.pyplot as plt


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
RWfunctions.graphing(increments, moveDistance, particleList)
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