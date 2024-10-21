import numpy as np
import time
import math
import matplotlib.pyplot as plt
import sys

# Clock time to record when the program starts
startTime = time.perf_counter()

''' Initialization stage '''

# Parameters
deltaT = 0.5
timeConst = 10
diffCon = 1
bSpin = 0
gamma = 0
numParticles = 100000

# Number of iterations the simulation will move the particles through
# this is sent to int, so if the output is not a whole number it will go to the next smallest integer
increments = int (timeConst / deltaT)

# X-Value amount that each move L/R will be
moveDistance = math.sqrt(2 * diffCon * deltaT)

# For drift step, move particles by this value on top of the selected move
shiftValue = deltaT * bSpin

# Percentage a particle has of jumping lines
jumpProb = deltaT * gamma

# Lists to hold each series of particles
topParticlesProb = []
bottomParticlesProb = []
topParticlesStep = []
bottomParticlesStep = []

'''   -----------------   Functions start here   -----------------   '''

# C(x, t) where an x-value and a time step are used to calculate the proportion of particles in this place
#       x = xAxis     t = iterations        v = b       D = 1   
def analyticSolution(x, t, v, D=1):    
    lead = 1 / math.sqrt(4 * math.pi * D * t)
    exponent = -1 * ((x - (v * t)) ** 2)/(4 * D * t)
    return lead * (math.e ** exponent)

# This is a function to generate a list of the solution values above
# This takes a list of an x range and the applicable parameters
def makeSolutionList(xRange, t, v, D=1):
    returnList = [] # List holds solutions
    for xVal in xRange: # Iterate through each value on the applicable x-axis 
        returnList.append(analyticSolution(xVal, t, v, D)) # Append the calculation with parameters
    return returnList

# This is a function that takes a list of particle frequency lists. 
# Then uses matplotlib to graph all these functions
def graphMultipleSeries(plots, title, xlabel, ylabel):

    for plot in plots: # Each list entry is a list of parameters and plots: [xVal, yVal, label, color, alpha, style="Plot"]
        xRange = plot[0]
        yValues = plot[1]
        label = plot[2]
        color = plot[3]
        alpha = plot[4]
        style = plot[5]

        if style == "Bar":
            plt.bar(xRange, yValues, label=label, color=color, alpha=alpha, width = 0.3)
        elif style == "Plot":
            plt.plot(xRange, yValues, label=label, color=color, alpha=alpha)
        elif style == "Hist":
            plt.hist(xRange, bins=yValues, label=label, color=color, alpha=alpha)
        else:
            print("Error: Style not found. Using default, Bar.\n")
            plt.bar(xRange, yValues, label=label, color=color, alpha=alpha)


    plt.legend()
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)

# This is a function that calculates the probability that a particle will move either left or right
# A sucess is a move right, a failure is a move left. Probabilities are compliment for each line. Top = P Bottom = 1 - P
# Takes the diffusion constant, b, which is spin, and delta t4
# When b is zero the dr4ift automatically becomes 0.5, however D or b must be nonzero
def moveCalculation(D, b, deltaT):
    # Conditional to prevent divison by zero. This results in the drift being set to 0.5, or even moves left and right
    if D == 0 and b == 0:
        print("Cannot compute. Division by zero. Using value: 0.5")
        return 0.5
    # Return the equation below to calculate the drift. I am not actually sure where this came from but Doctor Harmon sent me it so I use it. 
    # 2D divided by dt is new, previously did not include dt. 
    else:
        return 0.5 * (1 + (b / math.sqrt(((2*D)/deltaT)+(b**2))))

