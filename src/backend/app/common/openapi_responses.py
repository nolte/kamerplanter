"""Reusable OpenAPI ``responses=`` maps for the global error envelope.

Documentation-only module (spec/project/api-documentation/): routers compose
these maps into ``APIRouter(responses=...)`` so every actually-returned error
status code is documented per operation. The envelope shape itself is owned by
the global handlers in :mod:`app.common.error_handlers` — ``ErrorResponse``
mirrors it for schema generation and must be kept in sync with them.
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Global error envelope emitted by the exception handlers."""

    error_id: str = Field(description="Unique reference id for support and log correlation.")
    error_code: str = Field(description="Machine-readable error code, e.g. NOT_FOUND or VALIDATION_ERROR.")
    message: str = Field(description="Human-readable error message.")
    details: list[dict[str, Any]] = Field(default_factory=list, description="Optional structured error details.")
    timestamp: str = Field(description="ISO-8601 timestamp of the error.")
    path: str = Field(description="Request path that produced the error.")
    method: str = Field(description="HTTP method of the failing request.")


def request_body_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The JSON schema of *model* with every ``$defs`` entry inlined, for a hand-written ``openapi_extra`` body.

    ``model_json_schema()`` points nested models at ``#/$defs/<Name>`` — a root-relative reference that resolves
    nowhere once the schema sits inside ``paths`` of the published document (Spectral ``invalid-ref``). A recursive
    model has no inline form and is refused.
    """
    schema: dict[str, Any] = model.model_json_schema()
    defs: dict[str, Any] = schema.pop("$defs", {})

    def resolve(node: object, seen: tuple[str, ...]) -> object:
        if isinstance(node, list):
            items: list[object] = node
            return [resolve(item, seen) for item in items]
        if isinstance(node, dict):
            mapping: dict[str, object] = node
            return resolve_mapping(mapping, seen)
        return node

    def resolve_mapping(mapping: dict[str, object], seen: tuple[str, ...]) -> dict[str, object]:
        ref = mapping.get("$ref")
        if isinstance(ref, str):
            pointer: str = ref
            if pointer.startswith("#/$defs/"):
                name: str = pointer.removeprefix("#/$defs/")
                if name in seen:
                    raise ValueError(f"{model.__name__}: recursive model {name} cannot be inlined")
                target: dict[str, object] = defs[name]
                siblings = {key: resolve(value, seen) for key, value in mapping.items() if key != "$ref"}
                return {**resolve_mapping(target, (*seen, name)), **siblings}
        return {key: resolve(value, seen) for key, value in mapping.items()}

    return resolve_mapping(schema, ())


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


UNAUTHORIZED_RESPONSE: dict[int | str, dict[str, Any]] = {
    401: _error("Missing, invalid, or expired credentials."),
}

FORBIDDEN_RESPONSE: dict[int | str, dict[str, Any]] = {
    403: _error("Authenticated, but not allowed to access this resource."),
}

NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: _error("The requested resource does not exist."),
}

CONFLICT_RESPONSE: dict[int | str, dict[str, Any]] = {
    409: _error("A conflicting resource already exists (duplicate key or unique constraint)."),
}

VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    422: _error("The input data is invalid (field-level details in `details`)."),
}

#: A route behind the step-up verifier (#1816, #1815, #1841). Documented once so the
#: step-up routes cannot describe the same refusals differently.
STEP_UP_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: _error(
        "The step-up failed: the current password or the mailed one-time code is missing or wrong. "
        "`STEP_UP_CODE_REQUIRED` when an account without a local password sent no `step_up_code` — "
        "request one with `POST /api/v1/users/me/step-up-code`."
    ),
    403: _error("Not a signed-in session of a person: a request authenticated with an API key, or a service account."),
    429: _error(
        "`STEP_UP_LOCKED`: too many failed confirmations; `details[0].retry_after_minutes` states the wait. "
        "Signing in is not affected."
    ),
}

#: The 422s of the two step-up factor routes (#1815 review) — documented per route so
#: a generated client sees which ``error_code`` means which path.
STEP_UP_CODE_VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    422: _error(
        "`STEP_UP_PASSWORD_REQUIRED`: the account has a local password and confirms with it. "
        "`STEP_UP_REAUTH_REQUIRED`: a linked provider can re-authenticate — use `POST /users/me/step-up/oidc`. "
        "`VALIDATION_ERROR`: the act is missing or unknown."
    ),
}
STEP_UP_REAUTH_VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    422: _error(
        "`STEP_UP_PASSWORD_REQUIRED`: the account has a local password and confirms with it. "
        "`STEP_UP_REAUTH_UNAVAILABLE`: no linked provider (or not `provider_key`) can re-authenticate freshly — "
        "confirm with the e-mailed code (`POST /users/me/step-up-code`). "
        "`VALIDATION_ERROR`: the act is missing or unknown."
    ),
}

#: Only ``POST /users/me/step-up-code`` sends mail synchronously (/code-review of #1862).
STEP_UP_CODE_UNDELIVERABLE_RESPONSE: dict[int | str, dict[str, Any]] = {
    503: _error(
        "`STEP_UP_CODE_UNDELIVERABLE`: the code could not be mailed (no mail delivery configured, or the mail "
        "server failed). Nothing was issued; ask the operator."
    ),
}

# Composed profiles for the common router shapes.
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    **UNAUTHORIZED_RESPONSE,
    **FORBIDDEN_RESPONSE,
}

CRUD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **NOT_FOUND_RESPONSE,
    **CONFLICT_RESPONSE,
}

AUTH_CRUD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **AUTH_RESPONSES,
    **CRUD_RESPONSES,
}
