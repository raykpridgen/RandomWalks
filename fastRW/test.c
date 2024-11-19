#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdlib.h>

typedef struct {
    float x;
    int y;
    char padding[56]; // Avoid false sharing
} Particle;

float moveProbCalc(float D, float b, float dt);
void initializeParticles(Particle partList[], int numParts);
void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, float jumpRand, float moveRand);
void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, float jumpRand, float moveRand);
void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);

int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RW.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
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

    float moveDistance = sqrt(2 * diffCon * deltaT);
    int increments = (int)floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    Particle *particleListStep = malloc(numParticles * sizeof(Particle));
    if (!particleListProb || !particleListStep) {
        fprintf(stderr, "Memory allocation failed for particle lists\n");
        return 1;
    }
    
    initializeParticles(particleListProb, numParticles);
    initializeParticles(particleListStep, numParticles);

    // Allocate random number array
    float *randomNumbers = malloc(numParticles * increments * 4 * sizeof(float));
    if (!randomNumbers) {
        fprintf(stderr, "Memory allocation failed for random numbers\n");
        free(particleListProb);
        free(particleListStep);
        return 1;
    }

    // Precompute random numbers
    printf("Precomputing random numbers...\n");
    #pragma omp parallel
    {
        unsigned short seed[3] = { (unsigned short)time(NULL) + omp_get_thread_num(),
                                   (unsigned short)rand(),
                                   (unsigned short)rand() };

        #pragma omp for
        for (int i = 0; i < numParticles * increments * 4; i++) {
            randomNumbers[i] = erand48(seed); // High-quality random float in [0,1)
        }
    }
    
    printf("Starting simulation...\n");
    double simStart = omp_get_wtime();
    
    for (int i = 0; i < increments; i++) {
        #pragma omp parallel for schedule(dynamic, 500)
        for (int j = 0; j < numParticles; j++) {
            int idx = (i * numParticles + j) * 4;
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance, randomNumbers[idx], randomNumbers[idx + 1]);
        }

        #pragma omp parallel for schedule(dynamic, 500)
        for (int j = 0; j < numParticles; j++) {
            int idx = (i * numParticles + j) * 4;
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance, randomNumbers[idx + 2], randomNumbers[idx + 3]);
        }
    }

    double simEnd = omp_get_wtime();
    printf("Simulation completed in %.2f seconds\n", simEnd - simStart);

    printf("Exporting data...\n");
    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");

    free(particleListProb);
    free(particleListStep);
    free(randomNumbers);
    printf("Total time: %.2f seconds\n", omp_get_wtime() - startTime);
    return 0;
}

// Helper functions remain unchanged


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

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, float jumpRand, float moveRand) {
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        if (particle->y == 0) {
            moveProb = 1 - moveProb;
        }
        if (moveRand < moveProb) {
            particle->x += moveDistance;
        } else {
            particle->x -= moveDistance;
        }
    }
}

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, float jumpRand, float moveRand) {
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        if (particle->y == 1) {
            if (moveRand < 0.5) {
                particle->x = particle->x + moveDistance + driftVal;
            } else {
                particle->x = particle->x - moveDistance + driftVal;
            }
        } else {
            if (moveRand < 0.5) {
                particle->x = particle->x + moveDistance - driftVal;
            } else {
                particle->x = particle->x - moveDistance - driftVal;
            }
        }
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
