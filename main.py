# coding:utf-8

# 导入matplotlib模块并使用Qt5Agg
import matplotlib

matplotlib.use('Qt5Agg')
# 使用 matplotlib中的FigureCanvas
# (在使用 Qt5 Backends中 FigureCanvas继承自QtWidgets.QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import sys
import gmTools as tls

class main_window(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super(main_window,self).__init__(parent)
        # 重新调整大小
        self.resize(800, 600)
        self.setWindowTitle("aiCAP")


        # 添加菜单中的按钮
        self.menu = QtWidgets.QMenu("分析")
        self.menu_action = QtWidgets.QAction("例子",self.menu)
        self.menu.addAction(self.menu_action)
        self.menuBar().addMenu(self.menu)
        # 添加事件
        self.menu_action.triggered.connect(self.do_plot_sample)

        self.menu_research = QtWidgets.QMenu("研究")
        self.menu_research_action = QtWidgets.QAction("移动平均", self.menu_research)
        self.menu_research.addAction(self.menu_research_action)
        self.menuBar().addMenu(self.menu_research)
        # 添加事件
        self.menu_research_action.triggered.connect(self.do_plot1)

        self.setCentralWidget(QtWidgets.QWidget())

        # 状态条显示2秒
        self.statusBar().showMessage("matplotlib 万岁!", 2000)

    # 绘图方法
    def do_plot_sample(self):
        # 清屏
        plt.cla()
        # 获取绘图并绘制
        fig = plt.figure(figsize=(20,16))
        ax =fig.add_axes([0.1,0.1,0.8,0.8])
        ax.set_xlim([-1,6])
        ax.set_ylim([-1,6])
        ax.plot([0,1,2,3,4,5],'o--')
        cavans = FigureCanvas(fig)
        # 将绘制好的图像设置为中心 Widget
        self.setCentralWidget(cavans)

    def do_plot1(self):
        tls.cacl_bs_by_cap()
# 运行程序
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = main_window()
    main_window.show()
    app.exec()