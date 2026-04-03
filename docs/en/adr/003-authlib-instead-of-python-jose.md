# ADR-003: Authlib instead of python-jose for JWT

**Status:** Accepted
**Date:** 2026-02-01
**Deciders:** Kamerplanter Development Team

## Context

A Python library was needed for JWT creation and validation as well as OAuth2/OIDC flows. python-jose was the previous standard recommendation for FastAPI.

## Decision

Authlib replaces python-jose for all JWT and OAuth2/OIDC operations.

## Rationale

python-jose has been unmaintained since 2022 and has known security vulnerabilities. Authlib is actively maintained, supports modern JWT standards (RFC 7519), and provides complete OAuth2/OIDC client implementations.

## Consequences

### Positive
- Actively maintained library with regular security updates
- Full OAuth2/OIDC support for Google, GitHub, Apple

### Negative
- Different API than python-jose — migration required changes to `TokenEngine`

## References

- [Authlib Documentation](https://docs.authlib.org/)
- REQ-023: User Management & Authentication
