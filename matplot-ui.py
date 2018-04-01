import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import sys
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import MultiCursor
'''
Python学习-使用matplotlib画动态多图
https://www.cnblogs.com/blfshiye/p/5115410.html

Zoom Window
https://matplotlib.org/gallery/event_handling/zoom_window.html#
sphx-glr-gallery-event-handling-zoom-window-py

定义matplot用户交互界面的配置例子，含选项、按钮、slider以及对应的事件处理
键盘事件处理函数
鼠标移动位置
各部件的位置、大小均可配置
鼠标选址图像位置例子
https://matplotlib.org/gallery/event_handling/pick_event_demo2.html#
sphx-glr-gallery-event-handling-pick-event-demo2-py

矩阵区域选择
https://matplotlib.org/gallery/widgets/rectangle_selector.html#
sphx-glr-gallery-widgets-rectangle-selector-py
'''
fig, (ax,ax1) = plt.subplots(2)
left_space=0.10
widgets_start=0.025
widgets_hight=0.04
widgets_space=0.03
slider_width=0.5
reset_x=0.8
reset_width=0.1
plt.subplots_adjust(left=left_space, bottom=widgets_hight*5)
t = np.arange(0.0, 1.0, 0.001)
a0 = 5
f0 = 3
delta_f = 5.0
s = a0*np.sin(2*np.pi*f0*t)
l, = plt.plot(t, s, lw=2, color='red')
plt.axis([0, 1, -10, 10])

X = np.random.rand(100, 1000)
xs = np.mean(X, axis=1)
ys = np.std(X, axis=1)

#部件显示位置及颜色
axcolor = 'lightgoldenrodyellow'
reset_ax = plt.axes([reset_x,         widgets_start,  reset_width, widgets_hight*2+widgets_space])
freq_ax  = plt.axes([left_space,   widgets_start,  slider_width,   widgets_hight], facecolor=axcolor)
amp_ax   = plt.axes([left_space,   widgets_start*3,  slider_width,   widgets_hight], facecolor=axcolor)
radio_ax     = plt.axes([reset_x-reset_width,   widgets_start,  reset_width,  widgets_hight*2+widgets_space], facecolor=axcolor)

#部件定义
sfreq = Slider(freq_ax, 'Freq', 0.1, 30.0, valinit=f0)
samp = Slider(amp_ax, 'Amp', 0.1, 10.0, valinit=a0)
radio = RadioButtons(radio_ax, ('red', 'blue', 'green'), active=1)
button = Button(reset_ax, 'Reset', color=axcolor, hovercolor='0.975')

#定期更新图像例子
count=0
x = np.linspace(-3, 3)
#ax.plot(x, x ** 2)

ax.set_title('click on point to plot time series')
line, = ax.plot(x, x ** 2, 'o', picker=5)  # 5 points tolerance








#滑块参数变化事件处理函数
def update(val):
    amp = samp.val
    freq = sfreq.val
    l.set_ydata(amp*np.sin(2*np.pi*freq*t))
    fig.canvas.draw_idle()

sfreq.on_changed(update)
samp.on_changed(update)

#按钮clicked事件处理函数
def reset(event):
    sfreq.reset()
    samp.reset()
button.on_clicked(reset)

#Radio选项变化事件处理函数
def colorfunc(label):
    l.set_color(label)
    fig.canvas.draw_idle()
radio.on_clicked(colorfunc)

def press(event):
    print('press', event.key)
    sys.stdout.flush()
    if event.key == 'x':
        #其他处理函数
        fig.canvas.draw()

fig.canvas.mpl_connect('key_press_event', press)



def onpick(event):

    if event.artist != line:
        return True

    N = len(event.ind)
    if not N:
        return True

    figi, axs = plt.subplots(N, squeeze=False)
    for ax, dataind in zip(axs.flat, event.ind):
        ax.plot(X[dataind])
        ax.text(.05, .9, 'mu=%1.3f\nsigma=%1.3f' % (xs[dataind], ys[dataind]),
                transform=ax.transAxes, va='top')
        ax.set_ylim(-0.5, 1.5)
    figi.show()
    return True

fig.canvas.mpl_connect('pick_event', onpick)

#花式文本框:
plt.text(0, 6.5, "test", size=50, rotation=30.,ha="center", va="center",bbox=dict(boxstyle="round",ec=(1., 0.5, 0.5),fc=(1., 0.8, 0.8),))
plt.text(0, 4.4, "test", size=50, rotation=-30.,ha="right", va="top",bbox=dict(boxstyle="square",ec=(1., 0.5, 0.5),fc=(1., 0.8, 0.8),))
plt.draw()

#数学公式:
plt.title(r'$\alpha_i > \beta_i$', fontsize=20)
plt.text(0.01, 2.2, r'$\sum_{i=0}^\infty x_i$', fontsize=20)
plt.text(0.12, 3.6, r'$\mathcal{A}\mathrm{sin}(2 \omega t)$', fontsize=20)

#multi = MultiCursor(fig.canvas, (ax,ax1), color='r', lw=1)

from matplotlib import pyplot as plt
from matplotlib import animation

# first set up the figure, the axis, and the plot element we want to animate
ax12 = fig.add_subplot(2, 1, 1, xlim=(0, 2), ylim=(-4, 4))
ax22 = fig.add_subplot(2, 1, 2, xlim=(0, 2), ylim=(-4, 4))
line, = ax12.plot([], [], lw=2)
line2, = ax22.plot([], [], lw=2)




def update_title(axes):
    global  count

    count+=1
    #ax.plot(x,count *np.sin(count*x*x))
    #
    #ax.figure.canvas.draw()
    ax1.clear()
    ax1.set_title(datetime.now())
    s = a0 * np.sin(count * np.pi * f0 * t)
    ax1.plot(t, s, lw=2, color='red')
    ax1.figure.canvas.draw()
# Create a new timer object. Set the interval to 100 milliseconds
# (1000 is default) and tell the timer what function should be called.
timer = fig.canvas.new_timer(interval=100)
timer.add_callback(update_title, ax)
timer.start()

plt.show()