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

#define PARTICLE_COUNT 325
#ifndef HELPER_H
#define HELPER_H


typedef struct {
    float x;
    float y;
} Particle;

typedef struct {
    float x;
    float y;
    float freqx;
} DataParticle;

typedef struct {
    DataParticle particles[PARTICLE_COUNT];   
    int count;
    int read;
} ParticleDataList;


float moveProbCalc(float D, float b, float dt);
void initializeParticles(Particle partList[], int numParts);
bool moveParticleProb(Particle *particle, float jumpProb, float driftVal, float moveDistance, pcg32_random_t *rng_states);
bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, pcg32_random_t *rng_states);
void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);
void initialize_rng_states(int num_threads, pcg32_random_t *rng_states);
// Function to convert particles to frequency list
ParticleDataList particlesToFrequency(Particle particles[], int numParticles);
int sharedMemory(ParticleDataList send);
float roundValue(float number, int decimals);
#endif