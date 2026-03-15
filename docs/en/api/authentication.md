# Authentication

Kamerplanter supports local accounts (email + bcrypt) and federated accounts (Google, GitHub, Apple + generic OIDC providers via Authlib).

!!! note "Placeholder"
    This content will be elaborated in a subsequent step.

## Token Schema

- **Access Token**: JWT, 15-minute validity
- **Refresh Token**: 30 days, HttpOnly cookie, rotation on renewal
