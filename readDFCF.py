# -*- coding: utf-8 -*-

'''
  1、操作dfcf界面的控制程序，自动控制软件启动、登录、功能项选择等行情
  东方财富PC客户端可提供的数据：
  1.1 沪深个股和自选股的实时信息
    行情列表：当前实时行情快照信息
    增仓排名：当日、3日、5日、10日主力资金增仓排名情况
    资金流向：最新价、涨幅，主力净流入，集合竞价成交金额（深市不准），实时超大单、大单、中单和小单数据
    DDE决策：最新价、涨幅，当日资金流，5、10日资金流，DDX飘红天数，实时超大单、大单、中单和小单买卖占比
    财务数据：个股详细的财务数据，包括：更新日期	总股本	流通A股	人均持股数	每股收益	每股净资产
            加权净资产收益率	营业总收入	营业总收入同比	营业利润	投资收益	利润总额	归属净利润
            归属净利润同比	未分配利润	每股未分配利润	销售毛利率	总资产	流动资产	固定资产
            无形资产	总负债	流动负债	长期负债	资产负债比率	股东权益	股东权益比	公积金
            每股公积金	流通B股	H股	上市日期
    阶段统计：唯一可自定义感兴趣信息的类型，包括：最新价、涨幅，换手、总手，5、10、20日涨幅、换手率和
            跑赢大盘天数。需下载最新数据。除资金流、DDE和增仓排名等L2数据外，均可在此处自定义需要的数据。
            利用阶段统计数据可粗略判断标的当前走势。

    盈利预测：机构研究报告中心，数据准确度一般，暂时不关注
    多股同列：实时人工看盘使用。

  1.2 大户室数据
      考虑用于短线操作，监测到连续大幅度的主动性买盘时跟进，次日卖出（最多持仓不要超过3天），相反则采取卖出
   操作。收集并记录大户室的数据结合ticks数据进行分析，研究此策略的可行性。同时要考虑大盘走势。
      实时资金流是进行判断分析的基础，需要连续监控实时资金流的变化情况，收集实际成交数据判断市场热度、选择
   合适的介入对象。

  1.2.1 顶级挂单
      包括挂单时间、价格与总数、总金额，附带数据包括市盈率、换手率等参数。考虑用于短线操作。

  1.2.2 拖拉机单
       待研究数据用途

  1.2.3 强势狙击


  1.2.4 主力踪迹
        记录最近3个交易日的主力信息。

  1.2.5 L2核心内参

  1.2.6 资金全景
        与资金流向相同

  1.2.7 DDE全景
    DDE决策
  1.2.8 风云全景
     一致预期的标的，数据不能导出，未考虑好使用。

  1.3 沪深指数
      可方便导出主要市场参数。
      可导出全球主要指数。
  1.4 沪深板块

  1.5 数据中心
     大量数据，待挖掘使用。
  2、在交易日定期利用数据导出功能把数据导出到剪辑板或者文件再进行处理
  2.1 导出大盘指数情况
    未实现。
    可利用掘金的数据订阅功能实现数据收集。

  2.2 全市场涨跌情况：全市场快照，自定义标的快照
      通过资金流获得，方便统计涨跌情况、资金流入情况。
      未实现。

  2.3 自选股涨跌与资金流情况
      含平安推荐股票涨跌情况。
      已实现一致预期等自定义标的的直接导入分析。

  2.4 基于导出数据的价值挖掘  初步条件选股或盘中选股，交易期间动态优化
    一买选股（底部起涨，参数待进一步优化）
            条件与：15日内创30日新低，10日内连续缩量，
            条件或：5日内温和上涨，10日内间歇放量，5日内突然放量
            东方财富条件选股不好用，改用掘金量化终端自行选择
    二买选股（阶段突破）：
        1）搓揉线后的突破
        2）主力增仓突破  盘中实时导出数据，已能体现主力的趋势：1、5、10日增仓数据很有价值，
           每15分钟判断一次自选标的、每小时分析一次全市场前500个标的主力资金进出情况

   2.5 待挖掘使用的数据
      阶段统计：可组合定义各种参数，包括重要的基础参数：市盈率、股本、流通盘、换手率等
          自定义1至5日、10日、20日、30日成交量（换手率）、成交金额、振幅、复权后的均价，
                自行计算波动率：寻找突破者


      行情列表：包含1、3、6日换手率，量比：体现成交量的变化，阶段换手率突变者
                 1、3、6日涨幅，体现价格变化趋势
                 日内波动：价格波动程度
                 价格波动率：价格波动小者
      资金流：
          主力波动率：1、3、5、10四种交易日增仓、减仓，突然放量加或减，不能放在阶段统计

      综合主力、总量、价格综合：

  2.5 关注点hot

  3、必要时截屏发送相关图形，手机客户端有相关图形，目前不是十分迫切


'''
import pyautogui
import subprocess
import win32gui, win32api, win32con  #module name pywin32
import win32clipboard as clipboard
import datetime,time,re
import pandas as pd
import os,stat
import logging
import pyHook,pythoncom
import threading
import time


from multiprocessing import Process, Lock,Pipe,Pool,cpu_count,Queue,freeze_support


#import numpy as np
import gmTools
#import infWECHAT as wechat


