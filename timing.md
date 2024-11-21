## Timing for Random Walks Simulation
The purpose of this file is to manage timing for each type of simulatiob, so I know what to expect. 

Format is Walkers, Particles, Time

May be automating this later on
# No Coupling, zero gamma


## Research Computer
48 total cores
Overhead makes it slower sometimes

# 100,000 Walkers and 1,000 Steps
48 Cores - 188 seconds
24 Cores - 89 seconds
12 cores - 86 seconds
8 cores - 81 seconds
4 cores - 49 seconds
2 cores - 27 seconds
1 core - 6.13 seconds

WTH?
Maybe size is too small

# 1,000,000 Walkers and 1,000 Steps
1 core - 52 seconds
2 cores - 204 seconds
4 cores - 