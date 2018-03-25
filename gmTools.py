# -*- coding: utf-8 -*-
'''
  基础模块，包括数据获取、整理，通用处理函数
'''
from __future__ import print_function, absolute_import

import struct
import os
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
from scipy import optimize
import datetime
import time
import talib
import ui4backup    #ui interface
# ------------  gm3 ---------------------
try:
    from gm.api import *

    # 设置token
    set_token('c631be98d34115bd763033a89b4b632cef5e3bb1')
except:
    print('gm3 init error!!!!')

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
                dt = datetime.strptime(dt.replace('/', '-'), '%Y-%m-%d %H:%M:%S')
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
    columns = ['Date', 'Time', 'SmallBuy', 'MidBuy', 'BigBuy', 'HugeBuy', 'SmallSell', 'MidSell', 'BigSell', 'HugeSell']

    f = open(filepath, 'rb')
    dataSize = 72
    filedata = f.read()
    filesize = f.tell()
    f.close()

    tickCount = filesize / dataSize

    index = 0
    series = []
    last_cap = [0, 0]
    try:
        while filesize - index >= dataSize:
            cap = struct.unpack_from('2i8d', filedata, index)
            index = index + dataSize

            if sum(cap[2:]) >= 100.0:  # 去掉无交易数据
                # 由于前期数据保存软件设计的原因，数据可能存在重复读写的情况，要判断数据的有效性
                if cap[0] > last_cap[0] \
                        or (cap[0] == last_cap[0] and cap[1] > last_cap[1]):
                    series.append(cap)
                    last_cap = cap[:2]
                else:
                    # 出现数据重复,保留最新的数据
                    pass
    except:
        pass
    caps = pd.DataFrame(series, columns=columns)
    return caps



'''
    均线多头向上判断：多头向上时返回true，否则false
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
            trends = cacl_cap_trend(total_flow, count - 1, 0, maList[1], show)
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


def get_backtest_start_date(start_date, look_back_dates):
    # 获取开始读取数据的开始位置  从训练结束时间倒退一年内的从交易日数据
    try:
        stop_day = str(start_date.date())
        start_day = str((start_date + datetime.timedelta(days=-365)).date())
        trade_dates = get_trading_dates('SHSE', start_day, stop_day)
        return trade_dates[-look_back_dates]
    except:
        pass


'''
    利用掘金终端的函数读取指数的成份股
    stock_list :"SHSE.600000,SZSE.000001"
'''


def get_index_stock(index_symbol, return_list=True):
    # 连接本地终端时，td_addr为localhost:8001,
    if (True):
        try:
            css = get_constituents(index_symbol)
            css.sort()
            return css
        except:
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
            pass


'''
    利用掘金终端的函数读取指定股票最新价，用于统计当日当时价位情况
    stock_list :"SHSE.600000,SZSE.000001"
'''


def get_minutes_bars(stock_list, minutes, begin_time, end_time):
    # 连接本地终端时，td_addr为localhost:8001,
    if (td.init('haigezyj@qq.com', 'zyj2590@1109', 'strategy_1') == 0):
        try:
            bars = md.get_bars(stock_list, int(minutes * 60), begin_time, end_time)
            return bars
        except:
            pass


def get_daily_bars(stock_list, begin_time, end_time):
    # 连接本地终端时，td_addr为localhost:8001,
    if (td.init('haigezyj@qq.com', 'zyj2590@1109', 'strategy_1') == 0):
        try:
            bars = md.get_dailybars(stock_list, begin_time, end_time)
            return bars
        except:
            pass


'''
利用掘金终端的函数读取需要的K线数据
get_bars 提取指定时间段的历史Bar数据，支持单个代码提取或多个代码组合提取。策略类和行情服务类都提供该接口。
get_bars(symbol_list, bar_type, begin_time, end_time)
        参数名	类型	说明
        symbol_list	string	证券代码, 带交易所代码以确保唯一，如SHSE.600000，同时支持多只代码
        bar_type	int	bar周期，以秒为单位，比如60即1分钟bar
        begin_time	string	开始时间, 如2015-10-30 09:30:00
        end_time	string	结束时间, 如2015-10-30 15:00:00
return:dataframe  'eob','open','high','low','close','volume','amount'
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

                count = len(bars)
                # TODO 一次最多处理10000项以内数据，超出应有所提示
                if (count <= 5 or len(kdata) > max_record) \
                        or (bars.iloc[count - 1, 0] >= stop_time) \
                        or (start_time == bars.iloc[count - 1, 0]):
                    break

                start_time = bars.iloc[count - 1, 0]
            except:
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


