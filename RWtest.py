import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Tkagg")

def analyticSolution(x, t, v, D=1):    
    lead = 1 / math.sqrt(4 * math.pi * D * t)
    exponent = -1 * ((x - (v * t)) ** 2)/(4 * D * t)
    return lead * (math.e ** exponent)

# This is a function to generate a list of the solution values above
def makeSolutionList(increments, t, v, D=1):
    returnList = [] # List holds solutions
    xVal = -increments # Set the x-value to negative iterations, which is the farthest out a particle could get in these conditions
    while xVal <= increments: # Iterate through each value on the applicable x-axis 
        returnList.append(analyticSolution(xVal, t, v, D)) # Append the calculation with parameters
        xVal += 1
    return returnList

def graphMultipleSeries(plots, xRange, title, xlabel, ylabel):
    for plot in plots: # Each list entry is a list of parameters and plots: [xVal, yVal, label, color, alpha, style="Plot"]
        yValues = plot[0]
        if len(xRange) != len(yValues):
            print("Ranges not the same. Returning.") 
            break
        
        
        label = plot[1]
        color = plot[2]
        alpha = plot[3]
        style = plot[4]

        if style == "Bar":
            plt.bar(xRange, yValues, label=label, color=color, alpha=alpha)
        elif style == "Plot":
            plt.plot(xRange, yValues, label=label, color=color, alpha=alpha)
        else:
            print("Error: Style not found. Using default, Bar.\n")

    plt.legend()
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)


value = analyticSolution(5.8, 40, 0)
print(f"Value: {value}")

solList = makeSolutionList(20, 40, 0)
series = [solList, "Test Parts", "black", 1, "Plot"]
plots = [series]
xRange = np.linspace(-20, 20, 41)
graphMultipleSeries(plots, xRange, "Fuck you", "My Patience", "My attention")
plt.show()