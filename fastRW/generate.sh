#!/bin/bash

gcc -fopenmp -o RWoperation RWoperation.c help/helper.c pcg_basic.c -lm

imagesFolder="./images"
freqFolder="./freq"

# Check if the folder exists
if [ -d "$imagesFolder" ]; then
    # Delete all .png files in the folder
    rm -f "$imagesFolder"/*.png
    echo "All .png files in '$imagesFolder' have been deleted."
else
    mkdir images
fi

if [ -d "$freqFolder" ]; then
    rm -f "$freqFolder"/*.csv
    rm -f "$freqFolder"/*.txt
    echo "All files in '$freqFolder' have been deleted."
else
    mkdir images

fi

# Test - Different dt
#for i in $(awk 'BEGIN{for(i=0.0001;i<=1;i*=10) printf "%.1f\n", i}'); do
#  python3 RW.py $i 100 1 0.25 0.001 10000 4
#done

# Test - Different Time steps - T
#for i in $(awk 'BEGIN{for(i=100;i<=1000;i+=100) printf "%.1f\n", i}'); do
#  python3 RW.py 0.1 $i 1 0.25 0.001 10000 4
#done

# Test - Different Diffusion Constant - D
#for i in $(awk 'BEGIN{for(i=0;i<=10;i+=1) printf "%.1f\n", i}'); do
#  python3 RW.py 0.1 1000 $i 0.25 0.001 10000 4
#done

# Test - Different Biases - b
#for i in $(awk 'BEGIN{for(i=-0.5;i<=0.5;i+=0.05) printf "%.1f\n", i}'); do
#  python3 RW.py 0.1 1000 1 $i 0.001 10000 4
#done

#Test - Different Gammas - g
#for i in $(awk 'BEGIN{for(i=0.0015;i>=0;i-=0.0001) printf "%.4f\n", i}'); do
# python3 RW.py 0.1 1000 1 0.25 $i 10000 4
#done


# One iteration, base
#             dt - T - D - b - g - part - cores
python3 RW.py 0.1 1000 1 0.05 0 1000 4
rm RWoperation
