
from __future__ import annotations

import logging
from webFrame.loginview import TokenView, LoginView
from webFrame.websocketView import WebsocketAPIView
from webFrame.baseview import BaseView

_LOGGER = logging.getLogger(__name__)


async def async_setup(app, WxCommand):

    app.register_view(LoginView(app))

    app.register_view(TokenView(app))

    app.register_view(WebsocketAPIView(app, commonHandle))

    # 注册微信消息处理服务
    app.register_view(WeixinServiceView(app, WxCommand))

    app.hassclient.register_event_callback(createEventHandler(app))


def createEventHandler(app):
    def log_events(event: str, event_data: dict):
        """Log node value changes."""
        if not hasattr(app, "eventID"):
            return
        dt = {"id": app.eventID, "type": "event", "event": {"event_type": event, "data": event_data}}
        for client in app.CurrentWSClients:
            client.send_message(dt)
    return log_events


async def commonHandle(app, socketclient, type, msg):
    if type == "lovelace/config":
        ret = await app.hassclient.send_command({"type": "lovelace/config", "url_path": app.rooturlpath})
        ret["id"] = msg["id"]
        socketclient.send_message(ret)
    elif type == "get_states":
        ret = await app.hassclient.send_command({"type": "get_states"})
        ret["id"] = msg["id"]
        socketclient.send_message(ret)
    elif type == "subscribe_events":
        app.eventID = msg["id"]
        await app.hassclient.send_command(msg)
    elif type == "call_service":
        ret = await app.hassclient.send_command(msg)
        ret["id"] = msg["id"]
        socketclient.send_message(ret)
    else:
        _LOGGER.error("unkown Type=========>"+type)
        socketclient.send_message({"id": msg["id"], "type": "pong"})


class WeixinServiceView(BaseView):
    """微信服务."""

    requires_auth = False
    url = "/weixin/service"
    name = "api:service"

    def __init__(self, app,WxCommand):
        self.app = app
        self.WxCommand = WxCommand

    async def get(self, request):
        """获取发现信息."""
        signature = request.query.get("signature", "")
        timestamp = request.query.get("timestamp", "")
        nonce = request.query.get("nonce", "")
        echo_str = request.query.get("echostr", "")

        if not self.app.wxManage.check_signature(signature, timestamp, nonce):
            return self.json_result({"error": "access_denied"}, status_code=403,)

        return self.result(echo_str)

    async def post(self, request):
        """接受微信命令"""
        timestamp = request.query.get("timestamp", "")
        nonce = request.query.get("nonce", "")
        msg_signature = request.query.get("msg_signature", "")
        signature = request.query.get("signature", "")

        if not self.app.wxManage.check_signature(signature, timestamp, nonce):
            return self.json_result({"error": "access_denied"}, status_code=403,)

        txt = await request.text()
        msg = self.app.wxManage.decrypt_message(txt, msg_signature, timestamp, nonce)

        ret = await self.WxMsgDeal(msg)  # 调用外部处理，交换处理信息

        ret = self.app.wxManage.encrypt_message(msg, ret, timestamp, nonce)
        return self.result(ret)

    async def WxMsgDeal(self,msg):
        if msg.type == "text":
            ret = await self.WxCommand(msg.content)
        elif msg.type == "voice":
            ret = await self.WxCommand(msg.recognition)
        else:
            ret = "Sorry, can not handle this for now"
        return ret
