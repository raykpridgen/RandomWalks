#include <stdio.h>
#include <math.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h> 
#include <errno.h>
#include "pcg_basic.h"
#include "helper.h"

#define SHM_NAME "/particle_shm"
#ifndef HELPER_H
#define HELPER_H

// Calculate size of the shared memory block based on particles
size_t getSize(int numParts)
{
    size_t size = sizeof(int) + sizeof(int) + 4 + numParts * sizeof(Particle);
    return size;
}

// Calculate probability for a move
// RNG below output is a particle move right, greater than output is left
// 0.5 is even moves L and R
float moveProbCalc(float D, float b, float dt)
{
    if (D == 0 && b == 0) {
        return 0.5;
    } else {
        // Given
        //return 0.5 * (1 + (b / sqrt((2 * D) + (b * b)))); 
        // Possible rework
        float prob = 0.5 * (1 + b * sqrt(dt / (2 * D)));
        return fmax(0.0, fmin(1.0, prob));
    }
}

// Move distance calculation
// How far a particle moves within x axis
float moveDistanceCalc(float diffusionConstant, float deltaT)
{
    return sqrt(2 * diffusionConstant * deltaT);
}

// Initialize particles within shared memory
ParticleStruct* initializeParticles(int numParts, int* fd)
{
    // Try to open existing shared memory
    *fd = shm_open(SHM_NAME,O_RDWR, 0666);
    if (*fd == -1) 
    {
        perror("shm_open failed");
        close(*fd);
        return NULL;
    }

    // Map shared memory
    size_t size = getSize(numParts);
    void* shared_data = mmap(0, size, PROT_READ | PROT_WRITE, MAP_SHARED, *fd, 0);
    if (shared_data == MAP_FAILED) 
    {
        perror("mmap failed");
        close(*fd);
        return NULL;
    }
    ParticleStruct* result = (ParticleStruct*)shared_data;
    if (result->read != 1)
    {
        return NULL;
    }
    if (result->count != numParts) {
        printf("Count mismatch: expected %d, got %d\n", numParts, result->count); 
        fflush(stdout);
        munmap(result, size);
        close(*fd);
        return NULL;
    }

    // Set read flag
    result->read = 0;
    
    // Return the pointer to the shared memory
    return result;
}

// Move particles in a given step
int moveParticles(ParticleStruct *sharedData, float moveProb, float jumpProb, pcg32_random_t *rng_states, int step)
{
    if (sharedData == NULL) {
        printf("Error: sharedData is NULL\n"); fflush(stdout);
        return -1;
    }
    if (rng_states == NULL) {
        printf("Error: rng_states is NULL\n"); fflush(stdout);
        return -1;
    }
    if (sharedData->read != 1) {
        //printf("Read value is not 1, cannot access.\n"); fflush(stdout);
        return 0;
    }
    if (sharedData->count <= 0) {
        printf("Invalid particle count: %d\n", sharedData->count); fflush(stdout);
        return -1;
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
                uint32_t rand_val1 = pcg32_random_r(&rng_states[thread_id]);
                float moveRand = (float)(rand_val1 & 0x7FFFFFFF) / (float)0x7FFFFFFF;
                // Flip probability if on the bottom line
                float localMoveProb = (sharedData->particles[i].y == 0) ? 1 - moveProb : moveProb;
                
                if (moveRand > localMoveProb)
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
    sharedData->read = 0;
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

void cleanup_shared_memory(int fd, ParticleStruct* shared, size_t size) {
    if (shared) {
        munmap(shared, size);
    }
    if (fd != -1) {
        close(fd);
    }
}
#endif