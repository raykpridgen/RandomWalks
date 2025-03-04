import struct
import mmap
import os
import subprocess
SHM_NAME = "/particle_shm"
PARTICLE_COUNT = 325
STRUCT_FORMAT = f"{PARTICLE_COUNT * 3}f ii"
STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

dt = 0.1
T = 1000
D = 1
b = 0.05
g = 0
particles = 1000
cores = 4
command = [
    "./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)
]
print("C program was called\n")
print(command)
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

while not process.poll():
    try:
        # Try to open shared memory
        shm_fd = os.open(f"/dev/shm{SHM_NAME}", os.O_RDWR)  # No O_CREAT, only open
        shm = mmap.mmap(shm_fd, STRUCT_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
    except FileNotFoundError:
        raise FileNotFoundError("Shared memory segment does not exist. Please start the C program first.")

    # Read the `read` flag
    read_offset = STRUCT_SIZE - 4
    current_read = struct.unpack("i", shm[read_offset:read_offset + 4])[0]
    print(f"Current read count: {current_read}")

    # Unpack particles
    num_floats = PARTICLE_COUNT * 3
    STRUCT_FORMAT_PARTICLES = f"{num_floats}f"
    particles = struct.unpack(STRUCT_FORMAT_PARTICLES, shm[:num_floats * 4])

    particles_list = [particles[i:i+3] for i in range(0, len(particles), 3)]

    print(particles_list[:5])

    # Increment `read`
    new_read = current_read + 1
    shm[read_offset:read_offset + 4] = struct.pack("i", new_read)
    shm.flush()

    print(f"Updated read count to: {new_read}")

    shm.close()
    os.close(shm_fd)
