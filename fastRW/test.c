#include <time.h>
#include <stdio.h>
#include <stdlib.h>

int main()
{
    srand(time(NULL));
    for(int i=0; i<10; i++)
    {
        float intVal = rand();
        intVal = intVal / RAND_MAX;
        printf("%f, %d\n", intVal, RAND_MAX);
    }
    
}