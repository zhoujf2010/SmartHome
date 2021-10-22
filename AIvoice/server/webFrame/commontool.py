'''通用工具
'''

import asyncio
from aiohttp import web
import voluptuous as vol

import datetime as dt
from typing import Any, Callable
import datetime
import json

NATIVE_UTC = dt.timezone.utc

def utcnow() -> dt.datetime:
    """Get now in UTC time."""
    return dt.datetime.now(NATIVE_UTC)

async def getDataFromRequest(request: web.Request,schema: vol.Schema):
    data = await request.json()
    return schema(data)
    
    
MAJOR_VERSION = 2021
MINOR_VERSION = 4
PATCH_VERSION = "0.dev0"
__short_version__ = f"{MAJOR_VERSION}.{MINOR_VERSION}"
__version__ = f"{__short_version__}.{PATCH_VERSION}"




class JSONEncoder(json.JSONEncoder):
    """JSONEncoder that supports Home Assistant objects."""

    def default(self, o: Any) -> Any:
        """Convert Home Assistant objects.

        Hand other objects to the original method.
        """
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        if hasattr(o, "as_dict"):
            return o.as_dict()

        return json.JSONEncoder.default(self, o)
        