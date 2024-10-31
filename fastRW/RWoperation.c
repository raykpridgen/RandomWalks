#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <omp.h>

typedef struct
{
    float x;
    int y;
} Particle;

float moveProbCalc(float D, float b, float dt);

void initializeParticles(Particle partList[], int numParts);

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance);

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance);

void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename);

int main(int argc, char *argv[]) {
    if (argc != 8) {
        printf("Usage: ./RW.exe <deltaT> <timeConst> <diffCon> <bSpin> <gamma> <numParticles> <creationType>\n");
        return 1;
    }

    srand(time(NULL));

    // Parameters
    float deltaT = atof(argv[1]);
    float timeConst = atof(argv[2]);
    float diffCon = atof(argv[3]);
    float bSpin = atof(argv[4]);
    float gamma = atof(argv[5]);
    int numParticles = atoi(argv[6]);
    int creationType = atoi(argv[7]);

    // Behaviors
    float moveDistance = sqrt(2 * diffCon * deltaT);
    float increments = floor(timeConst / deltaT);
    float moveProb = moveProbCalc(diffCon, bSpin, deltaT);
    float jumpProb = gamma * deltaT;
    float shiftValue = deltaT * bSpin;

    Particle *particleListProb = malloc(numParticles * sizeof(Particle));
    Particle *particleListStep = malloc(numParticles * sizeof(Particle));

    initializeParticles(particleListProb, numParticles);
    initializeParticles(particleListStep, numParticles);
    
    // Increments
    for(int i=0; i<increments; i++)
    {
        // Particles
        #pragma omp parallel for 
        for(int j=0; j<numParticles; j++)
        {
            moveParticleProb(&particleListProb[j], jumpProb, moveProb, moveDistance);
        }
        #pragma omp parallel for
        for(int j=0; j<numParticles; j++)
        {
            moveParticleStep(&particleListStep[j], jumpProb, shiftValue, moveDistance);
        }
    }

    exportParticlesToCSV(particleListProb, numParticles, "sims/probSim.csv");
    exportParticlesToCSV(particleListStep, numParticles, "sims/stepSim.csv");
    
    free(particleListProb);
    free(particleListStep);
}

void initializeParticles(Particle partList[], int numParts)
{
    for(int i=0; i<floor(numParts/2); i++)
    {
        partList[i].x = (float)0;
        partList[i].y = 1;
    }
    for(int i=floor(numParts/2); i<numParts; i++)
    {
        partList[i].x = (float)0;
        partList[i].y = 0;
    }
}

void moveParticleProb(Particle *particle, float jumpProb, float moveProb, float moveDistance)
{
    float randJump = rand();
    randJump = randJump / RAND_MAX;
    // If jump succeeds
    if (randJump < jumpProb)
    {
        // If particle is on the top line
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    }
    // Jump fails, do move
    else
    {
        // Compliment probability if particle is on the bottom line
        if(particle->y == 0)
        {
            moveProb = 1 - moveProb;
        }

        float randMove = rand();
        randMove = randMove / RAND_MAX;
        // Move succeeds - move right
        if(randMove < moveProb)
        {
            particle->x = particle->x + moveDistance;

        }
        // Move fails - move left
        else
        {
            particle->x = particle->x - moveDistance;
        }
    }
}

void moveParticleStep(Particle *particle, float jumpProb, float driftVal, float moveDistance)
{
    //printf("moved particle %f, %f\n", particle->x, particle->y);
    float randJump = rand();
    randJump = randJump / RAND_MAX;
    // If jump succeeds
    if (randJump < jumpProb)
    {
        // Swap particle position
        particle->y = (particle->y == 0) ? 1 : 0;
        return;
    }
    // Jump fails, do move
    else
    {
        float moveRand = rand();
        moveRand = moveRand / RAND_MAX;
        if(particle->y == 1)
        {
            if(moveRand < 0.5)
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
            if(moveRand < 0.5)
            {
                particle->x = particle->x + moveDistance - driftVal;
            }
            else
            {
                particle->x = particle->x - moveDistance - driftVal;
            }
        }
        
    }
    //printf("to             %f, %f\n", particle->x, particle->y);
}

void exportParticlesToCSV(Particle particles[], int numParticles, const char *filename) {

    FILE *file = fopen(filename, "w"); // Open file for writing
    if (file == NULL) {
        perror("Error opening file");
        return;
    }

    // Write the header
    fprintf(file, "x,y\n");

    // Write the data for each particle
    for (int i = 0; i < numParticles; i++) {
        fprintf(file, "%.2f,%d\n", particles[i].x, particles[i].y);
    }

    fclose(file); // Close the file
}

float moveProbCalc(float D, float b, float dt)
{
    if(D == 0 && b == 0)
    {
        return 0.5;
    }
    else
    {
        return 0.5 * (1 + (b / sqrt(((2 * D) / dt) + (b * b))));
    }
}