# This is a function that times the program at different points. Mainly used to make this faster, will use more if parallelism comes in
def timing(initTime, createTime, moveTime, graphTime, startTime):
        
    # Since the times are recorded out of the computer clock time, I have to subtract each portion appropriately to get the actual time taken
    graphTime = graphTime - moveTime
    moveTime = moveTime - createTime
    createTime = createTime - initTime
    initTime = initTime - startTime
    totalTime = graphTime + moveTime + createTime + initTime # Total time is the sum of each portion
    
    # Create a proportion for each section of time. 
    
    # Time it took the simulation to graph the particles
    graphTimeProp = 100 * graphTime / totalTime
    # Time it took the simulation to actually run through each iteration
    moveTimeProp = 100 * moveTime / totalTime
    # Time it took to calculate behaviors and set up variables
    createTimeProp = 100 * createTime / totalTime
    # Time it took to initalize each partile, creating a tuple and then adding it to the list
    initTimeProp = 100 * initTime / totalTime

    # Get the magnitude for each number in creation, move time, and total time
    # These sections of the time are where it will slow down as the number of particles / timesteps grow
    createTimeMag = int(abs(createTime))
    moveTimeMag = int(abs(moveTime))
    totalTimeMag = int(abs(totalTime))
    graphTimeMag = int(abs(graphTime))

    # Initialize a varaible that defaults to milliseconds
    createTimeUnit = 'seconds'
    moveTimeUnit = 'seconds'
    totalTimeUnit = 'seconds'
    graphTimeUnit = 'seconds'

    # If the magnitude gets into ranges that are easier expressed in seconds, I divide by 1000 and change the unit to seconds
    # I only did this for creation, move, and total time since these will be dependent on the amount of particles
    
    # Graph Time
    if graphTimeMag < 1:
        graphTime = graphTime * 1000
        graphTimeUnit = 'miliseconds'

    # Creation time
    if createTimeMag < 1:
        createTime = createTime * 1000
        createTimeUnit = 'miliseconds'

    # Move time
    if moveTimeMag < 1:
        moveTime = moveTime * 1000
        moveTimeUnit = 'miliseconds'

    # Total time
    if totalTimeMag < 1:   
        totalTime = totalTime * 1000
        totalTimeUnit = 'miliseconds'

    # Print the details of the timing for this program
    print("\n\n\n----------------- Timing Details -----------------")
    print(f" Total time elapsed: {totalTime:.2f} {totalTimeUnit}")
    print(f"Initialization time: {initTime:.2f} milliseconds - {initTimeProp:.2f}%")
    print(f"      Creation Time: {createTime:.2f} {createTimeUnit} - {createTimeProp:.2f}%")
    print(f"          Move Time: {moveTime:.2f} {moveTimeUnit} - {moveTimeProp:.2f}%")
    print(f"      Graphing Time: {graphTime:.2f} {graphTimeUnit} - {graphTimeProp:.2f}%")
    print(f"--------------------------------------------------")

# Updated 10/17, now has entirely different functionality
# Takes a boolean for the line it resides on
# Returns the value the particle should move by
def moveParticleProb(isTop=True):
    if isTop: # If the particle is on the top line
        moveProb = moveCalculation(diffCon, bSpin, deltaT)
    else:
        moveProb = moveCalculation(diffCon, -bSpin, deltaT)
        
    if np.random.rand() < moveProb: # If the move succeds
        return moveDistance
    else:
        return -moveDistance
            
# This functions is similar to the one above, but it moves particles with a value as drift instead of probability
# Therefore all particles move with 50/50 L/R, but there is an additional value applied after every move
def moveParticleStep(isTop=True):
    if isTop: # If the particle is on the top line
        if np.random.rand() < 0.5: # If the random value is less than 50% (success)
            return shiftValue + moveDistance # Move particle right/positive, top line makes drift positive
        else: # If the random value is more than 50% (failure)
            return shiftValue - moveDistance # Move particle left/negative, top line makes drift positive
    else: # If the particle is on the bottom line
        if np.random.rand() < 0.5: # If the random value is less than 50% (success)
            return -shiftValue + moveDistance # Move particle right/positive, bottom line makes drift negative
        else: # If the random value is more than 50% (failure)
            return -shiftValue - moveDistance # Move particle right/positive, top line makes drift positive

initTime = time.perf_counter()

''' Run Stage '''

