# -*- coding: utf-8 -*-
'''
  基础模块，包括数据获取、整理，通用处理函数
  dfcf资金流信息的趋势算法太复杂，暂时无法理解，主力资金流信息暂时仅做参考20180330，改用基于ticks数据判断bs点

    史上最经典的K线搓揉线战法https://xueqiu.com/1764867941/83876556
，   http://www.360doc.com/content/17/0731/00/42629697_675595315.shtml
    先忽略个股所处位置、成交量配合等要求，只关注揉搓线这两根K线本身的特性，确定选股要求为
        1、前一日为长上影线K线，上影线长度/K线全长>0.7
        2、后一日为长下影线K线，下影线长度/K线全长>0.7



'''
from __future__ import print_function, absolute_import

import struct
import os
import pandas as pd
#import numpy  as np
#import matplotlib.pyplot as plt
#import sys
#from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import MultiCursor
from matplotlib.widgets import RectangleSelector
from pylab import *

from scipy import optimize
import datetime
import time
import talib
#import ui4backup    #ui interface
def write_log_msg():
    import traceback
    f = open("errorlog.txt", "w")
    f.write(traceback.format_exc())
    print(traceback.format_exc())

# ------------  gm3 ---------------------
try:
    from gm.api import *

    # 设置token
    set_token('c631be98d34115bd763033a89b4b632cef5e3bb1')
except:
    print('gm3 init error!!!!')
    write_log_msg()


#------------global varies
file_index=0


RISINGSUN_BUY = 1  # BUY
RISINGSUN_SELL = 2  # SELL

# 沪深300（SHSE.000300）、SHSE.000947 	内地银行  SHSE.000951 	300银行
#     上证50（SHSE.000016）
STOCK_BLOCK = 'SHSE.000300'

g_input_columns = 6 + 7

BUY_GATE = 7
SELL_GATE = 3
BUY_FEE = 1E-4
SELL_FEE = 1E-4
DAY_SECONDS = 24 * 60 * 60
g_max_step = 20000

g_max_stage = 11  # 持仓周期内收益等级
g_stage_rate = 1  # 2   if g_week>30 else 1#持仓周期内收益等级差

g_trade_minutes = 240

g_current_train_stop = 0  # 当前测试数据结束位置
g_test_stop = 0  # 当前实时数据结束位置
g_stock_current_price_list = 0

train_x = 0
train_y = 0

g_test_securities = ["SZSE.002415", "SZSE.000333", "SZSE.002460",
                     "SZSE.000001", "SZSE.002465", "SZSE.002466",
                     "SZSE.000651", "SZSE.000725", "SZSE.002152", "SZSE.000538", "SZSE.300072",
                     "SHSE.603288", "SHSE.600703", "SHSE.600271", "SHSE.600690", "SHSE.600585", "SHSE.600271",
                     "SHSE.600000", "SHSE.600519"]


# 标签数据生成，自动转成行向量 0-10共11级，级差1%
def make_stage(x):
    x = int(100 * x / g_stage_rate)
    if abs(x) < 5:
        x = x + 5
    elif x > 4:
        x = 10
    else:
        x = 0

    tmp = np.zeros(g_max_stage, dtype=np.int)
    tmp[x] = 1
    return tmp


# 获取测试集  步进为time_step的测试数据块,
# 与训练数据格式不一致、处理方式也不一致，预测周期越长越不准确
# 数据块不完整时必须用0补充完整
def get_test_data(data, normalized_data,
                  look_back_weeks=100):
    train_x, train_y = [], []
    start = look_back_weeks
    # for i in range(look_back_weeks, len(data)):
    for i in range(look_back_weeks, int(len(data))):
        x = normalized_data.iloc[start - look_back_weeks:start, :]
        y = data.iloc[start - look_back_weeks:start, 2]
        start += 1  # look_back_weeks

        train_x.append(x.values.tolist())

        # test_y.extend(y.values.tolist())
        train_y.append(y.values.tolist())

    return train_x, train_y


def create_market_data(stock, start_DateTime, stop_DateTime,
                       week=30, look_back_weeks=100,
                       hold_weeks=60):
    global g_market_train_data, g_input_columns, \
        g_normalized_data, g_max_step, train_x, train_y, g_current_train_stop

    g_market_train_data = read_kline(stock, int(week * 60),
                                     start_DateTime, stop_DateTime, 50000)  # 训练数据

    if len(g_market_train_data) == 0:
        return g_market_train_data

    # 预测look_back_weeks周期后的收益
    g_market_train_data['label'] = g_market_train_data['close'].pct_change(hold_weeks)
    g_market_train_data['label'] = g_market_train_data['label'].shift(-hold_weeks)
    # 将数据总项数整理成g_max_holding_weeks的整数倍
    # tmp = len(g_market_train_data)%g_max_holding_weeks+g_max_holding_weeks
    # g_market_train_data =g_market_train_data[tmp:]
    g_market_train_data['label'] = g_market_train_data['label'].fillna(0)
    g_market_train_data['label'] = g_market_train_data['label'].apply(make_stage)
    data_tmp = g_market_train_data.iloc[:, 1:-1]
    # todo  加入其他的技术分析指标

    data_tmp = add_ta_factors(data_tmp)
    # 数据归一化处理
    data_tmp = data_tmp.fillna(0)

    mean = np.mean(data_tmp, axis=0)
    std = np.std(data_tmp, axis=0)
    g_normalized_data = (data_tmp - mean) / std  # 标准化

    g_input_columns = len(data_tmp.columns)

    cols = ['eob', 'close', 'label', 'volume', 'amount']  # 买卖点分析需要量价信息
    g_market_train_data = g_market_train_data[cols]
    g_max_step = len(g_market_train_data)

    # 数据规整为look_back_weeks的整数倍
    # remainder=len(g_market_train_data)%look_back_weeks
    # g_market_train_data=g_market_train_data[remainder:]
    # g_normalized_data = g_normalized_data[remainder:]

    train_x, train_y = get_test_data(g_market_train_data,
                                     g_normalized_data, look_back_weeks)

    g_current_train_stop = 0
    return g_market_train_data


def create_market_last_n_data(stocks, count, stop_DateTime,
                              week=30, look_back_weeks=100):
    global g_stock_current_price_list, g_input_columns, \
        g_normalized_data, g_max_step, train_x, train_y

    market_train_data = read_last_n_kline(stocks, int(week * 60),
                                          count, stop_DateTime)  # 训练数据

    g_max_step = len(market_train_data)

    if g_max_step == 0:
        return
    g_stock_current_price_list = []
    train_x = []
    train_y = []

    # 以排序后的股票代码为序保存g_market_train_data['label'] = g_market_train_data['label'].apply(make_stage)
    for kline in market_train_data:
        stock, kdata = kline['code'], kline['kdata']

        data_tmp = kdata.iloc[:, 1:]
        # todo  加入其他的技术分析指标

        # 数据归一化处理
        mean = np.mean(data_tmp, axis=0)
        std = np.std(data_tmp, axis=0)
        g_normalized_data = (data_tmp - mean) / std  # 标准化

        g_input_columns = len(data_tmp.columns)

        cols = ['eob', 'close']
        g_stock_current_price_list.append({'code': stock, 'time_close': kdata[cols][-1:].values.tolist()})

        y = int(kdata['close'][len(kdata) - 1] * 100 / kdata['close'][0] - 100)
        train_x.append(g_normalized_data.values.tolist())
        # shape(?,g_max_tage)
        train_y.append([make_stage(y)])

def bcd_int2_date_str(data):
    ret="%02d"%(data%100)  #day
    data = int(data / 100)
    ret = "%02d-%s" % (data % 100, ret)  #month
    ret = "%04d-%s" % (data / 100, ret)  #year
    return ret

def bcd_int2_time_str(data):
    ret="%02d"%(data%100)  #second
    data=int(data/100)
    ret = "%02d:%s" % (data % 100, ret)  #minute
    ret = "%02d:%s" % (data / 100, ret)  #hour
    return ret



# utc 时间戳转换
def timestamp_datetime(ts):
    if isinstance(ts, (int, np.int64, float, str)):
        try:
            ts = int(ts)
        except ValueError:
            raise

        if len(str(ts)) == 13:
            ts = int(ts / 1000)
        if len(str(ts)) != 10:
            raise ValueError
    else:
        raise ValueError()

    return datetime.fromtimestamp(ts)


def datetime_timestamp(dt, type='ms'):
    if isinstance(dt, str):
        try:
            if len(dt) == 10:
                dt = datetime.strptime(dt.replace('/', '-'), '%Y-%m-%d')
            elif len(dt) == 19:
                dt = datetime.datetime.strptime(dt.replace('/', '-'), '%Y-%m-%d %H:%M:%S')
            else:
                raise ValueError()
        except ValueError as e:
            raise ValueError(
                "{0} is not supported datetime format." \
                "dt Format example: 'yyyy-mm-dd' or yyyy-mm-dd HH:MM:SS".format(dt)
            )

    if isinstance(dt, time.struct_time):
        dt = datetime.strptime(time.stftime('%Y-%m-%d %H:%M:%S', dt), '%Y-%m-%d %H:%M:%S')

    if isinstance(dt, datetime):
        if type == 'ms':
            ts = int(dt.timestamp()) * 1000
        else:
            ts = int(dt.timestamp())
    else:
        raise ValueError(
            "dt type not supported. dt Format example: 'yyyy-mm-dd' or yyyy-mm-dd HH:MM:SS"
        )
    return ts


'''
path: 
filename:文件名包含的子字符串，不支持通配符
onlyfile=True  是否仅返回文件名，不返回子目录名
'''
def get_code_in_cap_file(path, filename, minutes, onlyfile=True):
    lists = os.listdir(path)
    files = []

    if onlyfile == True:
        # only return file lists
        if len(filename) > 0:
            files = [file for file in lists if
                     file.find(filename) > -1 and file.find('.dat') > -1 and file.find(minutes) > -1]
            return files

    return lists


