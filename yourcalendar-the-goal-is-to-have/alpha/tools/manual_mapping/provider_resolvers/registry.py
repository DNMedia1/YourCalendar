from __future__ import annotations

from .base import ProviderIdResolver
from .thesportsdb import resolve_thesportsdb_provider_id


PROVIDER_ID_RESOLVERS: dict[str, ProviderIdResolver] = {
    "TheSportsDB": resolve_thesportsdb_provider_id,
}


def resolve_provider_id(source: dict[str, str]) -> str:
    provider = source["API-Provider"]
    resolver = PROVIDER_ID_RESOLVERS.get(provider)
    if resolver is None:
        raise RuntimeError(f"No resolver implemented for provider {provider}")
    return resolver(source)
