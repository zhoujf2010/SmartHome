
from __future__ import annotations
from aiohttp import web
from webFrame.baseview import BaseView, route
from ipaddress import ip_address
from datetime import timedelta
import voluptuous as vol
import webFrame.commontool as tool
import logging
import json

HTTP_BAD_REQUEST = 400
HTTP_Forbidden = 403
HTTP_OK = 200

_LOGGER = logging.getLogger(__name__)

class LoginView(BaseView):
    """登陆页视图."""
    name = "LoginView"

    def __init__(self, app):
        # self._store = app.store
        self.app = app

    @route("/api/discovery_info")
    async def getDiscovery(self, request):
        """登陆页基本信息"""
        data = {
            'name': 'Home Assistant Local',
            "location_name": "你好",
            "version": "1.0",
        }
        return self.json_result(data)

    @route("/auth/login_flow", methods=['POST'])
    async def postLoginFlow(self, request):
        """创建登陆流程，通常是打开登陆页，会分配一个flowID，用于后面的验证."""
        data = await tool.getDataFromRequest(request, vol.Schema(
            {vol.Required("client_id"): str, vol.Required("redirect_uri"): str}
        ))

        result = await self.app.tokenMgr.startLoginFlow({"ip_address": ip_address(request.remote)})
        return self.json_result(self._prepare_result_json(result))

    @route("/auth/login_flow/{flow_id}", methods=['POST'])
    async def postLoginFlowID(self, request, flow_id):
        """处理 提交登陆逻辑."""
        data = await tool.getDataFromRequest(request, vol.Schema({"client_id": str}, extra=vol.ALLOW_EXTRA))
        client_id = data.pop("client_id")

        result = await self.app.tokenMgr.async_configure(flow_id, data, 
                    self.app.userMgr.getUserInfoByInputData)

        if result.get("errors") is not None:
            return self.json_result(result)

        result.pop("data")
        # 临时保存Credentials信息至服务端,并返回code用于获取用户信息的凭证
        result["result"] = self.app.tokenMgr.store_result(client_id, result["result"])

        return self.json_result(result)

    @route("/auth/login_flow/{flow_id}", methods=['DELETE'])
    async def delete(self, request, flow_id):
        """Cancel a flow in progress."""
        self.app.tokenMgr.async_abort(flow_id)
        return self.json_result( {"message": "Flow aborted"})


class TokenView(BaseView):
    """View to issue or revoke tokens."""

    url = "/auth/token"
    name = "api:auth:token"
    requires_auth = False
    cors_allowed = True

    def __init__(self, app):
        """Initialize the token view."""
        self.app = app

    async def post(self, request):
        """Grant a token."""
        data = await request.post()

        grant_type = data.get("grant_type")

        # IndieAuth 6.3.5
        # The revocation endpoint is the same as the token endpoint.
        # The revocation request includes an additional parameter,
        # action=revoke.
        if data.get("action") == "revoke":
            return await self._async_handle_revoke_token(self.app, data)

        if grant_type == "authorization_code":  #生成token
            return await self._async_handle_auth_code(self.app, data, request.remote)

        if grant_type == "refresh_token": #刷新token
            return await self._async_handle_refresh_token(self.app, data, request.remote)

        return self.json_result(
            {"error": "unsupported_grant_type"}, status_code=HTTP_BAD_REQUEST
        )

    async def _async_handle_revoke_token(self, hass, data):
        """Handle revoke token request."""
        # OAuth 2.0 Token Revocation [RFC7009]
        # 2.2 The authorization server responds with HTTP status code 200
        # if the token has been revoked successfully or if the client
        # submitted an invalid token.
        token = data.get("token")

        if token is None:
            return web.Response(status=HTTP_OK)

        refresh_token = await self.app.tokenMgr.async_get_refresh_token_by_token(token)

        if refresh_token is None:
            return web.Response(status=HTTP_OK)

        await self.app.tokenMgr.async_remove_refresh_token(refresh_token)
        return web.Response(status=HTTP_OK)

    async def _async_handle_auth_code(self, hass, data, remote_addr):
        """Handle authorization code request."""
        client_id = data.get("client_id")
        if client_id is None:  # or not verify_client_id(client_id):
            return self.json_result(
                {"error": "invalid_request", "error_description": "Invalid client id"},
                status_code=HTTP_BAD_REQUEST,
            )

        code = data.get("code")

        if code is None:
            return self.json_result(
                {"error": "invalid_request", "error_description": "Invalid code"},
                status_code=HTTP_BAD_REQUEST,
            )
        
        user = self.app.tokenMgr.retrieve_result(client_id, code)

        if user is None:
            return self.json_result(
                {"error": "invalid_request", "error_description": "Invalid user info"},
                status_code=HTTP_Forbidden,
            )

        refresh_token = await self.app.tokenMgr.async_create_refresh_token(user, client_id, timedelta(minutes=30))

        access_token = self.app.tokenMgr.async_create_access_token(
            refresh_token, remote_addr
        )

        _LOGGER.info("用户登陆:" + user["name"])
        return self.json_result(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "refresh_token": refresh_token.token,
                "expires_in": int(refresh_token.access_token_expiration.total_seconds()),
            }
        )

    async def _async_handle_refresh_token(self, hass, data, remote_addr):
        """Handle authorization code request."""
        client_id = data.get("client_id")
        if client_id is not None: 
            return self.json_result(
                {"error": "invalid_request", "error_description": "Invalid client id"},
                status_code=HTTP_BAD_REQUEST,
            )

        token = data.get("refresh_token")

        if token is None:
            return self.json_result({"error": "invalid_request"}, status_code=HTTP_BAD_REQUEST)

        refresh_token = await hass.auth.async_get_refresh_token_by_token(token)

        if refresh_token is None:
            return self.json({"error": "invalid_grant"}, status_code=HTTP_BAD_REQUEST)

        if refresh_token.client_id != client_id:
            return self.json({"error": "invalid_request"}, status_code=HTTP_BAD_REQUEST)

        access_token = hass.auth.async_create_access_token(
            refresh_token, remote_addr
        )

        return self.json_result(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": int(
                    refresh_token.access_token_expiration.total_seconds()
                ),
            }
        )

