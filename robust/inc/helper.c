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
#include "pcg_basic.h"

#define SHM_NAME "/particle_shm"
#define PARTICLE_COUNT 325
#ifndef HELPER_H
#define HELPER_H


typedef struct {
    int x;
    int y;
} Particle;

typedef struct {
    Particle particles[PARTICLE_COUNT];
    int count;
    bool read;
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
ParticleStruct* initializeParticles()
{
    // Try to open existing shared memory
    int shm_fd = shm_open(SHM_NAME, O_RDWR, 0666);
    bool created = false;
    // If it doesn't exist, create it
    if (shm_fd == -1) 
    {
        if (errno == ENOENT) 
        {
            printf("Shared memory not found, creating new segment...\n");
            shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
            created = true;
        }
        if (shm_fd == -1) 
        {
            perror("shm_open failed");
            close(shm_fd);
            return NULL;
        }
    }

    // Initalize if block is created within function
    if (created) 
    {
        if (ftruncate(shm_fd, sizeof(ParticleStruct)) == -1) 
        {
            perror("ftruncate failed");
            close(shm_fd);
            return NULL;
        }
    }

    // Map shared memory
    ParticleStruct *shared_data = mmap(NULL, sizeof(ParticleStruct), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) 
    {
        perror("mmap failed");
        close(shm_fd);
        return NULL;
    }
    // Set values appropriately
    if (created)
    {
        // Set all values in struct to zero
        memset(shared_data, 0, sizeof(ParticleStruct));
        // Set count
        shared_data->count = PARTICLE_COUNT;
        // Set read value to true so python doesn't read during initialization
        shared_data->read = true;
        // Set values to zero for each particle
        for (int i = 0; i < PARTICLE_COUNT; i++)
        {
            // Set x, half y on top half y on bottom
            shared_data->particles[i].x = 0;
            if (i < PARTICLE_COUNT / 2)
            {
                shared_data->particles[i].y = 1;
            }
            else
            {
                shared_data->particles[i].y = 0;
            }
        }
    }

    // Return the pointer to the shared memory
    return shared_data;
}

// Move particles in a given step
int moveParticles(ParticleStruct *sharedData, float moveProb, float jumpProb, pcg32_random_t *rng_states, int step)
{
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
            float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
            // If jump is satisfied, move particle to other line
            if (jumpRand < jumpProb)
            {
                sharedData->particles[i].y = (sharedData->particles[i].y == 0) ? 1 : 0;
                continue;
            }
            else
            {
                // Thread safe random number for x-axis
                float moveRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
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
    // Set data to unread
    sharedData->read = false;
    return 0;
}

// Initialize RNG states for each thread
void initialize_rng_states(int num_threads, pcg32_random_t *rng_states);
// Round a float value to a number of decimal places
float roundValue(float number, int decimals);
#endif