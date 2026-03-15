from typing import Any


class AQLBuilder:
    """Builds parameterized AQL queries to prevent injection."""

    def __init__(self, collection: str) -> None:
        self._collection = collection
        self._filters: list[str] = []
        self._bind_vars: dict[str, Any] = {}
        self._sort: str | None = None
        self._limit: int | None = None
        self._offset: int | None = None
        self._var_counter = 0

    def filter(self, field: str, op: str, value: Any) -> AQLBuilder:
        var_name = f"v{self._var_counter}"
        self._var_counter += 1
        self._filters.append(f"doc.{field} {op} @{var_name}")
        self._bind_vars[var_name] = value
        return self

    def sort(self, field: str, direction: str = "ASC") -> AQLBuilder:
        self._sort = f"doc.{field} {direction}"
        return self

    def paginate(self, offset: int, limit: int) -> AQLBuilder:
        self._offset = offset
        self._limit = limit
        return self

    def build_list(self) -> tuple[str, dict[str, Any]]:
        parts = [f"FOR doc IN {self._collection}"]
        for f in self._filters:
            parts.append(f"  FILTER {f}")
        if self._sort:
            parts.append(f"  SORT {self._sort}")
        if self._offset is not None and self._limit is not None:
            parts.append(f"  LIMIT {self._offset}, {self._limit}")
        parts.append("  RETURN doc")
        return "\n".join(parts), self._bind_vars

    def build_count(self) -> tuple[str, dict[str, Any]]:
        parts = [f"FOR doc IN {self._collection}"]
        for f in self._filters:
            parts.append(f"  FILTER {f}")
        parts.append("  COLLECT WITH COUNT INTO total")
        parts.append("  RETURN total")
        return "\n".join(parts), self._bind_vars
