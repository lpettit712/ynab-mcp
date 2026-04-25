from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class SettingsError(RuntimeError):
    """Raised when local server configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    access_token: str


def get_settings(environ: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if environ is None else environ
    token = source.get("YNAB_ACCESS_TOKEN", "").strip()
    if not token:
        raise SettingsError(
            "Missing YNAB_ACCESS_TOKEN. Set it in your environment before starting ynab-mcp."
        )
    return Settings(access_token=token)
