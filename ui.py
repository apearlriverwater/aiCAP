import sys
import random

#import matplotlib
import  gmTools as tls

#matplotlib.use("Qt5Agg")

import  gmTools as tls
CAPITION="旭日东升RingSun"
'''
     matlibplot 自带很好的交互接口，UI暂时不必使用Qt。主要的交互接口包括键盘输入、
  图上选择点位、矩形选择、多子图光标显示、text输入、Radio选项、CheckBox选项、按钮、Slider等。
  1、  局部子图显示
    https://matplotlib.org/gallery/subplots_axes_and_figures/
    axes_demo.html#sphx-glr-gallery-subplots-axes-and-figures-axes-demo-py
  2、 在Pyqt画布动态显示图形例子，含定时更新图形的类
    https://matplotlib.org/gallery/user_interfaces/embedding_in_qt_sgskip.html#
    sphx-glr-gallery-user-interfaces-embedding-in-qt-sgskip-py
    
  3、子图标注
     https://matplotlib.org/gallery/pyplots/text_commands.html#
     sphx-glr-gallery-pyplots-text-commands-py
     # 设置子图上标签title
    self.axes[fig_index].set_title('axes title')

    #在子图上显示文字
    self.axes[fig_index].text(3, 8, 'boxed italics text in data coords', style='italic',
            bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10})

    self.axes[fig_index].text(2, 6, r'an equation: $E=mc^2$', fontsize=15)

    self.axes[fig_index].text(3, 2, u'unicode: Institut f\374r Festk\366rperphysik')
    
  4、左右Y轴的数据不同
     https://matplotlib.org/gallery/api/two_scales.html#
     sphx-glr-gallery-api-two-scales-py
  5、同一子图中多种图形动态选择   
     https://matplotlib.org/gallery/widgets/check_buttons.html#
     sphx-glr-gallery-widgets-check-buttons-py
'''
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

'''
class Widget(FigureCanvas):
    def __init__(self, parent=None, width=4, height=3, dpi=100,
                 fig_count=3):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.axes=[]  #最多支持5个子图
        self.fig.subplots_adjust(hspace=0)
        fig_index=min(5,fig_count)*100+11

        x = np.arange(0, 100, 0.1)

        for i in range(0,min(5,fig_count)):
            self.axes.append(self.fig.add_subplot(fig_index+i))
            y_right=[(i+1)*np.sin(x+i*i),'y right']
            self.draw_fig(i,x,(i+1)* np.cos(x+i),y_right=None,
                          ylabel='line' + str(i),  linewidth=1)
            #self.draw_fig(i,x, (i+1)*np.sin(x+i*i),
            #              ylabel='line' + str(i), linewidth=2)

        self.set_fig_text('fig text sample')
        self.axes[2].plot([2], [1], 'o')
        self.axes[2].annotate('annotate', xy=(2, 1), xytext=(3, 4),
                    arrowprops=dict(facecolor='red', shrink=0.05))

        self.setWindowTitle("旭日东升RingSun")

    def set_fig_text(self,text):
        self.axes[0].text(1, 1.5,text,style='italic',
                bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10})

    def set_xlabel(self,text):
        self.axes[len(self.axes)-1].set_xlabel(text, color='black')

    def update_fig(self):
        for i in len(self.axes):
            self.axes[i].figure.canvas.draw()

    #在指定的子图绘图，可加图例和Y轴标签
    def draw_fig(self,fig_index,x,y,label=None,text='',
                 ylabel='label',y_right=None,linewidth=1):
        try:
            self.axes[fig_index].clear()
            color = 'tab:red'
            self.axes[fig_index].plot(x, y,
                        color=color, label=label, linewidth=linewidth)

            if len(text)>0:
                self.axes[fig_index].text(1, 1.5, text, style='italic',
                                  bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10})
            if len(ylabel)>0:
                self.axes[fig_index].set_ylabel(ylabel,color=color)


            #   x相同、右轴不同数据的呈现方式，不同类型参数同时显示：价格与主力资金  显示有问题，暂时放弃
            if y_right != None:
                color = 'tab:brown'
                ax2 = self.axes[fig_index].twinx()  # instantiate a second axes that shares the same x-axis
                ax2.clear()
                ax2.set_ylabel(y_right[0],color=color)  # we already handled the x-label with ax1
                ax2.plot(x, y_right[1],color=color)
                ax2.canvas.draw()
                # ax2.tick_params(axis='y2')

            self.axes[fig_index].figure.canvas.draw()

        except:
            pass
'''

