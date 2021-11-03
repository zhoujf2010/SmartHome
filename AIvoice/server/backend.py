
from __future__ import annotations

from webFrame.websocketView import WebsocketAPIView
from webFrame.loginview import LoginView, TokenView
from webFrame.baseview import BaseView, route
import json
from urllib.parse import unquote
from shutil import copyfile


async def async_setup(app):
    app.register_view(DataView(app))


class DataView(BaseView):
    """登陆页视图."""
    name = "DataView"

    def __init__(self, app):
        # self._store = app.store
        self.app = app

    @route("/api/entityTypes")
    async def getentityTypes(self, request):
        """实体类型"""
        fo = open("./data/entityTypes.json", "r", encoding="utf-8")
        data = fo.read()
        fo.close()
        return self.result(data)

    @route("/api/entityTypes" , methods=['POST'])
    async def postentityTypes(self, request):
        """实体类型"""
        data = await request.text()
        fo = open("./data/entityTypes.json", "w", encoding="utf-8")
        fo.write(data)
        fo.close()
        return self.result("OK")

    @route("/api/intentTypes")
    async def getintentTypes(self, request):
        """意图类型列表"""
        fo = open("./data/intentTypes.json", "r", encoding="utf-8")
        data = fo.read()
        fo.close()
        self.app.eventBus.async_fire("configchange",None)
        return self.result(data)

    @route("/api/intentTypes" , methods=['POST'])
    async def postintentTypes(self, request):
        """意图类型列表"""
        data = await request.text()
        fo = open("./data/intentTypes.json", "w", encoding="utf-8")
        fo.write(data)
        fo.close()
        self.app.eventBus.async_fire("configchange",None)
        return self.result("OK")

    @route("/api/messages")
    async def getMessages(self, request):
        """列表数据"""
        fo = open("./data/intent.json", "r", encoding="utf-8")
        intent = json.loads(fo.read())

        fo = open("./data/slot.json", "r", encoding="utf-8")
        slot = json.loads(fo.read())

        slotmap = {}
        for item in slot:
            slotmap[item["content"]] = item["target"]

        data = []
        for item in intent:
            newitem = {}
            newitem["message"] = item["content"]
            if newitem["message"] in slotmap:
                newitem["entities"] = slotmap[newitem["message"]]
            else:
                newitem["entities"] = []

            newitem["labeltype"] = item["labeltype"]
            newitem["labeltype_hat"] = ""
            data.append(newitem)

        return self.json_result(data)

    @route("/api/data", methods=['POST'])
    async def saveData(self, request):
        """保存数据"""
        data = await request.json()
        messages = data["messages"]
        intent = []
        slot = []
        for item in messages:
            intent.append({"content": item["message"], "labeltype": item["labeltype"]})
            if  len(item["entities"]) >0:
                slot.append({"content": item["message"], "target": item["entities"]})

        copyfile("./data/intent.json", "./data/intent_bak.json")
        fo = open("./data/intent.json", "w", encoding="utf-8")
        fo.write(json.dumps(intent, indent=4, ensure_ascii=False))

        copyfile("./data/slot.json", "./data/slot_bak.json")
        fo = open("./data/slot.json", "w", encoding="utf-8")
        fo.write(json.dumps(slot, indent=4, ensure_ascii=False))

        # print(json.dumps(data, indent=4, ensure_ascii=False))

        ret = {"result": "OK"}
        return self.json_result(ret)
