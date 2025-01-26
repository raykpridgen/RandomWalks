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
#include "../pcg_basic.h"
#include "helper.h"
int main()
{
    ParticleDataList *freqList = NULL;
    int freqCount = 0;
    Particle particleList[4] = {
        {2.0, 0},
        {3.0, 0},
        {1.5, 0},
        {1.5, 0}
    };

    int numParticles = 4;
    particlesToFrequency(particleList, numParticles, &freqList, &freqCount);

    // Debugging: Check if freqCount is correct
    printf("Final freqCount: %d\n", freqCount);

    // Print the frequency list
    for (int i = 0; i < freqCount; i++)
    {
        printf("X: %f \nY: %f\n\n", freqList->particles[i].x, freqList->particles[i].freqx);
    }
}

