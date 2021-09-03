
from webFrame.userManage import UserManage
from typing import Any
import uuid
from collections import OrderedDict
import voluptuous as vol
import json

class WxUserManage(UserManage):
    def __init__(self,app) -> None:
        self.app = app
        self.cacheUser = []

    def getSchema(self):
        schema: dict[str, type] = OrderedDict()
        schema["code"] = str
        return vol.Schema(schema)

    async def getUserInfoByInputData(self,user_input):
        code = user_input["code"]
        if code == '':
            raise Exception("code不正确")

        if len(self.cacheUser) ==0:
            await self.loadUsers()

        openid = self.app.wxManage.getOpenID(code)

        userfind = None
        for item in self.cacheUser:
            if item["openid"] == openid:
                userfind = item
                break;
        if userfind == None:
            raise Exception("用户未登记")

        user =  userfind
        return user

    async def loadUsers(self):
        data = json.load(open(self.app.rootPath + "/data/user.json",encoding="utf-8"))
        self.cacheUser = data
        for item in data:
            item["id"] = uuid.uuid4().hex

    