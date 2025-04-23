#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

#define SEM_NAME "/example_sem"

int main() {
    // Create or open the semaphore
    sem_t *sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    if (sem == SEM_FAILED) {
        perror("sem_open failed");
        exit(EXIT_FAILURE);
    }

    // Print initial semaphore value (this part is just for demonstration)
    printf("Initial semaphore value: 1 (since we initialized it with 1)\n");

    // Modify the semaphore by acquiring it (decrease the semaphore value)
    printf("Attempting to acquire the semaphore...\n");
    if (sem_wait(sem) == -1) {
        perror("sem_wait failed");
        sem_close(sem);
        sem_unlink(SEM_NAME);
        exit(EXIT_FAILURE);
    }
    printf("Semaphore acquired. Its value is now 0.\n");

    // Show the semaphore value after acquiring it (in this case, it's not directly possible to print it)
    // We'll demonstrate the effect by releasing it and printing again
    sleep(2);  // Sleep for 2 seconds to simulate some work being done

    // Release the semaphore (increase its value)
    printf("Releasing the semaphore...\n");
    if (sem_post(sem) == -1) {
        perror("sem_post failed");
        sem_close(sem);
        sem_unlink(SEM_NAME);
        exit(EXIT_FAILURE);
    }
    printf("Semaphore released. Its value is now 1 again.\n");

    // Clean up
    sem_close(sem); // Close the semaphore
    sem_unlink(SEM_NAME); // Unlink the semaphore (remove it from the system)

    return 0;
}
