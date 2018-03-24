import unittest
import gmTools as tls
import os
import matplotlib.pyplot as plt
from scipy import optimize

class Test_uint_test(unittest.TestCase):
    def test_cacl_cap(self, cap_path='data0322'):
        tls.cacl_bs_by_cap()

    '''
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
