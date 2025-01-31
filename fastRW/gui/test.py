
import struct
import time
import subprocess
import sysv_ipc
import sys
import os
import ctypes


# Define the DataParticle structure
class DataParticle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("freqx", ctypes.c_float),
    ]

# Define the ParticleDataList structure
class ParticleDataList(ctypes.Structure):
    _fields_ = [
        ("particles", DataParticle * 325),  # Array of 325 DataParticle structures
        ("count", ctypes.c_int),            # Integer field
        ("read", ctypes.c_bool),            # Boolean field
    ]


def read_shared_memory(shm, plf, pc):
        print("read_shared_memory\n")
        """ Reads complex data structure from shared memory. """
        buffer = shm.read()
        if len(buffer) != ctypes.sizeof(ParticleDataList):
            raise RuntimeError(f"Shared memory size mismatch: expected {ctypes.sizeof(ParticleDataList)}, got {len(buffer)}")

        unpacked = struct.unpack(plf, buffer)

        count = unpacked[pc * 3]
        read_flag = unpacked[pc * 3 + 1]

        print(f"Count: {count}")
        print(f"Read: {read_flag}")

        # Unpack the data:
        if not read_flag:
            print("python reads flag as false, begins reading data\n")

            newParticles = []

            check = False

            for i in range(count):
                x, y, freqx = unpacked[i * 3 : (i * 3) + 3]
                if freqx != 0:
                    check = True
                newParticles.extend([x, y, freqx])
                
            sendSetup = ParticleDataList()
            sendSetup.read = True
            shm.write(bytearray(sendSetup))

            buffer = shm.read()
            updated_data = ParticleDataList.from_buffer_copy(buffer)

            print("Updated read flag:", updated_data.read)
            
            if not check:
                print("No data in incoming list. returning.\n")
                return 1
            else:
                print(f"Read data with {count} particles.\n")
                return 0

# Constants for shared memory size and key (replace with your actual values)
SHM_KEY = 4755  # The shared memory key
SHM_SIZE = 3908  # Size of the shared memory segment (adjust accordingly)



particle_count = 325
particle_format = "fff"  # Format for one particle (float x, y, freqx)
particle_list_format = f"{particle_count * 3}f i 3x ?" 

dt = 1
T = 100
D = 1
b = 0
g = 0
particles = 10000
cores = 4
command = [
    "./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)
]
print("C program was called\n")
print(command)
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Setup shared memory (key should match C program)
try:
    # Open the shared memory segment
    shm = sysv_ipc.SharedMemory(SHM_KEY)
except sysv_ipc.ExistentialError:
    print("Shared memory segment not found.")
    exit(1)


count = 0
while True:
    if read_shared_memory(shm, particle_list_format, particle_count) == 1:
        count +=1
        if count == 3:
            break

stdout, stderr = process.communicate()

print(stdout)

shm.detach()