# Mandanten exportieren und importieren (Runbook)

Mit dem Mandanten-Export sicherst du **einen** Garten (Mandanten) als Archiv, ohne die ganze Datenbank anzufassen. Mit dem Import spielst du so ein Archiv als **neuen** Mandanten ein — in dieselbe oder in eine andere Kamerplanter-Installation. Damit kannst du einen einzelnen Garten wiederherstellen, ihn von einer geteilten in eine eigene Installation umziehen oder ihn vor der endgültigen Löschung noch sichern.

Diese Seite richtet sich an Betreiber und Plattform-Admins. Die Datenbank-Sicherung der ganzen Installation beschreibt [Backup & Wiederherstellung](backup-restore.md).

!!! warning "Noch nicht implementiert"
    Eine Oberfläche dafür wird es in den Garten-Einstellungen und im Admin-Bereich geben; bis dahin nutzt du die API (interne Referenz: REQ-056 §15). Sensor-Messwerte aus TimescaleDB werden noch nicht mitgenommen. <!-- REQ-056 / Issue #2138 -->

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

Beide bestätigen mit dem eigenen Passwort (oder, ohne lokales Passwort, mit einer frischen Anmeldung bzw. einem E-Mail-Code). Ein API-Schlüssel oder ein Service Account kann weder exportieren noch ein Archiv auflisten oder herunterladen. Je Garten läuft höchstens ein Export gleichzeitig, und höchstens `TENANT_EXPORTS_PER_DAY` Exporte (Standard `3`) dürfen innerhalb von 24 Stunden angefordert werden — fehlgeschlagene zählen mit. Bei jedem Export bekommen alle Mitglieder mit Verwaltung eine E-Mail, und das Sicherheitsprotokoll vermerkt `tenant_export_requested`.

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

    Das Sicherheitsprotokoll vermerkt jeden Download (`tenant_export_downloaded`).

### Signatur

Deine Installation signiert jedes Archiv, das sie schreibt (`manifest.json`, Feld `signature`). Beim Import in **dieselbe** Installation meldet der Import `verified: true`: Das Archiv ist genau das hier geschriebene. Ein Archiv aus einer anderen Installation, ein unsigniertes oder ein nach dem Export verändertes wird mit `verified: false` importiert — sein Inhalt ist dann nur so vertrauenswürdig wie die Person, die es dir gegeben hat. Der Signaturschlüssel ist aus `JWT_SECRET_KEY` abgeleitet; wechselst du ihn, gelten ältere Archive als nicht verifiziert.

!!! warning "Nicht im Archiv"
    Die Schlüssel von Integrationen (zum Beispiel der OpenWeatherMap-Schlüssel einer Wetterquelle) werden aus dem Archiv entfernt. Richte sie in der Zielinstallation neu ein.

---

## Archiv importieren (Plattform-Admin)

Ein Import legt **immer einen neuen Garten** an. Er führt nie in einen bestehenden Garten zusammen, und jeder Datensatz bekommt eine neue interne Kennung — so kann ein Archiv keinen Datensatz eines anderen Gartens überschreiben.

### Vorbereiten

- **Mitglieder zuordnen:** Das Archiv kennt die Mitglieder nur über ihre alte interne Kennung (`user_key` in `members.jsonl`). Für jedes Mitglied, das im neuen Garten wieder dabei sein soll, nennst du die E-Mail-Adresse eines **bestehenden** Kontos in der Zielinstallation (es muss **aktiv** sein — ein deaktiviertes Konto lehnt der Import ab) **und die Rolle und Zusatzberechtigungen**, die diese Person bekommt. Die Rollen im Archiv sind nur ein Hinweis; der Import übernimmt deine Angabe. Nicht zugeordnete Mitglieder entfallen; Einträge, die sie verfasst haben, tragen danach das Pseudonym `_anonymized`.
- **Eigentümer:** Der neue Garten gehört dem dienstältesten zugeordneten Mitglied, dem du Leitung und Verwaltung gibst — mit genau den Zusatzberechtigungen, die du ihm gibst (gibst du nur `management`, bekommt es nicht zusätzlich `technical`). Ordnest du keines zu, gehört er dir mit beiden Zusatzberechtigungen, bis du ihn übergibst; so hat jeder importierte Garten jemanden, der ihn verwalten kann. Im Sicherheitsprotokoll stehst in beiden Fällen du als Handelnde:r jeder angelegten Mitgliedschaft.
- **Katalog:** Die Zielinstallation braucht alle globalen Katalogeinträge, auf die das Archiv verweist (Arten, Familien, Schädlinge …). Fehlt einer, lehnt der Import mit der Liste ab, und nichts wird geschrieben.

