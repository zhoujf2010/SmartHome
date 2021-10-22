
from __future__ import annotations
import pathlib
from aiohttp import hdrs, web, web_urldispatcher
from yarl import URL
import jinja2


async def async_setup(app,rootpath):
    #注册静态资源
    for path in ["js","css","img","static"]:
        app.register_static_path(f"/{path}", rootpath +"/" + path)

    app.register_static_path( "/authorize", rootpath +"/" + "authorize.html")

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
        if request.path != self.app.appName:
            return None, set()

        # if request.url.parts[2] not in {"lovelace":"","profile":""}:
        #     return None, set()

        if request.method != hdrs.METH_GET:
            return None, {"GET"}

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
            # Cache template if not running from repository
            # self._template_cache = tpl

        return tpl

    async def get(self, request: web.Request) -> web.Response:
        """Serve the index page for panel pages."""
        # hass = request.app["hass"]

        # if not hass.components.onboarding.async_is_onboarded():
        #     return web.Response(status=302, headers={"location": "/onboarding.html"})

        # template = self._template_cache

        # if template is None:
        #     template = await hass.async_add_executor_job(self.get_template)
        template = self.get_template()

        return web.Response(
            text=template.render(
                theme_color= "#03A9F4",
                extra_modules='',#hass.data[DATA_EXTRA_MODULE_URL],
                extra_js_es5='',#hass.data[DATA_EXTRA_JS_URL_ES5],
            ),
            content_type="text/html",
        )

    def __len__(self) -> int:
        """Return length of resource."""
        return 1

    def __iter__(self):
        """Iterate over routes."""
        return iter([self._route])

