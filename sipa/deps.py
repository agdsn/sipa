from __future__ import annotations

import typing as t

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from .config.typed_config import Settings as SipaSettings


# TODO define init method here as well to put state writing and state fetching closer together
def templates(request: Request) -> Jinja2Templates:
    return t.cast(Jinja2Templates, request.app.state.templates)


type Templates = t.Annotated[Jinja2Templates, Depends(templates)]
