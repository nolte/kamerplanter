# Service Accounts & API-Keys

!!! info "Nur über API / Betreiber-Konfiguration"
    Service Accounts und die Einschränkungen eines API-Keys richtest du über die REST-API ein; eine Oberfläche dafür gibt es noch nicht. <!-- REQ-023 §5b, Issue #2137 -->

Ein **Service Account** ist ein Konto für eine Maschine statt für einen Menschen — Home Assistant,
Grafana, eine CI/CD-Pipeline. Er gehört zu genau einem Garten (Mandanten), meldet sich nie mit
Passwort an und arbeitet ausschließlich mit API-Keys. So muss keine Integration mit deinem
persönlichen Key laufen, und du kannst ihr den Zugang jederzeit entziehen, ohne deinen eigenen
anzufassen.

---

## Was einen Service Account ausmacht

- **Kein Passwort, keine Anmeldung, keine Sitzung.** Ein Login mit seiner Adresse wird abgewiesen.
- **Genau ein Garten.** Er wird als Mitglied mit der Rolle **Beobachter** (`viewer`) oder **Gärtner** (`grower`) angelegt — nie als Leitung, ohne Verwaltungsrechte. Auch über die Mitgliederverwaltung wird er nicht zur Leitung (`403`).
- **Seine API-Keys gelten nur in diesem Garten.** Jeder Key ist an den Garten gebunden: Ein Aufruf in einem anderen Garten antwortet `403`, ebenso jede kontobezogene Route.
- **Er gründet keinen Garten und nimmt keine Einladung an** (`403`).
- **Er belegt einen Platz** im Mitgliederlimit des Gartens.
- Seine Adresse ist zufällig und unzustellbar (`sa-…@service.example.com`); er bekommt keine E-Mails.

---

## Voraussetzungen

- Du bist im Garten **Leitung** (`lead`) **und** hast den technischen Verwaltungsbereich (`technical`). Beides wird aus deiner gespeicherten Mitgliedschaft gelesen.
- Du bestätigst jede Änderung mit deinem eigenen Passwort (Step-up). Ohne lokales Passwort holst du dir einen Code oder meldest dich frisch an — Aktion `service_account_change`, Ziel: der Schlüssel des Gartens beim Anlegen, `<garten-schlüssel>|<service-account-schlüssel>` beim Rotieren und Entfernen.
- Eine Anfrage, die selbst mit einem API-Key authentifiziert ist, darf nichts davon (`403`).
- Im Light-Modus gibt es keine Service Accounts (`403`).

---

## Service Account anlegen

```bash
curl -X POST "https://kamerplanter.example.com/api/v1/t/mein-garten/service-accounts" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Home Assistant",
    "role": "grower",
    "ip_allowlist": ["192.168.1.0/24"],
    "rate_limit_per_minute": 600,
    "expires_at": "2027-04-01T00:00:00+02:00",
    "current_password": "<dein aktuelles Passwort>"
  }'
```

**Antwort (`201 Created`):**

```json
{
  "key": "8f3c…",
  "display_name": "Home Assistant",
  "role": "grower",
  "membership_key": "51a0…",
  "api_key": {
    "key": "a7d2…",
    "label": "Home Assistant",
    "raw_key": "kp_…",
    "key_prefix": "kp_Xy1aB",
    "tenant_scope": "<schlüssel von mein-garten>",
    "created_at": "2026-10-05T10:00:00Z",
    "ip_allowlist": ["192.168.1.0/24"],
    "rate_limit_per_minute": 600,
    "expires_at": "2027-03-31T22:00:00Z"
  }
}
```

!!! warning "Den Key siehst du nur einmal"
    `raw_key` steht nur in dieser Antwort (und in der Antwort einer Rotation). Gespeichert wird
    nur sein Hash. Trag ihn sofort in die Integration oder einen Secret-Manager ein.

**Ablehnungen, bevor nach deinem Passwort gefragt wird:**

| Antwort | Wann |
|---|---|
| `403` | Du bist nicht Leitung mit `technical`, die Anfrage kommt von einem API-Key, oder Light-Modus |
| `422` | Rolle nicht `viewer`/`grower`, oder eine der Key-Einschränkungen ist unbrauchbar (siehe unten) |
| `422 SERVICE_ACCOUNT_LIMIT_REACHED` | Der Garten hat schon so viele aktive Service Accounts, wie `TENANT_MAX_SERVICE_ACCOUNTS` erlaubt (Standard 20) |
| `422 MEMBER_LIMIT_REACHED` | Das Mitgliederlimit des Gartens ist erreicht |

Danach: `401` ohne oder mit falschem Passwort, `429 STEP_UP_LOCKED` nach zu vielen Fehlversuchen.

---

## Die Einschränkungen eines API-Keys

Dieselben drei Felder nimmt auch `POST /api/v1/auth/api-keys` an, mit dem du einen Key für dein
eigenes Konto ausstellst. Sie gelten auf der REST-API und auf dem MCP-Server gleich.

