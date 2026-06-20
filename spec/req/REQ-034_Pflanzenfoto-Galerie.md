# Spezifikation: REQ-034 - Pflanzenfoto-Galerie

```yaml
ID: REQ-034
Titel: Pflanzenfoto-Galerie (eigene Fotos pro Pflanzeninstanz)
Kategorie: Dokumentation / Visualisierung / KI-Datenbeitrag
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19/TypeScript 5.9, MUI 7
Status: Entwurf
Prioritaet: Hoch
Version: 1.1 (Security-Review SR-001..SR-007 eingearbeitet)
Autor: Business Analyst - Agrotech
Datum: 2026-06-19
Tags: [photos, gallery, plant-instance, attachments, storage, dinov2, user-contributed, dsgvo]
Quelle: .audits/plant-photos-handover.md (Featurewunsch eigene Pflanzenfotos), spec/analysis/casual-houseplant-user-review.md (N-001)
Abhaengigkeiten: [NFR-013 v1.2 (Storage-Fundament, category `plant`), REQ-013 (Pflanzdurchlauf/PlantInstance), REQ-029-A v1.2 (DINOv2-Referenzbeschaffung), REQ-025 v1.4 (DSGVO/Erasure), REQ-024 v1.5 (Mandant/Permissions), REQ-027 (Light-Modus), REQ-023 (Auth)]
Betroffene Module: [backend.app.services.attachment, backend.app.domain.models.plant_instance, backend.app.api.plant_instances, frontend.pages.pflanzen, frontend.components.identification]
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.1 | 2026-06-19 | **Security-Requirements-Review eingearbeitet.** SR-001: Consent-Purpose `reference_contribution` in REQ-025 v1.4 registriert (§4.4). SR-002: Permission-Vertrag auf den realen `Permission`-Enum (REQ-024 v1.5 §1a) umgestellt; neue Matrix-Zeile „Plant Instance Photos" (§6). SR-003: Provenienz-Felder + pgvector-Erasure-Phase 0.5 (REQ-029-A v1.2 §5.1, REQ-025 §3.5) (§5). SR-004: Galerie-Quota verbindlich (§3, O-01 aufgelöst). SR-005: Light-Modus-Auflösung des Reference-Hooks + Backlog-Limit gegen Index-Poisoning (§4). SR-006: interner Bildtransfer als ClusterIP/TLS-only gekennzeichnet (§4.2). SR-007: `POST /reference`-Vertrag in REQ-029-A v1.2 §3.3 definiert. O-04 auf „global pro Nutzer" entschieden. |
| 1.0 | 2026-06-19 | Erstentwurf — Foto-Galerie pro Pflanzeninstanz auf NFR-013-Fundament, DINOv2-Hook, DSGVO-Klassifizierung. |

---

## 0. Verhaeltnis zu bestehenden Spezifikationen

REQ-034 ist eine **Anwendungs-Spezifikation auf dem Storage-Fundament NFR-013**. Es erfindet **kein** neues Speicher-, Upload- oder DSGVO-Konzept, sondern nutzt das in NFR-013 (Status: Genehmigt) verbindlich definierte Adapter-Pattern, die `attachments`-Collection, die Upload-Pipeline (§5.1) und die Erasure-Reihenfolge (§6, W-007). REQ-034 fuegt diesem Fundament zwei Dinge hinzu:

1. eine **fachliche Anbindung** der Anhaenge an die **Pflanzeninstanz** (REQ-013) inklusive einer eigenen Galerie-UI, und
2. einen **optionalen Daten-Rueckfluss** der vom Nutzer beigesteuerten Fotos in den DINOv2-Referenz-Index (REQ-029-A), klar abgegrenzt und einwilligungs-/kuratierungs-gesteuert.

| Dokument | Was es liefert | Was REQ-034 daraus nutzt |
|----------|----------------|--------------------------|
| **NFR-013** | Storage-Adapter, `attachments`-Collection, Upload-Pipeline, Thumbnails, DSGVO-Erasure, Stable URI | Gesamtes Speicher-, Validierungs- und Loeschfundament. REQ-034 ergaenzt nur die neue `category = plant`. |
| **REQ-013** | `PlantInstance`, `plant_instances`-Collection, Detailseite, tenant-scoped Router | Anker fuer die Fotozuordnung (`photo_refs`), Galerie-Tab in der Detailseite. |
| **REQ-029-A** | DINOv2-Inferenz, `species_embeddings`-Index, Kuratierung (`is_active`), `InferenceServiceClient.reference()` | Ziel des optionalen Foto-Rueckflusses (`source = user_contributed`). |
| **REQ-025** | Erasure-Engine, Scopes `user_personal` / `user_diary_attachments`, EXIF-Strip | Klassifizierung der Pflanzenfotos in der Nutzer-Loeschung. |
| **REQ-029** | Bilderkennung verwirft Nutzerfotos bewusst (nur Hash + Ergebnis) | **Abgrenzung:** REQ-034 ist das Gegenteil — dauerhafte Speicherung. Eigener Datenfluss. |

> **Wichtige Abgrenzung zur Bilderkennung (REQ-029/-029-A):** Die Bilderkennung **speichert das Nutzerfoto bewusst nicht** dauerhaft (REQ-029 §5.2 — nur Bild-Hash + Ergebnis bleiben). Die Pflanzenfoto-Galerie ist der **bewusst gegenlaeufige** Anwendungsfall: Der Nutzer will seine Fotos **dauerhaft** behalten. Beide Datenfluesse bleiben getrennt; ein Galerie-Upload ist niemals implizit eine Identifikationsanfrage und umgekehrt.

---

## 1. Business Case

### 1.1 User Stories

**Als** Hobbygaertner / Zimmerpflanzen-Besitzer
**moechte ich** eigene Fotos zu jeder meiner Pflanzen aufnehmen und speichern
**um** den Wachstumsverlauf optisch festzuhalten und meine Pflanzen in der Uebersicht wiederzuerkennen.

**Als** Nutzer ohne botanisches Wissen (N-001, Casual User)
**moechte ich** ein Foto meiner Pflanze genauso einfach aufnehmen wie bei der Bilderkennung — per Webcam, Smartphone-Kamera oder Datei-Upload —
**ohne** mich um Speicherorte, Bucket-Namen oder Dateiformate kuemmern zu muessen.

**Als** Betreiber / Self-Hosted-Admin
**moechte ich** vorgeben koennen, **wo** diese Fotos liegen (lokales Volume oder S3),
**um** Speicherkosten, Backup und Datenhoheit selbst zu steuern.

**Als** datenschutzbewusster Nutzer
**moechte ich** dass meine Fotos die Instanz nicht ungewollt verlassen und beim Loeschen meines Kontos deterministisch behandelt werden
**um** die Kontrolle ueber meine Bilddaten zu behalten.

**Als** Community (Datenbeitrag, optional)
**moechte ich** meine Fotos einer korrekt bestimmten Pflanze optional als zusaetzliche Referenz fuer die Bilderkennung beisteuern koennen
**um** die self-hosted Erkennung fuer alle zu verbessern — aber nur freiwillig und nach Pruefung.

### 1.2 Geschaeftliche Motivation

Die Bilderkennung (REQ-029/-029-A) beantwortet die Frage „**Welche** Pflanze ist das?". REQ-034 beantwortet die Frage „**Wie** sieht **meine** Pflanze aus und wie entwickelt sie sich?". Das ist fuer den Casual-Houseplant-User (N-001) ein zentraler Wiedererkennungs- und Motivationsfaktor: Eine Pflanze mit eigenem Foto in der Liste ist persoenlich; eine Instanz-ID ohne Bild ist anonym.

Gleichzeitig entsteht aus den vom Nutzer beigesteuerten, **bereits korrekt einer Art zugeordneten** Fotos ein potenziell wertvoller Datenschatz fuer die self-hosted Erkennung (REQ-029-A): few-shot-Referenzen aus realen Indoor-/Praxisbedingungen, die in den Lizenz-freien Bilddatenbanken (GBIF/iNaturalist) oft fehlen (REQ-029-A §4.3 — gerade Indoor-Stadien sind unterrepraesentiert).

### 1.3 Scope-Abgrenzung

| In Scope (v1.0) | Out of Scope (v1.0) |
|-----------------|---------------------|
| Fotos pro **Pflanzeninstanz** (`plant_instances`) | Fotos an Species/Cultivar-Stammdaten (separate Stammdaten-Galerie) |
| Upload via Webcam / Smartphone / Datei-Upload (Wiederverwendung REQ-029-Capture) | Bulk-Import ganzer Foto-Archive |
| Galerie-Ansicht mit Thumbnails, Lightbox, Cover-Foto | Bildbearbeitung (Zuschnitt, Filter) im Client |
| Loeschen einzelner Fotos, Cover setzen | Video-Anhaenge |
| Optionaler DINOv2-Referenz-Hook (`user_contributed`, kuratiert) | Automatische Aktivierung user-beigesteuerter Referenzen ohne Pruefung |
| DSGVO-Klassifizierung der Galerie-Fotos | Foto-Sharing zwischen Tenants |

---

## 2. Fachliche Anforderungen

### 2.1 Foto-Zuordnung an die Pflanzeninstanz

Jedes Galerie-Foto ist ein **Attachment** im Sinne von NFR-013 mit `category = plant` und wird einer Pflanzeninstanz zugeordnet.

- **Datenmodell:** `PlantInstance` (REQ-013, `src/backend/app/domain/models/plant_instance.py`) erhaelt das Feld:

  ```python
  photo_refs: list[str] = Field(default_factory=list)
  # Geordnete Liste von attachment_id (NFR-013 §2.2). NICHT roh S3-URLs.
  cover_photo_ref: str | None = None
  # attachment_id des als Titelbild markierten Fotos; None => erstes Element aus photo_refs.
  ```

  Die Reihenfolge in `photo_refs` ist die Anzeige-Reihenfolge (neueste zuerst — Sortierung erfolgt im Service ueber `attachments.created_at`, `photo_refs` haelt die Zuordnung). `cover_photo_ref` MUSS Element von `photo_refs` sein, sonst `422`.

- **Konsistenz:** Ein `attachment_id` darf in `photo_refs` nur vorkommen, wenn das zugehoerige `attachments`-Dokument `category == "plant"` und denselben `tenant_key` wie die Pflanzeninstanz hat. Der Service erzwingt das beim Verknuepfen (Schutz vor Cross-Category-/Cross-Tenant-Referenzen).

- **Foto-Metadaten (v1.2):** Jedes Galerie-Foto traegt zwei optionale, vom Nutzer pflegbare Metadaten am `attachments`-Dokument:
  - `caption: str | None` — ein frei editierbarer Kommentar/Bildunterschrift (max. 500 Zeichen), Default `None`.
  - `taken_on: date | None` — das Aufnahmedatum. Default/Fallback ist das Upload-`created_at` (EXIF-Aufnahmezeit ist nicht verfuegbar, da EXIF beim Upload gestript wird, §3/NFR-013 §6.4). Der Nutzer kann ein abweichendes Datum setzen (z.B. fuer nachtraeglich hochgeladene aeltere Fotos). `taken_on` darf nicht in der Zukunft liegen.
  Beide werden ueber `PATCH /api/v1/t/{slug}/plant-instances/{key}/photos/{attachment_id}` gesetzt (`require_permission(UPDATE_RESOURCE)`, gleiche Konsistenz-/Zuweisungs-Guards wie Cover/Delete). In der Galerie werden Aufnahmedatum (`taken_on ?? created_at`) und Kommentar unter dem Thumbnail sowie in der Lightbox angezeigt und dort editiert. `caption`/`taken_on` sind generische Attachment-Felder (auch fuer andere Foto-Kategorien nutzbar), bleiben dort aber `None`.

- **Loeschung der Pflanzeninstanz:** Beim Entfernen einer `PlantInstance` werden die referenzierten Attachments ueber den Attachment-Service mitgeloescht (`delete_object` je `attachment_id` + Metadaten). Verwaiste Storage-Bytes sind unzulaessig.

### 2.2 Upload-Erlebnis (Wiederverwendung der Bilderkennungs-UX)

Der Foto-Upload nutzt **dieselben drei Erfassungswege** wie die Bilderkennung (REQ-029 §4.1, Komponente `ImageCapturePanel.tsx`):

1. **Live-Webcam** (`navigator.mediaDevices.getUserMedia()`) — Desktop/Kiosk
2. **Smartphone-Rueckkamera** (`<input type="file" accept="image/*" capture="environment">`)
3. **Datei-Upload / Drag&Drop**

Unterschied zur Erkennung: Galerie-Fotos sollen in **hoeherer Aufloesung** erhalten bleiben als die fuer die Erkennung normalisierten Bilder. Die Client-Normalisierung (`imageNormalization.ts`) wird **parametrisierbar** (z.B. `maxEdge` Galerie 2048 px statt 1280 px, JPEG-Qualitaet 0.9). EXIF wird clientseitig gestript (Konsistenz zu REQ-029 §5.4); die serverseitige EXIF-Behandlung gilt zusaetzlich (§5).

### 2.3 Anzeige in der Instanz-Uebersicht

- **Detailseite** (`PlantInstanceDetailPage.tsx`): neuer **Tab „Fotos"/„Galerie"** mit Thumbnail-Grid (512-px-Variante), Lightbox (1280 px), Upload-Button (oeffnet den wiederverwendeten Capture-Flow), Loeschen und „Als Titelbild setzen".
- **Info-Tab / Listenansicht:** Vorschau des Cover-Fotos (bzw. ersten Fotos) als visuelle Wiedererkennung. Pflanzen ohne Foto zeigen einen neutralen Platzhalter.
- **Performance:** Listen laden ausschliesslich Thumbnails (NFR-013 §8.1, Download P95 Thumbnail < 200 ms), nie das Originalbild.

### 2.4 Storage-Konfiguration durch den Admin

Wo die Fotos liegen, ist **keine** Nutzer-, sondern eine **Betreiber-Entscheidung** und wird zentral ueber das Storage-Backend (NFR-013 §4.1) konfiguriert — `local-fs` (Default, Light-Modus) oder `s3`. REQ-034 fuehrt **keine** eigene Storage-Konfiguration ein; die Admin-Settings-UI fuer das Storage-Backend ist Teil der NFR-013-Umsetzung (Handover Phase B.14) und gilt fuer **alle** Kategorien gleichermassen. Das Frontend der Galerie kennt — konform NFR-013 §2.4/AC-04 — **kein** Backend, keinen Bucket, keine Region, nur `attachment_id` und die Stable URI.

---

## 3. NFR-013-Erweiterung: category `plant`

REQ-034 fuehrt eine **neue Storage-Kategorie** ein. Das ist die einzige Aenderung am Storage-Fundament und wird in NFR-013 v1.2 nachgezogen (siehe dort Changelog + §4.3/§5.2).

| Eigenschaft | Wert |
|-------------|------|
| **Kategorie-Schluessel** | `plant` |
| **Storage-Key-Schema** | `t/{tenant_key}/plant/{yyyy}/{mm}/{ulid}.{ext}` (NFR-013 §4.3, unveraendert) |
| **Erlaubte MIME-Types** | `image/jpeg`, `image/png`, `image/webp`, `image/heic` (serverseitige Konvertierung empfohlen) — identisch zur Foto-Whitelist `diary`/`ipm`/`harvest` (NFR-013 §5.2) |
| **Max-Groesse (Default)** | 25 MB (NFR-013-Default; ueber `STORAGE_ALLOWED_MIME_TYPES_PLANT` / `STORAGE_MAX_FILE_SIZE_MB` ueberschreibbar) |
| **Quota (SR-004)** | `STORAGE_MAX_PHOTOS_PER_INSTANCE` (Default **50** Fotos/Pflanzeninstanz). Zusaetzlich greift die Tenant-Storage-Quota gemaess NFR-013 §5.1 Schritt 3 / NFR-012 §10 (Skalierungsstufe). Ueberschreitung ⇒ Upload abgelehnt (HTTP 409, vor dem Schreiben). |
| **Thumbnails** | 128 / 512 / 1280 px (NFR-013 §8.2, unveraendert) |
| **DSGVO-Scope** | `user_diary_attachments` (siehe §5) |
| **EXIF** | beim Upload standardmaessig gestript (NFR-013 §6.4); `STORAGE_KEEP_EXIF_PLANT` analog konfigurierbar |

**Begruendung der neuen Kategorie statt Wiederverwendung von `diary`:** Pflanzenfotos haengen an der **Instanz** (`plant_instances`), nicht an einem Tagebucheintrag (`diary`). Eine eigene Kategorie haelt das Storage-Key-Schema (`.../plant/...`) sauber, ermoeglicht kategorie-spezifische Quotas/Lifecycle-Regeln und eine praezise DSGVO-Klassifizierung — exakt der Erweiterungspunkt, den NFR-013 §4.3 (Enum) vorsieht.

---

## 4. DINOv2-Referenz-Hook (optionaler Daten-Rueckfluss)

Ein Galerie-Foto an einer Pflanze mit **bekannter Art** (`species_key` gesetzt) kann optional als zusaetzliche Referenz in den DINOv2-Index (REQ-029-A) einfliessen. Dieser Hook wird **jetzt** gebaut, bleibt aber bis Phase 2 der Bilderkennung **wirkungslos** (no-op) und ist strikt einwilligungs- und kuratierungs-gesteuert.

### 4.1 Datenfluss

```
Galerie-Upload an PlantInstance (species_key gesetzt)
   └─ Attachment in category `plant` gespeichert (Original bleibt beim Nutzer/Tenant)
   └─ Celery-Task feed_user_reference(attachment_id)
        Guard 1: settings.inference_service_enabled == True         → sonst no-op (Phase 1)
        Guard 2: NICHT Light-Modus (REQ-027)                         → sonst Abbruch (siehe unten)
        Guard 3: Nutzer-Consent `reference_contribution` == True     → sonst Abbruch
        Guard 4: species_key vorhanden & Art ist erkennbar (REQ-029-A §4.3)
        Guard 5: offene `pending_review`-Beitraege des Tenants < Backlog-Limit → sonst Abbruch (§4.3)
        → InferenceServiceClient.reference(
              species_key, scientific_name,
              image=<normalisiertes Bild>,
              source="user_contributed",
              tenant_key=<tenant_key>, contributed_by=<user_key>,  # Provenienz, SR-003
              is_active=False)            # Kuratierungs-Gate, siehe §4.3
        → Inferenz-Service (POST /reference, REQ-029-A §3.3) berechnet das
          Embedding und persistiert NUR den Vektor + Provenienz
          (KEIN Originalbild an den Inferenz-Service, REQ-029-A §4.4)