def read_last_n_kline(symbol_list, weeks_in_seconds, count, end_time):
    # 连接本地终端时，td_addr为localhost:8001,
    if (td.init('haigezyj@qq.com', 'zyj2590@1109', 'strategy_1') == 0):
        # 类结构体转成dataframe
        columns = ['eob', 'open', 'high', 'low', 'close', 'volume', 'amount']
        bars = 0

        is_daily = (weeks_in_seconds == 240 * 60)
        data_list = []  # pd.DataFrame(None, columns=columns)
        '''
        todo 整批股票读取有问题，数据取不全，放弃
        stocks = ''
        for x in symbol_list:
            stocks+=','+x

        read_days=int(count*weeks_in_seconds/240/60)+1
        start_date=md.get_calendar('SZSE',
            datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                -datetime.timedelta(days=read_days),end_time)[0].strtime
        start_date=start_date[:10] +' 09:30:00'

        while start_date<end_time:
            bars=md.get_bars(stocks[1:], weeks_in_seconds, start_date, end_time)
        '''
        for stock in symbol_list:
            # now = '[{0}] read k line'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            # print(now,stock)
            kdata = []
            # 返回结果是bar类数组
            if is_daily:
                bars = md.get_last_n_dailybars(stock, count, end_time)
            else:
                bars = md.get_last_n_bars(stock, weeks_in_seconds, count, end_time)

            for bar in bars:
                if is_daily:
                    kdata.append([int(bar.utc_time),
                                  bar.open, bar.high, bar.low, bar.close,
                                  bar.volume, bar.amount])
                else:
                    kdata.append([int(bar.utc_endtime),
                                  bar.open, bar.high, bar.low, bar.close,
                                  bar.volume, bar.amount])

            if len(bars) > 0:
                kdata = pd.DataFrame(kdata, columns=columns)
                kdata = kdata.sort_values(by='eob', ascending=False)
                data_list.append({'code': stock, 'kdata': kdata})

        return data_list


def draw_kline(stock, kdata, buy_time, sell_time,
               week, hold_week, fig_id=311, disp_low=-10, disp_high=10):
    plt.subplot(fig_id)
    plt.ylabel('PRICE')
    closing = kdata['close'].values
    data = closing.tolist()
    count = len(data)
    try:
        time_list = kdata['eob'].tolist()
        x = time_list.index(buy_time)
        buy_price = data[x]
        sell_price = data[time_list.index(sell_time)]
        reward = int(sell_price * 100 / buy_price - 100)
    except:
        reward = 0

    # 只用图形显示收益差距很大的情况
    # if reward<disp_high and reward>disp_low:
    #    return  reward

    plt.plot(list(range(count)),
             data, color='b', label='close')

    '''
    # EMA 指数移动平均线  ma6跌破ma12连续若干周期
    #ma6 = talib.EMA(closing, timeperiod=6)
    #ma12 = talib.EMA(closing, timeperiod=12)
    #ma26 = talib.EMA(closing, timeperiod=26)
    plt.plot(list(range(len(kdata))),
             ma6, color='r', label='ma6')
    plt.plot(list(range(len(kdata))),
             ma12, color='y', label='ma12')
    #plt.plot(list(range(len(kdata))),
    #         ma26, color='g', label='ma26')
    '''

    if buy_time == sell_time:
        # no sell time,sell on maxholding weeks
        if x + hold_week < len(time_list):
            sell_time = time_list[x + hold_week]
        else:
            sell_time = time_list[-1]

        no_sell = True
    else:
        no_sell = False

    if not no_sell:
        plt.annotate(str(x), xy=(x, buy_price),
                     xytext=(x, buy_price),
                     arrowprops=dict(facecolor='red', shrink=0.05),
                     )
        if not sell_time in time_list:
            x = -1
        else:
            x = time_list.index(sell_time)

        sell_price = data[x]

        plt.annotate(str(x), xy=(x, sell_price),
                     xytext=(x, sell_price),
                     arrowprops=dict(facecolor='green', shrink=0.05),
                     )
        reward = int(sell_price * 100 / buy_price - 100)
    else:
        reward = 0

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

    x = len(time_list) - 1
    plt.annotate(str(time_list[x].date()), xy=(x, date_high),
                 xytext=(x, date_high),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 )

    buy_time = buy_time.strftime('%Y-%m-%d %H-%M-%S')
    sell_time = sell_time.strftime('%Y-%m-%d %H-%M-%S')

    if no_sell:
        title = '%s week=%d ' % (stock, week)
    else:
        title = '%s week=%d reward=%d%%\n %s--%s' % (stock, week, reward, buy_time, sell_time)

    plt.title(title)
    # plt.legend(loc='upper left', shadow=True, fontsize='x-large')
    return reward


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


