"""
Home Assistant Client for python.
Simple wrapper for the websockets and rest Api's
provided by Home Assistant that allows for rapid development of apps
connected to Home Assistant.
"""
import asyncio
import functools
import logging
import os
import pprint
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
import time
import ujson
from aiohttp import (
    ClientSession,
    ClientWebSocketResponse,
    TCPConnector,
    WSMsgType,
    client_exceptions,
)
from typing import Optional


# url = "http://192.168.3.101:8123"
url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath = "lovelace-wx"

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIyMzhiNTU4ZTkzNGY0YjA3OWQ5MWM1ODU4NzJlYTYzNSIsImlhdCI6MTYzNjQ2NTIwOSwiZXhwIjoxOTUxODI1MjA5fQ.bh_Yu8h0BLw3Ur7CDlknzp7Z7tya0wLuG3TGIGpvkBA"
async def async_setup(app):
    
    def dataReceive(eventtype, data):  #收到角度变换数据
        print("from cmd:",data)

        
    # if "开灯" in ret:
    #     dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.testled"}, "id": 5}
    #     await v.hassclient.send_command(dt)
    # if "关灯" in ret or "谁" in ret:
    #     dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.testled"}, "id": 5}
    #     await v.hassclient.send_command(dt)

    
        return "OK-" + str(data)

    app.eventBus.async_listen("cmd", dataReceive)





class BaseHassClientError(Exception):
    """Base Hass Client exception."""


class TransportError(BaseHassClientError):
    """Exception raised to represent transport errors."""

    def __init__(self, message: str, error: Optional[Exception] = None) -> None:
        """Initialize a transport error."""
        super().__init__(message)
        self.error = error


class CannotConnect(TransportError):
    """Exception raised when failed to connect the client."""

    def __init__(self, error: Exception) -> None:
        """Initialize a cannot connect error."""
        super().__init__(f"{error}", error)


class ConnectionFailed(TransportError):
    """Exception raised when an established connection fails."""

    def __init__(self, error: Optional[Exception] = None) -> None:
        """Initialize a connection failed error."""
        if error is None:
            super().__init__("Connection failed.")
            return
        super().__init__(f"{error}", error)


class NotFoundError(BaseHassClientError):
    """Exception that is raised when an entity can't be found."""


class NotConnected(BaseHassClientError):
    """Exception raised when trying to handle unknown handler."""


class InvalidState(BaseHassClientError):
    """Exception raised when data gets in invalid state."""


class InvalidMessage(BaseHassClientError):
    """Exception raised when an invalid message is received."""


class AuthenticationFailed(BaseHassClientError):
    """Exception raised when authentication failed."""


class FailedCommand(BaseHassClientError):
    """When a command has failed."""

    def __init__(self, message_id: str, error_code: str):
        """Initialize a failed command error."""
        super().__init__(f"Command failed: {error_code}")
        self.message_id = message_id
        self.error_code = error_code
LOGGER = logging.getLogger(__package__)
EVENT_STATE_CHANGED = "state_changed"

IS_SUPERVISOR = os.environ.get("HASSIO_TOKEN") is not None


