import sys
import random

import matplotlib
matplotlib.use("Qt5Agg")

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np


class Widget(FigureCanvas):
    def __init__(self, parent=None, width=16, height=12, dpi=100,
                 fig_count=4):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.axes=[]  #最多支持5个子图
        self.fig.subplots_adjust(hspace=0)

        fig_index=min(5,fig_count)*100+11
        x = np.arange(0, 100, 0.1)
        for i in range(min(5,fig_count)):
            self.axes.append(self.fig.add_subplot(fig_index+i))
            self.draw_fig(i,x,(i+1)* np.cos(x+i),  linewidth=1)
            self.draw_fig(i,x, (i+1)*np.sin(x+i*i),
                          ylabel='line' + str(i), linewidth=2)

        self.setWindowTitle("旭日东升RingSun")

    #在指定的子图绘图，可加图例和Y轴标签
    def draw_fig(self,fig_index,x,y,label=None,ylabel='',linewidth=1):
        try:
            self.axes[fig_index].plot(x, y, label=label, linewidth=linewidth)
            if len(ylabel)>0:
                self.axes[fig_index].set_ylabel(ylabel)
        except:
            pass

class MyMplCanvas(FigureCanvas):
    """这是一个窗口部件，即QWidget（当然也是FigureCanvasAgg）"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # 每次plot()调用的时候，我们希望原来的坐标轴被清除(所以False)
        self.axes.hold(False)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class MyStaticMplCanvas(MyMplCanvas):
    """静态画布：一条正弦线"""
    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)


class MyDynamicMplCanvas(MyMplCanvas):
    """动态画布：每秒自动更新，更换一条折线。"""
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')

    def update_figure(self):
        # 构建4个随机整数，位于闭区间[0, 10]
        count=50
        l = [random.randint(0, count) for i in range(count)]

        self.axes.plot(range(count), l, 'r')
        self.draw()

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("程序主窗口")

        #---------file menu -------------------------------
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        #======================================================


        #---------help menu ---------------------------------
        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)
        # ======================================================

        self.main_widget = QWidget(self)

        l = QVBoxLayout(self.main_widget)
        sc=Widget(self.main_widget, width=16, height=12, dpi=100)
        l.addWidget(sc)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # 状态条显示2秒
        self.statusBar().showMessage("hello matplotlib", 2000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",
        """embedding_in_qt5.py example
        Copyright 2015 BoxControL

        This program is a simple example of a Qt5 application embedding matplotlib
        canvases. It is base on example from matplolib documentation, and initially was
        developed from Florent Rougon and Darren Dale.

        http://matplotlib.org/examples/user_interfaces/embedding_in_qt4.html

        It may be used and modified with no restriction; raw copies as well as
        modified versions may be distributed without limitation.
        """
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)

    aw = ApplicationWindow()
    aw.setWindowTitle("旭日东升RingSun")
    aw.show()
    #sys.exit(qApp.exec_())
    app.exec_()