import matplotlib.pyplot as plt
import numpy as np

t = np.linspace(0, 10, 100)
x = np.sin(t)
y = np.cos(t)
z = t

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z)
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')
ax.set_title('3D Scatter Plot')
plt.show()