# //仅保留有用的信息
# typedef struct tagCAPITALFLOWMINISTRUCK {
#	int32_t	m_nDate, m_nTime;       //date /时间  2*4
#	double	m_dblSmallBuy, m_dblMidBuy, m_dblBigBuy, m_dblHugeBuy;   4*8
#	double	m_dblSmallSell, m_dblMidSell, m_dblBigSell, m_dblHugeSell;  4*8

def read_cap_flow(filepath):
    columns = ['eob',#''Date', 'Time',
               'SmallBuy', 'MidBuy', 'BigBuy', 'HugeBuy',
               'SmallSell', 'MidSell', 'BigSell', 'HugeSell',
               'SmallBuyVol', 'MidBuyVol', 'BigBuyVol', 'HugeBuyVol',
               'SmallSellVol', 'MidSellVol', 'BigSellVol', 'HugeSellVol']

    f = open(filepath, 'rb')
    dataSize = 168 # 2018-03-28后改为 72
    filedata = f.read()
    filesize = f.tell()
    f.close()

    tickCount = filesize / dataSize

    index = 0
    series = []
    last_cap = [0, 0]
    try:
        while filesize - index >= dataSize:
            # 仅取前18个字段
            cap = struct.unpack_from('2i8d8Q', filedata, index)
            index = index + dataSize

            if sum(cap[2:10]) >= 100.0:  # 去掉无交易数据
                eob=bcd_int2_date_str(cap[0])+ ' '+bcd_int2_time_str(cap[1])
                eob=datetime.datetime.strptime(eob, '%Y-%m-%d %H:%M:%S')
                # 由于前期数据保存软件设计的原因，数据可能存在重复读写的情况，要判断数据的有效性
                if cap[0] > last_cap[0] \
                        or (cap[0] == last_cap[0] and cap[1] > last_cap[1]):
                    series.append((eob,)+cap[2:])
                    last_cap = cap[:2]
                else:
                    # 出现数据重复,保留最新的数据
                    pass
    except:
        write_log_msg()
        pass
    caps = pd.DataFrame(series, columns=columns)
    return caps

'''
# 读取dfcf自选股信息
文件格式：首行空行，每个股票一行，首数字代表市场：0/3深圳、6上海，6位股票代码
002320
002341
603608
'''
def read_dfcf_selfstock_file(filename):
    f = open(filename, 'r')
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
                    if stock[0] != '6':
                        market = 'SZSE.'
                    else:
                        market = 'SHSE.'

                    stock_list.append(market + stock)

            tmp = tmp[i + 1:]
        except:
            break

    return stock_list

'''
# 读取平安证券导出自选股信息
文件格式：首行空行，每个股票一行，首数字代表市场：0深圳、1上海，后6位股票代码
0002320
0002341
1603608
1603808
'''
def read_pazq_selfstock_path(data_path='pazq'):
    files = get_filelist_from_path(data_path, '.EBK')

    stock_list=[]
    for file_path in files:
        f = open(file_path, 'r')
        tmp = f.read()
        f.close()
        while len(tmp)>0:
            try:
                if '\n' not in tmp:
                    i=len(tmp)
                else:
                    i=tmp.index('\n')

                if i>0:
                    stock=tmp[:i]
                    if stock not in stock_list:
                        if stock[0]=='0':
                            market='SZSE.'
                        else:
                            market = 'SHSE.'

                        stock_list.append(market+stock[1:])
                else:
                    stock=''

                tmp = tmp[i + 1:]
            except:
                break

    return stock_list



'''
    主力资金流总量均线多头向上判断：多头向上时返回true，否则false
        dataList 待计算数据
        maList 周期序列列表，最少三个周期,
        nLastWeeks最少程序周期数
        均线单调递增、多头排列
'''
def main_cap_up(data, maList, nLastWeeks):
    bRet = True
    ma = []
    CaclCount = sum(maList) * 2 + nLastWeeks
    count = len(data)

    while len(maList) >= 3 and count > CaclCount:
        tmp = data[-CaclCount:]
        # 计算每个周期的主力资金流变化情况
        mainflow = tmp['BigBuy'] + tmp['HugeBuy'] - tmp['BigSell'] - tmp['HugeSell']

        flow = mainflow.values
        # 累计主力总资金流
        total_flow = [flow[0]]
        for i in range(1, CaclCount):
            total_flow.append(total_flow[i - 1] + flow[i])

        # 分析资金流变化情况的均线趋势  按列排序并进行比较
        # '''
        for week in maList:
            tmp = mainflow.rolling(week).mean().tolist()[-nLastWeeks:]

            if tmp != sorted(tmp, reverse=False):  # 必须单调递增
                bRet = False
                break

            ma.append(tmp[-nLastWeeks - 1:])
        # '''

        # '''
        # 判断资金流近期趋势
        if bRet:
            show = False
            trends = cacl_data_trend(total_flow, count - 1, 0, maList[1], show)
            total = 0
            up = 0
            for trend in trends:
                total += len(trend)
                up += trend.count(True)

            if up / total < 0.8:
                bRet = False

        # '''
        break

    return bRet

#主力资金流变化趋势多头排列
def main_delta_cap_up(data, maList, nLastWeeks):
    bRet = False
    CaclCount = sum(maList) * 2 + nLastWeeks
    count = len(data)

    while len(maList) >= 3 and count >= CaclCount:
        tmp = data[-CaclCount:]
        # 计算每个周期的主力资金流变化情况
        mainflow = tmp['BigBuy'] + tmp['HugeBuy'] - tmp['BigSell'] - tmp['HugeSell']

        ma1 = mainflow.rolling(maList[0]).mean().tolist()[-nLastWeeks:]

        #if not cacl_data_trend(ma1,type=1,week=nLastWeeks):  #trends up
        #    break

        ma2 = mainflow.rolling(maList[1]).mean().tolist()[-nLastWeeks:]
        #if not cacl_data_trend(ma2,type=1,week=nLastWeeks):  #trends up
        #    break

        ma3 = mainflow.rolling(maList[2]).mean().tolist()[-nLastWeeks:]
        #if not cacl_data_trend(ma3,type=1,week=nLastWeeks):  #trends up
        #    break

        # 分析资金流变化情况的均线趋势  按列排序并进行比较
        for i in range(1, nLastWeeks):
            if  not (ma1[i] >= ma2[i] and ma2[i] >= ma3[i]  ):
                break

        if i==nLastWeeks-1:
            bRet=True

        break

    return bRet

'''
    均线多头向下判断：多头向下时返回true，否则false
        dataList 待计算数据
        maList 周期序列列表，最少三个周期,
        nLastWeeks最少程序周期数
        单调递减、空头排列
'''
def IsCAPMaDown(data, maList, nLastWeeks):
    bRet = True
    ma = []
    columns = []
    CaclCount = sum(maList) + nLastWeeks + 2

    while len(maList) >= 3 and len(data) > CaclCount:
        # 计算每个周期的主力资金流变化情况
        # data['mainflow']=data['BigBuy']+data['HugeBuy']-data['BigSell']-data['HugeSell']
        mainflow = data['BigBuy'] + data['HugeBuy'] - data['BigSell'] - data['HugeSell']
        # mainflow=data['BigBuy']+data['HugeBuy']-data['BigSell']-data['HugeSell']
        for week in maList:
            columns.append(str(week))
            tmp = mainflow.rolling(week).mean().tolist()[-nLastWeeks:]

            if tmp != sorted(tmp, reverse=True):  # 均值必须递减
                bRet = False
                break
            ma.append(tmp[-nLastWeeks - 1:])
        '''
        if bRet==True:
            #分析资金流变化情况的均线趋势  按列排序并进行比较
            #均值空头发散
            for index in range(nLastWeeks):
                for i in range(1,len(maList)):
                    if ma[i][index]>ma[i-1][index]:
                        bRet=False
                        break

            break
        else:
            break
        '''
        break

    return bRet


# //必须固定为17字节数据，采用结构体单字节对齐方式
# typedef struct tagL2TICKS {
#	int m_nTime, m_nIndex;       //时间、成交笔序号
#	int m_nPriceMul1000, m_nVols;//价格*1000，成交股数
#	char m_nBS;                  //成交方向：2买  1卖 0 竞价？
# }L2TICKS;
# nTime,nIndex,nPrice1000,nVol,cBS
def read_ticks(tickfilepath):
    columns = ['Time', 'Index', 'PriceMul1000', 'Vol', 'BS']
    f = open(tickfilepath, 'rb')
    filedata = f.read()
    filesize = f.tell()
    f.close()
    dataSize = 17
    tickCount = filesize / dataSize

    index = 0
    series = []

    while index < filesize:
        tick = struct.unpack_from('4i1c', filedata, index)
        series.append(tick)
        index = index + dataSize

    ticks = pd.DataFrame(series, columns=columns)
    return ticks

#todo 待测试研究ticks与5分钟数据的对应关系
'''
超大单：大于等于50万股或者100万元的成交单；
大单：大于等于10万股或者20万元且小于50万股和100万元的成交单；
中单：大于等于2万股或者4万元且小于10万股和20万元的成交单；
小单：小于2万股和4万元的成交单；
'''
def cacl_ticks_cap(tickspath='\data\ticks-000001-20180329.dat',cappath='\data\cap-000001-005.dat'):
    ticks=read_ticks(tickspath)
    capdata=read_cap_flow(cappath)
    tick_time=ticks.loc[0,'Time']
    ticks_date=datetime.datetime.strptime('2018-03-29 09:35:00', '%Y-%m-%d %H:%M:%S')
    i=len(capdata)-48*5
    while capdata.loc[i,'Date']!=ticks_date:
        i+=48
        if i>len(capdata):
            break

    if i < len(capdata):
        # data found


        '''
        columns = ['Time', 'Index', 'PriceMul1000', 'Vol', 'BS']
        超大单：大于等于50万股或者100万元的成交单；
        大单：大于等于10万股或者20万元且小于50万股和100万元的成交单；
        中单：大于等于2万股或者4万元且小于10万股和20万元的成交单；
        小单：小于2万股和4万元的成交单；
        '''
        tick_time=0
        for i in range(len(ticks)):
            if ticks.loc[i,'Time']-tick_time<5*60:
                tick_time=ticks.loc[i,'Time']
                #5分钟内的总成交量
                if ticks.loc[i,'Vol']>=500000\
                   or ticks.loc[i,'Vol']*ticks.loc[i,'PriceMul1000']/1000>=1e6:
                    if ticks.loc[i,'BS']==1:
                        huge_sell += ticks.loc[i, 'Vol']
                    else:
                        huge_buy+=ticks.loc[i,'Vol']
                elif ticks.loc[i,'Vol']>=100000\
                   or ticks.loc[i,'Vol']*ticks.loc[i,'PriceMul1000']/1000>=2e5:
                    if ticks.loc[i,'BS']==1:
                        big_sell += ticks.loc[i, 'Vol']
                    else:
                        big_buy+=ticks.loc[i,'Vol']
                elif ticks.loc[i,'Vol']>=20000\
                   or ticks.loc[i,'Vol']*ticks.loc[i,'PriceMul1000']/1000>=4e4:
                    if ticks.loc[i,'BS']==1:
                        mid_sell += ticks.loc[i, 'Vol']
                    else:
                        mid_buy+=ticks.loc[i,'Vol']
                else:
                    if ticks.loc[i,'BS']==1:
                        small_sell += ticks.loc[i, 'Vol']
                    else:
                        small_buy+=ticks.loc[i,'Vol']
            else:
                huge_buy = 0
                huge_sell = 0
                big_buy = 0
                big_sell = 0
                mid_buy = 0
                mid_sell = 0
                samll_buy = 0
                small_sell = 0

    pass


