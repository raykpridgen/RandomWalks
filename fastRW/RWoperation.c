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
#include "pcg_basic.h"
#include "help/helper.h"

#define SHM_SIZE 3908
#define SHM_KEY 4755


int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RWoperation.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }
    double startTime = omp_get_wtime();
    printf("C Project running\n");
    
    // Parameters
    float deltaT = atof(argv[1]);
    float timeConst = atof(argv[2]);
    float diffCon = atof(argv[3]);
    float bSpin = atof(argv[4]);
    float gamma = atof(argv[5]);
    int numParticles = atoi(argv[6]);
    int coresToUse = atoi(argv[7]);
    int step = 50; // How many iterations to run before sending data

    // Behavior calculations
    float moveDistance = sqrt(2 * diffCon * deltaT);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    if (coresToUse > omp_get_num_procs()) {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } else {
        printf("Using %d threads.\n", coresToUse);
    }
    omp_set_num_threads(coresToUse);

    // Storage to hold each thread's rng state
    pcg32_random_t *rng_states = malloc(coresToUse * sizeof(pcg32_random_t));
    // Storage to hold particles to be moved by simulation
    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    // Confirm allocation for all
    if (rng_states == NULL || particleListProb == NULL) {
        perror("Failed to allocate memory, returning");
        exit(EXIT_FAILURE);
    }
    
    // Clear memory for each allocation to ensure proper data storage
    printf("Clearing memory for rng_states\n");
    memset(rng_states, 0, coresToUse * sizeof(pcg32_random_t));
    printf("Clearing memory for particleListProb\n");
    memset(particleListProb, 0, numParticles * sizeof(Particle));

    // Create shared memory block to send data elsewhere
    int shm_id = shmget(SHM_KEY, sizeof(ParticleDataList), IPC_CREAT | 0666);

    // Set unique states for each thread, used for randomness
    initialize_rng_states(coresToUse, rng_states);

    // Generate particles within particle list, this is where origins are defined
    initializeParticles(particleListProb, numParticles);
    //initializeParticles(particleListStep, numParticles);

    printf("Starting simulation...\n");
    double simStart = omp_get_wtime();

    int numMovesProb = 0;
    int numJumpsProb = 0; 

    // Increments are set here
    printf("Began computing...\n");
    for (int i = 0; i < increments; i++) {
        
        // Move particles
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++)
        {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance, rng_states);
            //moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }

        if (i % step == 0 && i != 0)
        {
            // Send data to python
            printf("Waiting for python...\n");
            while (shared_memory->read == false)
            {
                // Optional: Sleep for a brief moment to avoid excessive CPU usage
                sleep(0.5);
            }
            
            #pragma omp single
            {
                // Send data to python here
                particlesToFrequency(particleListProb, numParticles, &shared_memory);   
            }
        }
    }

    double simEnd = omp_get_wtime();
    printf("Simulation completed in %.2f seconds\n", simEnd - simStart);

    // Detach the shared memory segment
    if (shmdt(shared_memory) == -1) {
        perror("shmdt");
        exit(EXIT_FAILURE);
    }

    free(particleListProb);

    //free(particleListStep);
    free(rng_states);

    //printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}