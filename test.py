#from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
#from matplotlib import animation
import numpy as np

# first set up the figure, the axis, and the plot element we want to animate
fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1, xlim=(0, 2), ylim=(-40, 40))
ax2 = fig.add_subplot(2, 1, 2, xlim=(0, 2), ylim=(-4, 4))
line, = ax1.plot([], [], lw=2)
line2, = ax2.plot([], [], lw=2)
count=0

def init():
    line.set_data([], [])
    line2.set_data([], [])
    return line, line2


# animation function.  this is called sequentially
def animate(i):
    x = np.linspace(0, 2, 100)
    y = (i%40)*np.sin(2 * np.pi * (x - 0.01 * i))
    line.set_data(x, y)

    x2 = np.linspace(0, 2, 500)
    y2 = np.cos(2 * np.pi * (x2 - 0.05 * i)) * np.sin(2 * np.pi * (x2 - 0.08 * i))
    line2.set_data(x2, y2)
    return line, line2

def update_title(axes):
    global  count

    count+=1
    animate(count)
    ax1.figure.canvas.draw()

timer = fig.canvas.new_timer(interval=100)
timer.add_callback(update_title, ax1)
timer.start()

plt.show()