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
#include "../pcg_basic.h"
#include "helper.h"



void initializeParticles(Particle partList[], int numParts) {
    for (int i = 0; i < floor(numParts / 2); i++) {
        partList[i].x = (float)0;
        partList[i].y = 1;
    }
    for (int i = floor(numParts / 2); i < numParts; i++) {
        partList[i].x = (float)0;
        partList[i].y = 0;
    }
    return;
}

bool moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, pcg32_random_t *rng_states) {
    #pragma omp barrier
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } else {
        float moveRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
        if (particle->y == 0) {
            moveProb = 1 - moveProb;
        }
        if (moveRand < moveProb) {
            particle->x += moveDistance;
        } else {
            particle->x -= moveDistance;
        }
        return false;
    }
}

bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, pcg32_random_t *rng_states) {
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) 
    {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } 
    else 
    {
        float moveRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
        if (particle->y == 1) 
        {
            if (moveRand < 0.5) 
            {
                particle->x = particle->x + moveDistance + driftVal;
            } 
            else 
            {
                particle->x = particle->x - moveDistance + driftVal;
            }
        } 
        else 
        {
            if (moveRand < 0.5) 
            {
                particle->x = particle->x + moveDistance - driftVal;
            } 
            else 
            {
                particle->x = particle->x - moveDistance - driftVal;
            }
        }
        return false;
    }
}

void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename) {
    FILE *file = fopen(filename, "w");
    if (file == NULL) {
        perror("Error opening file");
        return;
    }

    fprintf(file, "x,y\n");
    for (int i = 0; i < numParticles; i++) {
        fprintf(file, "%.3f,%d\n", particles[i].x, particles[i].y);
    }
    fclose(file);
}

float moveProbCalc(float D, float b, float dt) {
    if (D == 0 && b == 0) {
        return 0.5;
    } else {
        return 0.5 * (1 + (b / sqrt(((2 * D) / dt) + (b * b)))); 
    }
}


void initialize_rng_states(int num_threads, pcg32_random_t *rng_states) {

    // Initialize RNG states for each thread
    #pragma omp parallel
    {
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


void particlesToFrequency(Particle particles[], int numParticles, ParticleDataList **freqList, int *freqCount) 
{
    // Temporary list to hold the frequencies of unique x values
    DataParticle *tempList = malloc(numParticles * sizeof(DataParticle));

    if (tempList == NULL) {
        perror("Memory allocation failed");
        exit(1);
    }

    // Initialize frequency counts
    *freqCount = 0;

    // Process each particle in the input list
    for (int i = 0; i < numParticles; i++) {
        bool found = false;

        // If the particle is in the top (y == 1), process for the top list
        for (int j = 0; j < *freqCount; j++) {
            if (tempList[j].x == particles[i].x && tempList[j].y == particles[i].y) {
                tempList[j].freqx += 1;  // Increment the frequency for top
                found = true;
                break;
            }
        }

        // If the x value wasn't found, add a new entry for top
        if (!found) {
            tempList[*freqCount].x = particles[i].x;
            tempList[*freqCount].y = particles[i].y;

            tempList[*freqCount].freqx = 1;  // Initialize frequency to 1 for top
            (*freqCount)++;  // Increase the count of unique x values for top
        }
    }

    // Set bottom particles for full function
    for (int i = 0; i < numParticles; i++)
    {
        if (tempList[i].y == 0)
        {
            tempList[i].freqx = -1 * tempList[i].freqx;
        }
    }

    // Allocate memory for the ParticleDataList if it is not allocated yet
    if (*freqList == NULL) {
        printf("FreqList just allocd in particlesToFrequency\n");
        *freqList = malloc(sizeof(ParticleDataList));
        if (*freqList == NULL) {
            perror("Memory allocation failed for ParticleDataList");
            free(tempList);
            exit(1);
        }
    }

    // Reallocate the particles array in freqList to hold the correct amount of DataParticles
    (*freqList)->count = *freqCount;
    memcpy((*freqList)->particles, tempList, *freqCount * sizeof(DataParticle));

    // Optionally, set read flag to true
    (*freqList)->read = true;

    // Clean up
    free(tempList);
}
