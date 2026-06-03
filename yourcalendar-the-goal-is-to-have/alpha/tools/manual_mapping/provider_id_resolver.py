from __future__ import annotations

from collections.abc import Callable

from .thesportsdb_team_resolver import resolve_provider_id as resolve_thesportsdb_provider_id


ProviderIdResolver = Callable[[dict[str, str]], str]

PROVIDER_ID_RESOLVERS: dict[str, ProviderIdResolver] = {
    "TheSportsDB": resolve_thesportsdb_provider_id,
}


def resolve_provider_id(source: dict[str, str]) -> str:
    provider = source["API-Provider"]
    resolver = PROVIDER_ID_RESOLVERS.get(provider)
    if resolver is None:
        raise RuntimeError(f"No resolver implemented for provider {provider}")
    return resolver(source)
