"""Cross-cutting platform primitives shared across the app layer.

This package hosts modules that the API, service and engine layers
all need to consult — for instance the RBAC permission matrix
(``permissions.py``) which defines which tenant role may perform
which action on which resource type.
"""