### Ablauf

```bash
curl -X POST https://<deine-instanz>/api/v1/admin/platform/tenant-imports \
  -H "Authorization: Bearer <access-token>" \
  -F "archive=@garden.zip" \
  -F 'member_mapping={"<alter user_key>": {"email": "anna@example.com", "role": "lead", "admin_scopes": ["management"]}}' \
  -F "current_password=<dein Passwort>"
```

Optional wählst du mit `-F "plan_key=<plan>"` den Plan des neuen Gartens; sonst bekommt er den Standardplan. Deine Bestätigung ist an diese Datei gebunden: Bestätigst du statt mit dem Passwort mit einem Token einer frischen Anmeldung, forderst du es für das Ziel `archive:<die ersten 32 Hex-Zeichen des SHA-256 der Datei>` an (`sha256sum garden.zip | cut -c1-32`). Die Antwort ist `202` mit dem Schlüssel des Imports und `verified` (siehe [Signatur](#signatur)).

Solange der Import schreibt, hat der neue Garten den Zustand **Wird importiert**: Niemand kann ihn öffnen, und die Mitgliedschaften werden erst am Ende aktiv. Den Stand und am Ende den Bericht (Anzahl je Datenart, keine Inhalte) liest du so:

```bash
curl https://<deine-instanz>/api/v1/admin/platform/tenant-imports/<import-key> \
  -H "Authorization: Bearer <access-token>"
```

Den Stand liest du wie den Import selbst nur angemeldet als Person, nicht mit einem API-Schlüssel (`403`).

`completed` nennt in `target_tenant_key` den neuen Garten. Das Sicherheitsprotokoll vermerkt `tenant_import_requested` und `tenant_imported` sowie jede angelegte Mitgliedschaft. Auch ein abgelehnter oder gescheiterter Import steht dort als `tenant_import_requested` — mit dem Ergebnis (`refused:<Code>`, `failed:<Code>`, `cleanup_pending:<Code>`) und dem SHA-256 des Archivs, sodass du nachvollziehen kannst, wer welches Archiv versucht hat.

### Wenn der Import ablehnt

| Antwort | Bedeutung | Was du tust |
|---|---|---|
| `422 IMPORT_FORMAT_UNSUPPORTED` | keine ZIP-Datei, unbekanntes Format, zu viele oder zu große Dateien, ein Archiv, das entpackt zu groß würde (eine Datei mehr als 100-fach komprimiert, mehr als 250 000 Datensätze in einer Datei oder 1 000 000 insgesamt, mehr als 128 MiB Datensätze oder 1 GiB insgesamt, eine Zeile über 1 MiB oder mehr als 5 000 000 JSON-Werte insgesamt), ein Datensatz, der nicht zum archivierten Garten gehört, eine Datei eines Typs, den diese Installation nicht annimmt (zum Beispiel SVG), oder das Archiv stammt aus einer neueren Installation | ein von Kamerplanter geschriebenes Archiv verwenden; Zielinstallation aktualisieren |
| `422 IMPORT_CHECKSUM_MISMATCH` | eine Datei im Archiv passt nicht zur Prüfsumme in `manifest.json` oder fehlt — das Archiv ist beschädigt | eine unbeschädigte Kopie verwenden |
| `422 IMPORT_UNDECLARED_REFERENCE` | das Archiv enthält ein Verweisfeld, das diese Installation nicht kennt | beide Installationen auf denselben Stand bringen |
| `422 IMPORT_MISSING_CATALOG_ENTRIES` | Katalogeinträge fehlen; die Liste steht in `details` | Katalog der Zielinstallation ergänzen (Seed-Stand prüfen) |
| `422 IMPORT_MEMBER_NOT_FOUND` | eine Zuordnung nennt kein Mitglied des Archivs oder kein bestehendes, aktives Konto | Zuordnung korrigieren |
| `422 MEMBER_LIMIT_REACHED` | der Zielplan lässt weniger Mitglieder zu, als der neue Garten hätte — gezählt werden alle zugeordneten Konten und der Eigentümer (bestätigst du kein Mitglied als Leitung mit Verwaltung, bist das du) | weniger Mitglieder zuordnen oder einen Plan mit mehr Mitgliedern wählen (`plan_key`) |
| `409 STORAGE_QUOTA_EXCEEDED` | die Dateien des Archivs sind größer als das Speicherkontingent des Zielplans (gezählt wie im laufenden Garten: jede Datei einmal) | einen Plan mit mehr Speicher wählen |
| `409 PHOTO_QUOTA_EXCEEDED` | eine Pflanze im Archiv hat mehr Galeriefotos, als der Zielplan je Pflanze zulässt; `details` nennt sie | einen Plan mit mehr Fotos je Pflanze wählen |
| `413` | größer als `TENANT_IMPORT_MAX_UPLOAD_MB` — oder als die allgemeine Upload-Grenze (siehe unten) | Grenze anheben oder Garten verkleinern |

Scheitert der Import erst während des Schreibens, entfernt er alles, was er bis dahin angelegt hat — zuerst die Datensätze, die er kennt, dann über die reguläre Gartenlöschung alles, was dem neuen Garten gehört (auch einen Schreibvorgang, dessen Ausgang unklar war), samt aller Dateien unter seinem Speicherpfad — und meldet `failed`. Die Kontingente des Zielplans prüft der Import schon beim Antrag (siehe Tabelle) und im Lauf noch einmal, bevor er den Garten anlegt: Hat jemand den Plan inzwischen verkleinert, endet er mit `failed` und dem Code der Dimension (zum Beispiel `MEMBER_LIMIT_REACHED`), ohne etwas geschrieben zu haben. Gelingt das Entfernen nicht vollständig (zum Beispiel weil die Datenbank gerade nicht erreichbar ist), meldet er `cleanup_pending`: Der halbe Garten bleibt im Zustand **Wird importiert** und damit unerreichbar, `target_tenant_key` nennt ihn, und der nächste stündliche Aufbewahrungsjob löscht ihn über die reguläre Gartenlöschung; danach steht der Import auf `failed`. Bricht sein Lauf ab (zum Beispiel bei einem Neustart des Workers), löscht der stündliche Aufbewahrungsjob den halben Garten nach sechs Stunden ohne Fortschritt über die reguläre Gartenlöschung und meldet `failed` mit `IMPORT_ABANDONED`. Ein halber Garten bleibt nicht stehen; nur die Protokolleinträge der angelegten Mitgliedschaften bleiben als Nachweis.

!!! info "Die Prüfsummen sind kein Herkunftsnachweis"
    Die Prüfsummen in `manifest.json` zeigen nur ein beschädigtes Archiv an: Wer eine Datei ändert, kann sie neu berechnen. Ob ein Archiv unverändert aus deiner Installation stammt, sagt allein `verified`.

!!! warning "Wiederherstellen neben dem noch bestehenden Original"
    Spielst du ein Archiv in **dieselbe** Installation ein, während der ursprüngliche Garten noch existiert, scheitert der Import an eigenen Arten mit demselben wissenschaftlichen Namen (die Datenbank erlaubt jeden Namen nur einmal) und wird vollständig zurückgerollt. Für eine Einzel-Wiederherstellung ist der ursprüngliche Garten in der Regel ohnehin verloren; sonst lösche ihn vorher oder importiere in eine andere Installation.

---

## Einstellungen

| Variable | Standard | Wirkung |
|---|---|---|
| `TENANT_EXPORTS_PER_DAY` | `3` | Exporte je Garten in 24 Stunden |
| `TENANT_IMPORT_MAX_UPLOAD_MB` | `512` | größtes Archiv, das ein Import annimmt; entpackt darf es unabhängig davon höchstens 1 GiB groß werden |
| `RATE_LIMIT_TENANT_IMPORT` | `10/hour` | Import-Anfragen je Konto |
| `RETENTION_EXPORT_FILE_RETENTION_HOURS` | `72` | wie lange ein Archiv ladbar bleibt (gilt auch für den persönlichen Datenexport) |

!!! warning "Die allgemeine Upload-Grenze gilt auch für den Import"
    Jeder Upload an das Backend ist auf `STORAGE_MAX_FILE_SIZE_MB` plus 1 MiB begrenzt (Standard: 26 MiB) — vor jeder Route, also auch vor dem Import. Ein größeres Archiv lehnt das Backend mit `413` ab, auch wenn `TENANT_IMPORT_MAX_UPLOAD_MB` höher steht. Für größere Archive musst du `STORAGE_MAX_FILE_SIZE_MB`, `UPLOAD_SPOOL_BUDGET_MB` und die Upload-Grenze deines Ingress gemeinsam anheben — das gilt dann für jeden Upload.

!!! info "Signaturschlüssel"
    Die Signatur der Archive wird aus `JWT_SECRET_KEY` abgeleitet. Wechselst du dieses Geheimnis, gelten ältere Archive beim Import als nicht verifiziert (`verified: false`); sie lassen sich weiter importieren.

---

## Siehe auch

- [Backup & Wiederherstellung](backup-restore.md)
- [Plattform-Administration](../user-guide/admin.md)
- [Umgebungsvariablen](../reference/environment-variables.md)
