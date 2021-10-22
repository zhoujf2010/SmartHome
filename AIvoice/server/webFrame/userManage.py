
from typing import Any
import uuid
from collections import OrderedDict
import voluptuous as vol


# @attr.s(slots=True)
# class User:
#     """A user."""

#     name: str | None = attr.ib()
#     perm_lookup = attr.ib(eq=False, order=False)
#     id: str = attr.ib(factory=lambda: uuid.uuid4().hex)
#     is_owner: bool = attr.ib(default=False)
#     is_active: bool = attr.ib(default=False)
#     system_generated: bool = attr.ib(default=False)

#     # groups: list[Group] = attr.ib(factory=list, eq=False, order=False)

#     # List of credentials of a user.
#     credentials: list[Credentials] = attr.ib(factory=list, eq=False, order=False)

#     # Tokens associated with a user.
#     refresh_tokens = attr.ib(
#         factory=dict, eq=False, order=False
#     )


class UserManage():
    def __init__(self,app) -> None:
        self.app = app

    def getSchema(self):
        schema: dict[str, type] = OrderedDict()
        schema["username"] = str
        schema["password"] = str
        return vol.Schema(schema)

    async def getUserInfoByInputData(self,user_input):
        if user_input["username"] != 'a':
            raise Exception("密码不对")

        kwargs: dict[str, Any] = {
            "name": user_input["username"],
            "perm_lookup":""
        }
        # user = User(**kwargs)
        user =  {
            "name": user_input["username"],
            "perm_lookup":"",
            "id":  uuid.uuid4().hex
        }
        user_input.pop("password")
        return user