def get_backtest_start_date(start_date, look_back_dates):
    # 获取开始读取数据的开始位置  从训练结束时间倒退一年内的从交易日数据
    try:
        stop_day = str(start_date.date())
        start_day = str((start_date + datetime.timedelta(days=-365)).date())
        trade_dates = get_trading_dates('SHSE', start_day, stop_day)
        return trade_dates[-look_back_dates]
    except:
        write_log_msg()
        pass


'''
    利用掘金终端的函数读取指数的成份股
    stock_list :"SHSE.600000,SZSE.000001"
'''


def get_index_stock(index_symbol):
    # 连接本地终端时，td_addr为localhost:8001,
    if (True):
        try:
            css = get_constituents(index_symbol)
            css.sort()
            return css
        except:
            write_log_msg()
            pass


'''
    利用掘金终端的函数读取各市场的可交易标的
    exchange:
        上交所，市场代码 SHSE
        深交所，市场代码 SZSE
        中金所，市场代码 CFFEX
        上期所，市场代码 SHFE
        大商所，市场代码 DCE
        郑商所，市场代码 CZCE
        纽约商品交易所， 市场代码 CMX (GLN, SLN)
        伦敦国际石油交易所， 市场代码 IPE (OIL, GAL)
        纽约商业交易所， 市场代码 NYM (CON, HON)
        芝加哥商品期货交易所，市场代码 CBT (SOC, SBC, SMC, CRC)
        纽约期货交易所，市场代码 NYB (SGN)
    sec_type 	int 	代码类型:1 股票，2 基金，3 指数，4 期货，5 ETF
    is_active 	int 	当天是否交易：1 是，0 否

    Instrument
        交易代码数据类型
        class Instrument(object):
            def __init__(self):
                self.symbol = ''                ## 交易代码
                self.sec_type = 0               ## 代码类型
                self.sec_name = ''              ## 代码名称
                self.multiplier = 0.0           ## 合约乘数
                self.margin_ratio = 0.0         ## 保证金比率
                self.price_tick = 0.0           ## 价格最小变动单位
                self.upper_limit = 0.0          ## 当天涨停板
                self.lower_limit = 0.0          ## 当天跌停板
                self.is_active = 0              ## 当天是否交易
                self.update_time = ''           ## 更新时间


    stock_list :"SHSE.600000,SZSE.000001"
'''


def get_stock_by_market(exchange, sec_type, is_active, return_list=True):
    # 连接本地终端时，td_addr为localhost:8001,
    if (td.init('haigezyj@qq.com', 'zyj2590@1109', 'strategy_1') == 0):
        try:
            stock_list = ""
            css = md.get_instruments(exchange, sec_type, is_active)

            if return_list:
                stock_list = [cs.symbol for cs in css]
            else:
                for cs in css:
                    stock_list += "," + cs.symbol
            return stock_list[1:]
        except:
            write_log_msg()
            pass


'''
    利用掘金终端的函数读取指定股票最新价，用于统计当日当时价位情况
    stock_list :"SHSE.600000,SZSE.000001"
'''

'''
利用掘金终端的函数读取需要的K线数据:有时会丢个别K线数据
get_bars 提取指定时间段的历史Bar数据，支持单个代码提取或多个代码组合提取。策略类和行情服务类都提供该接口。
get_bars(symbol_list, bar_type, begin_time, end_time)
        参数名	类型	说明
        symbol_list	string	证券代码, 带交易所代码以确保唯一，如SHSE.600000，同时支持多只代码
        bar_type	int	bar周期，以秒为单位，比如60即1分钟bar
        begin_time	string	开始时间, 如2015-10-30 09:30:00
        end_time	string	结束时间, 如2015-10-30 15:00:00
return:dataframe  'eob','open','high','low','close','volume','amount'
返回值没有唯一的索引ID
'''
def read_kline(symbol_list, weeks_in_seconds,
               begin_time, end_time, max_record=50000):

    if (True):
        start_time = begin_time
        stop_time = end_time
        # 类结构体转成dataframe
        columns = ['eob', 'open', 'high', 'low', 'close', 'volume', 'amount']
        read_columns = 'eob, open, high, low, close, volume, amount'

        kdata = pd.DataFrame(columns=columns)

        while (True):
            # 返回结果是bar类数组
            try:
                if weeks_in_seconds == 240 * 60:
                    freq = '1d'
                else:
                    freq = '%ds' % (weeks_in_seconds)

                # 数据有时有问题，数据缺失
                bars = history(symbol_list, frequency=freq,
                               start_time=start_time, end_time=stop_time,
                               fields=read_columns,
                               adjust=1, df=True)[columns]

                if len(kdata) == 0:
                    kdata = bars.copy()
                else:
                    kdata = kdata.append(bars)
                    #重新建立唯一的ID索引
                    kdata = kdata.set_index('eob')
                    kdata=kdata.reset_index()

                count = len(bars)
                # TODO 一次最多处理10000项以内数据，超出应有所提示
                if (count <= 5 or len(kdata) > max_record) \
                        or (bars.iloc[count - 1, 0] >= stop_time) \
                        or (start_time == bars.iloc[count - 1, 0]):
                    break

                start_time = bars.iloc[count - 1, 0]
            except:
                write_log_msg()
                break
        return kdata


def read_kline_ts(symbol_list, weeks_in_seconds, begin_time, end_time, max_record=50000):
    if (True):
        # 类结构体转成dataframe
        kdata = []
        columns = ['eob', 'open', 'high', 'low', 'close', 'volume', 'amount']
        bars = 0

        is_daily = (weeks_in_seconds == 240 * 60)

        while (True):

            # 返回结果是bar类数组
            if is_daily:
                bars = md.get_dailybars(symbol_list, begin_time, end_time)
            else:
                bars = md.get_bars(symbol_list, weeks_in_seconds, begin_time, end_time)

            for bar in bars:
                if is_daily:
                    kdata.append([int(bar.utc_time),
                                  bar.open, bar.high, bar.close, bar.low,
                                  bar.volume, bar.amount])
                else:
                    kdata.append([int(bar.utc_endtime),
                                  bar.open, bar.high, bar.close, bar.low,
                                  bar.volume, bar.amount])

            count = len(bars)
            # TODO 一次最多处理10000项以内数据，超出应有所提示
            if (count == 0 or len(kdata) > max_record) \
                    or (not is_daily and bars[count - 1].strendtime >= end_time) \
                    or (is_daily and bars[count - 1].strtime >= end_time):
                break

            # print("read [%s] k line:%s count=%d" % (symbol_list,
            #        bars[0].strtime[:10] + ' ' + bars[0].strtime[11:19], count))

            if is_daily:
                if count <= 10:
                    break
                else:
                    begin_time = bars[count - 1].strtime[:10] \
                                 + ' ' + bars[count - 1].strtime[11:19]
            else:
                begin_time = bars[count - 1].strendtime[:10] \
                             + ' ' + bars[count - 1].strendtime[11:19]
        return pd.DataFrame(kdata, columns=columns)

def get_next_trade_date(date='2017-05-01'):
    return     get_next_trading_date(exchange='SZSE', date=date)

#获取最近1分钟的交易日期、时间
def get_last_trade_datetime():
    last_trade_date = history_n('SHSE.000001', '60s', 1,
            None, skip_suspended=True, df=True).loc[0, 'eob']
    return last_trade_date

def read_last_n_kline(stock, weeks_in_seconds, count, end_time=None):
    # 连接本地终端时，td_addr为localhost:8001,
    if True:
        is_daily = (weeks_in_seconds == 240 * 60)
        # 返回结果是bar类数组
        if is_daily:
            bars = history_n(stock,'1d', count, end_time,skip_suspended=True, df=True)
            last_trade_date = history_n('SHSE.000001','1d', 1, end_time,skip_suspended=True, df=True).loc[0,'eob']
        else:
            bars = history_n(stock,'%ds'% weeks_in_seconds, count, end_time,skip_suspended=True,df=True)
            last_trade_date = history_n('SHSE.000001', '%ds'% weeks_in_seconds, 1, end_time, skip_suspended=True, df=True).loc[0, 'eob']

        #丢弃停牌的股票
        if len(bars)>0 and bars.loc[len(bars)-1,'eob']==last_trade_date:
            return bars


def draw_cap_fig(cap_data, fig_id=312):
    plt.subplot(fig_id)
    count = len(cap_data)
    cols = [['HugeBuy', 'HugeSell'], ['BigBuy', 'BigSell'], ['MidBuy', 'MidSell'], ['SmallBuy', 'SmallSell']]
    colors = ['red', 'brown', 'green', 'blue']
    color = 0
    for buy, sell in cols:
        flow = (cap_data[buy] - cap_data[sell]).values
        item = buy[:-3]
        ma1 = [flow[0]]
        for i in range(1, count):
            ma1.append(ma1[i - 1] + flow[i])

        plt.plot(list(range(count)),
                 ma1, color=colors[color], label=item)

        color += 1

    plt.legend(loc='upper left', shadow=True, fontsize='x-large')