#
def draw_cap_main(cap_data, buy_point, sell_point,
                  maList, fig_id=313, draw_delta=False):
    min_week_of_trend = 60
    plt.subplot(fig_id)
    count = len(cap_data)

    if draw_delta == False:
        flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']).values
        plt.ylabel('MAIN CAP')
        # 累计主力总资金流
        total_flow = [flow[0]]
        for i in range(1, count):
            total_flow.append(total_flow[i - 1] + flow[i])

        plt.plot(list(range(count)),
                 total_flow, color='brown')

        cacl_cap_trend(total_flow, buy_point,
                       sell_point, min_week_of_trend + 1, True)

        # 计算累计主力资金的趋势  曲线拟合：上升、下行两种状态

    else:
        plt.ylabel('MAIN DELTA')
        flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell'])
        plt.plot(list(range(count)),
                 flow.values, color='brown')
        plt.plot(list(range(count)),
                 [0.0 for _ in range(count)], color='black')

        for week in maList[:1]:
            tmp = flow.rolling(week).mean().tolist()
            plt.plot(list(range(count)),
                     tmp, label=str(week))


            # plt.legend(loc='upper left', shadow=True, fontsize='x-large')


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


def draw_rsi(kdata, fig_id=313, low=40, high=90,
             rsi_low=20, rsi_up=80):
    count = len(kdata)
    plt.subplot(fig_id)
    plt.ylabel('RSI')
    closing = kdata['close'].values
    # RSI
    RSI1 = talib.RSI(closing, timeperiod=5)

    plt.plot(list(range(count)),
             RSI1, color='r', label='RSI1')

    plt.plot(list(range(count)),
             [rsi_up for i in range(count)], color='black', label='U' + str(high))
    plt.plot(list(range(count)),
             [rsi_low for i in range(count)], color='green', label='D' + str(low))

    plt.legend(loc='upper left', shadow=True, fontsize='x-large')


# todo 结合ticks分析成交量的组成，特别是主力资金的占比
def draw_vol(kdata, fig_id=515):
    count = len(kdata)
    plt.subplot(fig_id)
    vol = np.double(kdata['volume'].values)
    plt.ylabel('VOL')
    # EMA 指数移动平均线  ma6跌破ma12连续若干周期
    ma6 = talib.EMA(vol, timeperiod=6)
    ma12 = talib.EMA(vol, timeperiod=12)
    # ma26 = talib.EMA(vol, timeperiod=26)

    plt.plot(list(range(len(kdata))),
             vol, color='blue', label='vol')
    plt.plot(list(range(len(kdata))),
             ma6, color='red', label='ma6')

    # plt.legend(loc='upper left', shadow=True, fontsize='x-large')


def draw_stock_ta_fig(stock, ma, kdata, buy_time, sell_time, cap_data,
                      week=30, bs=False, hold_week=60, log_dir='.',
                      rsi_low=20, rsi_up=80, disp_low=-6, disp_high=15,
                      buy_point=0, sell_point=0,fig_count = 510):
    # 以折线图表示结果 figsize=(20, 15)
    '''

    fig = plt.figure(figsize=(18, 10))
    fig.subplots_adjust(hspace=0)
    '''
      # 子图数量

    reward = draw_kline(stock, kdata, buy_time, sell_time, week,
                        hold_week, fig_count + 1, disp_low, disp_high)

    # 绘制主力资金图
    draw_cap_fig(cap_data, fig_count + 2)
    # 主力资金总趋势
    draw_cap_main(cap_data, buy_point, sell_point, ma, fig_count + 3, False)
    draw_cap_main(cap_data, buy_point, sell_point, ma, fig_count + 4, True)
    # 绘制RSI图
    # draw_rsi(kdata,fig_count+4,rsi_low, rsi_up)

    # 绘制volume图
    draw_vol(kdata, fig_count + 5)

    # try:
    buy_time = buy_time.strftime('%Y-%m-%d %H-%M-%S')
    sell_time = sell_time.strftime('%Y-%m-%d %H-%M-%S')

    if reward >= 0:
        reward1 = 'u%03d' % reward
    else:
        reward1 = 'd%03d' % (-reward)

    if bs == False:
        file = '%s/w%03d-%s-%s-%s-%s.png' % (
            log_dir + '/fig', week, reward1, stock, buy_time, sell_time)
    else:
        file = '%s/w%03d-%s-%s-%s-%s.png' % (
            log_dir + '/bs_fig', week, reward1, stock, buy_time, sell_time)
    plt.savefig(file)

    # except:
    #    pass
    plt.close()
    return reward


