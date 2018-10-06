# coding: utf-8
"""通用插件库"""


def flatten(x: Iterable):
    """多维数据降维,author:https://www.zhihu.com/question/63739026/answer/212712388
    :param x: 降维对象
    :return: 降维结果
    """
    for each in x:
        if not isinstance(each, Iterable) or isinstance(each, str):
            yield each
        else:
            yield from flatten(x=each)


def generate_only_id(length: int = 64) -> str:
    """生成唯一数字id
    :param length: id长度
    """
    timestamp = str(time.time()).replace('.', '')  # 毫秒级别唯一前缀(并发量不大的前提下,是唯一的.)
    result = ''
    for _ in range(length - len(timestamp)):  # 生成去除前缀长度的后缀
        result += str(random.randint(0, 9))
    return timestamp + result  # 组合返回


class Replay:
    """微信回复对象"""

    def __init__(self):
        self.data_ = self.get_dict()
        self.self = self.data_.get('ToUserName')
        self.user = self.data_.get('FromUserName')
        self.create_time = int(time.time())
        self.template_prefix = 'wechat_templates/'

    @staticmethod
    def get_dict():
        """解析xml为dict类型"""
        request_content = request.get_data()  # 获取xml内容
        dict_ = xmltodict.parse(request_content)  # 解析为dict类型的相同数据结构
        return dict_.get('xml')  # xml为外层标签,无用.直接返回内容

    def send_text(self, to_user_name: str = None, from_user_name: str = None, content: str = None):
        """发送文本消息
        :param to_user_name: 发送给那个用户,默认为当前发起请求用户
        :param from_user_name: 公众号id
        :param content: 内容
        """
        self.self = from_user_name or self.self
        self.user = to_user_name or self.user
        self.content = content or 'success'
        self.template = self.send_text
        return self

    def send_image(self, to_user_name: str = None, from_user_name: str = None, media_id: str = None):
        """发送图片消息
        :param to_user_name: 发送给那个用户,默认为当前发起请求用户
        :param from_user_name: 公众号id
        :param media_id: 图片在腾讯公众号素材库中的id
        :return:
        """
        self.self = from_user_name or self.self
        self.user = to_user_name or self.user
        self.media_id = media_id or self.data_.get('MediaId')
        self.template = self.send_image
        return self

    def send(self):
        """判断之前操作的方法,选择不同的模板"""
        if self.template == self.send_text:
            # 设置模板所需参数
            data = {
                'self': self.self,
                'user': self.user,
                'content': self.content,
                'template': self.template_prefix + self.template.__name__
            }
            return render_template('wechat_templates/wechat_text_template.xml', data=data)

        elif self.template == self.send_image:
            # 设置模板所需参数
            data = {
                'self': self.self,
                'user': self.user,
                'media_id': self.media_id,
                'template': self.template_prefix + self.template.__name__
            }
            return render_template('wechat_templates/wechat_text_template.xml', data=data)
