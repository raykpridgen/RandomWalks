import mmap
import time
from multiprocessing import shared_memory
import struct

# Define the shared memory name and size
SHM_NAME = "/RandomWalksData"
SHM_SIZE = 4096  # Size of the shared memory segment

# Define a structure to match the DataParticle structure in C
class DataParticle:
    def __init__(self, x, y, freqx):
        self.x = x
        self.y = y
        self.freqx = freqx

# Define a structure to match the ParticleDataList structure in C
class ParticleDataList:
    def __init__(self):
        self.particles = []  # List to store DataParticle objects
        self.count = 0
        self.read = 0

# Attach to the shared memory object
shm = shared_memory.SharedMemory(name=SHM_NAME)
# Create a view of the shared memory (cast to the appropriate format)
buffer = memoryview(shm.buf)

# Read the particle data and update flag
while True:
    # Read the "read" flag to check if data has been written by C
    read = struct.unpack('b', buffer[4804:4805])[0]  # assuming the 'read' flag is at offset 4804-4805

    if read == 1:
        # If the flag is set, read the particle data
        particle_data_list = ParticleDataList()
        
        # Read the count (number of active particles)
        particle_data_list.count = struct.unpack('i', buffer[4800:4804])[0]  # Assuming count is just before 'read' field

        # Read the particles (assuming particles start at offset 0)
        for i in range(particle_data_list.count):
            start_idx = i * 12  # 12 bytes per DataParticle (3 floats)
            x = struct.unpack('f', buffer[start_idx:start_idx+4])[0]
            y = struct.unpack('f', buffer[start_idx+4:start_idx+8])[0]
            freqx = struct.unpack('f', buffer[start_idx+8:start_idx+12])[0]

            particle = DataParticle(x, y, freqx)
            particle_data_list.particles.append(particle)

        # Print the particle data
        for particle in particle_data_list.particles:
            print(f"Particle data: x={particle.x}, y={particle.y}, freqx={particle.freqx}")

        # Reset the "read" flag to let C program know data was read
        struct.pack_into('b', buffer, 4804, 0)  # Reset the read flag to 0

    # Sleep for a short time before checking again
    time.sleep(0.1)
