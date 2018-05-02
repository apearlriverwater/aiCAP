# coding=utf-8

import tensorflow as tf
import numpy  as np
import talib
import gmTools_v2 as gmTools
import time
import  matplotlib.pyplot as plt
import pandas as pd
import datetime
import struct

""" 
2018-05-02:
    1）快车司机的微利策略：尾盘布局（下先手），次日跌幅大于1%坚决止损、涨幅大于3%止盈（除非持续保持盈利）
    利用沪深主要的ETF基金进行验证。关键是选准标的进行操作。
    2）利用主要大蓝筹进行操作
    
2018-03-21:
   1)ai预测效果一般，改回传统的处理方案，cap+技术分析：均线、RSI、成交量、MACD等
   统计分析cap主力趋势，结合均线趋势、RSI趋势确定买卖点
    

"""

MAX_HOLDING=5
MAX_STOCKS=5


BUY_GATE=7
SELL_GATE=3
BUY_FEE=1E-4
SELL_FEE=1E-4
DAY_SECONDS=24*60*60


#策略参数
g_week=15  #freqency
g_max_holding_days=15


g_trade_minutes=240
g_week_in_trade_day=int(g_trade_minutes/g_week)
g_look_back_weeks=max(10,g_week_in_trade_day*2)*10  #回溯分析的周期数
g_max_holding_weeks=g_week_in_trade_day*g_max_holding_days  #用于生成持仓周期内的收益等级


g_max_stage=11  #持仓周期内收益等级
g_stage_rate=2  if g_week>30 else 1#持仓周期内收益等级差

g_log_dir = '/01deep-ml/logs/w{0}hold{1}days'.format(g_week,g_max_holding_days)


g_current_train_stop=0                  #当前测试数据结束位置
g_test_stop=0                   #当前实时数据结束位置
g_stock_current_price_list=0

g_test_securities=["SZSE.002415","SZSE.000333","SZSE.002460",
                   "SZSE.000001","SZSE.002465","SZSE.002466",
"SZSE.000651","SZSE.000725","SZSE.002152","SZSE.000538","SZSE.300072",
"SHSE.603288","SHSE.600703","SHSE.600271", "SHSE.600690", "SHSE.600585", "SHSE.600271",
"SHSE.600000","SHSE.600519"]




#study()
if __name__ == '__main__':
    pass
