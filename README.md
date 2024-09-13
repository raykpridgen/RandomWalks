This repository is to hold code for the research involving Random Walks and Countercurrent flow.
The python code simulates two lines on the x-axis in space, where particles on these lines move in a discrete manner, either positive or negative x. 
Additionally, there is a factor which controls if / at what frequency the particles can jump to the other line. 
Lines are represented as up and down, similar to up and down spin in electrons. 
In this simulation, I define a move as a change on the x-axis, and a jump as a change on the y-axis

Takes the following parameters:
dt - delta t
  T - Time constant
  D - Diffusion constant
  b - spin constant
  gamma - jump factor

Equations are used to calculate the behaviors:
  Number of iterations (times each particle is allowed to move)
  Move distance
  Move drift (probability a particle will move left or right)
