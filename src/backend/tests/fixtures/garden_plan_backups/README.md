# Garden-plan backup samples (GP-NFR-072, #2671)

One real backup per `schema_version` the import must still read: `schema_v<N>.json`, written by the export of
that version. The guard `tests/unit/guards/test_plan_import_keeps_two_schema_versions.py` migrates each sample of
the two versions before the current one and validates it against the import model.

While `"1"` is the only version there is nothing to keep here. When the version is raised to `"2"`, export a
plan with the old version **before** the change and save it as `schema_v1.json`.
