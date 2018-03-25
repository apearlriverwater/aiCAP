import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5 import QtWidgets

class Widget(FigureCanvas):
     def __init__(self, parent=None, width=5, height=4, dpi=100):
         fig = Figure(figsize=(width, height), dpi=100)
         FigureCanvas.__init__(self, fig)


         self.setParent(parent)
         fig.subplots_adjust(hspace=0)
         # 散点图
         self.axes = fig.add_subplot(411)
         self.axes.scatter(np.random.rand(20), np.random.rand(20))

         # 折线图
         self.axes2 = fig.add_subplot(412)
         x = np.arange(0, 5, 0.1)
         self.axes2.plot(x, np.sin(x), x, np.cos(x))

         # 散点图
         self.axes = fig.add_subplot(413)
         self.axes.scatter(np.random.rand(20), np.random.rand(20))

         # 折线图
         self.axes2 = fig.add_subplot(414)
         x = np.arange(0, 5, 0.1)
         self.axes2.plot(x, np.sin(x), x, np.cos(x))

         self.setWindowTitle("示例：matplotlib 绑定到 PyQt5")

         fig.savefig('1.png')

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())