# Mandanten exportieren und importieren (Runbook)

Mit dem Mandanten-Export sicherst du **einen** Garten (Mandanten) als Archiv, ohne die ganze Datenbank anzufassen. Mit dem Import spielst du so ein Archiv als **neuen** Mandanten ein — in dieselbe oder in eine andere Kamerplanter-Installation. Damit kannst du einen einzelnen Garten wiederherstellen, ihn von einer geteilten in eine eigene Installation umziehen oder ihn vor der endgültigen Löschung noch sichern.

Diese Seite richtet sich an Betreiber und Plattform-Admins. Die Datenbank-Sicherung der ganzen Installation beschreibt [Backup & Wiederherstellung](backup-restore.md).

!!! warning "Noch nicht implementiert"
    Eine Oberfläche dafür wird es in den Garten-Einstellungen und im Admin-Bereich geben; bis dahin nutzt du die API (interne Referenz: REQ-056 §15). Sensor-Messwerte aus TimescaleDB werden noch nicht mitgenommen, und die Kontingente des Zielplans werden vor dem Import noch nicht geprüft. <!-- REQ-056 / Issue #2138 -->

---

## Was im Archiv steckt — und was nicht

Das Archiv ist eine ZIP-Datei im Format `kamerplanter-tenant-export/1`. Es enthält alles, was beim Löschen des Mandanten entfernt würde — abzüglich einer festen Liste von Ausnahmen, die mit Begründung im Archiv selbst steht (`manifest.json`, Feld `excluded`).

| Teil | Inhalt |
|---|---|
| `manifest.json` | Format, Migrationsstand der Quelle, Erstellzeit, eine zufällige Kennung der Quelle, je Datei Anzahl und SHA-256-Prüfsumme, die Liste der Ausnahmen |
| `tenant.json` | Name, Kurzname, Beschreibung und Einstellungen des Gartens |
| `collections/<name>.jsonl` | jeder Datensatz des Gartens: Standorte, Pflanzen, Durchläufe, Tagebuch, Aufgaben, Tanks, Sensoren, Ernte- und Behandlungsdokumentation, eigene Arten, Sorten, Dünger, Substrate und alles Weitere |
| `edges/<name>.jsonl` | die Verbindungen zwischen diesen Datensätzen und zu globalen Katalogeinträgen (Arten, Familien, Schädlinge …) |
| `members.jsonl` | je Mitglied: interne Kontokennung, Anzeigename, Rolle, Zusatzberechtigungen, Beitrittsdatum — **keine** E-Mail-Adresse |
| `objects/…` | die Originale der Fotos und Anhänge; Vorschaubilder entstehen nach dem Import beim ersten Aufruf neu |

**Nicht** im Archiv: Konten und Anmeldedaten, Sitzungen, API-Schlüssel, Einladungen, verschlüsselte Zugangsdaten von Integrationen (KI-Anbieter, InvenTree), die Freigaben der Home-Assistant-Entitäten, das Sicherheitsprotokoll und die anderen Audit-Protokolle, Benachrichtigungen, iCal-Abonnements, KI-Gespräche und Caches, Parzellen-Zuordnungen, Export-Anträge und Erkennungsvektoren.

!!! info "Das Archiv enthält personenbezogene Daten"
    Standortkoordinaten, Tagebuchtexte und Fotos der Mitglieder gehören dazu. Bewahre das Archiv entsprechend auf und lösche es, sobald du es nicht mehr brauchst. In Kamerplanter selbst ist es 72 Stunden ladbar (`RETENTION_EXPORT_FILE_RETENTION_HOURS`), danach löscht die Installation es.

---

## Garten exportieren

### Wer darf exportieren

- Ein Mitglied mit der Rolle **Leitung** und der Zusatzberechtigung **Verwaltung**, solange der Garten aktiv oder zur Löschung vorgemerkt ist.
- Ein **Plattform-Admin** in jedem Zustand außer gelöscht — auch für einen gesperrten oder verwaisten Garten.

Beide bestätigen mit dem eigenen Passwort (oder, ohne lokales Passwort, mit einer frischen Anmeldung bzw. einem E-Mail-Code). Ein API-Schlüssel oder ein Service Account kann nicht exportieren. Je Garten läuft höchstens ein Export gleichzeitig, und höchstens `TENANT_EXPORTS_PER_DAY` Exporte (Standard `3`) dürfen innerhalb von 24 Stunden angefordert werden — fehlgeschlagene zählen mit. Bei jedem Export bekommen alle Mitglieder mit Verwaltung eine E-Mail, und das Sicherheitsprotokoll vermerkt `tenant_export_requested`.

### Ablauf

1. Export anfordern:

    ```bash
    curl -X POST https://<deine-instanz>/api/v1/tenants/<slug>/exports \
      -H "Authorization: Bearer <access-token>" \
      -H "Content-Type: application/json" \
      -d '{"current_password": "<dein Passwort>"}'
    ```

    Als Plattform-Admin: `POST /api/v1/admin/platform/tenants/<tenant-key>/exports`. Die Antwort ist `202` mit dem Schlüssel des Exports (`key`) und `status: pending`.

2. Warten, bis `status` auf `completed` steht:

    ```bash
    curl https://<deine-instanz>/api/v1/tenants/<slug>/exports \
      -H "Authorization: Bearer <access-token>"
    ```

    Der Export läuft im Hintergrund auf der Warteschlange `bulk`. Bei großen Gärten dauert das einige Minuten. `failed` mit `failure_reason: too_large` heißt: Das Archiv wäre größer als das Speicherkontingent des Gartens plus 10 %.

