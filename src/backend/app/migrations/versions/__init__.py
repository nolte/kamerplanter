"""Versioned migration modules (``vNNNN_<slug>.py``).

Each module exports a module-level ``migration`` object — an instance of
:class:`app.migrations.framework.base.Migration`.  Discovery imports them in
version order; the numbering MUST be unique, strictly monotone and gapless
starting at ``0001`` (NFR-016 M-1).
"""
