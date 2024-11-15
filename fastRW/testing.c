#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdlib.h>

typedef struct {
    float x;
    int y;
    char padding[56];
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

    int clockTime = clock();
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
    }
    else
    {
        printf("Using %d threads.\n", coresToUse);
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
    clockTime = clock() - clockTime;
    printf("Init and malloc: %d\n", clockTime);

    clockTime = clock();

    int threads = omp_get_max_threads();
    unsigned short (*seeds)[3] = malloc(threads * sizeof(unsigned short[3]));  // Array of seeds for each thread
    if (seeds == NULL) 
    {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    unsigned int base_seed = (unsigned int)time(NULL);

    // Initialize thread-local seeds with unique values
    #pragma omp parallel
    {
        int thread_num = omp_get_thread_num();
        seeds[thread_num][0] = (unsigned short)(base_seed + thread_num);
        seeds[thread_num][1] = (unsigned short)((base_seed + thread_num) >> 16);
        seeds[thread_num][2] = (unsigned short)((base_seed + thread_num) >> 32);
    }

    clockTime = clock() - clockTime;
    printf("Thread setup: %d\n", clockTime);

    clockTime = clock();
    // Allocate the 2D array with 4 * increments columns for each particle
    float **randomNumbers = malloc(numParticles * sizeof(float *));
    for (int i = 0; i < numParticles; i++) {
        randomNumbers[i] = malloc(4 * increments * sizeof(float));
    }
    clockTime = clock() - clockTime;
    printf("Malloc randoms: %d\n", clockTime);
    clockTime = clock();

    int i, j;
    // Precompute random numbers in parallel
    
    
    for (int i = 0; i < increments; i++) {
        #pragma omp parallel for private(i, j)
        for (int j = 0; j < numParticles; j++) {
            unsigned int thread_num = omp_get_thread_num();
            
            // Use thread-local seed
            unsigned int local_seed = seeds[thread_num][0];
            
            // Update the seed for the next call
            seeds[thread_num][0] = (unsigned short)(local_seed + 1);

            // Generate random numbers for each particle using rand_r
            randomNumbers[j][4 * i + 0] = (float)rand_r(&local_seed) / RAND_MAX;
            randomNumbers[j][4 * i + 1] = (float)rand_r(&local_seed) / RAND_MAX;
            randomNumbers[j][4 * i + 2] = (float)rand_r(&local_seed) / RAND_MAX;
            randomNumbers[j][4 * i + 3] = (float)rand_r(&local_seed) / RAND_MAX;
            
            // Update the seed for the next random number generation
            seeds[thread_num][0] = (unsigned short)(local_seed);
        }
    }


    clockTime = clock() - clockTime;
    printf("Precompute randoms: %d\n", clockTime);
    clockTime = clock();

    // Particle movement: parallelize per iteration
    for (int i = 0; i < increments; i++) {
        #pragma omp parallel for schedule(dynamic, 500)
        for (int j = 0; j < numParticles; j++) {
            float jumpRand = randomNumbers[j][4 * i + 0];  
            float moveRand = randomNumbers[j][4 * i + 1];  
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance, jumpRand, moveRand);
        }

        #pragma omp parallel for schedule(dynamic, 500)
        for (int j = 0; j < numParticles; j++) {
            float jumpRand = randomNumbers[j][4 * i + 2];  
            float moveRand = randomNumbers[j][4 * i + 3]; 
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance, jumpRand, moveRand);
        }
    }
    clockTime = clock() - clockTime;
    printf("Move time: %d\n", clockTime);
    clockTime = clock();

    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");
    clockTime = clock() - clockTime;
    printf("Export: %d\n", clockTime);
    free(particleListProb);
    free(particleListStep);
    free(seeds);
    for (int i = 0; i < numParticles; i++) {
        free(randomNumbers[i]);
    }
    free(randomNumbers);
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

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, float jumpRand, float moveRand) {
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        if (particle->y == 0) {
            moveProb = 1 - moveProb;
        }
        if (moveRand < moveProb) {
            particle->x = particle->x + moveDistance;
        } else {
            particle->x = particle->x - moveDistance;
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

    FILE *file = fopen(filename, "w"); // Open file for writing
    if (file == NULL) {
        perror("Error opening file");
        return;
    }

    // Write the header
    fprintf(file, "x,y\n");

    // Write the data for each particle
    for (int i = 0; i < numParticles; i++) {
        fprintf(file, "%.2f,%d\n", particles[i].x, particles[i].y);
    }

    fclose(file); // Close the file
}

float moveProbCalc(float D, float b, float dt) {
    if (D == 0 && b == 0) {
        return 0.5;
    } else {
        return 0.5 * (1 + (b / sqrt(((2 * D) / dt) + (b * b))));
    }
}