logging.basicConfig(level = logging.DEBUG
                    ,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


'''
-----------掘金主要指数--------------------------------
SHSE.000001 	上证指数  SHSE.000009 	上证380
SHSE.000010 	上证180  SHSE.000016 	上证50
SHSE.000029 	180价值  SHSE.000042 	上证央企
SHSE.000044 	上证中盘  SHSE.000045 	上证小盘
SHSE.000043 	超大盘    SHSE.000069 	消费80
SHSE.000097 	高端装备  SHSE.000108 	380消费

SHSE.000300 	沪深300  SHSE.000838 	创业价值
SHSE.000905 	中证500  SHSE.000906 	中证800
SHSE.000932 	中证消费  SHSE.000933 	中证医药
SHSE.000934 	中证金融  SHSE.000960 	中证龙头
SHSE.000964 	中证新兴

SZSE.399001 	深证成指  SZSE.399002 	深成指R
SZSE.399005 	中小板指  SZSE.399006 	创业板指

SZSE.399008 	中小300  SZSE.399012 	创业300
SZSE.399013 	深市精选  SZSE.399673 	创业板50
-----------掘金主要指数--------------------------------
'''

STOCK_BLOCK = 'SHSE.000906'

#重点关注的板块
FAVORTE_BLOCKS=['SHSE.000009','SHSE.000016','SHSE.000097','SHSE.000300',
                'SHSE.000838','SZSE.399008','SZSE.399012','SZSE.399013','SZSE.399673']

dfcf_main_file = ["c:\\eastmoney\\swc8\\mainfree.exe",  "E:\\02soft\\99eastmoney\\swc8\\mainfree.exe"]

mystock_list = ['自选股', 'qsz2', '1buy', '2buy', 'paz', 'pabuy', 'hot', 'etf']

dfcf_top_menu_points=[
    ['首页',28,44],
    ['全景图',108,44],
    ['自选股',188,44],
    ['工具',510,16],
    ['设置自选股',201,44],
    ['沪深排行',266,44],
    ['板块检测',332,44],
    ['沪深指数',394,44]
]

dfcf_left_menu_points=[
    ['全景图',40,69],
    ['自选股',40,99],
    ['沪深个股',40,127],
    ['沪深板块',40,157],
    ['沪深指数',40,187],
    ['资讯中心',40,221],
    ['数据中心',40,249],
    ['L2大户室',40,339],
    ['股指期货',40,369],
    ['期权市场',40,399],
    ['全球指数',40,429],
    ['港股市场',40,459],
    ['美股市场',40,489],
    ['期货现货',40,519],
    ['基金债券',40,549],
    ['外汇市场',40,579],
    ['炒股大赛',40,609],
    ['委托交易',40,639]
]

#设置自选股主要操作
setup_my_stock_ui_item=[
    ['addstock',712,474],
    ['自选股',464,282],
    ['qsz2',464,302],
    ['1buy',464,322],
    ['2buy',464,342],
    ['pazq',464,362],
    ['pabuy',464,385],
    ['hot',464,406],
    ['clearstock',848,474],
    ['exit',796,516]
]

#沪深排行
hs_rank_top_menu=[
    ['行情列表',128,64],
    ['增仓排名',207,64],
    ['资金流向',274,64],
    ['DDE决策',343,64],
    ['盈利预测',423,64],
    ['财务数据',483,64],
    ['阶段统计',560,64]
]
hs_rank_botton_menu=[
    ['沪深A股',128,717],
    ['上证A股', 184, 717],
    ['深证A股', 184, 717],
    ['上证A股', 242, 717],
    ['中小板', 315, 717],
    ['创业板', 364, 717]
]

# 自选股  top Menu与hs_rank_top_menu一致
mystock_botton_menu=[
    ['自选股',122,519],
    ['qsz2', 176, 519],
    ['1buy',222,519],
    ['2buy',266,519],
    ['pazq',308,519],
    ['pabuy',345,519],
    ['hot',387,519],
    ['etf',432,519]
]

# no operate ,only for delay
no_operate=[
    ['nop',270,150]
]
#L2Room
L2Room_top_menu=[
    ['顶级挂单',127,62],
    ['拖拉机单',196,62],
    ['强势狙击',266,62],
    ['主力踪迹',329,62],
    ['L2核心内参',400,62],
    ['资金全景',476,62],
    ['DDE全景',546,62]
]




#true file exist ,false file not exist
def file_exist(file_path):
    try:
        os.stat(file_path)
        return True
    except:
        return False

#保存文件，title=True时若文件不存在把第一行作为title否则丢弃第一行
def write_text_file(file_path,msg,title=[]):

    def write_list(f,msg):
        for line in  msg:
            tmp='%s'%line[0]
            for item in line[1:]:
                tmp+='\t%s'%item

            tmp += '\n'
            f.write(tmp)

    #----------------------------------------------------------
    try:
        if file_exist(file_path=file_path):
            f = open(file_path, "a")
            write_list(f,msg)
            f.close()
        else:
            f = open(file_path, "wt")
            if len(title)>0:
                msg1=title[0]
                for item in title[1:]:
                    msg1+= '\t'+item

                msg1 += '\n'
                f.write(msg1)

            write_list(f,msg)
            f.close()

    except:
        write_log_msg()

'''
    均线多头向上判断：多头向上时返回true，否则false
        dataList 待计算数据
        maList 周期序列列表，最少三个周期,
        nLastWeeks最少程序周期数
        均线单调递增、多头排列
'''
def close_ma_up(closing, maList, nLastWeeks):
    bRet = True
    ma = []
    CaclCount = sum(maList) * 2 + nLastWeeks
    count = len(closing)

    if count >= CaclCount:
        for week in maList:
            tmp = (closing.rolling(week).mean()[-nLastWeeks:])
            if tmp.tolist()!=tmp.sort_values(0, True).tolist():  # 必须单调递增
                bRet = False
                break
            else:
                index = maList.index(week)
                if index > 0 and index < count:
                    # 多头检测 小周期均线值大于大周期均线值
                    diff = ma - tmp
                    diff = diff[diff >= 0]
                    if diff.count() < nLastWeeks:
                        bRet = False
                        break

                ma = tmp.copy()
    else:
        bRet = False

    return bRet


'''
    均线多头向下判断：多头向下时返回true，否则false
        dataList 待计算数据
        maList 周期序列列表，最少三个周期,
        nLastWeeks最少程序周期数
        单调递减、空头排列
'''
def close_ma_down(closing, maList, nLastWeeks):
    bRet = True
    CaclCount = sum(maList) * 2 + nLastWeeks
    count = len(closing)
    if count>=CaclCount:
        for week in maList:
            tmp = (closing.rolling(week).mean()[-nLastWeeks:])

            if tmp.tolist()!=tmp.sort_values(0, False).tolist():  # 必须单调递减
                bRet = False
                break
            else:
                index = maList.index(week)
                if index > 0 and index < count:
                    # 空头检测 小周期均线值小于大周期均线值
                    diff = ma - tmp
                    diff = diff[diff <=0]
                    if diff.count() < nLastWeeks:
                        bRet = False
                        break

                ma = tmp.copy()
    else:
        bRet = False

    return bRet

#自动向自选股添加需要的标的
def add_stock_2_mystock(group_name,stock_list):
    try:
        if len(stock_list)==0:
            return

        found = False
        for item in dfcf_top_menu_points:
            if '工具' == item[0]:
                pyautogui.click(item[1], item[2])
                key_list=[['down', 1],['enter', 1]]
                press_keys(key_list)
                found = True
                break

        if found == False:
            return

        found=False
        for item in setup_my_stock_ui_item:
            if group_name==item[0]:
                pyautogui.click(item[1],item[2])
                found=True
                break

        if found==False:
            return

        found = False
        for item in setup_my_stock_ui_item:
            if 'clearstock' == item[0]:
                time.sleep(0.1)
                pyautogui.click(item[1], item[2])
                found = True
                time.sleep(0.1)

                #清空自选股
                hwnd_dfcf = win32gui.FindWindow(None, '清空自选股')
                if hwnd_dfcf > 0:
                    press_keys([['enter', 1]])

                time.sleep(0.1)
                break

        if found == False:
            return

        for stock in stock_list:
            key_list = [[char, 1] for char in stock]
            key_list.append(['enter', 1])
            press_keys(key_list)
            time.sleep(0.1)

        for item in setup_my_stock_ui_item:
            if 'exit' == item[0]:
                pyautogui.click(item[1], item[2])
                break
    except:
        write_log_msg()

def write_log_msg():
    import traceback
    now = datetime.datetime.now()
    f = open("errorlog.txt", "a+")
    f.write('\n'+str(now)+'\n')
    f.write(traceback.format_exc())
    f.close()
    print(traceback.format_exc())

#进程间共享数据的变量，访问前加锁、解锁
class share_data:
    def __init__(self):
        self._lock = Lock()
        self._data=[]

    def set_data(self,data):
        self._lock.acquire()
        self._data.append(data)
        self._lock.release()

    def get_data(self):
        self._lock.acquire()
        data=self._data[-1]
        self._data = self._data[:-1]
        self._lock.release()
        return data

    def clear_data(self):
        self._lock.acquire()
        self._data = None
        self._lock.release()

    def is_empty(self):
        self._lock.acquire()
        ret=len(self._data)==0
        self._lock.release()
        return ret

capflow =share_data
class cWindow:
    def __init__(self):
        self._hwnd = None

    def SetAsForegroundWindow(self):
        # First, make sure all (other) always-on-top windows are hidden.
        self.hide_always_on_top_windows()
        win32gui.SetForegroundWindow(self._hwnd)

    def Maximize(self):
        win32gui.ShowWindow(self._hwnd, win32con.SW_MAXIMIZE)

    def _window_enum_callback(self, hwnd, regex):
        '''Pass to win32gui.EnumWindows() to check all open windows'''
        if self._hwnd is None and re.match(regex, str(win32gui.GetWindowText(hwnd))) is not None:
            self._hwnd = hwnd

    def find_window_regex(self, regex):
        self._hwnd = None
        win32gui.EnumWindows(self._window_enum_callback, regex)

    def hide_always_on_top_windows(self):
        win32gui.EnumWindows(self._window_enum_callback_hide, None)

    def _window_enum_callback_hide(self, hwnd, unused):
        if hwnd != self._hwnd:  # ignore self
            # Is the window visible and marked as an always-on-top (topmost) window?
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowLong(hwnd,
                                    win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST:
                # Ignore windows of class 'Button' (the Start button overlay) and
                # 'Shell_TrayWnd' (the Task Bar).
                className = win32gui.GetClassName(hwnd)
                if not (className == 'Button' or className == 'Shell_TrayWnd'):
                    # Force-minimize the window.
                    # Fortunately, this seems to work even with windows that
                    # have no Minimize button.
                    # Note that if we tried to hide the window with SW_HIDE,
                    # it would disappear from the Task Bar as well.
                    win32gui.ShowWindow(hwnd, win32con.SW_FORCEMINIMIZE)

def click_dfcf_menu(menu_points=dfcf_top_menu_points,menu_name='首页'):
    try:
        for item in menu_points:
            if menu_name==item[0]:
                pyautogui.click(item[1],item[2])
                time.sleep(0.001)
                return  True

        return  False
    except:
        pass

def show_dfcf():
    time.sleep(0.5)
    try:
        regex ='东方财富终端'
        cW = cWindow()
        cW.find_window_regex(regex)
        cW.Maximize()
        cW.SetAsForegroundWindow()
        #点击首页
        click_dfcf_menu(menu_points=dfcf_top_menu_points, menu_name='首页')
    except:
        write_log_msg()


def click_fig(fig_path,off_x=0,off_y=0):
    ret=True
    try:
        x, y = pyautogui.locateCenterOnScreen(fig_path)
        if x>0 and y>0:
            pyautogui.click(x+off_x, y+off_y)
    except:
        write_log_msg()
        ret=False

    return  ret

def  close_window(caption):
    ret = False
    # 根据类名及标题名查询句柄，
    try:
        hwnd_dfcf = win32gui.FindWindow(None, caption)
        if hwnd_dfcf>0:
            #time.sleep(1)
            win32api.SendMessage(hwnd_dfcf, win32con.WM_CLOSE, 0, 0)  # CLOSE WINDOWS
            ret = True
    except:
        #write_log_msg()
        pass

    return  ret

def  close_export_window():
    return  close_window(caption="导出对话框")

def  close_welcome():
    return close_window(caption="东方财富    [按Esc关闭本窗口]")

#自动登录gmzyj2590@1109
def login_gm():
    key_list = [['z', 1], ['y', 1], ['j', 1],['2', 1], ['5', 1], ['9', 1],['0', 1],\
                ['@', 1], ['1', 1], ['1', 1], ['0', 1],['9', 1]]
    try:
        pyautogui.click(610,465)
        press_keys(key_list)
        pyautogui.click(685,530)
        return True
    except:
        return  False

def openGM(file="C:\Program Files\掘金量化终端\goldminer3.exe"):
    prs = subprocess.Popen([file])
    #等待欢迎提示窗体，出现后关闭它
    # 找不到应用自行弹出的窗口，无法点击它
    waiting=6
    count=2
    time.sleep(8)
    while waiting>0:
        time.sleep(count)
        if login_gm():
            break

        waiting-=count

    time.sleep(15)


def openDFCF(files=dfcf_main_file):
    found=False
    for file in files:
        if file_exist(file):
            prs = subprocess.Popen([file])
            found=True
            break

    if not found:
        print("dfcf open error!!!")
        return

    #等待欢迎提示窗体，出现后关闭它，最长等待35秒
    # 找不到应用自行弹出的窗口，无法点击它
    waiting=60
    while  waiting>0:
        time.sleep(2)
        if close_welcome():
            break

        waiting-=3

    time.sleep(3)

    '''
    win32gui.ShowWindow(hwnd_dfcf, win32con.SW_MAXIMIZE)
    screenWidth, screenHeight = pyautogui.size()
    currentMouseX, currentMouseY = pyautogui.position()
    num_seconds = 1.2
    #  用num_seconds秒的时间把光标移动到(x, y)位置
    pyautogui.moveTo(screenWidth/2, screenHeight/2, duration=num_seconds)

    key_list=[['6',1],['0',1],['enter',1]]
    press_keys(key_list)
    time.sleep(3)
    
    '''

# 定义两个方法，来读写剪贴板，注意要和目标系统的编码方式相同
def get_text_from_clipboard():
    # 读取剪切板
    clipboard.OpenClipboard()
    d=b''
    i=0
    while True:
        try:
            i += 1
            d += clipboard.GetClipboardData(win32con.CF_TEXT)
            if d.__len__()<500 and i<5:
                #logger.debug('retry GetClipboardData')
                time.sleep(0.1)
            else:
                break
        except:
            logger.debug('open GetClipboardData')
            clipboard.OpenClipboard()

    clipboard.CloseClipboard()

    return d

def set_text_2_clipboard(aString=''):
    # 写入剪切板
    clipboard.OpenClipboard()
    clipboard.EmptyClipboard()
    clipboard.SetClipboardData(win32con.CF_TEXT, aString.encode(encoding='gbk'))
    clipboard.CloseClipboard()

# 按键序列处理
def press_keys(key_list):
    # 按键序列处理
    for key in key_list:
        for _ in range(key[1]):
            pyautogui.keyDown(key[0])
            time.sleep(0.005)
            pyautogui.keyUp(key[0])
            time.sleep(0.005)

#模拟人工操作的方式导出东方财富数据
def export_dfcf_data(click_points,key_list):
    ret=''

    try:
        set_text_2_clipboard()
        for point in click_points[:-1]:
            if point[0]=='delay':
                time.sleep(point[1])
            else:
                click_dfcf_menu(point[0],point[1])

        #popup menu
        pyautogui.rightClick(click_points[-1])

        #按键序列处理
        for key in key_list:
            for _ in range(key[1]):
                pyautogui.keyDown(key[0])
                #
                time.sleep(0.01)
                pyautogui.keyUp(key[0])
                time.sleep(0.01)

        close_export_window()

        #todo 二进制格式的文本待解析
        ret=get_text_from_clipboard()

    except:
        write_log_msg()
        pass
    
    return  ret

#获取字段内容并转成数字类型
def get_item_from_line(line,
    value_index=[],non_value_index=[],is_file=False):

    def get_file_item(next_tab,line):
        # 丢弃长度为0的字符串
        if next_tab > 0:
            item = line[1:next_tab-1]
            # 数字转换
            if len(non_value_index) > 0 and not item_index in non_value_index:
                if item.isdigit():
                    item = int(item)
                # 数字中有含单位：亿或万，应去掉
                elif is_float(item):
                    item = float(item)
                elif is_float(item[:-2]):
                    item = float(item[:-2])
                    tmp=item[-2:].decode('gbk')
                    if tmp=='万':
                        item=item*1e4
                    elif tmp=='亿':
                        item = item *1e8
                else:
                    item = 0.0

            return item

    def get_item(next_tab,line):
        # 丢弃长度为0的字符串
        if next_tab > 0:
            item = line[:next_tab]
            # 数字转换
            if len(non_value_index) > 0 and not item_index in non_value_index:
                if item.isdigit():
                    item = int(item)
                # 数字中有含单位：亿或万，应去掉
                elif is_float(item):
                    item = float(item)
                elif is_float(item[:-2]):
                    tmp = item[-2:].decode('gbk')
                    item = float(item[:-2])
                    if tmp=='万':
                        item=item*1e4
                    elif tmp=='亿':
                        item=item*1e8

                else:
                    item = 0.0
            else:
                item = item.decode('gbk')

            return item

    def is_float(str):
        try:
            float(str)
            return  True
        except:
            return  False

    data=[]
    try:
        item_index=0

        sep = b'\t'

        if len(value_index)>0:
            while len(line)>0:
                next_tab=line.index(sep)
                #丢弃长度为0的字符串
                if next_tab>0:
                    item=line[:next_tab]
                    #数字转换
                    if item_index in value_index:
                        if item.isdigit():
                            item=int(item)
                        #数字中有含单位：亿或万，应去掉
                        elif is_float(item) :
                            item=float(item)
                        elif is_float(item[:-2]):
                            if '万' in item:
                                item = float(item[:-2])/10000
                            else:
                                item = float(item[:-2])
                        else:
                            item=0.0
                    else:
                        item=item.decode('gbk')

                    data.append(item)
                    item_index += 1

                line=line[next_tab+1:]
        else:
            while len(line)>0:
                try:
                    next_tab=line.index(sep)
                except:#the last item
                    next_tab=len(line)-1

                item = get_item(next_tab, line)

                if not item is None:
                    data.append(item)
                    item_index += 1

                line=line[next_tab+1:]
    except:
        write_log_msg()
        pass

    return  data

'''
    dfcf导出的数据格式为文本格式，字段间用tab分隔，每条记录一行用（\n）分隔
    第一行为标题栏，记录各字段名，第二行起是具体内容
'''
def format_dfcf_export_text(export_text,values=[],
    non_values=[],pd_table=True,mul_lines=0,is_file=False,ret_queue=None):

    t0=time.time()
    index=0
    data_list=[]
    #get title

    sep =b'\n'

    try:
        next_end = index + export_text[index:].index(sep)
    except:
        return

    line = export_text[index:next_end]
    index = next_end + 1
    data_list.append(get_item_from_line(line,is_file=is_file))

    #确定数值类型的字段序号
    title=data_list[0]
    values_index=[title.index(value) for value in values]

    non_values_index =[]
    for value in non_values:
        if value in title:
            non_values_index.append(title.index(value))

    if len(values_index)>0:
        while index<len(export_text):
            next_end=index+export_text[index:].index(sep)
            line=export_text[index:next_end]
            index=next_end+1
            data_list.append(get_item_from_line(line,values_index,is_file=is_file))
    elif len(non_values_index)>0:
        while index<len(export_text):
            next_end=index+export_text[index:].index(sep)
            line=export_text[index:next_end]
            index=next_end+1

            #双行处理
            if mul_lines==1:
                next_end = index + export_text[index:].index(sep)
                line += export_text[index:next_end]
                index = next_end + 1

            data_list.append(get_item_from_line(line,'',non_values_index,is_file=is_file))

            # 确定数值类型的字段序号

    #logger.debug('format_dfcf_export_text time=%.2f' % (time.time() - t0))

    if pd_table==True:
        data = pd.DataFrame(data_list[1:])
        data.rename(columns={i: title[i] for i in range(len(title))}, inplace=True)
        if not ret_queue is None:
            ret_queue.put(data)
        return  data
    else:
        if not ret_queue is None:
            ret_queue.put(data_list)

        return data_list


'''--------------------基于东方财富的阶段统计数据处理--------------------------
1、增加字段：金额、量比、市盈率、市净率、流通市值、流通股本
下载历史数据：点击(810，90)进入：最近两年数据（604，261）、下载（811，528）、关闭（911，528）。
'''
def export_period_statics(index=-1,detect_buy=True,pe=[1,80]):
    #点击(810，90)进入：最近两年数据（604，261）、下载（811，528）、关闭（911，528）
    downlown_history_point=[[810,90],[604,261],[811,528],[911,528]]

    def export_allstock_period_statics():
        click_points=[
            [dfcf_top_menu_points,'沪深排行'],    #沪深排行
            [hs_rank_botton_menu, '沪深A股'],  #沪深A股
            [hs_rank_top_menu, '阶段统计'],
            [204, 150]   #呼出右键菜单
        ]
        key_list = [
            ['down', 7],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return  export_dfcf_data(click_points,key_list)

    def export_mystock_period_statics(index=0):

        if index >= len(mystock_list) or index<0:
            return

        click_points = [
            [dfcf_top_menu_points, '自选股'],
            [mystock_botton_menu, mystock_list[index]],
            [hs_rank_top_menu, '行情列表'],
            [204, 150]
        ]


        key_list = [
            ['down', 8],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return  export_dfcf_data(click_points,key_list)

    # 阶段统计
    # 自定义1至5日、10日、20日、30日成交量（换手率）、成交金额、振幅、复权后的均价，
    # 自行计算波动率：寻找突破者
    def read_real_period_static(all_stock=True, mystock=0):
        if all_stock:
            real_status = export_allstock_period_statics()  # export_mystock_real_status()  #      export_real_capflow()
        else:
            real_status = export_mystock_period_statics(index=mystock)  # export_real_capflow()

        non_values = [u'代码', u'名称']
        period_static = format_dfcf_export_text(real_status, '', non_values)

        # 统一排列字段名
        dates = ['1', '2', '3', '4', '5', '10', '20', '30']
        items = [u'日换手率%', u'日成交额', u'日振幅', u'日均价']

        cols = non_values
        for item in items:
            for date in dates:
                cols.append(date + item)

        period_static = period_static[cols]
        print(period_static[:2])

        # 按字段进行排序
        return period_static

    # 基于 f1=涨幅%  f5=5日涨幅%	f10=10日涨幅%	    f20=20日涨幅%	 判断当前趋势
    # 基于最近10日计算趋势，将来改为基于20日涨跌计算趋势或权重
    # 0 趋势不明朗，波动中，》100 升，<-100跌
    def detect_trend(period_statics):

        for i in range(len(period_statics)):
            if    period_statics.loc[i,'涨幅%']>0 \
              and period_statics.loc[i,'5日涨幅%']>-3 \
              and period_statics.loc[i,'10日涨幅%']>0:
                period_statics.loc[i, 'trend']=100+\
                     period_statics.loc[i,'涨幅%']\
                    +period_statics.loc[i,'5日涨幅%']\
                    +period_statics.loc[i, '5日涨幅%']
            elif period_statics.loc[i,'涨幅%']<0 \
              and period_statics.loc[i,'5日涨幅%']<2 \
              and period_statics.loc[i,'10日涨幅%']<0:
                period_statics.loc[i, 'trend'] =-100+ \
                    period_statics.loc[i, '涨幅%'] \
                    + period_statics.loc[i, '5日涨幅%'] \
                    + period_statics.loc[i, '5日涨幅%']
            else:
                period_statics.loc[i, 'trend']=0

        return period_statics

    #  main start
    def start():
        pass

    if index==-1:
        #all stock
        period_statics=export_allstock_period_statics()
    else:
        period_statics=export_mystock_period_statics(index=index)

    '''  主要字段
    代码	名称	最新	总手	金额 量比 市盈率	市净率	流通市值	流通股本	
    涨幅%  5日涨幅%	10日涨幅%	    20日涨幅%	
    换手%  5日换手率%	10日换手率%	20日换手率%	
    5日跑赢大盘天数	10日跑赢大盘天数	20日跑赢大盘天数	
    '''

    non_values = [u'代码', u'名称']

    period_statics = format_dfcf_export_text(period_statics, '', non_values)

    #剔除高风险、低成交额、低换手率标的
    period_statics = period_statics[period_statics['市盈率'] > pe[0]]
    period_statics = period_statics[period_statics['市盈率'] < pe[1]]
    period_statics = period_statics[period_statics['换手%'] > 0.8]
    period_statics = period_statics[period_statics['金额'] > 0.4]  #成交额4000万元以上

    #回避最近10日涨幅超过30%的大涨标的,避免追高
    period_statics = period_statics[period_statics['10日涨幅%'] <30]

    period_statics=period_statics.reset_index()
    period_statics = detect_trend(period_statics)

    if detect_buy:
        #detect buy
        period_statics=period_statics[period_statics['trend']>0].sort_values(
            by='trend',ascending=False)
        pass
    else:
        #detect sell
        period_statics = period_statics[period_statics['trend'] <0].sort_values(
            by='trend',ascending=False)
        pass

    return  period_statics

#实时加仓数据  增仓排名,每个交易日计算一次即可，实时加仓信息通过实时资金流计算
def read_real_add_holding(all_stock=True, index=-1, detect_buy=True):

    def export_allstock_real_add_holding(botton_menu='沪深A股'):
        click_points=[
            [dfcf_top_menu_points,'沪深排行'],    #沪深排行
            [hs_rank_botton_menu, botton_menu],
            [hs_rank_top_menu, '增仓排名'],   #增仓排名
            [204, 312]   #呼出右键菜单
        ]
        key_list = [
            ['down', 7],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return  export_dfcf_data(click_points,key_list)

    def export_mystock_real_add_holding(index=0):
        if index >= len(mystock_list) or index<0:
            return

        click_points = [
            [dfcf_top_menu_points, '自选股'],
            [mystock_botton_menu, mystock_list[index]],
            [hs_rank_top_menu, '增仓排名'],
            [204, 150]
        ]

        key_list = [
            ['down', 12],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return  export_dfcf_data(click_points,key_list)

    #
    if all_stock:
        real_status = export_allstock_real_add_holding()  # export_mystock_real_status()  #      export_real_capflow()
    else:
        real_status = export_mystock_real_add_holding(index=index)  # export_real_capflow()

    data_item = [
        u'今日增仓占比', u'今日排名', u'今日排名变化', u'今日涨幅%',
        u'3日增仓占比', u'3日排名', u'3日排名变化', u'3日涨幅%',
        u'5日增仓占比', u'5日排名', u'5日排名变化', u'5日涨幅%',
        u'10日增仓占比', u'10日排名', u'10日排名变化', u'10日涨幅%'
    ]
    # 各数据字段打分权重表，与data_item对应
    rank_coff = [2, -0.00, 0.01, 2,
                 2, -0.00, 0.02, 2,
                 2, -0.00, 0.03, 2,
                 2, -0.00, 0.04, 2
                 ]

    values = [u'序', u'代码', u'最新', u'涨幅%'] + data_item

    display_values = [u'代码', u'今日增仓占比', '3日增仓占比', '5日增仓占比', '10日增仓占比',
                      u'今日排名变化', u'3日排名变化', u'5日排名变化', u'10日排名变化',
                      u'今日涨幅%', u'3日涨幅%', u'5日涨幅%', u'10日涨幅%'
                      ]

    non_values = [u'代码', u'名称', u' 所属行业']
    real_status = format_dfcf_export_text(real_status, '', non_values)

    if detect_buy:  # detect buy point
        real_status = real_status[real_status['涨幅%'] > -3.0]
        real_status = real_status[real_status['涨幅%'] < 6.0]
        real_status = real_status[real_status['今日增仓占比'] > 6.0]
        real_status = real_status[real_status['今日增仓占比'] > real_status['3日增仓占比']]
        real_status = real_status[real_status['3日增仓占比'] > real_status['5日增仓占比']]
        real_status = real_status[real_status['今日排名变化'] > -200]
        real_status = real_status.reset_index()
        # todo 基于增仓和涨幅的排名：当日、3日、5日和10日不同权重，其结果不一样，待研究
        real_status['rank'] = 0

        for i in range(len(real_status)):
            for item in range(len(data_item)):
                real_status.loc[i, 'rank'] += real_status.loc[i, data_item[item]] * rank_coff[item]

        sort_vols = ['rank', '代码']
        display_values += ['rank']
        real_status = real_status.sort_values(sort_vols, ascending=False)[display_values]
    else:  # detect sell point
        real_status = real_status[real_status['涨幅%'] < 5.0]
        real_status = real_status[real_status['今日增仓占比'] < -2]
        real_status = real_status[real_status['今日排名变化'] < -100]
        real_status = real_status.reset_index()
        # todo 基于增仓和涨幅的排名：当日、3日、5日和10日不同权重，其结果不一样，待研究
        real_status['rank'] = 0

        for i in range(len(real_status)):
            for item in range(len(data_item)):
                real_status.loc[i, 'rank'] += real_status.loc[i, data_item[item]] * rank_coff[item]

        sort_vols = ['rank', '代码']
        display_values += ['rank']
        real_status = real_status.sort_values(sort_vols, ascending=True)[display_values]

    # 使用datetime.now()
    now = gmTools.get_last_trade_datetime()
    int_time = now.hour * 100 + now.minute
    real_status['time'] = int_time

    return real_status



'''
#模拟人工操作的方式导出all实时资金流
todo 模拟按键序列是影响效率的根本原因，最后能直接进入数据导出模式：
序	代码	名称	最新	涨幅%	主力净流入	集合竞价	超大单流入	超大单流出	超大单净额	超大单净占比%	大单流入	大单流出	大单净额	大单净占比%	中单流入	中单流出	中单净额	中单净占比%	小单流入	小单流出	小单净额	小单净占比%	
1	002460	赣锋锂业	72.41	3.47	1.85亿		794		4.69亿		-2.93亿		1.76亿		7.35		8.08亿		-8.00亿		851万		0.36		7.04亿		-8.03亿		-9936万		-4.15		4.05亿		-4.90亿		-8516万		-3.56		
2	600271	航天信息	26.32	4.49	7526万		141		1.18亿		-5591万		6212万		10.06		1.86亿		-1.73亿		1314万		2.13		1.73亿		-2.08亿		-3464万		-5.61		1.09亿		-1.50亿		-4062万		-6.58

代码    	集合竞价	超大单流入	超大单流出	大单流入	大单流出	中单流入	中单流出	小单流入	小单流出	
002460	4225万	5.40亿		-4.01亿		9.63亿	-9.86亿	8.93亿	-9.61亿	5.32亿	-5.79亿		
600271	141万	1.73亿		-6972万		2.36亿	-2.31亿	2.33亿	-2.85亿	1.53亿	-2.09亿
    当日600271 集合竞价阶段总成交141万、555手，全部流入单成交额与流出单成交额相等，
全部流入单成交额加集合竞价成交额等于当日总成交额。
  深圳股票的集合竞价的金额与分钟图的金额不一致,以分钟图的数据为准。

    结合L2大户室的信息：顶级挂单，拖拉机单，强势狙击和主力踪迹使用，基于资金流的短线操作
'''
last_capflow=None
main_capflow=None  #主力单数据队列

#资金流类
class capflow_class:

    def __init__(self):
        self._capflow=None        #当日实时资金流信息
        self._addholding=[]     #当日增减仓信息
        self._dde=[]            #当日dde信息
        self._propter=[]        #股票基本信息  流通盘、总盘、市盈率等基础参数
        self._last_cacl_eob=None
        self._big_buy=[]
        self._big_sell=[]
        self._stocks=[]
        self._lock=Lock()

        #大单分析参数   当前有效记录数，分析起点记录数，主力净流入前xx项
        self._item_count=0
        self._week=15
        self._big_buy_count=200

    def add_flow(self,data,file_path,is_file=False):
        self._lock.acquire()

        self._last_cacl_eob = data.loc[0, 'eob']
        self._item_count += 1

        if self._capflow is None:
            self._capflow = data.copy()
            if is_file:
                #get the first time stocks from file
                self._stocks = data[data['eob']==self._last_cacl_eob]['代码'].values.tolist()
            else:
                self._stocks =data['代码'].values.tolist()
        else:
            self._capflow = pd.concat([self._capflow , data], ignore_index=True)
            self._capflow=self._capflow.sort_values(by=['代码','eob'])

        if not is_file:
            file_path = "e:\\data\\%s-cap-%s.txt" % (file_path, datetime.datetime.now().date())
            write_text_file(file_path, msg=data.values.tolist(), title=data.columns)

        cur_data=self._capflow.copy()
        self._lock.release()

        self.detect_big_bs(data=data,cur_data=cur_data,is_file=is_file)
        self.cacl_dde()
        self.cacl_dde()
        self.cacl_flow()


    #资金流计算
    def cacl_flow(self):
        pass

    # 实时增仓计算
    def cacl_addholding(self):
        pass

    # 实时DDE计算
    def cacl_dde(self):
        pass

    #大单买卖检测  很好资源，需单独安排进程进行处理
    def detect_big_bs(self,data,cur_data,is_file=False):

        if self._item_count<self._week:
            return

        # 基于成交额10周期均值进行检测，按最近一周期的主力净流入成交额与均值比进行逆序、顺序排列
        # 同步考虑价格因素
        t0 = time.time()
        bs = []
        cols = ['代码', 'eob', '最新', '涨幅%', '主力净流入']
        cur_eob=data.loc[0,'eob']
        data = data[data['主力净流入'] > 0]
        data=data.sort_values(by='主力净流入',ascending=False)
        data = data[data['涨幅%']<7.0][:self._big_buy_count]
        to_be_analysed=data['代码'].values.tolist()

        tmp='\n'
        for stock in to_be_analysed:
            try:
                main_data = cur_data[cur_data['代码'] == stock][cols].reset_index()
                datalen=len(main_data)

                if  datalen< self._week+5:
                    continue

                if is_file:
                    start=self._week+5
                else:
                    start = datalen-1

                delta =main_data['主力净流入']- main_data['主力净流入'].shift(1)
                main_data['delta'] =delta

                if False:#is_file:
                    from pylab import plt
                    plt.plot(main_data['delta'],label='delta')
                    ma = delta.rolling(window=self._week, center=False).mean()
                    plt.plot(ma,label='ma')
                    plt.legend(loc='upper center', shadow=True, fontsize='x-large')
                    plt.show()

                for index in range(start,datalen):
                    ma = delta[index - self._week-1:index].rolling(
                        window=self._week,
                        center=False
                    ).mean().values.tolist()[-1]

                    if (ma>0.01 or ma<-0.01):
                        new_delta=delta[index-self._week-1:index].values.tolist()[-1]
                        ratio=abs(int(new_delta/ma))
                        if ratio>10:
                            bs.append([cur_eob, stock,ratio])
                            tmp+=('[eob=%d] stock=%s,ratio=%2d,price:[%.2f],delta=%.2f\n' %(
                                cur_eob,
                                stock,ratio,
                                main_data.loc[index, '涨幅%'],
                                new_delta)
                            )
            except:
                write_log_msg()

        logger.info("%s detect big bs ,time=%.2f\n\n"%(tmp,time.time()-t0))

def process_real_capflow(real_capflow,pipe,filepath):


    while True:
        try:
            real_status=pipe.recv()
            real_capflow.add_flow(real_status,file_path=filepath)

            #todo cacl buy sell point

        except:
            write_log_msg()

            # 从文件读取数据  效率很低，用分钟级别K线的资金流可能好用

# 不能在进程启动多进程，否则出现死机
def read_cap_from_file(real_capflow,
   file_paths=['e:\\data\\沪深A股-cap-2018-05-22.txt']):
    for file_path in file_paths:
        try:
            # get data from capflow file
            f = open(file_path, "rb")
            real_status = f.read()
            f.close()

            # 转成类似dfcf剪辑版内容的模式
            if True:
                count = 500000 * 70
                if len(real_status) > count:
                    real_status = real_status[:count + real_status[count:].index(b'\n') + 1]

            #real_status = real_status.replace(b',', b'\t')
            non_values = [u'代码', u'名称']

            # '''
            # 返回列表，自行处理数据,values='',non_values=''
            cpus = cpu_count()
            datalen = int(len(real_status) / cpus)

            args = []
            last_index = 0
            index = real_status.index(b'\n') + 1
            title = real_status[:index]
            real_status = real_status[index:]

            for i in range(cpus - 1):
                stop = last_index + datalen
                index = stop + real_status[stop:].index(b'\n') + 1

                args.append(title + real_status[last_index:index])
                last_index = index

            args.append(title + real_status[last_index:])
            freeze_support()
            tasks = []
            ret_queue = Queue()
            #cpus=1
            #args=[title+real_status]
            for i in range(cpus):
                p = Process(target=format_dfcf_export_text,
                            args=(args[i], [], non_values, True, 0, False, ret_queue))
                tasks.append(p)

            for task in tasks:
                task.start()

            real_status = []
            for _ in tasks:
                real_status.append(ret_queue.get())

            real_status = pd.concat(real_status)
            real_status = real_status.reset_index()

            real_capflow.add_flow(real_status, '', is_file=True)

        except:
            write_log_msg()



def read_real_capflow(index,pipe,pipe1,pipe2,is_file=False,debug=False,
        file_paths=['e:\\data\\沪深A股-cap-2018-05-24.txt'] ):

    global last_capflow,main_capflow,capflow,caplock

    # 模拟人工操作的方式导出all实时资金流
    def export_allstock_real_capflow(is_first=True):
        #todo 模拟按键序列是影响效率的根本原因，最后能直接进入数据导出模式：
        if is_first:
            click_points = [
                [dfcf_top_menu_points, '沪深排行'],
                [hs_rank_top_menu, '资金流向'],
                [hs_rank_botton_menu, '沪深A股'],
                ['delay', 1],
                [273, 150]
            ]
        else:
            click_points = [
                [273, 150]
            ]

        key_list = [
            ['down', 7],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    def export_mystock_real_capflow(index=0):
        if index >= len(mystock_list) or index < 0:
            return

        click_points = [
            [dfcf_top_menu_points, '自选股'],
            [mystock_botton_menu, mystock_list[index]],
            [hs_rank_top_menu, '资金流向'],
            [204, 150]
        ]
        key_list = [
            ['down', 12],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    def start():
        pass

    # --------------------------------------------------------------------------------

    if  debug:
        real_capflow = capflow_class()

    title = ['代码', 'eob', '最新', '涨幅%', '主力净流入',
             '超大单流入', '超大单流出',# '超大单净额', '超大单净占比%',
             '大单流入', '大单流出',# '大单净额', '大单净占比%',
             '中单流入', '中单流出',# '中单净额', '中单净占比%',
             '小单流入', '小单流出' #, '小单净额', '小单净占比%'
             ]

    #real mode
    load_dfcf()
    trade_star=93000
    trade_stop=150100
    relax=[113000,125900]
    non_values=['代码','名称']
    first_time=True

    proc_index=-1
    while not is_stop:
        try:
            t0=time.time()
            eob=datetime.datetime.now()
            eob = eob.hour * 10000 + eob.minute * 100 + eob.second
            #print(datetime.datetime.now())
            if (eob>relax[0] and eob<relax[1]) or eob<trade_star-1 :
                logger.debug("waiting to star trade")
                time.sleep(60)
                first_time=True
                continue

            if  eob>trade_stop :
                logger.debug("trade stopping")
                break

            if index==-1:
                real_status =export_allstock_real_capflow(is_first=first_time)
                file_path='沪深A股'
            else:
                file_path=mystock_list[index]
                real_status = export_mystock_real_capflow(index=index)

            first_time = False
            # 返回列表，自行处理数据,values='',non_values=''
            real_status = format_dfcf_export_text(
                export_text=real_status,
                values=[], non_values=non_values, pd_table=True, is_file=False
            )

            real_status = real_status[real_status['主力净流入'] !=0]

            eob = datetime.datetime.now()
            eob = eob.hour * 10000 + eob.minute * 100 + eob.second

            real_status['eob'] = eob
            real_status = real_status[title].reset_index()

            # check_big_trade(old_cap=last_capflow,new_flow=real_status)
            last_capflow = real_status.copy()

            if not debug:
                proc_index = proc_index + 1
                tmp=("\n[%d]send  real_status! %.2f\n" % (proc_index,time.time() - t0))
                if proc_index==0:
                    pipe.send(real_status)
                elif proc_index==1:
                    pipe1.send(real_status)
                else:
                    pipe2.send(real_status)
                    proc_index=-1



            else:
                real_capflow.add_flow(real_status,file_path=file_path)

            logger.debug("%sread real cap end! %.2f\n"%(tmp,time.time()-t0))

        except:
            write_log_msg()
            show_dfcf()
            first_time = True

    print("read_real_capflow process end!")

#每个交易日开始前或闭市后计算一次即可，实时的DDE数据可通过实时资金流自行计算
def read_real_DDE(index=-1):
    # 模拟人工操作的方式导出all实时资金流
    def export_allstock_DDE():
        click_points = [
            [dfcf_top_menu_points, '沪深排行'],
            [hs_rank_top_menu, 'DDE决策'],
            [hs_rank_botton_menu, '沪深A股'],
            [273, 307]
        ]
        key_list = [
            ['down', 7],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    def export_mystock_DDE(index=0):
        if index >= len(mystock_list) or index < 0:
            return

        click_points = [
            [dfcf_top_menu_points, '自选股'],
            [mystock_botton_menu, mystock_list[index]],
            [hs_rank_top_menu, 'DDE决策'],
            [204, 150]
        ]
        key_list = [
            ['down', 12],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    #--------------------------------------------------
    if index==-1:
        real_status =export_allstock_DDE()
    else:
        real_status = export_mystock_DDE(index=index)

    non_values = [u'代码', u'名称']

    #返回列表，自行处理数据,values='',non_values=''
    real_status = format_dfcf_export_text(
        export_text=real_status,
        values='',non_values=non_values,pd_table=False
    )

    return real_status

'''
获取各种挂单信息太费时间，不如基于资金流直接计算买卖强度
L2Room_top_menu=[
    
    ['顶级挂单',127,62],顶级挂单是指委托挂单在9000手以上的挂单，一般都为大主力所为，
    通过跟踪这些挂单的委托买入、委托卖出，以及撤销委托的行为从而发现大主力的踪迹以及意图。
    
    ['拖拉机单',196,62],拖拉机单是指有多笔相同数目的委买和委卖挂单，一般是同一主力所
    为。主力可以将大单拆成数笔同样的小单来隐藏自己的踪迹，也可以通过连续相同数目的大单
    向表明自己态度。用户可以跟踪这些拖拉机单来发现主力和判断主力的方向。
    
    ['强势狙击',266,62],强势狙击功能是基于交易人气量、股性活跃度和历史波动率等因素，
    分析测算推动股价上升的各种潜在力量而研发的一套算法模型，力求辅助用户挖掘市场上短线
    有望呈现强势的个股，并通过实时榜单形式发布。
    
    ['主力踪迹',329,62], 主力踪迹是通过LEVEL-2数据跟踪, 主要从顶级大单买入、拖拉机
    单买入以及DDX连续飘红中，对这三个LEVEL-2的数据分析，优选出有主力介入的股票。
    仅记录最近3个交易日数据，用途似乎不大，可自行管理。
    
    ['L2核心内参',400,62],
    ['资金全景',476,62],针对全市场的资金流
    ['DDE全景',546,62]，最对全市场的DDE数据
    数据要做分析，剔除相同的内容
    1、顶级挂单 保留的数据：
        代码,买卖方向,挂单时间,挂单价格,最新挂单明细,挂单总额,买入次数,卖出次数
    2、拖拉机单 保留的数据：
        代码,买卖方向,挂单时间,挂单价格,最新挂单明细,挂单总数,挂单总额,买入次数,卖出次数 
    3、强势狙击 保留的数据：   
        代码，强势力度，入榜时间，5日入榜，3日涨幅 
'''
qsjj_list=None
djgd_list=None
tljd_list=None

def read_real_L2Room(top_menu='强势狙击',is_test=False):
    global qsjj_list,djgd_list,tljd_list

    def test(top_menu='强势狙击'):
        global qsjj_list, djgd_list, tljd_list

        qsjj_list = [
            ['000017', '300', '11:27:03', '0次', 6.47],
            ['000020', '300', '11:16:53', '0次', 4.55]
        ]

        djgd_list = [
            ['000001', '顶级买单', '11:15', 11.07, '1万手', 1107.0, 3, 2],
            ['000011', '顶级买单', '10:07', 14.77, '1万手', 1477.0, 1, 0],
            ['000078', '顶级卖单', '10:48', 6.23, '9068手', 565.0, 0, 1],
            ['000413', '顶级卖单', '10:11', 8.55, '1万手', 855.0, 12, 1]
        ]
        tljd_list = [
            ['000002', '拖拉机卖', '11:08', 27.76, '100手*3', '3.00万', 83.3, 0, 1],
            ['000703', '拖拉机买', '09:50', 23.8, '113手*3', '3.39万', 80.7, 1, 0],
            ['002025', '拖拉机卖', '10:13', 24.73, '172手*3', '5.16万', 128.0, 0, 1],
            ['002027', '拖拉机买', '09:54', 12.14, '200手*3', '6.00万', 72.8, 2, 0],
            ['002067', '拖拉机卖', '11:10', 4.75, '500手*3', '15.0万', 71.3, 0, 1]
        ]

        if top_menu == '强势狙击':
            real_status = [
                ['000017', '300', '11:27:03', '0次', 6.47],
                ['000020', '300', '11:16:53', '0次', 4.55],
                ['000413', '300', '10:03:40', '0次', 4.68],
                ['000425', '300', '09:36:13', '0次', 2.76],
                ['000586', '500', '11:04:42', '0次', 8.54],
                ['002009', '300', '10:33:09', '0次', 1.51],
                ['002023', '300', '11:01:37', '0次', 4.18],
                ['002044', '300', '10:17:54', '0次', 1.74],
                ['002088', '300', '10:40:18', '0次', 2.31],
                ['002156', '300', '09:25:00', '0次', -0.25],
                ['002180', '310', '09:36:13', '0次', 3.54],
                ['002258', '301', '10:28:04', '0次', 5.36],
            ]
            qsjj_list =check_diff(old_list=qsjj_list, new_list=real_status)
        elif top_menu == '顶级挂单':
            real_status=[
                ['000078', '顶级卖单', '10:48', 6.23, '9068手', 565.0, 0, 1],
                ['000413', '顶级卖单', '10:11', 8.55, '1万手', 855.0, 12, 1],
                ['000425', '顶级买单', '11:01', 4.33, '1万手', 433.0, 1, 3],
                ['000528', '顶级买单', '10:53', 10.51, '9999手', 1051.0, 12, 0],
                ['000543', '顶级卖单', '10:14', 4.65, '1万手', 465.0, 0, 1],
                ['000592', '顶级卖单', '09:22', 4.11, '1万手', 411.0, 0, 2],
                ['000691', '顶级卖单', '10:06', 6.09, '1万手', 609.0, 0, 1],
                ['000718', '顶级卖单', '09:15', 4.1, '1万手', 410.0, 0, 2],
                ['000725', '顶级卖单', '11:27', 4.41, '1万手', 441.0, 30, 57],
                ['000735', '顶级买单', '11:18', 11.14, '1万手', 1114.0, 2, 0],
                ['000777', '顶级卖单', '10:12', 13.69, '9554手', 1308.0, 0, 1],
                ['000795', '顶级买单', '11:00', 5.45, '9300手', 507.0, 1, 0],
                ['000937', '顶级卖单', '10:11', 4.79, '9067手', 434.0, 0, 1],
                ['000975', '顶级卖单', '11:04', 16.38, '1万手', 1638.0, 0, 1],
                ['002023', '顶级买单', '10:52', 12.5, '9999手', 1250.0, 1, 0],
                ['002160', '顶级卖单', '10:09', 6.1, '9125手', 557.0, 0, 1],
                ['002178', '顶级买单', '10:02', 6.6, '9900手', 653.0, 1, 0],
                ['002194', '顶级卖单', '09:54', 5.62, '9100手', 511.0, 0, 1]
            ]
            djgd_list=check_diff(old_list=djgd_list, new_list=real_status)
        elif top_menu == '拖拉机单':
            real_status=[
                ['002027', '拖拉机买', '09:54', 12.14, '200手*3', '6.00万', 72.8, 2, 0],
                ['002067', '拖拉机卖', '11:10', 4.75, '500手*3', '15.0万', 71.3, 0, 1],
                ['002185', '拖拉机买', '10:01', 6.78, '500手*3', '15.0万', 102.0, 1, 0],
                ['002463', '拖拉机买', '10:49', 4.4, '1万手*4', '400万', 1760.0, 2, 0],
                ['002622', '拖拉机卖', '09:38', 7.63, '500手*3', '15.0万', 114.0, 0, 1],
                ['002772', '拖拉机买', '10:47', 9.91, '100手*7', '7.00万', 69.4, 1, 0],
                ['300137', '拖拉机卖', '09:42', 20.05, '100手*4', '4.00万', 80.2, 0, 1],
                ['300433', '拖拉机买', '10:33', 22.03, '200手*3', '6.00万', 132.0, 1, 0],
                ['300606', '拖拉机买', '10:02', 28.54, '200手*3', '6.00万', 171.0, 1, 0],
                ['600059', '拖拉机卖', '10:32', 8.66, '299手*3', '8.97万', 77.7, 0, 1],
                ['600810', '拖拉机卖', '09:54', 12.1, '100手*7', '7.00万', 84.7, 0, 1],
                ['600887', '拖拉机卖', '09:49', 26.98, '158手*3', '4.74万', 128.0, 0, 1],
                ['601699', '拖拉机卖', '11:13', 10.42, '123手*8', '9.84万', 103.0, 0, 1]
            ]
            tljd_list =check_diff(old_list=tljd_list, new_list=real_status)


    def check_diff(new_list,old_list,title=''):
         if old_list is None:
             file_path = 'e:\\data\\%s-%s.txt' % (top_menu, datetime.datetime.now().date())
             write_text_file(file_path=file_path, msg=new_list, title=title)
             return new_list

         keep=[]
         old_code=[item[0] for item in old_list]

         try:
             for row in new_list:   # 获取每行的index、row
                 row_exist=False

                 if  row[0] in old_code:
                     start = 0

                     while not row_exist:
                        if row[0] in old_code[start:]:
                            old_index=start+old_code[start:].index(row[0])     #todo 统一代码多项记录管理
                            if row==old_list[old_index]:
                                row_exist=True
                                break

                            if start>0 and old_index==0:
                                break
                            else:
                                if start==0 and old_index==0:
                                    start=1
                                else:
                                    start=old_index+1
                        else:
                            break

                 if  not row_exist:
                     keep.append(row)
                     old_list.append(row)
                     #todo new code process

         except:
            write_log_msg()

         if len(keep)>0:
             new_code = [item[0] for item in keep]
             print('\n')
             print(top_menu)
             print('new code')
             print(new_code)
             file_path='e:\\data\\%s-%s.txt'%(top_menu,datetime.datetime.now().date())
             write_text_file(file_path=file_path,msg= keep,title=title)
             #send_mail(top_menu,str(keep))

         else:
             new_code=[]

         return old_list,new_code


    if is_test:
        test(top_menu=top_menu)
        return

    # 强势狙击
    # 顶级挂单
    # 拖拉机单

    if top_menu=='强势狙击':
        delay=4
        mul_lines=0
    else:
        delay=0.05
        mul_lines = 1

    click_points = [
        [dfcf_top_menu_points, '全景图'],
        [dfcf_left_menu_points, 'L2大户室'],
        [L2Room_top_menu, top_menu],
        ['delay',delay],
        [273, 150]
    ]
    key_list = [
        ['down', 7],
        ['right', 1],
        ['enter', 1],
        ['tab', 4],
        ['up', 3],
        ['tab', 1],
        ['enter', 2]
    ]

    try:

        real_status= export_dfcf_data(click_points, key_list)

        #--------------------------------------------------
        non_values = [u'代码', u'名称', u'买卖方向', u'挂单时间', u'最新挂单明细', u'挂单总数',
                      u' 所属行业',u'强势力度',u'入榜时间', u'5日入榜']

        #返回列表，自行处理数据,values='',non_values=''
        real_status = format_dfcf_export_text(
            export_text=real_status,mul_lines=mul_lines,
            values='',non_values=non_values,pd_table=True).sort_values(by='代码',ascending=True)
        real_status=real_status.reset_index()

        if top_menu == '强势狙击':
            col = ['代码', '强势力度', '入榜时间', '5日入榜', '3日涨幅%']
            qsjj_list,new_code =check_diff(old_list=qsjj_list, new_list=real_status[col].values.tolist(),title=col)
            print(top_menu,new_code)
        elif top_menu == '顶级挂单':
            col = ['代码', '买卖方向', '挂单时间', '挂单价格', '最新挂单明细', '挂单总额', '买入次数', '卖出次数']
            djgd_list,new_code=check_diff(old_list=djgd_list, new_list=real_status[col].values.tolist(),title=col)
            print(top_menu, new_code)
        elif top_menu == '拖拉机单':
            col = ['代码', '买卖方向', '挂单时间', '挂单价格', '最新挂单明细', '挂单总数', '挂单总额', '买入次数', '卖出次数']
            tljd_list,new_code =check_diff(old_list=tljd_list, new_list=real_status[col].values.tolist(),title=col)
            print(top_menu, new_code)

    except:
        pass

#当前行情列表,含大量有用信息
#初始	代码	名称	最新	涨幅%	涨跌	总手	现手	买入价	卖出价	涨速%	换手%	金额	市盈率	 所属行业	最高	最低	开盘	昨收	振幅%	量比	委比%	委差	均价	内盘	外盘	内外比	买一量	卖一量	市净率	总股本	总市值	流通股本	流通市值	3日涨幅%	6日涨幅%	3日换手%	6日换手%
#1	600017	日照港	3.95	-1.99	-0.08	22.9万	100	3.94	3.95	0.00	0.75	9116万	17.79	 港口水运	4.01	3.93	3.99	4.03	1.99	0.76	48.20	2.16万	3.97	17.9万	5.02万	3.57	8438	29	1.12	30.8亿	121亿	30.8亿		121亿		-0.75		1.28		4.29		6.89
#2	000818	航锦科技	14.06	-3.03	-0.44	13.1万	2	14.06	14.07	0.07	1.90	1.87亿	18.98	 化工行业	14.60	14.02	14.60	14.50	4.00	0.92	12.63	263	14.21	8.96万	4.18万	2.14	36	24	3.71	6.92亿	97.3亿	6.90亿		97.1亿		-5.70		0.21		6.62		14.89
# 初始	代码	名称	最新	涨幅%	涨跌	总手	现手	买入价	卖出价	涨速%	换手%	金额	市盈率
#所属行业	最高	最低	开盘	昨收	振幅%	量比	委比%	委差	均价	内盘	外盘	内外比	买一量	卖一量
#市净率	总股本	总市值	流通股本	流通市值	3日涨幅%	6日涨幅%	3日换手%	6日换手%
#根据3日、6日涨幅可判断最近6日整体趋势，3日与（6日-3日）同号趋势相等，异号反转，6日值表明了涨、跌与维持
#换手率表明交投活跃程度，量比表明当日交易量的大小
def read_real_status(all_stock=True,mystock_index=0):
    '''
       获取自选股实时状态
       自选股序列可扩充，目前支持7种
     初始	代码	名称	最新	涨幅%	涨跌	总手	现手	买入价	卖出价	涨速%	换手%	金额	市盈率	 所属行业	最高	最低	开盘	昨收	振幅%	量比	委比%	委差	均价	内盘	外盘	内外比	买一量	卖一量	市净率	总股本	总市值	流通股本	流通市值	3日涨幅%	6日涨幅%	3日换手%	6日换手%
    1	600017	日照港	3.95	-1.99	-0.08	22.9万	100	3.94	3.95	0.00	0.75	9116万	17.79	 港口水运	4.01	3.93	3.99	4.03	1.99	0.76	48.20	2.16万	3.97	17.9万	5.02万	3.57	8438	29	1.12	30.8亿	121亿	30.8亿		121亿		-0.75		1.28		4.29		6.89
    2	000818	航锦科技	14.06	-3.03	-0.44	13.1万	2	14.06	14.07	0.07	1.90	1.87亿	18.98	 化工行业	14.60	14.02	14.60	14.50	4.00	0.92	12.63	263	14.21	8.96万	4.18万	2.14	36	24	3.71	6.92亿	97.3亿	6.90亿		97.1亿		-5.70		0.21		6.62		14.89
    3	300017	网宿科技	13.54	0.97	0.13	43.3万	110	13.54	13.55	0.00	2.69	5.87亿	37.85	 软件服务	13.71	13.37	13.48	13.41	2.54	0.96	29.80	1286	13.56	19.1万	24.2万	0.79	280	7	4.03	24.3亿	329亿	16.1亿		218亿		-1.17		1.35		9.20		20.24
    '''

    def export_mystock_real_status(index=0):

        if index >= len(mystock_list) or index < 0:
            return

        click_points = [
            [dfcf_top_menu_points, '自选股'],
            [mystock_botton_menu, mystock_list[index]],
            [hs_rank_top_menu, '行情列表'],
            [204, 150]
        ]

        key_list = [
            ['down', 12],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    def export_allstock_real_status():
        click_points = [
            [dfcf_top_menu_points, '沪深排行'],  # 沪深排行
            [hs_rank_botton_menu, '沪深A股'],  # 沪深A股
            [hs_rank_top_menu, '行情列表'],
            [204, 312]  # 呼出右键菜单
        ]
        key_list = [
            ['down', 7],
            ['right', 1],
            ['enter', 1],
            ['tab', 4],
            ['up', 3],
            ['tab', 1],
            ['enter', 2]
        ]

        return export_dfcf_data(click_points, key_list)

    if all_stock:
        real_status = export_allstock_real_status()
        values = u'序'
    else:
        real_status = export_mystock_real_status(mystock_index)
        values = u'初始'

    values=[values,u'代码', u'最新', u'涨幅%', u'涨跌', u'总手',
                   u'现手', u'买入价', u'卖出价', u'涨速%', u'换手%',
                   u'金额', u'市盈率', u'市净率',u'最高', u'最低', u'开盘',
            u'总股本',u'总市值',u'流通股本',u'流通市值',u'3日涨幅%',u'6日涨幅%',u'3日换手%',u'6日换手%',
                   u'昨收', u'量比', u'振幅%']

    non_values = [u'代码', u'名称', u' 所属行业']
    real_status = format_dfcf_export_text(real_status, '', non_values)

    return (real_status)


'''
    基于pe等参数选取当前满足特定参数的标的，参数为列表[low,high]
    市盈率pe
    市净率
    总股本
    总市值
    流通股本
    流通市值
    3日、6日涨幅%、换手%
'''
def get_all_stock_in_sh_sz_by_params(pe=[5,60]):
    col = '市盈率'
    need_cols = [col,'代码','金额']
    stocks=read_real_status(all_stock=True)[need_cols]

    # 剔除无成交的标的  停牌或未上市
    stocks = stocks[stocks['金额'] > 0.0]

    #按市盈率从小到大排序
    stocks=stocks.sort_values(by=col)
    stocks = stocks[stocks[col]>=pe[0] ]
    stocks = stocks[stocks[col] <= pe[1]]
    return stocks['代码'].values

def get_all_stock_current_status(all_stock=True,mystock_index=0):
    col = '金额'
    need_cols = [col,'代码']
    stocks=read_real_status(all_stock=all_stock,mystock_index=mystock_index)

    #按成交金额从大到小排序
    stocks=stocks.sort_values(by=col,ascending=False)
    #剔除无成交的标的
    stocks = stocks[stocks[col]>0.0 ]
    return stocks

'''
    多头选股：低位起涨  1 buy
            条件与：15日内创30日新低，10日内连续缩量，
                条件或：5日内温和上涨，10日内间歇放量，5日内突然放量
                东方财富条件选股不好用，改用掘金量化终端自行选择

                中证700 SHSE.000906，  沪深300 SHSE.000300
    '''
def get_stock_1buy(block='SHSE.000906',
    week_in_seconds=4 * 60 * 60,weeks=[5,10,20],stocks=''):
        if stocks=='':
            stock_list = gmTools.get_block_stock_list(block)
        else:
            stock_list=stocks

        stock_long=[]
        nLastWeeks=3
        count=sum(weeks)*2+nLastWeeks*2

        for stock in stock_list:
            bars = gmTools.read_last_n_kline(stock, week_in_seconds,count)

            if bars is None:
                continue

            closing=bars['close']
            if not close_ma_up(closing=closing, maList=weeks, nLastWeeks=nLastWeeks):
                continue

            # 15日内创30日新低
            vol_count = int(count/2)
            if closing.idxmin()!=closing[-vol_count:].idxmin():
                continue

            #最近5日收盘价大于5日均价至少4天
            closing_ma = closing[-vol_count:].rolling(window=5, center=False).mean()
            tmp=(closing[-5:]>=closing_ma[-5:]).tolist().count(True)>3
            if tmp==False:
                continue

            vols = bars['volume'][-vol_count * 2:]

            #15日内连续缩量  vol小于5日均值的数量占60%以上
            vol_ma=vols.rolling(window=5,center=False).mean()
            tmp=(vols[-vol_count:]<vol_ma[-vol_count:]).tolist().count(True)
            if tmp/vol_count<0.5:
                continue

            #条件或：10日内间歇放量
            vol_count = 10
            tmp = (vols[-vol_count:] >3* vol_ma[-vol_count:]).tolist().count(True)/vol_count
            tmp1=False
            tmp2=False
            if tmp<0.2:
                # 条件或：5日内温和上涨，5日内突然放量
                tmp1 = (vols[-vol_count:] >  vol_ma[-vol_count:]).tolist().count(True)/vol_count>0.4    #大于5日均线
                tmp2 = (vols[-vol_count:] > 3* vol_ma[-vol_count:]).tolist().count(True)/vol_count>0.4  #大于5日均线2倍

            if tmp>=0.2 or tmp1 or tmp2:
                #满足可介入条件
                stock_long.append(stock[5:])

        #print('stock long count: %d'%len(stock_long))
        #print( stock_long)
        return stock_long

#中期起涨  更常见的起涨模式  2buy
def get_stock_2buy(block='SHSE.000906',
    week_in_seconds=4 * 60 * 60,weeks=[5,10,20],stocks=''):
    if stocks=='':
        stock_list = gmTools.get_block_stock_list(block)
    else:
        stock_list=stocks

    nLastWeeks = 3
    count = sum(weeks) * 2 + nLastWeeks * 2
    stock_long = []
    for stock in stock_list:
        bars = gmTools.read_last_n_kline(stock, week_in_seconds, count)

        if bars is None or len(bars)<count:
            continue

        closing = bars['close']
        if not close_ma_up(closing=closing,maList=weeks,nLastWeeks=nLastWeeks):
            continue

        # 最近交易日创阶段放量新高
        if closing.idxmax() != len(closing)-1:
            continue

        vol_count = int(count / 2)
        vols = bars['volume'][-count:]


        vol_ma = vols.rolling(window=5, center=False).mean()

        #放量日：成交量是5日均线3倍以上、收阳线？？
        open=bars.loc[len(bars)-1,'open']

        if vols[count-1]<=3*vol_ma[count-1] and closing[count-1]<=open:
            continue

        # 缩量盘整，分析期后半段vol小于5日均值的数量占30%以上,不含新高日
        tmp = (vols[-vol_count+1:] < vol_ma[-vol_count+1:]).tolist().count(True)
        if tmp / (vol_count-1) < 0.3:
            continue

        # 满足可介入条件
        stock_long.append(stock[5:])

    return stock_long

#基于搓揉线的洗盘、见顶检测  很少见到，机会似乎不多
# 实时状态下检测最近5个交易日是否存在搓揉洗盘的情况
    #   1、前一日为长上影线K线，上影线长度 / K线全长 > 0.7  最大涨幅大于5%
    #   2、后一日为长下影线K线，下影线长度 / K线全长 > 0.7  最大跌幅大于5%
    #   返回搓揉线出现的位置
def check_washing(kdata,week=5):
    data_len=len(kdata)
    washing_index = []  # 洗盘点
    if data_len-week<1:
        return washing_index

    for i in range(data_len-week,data_len-1):
        if i-2<0:
            continue
        try:
            k_hight=kdata.loc[i-1,'high']-kdata.loc[i-1,'low']
            #阳线  长上影
            if kdata.loc[i-1,'close']-kdata.loc[i-1,'open']>0 \
              and kdata.loc[i-1,'high']/kdata.loc[i-2,'open']>1.03:
                k_hight=(kdata.loc[i-1, 'high'] - kdata.loc[i-1, 'close'])/k_hight
                if k_hight>0.7:
                    k_low=kdata.loc[i,'high']-kdata.loc[i,'low']
                    ll=min(kdata.loc[i, 'close'],kdata.loc[i, 'open'] )- kdata.loc[i, 'low']
                    #不论阴阳  长下影
                    if ll>=0.01 and kdata.loc[i, 'low']/kdata.loc[i-1, 'close']<0.97:
                        k_low = (ll)/k_low
                        if k_low>0.7:
                            washing_index.append(i)
        except:
            write_log_msg()
            pass
    return  washing_index

#检查标的目前是否处于多头状态
def get_stock_long(stock_list,
    week_in_seconds=4 * 60 * 60,weeks=[5,10,20]):

    now = datetime.datetime.now()
    stock_long = []
    count=sum(weeks)*2

    for stock in stock_list:
        bars = gmTools.read_last_n_kline(stock, week_in_seconds, count+10)

        if bars is None:
            continue

        wash_index=check_washing(bars,week=count)

        if len(wash_index)==0:
            continue

        print(stock[5:])

        if cacl_reward:
            #评估搓揉线的操作价值
            # 以搓揉线后的第二日开盘价买入，3日后以收盘价卖出的收益
            for washing_index in wash_index:
                if washing_index+4<count+10:
                    try:
                        reward2=int(bars.loc[washing_index+2,'close']/bars.loc[washing_index+1,'open']*100)-100
                        reward5 = int(bars.loc[washing_index + 5, 'close'] / bars.loc[washing_index + 1, 'open'] * 100) - 100
                        reward15 = int(bars.loc[washing_index + 15, 'close'] / bars.loc[washing_index + 1, 'open'] * 100) - 100
                        f.write("%s,%s,2:%s,5:%s,15:%s\n"%(stock[5:],
                            bars.loc[washing_index+1,'eob'].date(),reward2,reward5,reward15))

                    except:
                        break

        # 满足可介入条件
        stock_long.append(stock[5:])

    f.close()
    print('stock washing count: %d' % len(stock_long))
    return stock_long


#检查特定板块或全部关注标的最近5个交易日是否存在洗盘情况
def get_stock_washing(stock_list,
    week_in_seconds=4 * 60 * 60,count=20,
    cacl_reward=False):

    now = datetime.datetime.now()
    stock_long = []
    f = open(str(now.date()) + '-washing.txt', 'at')

    for stock in stock_list:
        bars = gmTools.read_last_n_kline(stock, week_in_seconds, count+10)

        if bars is None:
            continue

        wash_index=check_washing(bars,week=count)

        if len(wash_index)==0:
            continue

        print(stock[5:])

        if cacl_reward:
            #评估搓揉线的操作价值
            # 以搓揉线后的第二日开盘价买入，3日后以收盘价卖出的收益
            for washing_index in wash_index:
                if washing_index+4<count+10:
                    try:
                        reward2=int(bars.loc[washing_index+2,'close']/bars.loc[washing_index+1,'open']*100)-100
                        reward5 = int(bars.loc[washing_index + 5, 'close'] / bars.loc[washing_index + 1, 'open'] * 100) - 100
                        reward15 = int(bars.loc[washing_index + 15, 'close'] / bars.loc[washing_index + 1, 'open'] * 100) - 100
                        f.write("%s,%s,2:%s,5:%s,15:%s\n"%(stock[5:],
                            bars.loc[washing_index+1,'eob'].date(),reward2,reward5,reward15))

                    except:
                        break

        # 满足可介入条件
        stock_long.append(stock[5:])

    f.close()
    print('stock washing count: %d' % len(stock_long))
    return stock_long

#获取全部平安自选股和dfcf自选股列表
def sum_pazq_dfcf_stocks():
    stocks = gmTools.read_pazq_selfstock_path('pazq')
    for stock in gmTools.read_dfcf_selfstock_file('dfcf.ebk'):
        if stock not in stocks:
            stocks.append(stock)

    return  stocks

#从文件加载dfcf自定义股票列表
def load_dfcf_stock_2_mystock():
    f = open('dfcf.ebk', 'r')
    tmp = f.read()
    f.close()

    stock_list = []
    while len(tmp) > 0:
        try:
            if '\n' not in tmp:
                i = len(tmp)
            else:
                i = tmp.index('\n')

            if i > 0:
                stock = tmp[:i]
                if stock not in stock_list:
                    stock_list.append(stock)

            tmp = tmp[i + 1:]
        except:
            break

    add_stock_2_mystock('自选股', stock_list)



#分析平安证券有关的个股：一致预期、首次评级和调高评级标的介入机会
def add_pazq_stock_2_mystock():
    stocks=gmTools.read_pazq_selfstock_path('pazq')
    tmp=get_stock_1buy(block='',stocks=stocks)

    for stock in get_stock_2buy(block='', stocks=stocks):
        #剔除同名个股
        if stock not in tmp:
            tmp.append(stock)
    return  tmp#


#--------------main -------------------------------------
hwnd_dfcf=0
def load_dfcf():
    global hwnd_dfcf
    screenWidth, screenHeight = pyautogui.size()
    if screenWidth!=1366:
        #only use in 1366*768
        win32gui.MessageBox(None,'只能在1366*768分辨率下运行','dfcf接口',0)
    else:
        hwnd_dfcf=win32gui.FindWindow(None, '东方财富终端')
        if hwnd_dfcf!=0:
            win32gui.ShowWindow(hwnd_dfcf, win32con.SW_MAXIMIZE)
        else:
            openDFCF()

        time.sleep(1)
        show_dfcf()
        time.sleep(10)

mail_conten=''
def read_save_mystock_real_addholding(mystock_holding,index=0,
    send2wechat=5,is_all_stocks=False,check_buy=False,is_send_mail=False,select_buyable=False):
    global mail_conten

    show_dfcf()
    now = datetime.datetime.now()
    int_time = now.hour * 100 + now.minute

    save_all_col = ['代码','rank','今日增仓占比','3日增仓占比','5日增仓占比',
                    '10日增仓占比','今日排名变化', '3日排名变化', '5日排名变化', '10日排名变化', 'time']

    save_col = ['代码', 'rank','今日增仓占比','今日排名变化', 'time']

    try:
        if is_all_stocks :
            botton_menu='沪深A股'
            tmp = read_real_add_holding(all_stock=is_all_stocks, index=-1)[save_all_col]
            writer = pd.ExcelWriter(botton_menu + '昨日数据' + str(now.date()) + '.xlsx')
            tmp.to_excel(writer, '昨日数据')
            writer.save()
            writer.close()

            mystock_holding = tmp[save_col].copy()
        else:
            botton_menu=mystock_list[index]
            tmp = read_real_add_holding(all_stock=is_all_stocks, index=index)[save_col]
            mystock_holding = pd.concat([mystock_holding, tmp], ignore_index=True)  #累计当日标的

        if select_buyable:#基于增仓参数选股
            return mystock_holding['代码'].values
        else:
            #cacl buy point
            if check_buy and int_time>92500 and int_time<150500:
                all_count=0
                stocks=[]
                for stock in list(tmp['代码'].values):
                    if stock[0] == '6':
                        stock = 'SHSE.' + stock
                    else:
                        stock = 'SZSE.' + stock

                    if get_stock_1buy('', stocks=[stock]) \
                            or get_stock_2buy('', stocks=[stock]):
                        # todo 考虑利用1、3、5、10日的涨幅判断当前走势是否具备介入机会
                        stocks.append(stock[5:])
                        all_count += 1
                        if all_count >= 10:
                            break

                msg ='\n[' +botton_menu+ ']加仓:' + str(stocks)
                #send_mail("市场动态",msg=msg)
                #wechat.send_market_msg(msg)
            else:
                #仅输出加仓排名大的标的
                msg = '\n['+ botton_menu+ ']加仓:' + str(tmp['代码'][:send2wechat].values)

            mail_conten += msg
            if is_send_mail and len(mail_conten)>0:
                    #wechat.send_market_msg(msg)
                    #if  int_time>92500 and int_time<150500:
                    send_mail("市场动态", msg=mail_conten)
                    print(' \n[%s] send msg to user\n %s \n '%(now.time(),mail_conten))

                    mail_conten=''

            return  mystock_holding

    except:
        write_log_msg()

#基于增仓数据的买卖点检测
def detect_mystock_sell_real_addholding(mystock_holding, index=0,
                                      send2wechat=5, is_all_stocks=False,
                                      check_buy=False, is_send_mail=False):
    global mail_conten

    show_dfcf()
    now = datetime.datetime.now()
    int_time = now.hour * 100 + now.minute

    save_all_col = ['代码', 'rank', '今日增仓占比', '3日增仓占比', '5日增仓占比',
                    '10日增仓占比', '今日排名变化', '3日排名变化', '5日排名变化', '10日排名变化', 'time']
    save_col = ['代码', 'rank', '今日增仓占比', '今日排名变化', 'time']

    try:
        if mystock_holding is None:
            tmp = read_real_add_holding(all_stock=is_all_stocks, index=index,detect_buy=False)[save_all_col]
            mystock_holding = tmp[save_col].copy()
        else:
            tmp = read_real_add_holding(all_stock=is_all_stocks, index=index,detect_buy=False)[save_all_col]
            mystock_holding = pd.concat([mystock_holding, tmp], ignore_index=True)  # 累计当日标的

        # cacl sell point  save the lastest 10
        tmp=tmp[:send2wechat].reset_index()

        mail_conten +='[sell mystock] %s' % tmp['代码'].values

        if is_send_mail and len(mail_conten) > 0:
            # wechat.send_market_msg(msg)
            # if  int_time>92500 and int_time<150500:
            send_mail("市场动态", msg=mail_conten)
            print(' \n[%s] send msg to user\n %s \n ' % (now.time(), mail_conten))

            mail_conten = ''

            return mystock_holding

    except:
        write_log_msg()

# 分析最近2000交易日数据，效果不好，不足以指导操作
def check_washing_in_sh_sz_2_hot():
    load_dfcf()
    tmp = read_allstock_real_capflow()['代码'].tolist()
    stocks = []
    for stock in tmp:
        if stock[0] == '6':
            stocks.append('SHSE.' + stock)
        else:
            stocks.append('SZSE.' + stock)

    now = datetime.datetime.now()
    print(str(now) + ' caculate washing')
    add_stock_2_mystock('hot', get_stock_washing(stock_list=stocks,
                                                 week_in_seconds=4 * 60 * 60, count=30, cacl_reward=True))

#TODO 邮件发送有时不可靠
def send_mail(title,msg):
    import smtplib

    from email.mime.text import MIMEText
    from email.header import Header

    sender = "haigezyj@qq.com"
    receiver = ["haigezyj@qq.com"]
    subject = title
    smtpserver = "smtp.qq.com"
    username = 'haigezyj@qq.com'
    password = "luptgsjeqkdhcgfj"

    msg = MIMEText(msg, 'plain', 'utf-8')  # 中文需参数‘utf-8'，单字节字符不需要

    msg['From'] = Header("旭日东升", 'utf-8')
    msg['To'] = Header("市场动态", 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    smtp = smtplib.SMTP_SSL(smtpserver, 465)
    retry=0

    while retry<6:
        try:
            smtp.login(username, password)
            smtp.sendmail(sender, receiver, msg.as_string())
            smtp.quit()
            break
        except:
            retry+=1

#潘倩计算1、2买标的
def cacl_12buy(favorite_stocks=''):
    # 初始化当日可选标的列表
    now = datetime.datetime.now()
    print(str(now) + ' caculate all stock 1buy')

    #从阶段统计中获取待评估的标的
    tmp1=export_period_statics(index=-1,detect_buy=True,pe=[1,60])['代码'].values

    #基于主力增仓数据获取标的
    tmp = read_save_mystock_real_addholding(
        None,
        index=-1, send2wechat=10,
        is_all_stocks=True, check_buy=True,
        is_send_mail=False, select_buyable=True
    )

    #两种标的合成，以阶段统计数据为主
    stocks = tmp
    tmp=[]
    for stock in stocks:
        if stock in tmp1:
            tmp.append(stock)

    # 两种标的合成，以关注的数据为主
    if len(favorite_stocks)==0:
        stocks = tmp
    else:
        stocks = []
        for stock in tmp:
            if stock in favorite_stocks:
                stocks.append(stock)
                if len(stocks) > 200:
                    break

    add_stock_2_mystock('1buy', stocks)

    #获取自选股信息,计算2买
    print(str(now) + ' caculate my stock buy1/buy2 by addholding')
    tmp = read_save_mystock_real_addholding(
        None, index=0, check_buy=False, select_buyable=True)

    add_stock_2_mystock('hot', tmp)

    print(str(now) + ' caculate pabuy buy')
    tmp = read_save_mystock_real_addholding(
        None, index=5, check_buy=False, select_buyable=True)
    add_stock_2_mystock('2buy', tmp)

#交易日循环
'''
    利用独立线程定期完成实时性强、时效高的参数自动获取资金流、顶级挂单、拖拉机单、强势狙击，
其他参数时效性不高，每个交易日读取一次并保存即可。
'''
def trade_date_loop():
    allstock_holding = None

    #检测当日实时累计加仓情况，附带3、5、10日加仓数据统计
    #利用实时资金流可推算出累计资金流，本函数每日调用一次即可，待优化
    def check_addholding(count):
        global allstock_holding

        try:
            load_dfcf()

            detect_mystock_sell_real_addholding(
                None,
                index=0, check_buy=False, send2wechat=15
            )
            
            mystock_holding = read_save_mystock_real_addholding(
                None,
                index=0,check_buy=False,  send2wechat=10)

            etf_holding = read_save_mystock_real_addholding(None,
                index=7, check_buy=False, send2wechat=5)

            buy1_holding = read_save_mystock_real_addholding(None,
                                    index=2, check_buy=False, send2wechat=5)
            buy2_holding = read_save_mystock_real_addholding(None,
                                    index=3, check_buy=False, send2wechat=5)
            pabuy_holding = read_save_mystock_real_addholding(None,
                                    index=5, check_buy=True, send2wechat=5)

            hot_holding = read_save_mystock_real_addholding(None,
                                    index=6, check_buy=False, send2wechat=5)


            allstock_holding = read_save_mystock_real_addholding(
                allstock_holding,
                index=-1, send2wechat=10,
                is_all_stocks=True, check_buy=True, is_send_mail=True)

            data_change=True


        except:
            write_log_msg()


        return count+1

    #检测资金流情况并存盘
    def check_cap_flow(count=0):
        global allstock_holding,qsjj_list,djgd_list,tljd_list

        try:
            current_eob = gmTools.get_last_trade_datetime()
            current_eob=current_eob.hour()*10000+current_eob.minute()*100+current_eob.second()
            # 交易时间未发生变化，继续等待
            # '''
            if current_eob == last_eob:
                if not allstock_holding is None:
                    data_change = False
                    writer = pd.ExcelWriter('沪深A股' + str(now.date()) + '.xlsx')
                    allstock_holding.to_excel(writer, '沪深A股')
                    writer.save()
                    writer.close()

                return count+1
                # '''

            load_dfcf()
            last_eob=current_eob

            detect_mystock_sell_real_addholding(
                None,
                index=0, check_buy=False, send2wechat=15
            )
            mystock_holding = read_save_mystock_real_addholding(
                None,
                index=0,check_buy=False,  send2wechat=10)

            etf_holding = read_save_mystock_real_addholding(None,
                index=7, check_buy=False, send2wechat=5)

            buy1_holding = read_save_mystock_real_addholding(None,
                                    index=2, check_buy=False, send2wechat=5)
            buy2_holding = read_save_mystock_real_addholding(None,
                                    index=3, check_buy=False, send2wechat=5)
            pabuy_holding = read_save_mystock_real_addholding(None,
                                    index=5, check_buy=True, send2wechat=5)

            hot_holding = read_save_mystock_real_addholding(None,
                                    index=6, check_buy=False, send2wechat=5)


            allstock_holding = read_save_mystock_real_addholding(
                allstock_holding,
                index=-1, send2wechat=10,
                is_all_stocks=True, check_buy=True, is_send_mail=True)

            data_change=True

            if count %5==4 and int_time>trade_stop and data_change:
                writer = pd.ExcelWriter('沪深A股' + str(now.date()) + '.xlsx')
                allstock_holding.to_excel(writer, '沪深A股')
                writer.save()
                writer.close()
                data_change=False
                print("trade stop,save all data %s"%now)

        except:
            write_log_msg()


        return count+1

    #初始化每日基本参数
    def init_trade_loop():
        # 次日凌晨初始化下一交易日标的
        # openGM()
        load_dfcf()
        favorite_stocks = get_all_stock_in_sh_sz_by_params()  # 指定pe范围的标的
        favorite_stocks.sort()  # 按代码排序，便于后续使用,6位数字符串

        dailyinit = "dailyinit.txt"
        if not os.path.isfile(dailyinit):
            f = open(dailyinit, "wt")
            tmp = ''
        else:
            f = open(dailyinit, "r+")
            tmp = f.read()
            f.seek(0)

        if tmp != next_trade_datetime:
            f.write(next_trade_datetime)
            f.close()
            cacl_12buy(favorite_stocks)
        else:
            f.close()

    def start():
        pass

    #--------start----------------------------------------------------
    trade_stop=1503
    trade_start=925
    check_interval=0  #连续采集资金流数据，其他数据通过计算获得
    buy_check_time=[1000,1100,1330,1430] #buy  point detect time

    count = 0
    last_eob=0

    stock_list_need_init = True
    data_change=False

    while True:
        # 非交易时间段  不做处理
        now = datetime.datetime.now()

        int_time = now.hour * 100 + now.minute
        next_trade_datetime =str(now.date()) #str(gmTools.get_next_trade_date(now.date()))  #str(now.date())  # 下一交易日

        #init trade loop every trade day
        if stock_list_need_init and \
          next_trade_datetime == str(now.date()):
            init_trade_loop()
            stock_list_need_init = False
            print(str(now) + ' init_trade_loop \n')

        if  int_time>trade_stop or int_time<trade_start :
            count = 0

            print(str(now)+' waiting to trade\n')
            time.sleep(check_interval)

            #每个交易日六点自动初始化股票列表
            if  int_time>600 and  int_time<700  and next_trade_datetime == str(now.date()):
                count = 0
                last_eob = 0
                data_change = False
                stock_list_need_init = True
                qsjj_list = None
                djgd_list = None
                tljd_list = None

            time.sleep(20*60)
            continue

        current_eob = gmTools.get_last_trade_datetime()
        current_eob = current_eob.hour*10000+current_eob.minute*100+current_eob.second

        # 交易时间发生变化才进行实时状态检测  30秒检测一次
        if current_eob != last_eob:
            last_eob =current_eob

            #check cap flow every minute
            #logger.debug('read_real_capflow start %s'%(datetime.datetime.now().time()))
            #read_real_capflow(-1,current_eob)
            #logger.debug('read_real_capflow start %s' % (datetime.datetime.now().time()))

            '''
            获取各种挂单信息太费时间，不如基于资金流直接计算买卖强度
            print('强势狙击', datetime.datetime.now().time())
            read_real_L2Room(top_menu='强势狙击')

            print('顶级挂单', datetime.datetime.now().time())
            read_real_L2Room(top_menu='顶级挂单')

            print('拖拉机单', datetime.datetime.now().time())
            read_real_L2Room(top_menu='拖拉机单')

            #buy point detect
            if int_time in buy_check_time:
                count=check_addholding(count)
            '''

            time.sleep(check_interval)
        else:
            time.sleep(60)


def read_dfcf_real_cap(index):
    if index == -1:
        file_path = '沪深A股'
    else:
        file_path = mystock_list[index]

    (ppReadCap, ppCaclCap) = Pipe()

    (ppReadCap1, ppCaclCap1) = Pipe()
    (ppReadCap2, ppCaclCap2) = Pipe()

    # p1=Process(target=trade_date_loop, args=())

    # read_real_capflow(index,pipe,is_file=False,debug=False,
    #    file_paths=['e:\\data\\etf-cap-2018-05-18.txt'] ):
    p2 = Process(target=read_real_capflow,
                 args=(index, ppReadCap,ppReadCap1,ppReadCap2,
                       False, False,['e:\\data\\沪深A股-cap-2018-05-24.txt'])
                 )
    real_capflow = capflow_class()

    #大单检测很耗时间，用三个进程进行处理
    p3 = Process(target=process_real_capflow, args=(real_capflow,ppCaclCap,file_path))

    p4 = Process(target=process_real_capflow, args=(real_capflow,ppCaclCap1, file_path))
    p5 = Process(target=process_real_capflow, args=(real_capflow, ppCaclCap2, file_path))

    # p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()

    # p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()

is_stop=False
is_pause=False

def on_char(event):
    global  is_stop,is_pause

    if event.Key=='P':
        is_pause=not is_pause
        print('is_pause')
        time.sleep(0.5)
    elif event.Key=='Q':
        is_stop = not is_stop
        print('is_stop')
        time.sleep(0.5)

    return True

def hook_keyboard():
    hm = pyHook.HookManager()
    hm.KeyDown=on_char
    hm.HookKeyboard()
    print("waiting key event")
    # 进入循环，如不手动关闭
    pythoncom.PumpMessages()

capflow=[]
caplock=Lock()
if __name__ == '__main__':
    #threading.Thread(target=hook_keyboard, name='hook_keyboard').start()
    read_dfcf_real_cap(index=-1)



    '''
    
    real_capflow = capflow_class()
    read_cap_from_file(real_capflow=real_capflow,
                      file_paths=['e:\\data\\沪深A股-cap-2018-05-24.txt'] )
    read_real_capflow(index=-1,pipe=None,is_file= True,debug= True)
    file_exist('e:\\data\\ticks-600711-20180511.dat')
    file_exist('e:\\data\\ticks-600711-20180511--.dat')
    ret = read_real_capflow(1)
    read_real_L2Room(top_menu='强势狙击')
    read_real_L2Room(top_menu='顶级挂单')
    read_real_L2Room(top_menu='拖拉机单')
    print('\n')
    print(ret[:1])
    print(ret[1:2])


    ret = read_real_capflow(2)
    print('\n')
    print(ret[:1])
    print(ret[1:2])
    cacl_12buy()
    
    load_dfcf()
    load_dfcf_stock_2_mystock()
    
    
        '''

