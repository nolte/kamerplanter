# API-Referenz

!!! note "Automatisch generiert"
    Diese Seite wird automatisch aus Google-Style Docstrings des Backend-Codes via `mkdocstrings` generiert. Aktuell ist `mkdocstrings` noch nicht vollständig konfiguriert.

Für interaktive API-Docs mit laufendem Backend:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Print & Export (REQ-032)

Alle Print-Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{slug}/print/` und erfordern ein gültiges JWT-Token. Die Zugriffsrechte entsprechen den Berechtigungen der zugrundeliegenden Daten (REQ-024 RBAC) — wer einen Nährstoffplan lesen darf, darf ihn auch drucken.

**Gemeinsame Query-Parameter (alle Endpunkte):**

| Parameter | Typ | Standard | Werte |
|-----------|-----|---------|-------|
| `locale` | string | `de` | `de`, `en` |
| `format` | string | `pdf` | `pdf`, `csv` (nur bei tabellarischen Templates) |

### Nährstoffplan-PDF

Exportiert einen vollständigen Nährstoffplan als PDF inklusive Phasen-Tabelle, Mischanleitungen, Wasser-Konfiguration und CalMag/Flushing-Hinweisen.

```
GET /api/v1/t/{slug}/print/nutrient-plan/{plan_key}
```

**Pfad-Parameter:**

| Parameter | Beschreibung |
|-----------|-------------|
| `slug` | Mandanten-Slug |
| `plan_key` | ArangoDB-Key des NutrientPlan-Dokuments |

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="naehrstoffplan-{plan_key}.pdf"`

**Beispiel:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/nutrient-plan/nutrient_plans/42?locale=de" \
  -H "Authorization: Bearer <token>" \
  --output naehrstoffplan.pdf
```

---

### Pflege-Checkliste-PDF

Exportiert alle fälligen Pflegeaufgaben für ein bestimmtes Datum als Checkliste mit Checkboxen, gruppiert nach Dringlichkeit (überfällig, heute fällig, demnächst).

```
GET /api/v1/t/{slug}/print/care-checklist
```

**Query-Parameter (zusätzlich zu `locale` und `format`):**

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|-------------|
| `date` | string (ISO 8601) | Heutiges Datum | Stichtag für fällige Aufgaben, z.B. `2026-04-01` |

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="pflege-checkliste-{date}.pdf"`

**Beispiel:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/care-checklist?date=2026-04-15&locale=de" \
  -H "Authorization: Bearer <token>" \
  --output pflege-checkliste.pdf
```

---

### Pflanzen-Infokarten / Etiketten-PDF

Druckt kompakte Infokarten mit QR-Code für eine oder mehrere Pflanzinstanzen. Der QR-Code enthält die Deep-Link-URL zur jeweiligen Pflanze in der App.

```
GET /api/v1/t/{slug}/print/plant-labels
```

**Query-Parameter (zusätzlich zu `locale`):**

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|-----------|-----|---------|---------|-------------|
| `plant_keys` | string | Ja | — | Komma-separierte ArangoDB-Keys der Pflanzinstanzen (mind. 1) |
| `fields` | string | Nein | `name,scientific_name,planted_date` | Komma-separierte Felder auf der Karte |
| `layout` | string | Nein | `grid_2x4` | `single` (A6), `grid_2x4` (8×A4), `grid_3x3` (9×A4) |
| `qr_size_mm` | integer | Nein | `25` | QR-Code-Seitenlänge in mm (min: 20, max: 60) |

**Mögliche Werte für `fields`:**

`name`, `scientific_name`, `family`, `planted_date`, `current_phase`, `location`, `cultivar`, `note`

Der QR-Code ist immer enthalten und kann nicht über `fields` abgewählt werden.

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="pflanzen-etiketten.pdf"`

**Beispiel — 8 Karten pro A4-Seite mit Pflanzenname, wissenschaftlichem Namen und Pflanzdatum:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/plant-labels\
?plant_keys=plant_instances/101,plant_instances/102,plant_instances/103\
&fields=name,scientific_name,planted_date,location\
&layout=grid_2x4\
&qr_size_mm=25\
&locale=de" \
  -H "Authorization: Bearer <token>" \
  --output etiketten.pdf
```

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `400` | Ungültige Parameter (z.B. `layout`-Wert unbekannt, `qr_size_mm` außerhalb des Bereichs) |
| `401` | Nicht authentifiziert |
| `403` | Keine Berechtigung für diesen Mandanten oder die Ressource |
| `404` | Plan-Key oder Pflanzinstanz-Key nicht gefunden |
| `422` | Pflichtparameter fehlt (z.B. `plant_keys` bei `/plant-labels`) |

---

### Verfügbare Templates auflisten

Gibt eine Liste aller registrierten Print-Templates zurück.

```
GET /api/v1/print/templates
```

Dieser Endpunkt ist nicht mandantenspezifisch und erfordert lediglich eine gültige Authentifizierung.

**Response-Beispiel:**

```json
[
  {
    "type": "nutrient_plan",
    "label_de": "Nährstoffplan",
    "label_en": "Nutrient Plan",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "care_checklist",
    "label_de": "Pflege-Checkliste",
    "label_en": "Care Checklist",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "plant_label",
    "label_de": "Pflanzen-Infokarte",
    "label_en": "Plant Info Card",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  }
]
```

---

---

## Browser Push / PWA-Benachrichtigungen

Alle drei Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{tenant_slug}/notifications/pwa/` und erfordern ein gültiges JWT-Token.

### VAPID-Public-Key abrufen

Gibt den VAPID-Public-Key der Instanz zurück. Der Browser benötigt diesen Schlüssel, um eine Push-Subscription zu erstellen.

```
GET /api/v1/t/{tenant_slug}/notifications/pwa/vapid-public-key
```

**Response (200):**

```json
{
  "vapid_public_key": "BNm..."
}
```

Ist kein VAPID-Schlüsselpaar konfiguriert, antwortet der Endpunkt mit `503 Service Unavailable`.

---

### Push-Subscription registrieren

Registriert das aktuelle Gerät für Browser-Push-Benachrichtigungen. Die Subscription-Daten werden vom Browser nach dem Aufruf von `PushManager.subscribe()` bereitgestellt.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/subscribe
```

**Request-Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

**Response:** `201 Created` bei Erfolg, `409 Conflict` wenn die Subscription für dieses Gerät bereits registriert ist.

---

### Push-Subscription deregistrieren

Entfernt die Subscription des aktuellen Geräts. Danach werden keine Browser-Push-Benachrichtigungen mehr an dieses Gerät gesendet.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/unsubscribe
```

**Request-Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:** `204 No Content` bei Erfolg, `404 Not Found` wenn die Subscription nicht gefunden wurde.

---

### Siehe auch

- [Druckansichten & Export — Benutzerhandbuch](../user-guide/print-export.md)
- [Dünge-Logik](../user-guide/fertilization.md)
- [Pflegeerinnerungen](../user-guide/care-reminders.md)
- [Umgebungsvariablen — Browser Push (VAPID)](environment-variables.md#browser-push-pwa-vapid)
