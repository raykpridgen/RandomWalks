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
#include "inc/pcg_basic.h"
#include "inc/helper.h"

#define SHM_NAME "/particle_shm"

int main(int argc, char *argv[]) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    double time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
    printf("C started at: %.3f\n", time_ms);
    
    if (argc != 8) {
        printf("Usage: ./RWoperation.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }
    
    // Parameters
    float deltaT = atof(argv[1]); // Delta t
    float timeConst = atof(argv[2]); // Time Constant
    float diffCon = atof(argv[3]); // Diffusion Constant
    float bSpin = atof(argv[4]); // beta / bias
    float gamma = atof(argv[5]); // Gamma
    int numParticles = atoi(argv[6]); // Number of particles
    int coresToUse = atoi(argv[7]); // Cores to use in multithreading
    int step = 10; // How many iterations to run before sending data

    // Behavior calculations
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;

    printf("Behavior:\nIncrements: %d\nMove Probability: %f\nJump Probability: %f\n", increments, moveProb, jumpProb);

    // Open semaphore
    sem_t* sem = sem_open("/particle_sem", O_RDWR);
    if (sem == SEM_FAILED)
    {
        perror("sem_open failed. Returning.\n");
        exit(0);
    }
    printf("Opened semaphore from Python\n");
    
    // Error detection for incorrect cores
    if (coresToUse > omp_get_num_procs()) 
    {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } 
    
    // Set cores
    omp_set_num_threads(coresToUse);
    int threadnum;
    #pragma omp parallel
    {
        threadnum = omp_get_num_threads();
    }
    printf("Threads: %d\n", threadnum);
    
    // Allocate specific storage for each core's RNG state
    pcg32_random_t *rng_states = malloc(coresToUse * sizeof(pcg32_random_t));
    if (rng_states == NULL) 
    {
        perror("Failed to allocate memory, returning");
        
        free(rng_states);
        exit(0);
    }

    // Set unique states for each thread, used for randomness
    initialize_rng_states(coresToUse, rng_states);

    printf("All initialization successful. Running.\n");

    // Calculate step break to send data back to python
    int totalSteps = increments / step;
    int remainder = increments % step;
    
    /**
     * SEMAPHORE CRITICAL SECTION
     */
    clock_gettime(CLOCK_REALTIME, &ts);
    time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
    printf("C waiting for init: %.3f\n", time_ms);
    sem_wait(sem);
    clock_gettime(CLOCK_REALTIME, &ts);
    time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
    printf("C acquired for init: %.3f\n", time_ms);
    // Open shared memory
    int fd;
    ParticleStruct* particleList = initializeParticles(numParticles, &fd);
    if (particleList == NULL)
    {
        perror("Failed to init particles. Returning.\n");
        close(fd);
        sem_post(sem);
        
        free(rng_states);
        exit(0);
    }
    if (particleList->count != numParticles)
    {
        printf("Size mismatch, expected %d, got %d. Returning. \n", numParticles, particleList->count);
        munmap(particleList, getSize(numParticles));
        close(fd);
        sem_post(sem);
        
        free(rng_states);
        exit(0);
    }

    sem_post(sem);
    clock_gettime(CLOCK_REALTIME, &ts);
    time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
    printf("C posted from init: %.3f\n", time_ms);
    // For each increment defined
    for (int g = 0; g < totalSteps; g++)
    {
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C waiting for computation: %.3f\n", time_ms);
        sem_wait(sem);
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C acquired for computation: %.3f\n", time_ms);
        // Perform this step's iterations
        if (moveParticles(particleList, moveProb, jumpProb, rng_states, step) != 0)
        {
            printf("Move particles failed. Returning.\n");
            munmap(particleList, getSize(numParticles));
            close(fd);
            sem_post(sem);
            
            free(rng_states);
            exit(0);
        }
        printf("Batch %d: particle[0] x=%f, y=%f\n", g, particleList->particles[0].x, particleList->particles[0].y);
        sem_post(sem);
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C posted for computation: %.3f\n", time_ms);
        // Microseconds
        usleep(1000000);
    }

    // If step does not divide evenly, finish off iterations
    if (remainder > 0)
    {
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C waiting for computation: %.3f\n", time_ms);
        sem_wait(sem);
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C acquired for computation: %.3f\n", time_ms);
        if (moveParticles(particleList, moveProb, jumpProb, rng_states, remainder) != 0)
        {
            printf("Move particles failed. Returning.\n");
            munmap(particleList, getSize(numParticles));
            close(fd);
            sem_post(sem);
            free(rng_states);
            exit(0);
        }
        sem_post(sem);
        clock_gettime(CLOCK_REALTIME, &ts);
        time_ms = ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
        printf("C waiting for computation: %.3f\n", time_ms);
        usleep(10000);
    }
    
    /**
     * SEMAPHORE CRITIAL SECTION
     */
    // Dont close semaphore in case this is ran again. Python can clsoe.
    munmap(particleList, getSize(numParticles));
    close(fd);
    free(rng_states);
    //printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}