"""python3.6"""
from Crypto.Cipher import AES
from hashlib import md5
from urllib.parse import unquote
import base64


def redress(content):
    """矫正内容长度,以'0'填充.长度为block_size的倍数
    For `MODE_OPENPGP`, *plaintext* must be a multiple of *block_size*,
           unless it is the last chunk of the message
    :param content:密钥
    :return:矫正后的密钥
    """
    block_size = AES.block_size  # aes数据分组长度为128 bit
    return content + (block_size - len(content) % block_size) * '0'


class Aes:
    """高级加密标准（Advanced Encryption Standard，AES）"""

    def __init__(self, key):
        """:param key: 密钥,长度128位字符串.
        """
        self._m = md5(key.encode())  # 初始化实例
        self.key = self._m.digest()  # 加密密钥生成AES.key
        self.mode = AES.MODE_ECB  # dingdong使用ECB模式加密

    def encrypt(self, plaintext: str) -> bytes:
        """加密
        :param plaintext: 纯文本
        :return: 密文
        """
        cipher = AES.new(self.key, self.mode)
        cipher_text = cipher.encrypt(redress(plaintext))
        return cipher_text

    def decrypt(self, cipher_text: bytes) -> str:
        """解密
        :param cipher_text:密文
        :return:纯文本
        """
        cipher = AES.new(self.key, self.mode)
        plaintext = cipher.decrypt(cipher_text)
        return plaintext.decode()


#  示例
aes = Aes(key='你的128位AesKey')
state = unquote('state_value')  # 对回调参数state的值进行url解码
mi = base64.b64decode(state)  # 密文
result = aes.decrypt(mi)  # 解密,返回结果
print(result)
print(type(result))