import csv
from collections import Counter

def readDataCSV(filepath):
    """
    This function reads CSV data from a file into two lists, one list for the x-values on the top line and the 
    other for the bottom line. This CSV file should come from the simulation ran in C.

    Input: file path

    Output: top line list, bottom line list
    """

    x_top, x_bottom = [], []
    with open(filepath, mode='r') as file:
        reader = csv.DictReader(file)  # Automatically handles the header row
        for row in reader:
            x_val = float(row['x'])
            y_val = int(row['y'])
            if y_val == 1:
                x_top.append(x_val)
            else:
                x_bottom.append(x_val)
    return x_top, x_bottom

def writeFreqCSV(input, output1, output2, numParticles):
    """write
    This function takes a filename for a list of particles. From there, these particles are converted into frequencies
    that can be used as a histogram. Since each x-value can have a top or a bottom particle, it needs to be seperated
    into two lists for top particles and bottom particles, hence the two output files. 

    Input: file path, output name 1, output name 2, number of particles to process

    Output: No output, operates on files
    """

    # Dictionaries to hold each x-value and number of occurences
    x_countsTop = Counter()
    x_countsBottom = Counter()

    # Open file from name
    with open(input, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Ignore header row
            if (row[0] == 'x'):
                continue
            # String to float
            x = float(row[0])  # Convert x to a float (if necessary)
            # If the particle is on y = 1
            if (row[1] == '1'):
                # Increment dictionary for specific x-value
                x_countsTop[x] += 1
            # If particle is on y = 0
            else:
                # Increment dictionary
                x_countsBottom[x] += 1
 
    # Write the counts to the output CSV file
    with open(output1, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x', 'frequency'])  # Write header
        for x, freq in x_countsTop.items():
            writer.writerow([x, freq / numParticles])
    
    with open(output2, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x', 'frequency'])  # Write header
        for x, freq in x_countsBottom.items():
            writer.writerow([x, -freq / numParticles])

def writeFreqText(input, output1, output2, numParticles):
    """
    This function takes a filename for a list of particles. From there, these particles are converted into frequencies
    that can be used as a histogram. Since each x-value can have a top or a bottom particle, it needs to be seperated
    into two lists for top particles and bottom particles, hence the two output files. This is exactly like the other 
    function except it operates on .txt files.

    Input: file path, output name 1, output name 2, number of particles to process

    Output: No output, operates on files
    """
    
    # Dictionaries to hold each x-value and number of occurences
    x_countsTop = Counter()
    x_countsBottom = Counter()

    # Open file from name
    with open(input, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Ignore header row
            if (row[0] == 'x'):
                continue
            # String to float
            x = float(row[0])  # Convert x to a float (if necessary)
            # If the particle is on y = 1
            if (row[1] == '1'):
                # Increment dictionary for specific x-value
                x_countsTop[round(x, 2)] += 1
            # If particle is on y = 0
            else:
                # Increment dictionary
                x_countsBottom[round(x, 2)] += 1
 
    # Write the counts to the output file
    with open(output1, 'w') as txtfile:
        txtfile.write("X-Value : Frequency")  # Write header
        for x, freq in x_countsTop.items():
            #print(f"{x}, {freq}")
            freqValue = freq / numParticles
            txtfile.write(f"\n{x}, {freqValue}")
    
    with open(output2, 'w') as txtfile:
        txtfile.write("X-Value : Frequency")  # Write header
        for x, freq in x_countsBottom.items():
            txtfile.write(f"\n{x}, {freqValue}")