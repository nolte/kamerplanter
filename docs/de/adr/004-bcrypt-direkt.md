# ADR-004: bcrypt direkt statt passlib

**Status:** Akzeptiert
**Datum:** 2026-02-01
**Entscheider:** Kamerplanter Development Team

## Kontext

Für Passwort-Hashing wurde eine Bibliothek benötigt. passlib ist die übliche Empfehlung in FastAPI-Tutorials.

## Entscheidung

bcrypt wird direkt verwendet, ohne passlib als Abstraktionsschicht.

## Begründung

passlib 1.7.4 ist inkompatibel mit bcrypt 5.x (aktuell). Da Kamerplanter ausschließlich bcrypt für Passwort-Hashing nutzt, ist die Abstraktionsschicht von passlib nicht notwendig und verursacht Versionskonflikte.

## Konsequenzen

### Positiv
- Keine Dependency-Konflikte zwischen passlib und bcrypt
- Weniger Abhängigkeiten

### Negativ
- Keine passlib-kompatible Hash-Format-Abstraktion (kein Bedarf)
