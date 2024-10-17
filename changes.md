Thought I should start doing this to keep track of what I am doing

# 10/08/2024

Check function?

Update github

graph func

# 10/09/2024
Met w/ Harmon about graph issue

# 10/10/2024
Equation is fixed
After conferring, realized that the issue is probably with my current python code
    Not the equation, this mathces the mathematica code
    RWMath.py within mathematica also matches mathematica code
    Therefore it must be something with RW.py

# 10/11-12/2024
Research meeting today - learned some cool stuff about the band gap
    
## I have fixed all current problems. The simulated particles match the solution in Python and Mathematica.
The issue was with the way I was calculating the solution in python. Although I had everything straightened out in MMA,
I still had an underlying issue with the independent python code. The solution was showing up short of the simulated particles.
I found out that I was calculating x-values for each series a little different:

Simulated particles would be calculated with an adjusted range with the move distance.

Solution y-values would be calculated with the plain, incremented x-values without the move distance factor.

## Now I have several questions:
Two ways of using sim - Calculate drift with prob move L/R, or Calculate drift with an x-value addition to each step?

Can I make these two methods of sim match? What are the fudge factor(s) between these two methods? 

How can I improve the performance of this code? Should I consider eventually switching to another language like C?

# 10/17/2024
I realized I have to change the way the simulation stores the particle data. I cannot use a list of tuples, this is pretty inefficient. Instead I am going to use a list that holds entries of the Y values of each series. 