```

**Light-Modus-Auflösung von Guard 2 (SR-005b):** Im Light-Modus (REQ-027) ist der DSGVO-Consent-Mechanismus deaktiviert; ein `reference_contribution`-Consent kann dort gar nicht erteilt werden. Da der Inferenz-Service zudem erst Phase 2 der Bilderkennung ist und die Haushaltsausnahme keinen Community-Datenbeitrag rechtfertigt, ist der Reference-Hook im Light-Modus **generell deaktiviert** (Guard 2). Die Galerie selbst funktioniert im Light-Modus unveraendert.

**Interner Bildtransfer (SR-006):** Der Transfer des Originalbilds an den Inferenz-Service zur Embedding-Berechnung laeuft ausschliesslich ueber die **interne ClusterIP** des self-hosted Inferenz-Microservice (REQ-029-A §3.1, nicht oeffentlich exponiert) und ueber TLS im Cluster-Netzwerk (NFR-013 §5.3). Der Bildpfad darf niemals ueber eine extern erreichbare Route implementiert werden.

### 4.2 Was NICHT passiert

- Das **Originalbild verlaesst niemals** die Kamerplanter-Instanz Richtung Dritter. Der Inferenz-Service ist self-hosted (REQ-029-A §3); er erhaelt das Bild ausschliesslich zur lokalen Embedding-Berechnung und persistiert **nur den Vektor** (REQ-029-A §4.4).
- Es wird **kein** Embedding aktiv in die Erkennung aufgenommen, solange die Kuratierung (§4.3) es nicht freischaltet.
- Der Hook loest **niemals** automatisch eine Identifikation aus.

### 4.3 Kuratierungs-Gate (`is_active = false`)

User-beigesteuerte Referenzen sind potenziell fehlerhaft (falsche Selbst-Bestimmung der Art, falsches Organ, irrefuehrender Ausschnitt) und werden daher **nie ungeprueft** wirksam. Konsistent mit REQ-029-A §4.5:

- Neue `user_contributed`-Embeddings werden mit `is_active = false`, `source = "user_contributed"` und `exclusion_reason = "pending_review"` angelegt.
- Die Vektorsuche (REQ-029-A §5.3) beruecksichtigt ausschliesslich `is_active = true` — beigesteuerte Fotos beeinflussen die Erkennung erst nach **Platform-Admin-Freigabe** in der Referenzbild-Kuratierung (REQ-029-A §4.5, `PATCH /admin/reference-images/...`).
- Provenienz wird mitgefuehrt: `source = user_contributed`, `tenant_key`, `contributed_by`, `contributed_at` (REQ-029-A §5.1). Das beigesteuerte Original bleibt in der Galerie des Nutzers; im Referenz-Index liegt nur der Vektor.
- **Backlog-/Poisoning-Schutz (SR-005a):** Pro Tenant ist die Zahl gleichzeitig offener `pending_review`-Beitraege begrenzt (`REFERENCE_CONTRIBUTION_PENDING_LIMIT`, Default **100**); darueber wird der Hook abgewiesen (Guard 5), bis der Admin den Backlog abgearbeitet hat. Zusaetzlich rate-limitiert der `feed_user_reference`-Task pro Nutzer. Das verhindert ein Fluten des Kuratierungs-Backlogs mit absichtlich falsch bestimmten Fotos. Der Admin sieht in der Kuratierung die Provenienz (`contributed_by`) zur Plausibilisierung.
- **Light-Modus (REQ-027):** Der Reference-Hook ist im Light-Modus generell deaktiviert (§4.1, Guard 2). Die manuelle Kuratierung kuratiert-beschaffter Referenzen bleibt davon unberuehrt — der alleinige System-User ist Betreiber und Platform-Admin (Memory `project_light_mode_admin_gating`).

### 4.4 Consent

Der Daten-Beitrag ist **opt-in** und erfordert eine eigene Einwilligung `reference_contribution` (REQ-025-Consent-Mechanismus). Ohne Consent wird der Hook nicht ausgefuehrt; die Galerie funktioniert vollstaendig ohne ihn. Der Consent-Text nennt Zweck (Verbesserung der self-hosted Erkennung), Umfang (nur Embedding-Vektor, kein Bild an Dritte) und Widerrufbarkeit.

---

## 4a. Qualitaetsbewertung via Bilderkennung (v1.2)

Der Nutzer kann ein Galerie-Foto **manuell, on-demand** gegen die Bilderkennung (REQ-029/-029-A) schicken, um eine **Einschaetzung der Bildqualitaet** zu erhalten ("ist dieses Foto scharf und typisch genug, dass die Erkennung meine Pflanze sicher wiederfindet?"). Klar abzugrenzen vom DINOv2-Hook (§4): §4 ist ein automatischer, optionaler Daten-**Rueckfluss** in den Referenz-Index; §4a ist eine vom Nutzer ausgeloeste, anzeigende **Bewertung** des einzelnen Fotos.

### 4a.1 Adapter-Wahl
Der Nutzer waehlt den Erkennungspfad ueber die bestehende `IdentificationAdapterRegistry` (REQ-029):
- **`plantnet`** (externe API) — sendet das Foto an einen Dritten; erfordert Consent `plant_identification` (REQ-029 §5) und einen konfigurierten API-Key (`adapter.is_configured()`).
- **`local_embedding`** (DINOv2, self-hosted) — kein Datenabfluss an Dritte; **nur verfuegbar, wenn `inference_service_enabled` und der Adapter konfiguriert ist** (Phase 2). Solange nicht verfuegbar, wird die Option im UI **deaktiviert mit Hinweis** angeboten (aktiviert sich automatisch in Phase 2) — kein toter Code.

Die Bewertung laeuft ueber den bestehenden `IdentificationService` (Consent-Gate, Rate-Limiting, Quell-EXIF-Schutz). Das Galerie-Foto ist beim Upload bereits EXIF-gestript (§3); ein erneuter Strip ist nicht noetig.

### 4a.2 Abgeleitete Qualitaets-Bewertung (Ampel) + Persistenz
Aus dem `IdentificationResult` (suggestions mit `scientific_name`+`confidence`, `is_plant`) und der bekannten Art der Pflanze (`species_key` → erwarteter `scientific_name`) wird eine **Ampel-Bewertung** abgeleitet:
- **`poor` (rot):** `is_plant == false` ODER die erwartete Art ist nicht unter den Top-k UND die Top-1-Konfidenz ist niedrig → Bild vermutlich unscharf, falscher Ausschnitt oder untypisch.
- **`fair` (gelb):** erwartete Art unter den Top-k, aber nicht Top-1 / mittlere Konfidenz → brauchbar, aber nicht ideal.
- **`good` (gruen):** erwartete Art == Top-1 mit hoher Konfidenz → gut geeignet/repraesentativ.
- Hat die Pflanze **keine** Art gesetzt (`species_key` leer), entfaellt der Soll-Ist-Abgleich; die Bewertung stuetzt sich nur auf `is_plant` + Top-1-Konfidenz.

Das Ergebnis wird **am Attachment gespeichert** (`quality_assessment`: `adapter`, `assessed_at`, `is_plant`, `rating`, `expected_species_matched`, Top-3-`suggestions` mit Art+Konfidenz), sodass es **im Nachgang** in der Galerie/Lightbox sichtbar bleibt (Ampel-Badge) und erneut ausgeloest werden kann.

### 4a.3 Datenschutz & Abgrenzung
- `plantnet`-Pfad: Foto verlaesst die Instanz Richtung Dritter → Consent-Pflicht; im **Light-Modus** (REQ-027, Consent deaktiviert) ist der externe Pfad nur nutzbar, wenn der Betreiber das bewusst freischaltet (sonst nur `local_embedding`, sobald verfuegbar).
- `local_embedding`-Pfad: kein Datenabfluss (self-hosted, ClusterIP/TLS, REQ-029-A §3.1).
- Berechtigung: Ausloesen erfordert `require_permission` auf der Instanz (mind. `UPDATE_RESOURCE`, da ein Ergebnis persistiert wird); `viewer` darf eine vorhandene Bewertung sehen, aber keine neue ausloesen.

---

## 5. DSGVO-Konformitaet

REQ-034 erbt das gesamte Erasure-Fundament aus NFR-013 §6 / REQ-025 §3.1 (W-007). Galerie-Fotos werden wie folgt klassifiziert:

| Ereignis | Verhalten |
|----------|-----------|
| **Foto einzeln loeschen** (Nutzer) | Hard-Delete: `attachments`-Metadaten weg + `delete_object(storage_key)` + Entfernen aus `photo_refs`/`cover_photo_ref`. Thumbnails werden mitgeloescht. |
| **Pflanzeninstanz loeschen** | Alle `photo_refs`-Attachments hart geloescht (§2.1). |
| **Tenant loeschen** (REQ-024/-025) | `delete_prefix("t/{tenant_key}/")` erfasst auch `.../plant/...` (NFR-013 §6.1). |
| **Nutzer loeschen** (REQ-025, Scope `user_diary_attachments`) | Galerie-Fotos gehoeren zum **Pflanzen-Datensatz** des Tenants (z.B. Gemeinschaftsgarten) und bleiben erhalten; `created_by` wird auf `_anonymized` gesetzt; EXIF-Strip-Pass wenn `STORAGE_KEEP_EXIF_PLANT=true` (NFR-013 §6.2 Phase 0, W-007-Reihenfolge). |
| **Beigesteuerte DINOv2-Referenz** | Bei Nutzer-/Tenant-Loeschung werden `user_contributed`-Embeddings mit passendem `contributed_by`/`tenant_key` entfernt — als **Erasure-Phase 0.5** `_reference_index_cleanup` (REQ-025 §3.5, AK-OS-05), VOR der ArangoDB-Loeschung. Die dafuer noetigen Provenienz-Felder sind in REQ-029-A v1.2 §5.1 ergaenzt (SR-003). Nur Vektor + Provenienz, kein Bild. |

**Begruendung Scope-Wahl:** Galerie-Fotos sind primaer Dokumentation der Pflanze (analog Tagebuch-/Ernte-/Inspektionsfotos), nicht persoenliche Profil-/Notiz-Fotos. Daher `user_diary_attachments` (Anonymisierung statt Hard-Delete) — das bewahrt den Pflanzen-Datensatz in geteilten Tenants, entkoppelt ihn aber vom geloeschten Nutzer. EXIF (GPS/Geraete-ID) wird beim Upload ohnehin standardmaessig entfernt (§3, NFR-013 §6.4).

---

## 6. Sicherheit & Berechtigungen

- **Upload-Pipeline:** unveraendert NFR-013 §5.1 (Auth → AuthZ → Quota → MIME-Whitelist → Magic-Byte → Groessenlimit → optional Virus-Scan → SHA-256 → Schreiben → Metadaten → Audit-Log).
- **Permission-Vertrag (SR-002, REQ-024 v1.5 §1a):** Die in NFR-013 §5.1 abstrakt notierte `attachment:create`-Anforderung wird auf den realen `Permission`-Enum abgebildet — **Upload** = `Permission.CREATE_RESOURCE`, **Cover setzen** = `Permission.UPDATE_RESOURCE`, **Loeschen** = `Permission.DELETE_RESOURCE`. Jeweils mit der Zuweisungs-Write-Kontrolle aus REQ-024 §1a.5 (`grower` darf eigene/community-Pflanzen-Fotos, nicht fremde). Maßgeblich ist die neue Matrix-Zeile **„Plant Instance Photos (`category=plant`)"** (REQ-024 §1a.1).
- **Viewer:** `Permission.READ_RESOURCE` — darf die Galerie sehen, aber nicht hochladen/Cover setzen/loeschen (AC-13).
- **Stable URI** ist die einzige Frontend-Adresse (NFR-013 §2.4) — kein direkter Storage-Zugriff.
- **Cross-Tenant-Schutz:** Verknuepfen eines Attachments mit fremdem `tenant_key` wird abgelehnt (§2.1). Tenant-Isolation auf Storage-Ebene durch das Key-Schema (NFR-013 §2.3).
- **Reference-Hook-Berechtigung:** Der Daten-Beitrag (§4) erfordert zusaetzlich Consent `reference_contribution`; die Freigabe der Referenz ist ausschliesslich Platform-Admin.

---

## 7. API-Skizze (tenant-scoped, REQ-013-Router)

> Die generischen Attachment-Endpunkte (`POST/GET/DELETE /api/v1/t/{slug}/attachments`) liefert NFR-013. REQ-034 ergaenzt **nur** die fachliche Verknuepfung an der Pflanzeninstanz.

| Methode | Pfad | Zweck |
|---------|------|-------|
| `POST` | `/api/v1/t/{slug}/plant-instances/{key}/photos` | Foto hochladen (Proxy ODER presign-Initiierung) + an Instanz verknuepfen (category `plant`). |
| `GET` | `/api/v1/t/{slug}/plant-instances/{key}/photos` | Galerie-Listing: `attachment_id`, Thumbnail-URIs, `is_cover`, `created_at`. |
| `DELETE` | `/api/v1/t/{slug}/plant-instances/{key}/photos/{attachment_id}` | Foto loesen + Hard-Delete (§5). |
| `PUT` | `/api/v1/t/{slug}/plant-instances/{key}/photos/{attachment_id}/cover` | Als Titelbild markieren (`cover_photo_ref`). |

Antworten referenzieren ausschliesslich `attachment_id` + Stable URIs (`/api/v1/t/{slug}/attachments/{attachment_id}` und die Thumbnail-Varianten).

---

## 8. Akzeptanzkriterien

| ID | Kriterium |
|----|-----------|
| **AC-01** | Ein eingeloggter Nutzer mit `attachment:create`-Recht kann an einer Pflanzeninstanz ueber Webcam, Smartphone-Kamera ODER Datei-Upload ein Foto hochladen; es erscheint anschliessend in der Galerie der Instanz. |
| **AC-02** | Galerie und Listenansichten laden ausschliesslich Thumbnails; das Originalbild wird nur in der Lightbox/Detailansicht geladen. |
| **AC-03** | Das Frontend referenziert kein Storage-Backend, keinen Bucket, keine Region — ausschliesslich `attachment_id` und `/api/v1/t/{slug}/attachments/...` (NFR-013 AC-04). |
| **AC-04** | Hochgeladene Fotos werden mit `category = plant` und korrektem tenant-isoliertem Storage-Key (`t/{tenant_key}/plant/{yyyy}/{mm}/{ulid}.{ext}`) abgelegt; `ext` aus MIME-Type, nie aus dem Originalnamen. |
| **AC-05** | Magic-Byte-/MIME-Validierung blockiert Uploads, deren Inhalt nicht zur Foto-Whitelist passt (NFR-013 §5.1/AC-06). |
| **AC-06** | Ein Foto kann als Titelbild markiert werden; das Cover erscheint als Vorschau im Info-Tab und in der Listenansicht. Pflanzen ohne Foto zeigen einen Platzhalter. |
| **AC-07** | Einzelnes Loeschen eines Fotos entfernt Metadaten, Original und alle Thumbnails (keine verwaisten Bytes) und nimmt es aus `photo_refs`/`cover_photo_ref`. |
| **AC-08** | Loeschen der Pflanzeninstanz loescht alle zugehoerigen Galerie-Fotos vollstaendig. |
| **AC-09** | Bei Nutzer-Loeschung (Scope `user_diary_attachments`) bleiben Galerie-Fotos erhalten, `created_by` wird anonymisiert; EXIF-Strip-Pass laeuft bei `STORAGE_KEEP_EXIF_PLANT=true`. Tenant-Loeschung entfernt alle Galerie-Fotos via `delete_prefix`. |
| **AC-10** | Der DINOv2-Referenz-Hook ist implementiert, aber bei `inference_service_enabled = false` ein vollstaendiger no-op (kein Inferenz-Aufruf, keine Nebenwirkung). |
| **AC-11** | Bei aktivem Inferenz-Service und vorliegendem `reference_contribution`-Consent wird ein Galerie-Foto einer Pflanze mit bekannter Art als `user_contributed`-Embedding mit `is_active = false` angelegt; es beeinflusst die Erkennung erst nach Platform-Admin-Freigabe. Das Originalbild wird dabei nicht persistiert (nur der Vektor). |
| **AC-12** | EXIF-Daten (GPS/Geraete-ID) werden beim Upload standardmaessig entfernt (Client + Server), sofern nicht `STORAGE_KEEP_EXIF_PLANT=true`. |
| **AC-13** | Ein `viewer` kann die Galerie betrachten, aber keine Fotos hochladen/loeschen/als Cover setzen (REQ-024-Permission-Matrix). |
| **AC-14** | i18n DE/EN fuer alle Galerie-UI-Texte; DE ist Default/Fallback. |
| **AC-15** | Ueberschreiten der Galerie-Quota (`STORAGE_MAX_PHOTOS_PER_INSTANCE`, Default 50) ODER der Tenant-Storage-Quota lehnt den Upload vor dem Schreiben ab (HTTP 409) mit verstaendlicher Meldung; keine verwaisten Bytes. |
| **AC-16** | Im Light-Modus (REQ-027) ist der DINOv2-Referenz-Hook generell deaktiviert (kein Consent-Pfad noetig); die Galerie funktioniert dort vollstaendig. |

---

## 9. Definition of Done

- `PlantInstance.photo_refs` + `cover_photo_ref` implementiert; Service erzwingt Category-/Tenant-Konsistenz.
- Galerie-Tab in `PlantInstanceDetailPage.tsx` (Grid, Lightbox, Upload via wiederverwendetem `ImageCapturePanel`, Loeschen, Cover) + Cover-Vorschau im Info-/Listen-Kontext, i18n DE/EN, `useMemo`-Konvention.
- 4 fachliche API-Endpunkte (§7) auf dem NFR-013-Attachment-Fundament; tenant-scoped, permission-gegated.
- NFR-013 v1.2 mit category `plant` gemerged (Changelog + §4.3/§5.2).
- DINOv2-Referenz-Hook als Celery-Task mit drei Guards + Kuratierungs-Gate (`is_active=false`); no-op bis Phase 2.
- DSGVO: Galerie-Fotos in Erasure-Klassifizierung (`user_diary_attachments`) integriert; EXIF-Strip; Tenant-/Instanz-/Einzel-Loeschung deterministisch.
- E2E-Testcases `spec/e2e-testcases/TC-REQ-034.md`; Quality-Gate gruen (ruff/eslint/tsc/pytest/vitest); 3-Agent-Kette (UI-Review/Tests/Doku).

---

## 10. Offene Punkte

| Nr. | Frage | Entscheider | Status |
|-----|-------|-------------|--------|
| O-01 | Maximalzahl an Galerie-Fotos pro Pflanzeninstanz / Tenant-Quota? | Produkt + DevOps | **Gelöst (SR-004):** Default 50/Instanz (`STORAGE_MAX_PHOTOS_PER_INSTANCE`) + Tenant-Storage-Quota (§3). |
| O-02 | Sollen Galerie-Fotos optional einem **Tagebucheintrag** (REQ-013 PlantDiaryEntry) zugeordnet werden koennen (Cross-Referenz `plant` ↔ `diary`)? | Produkt | offen |
| O-03 | Soll die Cover-Foto-Vorschau auch in Kalender-/Dashboard-Kacheln (REQ-009/-015) erscheinen? | Produkt + Frontend | offen |
| O-04 | Granularitaet des `reference_contribution`-Consent (pro Foto/Pflanze/global)? | Produkt + Datenschutz | **Gelöst (SR-001):** global pro Nutzer (UNIQUE(user_key, purpose)-Constraint, REQ-025 §3.1). |
| O-05 | **Scope-Wahl im persoenlichen Tenant (SR-009, DPO-Follow-up):** Soll ein Galerie-Foto in einem **persoenlichen** Tenant bei Nutzer-Loeschung wirklich `user_diary_attachments` (bleibt) oder `user_personal` (Hard-Delete) sein? Im persoenlichen Tenant ohne Aufbewahrungspflicht ist Beibehalten schwerer zu rechtfertigen. Empfehlung: tenant-typ-abhaengige Klassifizierung (personal → `user_personal`, shared → `user_diary_attachments`). | DPO + Produkt | offen (Rechtsfrage) |

---

**Dokumenten-Ende**
**Version:** 1.0
**Status:** Entwurf
