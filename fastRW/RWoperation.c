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

#define SHM_KEY 4755  // Shared memory name
#define SHM_SIZE 1208  // Shared memory size


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
    
    // Step for GUI
    int step = 50;

    pcg32_random_t *rng_states = malloc(coresToUse * sizeof(pcg32_random_t));
    // Allocate memory for the RNG states for all threads before the parallel region
    if (!rng_states) {
        fprintf(stderr, "Memory allocation failed for RNG states\n");
        exit(1);
    }

    

    if (coresToUse > omp_get_num_procs()) {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } else {
        printf("Using %d threads.\n", coresToUse);
    }
    omp_set_num_threads(coresToUse);
    initialize_rng_states(coresToUse, rng_states);

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
    if (freqList == NULL) {
        perror("Failed to allocate memory for freqList");
        exit(EXIT_FAILURE);
    }
    printf("Clearing memory for freq list\n");
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

   
    int shm_id = shmget(SHM_KEY, SHM_SIZE, IPC_CREAT | 4755);
    struct shmid_ds shm_info;
    //if (shmctl(shm_id, IPC_STAT, &shm_info) == -1) {
    //    perror("shmctl IPC_STAT failed");
    //    exit(1);
    //}

    // Modify permissions to 0666 (read/write for all)
    //shm_info.shm_perm.mode = 0666;

    // Set the new permissions using shmctl
    //if (shmctl(shm_id, IPC_SET, &shm_info) == -1) {
       // perror("shmctl IPC_SET failed");
        //exit(1);
    //}
    //if (shm_id == -1)
    //{
    //    perror("shmget failed");
    //    exit(1);
    //}
    
    // Pointer to the first part of the shared memory (data + size + flag)
    ParticleDataList *particleDataList = (ParticleDataList*)shmat(shm_id, NULL, 0);
    if (particleDataList == NULL) {
        perror("Failed to allocate memory for particleDataList");
        exit(EXIT_FAILURE);
    }
    printf("Clearing memory for particledatalist\n");
    memset(particleDataList, 0, SHM_SIZE);

    int *data_size = (int*)shmat(shm_id, NULL, 0);  // To store the number of particles
    int *updated_flag = (int*)(shmat(shm_id, NULL, 0) + sizeof(int));  // To store updated flag
    printf("Stored number of particles and flag: %ls, %ls   \n", data_size, updated_flag);
    // Clear the memory (this should be done before writing new data)


    // Increments are set here
    printf("Began computing...\n");
    for (int i = 0; i < increments; i++) {
        // One thread moves two particles
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance, rng_states);
            //moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }
        if (i % step == 0)
        {
            // Send data to python
            printf("Waiting for python...\n");
            while (freqList->read == false)
            {
                // Optional: Sleep for a brief moment to avoid excessive CPU usage
                sleep(0.5);
            }
            int freqCount = 0;
            // Send data to python here
            particlesToFrequency(particleListProb, numParticles, &freqList, &freqCount);
            for (int j = 0; j < freqCount; j++)
            #pragma omp single
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
    free(rng_states);

    //printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}