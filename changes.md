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
## Drift step implementation
Delayed, need to rework base code. See next section

## Changing the behavior
List of tuples was a bad way to implement the simulation. Tuples are immutable so I am making the particles move by deleting them and making new ones every time. Instead I am going to use a list of positions, so I can just use the same list to add and delete values. 

# 10/18-19/2024
## Behavior changes
So I realized why I can't use a barebones list of each particle. Although it does work for plotting a single histogram, things get complicated when I plot the top and bottom line together. To fix this I think I will just go back to calculating proportions for each x-value. 

# 10/21/2024
## Finishing behavior
Small issue with new method: 
    How do I move a particle to another list, and then ignore it when I go to move the other list's particles?
    Example:
        If Jump happens, append particle to bottom list, delete from top list
        Particle is now on the bottom line, and has moved this iteration.
        Now particle is on the bottom line. When I go to move the particles in there, I see this particle and move it a second time
        Maybe I will use a temp list for each list so I can add particles to the temp list, but only insert them into the original lists after the end of the iteration.
