# Error Handling

All API errors follow a consistent JSON format. Every error response contains a unique error ID, a machine-readable error code, a human-readable message, and a `details` array for field-specific validation errors.

---

## Error Structure

```json
{
  "error_id": "err_f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "error_code": "ENTITY_NOT_FOUND",
  "message": "PlantInstance with key 'pi_xyz' not found.",
  "details": [
    {
      "field": "key",
      "reason": "No PlantInstance with key 'pi_xyz'.",
      "code": "ENTITY_NOT_FOUND"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/plant-instances/pi_xyz",
  "method": "GET"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error_id` | String | Unique UUID of the error event — use for support requests |
| `error_code` | String | Machine-readable code (full list below) |
| `message` | String | Short error description in English |
| `details` | Array | Field-specific error details (may be empty) |
| `details[].field` | String | Field name or path to the invalid value |
| `details[].reason` | String | Explanation of the specific problem |
| `details[].code` | String | Machine-readable detail code |
| `timestamp` | String | Time of the error (ISO 8601, UTC) |
| `path` | String | URL path of the failed request |
| `method` | String | HTTP method of the failed request |

!!! tip "Use error_id for support"
    The `error_id` is logged on the server. Always include this ID when debugging or raising support requests — it allows the error to be traced precisely on the server side.

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200 OK` | Success | Read requests (GET) |
| `201 Created` | Resource created | POST with new resource |
| `204 No Content` | Success without body | DELETE |
| `400 Bad Request` | Malformed request | Syntax error in request body |
| `401 Unauthorized` | Not authenticated | Missing or invalid token |
| `403 Forbidden` | No permission | Authenticated but missing role |
| `404 Not Found` | Resource not found | Unknown ID or slug |
| `409 Conflict` | Conflict | Duplicate entry or invalid state transition |
| `422 Unprocessable Entity` | Validation error | Business rules violated (e.g. pre-harvest interval) |
| `423 Locked` | Account locked | Too many failed login attempts |
| `429 Too Many Requests` | Rate limit exceeded | Too many requests per minute |
| `502 Bad Gateway` | External source unreachable | GBIF/Perenual timeout |
| `500 Internal Server Error` | Internal error | Unexpected server error |

---

## Error Codes

### General Errors

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `ENTITY_NOT_FOUND` | 404 | The requested resource does not exist |
| `DUPLICATE_ENTRY` | 409 | An entry with this value already exists |
| `VALIDATION_ERROR` | 422 | Pydantic validation error (types, required fields) |
| `INTERNAL_ERROR` | 500 | Unexpected internal error |

### Authentication and Authorization Errors

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `UNAUTHORIZED` | 401 | No valid token present |
| `INVALID_TOKEN` | 401 | Token expired or tampered |
| `FORBIDDEN` | 403 | Authenticated but without sufficient role |
| `EMAIL_NOT_VERIFIED` | 403 | Email address not yet confirmed |
| `ACCOUNT_LOCKED` | 423 | Account locked after too many failed attempts |

### Phase and State Errors

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `PHASE_TRANSITION_INVALID` | 422 | Invalid phase status transition (e.g. backward transition) |
| `INVALID_STATUS_TRANSITION` | 422 | Invalid status change of an object |
| `INVALID_RUN_STATE` | 409 | Operation not allowed in the current state |

### Plant Protection and Harvest Errors

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `KARENZ_VIOLATION` | 422 | Harvest not possible — pre-harvest interval (PHI) not yet elapsed |
| `RESISTANCE_WARNING` | 422 | Resistance risk — active ingredient applied too many times consecutively |
| `HST_VIOLATION` | 422 | Training measure (HST) not permitted in this growth phase |

### Substrate and Compatibility Errors

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `SUBSTRATE_EXHAUSTED` | 422 | Substrate batch has exceeded maximum reuse cycles |
| `ROTATION_VIOLATION` | 422 | Plant family was grown in this slot too recently |
| `INCOMPATIBLE_COMPANION` | 422 | Two plant species are incompatible as companion plants |

### External Services

| Error Code | HTTP | Description |
|-----------|------|-------------|
| `EXTERNAL_SOURCE_ERROR` | 502 | External data service (GBIF, Perenual) not reachable |
| `ADAPTER_NOT_FOUND` | 404 | No adapter registered for the specified source |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit of the server or an external service exceeded |

---

## Validation Errors (422)

FastAPI and Pydantic automatically produce structured validation errors for input mistakes. The `details` list contains one entry per invalid field:

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "not-a-valid-email",
  "password": "short",
  "display_name": ""
}
```

