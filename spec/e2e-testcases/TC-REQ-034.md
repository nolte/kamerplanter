---
req_id: REQ-034
title: Pflanzenfoto-Galerie (eigene Fotos pro Pflanzeninstanz)
test_count: 18
coverage_areas:
  - Galerie-Tab auf der Pflanzeninstanz-Detailseite
  - Foto-Upload via Datei-Upload (Drag&Drop)
  - Foto-Upload via Smartphone-Kamera (capture)
  - Foto-Upload via Webcam (getUserMedia)
  - Thumbnail-Grid und Lazy-Loading
  - Lightbox (Originalbild-Ansicht)
  - Cover-Foto setzen und Vorschau in Info-Tab/Liste
  - Einzelnes Foto loeschen
  - Platzhalter bei Pflanzen ohne Foto
  - Berechtigung viewer vs. grower (Upload/Loeschen gesperrt)
  - Ungueltiger Dateityp wird abgelehnt
  - DINOv2-Referenzbeitrag (Consent-Dialog, opt-in)
  - i18n DE/EN
generated: 2026-06-19
version: "1.0"
---

# TC-REQ-034: Pflanzenfoto-Galerie

Dieses Dokument enthaelt End-to-End-Testfaelle aus **REQ-034 Pflanzenfoto-Galerie v1.0**, ausschliesslich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfaellen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

Die UI-Sprache ist **Deutsch** (Standard-Locale). Alle Labels, Buttons und Meldungen referenzieren die deutschen i18n-Texte.

REQ-034 ergaenzt die Pflanzeninstanz (REQ-013) um eine Foto-Galerie auf Basis des Storage-Fundaments (NFR-013). Der Nutzer kann eigene Fotos seiner Pflanzen aufnehmen, ansehen, als Titelbild markieren und loeschen — mit derselben Aufnahme-UX wie die Bilderkennung (REQ-029).

---

## 1. Galerie-Tab & Anzeige

### TC-REQ-034-001: Galerie-Tab auf der Pflanzeninstanz-Detailseite sichtbar

**Requirement**: REQ-034 § 2.3 — Anzeige in der Instanz-Uebersicht
**Priority**: Critical
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt (Rolle grower oder admin)
- Mindestens eine Pflanzeninstanz existiert

**Testschritte**:
1. Nutzer navigiert zur Detailseite einer Pflanzeninstanz
2. Nutzer betrachtet die Tab-Leiste der Detailseite

**Erwartete Ergebnisse**:
- Ein Tab „Fotos" (bzw. „Galerie") ist in der Tab-Leiste sichtbar
- Beim Klick auf den Tab oeffnet sich die Galerie-Ansicht

**Nachbedingungen**:
- Galerie-Tab ist aktiv

**Tags**: [req-034, gallery, tab, plant-instance, navigation]

---

### TC-REQ-034-002: Leere Galerie zeigt Leerzustand mit Upload-Aufforderung

**Requirement**: REQ-034 § 2.3
**Priority**: High
**Category**: Leerzustand
**Preconditions**:
- Pflanzeninstanz ohne Fotos
- Galerie-Tab geoeffnet

**Testschritte**:
1. Nutzer betrachtet die Galerie-Ansicht einer Pflanze ohne Fotos

**Erwartete Ergebnisse**:
- Ein Leerzustand-Hinweis ist sichtbar (z.B. „Noch keine Fotos vorhanden")
- Ein Button zum Hinzufuegen eines Fotos ist sichtbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, gallery, empty-state]

---

### TC-REQ-034-003: Pflanze ohne Foto zeigt Platzhalter in der Listenansicht

**Requirement**: REQ-034 § 2.3, AC-06
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Pflanzeninstanz ohne Fotos
- Nutzer auf der Pflanzen-Listenseite

**Testschritte**:
1. Nutzer betrachtet die Pflanzen-Liste/Karten

**Erwartete Ergebnisse**:
- Die Pflanze ohne Foto zeigt einen neutralen Platzhalter (kein gebrochenes Bild)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, gallery, placeholder, list-view]

---

