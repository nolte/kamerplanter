# Authentifizierung

Kamerplanter unterstützt lokale Konten (E-Mail + bcrypt) und föderierte Konten (Google, GitHub, Apple + generische OIDC-Provider via Authlib).

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Token-Schema

- **Access Token**: JWT, 15 Minuten Gültigkeit
- **Refresh Token**: 30 Tage, HttpOnly Cookie, Rotation bei Erneuerung

## Demo-Login

```
POST /api/v1/auth/login
{
  "email": "demo@kamerplanter.local",
  "password": "demo-passwort-2024"
}
```
