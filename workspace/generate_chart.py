import matplotlib.pyplot as plt
import json

# Sample data structure - this would be extracted from report.txt
# Placeholder data for demonstration
regions = ['South Asia', 'Middle East', 'Southeast Asia', 'Africa']
muslim_pop = [500, 400, 300, 200]  # in millions
hindu_pop = [450, 50, 100, 30]

plt.figure(figsize=(10, 6))
bar_width = 0.35
index = range(len(regions))

bar1 = plt.bar(index, muslim_pop, bar_width, label='Muslim', color='blue')
bar2 = plt.bar([i + bar_width for i in index], hindu_pop, bar_width, label='Hindu', color='orange')

plt.xlabel('Region')
plt.ylabel('Population (in millions)')
plt.title('Muslim and Hindu Population by Region')
plt.xticks([i + bar_width / 2 for i in index], regions)
plt.legend()

plt.tight_layout()
plt.savefig('population_chart.png')
plt.close()

# Save data to JSON for verification
chart_data = {
    'regions': regions,
    'muslim_population': muslim_pop,
    'hindu_population': hindu_pop
}
with open('chart_data.json', 'w') as f:
    json.dump(chart_data, f)
