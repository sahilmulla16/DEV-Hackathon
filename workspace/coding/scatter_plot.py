import matplotlib.pyplot as plt
import numpy as np

# Generate random data
np.random.seed(0)
x = np.random.randn(100)
y = np.random.randn(100)

# Create scatter plot
plt.figure(figsize=(8, 6))
plt.scatter(x, y, color='blue')
plt.title('Scatter Plot of Random Data')
plt.xlabel('X values')
plt.ylabel('Y values')
plt.grid(True)
plt.show()