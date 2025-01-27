#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <float.h>
#include <limits.h>
#include "../pcg_basic.h"
#include "helper.h"

#pragma omp threadprivate(rng_states)

void initializeParticles(Particle partList[], int numParts) {
    for (int i = 0; i < floor(numParts / 2); i++) {
        partList[i].x = (float)0;
        partList[i].y = 1;
    }
    for (int i = floor(numParts / 2); i < numParts; i++) {
        partList[i].x = (float)0;
        partList[i].y = 0;
    }
}

bool moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance) {
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } else {
        int thread_id = omp_get_thread_num();
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

bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance) {
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) 
    {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } 
    else 
    {
        int thread_id = omp_get_thread_num();
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

void initialize_rng_states(int num_threads) {
    #pragma omp parallel
    {
        // Allocate rng_states for each thread
        rng_states = malloc(num_threads * sizeof(pcg32_random_t));
        if (!rng_states) {
            fprintf(stderr, "Memory allocation failed for RNG states\n");
            exit(1);
        }
        int thread_id = omp_get_thread_num();
        // Initialize each thread's rng state
        pcg32_srandom_r(&rng_states[thread_id], time(NULL) ^ thread_id, thread_id);
    }
}