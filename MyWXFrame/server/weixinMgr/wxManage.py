from wechatpy.crypto import WeChatCrypto
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.exceptions import InvalidAppIdException
from webFrame.webapp import current_request
import requests
import json


class wxManage():
    def __init__(self) -> None:
        self.AppId = "wxaf792784650e9b95"
        self.TOKEN = "aaabbbccc"
        self.EncodingAESKey = "aSji9G7hRb7hLz8NaHB8DqNVcxkVDqKKTBnebQ3NJaD"
        self.crypto = WeChatCrypto(self.TOKEN, self.EncodingAESKey, self.AppId)
        self.secret = "0c9c1281db26a2fa723e8037f39d34b0"

    def check_signature(self, signature, timestamp, nonce):
        try:
            check_signature(self.TOKEN, signature, timestamp, nonce)
            return True
        except InvalidSignatureException:
            return False

    def decrypt_message(self, msg, msg_signature, timestamp, nonce):
        try:
            msg = self.crypto.decrypt_message(msg, msg_signature, timestamp, nonce)
        except (InvalidSignatureException, InvalidAppIdException) as e:
            raise Exception("数据解析出错", e)
        msg = parse_message(msg)
        return msg

    def encrypt_message(self, msg, content, timestamp, nonce):
        reply = create_reply(content, msg)
        ret = self.crypto.encrypt_message(reply.render(), nonce, timestamp)
        return ret

    def getOpenID(self, code):
        """
        获取OpenID,
        openid是微信用户在公众号appid下的唯一用户标识
        """
        url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=" + \
            self.AppId + "&secret=" + self.secret + "&code=" + code + "&grant_type=authorization_code"
        dt = requests.get(url).json()
        if "errmsg" in dt:
            raise Exception(dt["errmsg"])
        openid = dt["openid"]
        return openid

    def getaccess_token(self):
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + \
            self.AppId + "&secret=" + self.secret
        response = requests.get(url)
        dt = response.json()
        if "access_token" not in dt:
            print("Error:",dt)
            return ""
        access_token = dt["access_token"]
        return access_token

    def genLogUrl(self,url):
        # url = java.net.URLEncoder.encode(url, "UTF-8");
        ret = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=" + self.AppId + "&redirect_uri=" + url \
            + "&response_type=code&scope=snsapi_base&state=123#wechat_redirect"
        return ret

    def createMenu(self,menus):
        access_token = self.getaccess_token()
        print("access_token:", access_token)

        posturl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=" + access_token
        j_menu = json.dumps(menus, ensure_ascii=False)  # 添加ensure_ascii=False 参数

        ret = requests.post(posturl, data=j_menu.encode())
        return ret.json()