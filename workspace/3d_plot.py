import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Generate sample data
def generate_data():
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x**2 + y**2))
    return x, y, z

# Create 3D surface plot
def main():
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    x, y, z = generate_data()
    surf = ax.plot_surface(x, y, z, cmap='viridis', edgecolor='none')

    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    plt.title('3D Surface Plot')
    plt.show()

if __name__ == '__main__':
    main()