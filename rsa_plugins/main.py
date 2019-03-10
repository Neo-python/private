import rsa, base64, datetime


class RsaKeys:
    """rsa加密 公私秘钥对象"""

    def __init__(self, public_filename='public.pem', private_filename='private.pem'):
        """还原公私秘钥"""
        with open(public_filename, 'r', encoding='utf-8') as pem:
            self.public = rsa.PublicKey.load_pkcs1(pem.read().encode())
        with open(private_filename, 'r', encoding='utf-8') as pem:
            self.private = rsa.PrivateKey.load_pkcs1(pem.read().encode())

    @staticmethod
    def generate():
        """生成rsa秘钥文件"""
        public_pem, private_pem = rsa.newkeys(1024)

        with open('private.pem', 'w') as f:
            f.write(private_pem.save_pkcs1().decode())

        with open('public.pem', 'w') as f:
            f.write(public_pem.save_pkcs1().decode())


class Token:
    """登录缓存秘钥"""

    def __init__(self, original_text: str, deadline: datetime.datetime):
        """
        :param original_text: token信息,一般情况为账户
        :param deadline:token过期时限,一般情况下,可以使用set_deadline快速设置
        """
        self.original_text = original_text
        self.deadline = deadline
        self.model = None

    @staticmethod
    def set_deadline(deadline: dict) -> datetime.datetime:
        """快速设置期限
        :param deadline: dict类型,example:{'days':-1} or {'seconds':10}
        :return:
        """
        return datetime.datetime.now() + datetime.timedelta(**deadline)

    def encryption(self) -> bytes:
        """加密"""
        keys = RsaKeys()
        message = f'{self.original_text},{self.deadline.strftime("%Y-%m-%d %H:%M:%S")}'
        token = rsa.encrypt(message.encode(), keys.public)
        return token

    def encryption_to_string(self) -> str:
        """返回utf8格式内容"""
        return base64.b64encode(self.encryption()).decode()

    @staticmethod
    def decrypt(token: bytes):
        """解密"""
        keys = RsaKeys()
        message = rsa.decrypt(crypto=token, priv_key=keys.private).decode()
        original_text, deadline = message.split(',')
        return Token(original_text=original_text, deadline=datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def string_decrypt(token: str):
        """utf8格式内容解密"""
        return Token.decrypt(base64.b64decode(token.encode()))
