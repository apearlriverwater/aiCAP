# coding:utf-8

'''-------------------------------------------------------------------------------------
    因为Python的线程虽然是真正的线程，但解释器执行代码时，有一个GIL锁：Global Interpreter Lock，
任何Python线程执行前，必须先获得GIL锁，然后，每执行100条字节码，解释器就自动释放GIL锁，让别的线
程有机会执行。这个GIL全局锁实际上把所有线程的执行代码都给上了锁，所以，多线程在Python中只能交替执
行，即使100个线程跑在100核CPU上，也只能用到1个核。
    GIL是Python解释器设计的历史遗留问题，通常我们用的解释器是官方实现的CPython，要真正利用多核，除非
重写一个不带GIL的解释器。所以，在Python中，可以使用多线程，但不要指望能有效利用多核。如果一定要通过多线
程利用多核，那只能通过C扩展来实现，不过这样就失去了Python简单易用的特点。
    不过，也不用过于担心，Python虽然不能利用多线程实现多核任务，但可以通过多进程实现多核任务。多个
Python进程有各自独立的GIL锁，互不影响。


---------------------------------------------------------------------------------------'''

from time import sleep
import multiprocessing
import os
import datetime
#
# 需求分析：有大批量数据需要执行，而且是重复一个函数操作（例如爆破密码），如果全部开始线程数N多，
# 这里控制住线程数m个并行执行，其他等待
#

'''
      官方例子
      An example showing how to use queues to feed tasks to a collection 
      of worker processes and collect the results:
'''
import time
import random
from multiprocessing import Process, Queue, current_process, freeze_support

#
# Function run by worker processes
#

def worker(input, output):
    for func, args in iter(input.get, 'STOP'):
        result = calculate(func, args)
        output.put(result)

#
# Function used to calculate result
#

def calculate(func, args):
    result = func(*args)
    return '%s says that %s%s = %s' % \
        (current_process().name, func.__name__, args, result)

#
# Functions referenced by tasks
#

def mul(a, b):
    time.sleep(0.5*random.random())
    return a * b

def plus(a, b):
    time.sleep(0.5*random.random())
    return a + b

#
#
#

def test():
    NUMBER_OF_PROCESSES = 4
    TASKS1 = [(mul, (i, 7)) for i in range(20)]
    TASKS2 = [(plus, (i, 8)) for i in range(10)]

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Submit tasks
    for task in TASKS1:
        task_queue.put(task)

    # Start worker processes
    for i in range(NUMBER_OF_PROCESSES):
        Process(target=worker, args=(task_queue, done_queue)).start()

    # Get and print results
    print('Unordered results:')
    for i in range(len(TASKS1)):
        print('\t', done_queue.get())

    # Add more tasks using `put()`
    for task in TASKS2:
        task_queue.put(task)

    # Get and print some more results
    for i in range(len(TASKS2)):
        print('\t', done_queue.get())

    # Tell child processes to stop
    for i in range(NUMBER_OF_PROCESSES):
        task_queue.put('STOP')





lock = multiprocessing.Lock()  # 一个锁


def a(x):  # 模拟需要重复执行的函数
    lock.acquire()  # 输出时候上锁，否则进程同时输出时候会混乱，不可读
    print('开始进程：', os.getpid(), '输入参数:', x)
    lock.release()

    # 模拟执行操作
    tmp=1.123456789e30
    for i in range(x):
        for _ in range(1000):
            tmp=tmp*tmp*tmp*tmp

    lock.acquire()
    print( '\n结束进程：', os.getpid(), '预测下一个进程启动会使用该进程号')
    lock.release()
def test_a():
    list = []
    for i in range(20):  # 产生一个随机数数组，模拟每次调用函数需要的输入，这里模拟总共有10组需要处理
        list.append(i * 9000)

    print('参数：', list)
    pool = multiprocessing.Pool(processes=4)  # 限制并行进程数为4

    # 创建进程池，调用函数a，传入参数为list,此参数必须是一个可迭代对象,因为map是在迭代创建每个进程
    pool.map(a, list)

    while True:
        sleep(7)

        lock.acquire()
        print('now time ：', datetime.datetime.time())
        lock.release()


if __name__ == '__main__':
    freeze_support()
    test()



