"""Declarative seed registry (NFR-016 §3.2 / S-4).

Seeds load idempotent *reference data* and run on every startup — as opposed to
versioned, one-time migrations.  :func:`app.migrations.seeds.registry.run_seeds`
replaces the scattered inline seed calls that used to live in ``main.py``.
"""
