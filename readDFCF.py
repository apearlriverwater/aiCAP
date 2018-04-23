# -*- coding: utf-8 -*-

'''
  1、操作dfcf界面的控制程序，自动控制软件启动、登录、功能项选择等
  2、在交易日定期利用数据导出功能把数据导出到剪辑板或者文件再进行处理
  2.1 导出大盘指数情况
    未实现。
    可利用掘金的数据订阅功能实现数据收集。

  2.2 全市场涨跌情况
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
import os
import numpy as np
import gmTools


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

dfcf_main_file = "c:\\eastmoney\\swc8\\mainfree.exe"
dfcf_menu_points=[
    ['首页',28,44],
    ['全景图',108,44],
    ['自选股',188,44],
    ['工具',510,16],
    ['设置自选股',201,44],
    ['沪深排行',266,44],
    ['板块检测',332,44],
    ['沪深指数',394,44]
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
    ['hot',387,519]
]

#自动向自选股添加需要的标的
def add_stock_2_mystock(group_name,stock_list):
    found = False
    for item in dfcf_menu_points:
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
        time.sleep(0.2)

    for item in setup_my_stock_ui_item:
        if 'exit' == item[0]:
            pyautogui.click(item[1], item[2])
            break

def write_log_msg():
    import traceback
    now = datetime.datetime.now()
    f = open("errorlog.txt", "a")
    f.write('\n'+str(now)+'\n')
    f.write(traceback.format_exc())
    f.close()
    print(traceback.format_exc())


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

def click_dfcf_menu(menu_points=dfcf_menu_points,menu_name='首页'):
    for item in menu_points:
        if menu_name==item[0]:
            pyautogui.click(item[1],item[2])
            time.sleep(0.2)
            return  True

    return  False

def show_dfcf():
    time.sleep(0.5)
    try:
        regex ='东方财富终端'
        cW = cWindow()
        cW.find_window_regex(regex)
        cW.Maximize()
        cW.SetAsForegroundWindow()
        #点击首页
        click_dfcf_menu(menu_points=dfcf_menu_points, menu_name='首页')
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
            time.sleep(1)
            win32api.SendMessage(hwnd_dfcf, win32con.WM_CLOSE, 0, 0)  # CLOSE WINDOWS
            ret = True
    except:
        write_log_msg()
        pass

    return  ret

def  close_export_window():
    return  close_window(caption="导出对话框")

def  close_welcome():
    return close_window(caption="东方财富    [按Esc关闭本窗口]")


def openDFCF(file=dfcf_main_file):
    prs = subprocess.Popen([file])

    #等待欢迎提示窗体，出现后关闭它，最长等待35秒
    # 找不到应用自行弹出的窗口，无法点击它
    waiting=60
    while waiting>0:
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
    d = clipboard.GetClipboardData(win32con.CF_TEXT)
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
            time.sleep(0.05)
            pyautogui.keyUp(key[0])
            time.sleep(0.1)

#模拟人工操作的方式导出东方财富数据
def export_dfcf_data(click_points,key_list):
    ret=''
    #try:
    #click_fig("dfcfMenu\\cap_flow.png")
    #time.sleep(2)
    if True: #click_fig("dfcfMenu\\l2_cap_flow.png", 85):
        set_text_2_clipboard()
        for point in click_points[:-1]:
            click_dfcf_menu(point[0],point[1])

        #popup menu
        pyautogui.rightClick(click_points[-1])

        #按键序列处理
        for key in key_list:
            for _ in range(key[1]):
                pyautogui.keyDown(key[0])
                pyautogui.keyUp(key[0])

        close_export_window()

        #todo 二进制格式的文本待解析
        ret=get_text_from_clipboard()

    #except:
    #    write_log_msg()
    #    ret=None
    return  ret

#模拟人工操作的方式导出all实时资金流
def export_allstock_real_capflow():
    click_points=[
        [dfcf_menu_points,'沪深排行'],
        [hs_rank_top_menu, '资金流向'],
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

    return  export_dfcf_data(click_points,key_list)


def export_allstock_real_status():
    click_points=[
        [dfcf_menu_points,'沪深排行'],    #沪深排行
        [hs_rank_botton_menu, '沪深A股'],  #沪深A股
        [hs_rank_top_menu, '行情列表'],
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

def export_allstock_period_statics():
    click_points=[
        [dfcf_menu_points,'沪深排行'],    #沪深排行
        [hs_rank_botton_menu, '沪深A股'],  #沪深A股
        [hs_rank_top_menu, '阶段统计'],
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

def export_mystock_period_statics(index=0):
    if index==0:
        click_points=[
            [dfcf_menu_points,'自选股'],    #沪深排行
            [mystock_botton_menu, '自选股'],
            [hs_rank_top_menu, '阶段统计'],
            [204, 312]   #呼出右键菜单
        ]
    else:
        click_points = [
            [dfcf_menu_points, '自选股'],  # 沪深排行
            [mystock_botton_menu, 'qsz2'],
            [hs_rank_top_menu, '阶段统计'],
            [204, 312]  # 呼出右键菜单
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

#实时加仓数据  增仓排名
def export_allstock_real_add_holding():
    click_points=[
        [dfcf_menu_points,'沪深排行'],    #沪深排行
        [hs_rank_botton_menu, '沪深A股'],
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


#实时加仓数据  增仓排名
def export_allstock_real_add_holding(botton_menu='沪深A股'):
    click_points=[
        [dfcf_menu_points,'沪深排行'],    #沪深排行
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


def export_mystock_real_add_holding(botton_menu='自选股'):
    click_points = [
        [dfcf_menu_points, '自选股'],  # 沪深排行
        [mystock_botton_menu, botton_menu],
        [hs_rank_top_menu, '增仓排名'],  # 增仓排名
        [204, 312]  # 呼出右键菜单
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


#模拟人工操作的方式导出all实时资金流
def export_mystock2_real_capflow():
    click_points=[
        [dfcf_menu_points, '自选股'],
        [mystock_botton_menu, '自选股'],
        [hs_rank_top_menu, '资金流向'],
        [204, 312]
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

def export_mystock_real_capflow():
    click_points=[
        [dfcf_menu_points,'自选股'],
        [mystock_botton_menu, '自选股'],
        [hs_rank_top_menu, '资金流向'],
        [204, 312]
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

def export_mystock2_real_status():
    click_points=[
        [175,40],
        [178,692],
        [127,62],
        [204, 312]
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

def export_mystock_real_status(index=0):
    if index==0:
        click_points=[
            [dfcf_menu_points,'自选股'],
            [mystock_botton_menu, '自选股'],
            [hs_rank_top_menu, '行情列表'],
            [204, 312]
        ]
    else:
        click_points = [
            [dfcf_menu_points, '自选股'],
            [mystock_botton_menu, 'qsz2'],
            [hs_rank_top_menu, '行情列表'],
            [204, 312]
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



#获取字段内容并转成数字类型
def get_item_from_line(line,value_index=[],non_value_index=[]):
    def is_float(str):
        try:
            float(str)
            return  True
        except:
            return  False


    data=[]
    try:
        item_index=0
        if len(value_index)>0:
            while len(line)>0:
                next_tab=line.index(b'\t')
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
                next_tab=line.index(b'\t')
                #丢弃长度为0的字符串
                if next_tab>0:
                    item=line[:next_tab]
                    #数字转换
                    if len(non_value_index)>0 and not item_index in non_value_index:
                        if item.isdigit():
                            item=int(item)
                        #数字中有含单位：亿或万，应去掉
                        elif is_float(item) :
                            item=float(item)
                        elif is_float(item[:-2]):
                            item = float(item[:-2])
                        else:
                            item=0.0
                    else:
                        item=item.decode('gbk')

                    data.append(item)
                    item_index += 1

                line=line[next_tab+1:]
    except:
        #write_log_msg()
        pass

    return  data

'''
    dfcf导出的数据格式为文本格式，字段间用tab分隔，每条记录一行用（\n）分隔
    第一行为标题栏，记录各字段名，第二行起是具体内容