class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("程序主窗口")

        self.files=[]

        #---------file menu -------------------------------
        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        #======================================================

        # ---------ta menu ----------------------------------------------
        self.ta_menu = QMenu('&Ta', self)

        # ++++++++++++++++RSI analyse++++++++++++++++++++++++
        self.add_menu_item(self.ta_menu, 'Ca&p 独立', self.taRSI,
                           QtCore.Qt.CTRL + QtCore.Qt.Key_P)

        #+++++++++++++++++Cap analyse+++++++++++++++++++++++++
        self.add_menu_item(self.ta_menu,'&Cap 集成', self.taCap,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_A)



        # ================================================================

        # ---------control START/STOP menu ----------------------------------------------
        '''
        elf.start_menu = QMenu('&Start', self)
        3self.menuBar().addMenu(self.start_menu)
        #self.start_menu.addAction('&Start', self.taStart)
        # 添加事件
        self.start_menu.get.connect(self.taStart)
        '''

        #---------help menu ---------------------------------
        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)
        # ======================================================

        '''
        self.main_widget = QWidget(self)

        l = QVBoxLayout(self.main_widget)
        self.fig=Widget(self.main_widget, width=16, height=12, dpi=100)
        l.addWidget(self.fig)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        '''
        # 状态条显示2秒
        self.statusBar().showMessage("hello matplotlib", 2000)

    # start stop
    def taStart(self):
        QMessageBox.about(self, "taStart", "taStart")

    #资金流分析
    def taCap(self):
        cap_path = 'data0322'
        filters = ['CAP-002', '005.dat']
        if len(self.files)==0:
            self.files = tls.get_filelist_from_path(cap_path, filters)

        stock, week, cap_data, kdata=tls.read_stock_data(self.files[0])
        count=len(cap_data)
        self.files=self.files[1:]
        x=np.arange(0, count, 1)
        klen=len(kdata)

        if klen==count:
            flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']).values
            # 累计主力总资金流
            total_flow = [flow[0]]
            for i in range(1, count):
                total_flow.append(total_flow[i - 1] + flow[i])

            self.fig.draw_fig(0, x, kdata.loc[:, 'close'], text=stock,
                              ylabel='close')

            self.fig.draw_fig(1, x, total_flow,ylabel='flow')

            self.fig.draw_fig(2, x, flow,ylabel='delta')


        self.fig.set_xlabel(stock)
        main_ui.setWindowTitle(CAPITION+'  '+stock)
        #self.fig.update_fig()

    # 资金流分析
    def taRSI(self):
        cap_path = 'data0322'
        filters = ['CAP-002', '005.dat']
        if len(self.files) == 0:
            self.files = tls.get_filelist_from_path(cap_path, filters)

        stock, week, cap_data, kdata = tls.read_stock_data(self.files[0])
        count = len(cap_data)
        self.files = self.files[1:]
        x = np.arange(0, count, 1)
        klen = len(kdata)

        if klen == count:
            flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']).values
            # 累计主力总资金流
            total_flow = [flow[0]]
            for i in range(1, count):
                total_flow.append(total_flow[i - 1] + flow[i])

        tls.draw_kline(stock,kdata,0,0,week,100,311,total_flow)

    # 增加菜单项
    def add_menu_item(self,menu,menu_name,menu_op,op_link):
        menu.addAction(menu_name, menu_op,op_link)
        self.menuBar().addMenu(menu)

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
    main_ui = ApplicationWindow()
    main_ui.setWindowTitle(CAPITION)
    main_ui.show()
    #aw.showFullScreen()
    app.exec_()