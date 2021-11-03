
from __future__ import annotations
import pathlib
from aiohttp import hdrs, web, web_urldispatcher
from yarl import URL
import jinja2


async def async_setup(app,rootpath):
    #注册静态资源
    for path in ["js","css","img","static","fonts","app.js"]:
        app.register_static_path(f"/{path}", rootpath +"/" + path)

    app.register_static_path( "/index", rootpath +"/" + "index.html")
    app.register_static_path( "/demo", rootpath +"/" + "demo.html")
    app.register_static_path( "/demo2", rootpath +"/" + "jsoneditor.html")
    app.register_static_path( "/jsoneditor", rootpath +"/" + "demo.html")

    # app.register_view(IndexView(rootpath, app))
