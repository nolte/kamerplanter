"""REQ-033 MCP server scaffold.

Exposes Kamerplanter resources (plants, tasks, harvests, calendar
feeds) as Model Context Protocol tools so external LLM clients can
query the system without writing custom REST glue. Concrete tool
registration lands with the REQ-033 follow-up PR.
"""
