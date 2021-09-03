
from __future__ import annotations
import asyncio
import json
from typing import Any
import uuid
import jwt
from typing import Any,  cast
import webFrame.commontool as tool
import hmac
import datetime as dt
import attr
from datetime import datetime, timedelta
import secrets
from webFrame.commontool import __version__,utcnow
import logging

_LOGGER = logging.getLogger(__name__)

@attr.s(slots=True)
class RefreshToken:
    """RefreshToken for a user to grant new access tokens."""

    user: Any = attr.ib()
    client_id: str | None = attr.ib()
    access_token_expiration: timedelta = attr.ib()
    token_type: str  | None = attr.ib(default=None)
    id: str = attr.ib(factory=lambda: uuid.uuid4().hex)
    created_at: datetime = attr.ib(factory=utcnow)
    token: str = attr.ib(factory=lambda: secrets.token_hex(64))
    jwt_key: str = attr.ib(factory=lambda: secrets.token_hex(64))

    last_used_at: datetime | None = attr.ib(default=None)
    last_used_ip: str | None = attr.ib(default=None)

    version: str | None = attr.ib(default=__version__)


class LoginFlow():
    def __init__(self) -> None:
        """Initialize the login flow."""
        self._auth_provider = ""
        self._auth_module_id: str | None = None
        self._auth_manager = ""#auth_provider.hass.auth
        self.available_mfa_modules: dict[str, str] = {}
        self.created_at = utcnow()
        self.invalid_mfa_times = 0
        self.user  = None
        self.credential = None
        self.init_step = "init"


class tokenManager:
    def __init__(self, app) -> None:
        self.app = app
        self._initializing: list[asyncio.Future] = []
        self._progress: dict[str, Any] = {}
        self.temp_results = {} #缓存访问进入
        self.loginUsersCache = [] #登陆用户缓存

    async def startLoginFlow(self, context: dict | None = None, data: Any = None):
        """初使化登陆流程"""
        if context is None:
            context = {}

        init_done: asyncio.Future = asyncio.Future()
        self._initializing.append(init_done)

        flow = LoginFlow()
        flow.flow_id = uuid.uuid4().hex
        flow.context = context
        self._progress[flow.flow_id] = flow

        try:
            result:dict ={
                "type": "form",
                "flow_id": flow.flow_id,
                "step_id": "init",
                "data_schema": self.app.userMgr.getSchema(),
            }
            init_done.set_result(None)
            flow.cur_step = result
        finally:
            self._initializing.remove(init_done)
        return result

    async def async_configure(
            self, flow_id: str, user_input: dict, checkIndentity):
        """提交登陆，并验证登陆信息."""
        flow = self._progress.get(flow_id)

        if flow is None:
            return {"errors": "登陆异常，请刷新页面"}

        cur_step = flow.cur_step

        if cur_step.get("data_schema") is not None and user_input is not None:
            user_input = cur_step["data_schema"](user_input)
        try:
            user = await checkIndentity(user_input)
        except Exception as e:
            _LOGGER.error("尝试用户登陆失败:" + json.dumps(user_input) + ":" + str(e))
            return {"errors": str(e)}

        result = {
            "type": "create_entry",
            "flow_id": flow.flow_id,
            "title": user["name"],
            "data": user_input,
            "result": user
        }
        self._progress.pop(flow.flow_id)
        return result

    def store_result(self, client_id, result):
        """临时保存登陆票据信息至服务端  并返回code，用于取回信息."""
        result_type = "user"
        code = uuid.uuid4().hex
        self.temp_results[(client_id, result_type, code)] = (
            tool.utcnow(),
            result_type,
            result,
        )
        return code

    def retrieve_result(self, client_id, code):
        """取回临时保存的登陆票据信息."""
        result_type = "user"
        key = (client_id, result_type, code)

        if key not in self.temp_results:
            return None

        created, _, result = self.temp_results.pop(key)

        # OAuth 4.2.1
        # The authorization code MUST expire shortly after it is issued to
        # mitigate the risk of leaks.  A maximum authorization code lifetime of
        # 10 minutes is RECOMMENDED.
        if tool.utcnow() - created < timedelta(minutes=10):
            return result

        return None

    async def async_create_refresh_token(
        self,
        user: Any,
        client_id: str | None = None,
        access_token_expiration: timedelta = timedelta(minutes=30)
    ) -> RefreshToken:
        '''创建更新token'''
        kwargs: dict[str, Any] = {
            "user": user,
            "client_id": client_id,
            "token_type": "normal", 
            "access_token_expiration": access_token_expiration,
        }

        refresh_token = RefreshToken(**kwargs)

        hasfind = False
        for find in self.loginUsersCache:
            if find["id"] == user["id"]:
                hasfind = True
                break
        if not hasfind:
            self.loginUsersCache.append(user)

        if not hasattr(user,"refresh_tokens"):
            user["refresh_tokens"] = {}
        
        user["refresh_tokens"][refresh_token.id] = refresh_token

        return refresh_token


    def async_create_access_token(
        self, refresh_token, remote_ip: str | None = None
    ) -> str:
        """创建访问token."""
        refresh_token.last_used_at =  dt.datetime.now( dt.timezone.utc)#.utcnow()
        refresh_token.last_used_ip = remote_ip

        now = tool.utcnow()
        return jwt.encode(
            {
                "iss": refresh_token.id,
                "iat": now,
                "exp": now + refresh_token.access_token_expiration,
            },
            refresh_token.jwt_key,
            algorithm="HS256",
        ).decode()

    async def get_User_by_token(self,token):
        found = None

        for user in self.loginUsersCache:
            for refresh_token in user["refresh_tokens"].values():
                if hmac.compare_digest(refresh_token.token, token):
                    found = user
        return found

    async def async_get_refresh_token_by_token(
        self, token: str
    ) -> RefreshToken | None:
        found = None

        for user in self.loginUsersCache:
            for refresh_token in user["refresh_tokens"].values():
                if hmac.compare_digest(refresh_token.token, token):
                    found = refresh_token

        return found

    async def async_remove_refresh_token(self,refreshtoken:RefreshToken):
        user = await self.get_User_by_token(refreshtoken.token)
        if refreshtoken.id in user["refresh_tokens"]:
            user["refresh_tokens"].pop(refreshtoken.id)

    async def async_get_refresh_token(
        self, token_id: str
    ) -> RefreshToken | None:
        """Get refresh token by id."""
        for user in self.loginUsersCache:
            refresh_token = user["refresh_tokens"].get(token_id)
            if refresh_token is not None:
                return refresh_token

        return None

    async def async_validate_access_token(
        self, token: str
    ):
        """Return refresh token if an access token is valid."""
        try:
            unverif_claims = jwt.decode(token, verify=False)
        except jwt.InvalidTokenError:
            return None

        refresh_token = await self.async_get_refresh_token(
            cast(str, unverif_claims.get("iss"))
        )

        if refresh_token is None:
            jwt_key = ""
            issuer = ""
        else:
            jwt_key = refresh_token.jwt_key
            issuer = refresh_token.id

        try:
            jwt.decode(token, jwt_key, leeway=10, issuer=issuer, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None

        return refresh_token
