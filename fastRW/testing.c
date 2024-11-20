#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <float.h>
#include <limits.h>


typedef struct {
    float x;
    int y;
} Particle;
unsigned long long int get_time_seed();

float rng(unsigned long long int *state);

int main(int argc, char *argv[]) 
{
    omp_set_num_threads(1);
    #pragma omp parallel for
    for (int i=0; i<32; i++)
    {
        double newD = fmod(pow((42677 * get_time_seed() + omp_get_thread_num()), (omp_get_thread_num() + 3)), 1844674407351615);
        //printf("Psuedoseed: %f\n", newD);
        unsigned long long int state = (unsigned long long int)newD;
        printf("%d - Random value: %f\n", omp_get_thread_num(), rng(&state));
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
