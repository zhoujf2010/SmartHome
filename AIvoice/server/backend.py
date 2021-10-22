
from __future__ import annotations

from webFrame.websocketView import WebsocketAPIView
from webFrame.loginview import LoginView,TokenView

async def async_setup(app):

    app.register_view(LoginView(app))

    app.register_view(TokenView(app))

    app.register_view(WebsocketAPIView(app,commonHandle))


async def  commonHandle(app,socketclient, type, msg):
    if type =="ping":
        socketclient.send_message({"id": msg["id"], "type": "pong"})
        return
    
    print("unkown Type=========>",type)
    socketclient.send_message({"id": msg["id"], "type": "pongxxx"})