class HomeAssistantClient:
    """Connection to HomeAssistant (over websockets)."""

    def __init__(
        self,
        url: str = None,
        token: str = None,
        aiohttp_session: Optional[ClientSession] = None,
    ):
        """
        Initialize the connection to HomeAssistant.
            :param url: full url to the HomeAssistant instance.
            :param token: a long lived token.
        If url and token are omitted, assume supervisor install.
        """
        self._states = {}
        self._device_registry = {}
        self._entity_registry = {}
        self._area_registry = {}
        if not url and IS_SUPERVISOR:
            self.ws_server_url = "ws://hassio/homeassistant/api/websocket"
            self._token = None
        elif url and token:
            url = url.replace("http", "ws")
            if not url.endswith("/api/websocket"):
                url = url + "/api/websocket"
            self.ws_server_url = url
            self._token = token
        else:
            raise CannotConnect("Please provide a valid url and token!")
        self._event_listeners = []
        self.msgcallback = []
        self._version = None
        self._last_msg_id = 0
        self._loop = asyncio.get_running_loop()
        self._http_session = aiohttp_session or ClientSession(
            loop=self._loop, connector=TCPConnector(enable_cleanup_closed=True)
        )
        self._client: Optional[ClientWebSocketResponse] = None
        self._result_futures: Dict[str, asyncio.Future] = {}
        self._shutdown_complete_event: Optional[asyncio.Event] = None

    @property
    def connected(self) -> bool:
        """Return if we're currently connected."""
        return self._client is not None and not self._client.closed

    @property
    def version(self) -> str:
        """Return version of connected Home Assistant instance."""
        return self._version

    def register_event_callback(
        self,
        cb_func: Callable[..., Union[None, Awaitable]],
        event_filter: Union[None, str, List[str]] = None,
        entity_filter: Union[None, str, List[str]] = None,
    ) -> Callable:
        """
        Add callback for events.
        Returns function to remove the listener.
            :param cb_func: callback function or coroutine
            :param event_filter: Optionally only listen for these events
            :param entity_filter: In case of state_changed event, only forward these entities
        """
        listener = (cb_func, event_filter, entity_filter)
        self._event_listeners.append(listener)

        def remove_listener():
            self._event_listeners.remove(listener)

        return remove_listener

    def register_Msg_callback(
        self,
        cb_func
    ) -> Callable:
        """
        Add callback for events.
        Returns function to remove the listener.
            :param cb_func: callback function or coroutine
            :param event_filter: Optionally only listen for these events
            :param entity_filter: In case of state_changed event, only forward these entities
        """
        self.msgcallback.append(cb_func)

    @property
    def device_registry(self) -> dict:
        """Return device registry."""
        if not self._device_registry:
            raise NotConnected("Please call connect first.")
        return self._device_registry

    @property
    def entity_registry(self) -> dict:
        """Return device registry."""
        if not self._entity_registry:
            raise NotConnected("Please call connect first.")
        return self._entity_registry

    @property
    def area_registry(self) -> dict:
        """Return device registry."""
        if not self._area_registry:
            raise NotConnected("Please call connect first.")
        return self._area_registry

    @property
    def states(self) -> dict:
        """Return all hass states."""
        if not self._states:
            raise NotConnected("Please call connect first.")
        return self._states

    @property
    def lights(self) -> List[dict]:
        """Return all light entities."""
        return self.items_by_domain("light")

    @property
    def switches(self) -> List[dict]:
        """Return all switch entities."""
        return self.items_by_domain("switch")

    @property
    def media_players(self) -> List[dict]:
        """Return all media_player entities."""
        return self.items_by_domain("media_player")

    @property
    def sensors(self) -> List[dict]:
        """Return all sensor entities."""
        return self.items_by_domain("sensor")

    @property
    def binary_sensors(self) -> List[dict]:
        """Return all binary_sensor entities."""
        return self.items_by_domain("binary_sensor")

    def items_by_domain(self, domain: str) -> List[dict]:
        """Retrieve all items for a domain."""
        if not self.connected:
            raise NotConnected("Please call connect first.")
        return [value for key, value in self._states.items() if key.startswith(domain)]

    def get_state(self, entity_id: str, attribute: str = "state") -> dict:
        """
        Get state(obj) of a Home Assistant entity.
            :param entity_id: The entity id for which the state must be returned.
            :param attribute: The attribute to return from the state object.
        """
        if not self.connected:
            LOGGER.warning("Connection is not yet ready.")
        state_obj = self._states.get(entity_id)
        if state_obj:
            if attribute == "state":
                return state_obj["state"]
            if attribute:
                return state_obj["attributes"].get(attribute)
            return state_obj
        return None

    async def call_service(self, domain: str, service: str, service_data: dict = None):
        """
        Call service on Home Assistant.
            :param url: Domain of the service to call (e.g. light, switch).
            :param service: The service to call  (e.g. turn_on).
            :param service_data: Optional dict with parameters (e.g. { brightness: 20 }).
        """
        if not self.connected:
            raise NotConnected("Please call connect first.")
        msg = {"type": "call_service", "domain": domain, "service": service}
        if service_data:
            msg["service_data"] = service_data
        return await self.send_command(msg)

    async def set_state(
        self, entity_id: str, new_state: str, state_attributes: dict = None
    ):
        """
        Set state on a homeassistant entity.
            :param entity_id: Entity id to set state for.
            :param new_state: The new state.
            :param state_attributes: Optional dict with parameters (e.g. { name: 'Cool entity' }).
        """
        if state_attributes is None:
            state_attributes = {}
        data = {
            "state": new_state,
            "entity_id": entity_id,
            "attributes": state_attributes,
        }
        return await self._post_data(f"states/{entity_id}", data)

    async def send_command(self, message: Dict[str, Any]) -> dict:
        """Send a command to the HA websocket and return response."""
        future: "asyncio.Future[dict]" = self._loop.create_future()
        self._last_msg_id += 1
        if "id" not in message:
            message["id"] = self._last_msg_id
        message_id = message["id"]
        self._result_futures[message_id] = future
        await self._send_json_message(message)
        try:
            return await future
        finally:
            self._result_futures.pop(message_id)

    async def connect(self) -> None:
        """Connect to the websocket server."""
        LOGGER.debug("Connecting to Home Assistant...")
        try:
            self._client = await self._http_session.ws_connect(
                self.ws_server_url, heartbeat=55
            )
            version_msg = await self._client.receive_json()
            self._version = version_msg["ha_version"]
            # send authentication
            await self._client.send_json({"type": "auth", "access_token": self._token})
            auth_result = await self._client.receive_json()
            if auth_result.get("type", "") != "auth_ok":
                raise AuthenticationFailed(
                    auth_result.get("message", "Authentication failed")
                )
        except (
            client_exceptions.WSServerHandshakeError,
            client_exceptions.ClientError,
        ) as err:
            raise CannotConnect(err) from err

        LOGGER.info(
            "Connected to Home Assistant %s (version %s)",
            self.ws_server_url.split("://")[0].split("/")[0],
            self.version,
        )
        # start task to handle incoming messages
        self._loop.create_task(self._process_messages())
        # register event listener
        await self.send_command({"type": "subscribe_events"})
        # request full state once
        await self._request_full_state()

    async def disconnect(self) -> None:
        """Disconnect the client."""
        LOGGER.debug("Closing client connection")

        if not self.connected:
            return

        self._shutdown_complete_event = asyncio.Event()
        await self._client.close()
        await self._shutdown_complete_event.wait()

    async def _process_messages(self) -> None:
        """Start listening to the websocket."""
        try:
            while not self._client.closed:
                msg = await self._client.receive()

                if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
                    break

                if msg.type == WSMsgType.ERROR:
                    raise ConnectionFailed()

                if msg.type != WSMsgType.TEXT:
                    raise InvalidMessage(f"Received non-Text message: {msg.type}")

                try:
                    data = msg.json(loads=ujson.loads)
                except ValueError as err:
                    raise InvalidMessage("Received invalid JSON.") from err

                if LOGGER.isEnabledFor(logging.DEBUG):
                    LOGGER.debug("Received message:\n%s\n", pprint.pformat(msg))

                self._handle_incoming_message(data)
                try:
                    for item in self.msgcallback:
                        await item(data)
                except Exception as e:
                    print(e)

        finally:
            # TODO: handle reconnect!
            LOGGER.debug("Listen completed. Cleaning up")

            for future in self._result_futures.values():
                future.cancel()

            if not self._client.closed:
                await self._client.close()

            if self._shutdown_complete_event:
                self._shutdown_complete_event.set()
            else:
                LOGGER.debug("Connection lost, will reconnect in 10 seconds...")
                self._loop.create_task(self._auto_reconnect())

    def _handle_incoming_message(self, msg: dict) -> None:
        """Handle incoming message."""
        if msg["type"] == "result":
            future = self._result_futures.get(msg["id"])

            if future is None:
                LOGGER.warning(
                    "Received result for unknown message with ID: %s", msg["id"]
                )
                return

            if msg["success"]:
                future.set_result(msg["result"])
                return

            future.set_exception(FailedCommand(msg["id"], msg["error"]["message"]))
            
            future.set_result(msg)
            return

        if msg["type"] != "event":
            # Can't handle
            LOGGER.debug(
                "Received message with unknown type '%s': %s", msg["type"], msg
            )
            return

        event_type = msg["event"]["event_type"]
        event_data = msg["event"]["data"]
        if event_type == EVENT_STATE_CHANGED:
            entity_id = event_data["entity_id"]
            self._states[entity_id] = event_data["new_state"]
        self._signal_event(event_type, event_data)

    async def _send_json_message(self, message: Dict[str, Any]) -> None:
        """Send a message.
        Raises NotConnected if client not connected.
        """
        if not self.connected:
            raise NotConnected

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("Publishing message:\n%s\n", pprint.pformat(message))

        assert self._client
        assert "id" in message

        await self._client.send_json(message, dumps=ujson.dumps)

    async def __aenter__(self) -> "HomeAssistantClient":
        """Connect to the websocket."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the websocket."""
        await self.disconnect()

    def __repr__(self) -> str:
        """Return the representation."""
        prefix = "" if self.connected else "not "
        return f"{type(self).__name__}(ws_server_url={self.ws_server_url!r}, {prefix}connected)"

    async def _request_full_state(self):
        """Request full state."""
        vv =await self.send_command({"type": "get_states"})
        for item in await self.send_command({"type": "get_states"}):
            entity_id = item["entity_id"]
            self._states[entity_id] = item
        # Request area registry
        for item in await self.send_command({"type": "config/area_registry/list"}):
            item_id = item["area_id"]
            self._area_registry[item_id] = item
        # Request device registry
        for item in await self.send_command({"type": "config/device_registry/list"}):
            item_id = item["id"]
            self._device_registry[item_id] = item
        # Request entity registry
        for item in await self.send_command({"type": "config/entity_registry/list"}):
            item_id = item["entity_id"]
            self._entity_registry[item_id] = item

    async def _post_data(self, endpoint: str, data: dict):
        """Post data to hass rest api."""
        url = self.ws_server_url.replace("wss://", "https://").replace(
            "ws://", "http://"
        )
        url = self.ws_server_url.replace("websocket", endpoint)
        headers = {
            "Authorization": "Bearer %s" % self._get_token(),
            "Content-Type": "application/json",
        }
        async with self._http_session.post(
            url, headers=headers, json=data, verify_ssl=False
        ) as response:
            return await response.json()

    def _signal_event(self, event: str, event_details: Any = None):
        """Signal event to registered callbacks."""
        for cb_func, event_filter, entity_filter in self._event_listeners:
            if not (event_filter is None or event in event_filter):
                continue
            if event == EVENT_STATE_CHANGED:
                entity_id = event_details.get("entity_id")
                if not (
                    entity_filter is None or not entity_id or entity_id in entity_filter
                ):
                    continue
            # call callback
            check_target = cb_func
            while isinstance(check_target, functools.partial):
                check_target = check_target.func
                check_target.args = (event, event_details)
            if asyncio.iscoroutine(check_target):
                self._loop.create_task(check_target)
            elif asyncio.iscoroutinefunction(check_target):
                self._loop.create_task(check_target(event, event_details))
            else:
                self._loop.run_in_executor(None, cb_func, event, event_details)

    def _get_token(self) -> str:
        """Get auth token for Home Assistant."""
        if IS_SUPERVISOR:
            # On supervisor installs the token is provided by a environment variable
            return os.environ["HASSIO_TOKEN"]
        return self._token

    async def _auto_reconnect(self):
        """Reconnect the websocket connection when connection lost."""
        while True:
            await asyncio.sleep(10)
            try:
                await self.connect()
                return
            except CannotConnect:
                pass


def fff(vv,tt):
    print(vv,tt)

async def test():
    hassclient = HomeAssistantClient(url, token)
    hassclient.register_event_callback(fff)
    await hassclient.connect()
    print(hassclient.sensors)

    time.sleep(2)
    print("ready...1")
    
    dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
    await hassclient.send_command(dt)

    time.sleep(2)
    print("ready...2")
    dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
    await hassclient.send_command(dt)

    _stopped = asyncio.Event()
    await _stopped.wait()


if __name__ == '__main__':
    asyncio.run(test())

