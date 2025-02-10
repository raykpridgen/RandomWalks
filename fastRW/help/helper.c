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
#include <sys/ipc.h>
#include <sys/shm.h> 
#include <errno.h>
#include "../pcg_basic.h"
#include "helper.h"

#define SHM_NAME "/particle_shm"
#define PARTICLE_COUNT 325



void initializeParticles(Particle partList[], int numParts) {
    for (int i = 0; i < floor(numParts / 2); i++) {
        partList[i].x = (float)0;
        partList[i].y = 1;
    }
    for (int i = floor(numParts / 2); i < numParts; i++) {
        partList[i].x = (float)0;
        partList[i].y = 0;
    }
    return;
}

bool moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance, pcg32_random_t *rng_states) {
    #pragma omp barrier
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } else {
        float moveRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
        if (particle->y == 0) {
            moveProb = 1 - moveProb;
        }
        if (moveRand < moveProb) {
            float movedistcalc = particle->x + moveDistance;
            particle->x = round(movedistcalc );
        } else {
            particle->x -= moveDistance;
        }
        return false;
    }
}

bool moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance, pcg32_random_t *rng_states) {
    int thread_id = omp_get_thread_num();
    float jumpRand = (float)pcg32_random_r(&rng_states[thread_id]) / UINT32_MAX;
    if (jumpRand < jumpProb) 
    {
        particle->y = (particle->y == 0) ? 1 : 0;
        return true;
    } 
    else 
    {
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
        fprintf(file, "%.3f,%f\n", particles[i].x, particles[i].y);
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

void initialize_rng_states(int num_threads, pcg32_random_t *rng_states) {

    // Initialize RNG states for each thread
    #pragma omp parallel
    {
        int thread_id = omp_get_thread_num();
        if (thread_id >= num_threads) {
            printf("Error: thread_id %d is out of bounds\n", thread_id);
            exit(1);
        }
        // Ensure that rng_states[thread_id] is a valid pointer before accessing it
        unsigned long long seed = (thread_id + 1) * 123456789ULL;
        //printf("Thread %d initializing RNG state\nSeed: %llx\n", thread_id, seed);
        #pragma omp barrier
        pcg32_srandom_r(&rng_states[thread_id], seed, thread_id);
        #pragma omp barrier
    }
}

ParticleDataList particlesToFrequency(Particle particles[], int numParticles) 
{
    printf("Starting part to freq...\n");
    
    ParticleDataList frequencies;

    frequencies.count = 0;
    // this is just for isntance, never used
    frequencies.read = 0;

    // Initialize frequency counts
    int freqCount = 0;

    // Process each particle in the input list
    for (int i = 0; i < numParticles; i++) {
        // Flag for finding a matching particle
        bool found = false;
        if (freqCount != 0)
        {
            for (int j = 0; j < freqCount; j++) 
            {
                // If a particle in the list matches the same location of another
                if (frequencies.particles[j].x == particles[i].x && frequencies.particles[j].y == particles[i].y) {
                    // increment counter in freqx
                    frequencies.particles[j].freqx += 1;
                    found = true;
                    break;
                }
            }
        }

        // If the x value wasn't found, add a new entry
        if (!found) {
            printf("Not found, particle added %d\n", freqCount);
            if (freqCount > PARTICLE_COUNT) 
            {
                printf("Warning: Maximum particle count reached!\n");
                break;
            }
            frequencies.particles[freqCount].x = particles[freqCount].x;
            frequencies.particles[freqCount].y = particles[freqCount].y;
            frequencies.particles[freqCount].freqx = 1;
            (freqCount)++;  // Increase the count of unique x values
        }
    }

    // Change particle count
    frequencies.count = freqCount;
    return frequencies;
}

int sharedMemory(ParticleDataList send)
{
    int shm_fd;
    int created = 0;

    // Try to open existing shared memory
    shm_fd = shm_open(SHM_NAME, O_RDWR, 0666);
    
    // If it doesn't exist, create it
    if (shm_fd == -1) 
    {
        if (errno == ENOENT) 
        {
            printf("Shared memory not found, creating new segment...\n");
            shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
            created = 1;
        }
        if (shm_fd == -1) 
        {
            perror("shm_open failed");
            close(shm_fd);
            return 1;
        }
    }

    // Set shared memory size if newly created
    if (created) 
    {
        if (ftruncate(shm_fd, sizeof(ParticleDataList)) == -1) 
        {
            perror("ftruncate failed");
            close(shm_fd);
            return 1;
        }
    }

    // Map shared memory
    ParticleDataList *shared_data = mmap(NULL, sizeof(ParticleDataList), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) 
    {
        perror("mmap failed");
        munmap(shared_data, sizeof(ParticleDataList));
        close(shm_fd);
        return 1;
    }
    if (created)
    {
        memset(shared_data, 0, sizeof(ParticleDataList));
        shared_data->count = send.count;
        memcpy(shared_data->particles, send.particles, sizeof(DataParticle) * send.count);
        shared_data->read = 0;
    }
    else
    {
        // Ensure C always leaves an even read flag
        if (shared_data->read % 2 == 1) 
        {
            shared_data->read += 1;  // Make even (ensuring Python acknowledges update)
        }
        else
        {
            // Python has not yet read, return 1
            munmap(shared_data, sizeof(ParticleDataList));
            close(shm_fd);
            return 1;
        }
        // Copy new data into shared memory
        shared_data->count = send.count;
        memcpy(shared_data->particles, send.particles, sizeof(DataParticle) * send.count);
    }

    // Force write to memory
    fsync(shm_fd);

    // Cleanup
    munmap(shared_data, sizeof(ParticleDataList));
    close(shm_fd);
    return 0;
}

float roundValue(float number, int decimals)
{
    float multiple = powf(10.0f, decimals); // Use float-specific powf()
    return roundf(number * multiple) / multiple;
}