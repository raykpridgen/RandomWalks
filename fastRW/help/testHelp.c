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
int testRoundFunction(float round, int decimal, float expected)
{
    float returned = roundValue(round, decimal);
    if (returned != expected)
    {
        printf("Not the same.\nReturned: %f \nExpected: %f", returned, expected);
        return 1;
    }
    return 0;
}
int testFreqCountDPL()
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
    *freqList = particlesToFrequency(particleList, numParticles);

    // Debugging: Check if freqCount is correct
    printf("Final freqCount: %d\n", freqCount);

    // Print the frequency list
    for (int i = 0; i < freqCount; i++)
    {
        printf("X: %f \nY: %f\n\n", freqList->particles[i].x, freqList->particles[i].freqx);
    }

}

int testMoveDistanceRounding(float diffCon, float deltaT)
{
    float moveDistance = sqrt(2 * diffCon * deltaT);
    printf("Move Distance Raw: %f\n", moveDistance);
    return 0;
}

int main()
{
    int success1 = testRoundFunction(4.05647583, 5, 4.05648);
    if (success1 == 0)
    {
        printf("Succeeded.\n");
    }
    else
    {
        printf("Failed.\n");
    }
    float initDt = 1;
    printf("DT: %f\n", initDt);
    int success2 = testMoveDistanceRounding(1, initDt);
    initDt = 0.1;
    printf("DT: %f\n", initDt);
    success2 = testMoveDistanceRounding(1, initDt);

    initDt = 0.01;
    printf("DT: %f\n", initDt);
    success2 = testMoveDistanceRounding(1, initDt);

    initDt = 0.001;
    printf("DT: %f\n", initDt);
    success2 = testMoveDistanceRounding(1, initDt);


    
    return 0;
}

