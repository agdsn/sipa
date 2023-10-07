import secrets
import typing as t
from dataclasses import dataclass, field

from werkzeug.datastructures import ContentSecurityPolicy


def generate_nonce() -> str:
    return secrets.token_hex(32)


def ensure_items(current_items: str | None, items: t.Iterable[str]) -> str:
    _cur = set(current_items.split()) if current_items else set()
    return " ".join(_cur | set(items))


@dataclass(frozen=True)
class NonceInfo:
    """struct to remember which nonces have been generated for inline scripts"""

    style_nonces: list[str] = field(default_factory=list)

    script_nonces: list[str] = field(default_factory=list)

    def add_style_nonce(self) -> str:
        self.style_nonces.append(n := generate_nonce())
        return n

    def add_script_nonce(self) -> str:
        self.script_nonces.append(n := generate_nonce())
        return n

    def apply_to_csp(self, csp: ContentSecurityPolicy) -> ContentSecurityPolicy:
        """Add nonces to the CSP object"""
        csp.script_src = ensure_items(
            csp.script_src, (f"'nonce-{n}'" for n in self.script_nonces)
        )
        csp.style_src = ensure_items(
            csp.style_src, (f"'nonce-{n}'" for n in self.style_nonces)
        )
        return csp
