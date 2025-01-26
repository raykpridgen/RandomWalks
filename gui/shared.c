#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <stdbool.h>

#define SHM_KEY 12345 // Shared memory key
#define SIZE 1024 // Size of the shared memory block

typedef struct {
    float data1;  // Example float data
    bool data2;   // Example boolean data
} SharedData;

int main() {
    // Get the shared memory ID
    int shmid = shmget(SHM_KEY, SIZE, 0666 | IPC_CREAT);
    if (shmid == -1) {
        perror("shmget failed");
        exit(1);
    }

    // Attach the shared memory
    SharedData* shm_ptr = (SharedData*) shmat(shmid, NULL, 0);
    if (shm_ptr == (SharedData*) -1) {
        perror("shmat failed");
        exit(1);
    }

    // Set values in shared memory
    shm_ptr->data1 = 42.0f;  // Example float
    shm_ptr->data2 = true;   // Example boolean

    printf("Data written to shared memory: %.2f, %d\n", shm_ptr->data1, shm_ptr->data2);

    // Detach and leave shared memory
    shmdt(shm_ptr);
    
    return 0;
}
