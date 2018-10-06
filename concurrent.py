# coding: utf-8
"""并发相关插件库"""


def db_context(func):
    def inner(*args, semaphore=None, **kwargs):
        """对数据库的读写操作,需要在线程内创建连接,即可在线程内commit().
        inner -->代表着需要并发的函数
        给需要并发的函数添加数据库连接上下文,控制并发池.
        :param args: 并发函数需要的位置参数集合
        :param semaphore: 命名参数,在并发函数外部使用,(不会传入并发函数).调度并发池.
        :param kwargs: 并发函数需要的命名参数集合
        :return: 并发函数返回的返回值 或 默认的None
        """
        if semaphore:
            with app.app_context():  # 激活app的连接  # 这一块我的理解不够深,但是目前只能以此实现线程内的上下文传递.
                return_value = func(*args, **kwargs)  # 执行并发函数,若有返回值,交给return_value
                db.session.close()
            semaphore.release()  # 任务结束,并发池的可调用并发数+1
            return return_value  # 返回 返回值

        else:
            with app.app_context():  # 激活app的连接  # 这一块我的理解不够深,但是目前只能以此实现线程内的上下文传递.
                return_value = func(*args, **kwargs)  # 执行并发函数,若有返回值,交给return_value
                db.session.close()
            return return_value  # 返回

    return inner


def threading_func(func, rows, args=None, concurrency_number=8, timeout=60, kwargs=None):
    """封装并发流程函数
    :param func: 需要并发的函数
    :param rows: 数据集合
    :param args: 其他位置参数
    :param concurrency_number: 并发线程数
    :param timeout: 控制线程超时时间,单位:秒.
    :param kwargs: 命名参数
    :return:
    """
    if not args:
        args = []
    if not kwargs:
        kwargs = {}
    semaphore = threading.Semaphore(concurrency_number)  # 设置并发池数量
    kwargs.update({'semaphore': semaphore})  # semaphore命名参数会被db_context装饰器所捕获,不会传入需要并发的函数内
    threads = []  # 生成的线程将装入此列表
    for row in rows:
        threads.append(
            threading.Thread(target=func, args=(row, *args), kwargs=kwargs))  # 构造线程
    for i in threads:
        i.start()
        semaphore.acquire(timeout=timeout)  # 并发池的可调用并发数减一,线程超时秒数.
    for i in threads:
        i.join()  # 等待线程


class Process:
    """进程加协程方法封装类"""

    def __init__(self, target, args: list or tuple):
        """
        :param target: 需要并发的函数
        :param args: 传递给并发函数的参数集合,args位数决定了进程数, args外层包含几个元素,就会产生几个进程:[[],[],[]] 这样的args产生2个进程,带主进程一共3个进程.
        数据结构:[[{'args_name': args, 'args_name2': args2}, {'args_name': args, 'args_name2': args2}] ,[] ,[] ,[]]
        解释:最外层list将元素分发给不同的进程,进程内:将进程内的list内的dict分发给每个协程,协程最后调用目标函数,将dict解包,把参数传入目标函数
        """
        self.target = target  # 目标函数
        self.current_args = args[0]  # 当前进程内协程所需的参数
        self.args = args[1:]  # 分配到其他进程内的参数集合
        self.processing_poll = []  # 进程池

    def gevent_func(self, args):  # 协程函数,将目标函数变为协程
        if isinstance(args, list or type or set):  # 多进程,协程模式.
            if isinstance(args[0], dict):
                jobs = [gevent.spawn(self.target, **i) for i in args]  # **i 解包dict,传入目标函数所需参数
            elif isinstance(args[0], list or type):
                jobs = [gevent.spawn(self.target, *i) for i in args]  # *i list,传入目标函数所需参数
            else:
                jobs = [gevent.spawn(self.target, i) for i in args]  # 传入目标函数所需参数
        else:
            jobs = [gevent.spawn(self.target, **args)]  # 这种模式为多进程多线程协程,target=线程函数,传入线程函数所需的参数.
        gevent.joinall(jobs, timeout=60)  # 启动所有协程

    def run(self):
        for i in self.args:  # 创建进程
            self.processing_poll.append(multiprocessing.Process(target=self.gevent_func, args=(i,)))
        for i in self.processing_poll:  # 启动进程
            i.start()
        self.gevent_func(self.current_args)  # 在当前进程执行协程函数


def distribution(resources: list, number: int):
    """平均分配资源,为并发做任务分配
    :param resources: 资源
    :param number: 分成几份
    :return: [[1,2,3], [4,5,6], [7,8]]
    """
    result = []
    length = len(resources)  # 计算资源总数
    average = int(length / number)  # 计算平均值
    for index, i in enumerate(range(0, length, average)):  # 获取当前分配次数index,与以平均值为步长的分配起始值i, 最大起始值不会超过资源总数
        if index + 1 < number:
            result.append(resources[i:i + average])
        else:  # 最后一次分配,将余下所有资源分配为一组.
            result.append(resources[i:])
            break  # 终止分配
    return result  # 返回结果