### TC-REQ-034-004: Thumbnail-Grid zeigt vorhandene Fotos

**Requirement**: REQ-034 § 2.3, AC-02
**Priority**: Critical
**Category**: Listenansicht
**Preconditions**:
- Pflanzeninstanz mit mindestens 3 Fotos
- Galerie-Tab geoeffnet

**Testschritte**:
1. Nutzer betrachtet die Galerie-Ansicht

**Erwartete Ergebnisse**:
- Die Fotos werden als Thumbnail-Raster (Grid) angezeigt
- Jedes Foto ist als kleine Vorschau sichtbar
- Die Ansicht laedt fluessig (Thumbnails, nicht die Originale)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, gallery, grid, thumbnails]

---

### TC-REQ-034-005: Klick auf Thumbnail oeffnet Lightbox mit Originalbild

**Requirement**: REQ-034 § 2.3, AC-02
**Priority**: High
**Category**: Detailansicht
**Preconditions**:
- Galerie mit mindestens 1 Foto

**Testschritte**:
1. Nutzer klickt auf ein Thumbnail in der Galerie

**Erwartete Ergebnisse**:
- Eine Lightbox/Vollbildansicht oeffnet sich
- Das Foto wird in hoher Aufloesung angezeigt
- Die Lightbox kann geschlossen werden (X oder Klick ausserhalb)

**Nachbedingungen**:
- Lightbox geschlossen, Galerie weiter sichtbar

**Tags**: [req-034, gallery, lightbox, detail-view]

---

## 2. Foto-Upload

### TC-REQ-034-006: Foto per Datei-Upload hinzufuegen

**Requirement**: REQ-034 § 2.2, AC-01
**Priority**: Critical
**Category**: Formular
**Preconditions**:
- Galerie-Tab geoeffnet
- Nutzer hat eine gueltige Bilddatei (JPEG/PNG)

**Testschritte**:
1. Nutzer klickt auf „Foto hinzufuegen"
2. Ein Aufnahme-Dialog mit drei Optionen (Webcam, Kamera, Datei) erscheint
3. Nutzer waehlt „Datei auswaehlen" und selektiert eine gueltige Bilddatei
4. Nutzer bestaetigt den Upload

**Erwartete Ergebnisse**:
- Waehrend des Uploads ist ein Ladezustand sichtbar
- Nach Abschluss erscheint das neue Foto als Thumbnail in der Galerie
- Eine Erfolgsmeldung wird angezeigt

**Nachbedingungen**:
- Die Galerie enthaelt ein zusaetzliches Foto

**Tags**: [req-034, upload, file-upload, gallery]

---

### TC-REQ-034-007: Aufnahme-Dialog bietet Webcam, Smartphone-Kamera und Datei-Upload

**Requirement**: REQ-034 § 2.2 — Wiederverwendung der Bilderkennungs-UX
**Priority**: High
**Category**: Formular
**Preconditions**:
- Galerie-Tab geoeffnet

**Testschritte**:
1. Nutzer klickt auf „Foto hinzufuegen"
2. Nutzer betrachtet den Aufnahme-Dialog

**Erwartete Ergebnisse**:
- Drei Erfassungswege sind sichtbar: Live-Webcam, Smartphone-Kamera (Rueckkamera), Datei-Upload/Drag&Drop
- Die Optionen entsprechen der UX der Bilderkennung

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, upload, capture-modes, webcam, camera]

---

### TC-REQ-034-008: Drag&Drop eines Fotos in die Galerie

**Requirement**: REQ-034 § 2.2, AC-01
**Priority**: Medium
**Category**: Formular
**Preconditions**:
- Aufnahme-Dialog mit Drag&Drop-Zone geoeffnet

**Testschritte**:
1. Nutzer zieht eine Bilddatei in die Drop-Zone und laesst sie los

**Erwartete Ergebnisse**:
- Die Datei wird uebernommen und als Vorschau angezeigt
- Nach Bestaetigung erscheint das Foto in der Galerie

**Nachbedingungen**:
- Die Galerie enthaelt ein zusaetzliches Foto