# Create particles
for i in range(numParticles // 2):
    # Half the particles start on the top line
    topParticlesProb.append(0)
    topParticlesStep.append(0)
for i in range(numParticles // 2):
    # Other half start on the bottom line
    bottomParticlesProb.append(0) 
    bottomParticlesStep.append(0)

createTime = time.perf_counter()

# Run simulation through each iteration

# Temp lists to add jumped particles to, used for avoiding multiple steps in one iteration. See changes for full description 10/21
tempTopProb = []
tempBottomProb = []
# Run simulation for the first movement style
for i in range(int(increments)):
    for index, particle in enumerate(topParticlesProb): # For each particle in the top list
        if np.random.rand() < jumpProb: # If the particle jumps to another line
            tempTopProb.append(particle) # Append it to the temp list, wait to add to other line until end of iteration
        else: # If the particle stays on it's line
            topParticlesProb[index] += moveParticleProb(True) # Move particle

    for index, particle in enumerate(bottomParticlesProb): # Same behavior for bottom particles
        if np.random.rand() < jumpProb: # If the particle jumps to another line
            tempBottomProb.append(particle) # Append it to the temp list, wait to add to other line until end of iteration
        else: # If the particle stays on it's line
            bottomParticlesProb[index] += moveParticleProb(False) # Move particle
    
    # After all particles have been altered, fix the jumped particles by appending temp list to total particles list
    for item in tempTopProb: # For each particle that jumped this iteration
        bottomParticlesProb.append(item) # Append it to the other list
        topParticlesProb.remove(item) # Remove it from the current list
    for item in tempBottomProb: # Same steps for bottom line jumps
        topParticlesProb.append(item)
        bottomParticlesProb.remove(item)
    # Clear the lists
    tempBottomProb = []
    tempTopProb = []


moveTime = time.perf_counter()

''' Graph / prep stage '''

# Convert to a list then back to a set to get all entries without duplicates
xValsTop = sorted(list(set(topParticlesProb)))
xValsBottom = sorted(list(set(bottomParticlesProb)))

xFreqTop = []
xFreqBottom = []

solTop = []
solBottom = []

# Using those x-values, calculate each solution point
for item in xValsTop:
    # Appends occurences of given x over total particles, or frequency
    xFreqTop.append(topParticlesProb.count(item) / len(topParticlesProb))
    solTop.append(analyticSolution(item, timeConst, bSpin, diffCon))
for item in xValsBottom:
    solBottom.append(-analyticSolution(item, timeConst, -bSpin, diffCon))
    xFreqBottom.append(-(bottomParticlesProb.count(item)) / len(bottomParticlesProb))



# solTop = [item * (math.sqrt(deltaT * 8)) for item in solTop]
# solBottom = [-item * (math.sqrt(deltaT * 8)) for item in solBottom]
plt.bar(xValsTop, xFreqTop)
plt.bar(xValsBottom, xFreqBottom)
plt.plot(xValsTop, solTop)
plt.plot(xValsBottom, solBottom)
plt.show()
sys.exit()


solTSeries = [xValsTop, solTop, "Solution", "black", 1, "Plot"]
solBSeries = [xValsBottom, solBottom, "Solution", "black", 1, "Plot"]
partTSeries = [xValsTop, xFreqTop, "Top Particles", "blue", 0.5, "Bar"]
partBSeries = [xValsBottom, xFreqBottom, "Bottom Particles", "red", 0.5, "Bar"]

seriesList = [partTSeries, partBSeries, solTSeries, solBSeries]
title = f"{numParticles} Random Walkers Taking {moveDistance:.2f} Sized Steps For {increments} Moves"

graphMultipleSeries(seriesList, title, "X-Value", "Particle Frequency")
# Time it took to graph the data. Will be the first thing subtracted from the start time to get the total time
graphTime = time.perf_counter()

# Using plt.show outside of the graph function to maintain continuity with graph time
plt.show()

# Timing function to reflect time invervals of the code
timing(initTime, createTime, moveTime, graphTime, startTime)

moveProb = moveCalculation(diffCon, bSpin, deltaT)

print("\n\n\n---------------------Behavior---------------------")
print(f"         Move Distance: {moveDistance}")
print(f"            Increments: {increments}")
print(f"                 Drift: {moveProb:.2f}")
print(f"                  Jump: {jumpProb}")
print("--------------------------------------------------")

""" 919


v is b
D is 1

Goals:
    Dicsover the behavior of the sqrt(8*dt) dependence between fourier transform and particles
    Alter the behavior to now add drift as a constant instead of manipulating probabilities
    Keep time 40 and dt gets smaller
    
    + bdt

        Is this how much I am supposed to add by in the alternative version of moving? Will be checking this
        Yes it is 
"""