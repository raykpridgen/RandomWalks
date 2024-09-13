import math
import numpy as np
import matplotlib.pyplot as plt

# This is a function that calculates the probability that a particle will move either left or right
# A sucess is a move right, a failure is a move left. Probabilities are compliment for each line. Top = P Bottom = 1 - P
# Takes the diffusion constant, b, which is spin, and delta t4
# When b is zero the drift automatically becomes 0.5, however D or b must be nonzero
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

# This function takes a particle as a tuple coordinate, along with the behaviors, then moves it appropriately by returning a new particle
# Takes the particle as a tuple, probability of jumping to the next line, probability of moving on the x-axis, and the most distance on x-axis
def moveParticle(particle, jumpProb, moveProb, moveDistance):
    
    # The simulation models concurrent flow, so the move probability is the compliment of that of the top line
    if particle[1] == 0: # If particle is on bottom line
        moveProb = 1 - moveProb # Get compliment of move probability
    
    jumpRand = np.random.rand() # Random variable for jumping to another y value (zero or one)
    if jumpRand < jumpProb: # If jump succeeds, move particle to the other line
        if particle[1] == 1:
            newParticle = (particle[0], 0)
        else:
            newParticle = (particle[0], 1)

    else: # If particle jump fails, do a move on the x-axis
        moveRand = np.random.rand() # Random value for moving to another x coordinate
        if moveRand < moveProb: # If move succeeds, traverse right
            newParticle = (particle[0] + moveDistance, particle[1])
        else: # If move fails, traverse left
            newParticle = (particle[0] - moveDistance, particle[1])

    return newParticle

# This function moves all the particles in one timestep
# Takes the full list of particles, drift probability, jump probability, and move distance
def moveParticles(particleList, LRProb, jumpProb, moveDistance):
    newList = [] # New list to hold updated particles
    for particle in particleList: # For each particle
        newParticle = moveParticle(particle, jumpProb, LRProb, moveDistance) # Calculate the new move
        newList.append(newParticle) # Append the new particle to the new list
    return newList # Return the list

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

# This is a function that graphs the simulation into matplotlib
def graphing(increments, moveDistance, particleList):

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

# This is a function that initalizes a simulation to run
def initSimulation(deltaT, Time, Diff, b, gamma):
    increments = int (Time / deltaT)
    # Distance each particle will move left or right
    moveDistance = particleMoveDistance(deltaT, Diff)
    # Probability a particle will jump to another line
    jumpProb = deltaT * gamma
    # Probability a particle will move either left or right
    moveProb = moveCalculation(Diff, b, deltaT)

def particleCreeator(numParticles):
    particleList = []
    # Create particles
    for i in range(numParticles // 2):
        particleList.append((0, 1)) # Half the particles start on the top line
    for i in range(numParticles // 2):
        particleList.append((0, 0)) # Other half start on the bottom line

    return particleList
