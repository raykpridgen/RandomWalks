#!/bin/bash

gcc -o RWoperation RWoperation.c help/helper.c pcg_basic.c -lm -fopenmp
./RWoperation 0.1 1000 1 0.05 0 10 4

# Give some time for the C program to write data
sleep 1  # Adjust this time if necessary

# Run the Python script to read from shared memory
python3 shared.py

rm RWoperation

