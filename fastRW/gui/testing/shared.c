#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#define SHM_NAME "/particle_shm"
#define PARTICLE_COUNT 325

typedef struct {
    float x;
    float y;
    float freqx;
} DataParticle;

typedef struct {
    DataParticle particles[PARTICLE_COUNT];
    int count;
    volatile int read;  // Ensure `read` is not optimized away
} ParticleDataList;

int main() 
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
            return 1;
        }
    }

    // Set shared memory size if newly created
    if (created) 
    {
        if (ftruncate(shm_fd, sizeof(ParticleDataList)) == -1) 
        {
            perror("ftruncate failed");
            return 1;
        }
    }

    // Map shared memory
    ParticleDataList *shared_data = mmap(NULL, sizeof(ParticleDataList), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) 
    {
        perror("mmap failed");
        return 1;
    }

    // If newly created, fill with test data
    if (created) 
    {
        printf("Initializing shared memory with test particle data...\n");
        for (int i = 0; i < PARTICLE_COUNT; i++) 
        {
            shared_data->particles[i].x = i * 1.0f;
            shared_data->particles[i].y = i * 2.0f;
            shared_data->particles[i].freqx = i * 0.1f;
        }
        shared_data->count = PARTICLE_COUNT;
        shared_data->read = 0;
        printf("Test data initialized.\n");
    }

    // Print first few particles
    printf("First 5 particles in shared memory:\n");
    for (int i = 0; i < 5; i++) 
    {
        printf("Particle %d -> x: %.2f, y: %.2f, freqx: %.2f\n",
               i, shared_data->particles[i].x, shared_data->particles[i].y, shared_data->particles[i].freqx);
    }

    printf("Current read count (C program): %d\n", shared_data->read);

    printf("Current read count (C program): %d\n", shared_data->read);

    // Do NOT unlink the shared memory so it persists
    munmap(shared_data, sizeof(ParticleDataList));
    close(shm_fd);
    return 0;
}
