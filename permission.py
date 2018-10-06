# coding: utf-8
"""权限相关插件库"""


class Permission:
    """类装饰器基类"""

    def __init__(self, blueprint):
        """权初始化绑定参数
        :param blueprint: 蓝图名
        """
        self.blueprint = blueprint.name

    @staticmethod
    def admin_permission(level: int = 1) -> bool:
        """管理员权限验证函数
        :param level: 权限等级
        :return: 验证结果
        """
        admin_info = session.get('admin_info', None)
        if admin_info and admin_info.get('level', None) >= level:
            return True
        else:
            return False

    @staticmethod
    def user_permission(status: bool = None) -> bool:
        """用户权限验证函数
        :param status: 账户状态
        :return: 验证结果
        """
        user_info = session.get('user_info', None)
        if user_info and (user_info.get('status', None) is status or status is None):
            return True
        else:
            return False

    def __call__(self, permission_func, kwargs_, backtrack=None):
        """权限装饰器
        :param permission_func: 权限函数
        :param kwargs_: 权限函数的参数
        :param backtrack: 失败跳转的地址,优先通过url_for解析蓝图地址.无法解析,则尝试直接跳转地址.
        """

        def transfer_(func):
            @wraps(func)
            def inner(*args, **kwargs):
                if permission_func(**kwargs_):  # 检验权限
                    return func(*args, **kwargs)
                else:
                    nonlocal backtrack
                    if backtrack is None:  # 默认返回登录页面,传递请求地址,待登录后跳转
                        backtrack = f'{self.blueprint}.login'  # 登录页面蓝图参数
                        return redirect(url_for(backtrack) + f'?url={request.url}')
                    try:
                        return redirect(url_for(backtrack))  # 尝试当做蓝图地址解析
                    except BuildError as err:
                        print(err)
                        return redirect(backtrack)  # 直接跳转地址

            return inner

        return transfer_


class JuHeApi:
    """聚合数据话费充值api集合,文档地址:https://www.juhe.cn/docs/api/id/85"""
    tel_check_url = 'http://op.juhe.cn/ofpay/mobile/telcheck'  # 检测手机号是否能充值地址
    tel_query_url = 'http://op.juhe.cn/ofpay/mobile/telquery'  # 根据手机号和面值查询商品信息
    tel_recharge_url = 'http://op.juhe.cn/ofpay/mobile/onlineorder'  # 手机直充接口
    tel_order_status_url = 'http://op.juhe.cn/ofpay/mobile/ordersta'  # 订单状态查询

    def __init__(self, open_id: str, phone: str, app_key: str, order_id: str = None):
        self.open_id = open_id
        self.app_key = app_key
        self.phone = phone
        self.order_id = order_id if order_id else generate_only_id(length=32)
        self.url = None
        self.parameters = {}
        self.result = {}

    def call_check(self, amount: int = 1) -> bool or str:
        """检测手机号是否能充值
        :param amount: 充值金额,必须为整数.
        :return: True or error_reason
        """
        parameter = {
            'phoneno': self.phone,
            'cardnum': amount,
            'key': self.app_key
        }

        self.url = self.tel_check_url
        self.parameters = parameter
        return self

    def call_query(self, amount: int = 1):
        """根据手机号和面值查询商品信息"""
        parameter = {
            'phoneno': self.phone,
            'cardnum': amount
        }
        self.parameters = parameter
        self.url = self.tel_query_url
        return self

    def call_recharge(self, amount: int):
        """手机直充接口"""

        parameter = {
            'phoneno': self.phone,
            'cardnum': amount,
            'orderid': self.order_id,
            'key': self.app_key,
            'sign': self.generate_sign(amount=amount, order_id=self.order_id)
        }
        self.parameters = parameter
        self.url = self.tel_recharge_url
        return self

    def call_order_query(self):
        """订单状态查询"""
        parameter = {
            'orderid': self.parameters.get('orderid')
        }
        self.parameters = parameter
        self.url = self.tel_order_status_url
        return self

    def execution(self):
        """执行请求,返回True或False"""
        req = requests.get(self.url, params=self.parameters)
        self.result = json.loads(req.text)  # 接口返回的是json格式数据,转换为dict.

        if self.result.get('error_code', 1) == 0:  # 没有错误,此接口的error_code会返回0
            """表明查询成功"""
            return True
        else:
            """查询失败"""
            print('request_url -> ', req.url)
            return False

    def generate_sign(self, amount: int, order_id: str) -> str:
        """生成校验值"""
        values = f'{self.open_id}{self.app_key}{self.phone}{amount}{order_id}'
        md5 = hashlib.md5()  # 初始化md5算法实例
        md5.update(values.encode())  # 更新加密内容
        return md5.hexdigest()  # 加密结果


def get_assistant(answer):
    """获取缓存中的助手对象.如果存在助手.提取出来,通过pickle从字节转化为实体对象.
    :param answer: 请求体,获取对话sessionID,以此ID查找助手对象.
    :return:返回助手
    """
    session_id = answer.get('session').get('session_id')
    recording = qst_redis.get(session_id)  # 记录
    if recording:
        assistant = pickle.loads(eval(recording))  # 将类型为str的值转为bytes,再通过pickle转换成assistant对象
        assistant.collect(answer=answer)
        assistant.is_end = 'false'
    else:
        assistant = VoiceAssistant()
        assistant.collect(answer=answer)
        assistant.is_end = 'false'
    return assistant
