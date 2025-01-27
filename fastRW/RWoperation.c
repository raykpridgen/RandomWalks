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
#include "pcg_basic.h"
#include "help/helper.h"

#define SHM_NAME "/RandomWalksData"  // Shared memory name
#define SHM_SIZE 4096  // Shared memory size


int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RWoperation.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }
    double startTime = omp_get_wtime();
    
    // Parameters
    float deltaT = atof(argv[1]);
    float timeConst = atof(argv[2]);
    float diffCon = atof(argv[3]);
    float bSpin = atof(argv[4]);
    float gamma = atof(argv[5]);
    int numParticles = atoi(argv[6]);
    int coresToUse = atoi(argv[7]);
    
    // Step for GUI
    int step = 10;
    

    if (coresToUse > omp_get_num_procs()) {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } else {
        printf("Using %d threads.\n", coresToUse);
    }
    omp_set_num_threads(coresToUse);
    initialize_rng_states(coresToUse);

    float moveDistance = sqrt(2 * diffCon * deltaT);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    //printf("--------- Behavior ---------\n");
    //printf("Increments:          %d\nNumber of Particles: %d\nMove Distance:       %.4f\nMove Probability:    %.4f\nJump Probability:    %.4f\nShift Value:         %.4f\n", increments, numParticles, moveDistance, moveProb, jumpProb, shiftValue);
    //printf("----------------------------\n");

    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    ParticleDataList *freqList = malloc(sizeof(ParticleDataList));  // Allocate memory for freqList
    if (!freqList) {
        fprintf(stderr, "Memory allocation failed for freqList\n");
          exit(1);
    }
    memset(freqList, 0, sizeof(ParticleDataList));  // Clear memory

    //Particle *particleListStep = malloc(numParticles * sizeof(Particle));
    if (!particleListProb) {
        fprintf(stderr, "Memory allocation failed for particle lists\n");
        return 1;
    }
    
    initializeParticles(particleListProb, numParticles);
    //initializeParticles(particleListStep, numParticles);

    printf("Starting simulation...\n");
    double simStart = omp_get_wtime();

    int numMovesProb = 0;
    int numJumpsProb = 0; 

    // Open or create shared memory
    int shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) 
    {
        perror("shm_open failed");
        exit(1);
    }

    
    // Set the size of the shared memory
    ftruncate(shm_fd, SHM_SIZE);
    void *shm_ptr = mmap(0, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shm_ptr == MAP_FAILED) 
    {
        perror("mmap failed");
        exit(1);
    }
    
    // Pointer to the first part of the shared memory (data + size + flag)
    ParticleDataList *particleDataList = (ParticleDataList*)shm_ptr;
    int *data_size = (int*)shm_ptr;  // To store the number of particles
    int *updated_flag = (int*)(shm_ptr + sizeof(int));  // To store updated flag

    // Clear the memory (this should be done before writing new data)
    memset(particleDataList, 0, SHM_SIZE);


    // Increments are set here
    for (int i = 0; i < increments; i++) {
        // One thread moves two particles
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance);
            //moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }
        if (i % step == 0)
        {
            // Send data to python
            while (freqList->read == false)
            {
                // Optional: Sleep for a brief moment to avoid excessive CPU usage
                sleep(0.5); // Uncomment this line if needed
            }
            int freqCount = 0;
            // Send data to python here
            particlesToFrequency(particleListProb, numParticles, &freqList, &freqCount);
            for (int j = 0; j < freqCount; j++)
            #pragma omp critical
            {
                // Update shared memory
                particleDataList->particles[j].x = freqList->particles[j].x;
                particleDataList->particles[j].y = freqList->particles[j].y;
                particleDataList->particles[j].freqx = freqList->particles[j].freqx;
                
            }
            particleDataList->read = false;
        }
    }

    double simEnd = omp_get_wtime();
    printf("Simulation completed in %.2f seconds\n", simEnd - simStart);

    free(particleListProb);
    free(freqList);  // If freqList was dynamically allocated

    //free(particleListStep);
    free_rng_states();

    //printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}