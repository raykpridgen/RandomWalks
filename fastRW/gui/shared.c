#include <fcntl.h>  // For shm_open() flags (O_CREAT, O_RDWR)
#include <sys/mman.h>  // For mmap(), MAP_SHARED
#include <sys/stat.h>  // For mode constants (0666)
#include <stdio.h>  // For perror() and printf()
#include <stdlib.h>  // For exit()
#include <string.h>  // For memset() (if needed)
#include <unistd.h>  // For sleep()

#define SHM_NAME "/TESTINGTESTING123"  // Shared memory name
#define SHM_SIZE 1024  // Shared memory size

// Define a structure to store particle data
typedef struct {
    float x;
    float y;
    int id;
    char active;  // Boolean-like flag
    int updated;  // Flag to indicate if the data has been updated
} Particle;

int main() 
{
    int shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) 
    {
        perror("shm_open failed");
        exit(1);
    }

    ftruncate(shm_fd, SHM_SIZE);  // Set the size of the shared memory segment
    void *shm_ptr = mmap(0, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shm_ptr == MAP_FAILED) 
    {
        perror("mmap failed");
        exit(1);
    }

    // Pointer to shared memory
    Particle *p = (Particle*)shm_ptr;

    // Update the particle data and set the updated flag
    p->x = 1.5;
    p->y = -2.3;
    p->id = 42;
    p->active = 1;  // True

    // Indicate that data has been updated
    p->updated = 1;

    printf("Particle data written to shared memory.\n");

    // Sleep for a while (simulating time passing)
    sleep(1);  // Simulate delay for next update

    // Unset the updated flag after consumption (this will be done by Python)
    p->updated = 0;

    return 0;
}
