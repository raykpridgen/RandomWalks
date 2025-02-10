#ifndef HELPER_H
#define HELPER_H
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

extern pcg32_random_t *rng_states; // Declare as thread-private variable
#pragma omp threadprivate(rng_states)

typedef struct {
    float x;
    int y;
} Particle;

void initializeParticles(Particle partList[], int numParts);

bool moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance);

bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance);

void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);

float moveProbCalc(float D, float b, float dt);

void initialize_rng_states(int num_threads);

float roundValue(float number, int decimals);
#endif // HELPER_H