#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdlib.h>

typedef struct {
    float x;
    int y;
} Particle;

float moveProbCalc(float D, float b, float dt);

void initializeParticles(Particle partList[], int numParts);

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, unsigned short seed[]);

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, unsigned short seed[]);

void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);

int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RW.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <numCores>\n");
        return 1;
    }

    // Parameters
    float deltaT = atof(argv[1]);
    float timeConst = atof(argv[2]);
    float diffCon = atof(argv[3]);
    float bSpin = atof(argv[4]);
    float gamma = atof(argv[5]);
    int numParticles = atoi(argv[6]);
    int coresToUse = atoi(argv[7]);

    if (coresToUse > omp_get_num_procs()) {
        printf("Not enough cores. Using max: %d", omp_get_num_procs());
        coresToUse = omp_get_num_procs();
    }
    omp_set_num_threads(coresToUse);

    float moveDistance = sqrt(2 * diffCon * deltaT);
    float increments = floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    Particle *particleListStep = malloc(numParticles * sizeof(Particle));

    initializeParticles(particleListProb, numParticles);
    initializeParticles(particleListStep, numParticles);
    
    unsigned short seeds[omp_get_max_threads()][3];  // Array of seeds for each thread
    unsigned int base_seed = (unsigned int)time(NULL);

    // Initialize thread-local seeds with unique values
    #pragma omp parallel
    {
        int thread_num = omp_get_thread_num();
        seeds[thread_num][0] = (unsigned short)(base_seed + thread_num);
        seeds[thread_num][1] = (unsigned short)((base_seed + thread_num) >> 16);
        seeds[thread_num][2] = (unsigned short)((base_seed + thread_num) >> 32);
    }

    for (int i = 0; i < increments; i++) {
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            int thread_num = omp_get_thread_num();
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance, seeds[thread_num]);
        }

        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            int thread_num = omp_get_thread_num();
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance, seeds[thread_num]);
        }
    }

    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");

    free(particleListProb);
    free(particleListStep);
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

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, unsigned short seed[]) {
    float randJump = (float)erand48(seed);
    if (randJump < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        if (particle->y == 0) {
            moveProb = 1 - moveProb;
        }
        float randMove = (float)erand48(seed);
        if (randMove < moveProb) {
            particle->x += moveDistance;
        } else {
            particle->x -= moveDistance;
        }
    }
}

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, unsigned short seed[]) {
    float randJump = (float)erand48(seed);
    if (randJump < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        float moveRand = (float)erand48(seed);
        if (particle->y == 1) {
            if (moveRand < 0.5) {
                particle->x += moveDistance + driftVal;
            } else {
                particle->x -= moveDistance + driftVal;
            }
        } else {
            if (moveRand < 0.5) {
                particle->x += moveDistance - driftVal;
            } else {
                particle->x -= moveDistance - driftVal;
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
