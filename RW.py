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
numParticles = 10000

# Behavior of the simulation
# Number of iterations the simulation will move the particles through
# this is sent to int, so if the output is not a whole number it will go to the next smallest integer
increments, moveDistance, jumpProb, moveProb = RWfunctions.initSimulation(deltaT, timeConst, diffCon, bSpin, gamma)

print(f"Behavior: \nIncrements: {increments}\n Move Distance: {moveDistance}")
# Time it took to complete all the above code, will be subtracted from the start time last since it will be needed in other calculations

''' Run Stage '''

particleList = RWfunctions.runSimulation(increments, moveDistance, jumpProb, moveProb, numParticles)

# Time it took to create these particles, can change based on parameters. Will be subtracted from initTime second to last


# Time it took to move the partilces through simulation. This should be the bottleneck for speed. Same operations for timing






''' Graph Stage '''
RWfunctions.graphing(increments, moveDistance, particleList)
plt.show()



#RWfunctions.timing(initTime, createTime, moveTime, graphTime, startTime)


print("\n\n\n---------------------Behavior---------------------")
print(f"         Move Distance: {moveDistance}")
print(f"            Increments: {increments}")
print(f"                 Drift: {moveProb:.2f}")
print(f"                  Jump: {jumpProb}")
print("--------------------------------------------------")
#print(particlesTop)
#print(particlesBottom)