from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np
from matplotlib.widgets import MultiCursor

# first set up the figure, the axis, and the plot element we want to animate   
fig = plt.figure()
a1=10
a2=15
ax1 = fig.add_subplot(2, 1, 1, xlim=(0, 2), ylim=(-a1, a1))
ax2 = fig.add_subplot(2, 1, 2, xlim=(0, 2), ylim=(-a2, a2))
line, = ax1.plot([], [], lw=2)
line2, = ax2.plot([], [], lw=2)


def init():
    line.set_data([], [])
    line2.set_data([], [])
    return line, line2


# animation function.  this is called sequentially
def animate(i):
    x = np.linspace(0, 2, 100)
    y = a1*np.sin(2 * np.pi * (x - 0.01 * i))
    line.set_data(x, y)

    x2 = np.linspace(0, 2, 100)
    y2 = a2*np.cos(2 * np.pi * (x2 - 0.01 * i)) * np.sin(2 * np.pi * (x - 0.01 * i))
    line2.set_data(x2, y2)
    return line, line2


anim1 = animation.FuncAnimation(fig, animate, init_func=init, frames=50, interval=10)

multi = MultiCursor(fig.canvas, (ax1,ax2), color='r', lw=1)

plt.show() 