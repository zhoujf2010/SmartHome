
from __future__ import annotations

import asyncio
from aiohttp import web
import json
from re import template
import logging
from typing import Any, Callable
import datetime
from aiohttp.typedefs import LooseHeaders
import voluptuous_serialize
from webFrame.commontool import JSONEncoder

from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
    HTTPUnauthorized,
    HTTPOk
)

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

HTTP_OK = 200

def route(rule: str, **options: Any) -> Callable:
    options["rule"] = rule
    if "methods" not in options:
        options["methods"] = ["GET"]
    def decorator(f: Callable) -> Callable:
        setattr(f, "_options", options)
        return f
    return decorator
    

class BaseView: #HomeAssistantView
    """Base view for all views."""

    extra_urls: list[str] = []
    requires_auth = True
    cors_allowed = False

    @staticmethod
    def json_result(result: Any,status_code: int = HTTP_OK,headers: LooseHeaders | None = None) -> web.Response:
        """Return a JSON response."""
        try:
            msg = json.dumps(result, cls=JSONEncoder, allow_nan=False).encode("UTF-8")
        except (ValueError, TypeError) as err:
            _LOGGER.error("Unable to serialize to JSON: %s\n%s", err, result)
            raise HTTPInternalServerError from err
        return BaseView.result(msg,status_code,headers)

    @staticmethod
    def result(result: Any,status_code: int = HTTP_OK,headers: LooseHeaders | None = None) -> web.Response:
        """Return a JSON response."""
        msg = result
        response = web.Response(
            body=msg,
            content_type="application/json",
            status=status_code,
            headers=headers,
        )
        response.enable_compression()
        return response
        
    def _prepare_result_json(self,result):
        """Convert result to JSON."""
        if result["type"] == "create_entry":
            data = result.copy()
            data.pop("result")
            data.pop("data")
            return data

        if result["type"] != "form":
            return result

        data = result.copy()

        schema = data["data_schema"]
        if schema is None:
            data["data_schema"] = []
        else:
            data["data_schema"] = voluptuous_serialize.convert(schema)

        return data

    def register(self, app: web.Application, router: web.UrlDispatcher) -> None:
        """Register the view with a router."""

        routes = []
        if not hasattr(self, "url"):#新模式，扫描所有方法
            for name in dir(self):
                handler = getattr(self,name, None)
                dd = getattr(handler, "_options", None)
                if dd is not None:
                    handler = request_handler_factory(self, handler)
                    for method in dd["methods"]:
                        routes.append(router.add_route(method, app.appName + dd["rule"], handler))
        else:

            assert self.url is not None, "No url set for view"
            urls = [self.url] + self.extra_urls

            for method in ("get", "post", "delete", "put", "patch", "head", "options"):
                handler = getattr(self, method, None)

                if not handler:
                    continue

                handler = request_handler_factory(self, handler)

                for url in urls:
                    routes.append(router.add_route(method, app.appName + url, handler))

        if not self.cors_allowed:
            return

        # for route in routes:
        #     app["allow_cors"](route)

def request_handler_factory(view: BaseView, handler: Callable) -> Callable:
    """Wrap the handler classes."""
    assert asyncio.iscoroutinefunction(handler), "Handler should be a coroutine."

    async def handle(request: web.Request) -> web.StreamResponse:
        """Handle incoming request."""
        try:
            result = handler(request, **request.match_info)

            if asyncio.iscoroutine(result):
                result = await result
        except vol.Invalid as err:
            raise HTTPBadRequest() from err

        if isinstance(result, web.StreamResponse):
            # The method handler returned a ready-made Response, how nice of it
            return result

        status_code = HTTP_OK

        if isinstance(result, tuple):
            result, status_code = result

        if isinstance(result, bytes):
            bresult = result
        elif isinstance(result, str):
            bresult = result.encode("utf-8")
        elif result is None:
            bresult = b""
        else:
            assert (
                False
            ), f"Result should be None, string, bytes or Response. Got: {result}"

        return web.Response(body=bresult, status=status_code)

    return handle