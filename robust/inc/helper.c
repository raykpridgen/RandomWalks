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
#include <errno.h>
#include <semaphore.h>
#include "pcg_basic.h"

#define SHM_NAME "/particle_shm"
#define SEM_NAME "/particle_sem"
#ifndef HELPER_H
#define HELPER_H

typedef struct {
    float x;
    float y;
} Particle;

typedef struct {
    int count;
    Particle* particles;
} ParticleStruct;

// Calculate probability for a move
float moveProbCalc(float D, float b, float dt)
{
    if (D == 0 && b == 0) {
        return 0.5;
    } else {
        return 0.5 * (1 + (b / sqrt(((2 * D) / dt) + (b * b)))); 
    }
}

// Move distance calculation
float moveDistanceCalc(float diffusionConstant, float deltaT)
{
    return sqrt(2 * diffusionConstant * deltaT);
}

// Initialize particles within shared memory
ParticleStruct* initializeParticles(int numParts, int* fd, sem_t** sem)
{
    size_t size = getSize(numParts);
    // Try to open existing shared memory
    *fd = shm_open(SHM_NAME, O_RDWR, 0666);
    bool created = false;
    // If it doesn't exist, create it
    if (*fd == -1) 
    {
        if (errno == ENOENT) 
        {
            printf("Shared memory not found, creating new segment...\n");
            *fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
            created = true;
        }
        if (*fd == -1) 
        {
            perror("shm_open failed");
            close(*fd);
            return NULL;
        }
    }

    // Check that sizes match
    struct stat shm_stat;
    if (fstat(*fd, &shm_stat) == -1) 
    {
        perror("fstat failed");
        close(*fd);
        return NULL;
    }

    if (created || shm_stat.st_size != size) 
    {
        printf("Existing shared memory size mismatch, resizing...\n");
        if (ftruncate(*fd, size) == -1) 
        {
            perror("ftruncate failed");
            close(*fd);
            return NULL;
        }
    }

    // Map shared memory
    void* shared_data = mmap(0, size, PROT_READ | PROT_WRITE, MAP_SHARED, *fd, 0);
    if (shared_data == MAP_FAILED) 
    {
        perror("mmap failed");
        close(*fd);
        return NULL;
    }

    // Open / Create semaphore
    *sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    if (*sem == SEM_FAILED)
    {
        perror("sem_open failed.\n");
        munmap(shared_data, size);
        close(*fd);
        return NULL;
    }

    // Return the pointer to the shared memory
    return (ParticleStruct*)shared_data;
}

// Resize structure based on old and new sizes
ParticleStruct* resizeSharedMemory(int fd, ParticleStruct* oldPointer, size_t oldSize, int newNumber)
{
    // Set size
    size_t newSize = sizeof(ParticleStruct) + newNumber * sizeof(Particle);

    // Unmap old memory
    if (munmap(oldPointer, oldSize) == -1)
    {
        perror("munmap failed.");
        return NULL;
    }

    // Resize the shared memory
    if (ftruncate(fd, newSize) == -1) {
        perror("ftruncate failed");
        exit(1);
    }

    // Remap the shared memory
    void* new_ptr = mmap(0, newSize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (new_ptr == MAP_FAILED) {
        perror("mmap failed");
        exit(1);
    }

    return (ParticleStruct*)new_ptr;

}

// Calculate size of the shared memory block based on particles
size_t getSize(int numParts)
{
    size_t size = sizeof(ParticleStruct) + numParts * sizeof(Particle);
    return size;
}

// Move particles in a given step
int moveParticles(ParticleStruct *sharedData, float moveProb, float jumpProb, pcg32_random_t *rng_states, int step, sem_t* sem)
{
    // Check semaphore logic to proceed correctly
    if (sem_wait(sem) == -1)
    {
        perror("sem_wait failed.");
        return 1;
    }

    // For iterations in step
    for (int k = 0; k < step; k++)
    {
        // For each particle, parallelized portion
        #pragma omp parallel for
        for (int i = 0; i < sharedData->count; i++)
        {
            // Get current thread
            int thread_id = omp_get_thread_num();
            // Calculate jump varaible
            uint32_t rand_val = pcg32_random_r(&rng_states[thread_id]);
            float jumpRand = (float)(rand_val & 0x7FFFFFFF) / (float)0x7FFFFFFF;
            // If jump is satisfied, move particle to other line
            if (jumpRand < jumpProb)
            {
                sharedData->particles[i].y = (sharedData->particles[i].y == 0) ? 1 : 0;
                continue;
            }
            else
            {
                // Thread safe random number for x-axis
                float moveRand = (float)(rand_val >> 16) / (float)0xFFFF;
                // Flip probability if on the bottom line
                float localMoveProb = (sharedData->particles[i].y == 0) ? 1 - moveProb : moveProb;
                if (moveRand < localMoveProb)
                {
                    // Move one discrete increment positive
                    sharedData->particles[i].x += 1;
                }
                else
                {
                    // Negative x
                    sharedData->particles[i].x -= 1;
                }
            }
        }
    }

    // Signal python to read data
    if (sem_post(sem) == -1)
    {
        perror("sem_post failed.");
        return 1;
    }
    
    return 0;
}

// Initialize states for each thread for unique RNG generation
void initialize_rng_states(int num_threads, pcg32_random_t *rng_states) {
    // Open OMP block
    #pragma omp parallel
    {
        // Get thread number
        int thread_id = omp_get_thread_num();
        if (thread_id >= num_threads) {
            printf("Error: thread_id %d is out of bounds\n", thread_id);
            exit(1);
        }
        // Ensure that rng_states[thread_id] is a valid pointer before accessing it
        unsigned long long seed = (thread_id + 1) * 123456789ULL;
        //printf("Thread %d initializing RNG state\nSeed: %llx\n", thread_id, seed);
        #pragma omp barrier
        pcg32_srandom_r(&rng_states[thread_id], seed, thread_id);
        #pragma omp barrier
    }
}

// Round a float value to a number of decimal places
float roundValue(float number, int decimals)
{
    float multiple = powf(10.0f, decimals); // Use float-specific powf()
    return roundf(number * multiple) / multiple;
}
#endif