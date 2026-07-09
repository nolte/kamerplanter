"""Central registration of side-effect-importing adapter modules.

Several adapters register themselves in their respective registries as an import
side effect of an ``@Registry.register`` class decorator (weather adapters in
:class:`WeatherAdapterRegistry`, pest/identification adapters, and the NFR-013
storage-factory registry). Those decorators only run when the defining module is
imported.

Historically the imports lived only in :mod:`app.main` (the FastAPI entry point),
so the **Celery worker** — which boots via ``celery -A app.tasks`` and never
imports ``app.main`` — started with an *empty* registry. Any task resolving an
adapter through a registry (notably the REQ-046 weather fetch) then failed with
``weather_source_unknown`` and wrote nothing. Centralising the imports here lets
both entry points share one call and stops the two import lists from drifting.

Both :mod:`app.main` and :mod:`app.tasks` call :func:`register_external_adapters`
at import time.
"""


def register_external_adapters() -> None:
    """Import every self-registering adapter module for its side effect.

    Safe to call from both entry points in the same process: after the first
    import each module is cached, so repeated calls are cheap no-ops. Note the
    registration is a *first-import* side effect — it does NOT re-populate a
    registry that was explicitly cleared (the decorators do not re-run on a cached
    import). Imports are local to keep importing this module itself
    side-effect-free and to avoid import cycles.
    """
    import app.data_access.external.demo_pest_adapter  # noqa: F401  REQ-044 demo adapter (opt-in preview)
    import app.data_access.external.dwd_weather_adapter  # noqa: F401  REQ-046 weather adapter
    import app.data_access.external.gbif_adapter  # noqa: F401  enrichment adapter
    import app.data_access.external.home_assistant_weather_adapter  # noqa: F401  REQ-046 weather adapter
    import app.data_access.external.kindwise_pest_adapter  # noqa: F401  REQ-044 cloud adapter (opt-in)
    import app.data_access.external.local_embedding_adapter  # noqa: F401  identification adapter (priority 1)
    import app.data_access.external.local_pest_adapters  # noqa: F401  REQ-044 self-hosted adapters
    import app.data_access.external.open_meteo_weather_adapter  # noqa: F401  REQ-046 weather adapter
    import app.data_access.external.openweathermap_weather_adapter  # noqa: F401  REQ-046 weather adapter
    import app.data_access.external.perenual_adapter  # noqa: F401  enrichment adapter
    import app.data_access.external.plantnet_adapter  # noqa: F401  REQ-029 adapter
    import app.data_access.storage.registry  # noqa: F401  NFR-013 storage adapter factories