**Response (422):**

```json
{
  "error_id": "err_b5e3c8a1-...",
  "error_code": "VALIDATION_ERROR",
  "message": "The input data is invalid.",
  "details": [
    {
      "field": "body.email",
      "reason": "value is not a valid email address",
      "code": "value_error"
    },
    {
      "field": "body.password",
      "reason": "String should have at least 10 characters",
      "code": "string_too_short"
    },
    {
      "field": "body.display_name",
      "reason": "String should have at least 1 character",
      "code": "string_too_short"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/auth/register",
  "method": "POST"
}
```

---

## Pre-Harvest Interval Violation (KARENZ_VIOLATION)

The pre-harvest interval (PHI) gate prevents creating a harvest record while the waiting period of an applied pesticide has not yet elapsed.

```http
POST /api/v1/t/my-garden/harvest/batches
```

**Response (422) when PHI is active:**

```json
{
  "error_id": "err_c7d2e5f3-...",
  "error_code": "KARENZ_VIOLATION",
  "message": "Cannot harvest: safety interval for 'Pyrethrin' has 5 days remaining.",
  "details": [
    {
      "field": "active_ingredient",
      "reason": "Safety interval not elapsed: 5 days remaining.",
      "code": "KARENZ_VIOLATION"
    }
  ],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/my-garden/harvest/batches",
  "method": "POST"
}
```

!!! danger "Pre-harvest intervals are legally relevant"
    The pre-harvest interval (Karenzzeit) between the last pesticide application and harvest is legally mandated (PflSchG/CanG). Clients must never suppress or ignore this error.

---

## Conflicts (409)

HTTP 409 is used when an operation cannot be performed due to the current state — for example, adding a plant to an already completed run:

```json
{
  "error_id": "err_a1b2c3d4-...",
  "error_code": "INVALID_RUN_STATE",
  "message": "Operation 'add_plant' not allowed in status 'completed'.",
  "details": [],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/my-garden/planting-runs/run_123/plants",
  "method": "POST"
}
```

---

## Rate Limiting (429)

When the rate limit is exceeded, the API responds with HTTP 429. The `Retry-After` header indicates how many seconds to wait before retrying:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

```json
{
  "error": "Rate limit exceeded: 20 per 1 minute"
}
```

---

## Internal Errors (500)

For unexpected internal errors, the API never exposes server-side details. The `error_id` is the only instrument for error correlation:

```json
{
  "error_id": "err_9f8e7d6c-...",
  "error_code": "INTERNAL_ERROR",
  "message": "An internal error occurred. Please contact support with the reference ID.",
  "details": [],
  "timestamp": "2026-03-17T10:30:00.000000+00:00",
  "path": "/api/v1/t/my-garden/plant-instances/",
  "method": "GET"
}
```

---

## Recommendations for API Clients

- **Evaluate the error code, not just the HTTP status code.** Multiple semantically distinct errors can share the same status code (e.g. `KARENZ_VIOLATION`, `HST_VIOLATION`, and `ROTATION_VIOLATION` are all HTTP 422).
- **Log the `error_id`.** Always include the `error_id` in your own logs and in support requests.
- **Iterate the `details` array** for field-specific error messages in form validation.
- **Respond to `401` with a token refresh.** When the access token expires (15 min), the API returns `401 UNAUTHORIZED`. The client should automatically attempt a refresh.
- **Do not retry `409 INVALID_RUN_STATE`.** This error indicates a business-level state conflict — the operation is only possible after a state change.

---

## See Also

- [API Overview](overview.md) — URL structure and endpoint groups
- [Authentication](authentication.md) — Auth errors in detail
- [IPM / Pest Management](../user-guide/pest-management.md) — Pre-harvest interval concept explained
