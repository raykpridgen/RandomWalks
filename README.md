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

