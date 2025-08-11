#!/bin/bash
set -e

echo "Installing Python dependencies"
pip install -r requirements.txt

echo "Building C code"
mkdir -p build
cd build
cmake ..
make
cd ..

echo "Done"