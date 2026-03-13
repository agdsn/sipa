import secrets
import typing as t

from fastapi import Response


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def response_set_csp(r: Response, nonce: str) -> Response:
    """Overwrites the `Content-Security-Policy` header of the given response"""
    SELF = "'self'"
    NONCE = f"'nonce-{nonce}'"
    required: CSPItems = {
        "default-src": (SELF,),
        "connect-src": (
            SELF,
            "https://status.agdsn.net",
            "https://*.tile.openstreetmap.de",
        ),
        "form-action": (SELF,),
        "frame-ancestors": (SELF,),
        "img-src": (
            SELF,
            "data:",
            "https://*.tile.openstreetmap.de",
        ),
        "script-src": (
            SELF,
            NONCE,
            "https://status.agdsn.net",
        ),
        "style-src": (SELF, NONCE),
        "style-src-attr": (SELF, "'unsafe-inline'"),
        "worker-src": ("'none'",),
    }
    r.headers["Content-Security-Policy"] = "; ".join(f"{directive} {' '.join(values)}"
        for directive, values in required.items()
    )
    return r


CSPItems = t.TypedDict(  # noqa: UP013
    "CSPItems",
    {
        "default_src": t.NotRequired[tuple[str, ...]],
        "connect_src": t.NotRequired[tuple[str, ...]],
        "form_action": t.NotRequired[tuple[str, ...]],
        "frame_ancestors": t.NotRequired[tuple[str, ...]],
        "img_src": t.NotRequired[tuple[str, ...]],
        "script_src": t.NotRequired[tuple[str, ...]],
        "style_src": t.NotRequired[tuple[str, ...]],
        "style_src_attr": t.NotRequired[tuple[str, ...]],
        "worker_src": t.NotRequired[tuple[str, ...]],
    },
)

