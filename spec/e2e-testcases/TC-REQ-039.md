---
requirement_id: REQ-039
title: Klimazonen- & Winterhärte-Geodaten (Hardiness Zones)
test_count: 17
coverage_areas: [Automatische Zonen-Ableitung (GPS/PLZ), Manuelle Übersteuerung, Rand-Clamping, Zonenkatalog & HardinessZoneBadge, Winterhärte-Ampel-Grenzfälle, Rückwärtskompatibilität/Migration, Periodische Aktualisierung, Standort-Typ-Einschränkung, Frosttermin-Defaults, Pflanzen-Anlage-Warnung, Navigation]
generated: "2026-07-11"
---

## Hinweis zur Ableitungsbasis

Die Recherche im Interface-Bestand (`src/frontend/src/pages/standorte/`, `src/frontend/src/pages/pflanzen/`, `src/frontend/src/pages/ueberwinterung/`) ergab: Das **Backend** von REQ-039 ist vollständig implementiert (`HardinessZoneResolver`, `HardinessZoneService`, `evaluate_winter_hardiness`/`winter_hardiness_engine.py`, Endpunkte `/api/v1/hardiness-zones`, `/api/v1/hardiness-zones/{zone}`, `/api/v1/t/{tenant}/sites/{key}/hardiness`, `POST .../resolve-hardiness-zone`, Celery-Task `refresh_site_hardiness_zones`). Die in REQ-039 §4 beschriebene **Frontend-Oberfläche** (Button „Zone automatisch ermitteln", `HardinessZoneBadge`-Chip, Inline-Warnung im Pflanzen-Anlage-Dialog, Zonendifferenz-Begründungstext in der Ampel) ist im aktuellen Codestand **nicht auffindbar** — das Standort-Formular (`SiteCreateDialog.tsx`, `SiteDetailPage.tsx`) bietet weiterhin nur das bestehende freie `climate_zone`-Textfeld. Test-Fälle, die diese noch nicht gebaute Oberfläche betreffen, sind daher **aus dem Anforderungstext abgeleitet** (nicht am realen Bildschirm verifiziert) und sind unten mit „(spec-abgeleitet)" gekennzeichnet. Test-Fälle, die auf tatsächlich vorhandenen Bildschirmen (Standort-Formular, Überwinterungs-Abschnitt der Pflanzen-Detailseite `OverwinteringSection.tsx`) beruhen, sind mit „(bildschirm-verifiziert)" gekennzeichnet.

---

## TC-REQ-039-001: Automatische Zonen-Ableitung aus GPS-Koordinaten (spec-abgeleitet)
**Requirement**: REQ-039 — §3 `HardinessZoneResolver.derive_from_climate_normals` / §4 Frontend-Integration / §7 Akzeptanzkriterium 3
**Priority**: Critical
**Category**: happy-path
**Technique**: user-journey
**Preconditions**:
- Nutzerin ist angemeldet und hat einen Standort mit gesetzten GPS-Koordinaten (Typ „Außenbereich" oder „Gewächshaus") ohne bisher gesetzte Winterhärtezone angelegt.
- Für den Standort liegen bereits Klimanormale (REQ-041) vor.
**Steps**:
1. Nutzerin öffnet die Detailseite des Standorts.
2. Nutzerin klickt auf die Schaltfläche „Zone automatisch ermitteln" neben dem Zonenfeld.
**Expected Results**:
- Die Seite zeigt die ermittelte Winterhärtezone (z. B. „7b") sowie den daraus abgeleiteten mittleren Jahres-Tiefstwert und die Quelle „automatisch aus GPS-Daten" an.
- Es erscheint keine Fehlermeldung.
**Postconditions**:
- Der Standort zeigt bei erneutem Aufruf der Detailseite dieselbe automatisch ermittelte Zone, bis sie manuell überschrieben oder eine erzwungene Neu-Ermittlung ausgelöst wird.
**Related Cases**: [TC-REQ-039-004, TC-REQ-039-005, TC-REQ-039-009]
**Tags**: [REQ-039, standorte, happy-path]

## TC-REQ-039-002: Schaltfläche „Zone automatisch ermitteln" bleibt ohne Standortdaten deaktiviert (spec-abgeleitet)
**Requirement**: REQ-039 — §4 Frontend-Integration
**Priority**: High
**Category**: validation
**Technique**: visual-feedback
**Preconditions**:
- Nutzerin legt gerade einen neuen Standort an oder bearbeitet einen bestehenden Standort ohne GPS-Koordinaten und ohne Postleitzahl.
**Steps**:
1. Nutzerin öffnet das Standort-Formular.
2. Nutzerin lässt die Felder „GPS-Koordinaten" und „Postleitzahl" leer.
3. Nutzerin betrachtet die Schaltfläche „Zone automatisch ermitteln".
**Expected Results**:
- Die Schaltfläche ist sichtbar, aber inaktiv (nicht anklickbar).
- Ein Hinweistext erklärt, dass GPS-Koordinaten oder eine Postleitzahl benötigt werden.
**Postconditions**:
- Keine Zustandsänderung am Standort.
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-004]
**Tags**: [REQ-039, standorte, validation]

## TC-REQ-039-003: Automatische Ableitung meldet verständlichen Fehler ohne Klimanormale (bildschirm-teilweise-verifiziert: Fehlerverhalten des Endpunkts real, Anzeige spec-abgeleitet)
**Requirement**: REQ-039 — §3 `HardinessZoneService.resolve_for_site` / §7 Akzeptanzkriterium 3
**Priority**: High
**Category**: error
**Technique**: error-guessing
**Preconditions**:
- Standort mit GPS-Koordinaten existiert, aber es wurden für ihn noch keine Klimanormale (REQ-041) abgerufen.
**Steps**:
1. Nutzerin öffnet die Standort-Detailseite.
2. Nutzerin klickt auf „Zone automatisch ermitteln".
**Expected Results**:
- Die Seite zeigt eine verständliche Fehlermeldung, dass für den Standort noch keine Klimanormale vorliegen und zunächst die Klimadaten abgerufen werden müssen.
- Die Winterhärtezone des Standorts bleibt unverändert (leer).
**Postconditions**:
- Kein `hardiness_zone`-Wert wird gesetzt; ein erneuter Versuch nach Abruf der Klimanormale (siehe REQ-041) kann wiederholt werden.
**Related Cases**: [TC-REQ-039-001]
**Tags**: [REQ-039, standorte, error]

## TC-REQ-039-004: Zonen-Ableitung über Postleitzahl als GPS-Alternative (spec-abgeleitet)
**Requirement**: REQ-039 — §2 `Site.postal_code` / §4 Frontend-Integration
**Priority**: Medium
**Category**: happy-path
**Technique**: equivalence-partition
**Preconditions**:
- Standort ohne GPS-Koordinaten, aber mit gesetzter Postleitzahl existiert.
**Steps**:
1. Nutzerin öffnet die Standort-Detailseite.
2. Nutzerin klickt auf „Zone automatisch ermitteln".
**Expected Results**:
- Die Schaltfläche ist aktiv (da eine Postleitzahl vorliegt) und die Ableitung liefert eine Zone auf Basis der postleitzahlbasierten Klimadaten.
**Postconditions**:
- Winterhärtezone und Quelle sind am Standort gesetzt.
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-002]
**Tags**: [REQ-039, standorte, happy-path]

