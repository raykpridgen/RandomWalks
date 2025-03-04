#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <float.h>
#include <limits.h>
#include <fcntl.h>  // For shm_open() flags (O_CREAT, O_RDWR)
#include <sys/mman.h>  // For mmap(), MAP_SHARED
#include <sys/stat.h>  // For mode constants (0666)
#include <string.h>  // For memset() (if needed)
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h> 
#include "inc/pcg_basic.h"
#include "inc/helper.h"

#define SHM_NAME "/particle_shm"
#define PARTICLE_COUNT 325


int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RWoperation.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }
    printf("Simulation Running...\n");
    
    // Parameters
    float deltaT = atof(argv[1]); // Delta t
    float timeConst = atof(argv[2]); // Time Constant
    float diffCon = atof(argv[3]); // Diffusion Constant
    float bSpin = atof(argv[4]); // beta / bias
    float gamma = atof(argv[5]); // Gamma
    int numParticles = atoi(argv[6]); // Number of particles
    int coresToUse = atoi(argv[7]); // Cores to use in multithreading
    int step = 50; // How many iterations to run before sending data

    // Behavior calculations
    float moveDistance = moveDistanceCalc(diffCon, deltaT);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;

    // Error detection for incorrect cores
    if (coresToUse > omp_get_num_procs()) 
    {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } 
    else 
    {
        printf("Using %d threads.\n", coresToUse);
    }
    omp_set_num_threads(coresToUse);

    // Allocate specific storage for each cores RNG state
    pcg32_random_t *rng_states = malloc(coresToUse * sizeof(pcg32_random_t));

    // Confirm allocation 
    if (rng_states == NULL) 
    {
        perror("Failed to allocate memory, returning");
        exit(EXIT_FAILURE);
    }
    
    // Clear memory for each allocation to ensure proper data storage
    memset(rng_states, 0, coresToUse * sizeof(pcg32_random_t));

    // Set unique states for each thread, used for randomness
    initialize_rng_states(coresToUse, rng_states);

    // Open shared memory and populate particles with 0s
    ParticleStruct* particleList = initializeParticles();
    if (particleList == NULL)
    {
        perror("Failed to init particles. Returning.\n");
    }

    printf("Initialization complete...\n");

    int numMovesProb = 0;
    int numJumpsProb = 0; 

    
    printf("Computing...\n");
    // For each increment defined
    for (int g = 0; g < (int)increments / step; g++)
    {
        // If read flag is marked read
        if (particleList->read)
        {
            printf("Data received from Python....\n");
            // Perform this step's iterations
            moveParticles(particleList, moveProb, jumpProb, rng_states, step);
        }
        // While flag is set to unread
        while (!particleList->read)
        {   
            // Wait for python
            sleep(1);
        }
        
    }
    
    //free(particleListStep);
    free(rng_states);

    //printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}