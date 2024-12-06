#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <float.h>
#include <limits.h>
#include "pcg_basic.h"

pcg32_random_t *rng_states; // Declare as thread-private variable
#pragma omp threadprivate(rng_states)

typedef struct {
    float x;
    int y;
} Particle;

float moveProbCalc(float D, float b, float dt);
void initializeParticles(Particle partList[], int numParts);
bool moveParticleProb(Particle *particle, float jumpProb, float driftVal, float moveDistance);
bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance);
void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);
void initialize_rng_states(int num_threads);

int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RWoperation.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }
    double startTime = omp_get_wtime();
    
    // Parameters
    float deltaT = atof(argv[1]);
    float timeConst = atof(argv[2]);
    float diffCon = atof(argv[3]);
    float bSpin = atof(argv[4]);
    float gamma = atof(argv[5]);
    int numParticles = atoi(argv[6]);
    int coresToUse = atoi(argv[7]);

    if (coresToUse > omp_get_num_procs()) {
        printf("Not enough cores. Using max: %d\n", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    } else {
        printf("Using %d threads.\n", coresToUse);
    }
    omp_set_num_threads(coresToUse);
    initialize_rng_states(coresToUse);

    float moveDistance = sqrt(2 * diffCon * deltaT);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    printf("--------- Behavior ---------\n");
    printf("Increments:          %d\nNumber of Particles: %d\nMove Distance:       %.4f\nMove Probability:    %.4f\nJump Probability:    %.4f\nShift Value:         %.4f\n", increments, numParticles, moveDistance, moveProb, jumpProb, shiftValue);
    printf("----------------------------\n");

    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    Particle *particleListStep = malloc(numParticles * sizeof(Particle));
    if (!particleListProb || !particleListStep) {
        fprintf(stderr, "Memory allocation failed for particle lists\n");
        return 1;
    }
    
    initializeParticles(particleListProb, numParticles);
    initializeParticles(particleListStep, numParticles);

    printf("Starting simulation...\n");
    double simStart = omp_get_wtime();

    int numMovesProb = 0;
    int numJumpsProb = 0; 

    // Increments are set here
    for (int i = 0; i < increments; i++) {
        // One thread moves two particles
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance);
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }
    }

    double simEnd = omp_get_wtime();
    printf("Simulation completed in %.2f seconds\n", simEnd - simStart);

    // Calculate frequencies for each x
    int xValsProb[3]; 
    // For each particle, get all x values
    for (int i = 0; i < numParticles; i++) 
    {
        

    }
    printf("Exporting data...\n");
    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");

    free(particleListProb);
    free(particleListStep);
    free(rng_states);

    printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}

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
        fprintf(file, "%.2f,%d\n", particles[i].x, particles[i].y);
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