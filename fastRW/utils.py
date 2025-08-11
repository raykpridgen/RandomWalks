import csv
from collections import defaultdict

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
    """
    This function is designed to take a name for a CSV file, convert the values in the file starting 
    as (X,Y) to (X, frequency(X)). Then, this function places these frequencies into two separate CSV
    files for the top line and the bottom line.

    Input: file path, output name 1, output name 2, number of particles to process

    Output: No output, operates on files
    """

    output1 = output1 + ".csv"
    output2 = output2 + ".csv"
    #Dictionaries for top and bottom particles
    coordTopDict = defaultdict(int)
    coordBottomDict = defaultdict(int)

    # Read values out of CSV into a dictionary
    with open(input, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Ignore header
            if (row[0] == 'x'):
                continue
            if (row[1] == '1'):
                coordTopDict[row[0]] += 1
                # Add to top dictionary
            elif (row[1] == '0'):
                # Add to bottom dictionary
                coordBottomDict[row[0]] += 1
    #print(sum(coordTopDict.values()))
    #print(sum(coordBottomDict.values()))

    # Write the values into output CSV file
    with open(output1, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x', 'frequency'])  # Write header
        for x, freq in coordTopDict.items():
            writer.writerow([x, freq / numParticles])
    
    with open(output2, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['x', 'frequency'])  # Write header
        for x, freq in coordBottomDict.items():
            writer.writerow([x, freq / numParticles])
    return

def writeFreqTXT(input, output1, output2, numParticles):
    """
    This function is designed to take a name for a CSV file, convert the values in the file starting 
    as (X,Y) to (X, frequency(X)). Then, this function places these frequencies into two separate CSV
    files for the top line and the bottom line.

    Input: file path, output name 1, output name 2, number of particles to process

    Output: No output, operates on files
    """
    output1 = output1 + ".txt"
    output2 = output2 + ".txt"
    #Dictionaries for top and bottom particles
    coordTopDict = defaultdict(int)
    coordBottomDict = defaultdict(int)

    # Read values out of CSV into a dictionary
    with open(input, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Ignore header
            if (row[0] == 'x'):
                continue
            if (row[1] == '1'):
                coordTopDict[float(row[0])] += 1
                # Add to top dictionary
            elif (row[1] == '0'):
                # Add to bottom dictionary
                coordBottomDict[float(row[0])] += 1
    #print(sum(coordTopDict.values()))
    #print(sum(coordBottomDict.values()))

    # Write the values into output CSV file
    with open(output1, 'w') as txtfile:
        txtfile.write('x, frequency')  # Write header
        for x, freq in coordTopDict.items():
            txtfile.write(f"\n{x}, {freq / numParticles}")

    with open(output2, 'w') as txtfile:
        txtfile.write('x, frequency') # Write header
        for x, freq in coordBottomDict.items():
            txtfile.write(f"\n{x}, {freq / numParticles}")
    return