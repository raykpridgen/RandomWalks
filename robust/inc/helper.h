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
#include <errno.h>
#include <semaphore.h>
#include "pcg_basic.h"

#define SHM_NAME "/particle_shm"
#define SEM_NAME "/particle_sem"


typedef struct {
    float x;
    float y;
} Particle;

typedef struct {
    int count;
    Particle* particles;
} ParticleStruct;

// Calculate probability for a move
float moveProbCalc(float D, float b, float dt);

// Move distance calculation
float moveDistanceCalc(float diffusionConstant, float deltaT);

// Initialize particles within shared memory
ParticleStruct* initializeParticles(int numParts, int* fd, sem_t** sem);

// Resize structure based on old and new sizes
ParticleStruct* resizeSharedMemory(int fd, ParticleStruct* oldPointer, size_t oldSize, int newNumber);

// Calculate size of the shared memory block based on particles
size_t getSize(int numParts);

// Move particles in a given step
int moveParticles(ParticleStruct *sharedData, float moveProb, float jumpProb, pcg32_random_t *rng_states, int step, sem_t* sem);

// Initialize states for each thread for unique RNG generation
void initialize_rng_states(int num_threads, pcg32_random_t *rng_states);

// Round a float value to a number of decimal places
float roundValue(float number, int decimals);