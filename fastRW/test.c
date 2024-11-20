#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <float.h>
#include <limits.h>

typedef struct {
    float x;
    int y;
} Particle;

float moveProbCalc(float D, float b, float dt);
void initializeParticles(Particle partList[], int numParts);
void moveParticleProb(Particle *particle, float jumpProb, float driftVal, float moveDistance);
void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance);
void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);
float rng(unsigned long long int *state);
unsigned long long int get_time_seed();
unsigned long long int int_pow(unsigned long long int base, unsigned int exp);



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

    printf("Starting simulation...\n");
    double simStart = omp_get_wtime();
    
    // Increments are set here
    for (int i = 0; i < increments; i++) {
        // First version of movement
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance);
        }

        // Second version
        #pragma omp parallel for
        for (int j = 0; j < numParticles; j++) {
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }
    }

    double simEnd = omp_get_wtime();
    printf("Simulation completed in %.2f seconds\n", simEnd - simStart);

    printf("Exporting data...\n");
    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");

    free(particleListProb);
    free(particleListStep);

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

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance) {
    unsigned long long int seed = int_pow((42677 * get_time_seed()), (omp_get_thread_num() + 3)) % 1844674407351615;
    float jumpRand = rng(&seed);
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        unsigned long long int seed = int_pow((42677 * get_time_seed()), (omp_get_thread_num() + 3)) % 1844674407351615;        
        float moveRand = rng(&seed);
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

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance) {
    unsigned long long int seed = int_pow((42677 * get_time_seed()), (omp_get_thread_num() + 3)) % 1844674407351615;    
    float jumpRand = rng(&seed);
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    } else {
        unsigned long long int seed = int_pow((42677 * get_time_seed()), (omp_get_thread_num() + 3)) % 1844674407351615;        
        float moveRand = rng(&seed);
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

unsigned long long int get_time_seed()
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ts.tv_nsec;  // Use the nanoseconds part as the seed
}

float rng(unsigned long long int *state)
{
    *state = *state ^ *state << 23; 
    *state = *state ^ *state >> 31; 
    *state = *state ^ *state << 9; 
    //printf("Final state: %llx\nFltMax: %f\n", *state, (float)ULLONG_MAX);
    return (float)(*state) / (float)(ULLONG_MAX);
}

unsigned long long int int_pow(unsigned long long int base, unsigned int exp) {
    unsigned long long int result = 1;
    while (exp) {
        if (exp % 2 == 1) {
            result *= base;
        }
        base *= base;
        exp /= 2;
    }
    return result;
}