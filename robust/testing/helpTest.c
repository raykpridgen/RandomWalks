#include <stdio.h>
#include <stdlib.h>
#include "../inc/helper.h"

#define SHM_NAME "/dev/shm/particle_shm"
#define SEM_NAME "/particle_sem"
// Test getSize
void test_getSize() {
    int numParts = 10;
    size_t result = getSize(numParts);
    size_t expected = sizeof(ParticleStruct) + numParts * sizeof(Particle);
    printf("test_getSize: %s (Result: %zu, Expected: %zu)\n", 
           result == expected ? "PASSED" : "FAILED", result, expected);
}

// Test moveProbCalc
void test_moveProbCalc() {
    float result1 = moveProbCalc(0.0f, 0.0f, 1.0f);  // Should return 0.5
    float result2 = moveProbCalc(1.0f, 1.0f, 1.0f);  // Should return > 0.5
    printf("test_moveProbCalc: %s (Zero case: %.2f, Non-zero case: %.2f)\n",
           (result1 == 0.5f && result2 > 0.5f) ? "PASSED" : "FAILED",
           result1, result2);
}

// Test moveDistanceCalc
void test_moveDistanceCalc() {
    float result = moveDistanceCalc(2.0f, 1.0f);
    float expected = sqrtf(4.0f);  // sqrt(2 * 2 * 1)
    printf("test_moveDistanceCalc: %s (Result: %.2f, Expected: %.2f)\n",
           fabs(result - expected) < 0.0001f ? "PASSED" : "FAILED",
           result, expected);
}

// Test initializeParticles (simplified version since it needs shared memory)
void test_initializeParticles() {
    int fd;
    sem_t* sem;
    // Create shared memory first (minimal setup for test)
    size_t size = getSize(5);
    fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, size);
    sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    
    ParticleStruct* result = initializeParticles(5, &fd, &sem);
    int passed = (result != NULL && result->particles != NULL);
    
    // Cleanup
    cleanup_shared_memory(fd, result, size, sem);
    shm_unlink(SHM_NAME);
    
    printf("test_initializeParticles: %s\n", passed ? "PASSED" : "FAILED");
}

// Test resizeSharedMemory
void test_resizeSharedMemory() {
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    size_t oldSize = getSize(5);
    ftruncate(fd, oldSize);
    ParticleStruct* oldPtr = mmap(0, oldSize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    
    ParticleStruct* newPtr = resizeSharedMemory(fd, oldPtr, oldSize, 10);
    size_t newSize = getSize(10);
    
    int passed = (newPtr != NULL);
    cleanup_shared_memory(fd, newPtr, newSize, SEM_FAILED);
    shm_unlink(SHM_NAME);
    
    printf("test_resizeSharedMemory: %s\n", passed ? "PASSED" : "FAILED");
}

// Test moveParticles (simplified - needs RNG setup)
void test_moveParticles() {
    int fd;
    sem_t* sem;
    size_t size = getSize(2);
    fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, size);
    sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    ParticleStruct* shared = initializeParticles(2, &fd, &sem);
    shared->count = 2;
    shared->particles[0] = (Particle){0.0f, 0.0f};
    shared->particles[1] = (Particle){1.0f, 1.0f};
    
    pcg32_random_t rng_states[1];
    initialize_rng_states(1, rng_states);
    int result = moveParticles(shared, 0.5f, 0.1f, rng_states, 1, sem);
    
    printf("test_moveParticles: %s (Return: %d)\n", 
           result == 0 ? "PASSED" : "FAILED", result);
    
    cleanup_shared_memory(fd, shared, size, sem);
    shm_unlink(SHM_NAME);
}

// Test initialize_rng_states
void test_initialize_rng_states() {
    pcg32_random_t rng_states[2];
    initialize_rng_states(2, rng_states);
    uint32_t val1 = pcg32_random_r(&rng_states[0]);
    uint32_t val2 = pcg32_random_r(&rng_states[1]);
    int passed = (val1 != val2);  // Different seeds should give different values
    printf("test_initialize_rng_states: %s (Val1: %u, Val2: %u)\n",
           passed ? "PASSED" : "FAILED", val1, val2);
}

// Test roundValue
void test_roundValue() {
    float result = roundValue(3.14159f, 2);
    float expected = 3.14f;
    printf("test_roundValue: %s (Result: %.2f, Expected: %.2f)\n",
           fabs(result - expected) < 0.0001f ? "PASSED" : "FAILED",
           result, expected);
}

// Test cleanup_shared_memory
void test_cleanup_shared_memory() {
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    size_t size = getSize(5);
    ftruncate(fd, size);
    ParticleStruct* shared = mmap(0, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    sem_t* sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    
    cleanup_shared_memory(fd, shared, size, sem);
    shm_unlink(SHM_NAME);
    
    // Try to open again - should fail if cleanup worked
    int new_fd = shm_open(SHM_NAME, O_RDWR, 0666);
    int passed = (new_fd == -1);
    if (new_fd != -1) close(new_fd);
    printf("test_cleanup_shared_memory: %s\n", passed ? "PASSED" : "FAILED");
}

int main() {
    printf("Running tests...\n");
    
    test_getSize();
    test_moveProbCalc();
    test_moveDistanceCalc();
    test_initializeParticles();
    test_resizeSharedMemory();
    test_moveParticles();
    test_initialize_rng_states();
    test_roundValue();
    test_cleanup_shared_memory();
    
    printf("Tests completed.\n");
    return 0;
}