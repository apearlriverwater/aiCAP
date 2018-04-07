# -*- coding: utf-8 -*-

'''
  1、操作dfcf界面的控制程序，自动控制软件启动、登录、功能项选择等
  2、在交易日定期利用数据导出功能把数据导出到剪辑板或者文件再进行处理
  2.1 导出大盘指数情况
  2.2 全市场涨跌情况
      通过资金流获得，方便统计涨跌情况、资金流入情况
  2.3 自选股涨跌与资金流情况
      含平安推荐股票涨跌情况

  3、必要时截屏发送相关图形，手机客户端有相关图形，目前不是十分迫切


'''
import pyautogui
import subprocess
import win32gui, win32api, win32con  #module name pywin32
import win32clipboard as clipboard
import time,re

file = "E:\\02soft\\99eastmoney\\swc8\\mainfree.exe"

def write_log_msg():
    import traceback
    f = open("errorlog.txt", "a")
    f.write(traceback.format_exc())
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

def show_dfcf():
    time.sleep(2)
    try:
        regex ='东方财富终端'
        cW = cWindow()
        cW.find_window_regex(regex)
        cW.Maximize()
        cW.SetAsForegroundWindow()
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


def openDFCF(file=file):
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
    win32gui.ShowWindow(hwnd_dfcf, win32con.SW_MAXIMIZE)
    '''
    screenWidth, screenHeight = pyautogui.size()
    currentMouseX, currentMouseY = pyautogui.position()
    num_seconds = 1.2
    #  用num_seconds秒的时间把光标移动到(x, y)位置
    pyautogui.moveTo(screenWidth/2, screenHeight/2, duration=num_seconds)
    '''

    key_list=[['6',1],['0',1],['enter',1]]
    press_keys(key_list)
    time.sleep(3)

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
            time.sleep(0.2)
            pyautogui.keyUp(key[0])
            time.sleep(0.3)

#模拟人工操作的方式导出东方财富数据
def export_dfcf_data(click_points,key_list):
    show_dfcf()
    ret=''
    #try:
    #click_fig("dfcfMenu\\cap_flow.png")
    #time.sleep(2)
    if True: #click_fig("dfcfMenu\\l2_cap_flow.png", 85):
        set_text_2_clipboard()
        for point in click_points[:-1]:
            pyautogui.click(point)

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
    show_dfcf()
    click_points=[
        [976,44],
        [976, 44],
        [976, 44],
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

#模拟人工操作的方式导出all实时资金流
def export_mystock2_real_capflow():
    show_dfcf()
    click_points=[
        [175,40],
        [178,692],  #178,692  second self stocks  119, 689
        [270, 62],
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
    show_dfcf()
    click_points=[
        [175,40],
        [175, 40],
        [119, 689],  #178,692  second self stocks
        [119, 689],  # 178,692  second self stocks
        [270, 62],
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
    show_dfcf()
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

def export_mystock_real_status():
    show_dfcf()
    click_points=[
        [175,40],
        [119, 689],
        [127, 62],
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

def export_allstock_real_status():
    show_dfcf()
    click_points=[
        [256,42],    #沪深排行
        [38, 128],  #沪深个股
        [127, 62],   #行情列表
        [127, 714],   # 沪深A股
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
    title=[item.decode('gbk') for item in data_list[0]]
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

    return  data_list

def read_real_capflow():
    real_status =export_allstock_real_capflow() # export_mystock_real_capflow()  # export_allstock_real_capflow():
    values = [u'序', u'最新', u'涨幅%', u'集合竞价', u'主力净流入',
              u'超大单净占比%', u'大单净占比%']

    real_status = format_dfcf_export_text(real_status, values)

    # 确定数值类型的字段序号
    values = [u'序', u'代码', u'最新', u'涨幅%', u'集合竞价', u'主力净流入',
              u'超大单净占比%', u'大单净占比%']
    title = [item.decode('gbk') for item in  real_status[0]]
    values_index = [title.index(value) for value in values]

    print(values)
    for line in   real_status[1:9]:
        display = [line[item] for item in values_index]
        print(display)

def read_real_status(all_stock=True):
    if all_stock:
        real_status = export_allstock_real_status()  # export_mystock_real_status()  #      export_real_capflow()
        values = u'序'
    else:
        real_status = export_mystock_real_status()  # export_real_capflow()
        values = u'初始'

    values=[values,u'代码', u'最新', u'涨幅%', u'涨跌', u'总手',
                   u'现手', u'买入价', u'卖出价', u'涨速%', u'换手%',
                   u'金额', u'市盈率', u'最高', u'最低', u'开盘',
                   u'昨收', u'量比', u'振幅%']

    non_values = [u'代码', u'名称', u' 所属行业']
    real_status = format_dfcf_export_text(real_status, '', non_values)

    # 确定数值类型的字段序号
    title = [item.decode('gbk') for item in real_status[0]]
    values_index = [title.index(value) for value in values]

    print(values)
    for line in real_status[1:9]:
        display = [line[item] for item in values_index]
        print(display)

    def read_real_capflow():
        real_status = export_mystock_real_capflow()  # export_real_capflow()
        values = [u'序', u'最新', u'涨幅%', u'集合竞价', u'主力净流入',
                  u'超大单净占比%', u'大单净占比%']

        real_status = format_dfcf_export_text(real_status, values)

        # 确定数值类型的字段序号
        values = [u'序', u'代码', u'最新', u'涨幅%', u'集合竞价', u'主力净流入',
                  u'超大单净占比%', u'大单净占比%']
        title = [item.decode('gbk') for item in real_status[0]]
        values_index = [title.index(value) for value in values]

        print(values)
        for line in real_status[1:9]:
            display = [line[item] for item in values_index]
            print(display)

#--------------main -------------------------------------
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

    read_real_capflow()
    read_real_status(True)
    read_real_status(False)

