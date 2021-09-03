"""
通用web服务器.
"""

from __future__ import annotations
from aiohttp import web, web_urldispatcher
from aiohttp.web import middleware
import mimetypes
from contextvars import ContextVar
import logging
import os
from aiohttp.web_exceptions import HTTPMovedPermanently
from webFrame.tokenManager import tokenManager
from webFrame.userManage import UserManage

_LOGGER = logging.getLogger(__name__)

MAX_CLIENT_SIZE: int = 1024 ** 2 * 16

current_request: ContextVar[web.Request] = ContextVar(
    "current_request", default=None
)

class webapp:
    def __init__(self,server_port,appName="") -> None:
        self.app = web.Application(
            middlewares=[], client_max_size=MAX_CLIENT_SIZE
        )
        self.tokenMgr = tokenManager(self)
        self.userMgr = UserManage(self)

        mimetypes.add_type("text/css", ".css")
        mimetypes.add_type("application/javascript", ".js")
        self.server_port = server_port
        if appName !="" and appName[0] != "/":
            self.appName = "/" + appName
        else:
            self.appName ="/"
        self.app.appName = self.appName

        self.__setup_request_context(self.app, current_request)
        

    def __setup_request_context(self,app, context):
        """创建app中间件."""

        @middleware
        async def request_context_middleware(request, handler):
            """Request context middleware."""
            context.set(request)
            return await handler(request)

        app.middlewares.append(request_context_middleware)

    async def start(self):
        """启动web服务."""
        self.app._router.freeze = lambda: None
        self.runner = web.AppRunner(self.app,access_log=None)

        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "", self.server_port)

        try:
            await self.site.start()
        except OSError as error:
            _LOGGER.error(
                "Failed to create HTTP server at port %d: %s", self.server_port, error
            )

        _LOGGER.info("Now listening on port %d", self.server_port)
    
    async def stop(self):
        """停止web服务."""
        await self.site.stop()
        await self.runner.cleanup()

    def register_view(self, view):
        """注册一个视图."""
        if isinstance(view, type):
            view = view()# 传入的类，自动创建对象

        if isinstance(view, web_urldispatcher.AbstractResource):
            self.app.router.register_resource(view)
            return

        if not hasattr(view, "name"):
            class_name = view.__class__.__name__
            raise AttributeError(f'{class_name} missing required attribute "name"')

        view.register(self.app, self.app.router)

    def register_redirect(self, url, redirect_to, *, redirect_exc=HTTPMovedPermanently):
        """注册一个跳转."""
        async def redirect(request):
            raise redirect_exc(redirect_to)

        self.app.router.add_route("GET", url, redirect)
        
    def register_static_path(self, url_path, path):
        """注册一个静态资源."""
        if os.path.isdir(path):
            self.app.router.register_resource(web.StaticResource(self.appName.rstrip("/") + url_path, path))
            return

        async def serve_file(request):
            return web.FileResponse(path)

        self.app.router.add_route("GET", self.appName.rstrip("/") + url_path, serve_file)
