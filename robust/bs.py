import numpy as np

# Sample data points
data = np.random.randn(1000)  # Example dataset

# Compute histogram data
hist, bin_edges = np.histogram(data, bins=30, density=True)

# hist contains the normalized frequency values (probability density)
# bin_edges contains the bin boundaries
print("Histogram Data (Density):", hist)
print("Bin Edges:", bin_edges)

import numpy as np
import matplotlib.pyplot as plt

# Sample data points
data = np.random.randn(1000)  # Generate 1000 random points from a normal distribution

# Create a histogram
hist, bin_edges = np.histogram(data, bins=30, density=True)

# Plot histogram
plt.bar(bin_edges[:-1], hist, width=np.diff(bin_edges), alpha=0.7, color='blue', edgecolor='black')
plt.xlabel('Value')
plt.ylabel('Probability Density')
plt.title('Histogram as Distribution')
plt.show()