## TC-REQ-039-005: Manuelle Zonen-Eingabe überschreibt einen abgeleiteten Wert (bildschirm-verifiziert: `climate_zone`-Textfeld real vorhanden)
**Requirement**: REQ-039 — §2 `Site.hardiness_zone_source` / §4 Frontend-Integration „Manueller Override bleibt jederzeit möglich"
**Priority**: Critical
**Category**: state-transition
**Technique**: state-transition
**Preconditions**:
- Standort hat eine automatisch ermittelte Winterhärtezone (Quelle „automatisch").
**Steps**:
1. Nutzerin öffnet das Bearbeiten-Formular des Standorts.
2. Nutzerin trägt im Zonenfeld manuell einen abweichenden Zonenwert ein (z. B. „6b" statt „7a").
3. Nutzerin speichert das Formular.
**Expected Results**:
- Der Standort zeigt danach die manuell eingetragene Zone „6b".
- Die angezeigte Quelle wechselt auf „manuell".
**Postconditions**:
- Der manuell gesetzte Wert bleibt bestehen, bis er erneut manuell geändert oder eine erzwungene automatische Neu-Ermittlung ausgelöst wird (siehe TC-REQ-039-006, TC-REQ-039-016).
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-006, TC-REQ-039-016]
**Tags**: [REQ-039, standorte, state-transition]

