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
#include "help/helper.h"

pcg32_random_t *rng_states; // Declare as thread-private variable
#pragma omp threadprivate(rng_states)


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

    float moveDistance = roundValue(sqrt(2 * diffCon * deltaT), 2);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = roundValue((deltaT * bSpin), 2);

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
