
import struct
import time
import subprocess
import sysv_ipc
import sys
import os

sys.path.append('/home/raykpridgen/research/randomwalks/RandomWalks/fastRW')
#print(sys.path)

print(os.getcwd())




# Constants for shared memory size and key (replace with your actual values)
SHM_KEY = 4755  # The shared memory key
SHM_SIZE = 3908  # Size of the shared memory segment (adjust accordingly)

# Open the shared memory segment using sysv_ipc
shm = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, SHM_SIZE)

dt = 1
T = 100
D = 1
b = 0
g = 0
particles = 100000
cores = 4
command = [
    "sudo", "./RWoperation", str(dt), str(T), str(D), str(b), str(g), str(particles), str(cores)
]
print("C program was called\n")
print(command)
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Function to read and simulate flag change
def read_and_switch_flag():
    # Read raw data from the shared memory
    raw_data = shm.read(SHM_SIZE)

    # Unpack the data (first 5 bytes: count and read_flag)
    count, read_flag = struct.unpack("I?", raw_data[:5])
    
    print(f"Initial count: {count}, Read flag: {read_flag}")

    # If the read flag is not already False, we simulate switching it to False
    if not read_flag:
        print("Switching the read flag to False...")
        # Change the read flag to False
        new_data = struct.pack("I?", count, False)
        
        # Write the modified data back to shared memory (first 5 bytes: count and False read_flag)
        shm.write(new_data)

        # Sleep for a bit so the C program can process
        time.sleep(1)

# Run the flag switching function
while process.poll() is not None:
    read_and_switch_flag()
    time.sleep(0.1)  # Check every 100ms (adjust timing as needed)
