# ADR-004: bcrypt directly instead of passlib

**Status:** Accepted
**Date:** 2026-02-01
**Deciders:** Kamerplanter Development Team

## Decision

bcrypt is used directly, without passlib as an abstraction layer.

## Rationale

passlib 1.7.4 is incompatible with bcrypt 5.x (current). Since Kamerplanter uses exclusively bcrypt for password hashing, the abstraction layer provided by passlib is unnecessary and causes version conflicts.

## Consequences

### Positive
- No dependency conflicts between passlib and bcrypt
- Fewer dependencies

### Negative
- No passlib-compatible hash format abstraction (not needed)
