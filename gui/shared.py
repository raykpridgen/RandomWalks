import numpy as np
from multiprocessing import shared_memory
import time

SHM_KEY = 12345  # Same as the C key
SIZE = 1024  # Same size as C

# Access the existing shared memory
shm = shared_memory.SharedMemory(name=str(SHM_KEY))

# Create a numpy array backed by the shared memory
shared_array = np.ndarray((2,), dtype=np.float32, buffer=shm.buf)

# Read initial values from shared memory
print(f"Initial data from shared memory: {shared_array[0]}, {shared_array[1]}")

# Update shared memory values
shared_array[0] = 99.0  # Update the first data (float)
shared_array[1] = 1.0   # Update the second data (bool)

# Read updated values
print(f"Updated data from shared memory: {shared_array[0]}, {shared_array[1]}")

# Allow C to read the updates (simulate real-time updates)
time.sleep(2)

# Cleanup shared memory
shm.close()
