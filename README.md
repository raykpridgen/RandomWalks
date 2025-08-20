# Random Walks
This repository holds code for my research involving countercurrent and cocurrent flow in a random walks environment. 

## General Workflow
The program is invoked by running a python file, that will call a C program. These work in tandem to generate and plot the particles. The C program is responsible for random particle operations, utilizing parallel processing to increase speed of output. The data for the particles are placed within a shared memory block, where the Python program can then access, process, and plot the particles. This is accomplished by using a primitive version of a semaphore that dictates read / write access. PyQt is used as a visual interface to display a particle distribution and alter parameters.  

Note: The folder "robust" contains the most recent work. Operate within this folder to access the GUI interface / parallelized simulation.

## Simulation
The simulation itself takes place on a one-dimensional plane, with a boolean condition that determines behavior. This can be thought of as an x-axis and two values on the y-axis. Particles move in a psuedo-random manner that is determined by several parameters used in equations that determine x-axis move probability (moves), probability for the particle to change the boolean y-axis value (jumps), move distance, and increments.

Each particle begins an increment by generating a random number compared with a probability to "jump" to the other y-axis. If this jump succeeds, no other action is taken until the next increment. If it fails, the particle then generates a second number to compare against the "move" probability. A success is a discrete move in one direction and a failure is a move in the other direction. 

During countercurrent flow, particles on one y-axis will be influenced by a bias in the move probability, and the particles on the other y-axis will be influenced in an inverse manner. Cocurrent flow can be easily acheived by removing the logic for "localMoveProb" in the moveParticles function, so that the bias of each particle will be the same regardless of the y-axis. 

## Parameters
dt : Influences increments, jump probability, and in some cased move probability

T : Time constant: Used with dt to determine number of increments the simulation will execute

D : Diffusion constant: Influences move distance with dt, and probability of an x-axis move

b : Drift constant: Biases the move probability of a particle on the x-axis

Gamma : "Jump" / flip constant: Influences the probability a particle will switch to the other y-axis with dt 

Count : Number of particles to simulate

## Equations
moveProbCalc - Probability for an individual move.
 - Parameters: dt, D, b
 - See code for logic implementation

moveDistanceCalc - Determines size of an individual move
 - Parameters: dt, D
 - sqrt(2Ddt)

Jump Probability
 - Paramters: dt, gamma
 - dt * gamma

Increments
 - Parameters: dt, T
 - T / dt

## Installation / Setup
For C support, a C compiler is needed with OMP support, as well as a POSIX system.

For Python dependencies, Python 3.10+ is required. 

A virtual environment is recommended:

- python -m venv venv

(Linux/Mac)

- source venv/bin/activate

(Windows)

- venv\Scripts\activate

Install Python dependencies from requirements.txt

- pip install -r requirements.txt

WITHIN "robust" FOLDER

Compile the C program 

- make clean
- make
- python3 main.py