## TC-REQ-039-006: Erneutes automatisches Ermitteln überschreibt eine manuell gesetzte Zone nicht (spec-abgeleitet)
**Requirement**: REQ-039 — §3 `resolve_for_site` (`force`-Parameter) / §7 Akzeptanzkriterium „manuell gesetztes hardiness_zone wird … nicht überschrieben"
**Priority**: High
**Category**: state-transition
**Technique**: state-transition
**Preconditions**:
- Standort mit manuell gesetzter Winterhärtezone (Quelle „manuell") aus TC-REQ-039-005.
**Steps**:
1. Nutzerin öffnet die Standort-Detailseite.
2. Nutzerin klickt erneut auf „Zone automatisch ermitteln" (ohne eine „Erzwingen"-Option zu wählen).
**Expected Results**:
- Die angezeigte Zone bleibt unverändert bei der manuell gesetzten „6b".
- Die Quelle bleibt „manuell".
**Postconditions**:
- Keine Zustandsänderung am Standort.
**Related Cases**: [TC-REQ-039-005, TC-REQ-039-016]
**Tags**: [REQ-039, standorte, state-transition]

## TC-REQ-039-007: Rand-Clamping bei extrem kaltem Klimanormal (spec-abgeleitet)
**Requirement**: REQ-039 — §3 `classify_from_minimum` „Werte unterhalb Zone 1 → 1a" / §7 Akzeptanzkriterium 3
**Priority**: Medium
**Category**: validation
**Technique**: boundary-value
**Preconditions**:
- Standort mit Klimanormalen, deren mittleres Jahres-Tiefstminimum extrem kalt ist (z. B. unterhalb der Zone-1a-Untergrenze, arktisches Klima).
**Steps**:
1. Nutzerin klickt auf „Zone automatisch ermitteln" für diesen Standort.
**Expected Results**:
- Die angezeigte Zone ist „1a" (kälteste Zone), keine Fehlermeldung, kein Absturz der Ableitung.
**Postconditions**:
- `hardiness_zone` = „1a", Quelle „automatisch".
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-008]
**Tags**: [REQ-039, standorte, boundary-value]

## TC-REQ-039-008: Rand-Clamping bei extrem warmem Klimanormal (spec-abgeleitet)
**Requirement**: REQ-039 — §3 `classify_from_minimum` „oberhalb 13 → 13b" / §7 Akzeptanzkriterium 3
**Priority**: Medium
**Category**: validation
**Technique**: boundary-value
**Preconditions**:
- Standort mit Klimanormalen, deren mittleres Jahres-Tiefstminimum extrem warm ist (z. B. tropisches Klima, oberhalb der Zone-13b-Obergrenze).
**Steps**:
1. Nutzerin klickt auf „Zone automatisch ermitteln" für diesen Standort.
**Expected Results**:
- Die angezeigte Zone ist „13b" (wärmste Zone), keine Fehlermeldung.
**Postconditions**:
- `hardiness_zone` = „13b", Quelle „automatisch".
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-007]
**Tags**: [REQ-039, standorte, boundary-value]

