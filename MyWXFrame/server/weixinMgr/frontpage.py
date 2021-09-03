
from __future__ import annotations
from re import template
from aiohttp import  web, web_urldispatcher
from yarl import URL
import jinja2
from webFrame.baseview import BaseView
from webFrame.webapp import webapp


async def async_setup(app:webapp, rootpath):


    #注册静态资源
    for path in ["js","css","img","static"]:
        app.register_static_path(f"/{path}", rootpath +"/" + path)

    #注册功能页面处理
    app.register_view(IndexView(rootpath, app))



class IndexView(web_urldispatcher.AbstractResource):
    """Serve the frontend."""

    def __init__(self, rootpath, app):
        """Initialize the frontend view."""
        super().__init__(name="frontend:index")
        self.rootpath = rootpath
        self.app = app
        self._template_cache = None

    @property
    def canonical(self) -> str:
        """Return resource's canonical path."""
        return self.app.appName

    @property
    def _route(self):
        """Return the index route."""
        return web_urldispatcher.ResourceRoute("GET", self.get, self)

    def url_for(self, **kwargs: str) -> URL:
        """Construct url for resource with additional params."""
        return URL(self.app.appName)

    async def resolve(
        self, request: web.Request
    ) -> tuple[web_urldispatcher.UrlMappingMatchInfo | None, set[str]]:
        """Resolve resource.

        Return (UrlMappingMatchInfo, allowed_methods) pair.
        """
        # code = request.query.get("code")
        # print("code=" + code)
        return web_urldispatcher.UrlMappingMatchInfo({}, self._route), {"GET"}

    def add_prefix(self, prefix: str) -> None:
        """Add a prefix to processed URLs.

        Required for subapplications support.
        """

    def get_info(self):
        """Return a dict with additional info useful for introspection."""
        return {"panels": list(self.hass.data["panels"])}

    def freeze(self) -> None:
        """Freeze the resource."""

    def raw_match(self, path: str) -> bool:
        """Perform a raw match against path."""

    def get_template(self):
        """Get template."""
        tpl = self._template_cache
        if tpl is None:
            with open(self.rootpath + "/index.html") as file:
                tpl = jinja2.Template(file.read())
            # self._template_cache = tpl

        return tpl

    async def get(self, request: web.Request) -> web.Response:
        """Serve the index page for panel pages."""
        template = self.get_template()


        return web.Response(
            text=template.render(),
            content_type="text/html",
        )

    def __len__(self) -> int:
        """Return length of resource."""
        return 1

    def __iter__(self):
        """Iterate over routes."""
        return iter([self._route])
