import matplotlib.pyplot as plt
import numpy as np

# Generate random data
data = np.random.randint(1, 100, 10)
categories = [f'Category {i+1}' for i in range(10)]

# Create bar chart
plt.figure(figsize=(10, 6))
plt.bar(categories, data, color='skyblue')
plt.title('Random Data Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.xticks(rotation=45)

# Save the chart
plt.tight_layout()
plt.savefig('bar_chart.png')
plt.close()

print('Bar chart saved as bar_chart.png')