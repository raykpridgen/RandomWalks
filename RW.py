import numpy as np
import time
import math
import matplotlib.pyplot as plt

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

# This is a function that calculates the actual distance a particle will move when an x-axis move occurs. Takes delta t and the diffusion constant 
def particleMoveDistance(deltaT, D):
    # Return 2 times diffusion constant times delta t. 
    return math.sqrt(2 * D * deltaT)

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

# This function takes a particle as a tuple coordinate, along with the behaviors, then moves part appropriately by returning a new particle
# Takes the particle as a tuple, probability of jumping to the next line, probability of moving on the x-axis, and the most distance on x-axis
def moveParticleProb(particle, jumpProb, moveProb, moveDistance):
    # The simulation models concurrent flow, so the move probability is the compliment of that of the top line
    if particle[1] == 0: # If particle is on bottom line
        moveProb = 1 - moveProb # Get compliment of move probability
    
    jumpRand = np.random.rand() # Random variable for jumping to another y value (zero or one)
    if jumpRand < jumpProb: # If jump succeeds, move particle to the other line
        if particle[1] == 1:
            return (particle[0], 0)
        else:
            return (particle[0], 1)

    else: # If particle jump fails, do a move on the x-axis
        moveRand = np.random.rand() # Random value for moving to another x coordinate
        if moveRand < moveProb: # If move succeeds, traverse right
            return (particle[0] + moveDistance, particle[1])
        else: # If move fails, traverse left
            return (particle[0] - moveDistance, particle[1])

# This functions is similar to the one above, but it moves particles with a value as drift instead of probability
# Therefore all particles move with 50/50 L/R, but there is an additional value applied after every move
def moveParticleStep(particle, jumpProb, shiftVal, moveDistance):
    # The simulation models concurrent flow, so the move probability is the compliment of that of the top line
    if particle[1] == 0: # If particle is on bottom line
        shiftVal = - shiftVal # Get compliment of move
    
    jumpRand = np.random.rand() # Random variable for jumping to another y value (zero or one)
    if jumpRand < jumpProb: # If jump succeeds, move particle to the other line
        if particle[1] == 1:
            return (particle[0], 0)
        else:
            return (particle[0], 1)

    else: # If particle jump fails, do a move on the x-axis
        moveRand = np.random.rand() # Random value for moving to another x coordinate
        if moveRand < 0.5: # If move succeeds, traverse right
            return (particle[0] + moveDistance + shiftVal, particle[1])
        else: # If move fails, traverse left
            return (particle[0] - moveDistance + shiftVal, particle[1])    

# This function moves all the particles in one timestep
# Takes the full list of particles, drift probability, jump probability, and move distance
def moveParticles(particleList, jumpProb, LRProb, moveDistance):
    newList = [] # New list to hold updated particles
    for particle in particleList: # For each particle
        newParticle = moveParticleProb(particle, jumpProb, LRProb, moveDistance) # Calculate the new move
        newList.append(newParticle) # Append the new particle to the new list
    return newList # Return the list

def moveParticlesStep(particleList, jumpProb, shiftVal, moveDistance):
    newList = [] # New list to hold updated particles
    for particle in particleList: # For each particle
        newParticle = moveParticleStep(particle, jumpProb, shiftVal, moveDistance) # Calculate the new move
        newList.append(newParticle) # Append the new particle to the new list
    return newList # Return the list

# Clock time to record when the program starts
startTime = time.perf_counter()

# This is a boolean to hold the type of simulation to run. 
# Can be the sim with the drift calculated as probability, or calculated with the added drift amount.
# Difference is using moveParticleProb vs moveParticleStep
# True is prob, false is step
simType = True

''' Initialization stage '''

# Parameters
deltaT = 0.5
timeConst = 10
diffCon = 1
bSpin = 0.5
gamma = 0
numParticles = 10000

# Behavior of the simulation
# Number of iterations the simulation will move the particles through
# this is sent to int, so if the output is not a whole number it will go to the next smallest integer
increments = int (timeConst / deltaT)

# Distance each particle will move left or right
moveDistance = particleMoveDistance(deltaT, diffCon)
# Probability a particle will jump to another line
jumpProb = deltaT * gamma
# Probability a particle will move either left or right
moveProb = moveCalculation(diffCon, bSpin, deltaT)

# List for the particles to be stored in
particleList = []

initTime = time.perf_counter()

''' Run Stage '''

# Create particles
for i in range(numParticles // 2):
    particleList.append((0, 1)) # Half the particles start on the top line
for i in range(numParticles // 2):
    particleList.append((0, 0)) # Other half start on the bottom line
createTime = time.perf_counter()

# Run simulation through each iteration
for i in range(int(increments)):
    particleList = moveParticles(particleList, jumpProb, moveProb, moveDistance) # Change each particle

moveTime = time.perf_counter()

''' Graph / prep stage '''

# Initialize lists for x-values and particle counts
particleRange = [i * moveDistance for i in range(-increments, increments + 1)]
particlesTop = [0] * len(particleRange)
particlesBottom = [0] * len(particleRange)

# Count the particles on the top and bottom lines
for particle in particleList:
    # X value from tuple, remove moveDistance factor by dividing, and then add the number of increments to cancel negative values
    index = int((particle[0] / moveDistance) + increments)  # Calculate index for x-value
    # Apply particles to different lists based on line
    if particle[1] == 1:
        particlesTop[index] += 1
    elif particle[1] == 0:
        particlesBottom[index] += 1

# Calculate total particles for normalization (Don't crucify me for using this term, I am not sure this is used in the right context)
# I realize this part may be causing an issue, since the way the proportion can be interpreted two ways:
# Either number of particles on x / particles on line   OR   number of particles on x / total particles
topAmount = sum(particlesTop)
bottomAmount = sum(particlesBottom)

# Normalize counts to proportions
particlesTop = [count / topAmount for count in particlesTop]
particlesBottom = [-count / bottomAmount for count in particlesBottom]
solTop = makeSolutionList(particleRange, timeConst, bSpin, diffCon)
solBottom = makeSolutionList(particleRange, timeConst, -bSpin, diffCon)

solTop = [item * (math.sqrt(deltaT * 8)) for item in solTop]
solBottom = [-item * (math.sqrt(deltaT * 8)) for item in solBottom]

solTSeries = [particleRange, solTop, "Solution", "black", 1, "Plot"]
solBSeries = [particleRange, solBottom, "Solution", "black", 1, "Plot"]
partTSeries = [particleRange, particlesTop, "Top Particles", "blue", 0.5, "Bar"]
partBSeries = [particleRange, particlesBottom, "Bottom Particles", "red", 0.5, "Bar"]

seriesList = [solTSeries, solBSeries, partTSeries, partBSeries]
title = f"{numParticles} Random Walkers Taking {moveDistance:.2f} Sized Steps For {increments} Moves"

graphMultipleSeries(seriesList, title, "X-Value", "Particle Frequency")

# Time it took to graph the data. Will be the first thing subtracted from the start time to get the total time
graphTime = time.perf_counter()

# Using plt.show outside of the graph function to maintain continuity with graph time
plt.show()

# Timing function to reflect time invervals of the code
timing(initTime, createTime, moveTime, graphTime, startTime)

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