'''
    在价格走势图显示买卖点信息
'''
def draw_bs_on_kline(stock, kdata, buy_time, sell_time,
                     week=30, bs=False, hold_week=60, log_dir='.'):
    # 以折线图表示结果 figsize=(20, 15)
    try:
        reward = 0
        plt.figure(figsize=(16, 9))
        closing = kdata['close'].values
        data = closing.tolist()
        plt.ylabel('KDATA')
        plt.plot(list(range(len(kdata))),
                 data, color='b', label='close')

        # EMA 指数移动平均线  ma6跌破ma12连续若干周期
        ma6 = talib.EMA(closing, timeperiod=6)

        plt.plot(list(range(len(kdata))),
                 ma6, color='r', label='ma6')

        time_list = kdata['eob'].tolist()

        x = time_list.index(buy_time)
        buy_price = data[x]

        if buy_time == sell_time:
            # no sell time,sell on maxholding weeks
            if x + hold_week < len(time_list):
                sell_time = time_list[x + hold_week]
            else:
                sell_time = time_list[-1]

            no_sell = True
        else:
            no_sell = False

        plt.annotate(str(x), xy=(x, buy_price),
                     xytext=(x * 1.1, buy_price),
                     arrowprops=dict(facecolor='red', shrink=0.05),
                     )
        x = time_list.index(sell_time)
        sell_price = data[x]

        plt.annotate(str(x), xy=(x, sell_price),
                     xytext=(x * 0.9, sell_price),
                     arrowprops=dict(facecolor='green', shrink=0.05),
                     )
        # display start date,mid date and stop date
        x = 5
        date_high = min(closing)
        plt.annotate(str(time_list[x].date()), xy=(x, date_high),
                     xytext=(x, date_high),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     )

        x = int(len(time_list) / 2)
        plt.annotate(str(time_list[x].date()), xy=(x, date_high),
                     xytext=(x, date_high),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     )

        x = len(time_list) - 5
        plt.annotate(str(time_list[x].date()), xy=(x, date_high),
                     xytext=(x, date_high),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     )

        reward = int(sell_price * 100 / buy_price - 100)
        buy_time = buy_time.strftime('%Y-%m-%d %H-%M-%S')
        sell_time = sell_time.strftime('%Y-%m-%d %H-%M-%S')
        title = '%s week=%d reward=%d%%\n %s--%s' % (stock, week, reward, buy_time, sell_time)

        if no_sell:
            title = 'no sell ' + title

        plt.title(title)
    except:
        write_log_msg()
        pass

    plt.legend(loc='upper left', shadow=True, fontsize='x-large')

    if bs == False:
        file = '%s/%03d-%s-%s-%s.png' % (
            log_dir + '/fig', reward, stock, buy_time, sell_time)
    else:
        file = '%s/%03d-%s-%s-%s.png' % (
            log_dir + '/bs_fig', reward, stock, buy_time, sell_time)
    plt.savefig(file)
    plt.close()

    return reward

