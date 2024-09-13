import numpy as np
import math

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

''' Initialization stage '''

# Parameters
deltaT = 0.1
timeConst = 2
diffCon = 20
bSpin = 0
gamma = 0
numParticles = 100000

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


''' Run Stage '''

# Create particles
for i in range(numParticles // 2):
    particleList.append((0, 1)) # Half the particles start on the top line
for i in range(numParticles // 2):
    particleList.append((0, 0)) # Other half start on the bottom line

# Run simulation through each iteration
for i in range(int(increments)):
    particleList = moveParticles(particleList, moveProb, jumpProb, moveDistance) # Change each particle

''' Graph / prep stage '''

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

topData = []
bottomData = []
for i in range(0, increments*2 + 1):
    topData.append((particleRange[i], particlesTop[i]))
    bottomData.append((particleRange[i], particlesBottom[i]))

totalData = [topData, bottomData]
