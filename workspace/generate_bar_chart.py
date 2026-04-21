import matplotlib.pyplot as plt
import numpy as np

# Set random seed for reproducibility
np.random.seed(0)

# Generate random data
categories = ['A', 'B', 'C', 'D', 'E']
data = np.random.randint(1, 20, size=len(categories))

# Create bar chart
plt.figure(figsize=(8, 6))
plt.bar(categories, data, color='skyblue')
plt.title('Random Data Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Save the chart as PNG
plt.savefig('bar_chart.png')
plt.close()

print('Bar chart saved as bar_chart.png')