from __future__ import annotations
from fastapi.websockets import WebSocketState

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from watchfiles import awatch

from ._pkg_path import get_package_path


@asynccontextmanager
async def lifespan_dev_watcher(app: FastAPI):
    w = asyncio.create_task(_watcher())
    yield
    if not w.cancel():
        return
    with suppress(asyncio.CancelledError):
        await w


def add_dev_websocket(app: FastAPI):
    @app.websocket("/__dev/reload", name="__dev_reload_socket")
    async def dev_reload(ws: WebSocket):
        await ws.accept()
        clients.add(ws)
        try:
            # we are a socket and need to stay alive → infinite loop!
            while ws.state == WebSocketState.CONNECTED:
                with suppress(WebSocketDisconnect):
                    _ = await ws.receive_json()
        finally:
            clients.discard(ws)


async def _watcher():
    # HINT: use `debug=True` if anything breaks
    async for _changes in awatch(get_package_path()):
        await _broadcast("RELOAD")


async def _broadcast(msg: str):
    dead: list[WebSocket] = []
    for client in clients:
        try:
            await client.send_text(msg)
        except WebSocketDisconnect:
            dead.append(client)

    for d in dead:
        clients.discard(d)


clients: set[WebSocket] = set()
