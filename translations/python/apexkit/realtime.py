import json
import asyncio
import websockets
import uuid
from typing import Optional, Dict, Any, Callable, List
import requests

class ApexKitRealtimeWSClient:
    def __init__(self, url: str, token: Optional[str] = None):
        self.url = url.replace("http", "ws").rstrip("/") + "/ws"
        self.token = token
        self.socket = None
        self.reconnect_interval = 3
        self.listeners: List[Callable[[Any], None]] = []
        self.is_connected = False
        self.current_filter = None
        self.pending_requests = {}

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.socket = websocket
                    self.is_connected = True
                    print("[ApexKit] Realtime Connected")

                    if self.current_filter:
                        await self.subscribe(self.current_filter)

                    async for message in websocket:
                        try:
                            msg = json.loads(message)
                            if 'request_id' in msg:
                                self._handle_request_response(msg)
                            else:
                                self.notify(msg)
                        except json.JSONDecodeError:
                            if message == "Pong":
                                continue
                            print(f"WS Parse Error: {message}")
            except Exception as e:
                self.is_connected = False
                print(f"[ApexKit] Disconnected: {e}. Retrying in {self.reconnect_interval}s...")
                await asyncio.sleep(self.reconnect_interval)

    async def subscribe(self, filter_data: Dict[str, Any]):
        self.current_filter = filter_data
        if self.socket and self.is_connected:
            await self.socket.send(json.dumps({
                "type": "Subscribe",
                "payload": {
                    "collection_id": filter_data.get("collectionId"),
                    "record_id": filter_data.get("recordId"),
                    "event_type": filter_data.get("eventType"),
                    "filter": filter_data.get("dataFilter"),
                    "channel": filter_data.get("channel"),
                    "custom_event": filter_data.get("customEvent")
                }
            }))

    async def send_signal(self, channel: str, event_name: str, data: Any):
        if self.socket and self.is_connected:
            await self.socket.send(json.dumps({
                "type": "Signal",
                "payload": {"channel": channel, "event": event_name, "data": data}
            }))

    async def search(self, collection_id: Any, query: str, limit: int = 10):
        if not self.is_connected or not self.socket:
            raise Exception("Socket not connected")

        request_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        self.pending_requests[request_id] = future

        await self.socket.send(json.dumps({
            "type": "Search",
            "payload": {
                "collection_id": int(collection_id),
                "query": query,
                "limit": limit,
                "request_id": request_id
            }
        }))

        try:
            return await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise Exception("Search request timed out")

    def on_event(self, callback: Callable[[Any], None]):
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

    def notify(self, msg: Any):
        for listener in self.listeners:
            listener(msg)

    def _handle_request_response(self, msg: Any):
        request_id = msg.get('request_id')
        future = self.pending_requests.pop(request_id, None)
        if future:
            if msg.get('type') == "Error":
                future.set_exception(Exception(msg.get('message')))
            else:
                future.set_result(msg.get('results'))

class ApexKitRealtimeSSEClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.listeners: List[Callable[[Any], None]] = []

    def connect(self, channel: str = None, event_name: str = None):
        import sseclient # pip install sseclient-py
        params = {}
        if channel: params['channel'] = channel
        if event_name: params['event'] = event_name

        url = f"{self.base_url}/sse"
        response = requests.get(url, params=params, stream=True)
        client = sseclient.SSEClient(response)

        for event in client.events():
            try:
                msg = json.loads(event.data)
                self.notify(msg)
            except Exception as e:
                print(f"[ApexKit] SSE Parse Error: {e}")

    def on_event(self, callback: Callable[[Any], None]):
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

    def notify(self, msg: Any):
        for listener in self.listeners:
            listener(msg)