## TC-REQ-039-009: Zonen-Chip zeigt Zone und Temperaturklasse im Tooltip (spec-abgeleitet — `HardinessZoneBadge`-Komponente im Code nicht auffindbar)
**Requirement**: REQ-039 — §4 Frontend-Integration `HardinessZoneBadge`
**Priority**: Medium
**Category**: happy-path
**Technique**: visual-feedback
**Preconditions**:
- Standort mit aufgelöster Winterhärtezone (z. B. „7a").
**Steps**:
1. Nutzerin öffnet die Standort-Detailseite (oder eine Pflanzen-Karte am selben Standort).
2. Nutzerin bewegt den Mauszeiger über den Zonen-Chip „7a".
**Expected Results**:
- Der Chip zeigt den Zonenwert „7a" prominent an.
- Der Tooltip zeigt die deutsche Temperaturklassen-Beschreibung (z. B. „Mittleres Jahresminimum −17,8 °C bis −15,0 °C").
**Postconditions**:
- Keine Zustandsänderung; rein informative Anzeige.
**Related Cases**: [TC-REQ-039-001, TC-REQ-039-010]
**Tags**: [REQ-039, standorte, visual-feedback]

## TC-REQ-039-010: Globaler Zonenkatalog liefert konsistente Referenzdaten für alle Zonen 1a–13b (spec-abgeleitet, per Chip-Tooltip beobachtbar)
**Requirement**: REQ-039 — §2 `HardinessZone`-Collection / §5 Seed-Daten / §7 Akzeptanzkriterium 1
**Priority**: Low
**Category**: happy-path
**Technique**: equivalence-partition
**Preconditions**:
- Mehrere Standorte mit unterschiedlichen, über die gesamte Bandbreite (kalt bis warm) verteilten Winterhärtezonen sind angelegt.
**Steps**:
1. Nutzerin ruft für einen Standort in einer kalten Zone (z. B. „6a") den Zonen-Chip-Tooltip auf.
2. Nutzerin ruft für einen Standort in einer warmen DACH-Zone (z. B. „8b") den Zonen-Chip-Tooltip auf.
**Expected Results**:
- Beide Tooltips zeigen jeweils plausible, unterschiedliche deutsche Temperaturklassen-Beschreibungen passend zur jeweiligen Zone.
- Keine Zone zeigt eine leere oder fehlerhafte Beschreibung an.
**Postconditions**:
- Keine Zustandsänderung.
**Related Cases**: [TC-REQ-039-009]
**Tags**: [REQ-039, standorte, equivalence-partition]

## TC-REQ-039-011: Inline-Warnung im Pflanzen-Anlage-Dialog bei nicht winterharter Art (spec-abgeleitet — im Code nicht auffindbar)
**Requirement**: REQ-039 — §4 Frontend-Integration „Pflanzen-Anlage-Dialog: Inline-Warnung"
**Priority**: Critical
**Category**: validation
**Technique**: error-guessing
**Preconditions**:
- Standort mit aufgelöster Winterhärtezone „7a" existiert.
- Eine Pflanzenart mit einer Mindest-Winterhärtezone von „8a" (d. h. am Standort nicht ohne Schutz winterhart) ist im Stammdatenkatalog vorhanden.
**Steps**:
1. Nutzerin öffnet den Dialog „Pflanze anlegen" für den Standort mit Zone „7a".
2. Nutzerin wählt die mehrjährige Art mit Mindestzone „8a" aus.
**Expected Results**:
- Eine Inline-Warnung erscheint, z. B. „Diese Art ist für Zone 8a angegeben, dein Standort ist Zone 7a → ohne Winterschutz erfriert sie."
- Die Warnung verhindert das Anlegen nicht, sondern informiert nur.
**Postconditions**:
- Keine Zustandsänderung, bis die Nutzerin den Dialog bestätigt.
**Related Cases**: [TC-REQ-039-012, TC-REQ-039-017]
**Tags**: [REQ-039, pflanzen, validation]

## TC-REQ-039-012: Navigation von der Inline-Warnung zum Überwinterungsprofil (spec-abgeleitet)
**Requirement**: REQ-039 — §4 Frontend-Integration „verlinkt auf das OverwinteringProfile"
**Priority**: Medium
**Category**: navigation
**Technique**: navigation
**Preconditions**:
- Die Inline-Warnung aus TC-REQ-039-011 wird angezeigt.
**Steps**:
1. Nutzerin klickt in der Inline-Warnung auf den Link/Verweis zum Überwinterungsprofil.
**Expected Results**:
- Die Anwendung navigiert zur Überwinterungs-Ansicht der neu angelegten (oder in Anlage befindlichen) Pflanze.
**Postconditions**:
- Nutzerin befindet sich auf der Überwinterungs-Detailansicht.
**Related Cases**: [TC-REQ-039-011]
**Tags**: [REQ-039, pflanzen, navigation]

## TC-REQ-039-013: Bestandsstandort ohne GPS bleibt nach der Migration unverändert nutzbar (bildschirm-verifiziert: `climate_zone`-Feld real vorhanden)
**Requirement**: REQ-039 — §2 „Migration: Bestehendes Site.climate_zone wird als Initialwert … übernommen" / §7 Akzeptanzkriterium „bestehende Sites ohne GPS funktionieren unverändert"
**Priority**: High
**Category**: state-transition
**Technique**: equivalence-partition
**Preconditions**:
- Ein vor Einführung von REQ-039 angelegter Standort ohne GPS-Koordinaten mit manuell gepflegtem Zonentext existiert.
**Steps**:
1. Nutzerin öffnet die Detailseite dieses Bestandsstandorts.
**Expected Results**:
- Das Zonenfeld zeigt weiterhin den zuvor gepflegten Zonenwert unverändert an.
- Alle übrigen Standortfunktionen (Bewässerung, Standort-Baum, Sensoren) funktionieren normal, ohne Fehlermeldung.
**Postconditions**:
- Keine ungewollte automatische Änderung der Zone bei einem Standort ohne GPS-Koordinaten.
**Related Cases**: [TC-REQ-039-005]
**Tags**: [REQ-039, standorte, regression]

## TC-REQ-039-014: Frosttermin-Defaults werden aus den Zonen-Richtwerten vorbefüllt (spec-abgeleitet — Anzeige der Frosttermine im Standort-Formular nicht auffindbar)
**Requirement**: REQ-039 — §2 `typical_last_frost_md`/`typical_first_frost_md` / §7 Akzeptanzkriterium „Frosttermin-Defaults … werden aus den Zonen-Richtwerten vorbefüllt"
**Priority**: Medium
**Category**: happy-path
**Technique**: state-transition
**Preconditions**:
- Standort ohne bisher gesetzte Frosttermine (weder manuell noch aus Live-Wetterdaten) und ohne bisherige Winterhärtezone.
**Steps**:
1. Nutzerin klickt auf „Zone automatisch ermitteln" für den Standort.
2. Nutzerin öffnet danach den Aussaatkalender-/Frosttermin-Bereich des Standorts.
**Expected Results**:
- Die Felder „durchschnittlicher letzter Frost" und „durchschnittlicher erster Frost" zeigen die aus der ermittelten Zone abgeleiteten Richtwerte an (statt leer zu bleiben).
**Postconditions**:
- Die vorbefüllten Frosttermine bleiben bestehen, bis der Nutzer sie manuell überschreibt oder eine Wetter-API-Anbindung eigene Werte liefert.
**Related Cases**: [TC-REQ-039-001]
**Tags**: [REQ-039, standorte, happy-path]

## TC-REQ-039-015: Winterhart eingestufte Pflanze zeigt „kein Schutz nötig"-Hinweis ohne Überwinterungsprofil (bildschirm-verifiziert: `OverwinteringSection.tsx` „emptyHint")
**Requirement**: REQ-039 — §3 `evaluate_winter_hardiness` grün-Fall (`hardy` UND `delta > 0`) / §7 Akzeptanzkriterium „für hardy-Arten werden weiterhin keine Winterschutz-Erinnerungen generiert"
**Priority**: High
**Category**: state-transition
**Technique**: boundary-value
**Preconditions**:
- Pflanzeninstanz einer winterharten Art an einem Standort, dessen Winterhärtezone strikt wärmer ist als die Mindestzone der Art (Standortzone > Art-Mindestzone), auf einer freilandfähigen Fläche.
**Steps**:
1. Nutzerin öffnet die Detailseite dieser Pflanzeninstanz.
2. Nutzerin betrachtet den Überwinterungs-Abschnitt der Seite.
**Expected Results**:
- Der Abschnitt zeigt einen Hinweistext, dass für diese Pflanze kein Winterschutz nötig ist.
- Es wird kein Überwinterungsprofil und keine Winterschutz-Erinnerung erzeugt.
**Postconditions**:
- Keine Aufgaben/Erinnerungen zum Winterschutz für diese Pflanze.
**Related Cases**: [TC-REQ-039-016, TC-REQ-039-017]
**Tags**: [REQ-039, pflanzen, boundary-value]

## TC-REQ-039-016: Ampel-Grenzfall bei Zonengleichheit erzeugt In-situ-Schutzplan (Pfad A) (bildschirm-verifiziert: `OverwinteringSection.tsx` Pfad-Chip)
**Requirement**: REQ-039 — §3 `evaluate_winter_hardiness` gelb-Fall (Zonengleichheit `delta == 0`) / §7 Akzeptanzkriterium „bei Zonengleichheit … yellow" / Versionshistorie 1.3
**Priority**: Critical
**Category**: state-transition
**Technique**: boundary-value
**Preconditions**:
- Pflanzeninstanz einer Art, deren Mindestzone exakt der Standortzone entspricht (Zonengleichheit), mit bereits automatisch materialisiertem Überwinterungsprofil (Herbst-Übergang, REQ-047).
**Steps**:
1. Nutzerin öffnet die Detailseite dieser Pflanzeninstanz.
2. Nutzerin betrachtet den Überwinterungs-Abschnitt.
**Expected Results**:
- Ein automatisch generiertes Profil wird angezeigt.
- Der Winterpfad-Chip zeigt Pfad „A" (in-situ/Freiland-Schutz, z. B. Vlies/Mulch) in der für den Warnzustand vorgesehenen Farbe an.
**Postconditions**:
- Die Pflanze verbleibt am Standort mit Winterschutzmaßnahme statt Umzug.
**Related Cases**: [TC-REQ-039-015, TC-REQ-039-017]
**Tags**: [REQ-039, pflanzen, boundary-value]

## TC-REQ-039-017: Standort mehr als eine Zone zu kalt erzeugt Verlagerungs-Schutzplan (Pfad B) (bildschirm-verifiziert: `OverwinteringSection.tsx` Pfad-Chip)
**Requirement**: REQ-039 — §3 `evaluate_winter_hardiness` rot-Fall (`delta < -1` oder `tender`) / §7 Akzeptanzkriterium „(Art mind. Zone 8a, Standort 7a, tender) → red"
**Priority**: Critical
**Category**: state-transition
**Technique**: boundary-value
**Preconditions**:
- Pflanzeninstanz einer frostempfindlichen Art, deren Mindestzone mehr als eine volle Zone über der Standortzone liegt, mit bereits automatisch materialisiertem Überwinterungsprofil.
**Steps**:
1. Nutzerin öffnet die Detailseite dieser Pflanzeninstanz.
2. Nutzerin betrachtet den Überwinterungs-Abschnitt.
**Expected Results**:
- Der Winterpfad-Chip zeigt Pfad „B" (Verlagerung, z. B. „ins Haus/Lager") in der für den kritischen Zustand vorgesehenen Farbe an.
**Postconditions**:
- Die Pflanze wird gemäß Profil ins Winterquartier verlagert statt im Freiland zu verbleiben.
**Related Cases**: [TC-REQ-039-015, TC-REQ-039-016, TC-REQ-039-011]
**Tags**: [REQ-039, pflanzen, boundary-value]

---

## Abdeckungs-Tabelle

| Abschnitt der Spezifikation | Abgedeckt durch |
|---|---|
| §1 Business Case / User Stories (automatische Ableitung, Standort-Pflanze-Abgleich, Ampel-Automatisierung, Frost-Basisdaten) | TC-001, TC-004, TC-011, TC-014, TC-015–017 |
| §2 Datenmodell — `HardinessZone`-Collection (Referenzdaten) | TC-009, TC-010 |
| §2 Datenmodell — `Site`-Erweiterung (`hardiness_zone`, `hardiness_zone_source`, `postal_code`, Migration) | TC-005, TC-006, TC-013 |
| §2 Datenmodell — `located_in_zone`-Kante | offen (siehe unten) |
| §3 `HardinessZoneResolver.classify_from_minimum` (Rand-Clamping) | TC-007, TC-008 |
| §3 `HardinessZoneResolver.derive_from_climate_normals` (GPS/PLZ-Ableitung) | TC-001, TC-003, TC-004 |
| §3 `evaluate_winter_hardiness` (Ampel-Grenzfälle grün/gelb/rot) | TC-015, TC-016, TC-017 |
| §3 `FrostlineUsAdapter` (US-Schnellpfad) | offen (siehe unten) |
| §3 `HardinessZoneService.resolve_for_site` (force-Override, Frosttermin-Vorbefüllung) | TC-006, TC-014 |
| §3 Celery-Task `refresh_site_hardiness_zones` (quartalsweise, respektiert manuelle Zone) | TC-006 (Beobachtung des Ergebnisses; Auslösung selbst ist kein Nutzer-Vorgang) |
| §4 Frontend-Integration (Button, Badge, Ampel-Begründungstext, Inline-Warnung, i18n) | TC-002, TC-009, TC-011, TC-012 |
| §5 Konfiguration/Deployment/Lizenz | offen (siehe unten) |
| §7 Akzeptanzkriterien | über die obigen Fälle verteilt abgedeckt |

## Offene Anforderungsabschnitte (kein Testfall ableitbar)

- **§2 `located_in_zone`-Kante**: reine Graph-Persistenzstruktur ohne eigenständig beobachtbares Nutzer-Verhalten (wird indirekt über TC-001/TC-005 mitprüfbar, aber nicht separat aus Nutzersicht beobachtbar).
- **§3 `FrostlineUsAdapter` (US-ZIP-Schnellpfad)**: Adapter ist laut Spezifikation optional und im aktuellen Code nicht implementiert (kein `FrostlineUsAdapter` auffindbar) — kein beobachtbares Verhalten ableitbar, bis der Adapter existiert.
- **§3 Celery-Task `seed_hardiness_zones`**: einmaliger Migrations-/Seed-Vorgang ohne Nutzerinteraktion; nicht aus Anwendersicht beobachtbar (nur indirekt über TC-009/TC-010 prüfbar, dass Referenzdaten vorhanden sind).
- **§5 Konfiguration (Umgebungsvariablen `HARDINESS_NORMAL_PERIOD_START/END`, `HARDINESS_SOURCE_PRIORITY`, `FROSTLINE_API_BASE_URL`)**: Deployment-/Konfigurationsdetails ohne UI-Repräsentation.
- **§5 Lizenz-Compliance (MIT-Hinweis, DWD-/Open-Meteo-Attribution in `THIRD_PARTY_LICENSES`/NOTICE)**: Dokumentations-/Compliance-Anforderung, kein Anwendungsverhalten.
- **§6 Abhängigkeiten (reine Verweistabelle)**: kein eigenständiges Verhalten, wird über die abhängigen Anforderungen (REQ-003, REQ-022, REQ-005, REQ-046, REQ-015-A) getestet, nicht hier.
