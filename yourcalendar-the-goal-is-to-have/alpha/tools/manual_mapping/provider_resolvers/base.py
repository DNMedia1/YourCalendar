from __future__ import annotations

from collections.abc import Callable


ProviderIdResolver = Callable[[dict[str, str]], str]
