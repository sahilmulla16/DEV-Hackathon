import matplotlib.pyplot as plt

# Data
countries = ['India', 'Indonesia', 'Pakistan', 'Bangladesh', 'Nigeria', 'Nepal']
hindus = [1170, 0, 0, 0, 0, 29]
muslims = [206.5, 242, 212, 153, 106, 1.6]

# Create grouped bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.35
index = range(len(countries))

bar1 = ax.bar(index, hindus, bar_width, label='Hindus', color='orange')
bar2 = ax.bar([i + bar_width for i in index], Muslims, bar_width, label='Muslims', color='green')

ax.set_xlabel('Country')
ax.set_ylabel('Population (millions)')
ax.set_title('Muslim and Hindu Population by Country (Absolute Numbers)')
ax.set_xticks([i + bar_width / 2 for i in index])
ax.set_xticklabels(countries)
ax.legend()

plt.tight_layout()
plt.savefig('population_chart.png')
plt.close()