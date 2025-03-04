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
float moveProbCalc(float D, float b, float dt);
// Discrete move distance for each particle - SQRT(2D*dt)
float moveDistanceCalc(float diffusionConstant, float deltaT);
// Initialize particles within shared memory
ParticleStruct* initializeParticles();
// Move a single particle
int moveParticles(ParticleStruct *sharedData, float moveProb, float jumpProb, pcg32_random_t *rng_states, int step);
// Initialize RNG states for each thread
void initialize_rng_states(int num_threads, pcg32_random_t *rng_states);
// Round a float value to a number of decimal places
float roundValue(float number, int decimals);
#endif