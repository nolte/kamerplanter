<!-- Quelle: REQ-011 (Externe Stammdatenanreicherung); Code: src/backend/app/api/v1/enrichment/, src/backend/app/domain/engines/enrichment_engine.py, src/backend/app/data_access/external/{gbif_adapter,perenual_adapter}.py, src/frontend/src/components/common/OriginChip.tsx, src/frontend/src/hooks/useOriginProtection.ts -->

# Externe Datenanreicherung

Kamerplanter kann die botanischen Stammdaten einer Pflanzenart automatisch aus öffentlichen Datenbanken ergänzen — zum Beispiel Trivialnamen, natürlicher Lebensraum oder taxonomische Angaben. So musst du diese Informationen nicht für jede Art einzeln recherchieren und eintragen.

Die Anreicherung läuft im Hintergrund und ergänzt gezielt nur **fehlende** Angaben. Bereits von dir gepflegte Daten haben immer Vorrang und werden nie automatisch überschrieben.

---

## Was wird ergänzt?

Betroffen sind ausschließlich die botanischen **Artdaten** (nicht deine persönlichen Pflanzen, Standorte oder Erntedaten). Folgende Felder kann die externe Anreicherung befüllen, sofern sie bei einer Art noch leer sind:

| Feld | Beispiel |
|------|---------|
| Trivialnamen | „Tomate", „Love Apple" |
| Gattung | *Solanum* |
| Botanische Familie | Solanaceae (Nachtschattengewächse) |
| Wuchsform | krautig, strauchig, kletternd |
| Natürlicher Lebensraum | Herkunftsregion und Standortbedingungen |
| Winterhärtezonen | z. B. 7a–9b |
| Synonyme | ältere oder abweichende wissenschaftliche Namen |
| Taxonomische Autorenzitierung und -status | z. B. „L." für Linné, Status „ACCEPTED"/„SYNONYM" |
| Kurzbeschreibung | botanische Kurzcharakteristik |

