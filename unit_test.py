import unittest
import gmTools as tls
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy import optimize

class Test_uint_test(unittest.TestCase):
    tls.etf_rolling(filters=['CAP-', '.dat'],backtest=True)

    '''
    多头选股：条件与：15日内创30日新低，10日内连续缩量，
                条件或：5日内温和上涨，10日内间歇放量，5日内突然放量
                东方财富条件选股不好用，改用掘金量化终端自行选择

                SHSE.000906  SHSE.000300
    def test_stock_long(self, block='SHSE.000300',week_in_seconds=4 * 60 * 60,count=60):

        stock_list = tls.get_block_stock_list(block)
        stock_long=[]
        for stock in stock_list:
            bars = tls.read_last_n_kline(stock, week_in_seconds,count)

            if bars is None:
                continue

            #条件与：15日内创30日新低，10日内连续缩量
            closing=bars['close']

            # 15日内创30日新低
            vol_count = int(count/2)
            if closing.idxmin()!=closing[-vol_count:].idxmin():
                continue

            vols = bars['volume'][-vol_count * 2:]

            #15日内连续缩量  vol小于5日均值的数量占60%以上
            vol_ma=vols.rolling(window=5,center=False).mean()
            tmp=(vols[-vol_count:]<vol_ma[-vol_count:]).tolist().count(True)
            if tmp/vol_count<0.5:
                continue

            #条件或：10日内间歇放量
            vol_count = int(count/4)
            tmp = (vols[-vol_count:] >2* vol_ma[-vol_count:]).tolist().count(True)/vol_count
            tmp1=False
            tmp2=False
            if tmp<0.2:
                # 条件或：5日内温和上涨，5日内突然放量
                tmp1 = (vols[-vol_count:] >  vol_ma[-vol_count:]).tolist().count(True)/vol_count>0.4    #大于5日均线
                tmp2 = (vols[-vol_count:] > 2* vol_ma[-vol_count:]).tolist().count(True)/vol_count>0.2  #大于5日均线2倍

            if tmp>=0.2 or tmp1 or tmp2:
                #满足可介入条件
                stock_long.append(stock)
        print(stock_long[:5])
        return stock_long

    def test_cacl_cap(self, cap_path='data0322'):
        tls.cacl_bs_by_cap()
    def test_cacl_cap(self, cap_path='data0322'):
        tls.cacl_bs_by_cap()
    
    def test_cacl_cap_trend(self,cap_path='data0322'):

        plt.figure()

        filters = ['CAP-', '005.dat']
        files = tls.get_filelist_from_path(cap_path, filters)
        week=61

        for file_path in files:
            #file_path = 'e:/data/CAP-000554-015.dat'
            cap_data = tls.read_cap_flow(file_path)
            stock = os.path.basename(file_path)[4:10]
            cap_len = len(cap_data)
            count = cap_len
            cap_data=cap_data[:count]
            flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']).values
            plt.ylabel('main flow')
            plt.title(stock)
            # 累计主力总资金流
            datas = [flow[0]]
            for i in range(1, count):
                datas.append(datas[i - 1] + flow[i])


            plt.plot(range(count),datas)

            tls.cacl_cap_trend(cap_data,week,True)

            plt.legend(loc='upper left', shadow=True, fontsize='x-large')
            plt.clf()
            
        symbol_list	string	证券代码, 带交易所代码以确保唯一，如SHSE.600000，同时支持多只代码
        bar_type	int	bar周期，以秒为单位，比如60即1分钟bar
        begin_time	string	开始时间, 如2015-10-30 09:30:00
        end_time	string	结束时间, 如2015-10-30 15:00:00
    
     def test_cacl_cap(self, cap_path='data0322'):
        cap_path = 'data0322'
        filters = ['CAP-002', '005.dat']

        files = tls.get_filelist_from_path(cap_path, filters)

        stock, week, cap_data, kdata = tls.read_stock_data(files[0])
        count = len(cap_data)
        files = files[1:]
        x = np.arange(0, count, 1)
        klen = len(kdata)

        if klen == count:
            flow = (cap_data['HugeBuy'] - cap_data['HugeSell'] + cap_data['BigBuy'] - cap_data['BigSell']).values
            # 累计主力总资金流
            total_flow = [flow[0]]
            for i in range(1, count):
                total_flow.append(total_flow[i - 1] + flow[i])

        tls.draw_kline(stock, kdata, 0, 0, week, 100, 311, total_flow)
    
    def test_read_kline(self):
        symbol_list	='SHSE.600000'
        bar_type=15*60
        begin_time='2015-10-30 09:30:00'
        end_time='2015-10-30 15:00:00'
        bars=tls.read_kline(symbol_list,bar_type,begin_time,end_time)
        print(bars[:3])
        print(bars[-3:])
        
        def test_read_cap(self):
        tls.cacl_bs_by_cap()   
    '''


    #def test_read_ticks(self):
    #    tick_file_path='e:/data/ticks-000001-20180201.dat'
    #    ticks=tls.read_ticks(tick_file_path)
    #    print(ticks[:3])
    #    print(ticks[-3:])
        




if __name__ == '__main__':
    unittest.main()