**Tags**: [req-034, upload, drag-drop]

---

### TC-REQ-034-009: Ungueltiger Dateityp wird abgelehnt

**Requirement**: REQ-034 AC-05 — Magic-Byte-/MIME-Validierung
**Priority**: Critical
**Category**: Validierung
**Preconditions**:
- Aufnahme-Dialog geoeffnet

**Testschritte**:
1. Nutzer versucht, eine Nicht-Bilddatei hochzuladen (z.B. eine PDF- oder Textdatei, ggf. mit umbenannter Endung)

**Erwartete Ergebnisse**:
- Der Upload wird abgelehnt
- Eine verstaendliche Fehlermeldung erscheint (z.B. „Nur Bilddateien sind erlaubt")
- Es wird kein Foto in die Galerie aufgenommen

**Nachbedingungen**:
- Die Galerie ist unveraendert

**Tags**: [req-034, upload, validation, mime, error]

---

### TC-REQ-034-010: Zu grosse Datei wird abgelehnt

**Requirement**: REQ-034 § 3 — Max-Groesse 25 MB
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Aufnahme-Dialog geoeffnet

**Testschritte**:
1. Nutzer versucht, eine Bilddatei oberhalb des Groessenlimits hochzuladen

**Erwartete Ergebnisse**:
- Der Upload wird abgelehnt
- Eine Fehlermeldung nennt das Groessenlimit

**Nachbedingungen**:
- Die Galerie ist unveraendert

**Tags**: [req-034, upload, validation, file-size, error]

---

## 3. Cover-Foto & Loeschen

### TC-REQ-034-011: Foto als Titelbild markieren

**Requirement**: REQ-034 § 2.3, AC-06
**Priority**: High
**Category**: Formular
**Preconditions**:
- Galerie mit mindestens 2 Fotos

**Testschritte**:
1. Nutzer oeffnet das Kontextmenue/die Aktionen eines Fotos
2. Nutzer waehlt „Als Titelbild setzen"

**Erwartete Ergebnisse**:
- Das gewaehlte Foto wird als Titelbild markiert (visuelle Kennzeichnung)
- Eine Bestaetigungsmeldung erscheint

**Nachbedingungen**:
- Das markierte Foto ist das Cover der Pflanze

**Tags**: [req-034, gallery, cover-photo]

---

### TC-REQ-034-012: Titelbild erscheint als Vorschau im Info-Tab

**Requirement**: REQ-034 § 2.3, AC-06
**Priority**: Medium
**Category**: Detailansicht
**Preconditions**:
- Pflanzeninstanz mit gesetztem Titelbild

**Testschritte**:
1. Nutzer wechselt auf den Info-Tab der Pflanzeninstanz

**Erwartete Ergebnisse**:
- Das Titelbild wird als Vorschau im Info-Tab angezeigt

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, gallery, cover-photo, info-tab]

---

### TC-REQ-034-013: Einzelnes Foto loeschen

**Requirement**: REQ-034 § 5, AC-07
**Priority**: Critical
**Category**: Formular
**Preconditions**:
- Galerie mit mindestens 1 Foto

**Testschritte**:
1. Nutzer oeffnet die Aktionen eines Fotos
2. Nutzer waehlt „Loeschen"
3. Nutzer bestaetigt die Sicherheitsabfrage

**Erwartete Ergebnisse**:
- Das Foto verschwindet aus der Galerie
- Eine Bestaetigungsmeldung erscheint

**Nachbedingungen**:
- Die Galerie enthaelt ein Foto weniger

**Tags**: [req-034, gallery, delete, confirmation]

---

### TC-REQ-034-014: Loeschen des Titelbildes setzt Cover zurueck

**Requirement**: REQ-034 § 2.1, § 5
**Priority**: Medium
**Category**: Formular
**Preconditions**:
- Galerie mit mehreren Fotos, eines davon Titelbild

**Testschritte**:
1. Nutzer loescht das aktuell als Titelbild markierte Foto