# 判断当前走势能否买入？
# todo use tf model to decice the buy-sell point
def can_buy(kdata, start, stop, week=3, rsi_low=20, rsi_up=80):
    ret = False
    data = kdata[start:stop]
    closing = data['close'].values

    while not ret:
        # RSI
        RSI1 = talib.RSI(closing, timeperiod=5)[-week:]

        for i in range(1, week):
            if (RSI1[i] < rsi_low or RSI1[i] > rsi_up):
                break

        # MACD  bar 最新三项大于0且处于金叉后的上升阶段
        '''
        dif, dea, bar = talib.MACD(closing,
            fastperiod=12, slowperiod=26, signalperiod=9)

        bar = bar[-week:]
        dif = dif[-week:]
        dea = dea[-week:]

        for i in range(1, week):
            if bar[i] < bar[i - 1] \
                    or dif[i] < dif[i - 1] \
                    or dea[i] < dea[i - 1]:
                break

        if i < week - 1:
            break
        '''

        # EMA 指数移动平均线  多头发散
        ma6 = talib.EMA(closing, timeperiod=6)[-week:]
        ma12 = talib.EMA(closing, timeperiod=12)[-week:]
        ma26 = talib.EMA(closing, timeperiod=26)[-week:]

        for i in range(week):
            if ma6[-i] < ma12[-i] \
                    or ma12[-i] < ma26[-i]:
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


# todo 利用ticks数据判断当日主力进出的强度，低位流入、高位流出
# 确定买卖点
def can_sell(kdata, start, buy_point, stop,
             hold_week, week=3, rsi_low=20, rsi_up=80):
    ret = False
    closing = np.double(kdata[start:stop]['close'])
    while not ret:
        # EMA 指数移动平均线  ma6跌破ma12连续若干周期
        ma6 = talib.EMA(closing, timeperiod=6)[-week:]
        ma12 = talib.EMA(closing, timeperiod=12)[-week:]
        # ma26 = talib.EMA(closing, timeperiod=26)

        # 达到最大持有周期后出现连续3周低于ma6,必须清仓
        '''
        if stop-buy_point>hold_week :
            for i in range(-3,0):
                if closing[i-1]>ma6[i]:
                    break

            if i < -1:
                break
        '''

        for i in range(week):
            if ma6[i] > ma12[i]:
                break

        if i < week - 1:
            break

        ret = True

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
# 累计主力资金的走势与股价未来的走势影响极大，处于下行走势的股票下跌可能性很大
def cacl_bs_by_cap(cap_path='data0322',
                   filters=['CAP-002', '005.dat'],
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
        if stock[0] == '6':
            stock = 'SHSE.' + stock
        else:
            stock = 'SZSE.' + stock

        cap_data = read_cap_flow(file_path)
        cap_len = len(cap_data)

        try:
            start_dt = int2_datetime(cap_data.iloc[0, 0], cap_data.iloc[0, 1])
            stop_dt = int2_datetime(cap_data.iloc[cap_len - 1, 0], cap_data.iloc[cap_len - 1, 1])
        except:
            continue

        if week == 0:
            week = 240

        kdata = read_kline(stock, week * 60, start_dt, stop_dt)
        klen = len(kdata)
        ok = 0
        nok = 0
        total = 0
        if cap_len != klen:
            if cap_len - klen > 1:
                # todo kdata's length does not equal with cap cap_data[840-1290] [CAP-000018-005.dat]
                # kdata     's length does not equal with cap cap_data[1167-1169] [CAP-000150-005.dat]
                # kdata's length does not equal with cap cap_data[1281-1283] [CAP-002107-005.dat]
                # kdata     's length does not equal with cap cap_data[1178-1180] [CAP-000622-005.dat]
                # 此时出现局部时段停牌，但cap仍有数据，属于错误信息，必须过滤
                print("kdata's length does not equal with cap cap_data[%d-%d] [%s]  " % (
                    len(kdata), cap_len, filename))
                continue

        nCount = sum(ma) + nBuyLastWeek + nSellLastWeek
        look_back_week = nCount * 3
        i = nCount * 6
        buy = False
        bs = False
        week_in_day = int(240 / week)
        hold_week = int(10 * week_in_day)
        log_dir = '.'

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
                    if reward > 1.06 or reward < 0.95:
                        draw_stock_ta_fig(stock, ma,
                                          kdata,
                                          int2_datetime(cap_data.iloc[buy_point, 0],
                                                        cap_data.iloc[buy_point, 1]),
                                          int2_datetime(cap_data.iloc[i, 0],
                                                        cap_data.iloc[i, 1]),
                                          cap_data, week=week, bs=bs,
                                          hold_week=hold_week, log_dir=log_dir,
                                          rsi_low=rsi_low, rsi_up=rsi_up,
                                          buy_point=buy_point, sell_point=i)

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
    if stotal > 0:
        print('total  %03d,good=%.0f%%,bad=%.0f%%' % (
            week, 100 * sok / stotal, 100 * snok / stotal))






def cacl_cap_trend(total_flow, buy_point, sell_point, week, show=False):
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

    if buy_point > 0:
        trends = regression123(total_flow[:buy_point], show)
    if sell_point > 0:
        trends = regression123(total_flow[:sell_point], show)

    return trends

#todo 基于移动平均的局部主力资金流的变化情况分析、判断波段介入时机