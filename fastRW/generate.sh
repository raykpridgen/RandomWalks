#!/bin/bash

gcc -fopenmp -o RWoperation RWoperation.c pcg_basic.c -lm

folder="./images"

# Check if the folder exists
if [ -d "$folder" ]; then
    # Delete all .png files in the folder
    rm -f "$folder"/*.png
    echo "All .png files in '$folder' have been deleted."
else
    mkdir images
fi
# Test 1 - Different Biases
#for i in $(awk 'BEGIN{for(i=-1;i<=1;i+=0.1) printf "%.1f\n", i}'); do
#  python3 RW.py 0.1 1000 1 $i 0.001 100000 4
#done

# Test 2 - Different Time steps
#for i in $(awk 'BEGIN{for(i=100;i<=1000;i+=100) printf "%.1f\n", i}'); do
#  python3 RW.py 0.1 $i 1 0.25 0.001 100000 4
#done

#Test 3 - Different Gammas
#for i in $(awk 'BEGIN{for(i=0;i<=0.1;i+=0.005) printf "%.1f\n", i}'); do
# python3 RW.py 0.1 1000 1 0.25 $i 10000 4
#done

# One iteration, base
python3 RW.py 0.1 1000 1 0.25 0.0005 10000 4
rm RWoperation