3. Archiv herunterladen (nur die Person, die den Export angefordert hat):

    ```bash
    curl -o garden.zip https://<deine-instanz>/api/v1/tenants/<slug>/exports/<export-key>/download \
      -H "Authorization: Bearer <access-token>"
    ```

---

## Archiv importieren (Plattform-Admin)

Ein Import legt **immer einen neuen Garten** an. Er führt nie in einen bestehenden Garten zusammen, und jeder Datensatz bekommt eine neue interne Kennung — so kann ein Archiv keinen Datensatz eines anderen Gartens überschreiben.

### Vorbereiten

- **Mitglieder zuordnen:** Das Archiv kennt die Mitglieder nur über ihre alte interne Kennung (`user_key` in `members.jsonl`). Für jedes Mitglied, das im neuen Garten wieder dabei sein soll, nennst du die E-Mail-Adresse eines **bestehenden** Kontos in der Zielinstallation. Nicht zugeordnete Mitglieder entfallen; Einträge, die sie verfasst haben, tragen danach das Pseudonym `_anonymized`.
- **Eigentümer:** Der neue Garten gehört dem dienstältesten zugeordneten Mitglied mit Leitung und Verwaltung. Ordnest du keines zu, gehört er dir, bis du ihn übergibst.
- **Katalog:** Die Zielinstallation braucht alle globalen Katalogeinträge, auf die das Archiv verweist (Arten, Familien, Schädlinge …). Fehlt einer, lehnt der Import mit der Liste ab, und nichts wird geschrieben.

### Ablauf

```bash
curl -X POST https://<deine-instanz>/api/v1/admin/platform/tenant-imports \
  -H "Authorization: Bearer <access-token>" \
  -F "archive=@garden.zip" \
  -F 'member_mapping={"<alter user_key>": "anna@example.com"}' \
  -F "current_password=<dein Passwort>"
```

Optional wählst du mit `-F "plan_key=<plan>"` den Plan des neuen Gartens; sonst bekommt er den Standardplan. Die Antwort ist `202` mit dem Schlüssel des Imports. Den Stand und am Ende den Bericht (Anzahl je Datenart, keine Inhalte) liest du so:

```bash
curl https://<deine-instanz>/api/v1/admin/platform/tenant-imports/<import-key> \
  -H "Authorization: Bearer <access-token>"
```

`completed` nennt in `target_tenant_key` den neuen Garten. Das Sicherheitsprotokoll vermerkt `tenant_import_requested` und `tenant_imported` sowie jede angelegte Mitgliedschaft.

### Wenn der Import ablehnt

| Antwort | Bedeutung | Was du tust |
|---|---|---|
| `422 IMPORT_FORMAT_UNSUPPORTED` | keine ZIP-Datei, unbekanntes Format, oder das Archiv stammt aus einer neueren Installation | Zielinstallation aktualisieren und erneut versuchen |
| `422 IMPORT_CHECKSUM_MISMATCH` | eine Datei im Archiv wurde verändert oder fehlt | ein unverändertes Archiv verwenden |
| `422 IMPORT_UNDECLARED_REFERENCE` | das Archiv enthält ein Verweisfeld, das diese Installation nicht kennt | beide Installationen auf denselben Stand bringen |
| `422 IMPORT_MISSING_CATALOG_ENTRIES` | Katalogeinträge fehlen; die Liste steht in `details` | Katalog der Zielinstallation ergänzen (Seed-Stand prüfen) |
| `422 IMPORT_MEMBER_NOT_FOUND` | eine Zuordnung nennt kein Mitglied des Archivs oder kein bestehendes Konto | Zuordnung korrigieren |
| `413` | größer als `TENANT_IMPORT_MAX_UPLOAD_MB` | Grenze anheben oder Garten verkleinern |

Scheitert der Import erst während des Schreibens, entfernt er alles, was er bis dahin angelegt hat, und meldet `failed`. Ein halber Garten bleibt nicht stehen; nur die Protokolleinträge der angelegten Mitgliedschaften bleiben als Nachweis.

!!! warning "Wiederherstellen neben dem noch bestehenden Original"
    Spielst du ein Archiv in **dieselbe** Installation ein, während der ursprüngliche Garten noch existiert, scheitert der Import an eigenen Arten mit demselben wissenschaftlichen Namen (die Datenbank erlaubt jeden Namen nur einmal) und wird vollständig zurückgerollt. Für eine Einzel-Wiederherstellung ist der ursprüngliche Garten in der Regel ohnehin verloren; sonst lösche ihn vorher oder importiere in eine andere Installation.

---

## Einstellungen

| Variable | Standard | Wirkung |
|---|---|---|
| `TENANT_EXPORTS_PER_DAY` | `3` | Exporte je Garten in 24 Stunden |
| `TENANT_IMPORT_MAX_UPLOAD_MB` | `512` | größtes Archiv, das ein Import annimmt (entpackt höchstens das Vierfache) |
| `RATE_LIMIT_TENANT_IMPORT` | `10/hour` | Import-Anfragen je Konto |
| `RETENTION_EXPORT_FILE_RETENTION_HOURS` | `72` | wie lange ein Archiv ladbar bleibt (gilt auch für den persönlichen Datenexport) |

---

## Siehe auch

- [Backup & Wiederherstellung](backup-restore.md)
- [Plattform-Administration](../user-guide/admin.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
