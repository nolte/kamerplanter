"""Reusable machinery shared by migration version modules — no ``Migration`` subclasses.

A version module's class source is hashed by ``Migration.checksum()`` (M-7), so an
applied migration's class can never be edited to grow a seam for a later one. Logic
that more than one migration needs therefore lives here instead — see
:mod:`app.migrations.support.care_profile_recompute`.
"""