'''
def format_dfcf_export_text(export_text,values='',non_values=''):
    index=0
    data_list=[]
    #get title
    next_end = index + export_text[index:].index(b'\n')
    line = export_text[index:next_end]
    index = next_end + 1
    data_list.append(get_item_from_line(line))

    #确定数值类型的字段序号
    title=data_list[0]
    values_index=[title.index(value) for value in values]
    non_values_index = [title.index(value) for value in non_values]

    if len(values_index)>0:
        while index<len(export_text):
            next_end=index+export_text[index:].index(b'\n')
            line=export_text[index:next_end]
            index=next_end+1
            data_list.append(get_item_from_line(line,values_index))

    if len(non_values_index)>0:
        while index<len(export_text):
            next_end=index+export_text[index:].index(b'\n')
            line=export_text[index:next_end]
            index=next_end+1
            data_list.append(get_item_from_line(line,'',non_values_index))

            # 确定数值类型的字段序号

    data = pd.DataFrame(data_list[1:])
    data.rename(columns={i: title[i] for i in range(len(title))}, inplace=True)
    return  data

def read_allstock_real_capflow():
    real_status =export_allstock_real_capflow() # export_mystock_real_capflow()  # export_allstock_real_capflow():
    non_values = [u'代码', u'名称']

    real_status = format_dfcf_export_text(real_status,'',non_values)
    return real_status


def read_mystock_real_capflow(index=0):
    if index==0:
        real_status =export_mystock_real_capflow()
    else:
        real_status = export_mystock2_real_capflow()

    non_values = [u'代码', u'名称']

    real_status = format_dfcf_export_text(real_status, '', non_values)


    print(real_status.loc[:2])


#阶段统计
# 自定义1至5日、10日、20日、30日成交量（换手率）、成交金额、振幅、复权后的均价，
# 自行计算波动率：寻找突破者
def read_real_period_static(all_stock=True,mystock=0):
    if all_stock:
        real_status = export_allstock_period_statics()  # export_mystock_real_status()  #      export_real_capflow()
    else:
        real_status = export_mystock_period_statics(index=mystock)  # export_real_capflow()



    non_values = [u'代码', u'名称']
    period_static = format_dfcf_export_text(real_status, '', non_values)

    #统一排列字段名
    dates = ['1', '2', '3', '4', '5', '10', '20', '30']
    items = [u'日换手率%', u'日成交额', u'日振幅', u'日均价']

    cols=non_values
    for item in items:
        for date in dates:
            cols.append(date+item)

    period_static=period_static[cols]
    print(period_static[:2])

    #按字段进行排序
    return period_static

def read_real_status(all_stock=True,mystock=0):
    if all_stock:
        real_status = export_allstock_real_status()  # export_mystock_real_status()  #      export_real_capflow()
        values = u'序'
    else:
        real_status = export_mystock_real_status(mystock)  # export_real_capflow()
        values = u'初始'

    values=[values,u'代码', u'最新', u'涨幅%', u'涨跌', u'总手',
                   u'现手', u'买入价', u'卖出价', u'涨速%', u'换手%',
                   u'金额', u'市盈率', u'最高', u'最低', u'开盘',
                   u'昨收', u'量比', u'振幅%']

    non_values = [u'代码', u'名称', u' 所属行业']
    real_status = format_dfcf_export_text(real_status, '', non_values)

    print(real_status.loc[:2])

def read_real_add_holding(all_stock=True,botton_menu='沪深A股'):
    if all_stock:
        real_status = export_allstock_real_add_holding(botton_menu)  # export_mystock_real_status()  #      export_real_capflow()
    else:
        real_status = export_mystock_real_add_holding(botton_menu)  # export_real_capflow()

    values=[u'序',u'代码', u'最新', u'涨幅%',
           u'今日增仓占比', u'今日排名',u'今日排名变化', u'今日涨幅%',
           u'3日增仓占比', u'3日排名', u'3日排名变化',u'3日涨幅%',
           u'5日增仓占比', u'5日排名', u'5日排名变化',u'5日涨幅%',
           u'10日增仓占比', u'10日排名', u'10日排名变化',u'10日涨幅%'
    ]

    display_values = [ u'代码',
              u'今日排名变化', u'3日排名变化',u'5日排名变化',u'10日排名变化',
              u'今日涨幅%',u'3日涨幅%',u'5日涨幅%',u'10日涨幅%'
              ]
    non_values = [u'代码', u'名称', u' 所属行业']
    real_status = format_dfcf_export_text(real_status, '', non_values)[display_values]

    sort_vols=['今日排名变化','10日涨幅%']
    real_status=real_status.sort_values(sort_vols,ascending=False)
    #print(sort_vols)
    #print(real_status.loc[:10,sort_vols])

    # 使用datetime.now()
    now = gmTools.get_last_trade_datetime()
    int_time=now.hour*100+now.minute
    real_status['time']=int_time

    return real_status


def read_real_capflow():
    real_status = export_mystock_real_capflow()  # export_real_capflow()
    values = [u'序', u'最新', u'涨幅%', u'集合竞价', u'主力净流入',
              u'超大单净占比%', u'大单净占比%']

    real_status = format_dfcf_export_text(real_status, values)


    print(real_status.loc[:2])


'''
    多头选股：低位起涨  1 buy
            条件与：15日内创30日新低，10日内连续缩量，
                条件或：5日内温和上涨，10日内间歇放量，5日内突然放量
                东方财富条件选股不好用，改用掘金量化终端自行选择

                中证700 SHSE.000906，  沪深300 SHSE.000300
    '''
def get_stock_1buy(block='SHSE.000906',
    week_in_seconds=4 * 60 * 60,count=40,stocks=''):
        if stocks=='':
            stock_list = gmTools.get_block_stock_list(block)
        else:
            stock_list=stocks

        stock_long=[]

        for stock in stock_list:
            bars = gmTools.read_last_n_kline(stock, week_in_seconds,count)

            if bars is None:
                continue


            closing=bars['close']

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
    week_in_seconds=4 * 60 * 60,count=20,stocks=''):
    if stocks=='':
        stock_list = gmTools.get_block_stock_list(block)
    else:
        stock_list=stocks

    stock_long = []
    for stock in stock_list:
        bars = gmTools.read_last_n_kline(stock, week_in_seconds, count)

        if bars is None or len(bars)<count:
            continue

        closing = bars['close'][-count:]

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


#--------------main --------------------------------60006-----
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
        time.sleep(1)

mail_conten=''
def read_save_mystock_real_addholding(mystock_holding,botton_menu='自选股',
    send2wechat=5,is_all_stocks=False,check_buy=False,is_send_mail=False):
    global mail_conten

    now = datetime.datetime.now()
    #import infWECHAT as wechat
    save_all_col = ['代码', '今日排名变化', '3日排名变化', '5日排名变化', '10日排名变化', 'time']
    save_col = ['代码', '今日排名变化', 'time']

    if mystock_holding is None :
        tmp = read_real_add_holding(all_stock=is_all_stocks, botton_menu=botton_menu)[save_all_col]
        if  is_all_stocks:
            writer = pd.ExcelWriter(botton_menu + '昨日数据' + str(now.date()) + '.xlsx')
            tmp.to_excel(writer, '昨日数据')
            writer.save()
            writer.close()

        mystock_holding = tmp[save_col].copy()
    else:
        tmp = read_real_add_holding(all_stock=is_all_stocks, botton_menu=botton_menu)[save_col]
        mystock_holding = pd.concat([mystock_holding, tmp], ignore_index=True)

    #todo 考虑利用1、3、5、10日的涨幅判断当前走势是否具备介入机会
    #最近 1、2、2、5日走势
    if check_buy:
        all_count=0
        stocks=[]
        for stock in list(tmp['代码'].values):
            if stock[0] == '6':
                stock = 'SHSE.' + stock
            else:
                stock = 'SZSE.' + stock

            if get_stock_1buy('', stocks=[stock]) \
                    or get_stock_2buy('', stocks=[stock]):
                stocks.append(stock[5:])
                all_count += 1
                if all_count >= 10:
                    break

        msg ='\n[' +botton_menu+ ']加仓:' + str(stocks)
        #send_mail("市场动态",msg=msg)
        #wechat.send_market_msg(msg)

    else:
        msg = '\n['+ botton_menu+ ']加仓:' + str(tmp['代码'][:send2wechat].values)
        #wechat.send_market_msg(msg)
        pass

    mail_conten += msg
    if is_send_mail:
            send_mail("市场动态", msg=mail_conten)
            mail_conten=''
            print('send msg to user')


    return  mystock_holding

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
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

#交易日循环
def trade_date_loop():
    load_dfcf()
    mystock_holding = None
    buy1_holding = None
    buy2_holding = None
    pabuy_holding = None
    allstock_holding = None
    count = 0
    last_eob=0
    next_trade_datetime=str(datetime.datetime.now().date())  #下一交易日
    stock_list_need_init = True
    data_change=False
    while True:
        now = datetime.datetime.now()

        #非交易时间段  不做处理
        int_time=now.hour*100+now.minute
        if stock_list_need_init and \
            next_trade_datetime == str(now.date()):

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

                # 初始化当日可选标的列表
                stock_list_need_init = False
                tmp = gmTools.get_stocks_form_blocks(FAVORTE_BLOCKS)
                print(str(now) + ' caculate washing')
                add_stock_2_mystock('hot', get_stock_1buy(block='', stocks=tmp))

                print(str(now)+' caculate 1buy')
                add_stock_2_mystock('1buy', get_stock_1buy(block='', stocks=tmp))
                print(str(now)+' caculate 1buy')
                add_stock_2_mystock('2buy', get_stock_2buy(block='', stocks=tmp))

            f.close()
            stock_list_need_init = False
        #'''
        if  False:# int_time>1520 or now.hour<9 :
            mystock_holding=None
            buy1_holding=None
            buy2_holding = None
            pabuy_holding = None
            allstock_holding=None

            time.sleep(5 * 60)
            continue
        #'''

        try:
            # 次日凌晨初始化下一交易日标的
            stock_list_need_init = True
            current_eob = gmTools.get_last_trade_datetime()
            next_trade_datetime = gmTools.get_next_trade_date(str(current_eob.date()))
            # 交易时间未发生变化，继续等待
            # '''
            if current_eob == last_eob:

                if not allstock_holding is None and data_change:
                    data_change = False
                    writer = pd.ExcelWriter('沪深A股' + str(now.date()) + '.xlsx')
                    allstock_holding.to_excel(writer, '沪深A股')
                    writer.save()
                    writer.close()

                time.sleep(5 * 60)
                continue
                # '''

            load_dfcf()
            last_eob=current_eob

            allstock_holding = read_save_mystock_real_addholding(allstock_holding,
                                                                 botton_menu='沪深A股', send2wechat=10,
                                                                 is_all_stocks=True, check_buy=True, is_send_mail=True)

            if count % 3 == 0:
                buy1_holding = read_save_mystock_real_addholding(buy1_holding,
                                        botton_menu='1buy', send2wechat=5)
                buy2_holding = read_save_mystock_real_addholding(buy2_holding,
                                        botton_menu='2buy', send2wechat=5)
                pabuy_holding = read_save_mystock_real_addholding(pabuy_holding,
                                        botton_menu='pabuy', send2wechat=5)

            allstock_holding = read_save_mystock_real_addholding(allstock_holding,
                                    botton_menu='沪深A股', send2wechat=10,
                                    is_all_stocks=True,check_buy=True,is_send_mail=True)
            data_change=True

            if count %5==0:
                writer = pd.ExcelWriter('沪深A股' + str(now.date()) + '.xlsx')
                allstock_holding.to_excel(writer, '沪深A股')
                writer.save()
                writer.close()
                data_change=False
                print('now ',now)

        except:
            write_log_msg()

        count+=1
        time.sleep(5*60)

