import matplotlib.pyplot as plt

# Sample data
categories = ['A', 'B', 'C', 'D', 'E']
scores = [10, 24, 30, 18, 40]

# Create bar chart
plt.figure(figsize=(8, 6))
plt.bar(categories, scores, color='skyblue')
plt.title('Sample Bar Chart')
plt.xlabel('Categories')
plt.ylabel('Scores')
plt.savefig('bar_chart.png')
plt.close()
print('Bar chart generated successfully as bar_chart.png')