!!! note "Nicht zu verwechseln mit den Referenzbildern"
    Diese Seite behandelt die **textuellen** Stammdaten. Die Fotos, die dir in der Artenansicht als Vergleichsbild angezeigt werden, stammen aus einer separaten Bildbeschaffung und sind unter [Referenzbilder in der Artenansicht](../user-guide/plant-management.md#referenzbilder-in-der-artenansicht) beschrieben. Beide Funktionen nutzen teilweise dieselbe Quelle (GBIF, Global Biodiversity Information Facility), laufen aber unabhängig voneinander.

## Woher stammen die Daten?

| Quelle | Liefert | Voraussetzung |
|--------|---------|---------------|
| **GBIF** (Global Biodiversity Information Facility) | Taxonomie, Synonyme, Trivialnamen, Lebensraum, Kurzbeschreibung | Keine — öffentliche API, kein Schlüssel nötig |
| **Perenual** | Ergänzende Pflegeangaben (u. a. Wuchsform, Winterhärtezonen) | Kostenloser API-Schlüssel des Betreibers erforderlich |

Ist für eine Quelle kein Schlüssel hinterlegt (z. B. Perenual auf einer frisch installierten Instanz), liefert sie einfach keine Daten — der Rest des Systems funktioniert unverändert weiter.

## Automatischer Abgleich

Ein Abgleich mit den externen Quellen läuft **automatisch im Hintergrund**, du musst dafür nichts tun:

- **Täglich** wird geprüft, welche Arten noch keine Anreicherung aus einer Quelle haben, und für diese ein Abgleich durchgeführt.
- **Wöchentlich** wird zusätzlich ein vollständiger Abgleich aller Arten ausgeführt, damit auch Aktualisierungen an bereits abgeglichenen Arten übernommen werden. Unveränderte Daten werden dabei übersprungen.

## Wie mit vorhandenen Angaben umgegangen wird

Für jedes Feld gilt die Regel **„lokale Angaben haben Vorrang"**:

- War das Feld bei einer Art **leer**, übernimmt das System den externen Wert automatisch.
- War bereits ein Wert **eingetragen**, wird der externe Wert nur als Vorschlag hinterlegt und **nicht** automatisch übernommen — dein bestehender Wert bleibt unverändert.

!!! tip "Herkunfts-Kennzeichnung in der Oberfläche"
    Automatisch übernommene Felder markiert Kamerplanter in den Stammdaten-Ansichten mit der Herkunfts-Kennzeichnung **„Angereichert"** (Symbol mit funkelndem Stern). Diese Kennzeichnung ist schreibgeschützt, damit die extern bezogenen Fachdaten nicht versehentlich überschrieben werden — im Unterschied zu selbst importierten oder manuell gepflegten Daten kannst du sie nicht direkt bearbeiten.

## Datenschutz

Die externe Datenanreicherung verarbeitet ausschließlich botanische Fachdaten (wissenschaftliche Artnamen) — keine personenbezogenen Daten von dir. Trotzdem ist die Funktion als **optionale, widerrufbare Einwilligung** hinterlegt, da dabei Anfragen an Drittanbieter-APIs (GBIF, Perenual) gesendet werden. Details und wie du die Einwilligung verwaltest: [Datenschutz (DSGVO, Datenschutz-Grundverordnung)](../user-guide/privacy.md#einwilligungen-verwalten-art-7-dsgvo).

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

!!! note "Zielgruppe: Betreiber und Entwickler"
    Die folgenden Abschnitte richten sich an Personen, die eine eigene Kamerplanter-Instanz betreiben oder administrieren. Für den täglichen Gebrauch im Garten ist keiner dieser Schritte nötig — die Anreicherung läuft automatisch im Hintergrund.

### Perenual-Schlüssel einrichten

GBIF funktioniert ohne Konfiguration. Für Perenual benötigst du einen kostenlosen API-Schlüssel, den du als Umgebungsvariable hinterlegst. Details und Beispielwerte: [Umgebungsvariablen-Referenz](../reference/environment-variables.md#externe-datenanreicherung-req-011).

### Status der Quellen prüfen

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources | python3 -m json.tool
```

Ob eine Quelle aktuell erreichbar ist, zeigt der Health-Check:

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/health | python3 -m json.tool
```

### Abgleich manuell auslösen

Statt auf den nächsten geplanten Lauf zu warten, kannst du einen Abgleich sofort anstoßen — etwa nach dem Anlegen mehrerer neuer Arten:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources/gbif/sync
```

Für einen vollständigen Abgleich aller Arten (nicht nur der noch nicht angereicherten) den Parameter `full_sync` setzen:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"full_sync": true}' \
  http://localhost:8000/api/v1/enrichment/sources/perenual/sync
```

Der Aufruf startet den Abgleich asynchron und liefert sofort den Status des gestarteten Laufs zurück. Den Verlauf früherer Läufe (inkl. Fehlern) zeigt:

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources/gbif/history | python3 -m json.tool
```

### Vorgeschlagene Werte prüfen, übernehmen oder verwerfen

Für eine bestimmte Art zeigt folgender Aufruf alle Anreicherungen inklusive automatisch übernommener und noch offener Vorschläge:

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments | python3 -m json.tool
```

Einen offenen Vorschlag gezielt übernehmen (überschreibt den bisherigen lokalen Wert) oder verwerfen:

```bash
# Vorschlag übernehmen
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"fields": ["hardiness_zones"]}' \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments/perenual/accept

# Vorschlag verwerfen
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"fields": ["hardiness_zones"]}' \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments/perenual/reject
```

### Externe Quellen durchsuchen, ohne zu importieren

Um vor einem Import zu prüfen, welche Daten eine Quelle für einen Suchbegriff liefert:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"source_key": "gbif", "query": "Solanum lycopersicum"}' \
  http://localhost:8000/api/v1/enrichment/search | python3 -m json.tool
```

Dieser Aufruf verändert keine Stammdaten — er dient nur der Vorschau.

!!! warning "Alle Endpunkte erfordern eine Anmeldung"
    Sämtliche Enrichment-Endpunkte setzen einen gültigen JWT-Zugriffstoken voraus. Es handelt sich um globale Ressourcen (keine Mandanten-URL, `/api/v1/enrichment/...`), da botanische Artdaten mandantenübergreifend gemeinsam genutzt werden.

---

## Häufige Fragen

??? question "Warum sehe ich bei manchen Arten keine Anreicherung?"
    Mögliche Gründe: Die Art wurde noch nicht abgeglichen (der tägliche Lauf verarbeitet unangereicherte Arten schrittweise), der wissenschaftliche Name konnte in der externen Quelle keiner eindeutigen Art zugeordnet werden, oder für Perenual ist auf dieser Instanz kein API-Schlüssel hinterlegt.

??? question "Kann ich einen bereits übernommenen Wert wieder rückgängig machen?"
    Der automatisch übernommene Wert kann wie jedes andere Feld dieses Ursprungs betrachtet, aber nicht direkt bearbeitet werden. Um einen falschen Wert zu korrigieren, wende dich an den Betreiber deiner Instanz — technische Details dazu findest du im Abschnitt [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster).

??? question "Beeinflusst die Anreicherung auch meine eigenen Pflanzen oder Ernten?"
    Nein. Die Anreicherung wirkt ausschließlich auf die botanischen Artdaten (die gemeinsame Wissensbasis), nicht auf deine individuellen Pflanzen, Standorte, Aufgaben oder Erntedaten.

??? question "Was passiert, wenn eine externe Quelle nicht erreichbar ist?"
    Ein einzelner fehlgeschlagener Quellabgleich beeinträchtigt die anderen Quellen nicht und ändert nichts an deinen bestehenden Stammdaten. Der nächste planmäßige Lauf versucht es erneut.

## Siehe auch

- [Stammdaten verwalten](../user-guide/plant-management.md) — Arten, Sorten und botanische Familien pflegen
- [Pflanze per Foto identifizieren](../user-guide/plant-identification.md) — verwandte, aber unabhängige Funktion zur Artbestimmung per Foto
- [Datenschutz (DSGVO)](../user-guide/privacy.md) — Einwilligungen verwalten
- [Umgebungsvariablen-Referenz](../reference/environment-variables.md#externe-datenanreicherung-req-011) — Konfiguration für Betreiber