#分析最近2000交易日数据，效果不好，不足以指导操作
def check_washing_in_sh_sz_2_hot():
    load_dfcf()
    tmp = read_allstock_real_capflow()['代码'].tolist()
    stocks=[]
    for stock in tmp:
        if stock[0]=='6':
            stocks.append('SHSE.'+stock)
        else:
            stocks.append('SZSE.' + stock)

    now = datetime.datetime.now()
    print(str(now) + ' caculate washing')
    add_stock_2_mystock('hot', get_stock_washing(stock_list=stocks,
        week_in_seconds=4 * 60 * 60,count=30,cacl_reward=True) )

if __name__ == '__main__':


    trade_date_loop()
    pass

    '''
     check_washing_in_sh_sz_2_hot()
    load_dfcf_stock_2_mystock()
    load_dfcf_stock_2_mystock()
    add_stock_2_mystock('pabuy', add_pazq_stock_2_mystock())
    add_stock_2_mystock('1buy', get_stock_1buy(STOCK_BLOCK))
    add_stock_2_mystock('2buy', get_stock_2buy(STOCK_BLOCK))
    get_stock_washing(block='')
    
    add_stock_2_mystock('1buy',['002465','600000'])
    read_real_period_static(False, 0)
    read_real_period_static(False, 1)
    read_real_period_static(True)

    read_real_add_holding(False,0)
    read_real_add_holding(False,1)
    read_real_add_holding(True)

    read_real_status(True)
    read_real_status(False,0)
    read_real_status(False, 1)

    read_mystock_real_capflow(0)
    read_mystock_real_capflow(1)
    read_allstock_real_capflow()
    '''

