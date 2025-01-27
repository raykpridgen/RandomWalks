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
typedef struct {
    float x;
    float y;
    float freqx;
} DataParticle;

typedef struct {
    DataParticle particles[325];   
    int count;                  // Number of top particles
    bool read;
} ParticleDataList;

int main()
{
    printf("\n\nSize: %ld\n\n", sizeof(DataParticle));

    printf("\n\nSize: %ld\n\n", sizeof(ParticleDataList));
}
