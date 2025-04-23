# Random Walks
This repository is to hold code for the research involving Random Walks and Countercurrent / Cocurrent flow.

The simulation is run through a python file RW.py, which calls a RWoperation.c executable. The bulk of the simulation is done with C, and then Python is used to represent the data to the user. This simulation models random walks of particles in two 1D planes. There is a "top" and a "bottom" line, in which particles can exist. These particles move either according to a probability function, or a shift value. These two behaviors are simulated at the same time, and expect similar results. 

Probability:
  Calculates probability to jump to the other line first
  If jump probability fails, a move probability is then calculated
  Left and right probabilities are calculated differently based on the line the particle exists on

Step / Shift:
  Calculates probability to jump to the other line first
  If jump probability fails, a 50% probability to move left or right is calculated
  After the particle moves, an additional shift value is added to it's x position

## Takes the following parameters:
dt - delta t

T - Time constant

D - Diffusion constant

b - spin constant

gamma - jump factor

numParticles - number of particles to simulate

Python initializes both semaphores and shared memory, then starts the C program.
C program runs a batch in moveParticles:
Acquires /particle_sem.
Updates particleList.
Releases /particle_sem.
Posts /particle_ready to signal completion.
Python waits on /particle_ready:
Once signaled, acquires /particle_sem.
Reads particleList.
Releases /particle_sem.
Updates the plot.
Repeat for each batch until the C program completes.

c / usleep uses microseconds
py / timer uses milliseconds
1 second = 1,000 milliseconds = 1,000,000 microseconds
0.1s = 100ms = 100,000mcs

current:
1,000 ms = 1 second
10,000 mcs = 0.01 second