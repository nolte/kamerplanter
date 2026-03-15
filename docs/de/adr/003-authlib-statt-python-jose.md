# ADR-003: Authlib statt python-jose für JWT

**Status:** Akzeptiert
**Datum:** 2026-02-01
**Entscheider:** Kamerplanter Development Team

## Kontext

Für JWT-Erstellung und -Validierung sowie OAuth2/OIDC-Flows wurde eine Python-Bibliothek benötigt. python-jose war die bisherige Standardempfehlung für FastAPI.

## Entscheidung

Authlib ersetzt python-jose für alle JWT- und OAuth2/OIDC-Operationen.

## Begründung

python-jose ist seit 2022 nicht mehr aktiv gepflegt und hat bekannte Sicherheitslücken. Authlib ist aktiv maintained, unterstützt moderne JWT-Standards (RFC 7519) und bietet vollständige OAuth2/OIDC-Client-Implementierungen.

## Konsequenzen

### Positiv
- Aktiv gepflegte Bibliothek mit regelmäßigen Security-Updates
- Vollständige OAuth2/OIDC-Unterstützung für Google, GitHub, Apple

### Negativ
- Andere API als python-jose — Migration erforderte Anpassungen in `TokenEngine`

## Referenzen

- [Authlib Dokumentation](https://docs.authlib.org/)
- REQ-023: Benutzerverwaltung & Authentifizierung