#技术分析可视化界面
#逐步增加处理，操作图形显示的内容，实现人机交互
#K线、RSI和主力资金变化均处于多头，且RSI处于安全范围【45-85】
def draw_stock_ta_fig(stock, ma, kdata, cap_data,
                              kweek, hold_week,rsi_low, rsi_up,
                              bs, fig_count,bs_msg):

    fig = plt.figure(figsize=(12, 6))



    left_space = 0.10
    widgets_start = 0.025
    widgets_hight = 0.04
    my_cmd_x = left_space * 2
    my_cmd_width = 0.05

    plt.subplots_adjust(wspace=0, hspace=0, left=left_space, bottom=widgets_hight * 3)


    #TODO  RECT SELECTION AND ZOOM
    def rect_select_callback(eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        print("33(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
        print(" The button you used were: %s %s" % (eclick.button, erelease.button))

    def toggle_selector(event):
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and toggle_selector.RS.active:
            print(' RectangleSelector deactivated.')
            toggle_selector.RS.set_active(False)
        if event.key in ['A', 'a'] and not toggle_selector.RS.active:
            print(' RectangleSelector activated.')
            toggle_selector.RS.set_active(True)


    # 计算主力资金的累计值
    def cacl_main_cap_total(cap_data):
        count = len(cap_data)
        cols = [['HugeBuy', 'HugeSell'], ['BigBuy', 'BigSell']]  # , ['MidBuy', 'MidSell'], ['SmallBuy', 'SmallSell']]
        total_flow = [0 for i in range(count)]

        flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + \
                      cap_data['BigBuy'] - cap_data['BigSell']).values

        total_flow[0]=flow[0]

        for i in range(1, count):
            total_flow[i]=(total_flow[i - 1] + flow[i])

        return total_flow

    def draw_rsi(kdata, ax, rsi_low=30, rsi_up=70):
        count = len(kdata)
        ax.set_ylabel('RSI')
        closing = kdata['close'].values
        # RSI
        RSI5 = talib.RSI(closing, timeperiod=5)
        RSI10 = talib.RSI(closing, timeperiod=10)
        RSI26 = talib.RSI(closing, timeperiod=26)

        ax.plot(list(range(count)),
                 RSI5, color='gray', label='RSI5')

        ax.plot(list(range(count)),
                RSI10, color='blue', label='RSI10')

        ax.plot(list(range(count)),
                RSI26, color='red', label='RSI26')

        ax.plot(list(range(count)),
                 [rsi_up for i in range(count)], color='yellow',label='U'+str(rsi_up))
        ax.plot(list(range(count)),
                 [rsi_low for i in range(count)], color='green',label='D'+str(rsi_low))

        ax.legend(loc='upper left', shadow=True, fontsize='x-large')

    #
    def draw_cap_main(cap_data,week,fig_id=313, draw_delta=False):
        min_week_of_trend = 60
        ax = plt.subplot(fig_id)
        count = len(cap_data)
        flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell'])

        if draw_delta == False:
            flow = flow.values
            plt.ylabel('MAIN CAP')
            # 累计主力总资金流
            total_flow = [flow[0]]
            for i in range(1, count):
                total_flow.append(total_flow[i - 1] + flow[i])

            plt.plot(list(range(count)),
                     total_flow, color='brown')

            ax1 = ax.twinx()
            ax1.plot(list(range(count)), flow)
            # cacl_data_trend(total_flow, buy_point,
            #               sell_point, min_week_of_trend + 1, True)

            # 计算累计主力资金的趋势  曲线拟合：上升、下行两种状态

        else:
            plt.ylabel('MAIN DELTA')

            ma5 = flow.rolling(week).mean().tolist()
            ma10 = flow.rolling(week*2).mean().tolist()
            plt.plot(list(range(count)),
                     flow, color='gray', label='delta')

            plt.plot(list(range(count)), [0 for _ in range(count)], color='black')

            plt.plot(list(range(count)), ma5, color='red', label='ma' + str(week))
            plt.plot(list(range(count)), ma10, color='blue', label='ma' + str(week*2))

            plt.legend(loc='upper left', shadow=True, fontsize='x-large')

            #ax1 = ax.twinx()
            #ax1.plot(list(range(count)), ma5, color='red', label='ma5')
            #ax1.plot(list(range(count)), ma10, color='blue', label='ma' + str(week))

            #ax1.legend(loc='upper left', shadow=True, fontsize='x-large')

        return ax

    def draw_kline(stock, cap_data,kdata,stage_days, bs,
                   week,kweek, hold_week, ax, main_flow=None,title_msg=''):


        #ax = plt.subplot(fig_id)
        ax2 = ax
        ax = ax2.twinx()

        count = len(kdata)
        ax.clear()
        ax.set_ylabel('PRICE')

        closing = kdata['close']
        week2=week*2
        ma1=closing.rolling(week).mean()
        ma2 = closing.rolling(week2).mean()
        closing = closing.values

        data = closing.tolist()

        try:
            time_list = kdata['eob'].tolist()
        except:
            write_log_msg()
            reward = 0

        # 只用图形显示收益差距很大的情况
        # if reward<disp_high and reward>disp_low:
        #    return  reward

        ax.plot(list(range(count)),
                 data, color='blue', label='close')

        ax.plot(list(range(count)),
                 ma1, color='red', label=str(week))
        ax.plot(list(range(count)),
                 ma2, color='black', label=str(week2))

        msg=''
        #阶段新高、新低检测
        high_low_list=check_stage_high_low(kdata,
                    stage_days)

        for week,index,fig_type in high_low_list:
            ax.plot(index,data[index]*1.02, fig_type)
            if fig_type=='rx':
                msg+="(%d,%d)high,"%(week,index)
            else:
                msg += "(%d,%d)low," % (week, index)


        washing=check_washing_stock(kdata,len(kdata)-min(stage_days)) #stage_days[0])
        if len(washing)>0:
            for index,fig_type in washing:
                ax.plot(index,data[index]*1.02, fig_type)
                msg += "(%d)wash," % (index)


        #买卖点信息20180506  ????  display error
        for sell,buy in bs:
            ax.plot(buy, data[buy] , 'go')
            ax.plot(sell, data[sell], 'ro')


        title = '%s,week=%d,%s\n' % (stock, kweek,time_list[-1].strftime('%Y-%m-%d %H-%M-%S'))
        ax.legend(loc='upper left', shadow=True, fontsize='x-large')

        if len(msg)>1:
            title+=msg

        if len(title_msg)>1:
            title+='\n'+title_msg

        ax.set_title(title)

        if main_flow != None:
            ax2.plot(list(range(count)), main_flow, 'brown',lw=3)
            ax2.set_ylabel('main total flow')
            ax.format_coord = format_coord1
        else:
            ax2.format_coord = format_coord1


    #self define status
    def format_coord1(x, y):
        col = int(x + 0.5)
        if col >= len(kdata) or col < 1:
            return 'x=%d, y=%1.4f' % (col, y)

        row = int(y + 0.5)

        return 'kline %s,x=%d, y=%1.4f' % (kdata.loc[col-1,'eob'].strftime('%Y-%m-%d %H-%M-%S'),col, y)

    def format_coord2(x, y):
        col = int(x + 0.5)
        if col >= len(kdata) or col < 1:
            return 'x=%d, y=%1.4f' % (col, y)

        row = int(y + 0.5)

        return 'vol %s,x=%d, y=%1.4f' % (kdata.loc[col-1,'eob'].strftime('%Y-%m-%d %H-%M-%S'),col, y)

    def format_coord3(x, y):
        col = int(x + 0.5)
        if col >= len(kdata) or col < 1:
            return 'x=%d, y=%1.4f' % (col, y)

        row = int(y + 0.5)

        return 'main delta %s,x=%d, y=%1.4f' % (kdata.loc[col-1,'eob'].strftime('%Y-%m-%d %H-%M-%S'),col, y)

    def format_coord4(x, y):
        col = int(x + 0.5)
        if col>=len(kdata) or col<1:
            return 'x=%d, y=%1.4f' % (col, y)

        row = int(y + 0.5)

        return 'rsi %s,x=%d, y=%1.4f' % (kdata.loc[col-1,'eob'].strftime('%Y-%m-%d %H-%M-%S'),col, y)

    #todo 结合ticks分析成交量的组成，特别是主力资金的占比
    def draw_vol(kdata, week, fig_id=515, cap_data=[]):
        count = len(kdata)
        ax = plt.subplot(fig_id)

        vol = kdata['amount']/1e6  #amount volume
        x = list(range(count))
        plt.plot(x, vol, color='black', label='vol')
        plt.ylabel('VOLx1E6')

        msg=''
        # 主力大单突变点计算与显示
        vol_changes = vol_big_change(cap_data, kdata, week)
        for index, fig_type in vol_changes:
            try:
                ax.plot(index, vol[index], fig_type)
                if index>count-10:
                    if fig_type=='go':
                        msg+=",%d big buy"%index
                    else:
                        msg += ",%d big sell" % index
            except:
                write_log_msg()
                break
        #ma = vol.rolling(week).mean()
        #plt.plot(x, ma, color='black', label='ma', lw=2)

        if len(cap_data) > 0:
            cols = [['HugeBuy', 'HugeSell'], ['BigBuy', 'BigSell'], ['MidBuy', 'MidSell'], ['SmallBuy', 'SmallSell']]
            cols_vol = [['HugeBuyVol', 'HugeSellVol'], ['BigBuyVol', 'BigSellVol'],
                    ['MidBuyVol', 'MidSellVol'], ['SmallBuyVol', 'SmallSellVol']]
            colors = ['red', 'yellow', 'green', 'blue']

            #data normorise
            amt_rate = 1e7  # 单位：千万元amt_
            vol_rate = 1e6  # 单位：百万股，万手
            cap_data['vol'] = 0    #总成交量
            cap_data['amt'] = 0.0  #总金额
            for i in range(len(cols)):
                buy=cols[i][0]
                sell = cols[i][1]
                item = buy[:-3]  # flow name
                cap_data[buy] = cap_data[buy] / amt_rate
                cap_data[sell] = cap_data[sell] / amt_rate
                cap_data['amt']=cap_data['amt']+cap_data[buy]
                cap_data[item] = (cap_data[buy] - cap_data[sell])  #净流量

                buy = cols_vol[i][0]
                sell = cols_vol[i][1]
                cap_data[buy] = cap_data[buy] / vol_rate
                cap_data[sell] = cap_data[sell] / vol_rate
                #cap_data['vol'] = cap_data['vol'] + cap_data[buy]
                #cap_data[item+'_vol'] = (cap_data[buy] - cap_data[sell])  # 净买量

            ax2 = ax.twinx()
            ax2.set_ylabel('main flow delta')
            color = 0
            for buy, sell in cols:
                # 计算4种资金流的累计值
                item = buy[:-3]  # flow name
                flow = (cap_data[buy]-cap_data[sell]).values
                for i in range(1, count):
                    flow[i]=flow[i]+flow[i-1]

                ax2.plot(list(range(count)),
                         flow, color=colors[color], label=item)
                color += 1

            ax2.legend(loc='upper left', shadow=True, fontsize='x-large')
            ax2.format_coord=format_coord2
        else:
            ax.format_coord = format_coord2

        #cols=['Date', 'Time','vol','amt','Huge','Big','Huge_vol','Big_vol']
        #tmp=cap_data[cols]
        return msg

    #成交量突变检测
    def vol_big_change(cap_data,kdata,week):
        main_flow = cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']
        #main_flow = main_flow.rolling(5).mean()

        # 检查成交量突破点位置  index values访问数据
        vol = kdata['volume']
        ma=vol.rolling(week*5).mean()
        poi = vol[vol > ma * 3]

        change_list=[]

        try:
            for i in range(len(poi)):
                index = poi.index[i]
                value = poi.values[i]
                if index < week:
                    continue

                if main_flow[index] > 0:
                    # 主力介入
                    change_list.append([index,'go'])
                    #plt.plot(x[index], vol[index], 'go')
                else:
                    # 主力退出
                    change_list.append([index, 'ro'])
                    #plt.plot(x[index], vol[index], 'ro')
        except:
            write_log_msg()
            pass
        return  change_list

    # 按钮clicked事件处理函数
    def my_cmd(event):
        print('botton clicked')

    def press(event):
        sys.stdout.flush()

        if event.key == 'x':

            # 其他处理函数
            fig.canvas.draw()

    #阶段高低检测  回看周期数可选
    # 返回结果：week，Index，‘high/low’
    def check_stage_high_low(kdata,weeks=[30,60,90]):
        ret=[]
        data_len=len(kdata)

        for i in range(data_len-min(weeks),data_len):
            cur_high = kdata.loc[i - 1, 'high']
            cur_low = kdata.loc[i - 1, 'low']
            for week in weeks:
                high=max(kdata.loc[i-week:i,'high'])
                low= min(kdata.loc[i-week:i,'low'])
                if high==cur_high:
                    ret.append([week,i,'rx'])
                elif cur_low==low:
                    ret.append([week, i, 'gx'])

        return ret

    #基于搓揉线的洗盘、见顶检测  很少见到，机会似乎不多
    #   1、前一日为长上影线K线，上影线长度 / K线全长 > 0.7
    #   2、后一日为长下影线K线，下影线长度 / K线全长 > 0.7
    def check_washing_stock(kdata,start=20):
        data_len=len(kdata)
        washing_index=[]  # 洗盘点
        for i in range(start,data_len-1):
            try:
                k_hight=kdata.loc[i-1,'high']-kdata.loc[i-1,'low']
                #阳线
                if kdata.loc[i-1,'close']-kdata.loc[i-1,'open']>0:
                    k_hight=(kdata.loc[i-1, 'high'] - kdata.loc[i-1, 'close'])/k_hight
                    if k_hight>0.7:
                        k_low=kdata.loc[i,'high']-kdata.loc[i,'low']
                        ll=min(kdata.loc[i, 'close'],kdata.loc[i, 'open'] )- kdata.loc[i, 'low']
                        #不论阴阳
                        if ll>0.01:
                            k_low = (ll)/k_low
                            if k_low>0.7:
                                washing_index.append([i,'bo'])
            except:
                write_log_msg()
                pass
        return  washing_index

    def start():
        pass

    #FUNCTION STARTS..............................


    # 部件显示位置及颜色
    axcolor = 'lightgoldenrodyellow'
    my_cmd_ax = plt.axes([my_cmd_x, widgets_start,
                         my_cmd_width, widgets_hight ])

    button = Button(my_cmd_ax, 'Reset', color=axcolor, hovercolor='0.975')

    button.on_clicked(my_cmd)

    fig.canvas.mpl_connect('key_press_event', press)
    ax1 = fig.add_subplot(4, 1, 1)
    ax2 = fig.add_subplot(4, 1, 2)
    ax3 = fig.add_subplot(4, 1, 3)
    ax4 = fig.add_subplot(4, 1, 4)

    # drawtype is 'box' or 'line' or 'none'
    toggle_selector.RS = RectangleSelector(ax1, rect_select_callback,
                                           drawtype='box', useblit=True,
                                           button=[1, 3],  # don't use middle button
                                           minspanx=5, minspany=5,
                                           spancoords='pixels',
                                           interactive=True)

    plt.connect('key_press_event', toggle_selector)

    week_in_day = int(240 / kweek)
    hold_week = int(10 * week_in_day)
    analyse_week=5
    total_flow = cacl_main_cap_total(cap_data)
    data_len=len(kdata)

    #阶段高低检测周期数
    stage_days=[5,10,20]

    if len(bs_msg)>0:
        title_msg=bs_msg+'\n'
    else:
        title_msg=''



    # 绘制volume图
    title_msg +=draw_vol(kdata= kdata, week=analyse_week,fig_id= ax2,cap_data= cap_data)
    # 主力资金总趋势
    draw_cap_main(cap_data= cap_data, week=analyse_week,fig_id= ax3,draw_delta= True)

    # 绘制RSI图
    draw_rsi(kdata,ax4,rsi_low, rsi_up)

    draw_kline(stock=stock,cap_data= cap_data,kdata= kdata,kweek=kweek,stage_days= stage_days,
               bs=bs, week= analyse_week,hold_week= hold_week,ax= ax1,
               main_flow= total_flow,title_msg=  title_msg)

    multi = MultiCursor(fig.canvas, (ax1, ax2, ax3,ax4), color='r', lw=1)

    ax3.format_coord = format_coord3
    ax4.format_coord = format_coord4

    plt.show()

# 判断当前走势能否买入？
# todo use tf model to decice the buy-sell point
def can_buy(kdata, ma_list=[6,12,26], week=3, rsi_low=45, rsi_up=75):
    ret = False
    closing = kdata['close'].fillna(0)

    while not ret:
        # 均线多头发散  trends up
        ma1 = closing.rolling(ma_list[0]).mean().tolist()[-week:]
        if not cacl_data_trend(data=ma1,week=week):
            break

        ma2 = closing.rolling(ma_list[1]).mean().tolist()[-week:]
        #if not cacl_data_trend(data=ma2, week=week):
        #    break

        ma3 = closing.rolling(ma_list[2]).mean().tolist()[-week:]
        #if not cacl_data_trend(data=ma3, week=week):
        #    break

        if  ma1[-2] < ma1[-1]:
            for i in range(week):
                if not(ma1[i] >= ma2[i]):
                    break
        else:
            break

        if i < week - 1:
            break

        # RSI  多头且必须单调递增
        closing = kdata['close'].fillna(0).values
        RSI5 = talib.RSI(closing, timeperiod=5).tolist()[-week:]
        if not cacl_data_trend(data=RSI5, week=week):  # 必须单调递增
            break

        RSI10 = talib.RSI(closing, timeperiod=10).tolist()[-week:]
        #if not cacl_data_trend(data=RSI10, week=week):  # 必须单调递增
        #    break

        RSI26 = talib.RSI(closing, timeperiod=26).tolist()[-week:]
        #if not cacl_data_trend(data=RSI26, week=week):  # 必须单调递增
        #    break

        #long trends
        if  RSI5[-2] < RSI5[-1] and RSI10[-2] < RSI10[-1]:
            for i in range(1, week):
                if  (RSI5[i]>=rsi_low and RSI5[i]<=rsi_up and RSI5[i] >= RSI10[i]) :
                    pass
                else:
                    break

        else:
            break

        if i < week - 1:
            break

        ret = True

    return ret

def can_sell(kdata, ma_list=[6,12,26], week=3, rsi_low=45, rsi_up=85):
    ret = False
    closing = kdata['close'].fillna(0)

    while not ret:
        # 均线short头发散  trends down
        ma1 = closing.rolling(ma_list[0]).mean().tolist()[-week:]
        #if  cacl_data_trend(data=ma1,week=week):
        #    break

        ma2 = closing.rolling(ma_list[1]).mean().tolist()[-week:]

        ma3 = closing.rolling(ma_list[2]).mean().tolist()[-week:]
        closing=closing[-week:].tolist()

        #short trends or closing below ma1
        for i in range(week):
            if ma1[i] >= ma2[i] or closing[i]>=ma1[i]:
                break

        if i < week - 1:
            break

        ret = True

    return ret

def stop_loss(kdata, start, buy_point, stop):
    data = np.double(kdata[start:stop]['close'])
    cost = kdata.loc[buy_point, 'close']

    max_price = max(data[buy_point - start:stop])

    cur_price = data[-1]
    # 持仓后最大跌幅大于15% 或者涨幅大于30% or cur_price/cost>1.35,或者亏损超过9%，暂时清仓
    if cur_price / cost < 0.9 or cur_price / max_price < 0.85:
        ret = True
    else:
        ret = False

    return ret


# 基于talib产生每个周期的技术指标因子
def add_ta_factors(kdata):
    opening = kdata['open'].values
    closing = kdata['close'].values
    highest = kdata['high'].values
    lowest = kdata['low'].values
    # volume = np.double(kdata['volume'].values)
    tmp = kdata

    # RSI
    tmp['RSI1'] = talib.RSI(closing, timeperiod=6)
    tmp['RSI2'] = talib.RSI(closing, timeperiod=14)
    tmp['RSI3'] = talib.RSI(closing, timeperiod=26)
    # SAR 抛物线转向
    tmp['SAR'] = talib.SAR(highest, lowest, acceleration=0.02, maximum=0.2)

    # MACD
    tmp['MACD_DIF'], tmp['MACD_DEA'], tmp['MACD_bar'] = \
        talib.MACD(closing, fastperiod=12, slowperiod=24, signalperiod=9)

    '''
    # EMA 指数移动平均线
    tmp['EMA6'] = talib.EMA(closing, timeperiod=6)
    tmp['EMA12'] = talib.EMA(closing, timeperiod=12)
    tmp['EMA26'] = talib.EMA(closing, timeperiod=26)
    # OBV 	能量潮指标（On Balance Volume，OBV），以股市的成交量变化来衡量股市的推动力，
    # 从而研判股价的走势。属于成交量型因子
    tmp['OBV'] = talib.OBV(closing, volume)

        # 中位数价格 不知道是什么意思
    tmp['MEDPRICE'] = talib.MEDPRICE(highest, lowest)

    # 负向指标 负向运动
    tmp['MiNUS_DI'] = talib.MINUS_DI(highest, lowest, closing, timeperiod=14)
    tmp['MiNUS_DM'] = talib.MINUS_DM(highest, lowest, timeperiod=14)

    # 动量指标（Momentom Index），动量指数以分析股价波动的速度为目的，研究股价在波动过程中各种加速，
    # 减速，惯性作用以及股价由静到动或由动转静的现象。属于趋势型因子
    tmp['MOM'] = talib.MOM(closing, timeperiod=10)

    # 归一化平均值范围
    tmp['NATR'] = talib.NATR(highest, lowest, closing, timeperiod=14)
    # PLUS_DI 更向指示器
    tmp['PLUS_DI'] = talib.PLUS_DI(highest, lowest, closing, timeperiod=14)
    tmp['PLUS_DM'] = talib.PLUS_DM(highest, lowest, timeperiod=14)

    # PPO 价格振荡百分比
    tmp['PPO'] = talib.PPO(closing, fastperiod=6, slowperiod=26, matype=0)

    # ROC 6日变动速率（Price Rate of Change），以当日的收盘价和N天前的收盘价比较，
    # 通过计算股价某一段时间内收盘价变动的比例，应用价格的移动比较来测量价位动量。属于超买超卖型因子。
    tmp['ROC6'] = talib.ROC(closing, timeperiod=6)
    tmp['ROC20'] = talib.ROC(closing, timeperiod=20)
    # 12日量变动速率指标（Volume Rate of Change），以今天的成交量和N天前的成交量比较，
    # 通过计算某一段时间内成交量变动的幅度，应用成交量的移动比较来测量成交量运动趋向，
    # 达到事先探测成交量供需的强弱，进而分析成交量的发展趋势及其将来是否有转势的意愿，
    # 属于成交量的反趋向指标。属于成交量型因子
    tmp['VROC6'] = talib.ROC(volume, timeperiod=6)
    tmp['VROC20'] = talib.ROC(volume, timeperiod=20)

    # ROC 6日变动速率（Price Rate of Change），以当日的收盘价和N天前的收盘价比较，
    # 通过计算股价某一段时间内收盘价变动的比例，应用价格的移动比较来测量价位动量。属于超买超卖型因子。
    tmp['ROCP6'] = talib.ROCP(closing, timeperiod=6)
    tmp['ROCP20'] = talib.ROCP(closing, timeperiod=20)
    # 12日量变动速率指标（Volume Rate of Change），以今天的成交量和N天前的成交量比较，
    # 通过计算某一段时间内成交量变动的幅度，应用成交量的移动比较来测量成交量运动趋向，
    # 达到事先探测成交量供需的强弱，进而分析成交量的发展趋势及其将来是否有转势的意愿，
    # 属于成交量的反趋向指标。属于成交量型因子
    tmp['VROCP6'] = talib.ROCP(volume, timeperiod=6)
    tmp['VROCP20'] = talib.ROCP(volume, timeperiod=20)

    # 累积/派发线（Accumulation / Distribution Line，该指标将每日的成交量通过价格加权累计，
    # 用以计算成交量的动量。属于趋势型因子
    tmp['AD'] = talib.AD(highest, lowest, closing, volume)

    # 佳庆指标（Chaikin Oscillator），该指标基于AD曲线的指数移动均线而计算得到。属于趋势型因子
    tmp['ADOSC'] = talib.ADOSC(highest, lowest, closing, volume, fastperiod=3, slowperiod=10)

    # 平均动向指数，DMI因子的构成部分。属于趋势型因子
    tmp['ADX'] = talib.ADX(highest, lowest, closing, timeperiod=14)

    # 相对平均动向指数，DMI因子的构成部分。属于趋势型因子
    tmp['ADXR'] = talib.ADXR(highest, lowest, closing, timeperiod=14)

    # 绝对价格振荡指数
    tmp['APO'] = talib.APO(closing, fastperiod=12, slowperiod=26)

    # Aroon通过计算自价格达到近期最高值和最低值以来所经过的期间数，
    # 帮助投资者预测证券价格从趋势到区域区域或反转的变化，
    # Aroon指标分为Aroon、AroonUp和AroonDown3个具体指标。属于趋势型因子
    tmp['AROONDown'], tmp['AROONUp'] = talib.AROON(highest, lowest, timeperiod=14)
    tmp['AROONOSC'] = talib.AROONOSC(highest, lowest, timeperiod=14)


    # 均幅指标（Average TRUE Ranger），取一定时间周期内的股价波动幅度的移动平均值，
    # 是显示市场变化率的指标，主要用于研判买卖时机。属于超买超卖型因子。
    tmp['ATR14'] = talib.ATR(highest, lowest, closing, timeperiod=14)
    tmp['ATR6'] = talib.ATR(highest, lowest, closing, timeperiod=6)

    # 布林带
    tmp['Boll_Up'], tmp['Boll_Mid'], tmp['Boll_Down'] = \
        talib.BBANDS(closing, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    # 均势指标
    tmp['BOP'] = talib.BOP(opening, highest, lowest, closing)

    # 5日顺势指标（Commodity Channel Index），专门测量股价是否已超出常态分布范围。属于超买超卖型因子。
    tmp['CCI5'] = talib.CCI(highest, lowest, closing, timeperiod=5)
    tmp['CCI10'] = talib.CCI(highest, lowest, closing, timeperiod=10)
    tmp['CCI20'] = talib.CCI(highest, lowest, closing, timeperiod=20)
    tmp['CCI88'] = talib.CCI(highest, lowest, closing, timeperiod=88)

    # 钱德动量摆动指标（Chande Momentum Osciliator），与其他动量指标摆动指标如
    # 相对强弱指标（RSI）和随机指标（KDJ）不同，
    # 钱德动量指标在计算公式的分子中采用上涨日和下跌日的数据。属于超买超卖型因子
    tmp['CMO_Close'] = talib.CMO(closing, timeperiod=14)
    tmp['CMO_Open'] = talib.CMO(opening, timeperiod=14)

    # DEMA双指数移动平均线
    tmp['DEMA6'] = talib.DEMA(closing, timeperiod=6)
    tmp['DEMA12'] = talib.DEMA(closing, timeperiod=12)
    tmp['DEMA26'] = talib.DEMA(closing, timeperiod=26)

    # DX 动向指数
    tmp['DX'] = talib.DX(highest, lowest, closing, timeperiod=14)

    # KAMA 适应性移动平均线
    tmp['KAMA'] = talib.KAMA(closing, timeperiod=30)

    # TEMA
    tmp['TEMA6'] = talib.TEMA(closing, timeperiod=6)
    tmp['TEMA12'] = talib.TEMA(closing, timeperiod=12)
    tmp['TEMA26'] = talib.TEMA(closing, timeperiod=26)

    # TRANGE 真实范围
    tmp['TRANGE'] = talib.TRANGE(highest, lowest, closing)

    # TYPPRICE 典型价格
    tmp['TYPPRICE'] = talib.TYPPRICE(highest, lowest, closing)

    # TSF 时间序列预测
    tmp['TSF'] = talib.TSF(closing, timeperiod=14)

    # ULTOSC 极限振子
    tmp['ULTOSC'] = talib.ULTOSC(highest, lowest, closing, timeperiod1=7, timeperiod2=14, timeperiod3=28)

    # 威廉指标
    tmp['WILLR'] = talib.WILLR(highest, lowest, closing, timeperiod=14)
    '''
    return tmp


def feed_dict(train):
    global g_current_train_stop
    try:
        xs = train_x[g_current_train_stop]
        ys = train_y[g_current_train_stop]
    except:
        write_log_msg()
        print('error in feed_dict %d' % (g_current_train_stop))

    # todo  数据取完后如何处理？  直接退出运行,需支持对未来收益的预测
    if train:
        g_current_train_stop += 1
    else:
        k = 1.0

    return xs, ys


'''
图形化显示标的走势
'''


def draw_figure(data1, data2=None, title=''):
    # 以折线图表示结果 figsize=(20, 15)
    plt.figure()
    plot_predict = plt.plot(list(range(len(data1))),
                            data1, color='b', label='predict')
    if data2 != None:
        plot_test_y = plt.plot(list(range(len(data2))),
                               data2, color='r', label='true')

    legend = plt.legend(loc='upper right', shadow=True, fontsize='x-large')

    if len(title) > 0:
        plt.title(title)

    # plt.show()

    return plt


def show_BS(plt, point, price, is_buy=True, title=''):
    if is_buy:
        plt.annotate('b', xy=(point, price),
                     xytext=(point * 1.1, price),
                     arrowprops=dict(facecolor='red', shrink=0.05),
                     )
    else:
        plt.annotate('s', xy=(point, price),
                     xytext=(point * 0.9, price),
                     arrowprops=dict(facecolor='green', shrink=0.05),
                     )

    if len(title) > 0:
        plt.title(title)


def get_block_stock_list(stock_block):
    return get_index_stock(stock_block)

#从板块组合找出股票列表，进行重复股票代码检测
# 预先选定的集合favorte_stocks
def get_stocks_form_blocks(blocks,favorite_stocks=[]):
    stock_list=[]
    check_favorite=len(favorite_stocks)>0
    for block in blocks:
        stocks=get_block_stock_list(block)

        for stock in stocks:
            # 不在预先选定的集合股票不做处理
            if check_favorite:
                if not stock[5:] in favorite_stocks:
                    continue

            if not stock in stock_list:
                stock_list.append(stock)

    return  stock_list

# 20151206 110507 -->'2015-12-06 11:05:07'
def int2_datetime_str(date_int, time_int):
    date_str = '%04d-%02d-%02d ' % (date_int / 10000, (date_int % 10000) / 100, (date_int % 10000) % 100)
    time_str = '%02d:%02d:%02d' % (time_int / 10000, (time_int % 10000) / 100, (time_int % 10000) % 100)
    return date_str + time_str


# 20151206 110507 -->'2015-12-06 11:05:07'
def int2_datetime(date_int, time_int):
    return datetime.datetime(int(date_int / 10000),
                             int((date_int % 10000) / 100),
                             int((date_int % 10000) % 100),
                             int(time_int / 10000),
                             int((time_int % 10000) / 100),
                             int((time_int % 10000) % 100)
                             )

#检测文件名是否包括制定的字符串
def check_filter(object_name, filters):
    ret = True
    for filter in filters:
        if not filter in object_name:
            ret = False
            break

    return ret


def get_filelist_from_path(path, filters):
    filelist = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if check_filter(name, filters):
                filelist.append(os.path.join(root, name))

    return filelist


#  todo 确定停牌时段
def find_stop_trade_index(kdata, week):
    count_week_in_trade_day = int(240 / week)
    return -1, -1


# todo 分析主力资金持续流入的市场表现：持续上升，先跌后升，平盘或下跌
# todo 分析ticks数据对后续走势的影响,特别是大单进出的后续影响力
'''
2018-05-02:
    1）快车司机的微利策略：尾盘布局（下先手），次日跌幅大于1%坚决止损、涨幅大于3%止盈（除非持续保持盈利）
    利用沪深主要的ETF基金进行验证。关键是选准标的进行操作。
    2）利用主要大蓝筹进行操作
'''
# 累计主力资金的走势与股价未来的走势影响极大，处于下行走势的股票下跌可能性很大  ？？？
def cacl_bs_by_cap(cap_path='\data',
                   filters=['CAP-', '015.dat'],
                   ma=[5, 10, 20], nBuyLastWeek=4, nSellLastWeek=6,
                   rsi_low=20, rsi_up=80):
    stotal = 0
    sok = 0
    snok = 0

    files = get_filelist_from_path(cap_path, filters)

    for file_path in files:
        # file_path = 'e:/data/CAP-000554-015.dat'
        filename = os.path.basename(file_path)
        stock = filename[4:10]
        week = int(filename[11:14])

        if stock[0] == '6' or stock[0] == '5':
            stock = 'SHSE.' + stock
        else:
            stock = 'SZSE.' + stock

        cap_data = read_cap_flow(file_path)
        cap_len = len(cap_data)

        try:
            start_dt = cap_data.iloc[0, 0]
            stop_dt = cap_data.iloc[cap_len - 1, 0]
        except:
            write_log_msg()
            continue

        if week == 0:
            week = 240

        kdata = read_kline(stock, week * 60, start_dt, stop_dt)
        klen = len(kdata)

        #todo 数据对齐处理  cap_data、Kdata有时会少数据，少的补充0
        if cap_len != klen and klen>10:
            cap1=cap_data.set_index('eob')
            k1=kdata.set_index('eob')
            if cap_len > klen:
                for col in k1.columns:
                    cap1[col]=k1[col]

                #cap1=cap1.fillna(0)  #价格为0导致显示有偏移量
                kdata = cap1[k1.columns]
                kdata=kdata.reset_index()
            else:
                for col in cap1.columns:
                    k1[col]=cap1[col]

                k1=k1.fillna(0)   #交易数据可以为0
                cap_data= k1[cap1.columns]
                cap_data = cap_data.reset_index()

        nCount = sum(ma) + nBuyLastWeek + nSellLastWeek
        week_in_day = int(240 / week)

        #view ta figure
        draw_stock_ta_fig(stock, ma, kdata, cap_data,
                              week=week, hold_week=60,
                              rsi_low=45, rsi_up=90,
                              buy_point=0, sell_point=0, fig_count=410)

        '''
        #买卖成功率统计
        while i < cap_len:
            start = i - look_back_week
            if not buy and \
                    (main_cap_up(cap_data[:i], ma, nBuyLastWeek)) \
                    and can_buy(kdata, start, i, nBuyLastWeek, rsi_low, rsi_up):  # and
                # print ('main flow ma up\n',cap_data[col][i+nCount-1:i+nCount])
                buy_point = i
                buy = True

            if buy and i - buy_point > week_in_day:
                if stop_loss(kdata, start, buy_point, i) \
                        or ((IsCAPMaDown(cap_data[:i], ma, nSellLastWeek))
                            and can_sell(kdata, start, buy_point, i, hold_week, nSellLastWeek, rsi_low, rsi_up)):  #
                    reward = kdata.loc[i, 'close'] / kdata.loc[buy_point, 'close']

                    if reward > 1.02:
                        ok += 1
                    else:
                        nok += 1

                    total += 1

                    buy = False

            i = i + 1

        if total > 0:
            print('%s,%03d,good=%.0f%%,bad=%.0f%%' % (
                stock, week, 100 * ok / total, 100 * nok / total))

        stotal += total
        sok += ok
        snok += nok
        '''
    if stotal > 0:
        print('total  %03d,good=%.0f%%,bad=%.0f%%' % (
            week, 100 * sok / stotal, 100 * snok / stotal))

    plt.close()


'''
2018-05-02:
    1）快车司机的微利策略：尾盘布局（下先手），次日跌幅大于1%坚决止损、涨幅大于3%止盈（除非持续保持盈利）
    利用沪深主要的ETF基金进行验证。关键是选准标的进行操作。
        159902	中 小 板	
        159919	300ETF	
        159952	创业ETF	
        510300	300ETF	
        159915	创业板	
        510500	500ETF	
        510050	50ETF	
        159949	创业板50	
    2）利用主要ETF进行操作  ETF轮动策略
       K线、RSI和主力资金变化均处于多头，且RSI处于安全范围【45-85】

'''
def etf_rolling(cap_path='\data',filters=['CAP-', '015.dat'],
                   ma=[5, 10, 20], nBuyLastWeek=4, nSellLastWeek=6,
                   rsi_low=40, rsi_up=75,backtest=False,view_ta=False):
    etfs=['159902','159919','159952','510300','159915','510500','510050','159949']
    etf_name=['中 小 板','300ETF' , '创业ETF','300ETF','创业板','500ETF','50ETF','创业板50']

    stotal = 0
    sok = 0
    snok = 0

    analyse_count=sum(ma)*2+nBuyLastWeek

    files = get_filelist_from_path(cap_path, filters)

    for file_path in files:
        filename = os.path.basename(file_path)
        stock = filename[4:10]
        if stock not in etfs:
            continue

        #最多处理到日线级别的K线
        week = int(filename[11:14])
        if week == 0:
            week = 240

        weeks_in_trade_day=int(240/week)

        if stock[0] == '6' or stock[0] == '5':
            stock = 'SHSE.' + stock
        else:
            stock = 'SZSE.' + stock

        cap_data = read_cap_flow(file_path)
        cap_len = len(cap_data)

        if cap_len<analyse_count:
            continue

        if backtest:
            analyse_start=analyse_count
        else:
            analyse_start =cap_len-analyse_count

        try:
            start_dt = cap_data.iloc[0, 0]
            stop_dt = cap_data.iloc[cap_len - 1, 0]
        except:
            write_log_msg()
            continue

        kdata = read_kline(stock, week * 60, start_dt, stop_dt)
        klen = len(kdata)
        if klen<analyse_count:
            continue

        # cap_data、Kdata有时会少数据，cap_data少的补充0，Kdata保持NAN
        if cap_len != klen and klen > 10:
            cap1 = cap_data.set_index('eob')
            k1 = kdata.set_index('eob')
            if cap_len > klen:
                for col in k1.columns:
                    cap1[col] = k1[col]

                # cap1=cap1.fillna(0)  #价格为0导致显示有偏移量
                kdata = cap1[k1.columns]
                kdata = kdata.reset_index()
            else:
                for col in cap1.columns:
                    k1[col] = cap1[col]

                k1 = k1.fillna(0)  # 交易数据可以为0
                cap_data = k1[cap1.columns]
                cap_data = cap_data.reset_index()

        buy_list=[]
        bs=[]
        has_buy=False
        bs_msg=''
        must_sell=False
        while cap_len-analyse_start>1:
            analyse_start += 1

            if len(buy_list)>0:
                #sell poit detect
                try:
                    if must_sell or  can_sell(kdata=kdata[:analyse_start], \
                                ma_list=ma, week=nBuyLastWeek, rsi_low=rsi_low, rsi_up=rsi_up):
                        must_sell=True
                        tmp=buy_list.copy()
                        for buy_point in tmp:
                            if kdata.loc[analyse_start-1, 'eob'].date()==kdata.loc[buy_point, 'eob'].date():
                                continue

                            if view_ta:
                                bs_tmp=("[%s,%0.3f]-[%s,%0.3f]" % (\
                                       kdata.loc[buy_point, 'eob'].strftime('%Y-%m-%d %H-%M-%S'),kdata.loc[buy_point, 'close'],
                                       kdata.loc[analyse_start-1, 'eob'].strftime('%Y-%m-%d %H-%M-%S'),kdata.loc[analyse_start-1, 'close']
                                                           ))
                                print("    =====sell:%s" % bs_tmp)
                                bs_msg+=bs_tmp

                            bs.append((analyse_start-1,buy_point))
                            buy_list.__delitem__(buy_list.index(buy_point))

                except:
                    write_log_msg()
                    pass

            #if not main_delta_cap_up(data=cap_data[:analyse_start],\
            #  maList=ma,nLastWeeks=nBuyLastWeek):
            #    continue

            if not can_buy(kdata=kdata[:analyse_start],
              ma_list=ma,week=nBuyLastWeek,rsi_low=rsi_low,rsi_up=rsi_up):
                continue

            must_sell=False
            buy_list.append(analyse_start-1)
            if not has_buy:
                print('\n ------------------%s----------------------' % filename)
                has_buy=True
                
            #print("code:%s,%s,buy"%\
            #      (filename,kdata.loc[analyse_start,'eob'].strftime('%Y-%m-%d %H-%M-%S')))

        if len(buy_list)>0:
            for buy_point in buy_list:
                bs.append((analyse_start, buy_point))
                if view_ta:
                    bs_tmp = (" [%s,%0.3f]-[%s,%0.3f]" % ( \
                        kdata.loc[buy_point, 'eob'].date(), kdata.loc[buy_point, 'close'],
                        kdata.loc[analyse_start, 'eob'].date(), kdata.loc[analyse_start, 'close']
                    ))
                    bs_msg+=bs_tmp
                    print("    =====holding:%s" % bs_tmp)

        #view ta figure
        if len(bs)>0 and view_ta:
            draw_stock_ta_fig(stock, ma, kdata, cap_data,
                              kweek =week, hold_week=60,
                              rsi_low = rsi_low, rsi_up=rsi_up,
                              bs =bs,  fig_count=410,bs_msg=bs_msg)

        #'''
        #买卖成功率统计
        ok = 0
        nok = 0
        total=0
        for sell,buy in bs:
            reward = kdata.loc[sell, 'close'] / kdata.loc[buy, 'close']

            if reward >= 1.006:
                ok += 1
            else:
                nok += 1

            total += 1

        if total > 0:
            print('%s,%03d,good=%.0f%%,bad=%.0f%%' % (
                stock, week, 100 * ok / total, 100 * nok / total))

        stotal += total
        sok += ok
        snok += nok
        #'''

    if stotal > 0:
        print('total  %03d,good=%.0f%%,bad=%.0f%%' % (
            week, 100 * sok / stotal, 100 * snok / stotal))

    plt.close()


#曲线拟合方案：一次到四次，方向判断用一次拟合方案
def cacl_data_trend(data,type=1, week=30, show=False):

    if len(data)<week:
        return

    # 基本曲线拟合模型 线性（一次）、二次、三次、四次
    # fnx=(a0*x+a1)*x+a2...
    def fnx(x, coefficients):
        fn = coefficients[0] * x + coefficients[1]
        for an in coefficients[2:]:
            fn = fn * x + an

        return fn

    # 直线方程函数
    def f1(x, A, B):
        return fnx(x, [A, B])

    # 二次曲线方程
    def f2(x, A, B, C):
        return fnx(x, [A, B, C])

    # 三次曲线方程
    def f3(x, A, B, C, D):
        return fnx(x, [A, B, C, D])

    # 4次曲线方程
    def f4(x, A, B, C, D, E):
        return fnx(x, [A, B, C, D, E])

    # 4次曲线方程
    def f4(x, A, B, C, D, E):
        return fnx(x, [A, B, C, D, E])

    # 5次曲线方程
    def f5(x, A, B, C, D, E, F):
        return fnx(x, [A, B, C, D, E, F])

    # 5次曲线方程
    def f6(x, A, B, C, D, E, F, G):
        return fnx(x, [A, B, C, D, E, F, G])

    def regression456(datas, show):
        cap_len = len(datas)
        x2 = range(cap_len)

        A4, B4, C4, D4, E4 = optimize.curve_fit(f4, x2, datas)[0]

        A5, B5, C5, D5, E5, F5 = optimize.curve_fit(f5, x2, datas)[0]

        A2, B2, C2, D2, E2, F2, G2 = optimize.curve_fit(f6, x2, datas)[0]

        x2 = x2[-week - 1:]
        y4 = fnx(x2, [A4, B4, C4, D4, E4])
        y5 = fnx(x2, [A5, B5, C5, D5, E5, F5])
        y6 = fnx(x2, [A2, B2, C2, D2, E2, F2, G2])

        ys = [y4, y5, y6]
        trends = []
        for i in range(1, week):
            trend = []
            for y in ys:
                trend.append(y[i] >= y[i - 1])

            trends.append(trend)

        if show:
            plt.plot(x2, y4, label='y4')
            plt.plot(x2, y5, label='y5')
            plt.plot(x2, y6, label='y6')
            # plt.legend(loc='upper right', shadow=True, fontsize='x-large')
            # 返回最近week趋势：全增，全减  趋势确定
            #               增减，减增  趋势可能转变
        return trends

    def regression123(datas, show):
        cap_len = len(datas)
        x2 = range(cap_len)

        A1, B1 = optimize.curve_fit(f1, x2, datas)[0]
        A2, B2, C2 = optimize.curve_fit(f2, x2, datas)[0]
        A3, B3, C3, D3 = optimize.curve_fit(f3, x2, datas)[0]

        x2 = x2[-week - 1:]
        y4 = fnx(x2, [A1, B1])
        y5 = fnx(x2, [A2, B2, C2])
        y6 = fnx(x2, [A3, B3, C3, D3])

        ys = [y4, y5, y6]
        trends = []
        for i in range(1, week):
            trend = []
            for y in ys:
                trend.append(y[i] >= y[i - 1])

            trends.append(trend)

        if show:
            plt.plot(x2, y4, label='y4')
            plt.plot(x2, y5, label='y5')
            plt.plot(x2, y6, label='y6')
            # plt.legend(loc='upper right', shadow=True, fontsize='x-large')
            # 返回最近week趋势：全增，全减  趋势确定
            #               增减，减增  趋势可能转变
        return trends

    def line_regression(datas):
        x2 = range(week)
        A1, B1 = optimize.curve_fit(f1, x2, datas[-week:])[0]

        y2 = fnx(x2, [A1, B1])

        #通过起始值判断趋势：升或跌
        return  y2[-1]>y2[0]

    try:
        if type==1:
            return  line_regression(data)
        else:
            return False
    except:
        write_log_msg()
        return False
#todo 基于移动平均的局部主力资金流的变化情况分析、判断波段介入时机


def read_stock_data( file_path):
    try:
        # file_path = 'e:/data/CAP-000554-015.dat'
        filename = os.path.basename(file_path)
        stock = filename[4:10]
        week = int(filename[11:14])
        if stock[0] == '6':
            stock = 'SHSE.' + stock
        else:
            stock = 'SZSE.' + stock

        cap_data = read_cap_flow(file_path)
        cap_len = len(cap_data)

        start_dt = int2_datetime(cap_data.iloc[0, 0], cap_data.iloc[0, 1])
        stop_dt = int2_datetime(cap_data.iloc[cap_len - 1, 0], cap_data.iloc[cap_len - 1, 1])

        if week == 0:
            week = 240

        kdata = read_kline(stock, week * 60, start_dt, stop_dt)

        return  stock,week,cap_data,kdata
    except:
        write_log_msg()
        print('error in read_stock_data')
        pass