| Feld | Erlaubt | Wirkung |
|---|---|---|
| `ip_allowlist` | Höchstens 32 Bereiche in CIDR-Schreibweise; eine einzelne Adresse wird als `/32` bzw. `/128` gespeichert. Keine gesetzten Host-Bits (`10.0.0.5/8` wird abgelehnt), nicht weiter als `/8` (IPv4) bzw. `/32` (IPv6). Leer oder weggelassen: keine Einschränkung | Ein Aufruf von einer anderen Adresse antwortet `401` |
| `rate_limit_per_minute` | 1–10000 | Darüber `429`; REST und MCP zählen gemeinsam |
| `expires_at` | Mit Zeitzone, in der Zukunft, höchstens 730 Tage voraus | Danach antwortet jeder Aufruf `401` |

`GET /api/v1/auth/api-keys` zeigt die drei Werte für deine eigenen Keys an.

---

## Service Accounts auflisten

```bash
curl "https://kamerplanter.example.com/api/v1/t/mein-garten/service-accounts" \
  -H "Authorization: Bearer {access_token}"
```

Die Liste nennt jeden aktiven Service Account mit Rolle und seinen Keys in diesem Garten — nur
Metadaten (Präfix, Einschränkungen, letzter Zugriff, widerrufen ja/nein), nie den Key selbst.

---

## Key rotieren

```bash
curl -X POST "https://kamerplanter.example.com/api/v1/t/mein-garten/service-accounts/{sa_key}/rotate-key" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"overlap_minutes": 30, "current_password": "<dein aktuelles Passwort>"}'
```

- Der neue Key übernimmt **IP-Allowlist und Ratenlimit** des jüngsten bisherigen Keys. Ein neues Ablaufdatum gibst du optional mit `expires_at` an.
- `overlap_minutes` (0–1440, Standard **0**): Bei `0` sind die bisherigen Keys **sofort** widerrufen — der richtige Wert, wenn ein Key in falsche Hände geraten ist. Bei einem Wert über 0 funktionieren sie noch so viele Minuten weiter, damit du die Integration ohne Unterbrechung umstellen kannst; danach lehnt jeder Aufruf sie ab.
- Die Antwort enthält den neuen Key (`api_key.raw_key`, nur dieses eine Mal), `previous_keys_end_at` (das Ende des Übergangsfensters oder `null`) und `replaced_key_count`.

!!! tip "Umstellen ohne Ausfall"
    1. Rotieren mit `overlap_minutes` (z. B. 30).
    2. Den neuen Key in Home Assistant oder der Pipeline eintragen.
    3. Testen. Spätestens nach dem Fenster gilt nur noch der neue Key.

---

## Service Account entfernen

```bash
curl -X DELETE "https://kamerplanter.example.com/api/v1/t/mein-garten/service-accounts/{sa_key}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "<dein aktuelles Passwort>"}'
```

Alle Keys des Service Accounts in diesem Garten werden sofort widerrufen, seine Mitgliedschaft
endet (ihm zugewiesene Aufgaben verlieren die Zuweisung), und das Konto wird deaktiviert. Was er
geschrieben hat, behält ihn als Urheber.

Anlegen, Rotieren und Entfernen stehen im Sicherheitsprotokoll, das Plattform-Admins lesen können.

---

## Den Key verwenden

```bash
curl "https://kamerplanter.example.com/api/v1/t/mein-garten/sites" \
  -H "Authorization: Bearer kp_…"
```

Der Key handelt mit der Rolle des Service Accounts im Garten — ein `viewer` liest nur, ein
`grower` darf auch schreiben, aber nichts löschen.

---

## Was noch fehlt

!!! warning "Noch nicht implementiert"
    Folgendes wird es erst später geben: Service Accounts bearbeiten, vorübergehend sperren und
    wieder freigeben; Service Accounts auf Plattformebene für mehrere Gärten; eine Oberfläche in
    den Garten-Einstellungen. <!-- REQ-023 §5b.0 -->

---

## Häufige Fragen

??? question "Kann ein Service Account mehrere Keys haben?"
    Während eines Übergangsfensters nach einer Rotation ja — danach gilt nur der neue. Bei einer
    Rotation mit `overlap_minutes: 0` gibt es nie zwei gültige Keys.

??? question "Was tue ich bei einem kompromittierten Key?"
    Rotiere mit `overlap_minutes: 0` — der alte Key ist im selben Moment ungültig. Brauchst du die
    Integration nicht mehr, entferne den Service Account.

??? question "Worin unterscheidet er sich von meinem eigenen API-Key?"
    Dein eigener Key handelt als du, in allen deinen Gärten (oder dem einen, auf den du ihn
    beschränkst), mit deiner Rolle. Ein Service Account ist ein eigenes Mitglied mit höchstens
    Gärtner-Rechten in genau einem Garten — entfernst du ihn, bleibt dein Zugang unberührt.

## Siehe auch

- [Authentifizierung](authentication.md)
- [Fehlerbehandlung](error-handling.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
- [MCP-Server](mcp-server.md)