**Erwartete Ergebnisse**:
- Das Foto wird entfernt
- Die Cover-Vorschau zeigt nun ein anderes (z.B. das erste) Foto oder den Platzhalter, falls kein Foto mehr vorhanden ist

**Nachbedingungen**:
- Konsistenter Cover-Zustand

**Tags**: [req-034, gallery, delete, cover-photo]

---

## 4. Berechtigungen

### TC-REQ-034-015: Viewer kann Galerie sehen, aber nicht hochladen oder loeschen

**Requirement**: REQ-034 § 6, AC-13
**Priority**: Critical
**Category**: Berechtigung
**Preconditions**:
- Nutzer mit Rolle „viewer" im Tenant
- Pflanzeninstanz mit Fotos

**Testschritte**:
1. Viewer oeffnet den Galerie-Tab einer Pflanzeninstanz

**Erwartete Ergebnisse**:
- Die Fotos sind sichtbar
- Es ist kein „Foto hinzufuegen"-Button verfuegbar
- Loeschen- und „Als Titelbild setzen"-Aktionen sind nicht verfuegbar

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, permissions, viewer, read-only]

---

## 5. DINOv2-Referenzbeitrag (optional)

### TC-REQ-034-016: Beitrags-Option nur bei Pflanze mit bekannter Art und aktivem Inferenz-Service

**Requirement**: REQ-034 § 4 — DINOv2-Referenz-Hook
**Priority**: Medium
**Category**: Formular
**Preconditions**:
- Inferenz-Service ist deaktiviert (Phase 1, Default)
- Pflanzeninstanz mit gesetzter Art

**Testschritte**:
1. Nutzer laedt ein Foto hoch und betrachtet die Galerie-Optionen

**Erwartete Ergebnisse**:
- Es erscheint **keine** Aufforderung, das Foto als Referenz beizusteuern (Hook ist no-op)
- Der Upload funktioniert normal

**Nachbedingungen**:
- Kein Referenzbeitrag erfolgt

**Tags**: [req-034, dinov2, reference, no-op]

---

### TC-REQ-034-017: Referenzbeitrag erfordert ausdrueckliche Einwilligung

**Requirement**: REQ-034 § 4.4, AC-11
**Priority**: High
**Category**: Berechtigung
**Preconditions**:
- Inferenz-Service ist aktiv
- Pflanzeninstanz mit bekannter Art
- Nutzer hat noch keine Einwilligung „reference_contribution" erteilt

**Testschritte**:
1. Nutzer laedt ein Foto hoch
2. Nutzer wird gefragt, ob er das Foto als Referenz beisteuern moechte
3. Nutzer betrachtet den Einwilligungstext

**Erwartete Ergebnisse**:
- Der Einwilligungstext nennt Zweck (Verbesserung der Erkennung), Umfang (nur Embedding, kein Bild an Dritte) und Widerrufbarkeit
- Ohne Zustimmung erfolgt kein Beitrag; die Galerie funktioniert dennoch normal
- Bei Zustimmung wird der Beitrag angenommen (Hinweis, dass er erst nach Pruefung wirksam wird)

**Nachbedingungen**:
- Foto ist in der Galerie; Referenzbeitrag nur bei Zustimmung vorgemerkt (inaktiv bis Admin-Freigabe)

**Tags**: [req-034, dinov2, reference, consent]

---

## 6. Internationalisierung

### TC-REQ-034-018: Galerie-UI in Englisch

**Requirement**: REQ-034 AC-14
**Priority**: Medium
**Category**: i18n
**Preconditions**:
- Nutzer hat die UI-Sprache auf Englisch umgestellt

**Testschritte**:
1. Nutzer oeffnet den Galerie-Tab einer Pflanzeninstanz

**Erwartete Ergebnisse**:
- Alle Galerie-Texte (Tab-Titel, Buttons, Leerzustand, Meldungen) erscheinen in Englisch
- Keine fehlenden Uebersetzungsschluessel (kein roher i18n-Key sichtbar)

**Nachbedingungen**:
- Kein Status geaendert

**Tags**: [req-034, i18n, english]

---

**Dokumenten-Ende**
