# Feature-Request: FR-001 — Modulare Feature-Sichtbarkeit

```yaml
ID: FR-001
Titel: Persönliche Modul- und Feature-Sichtbarkeit (Nutzer blendet uninteressante Bereiche aus)
Typ: Feature-Request
Status: Vorgeschlagen
Eingereicht: 2026-06-20
Betroffene Zielgruppen: Casual Houseplant User, Zierpflanzen-Sammler, fokussierte Profis
Verwandte Anforderungen: REQ-021 (UI-Erfahrungsstufen), REQ-020 (Onboarding/UserPreference), REQ-009 (Dashboard), REQ-027 (Light-Modus)
Resultierende Spezifikation: REQ-042 (../req/REQ-042_Modulare-Feature-Sichtbarkeit.md)
GitHub-Issue: https://github.com/nolte/kamerplanter/issues/243
```

## Problem / Motivation

Kamerplanter bietet mit **REQ-021** bereits drei Erfahrungsstufen (Einsteiger / Fortgeschritten / Experte), die die Oberfläche je nach Kenntnisstand vereinfachen. Diese Abstufung ist aber **eindimensional** und bündelt ganze Funktionsbereiche fest an eine Stufe.

Das Interesse an Funktionsbereichen hängt jedoch **nicht** zwangsläufig von der Erfahrung ab:

- Ein botanisch versierter **Zimmerpflanzen-Liebhaber** beherrscht die App sicher, **düngt und erntet aber nie**. Module wie **Tankmanagement** oder **Erntechargen** sind für ihn dauerhaft irrelevant — aktuell muss er sie trotzdem im Experten-Modus mitschleppen.
- Ein **Einsteiger** interessiert sich gezielt für **Pflanzenschutz**, möchte aber nicht die gesamte Oberfläche auf „Experte" umstellen, nur um dieses eine Modul zu sehen.
- Ein **fokussierter Profi** nutzt bewusst nur einen Teil der Module und empfindet den vollen Experten-Umfang als unübersichtlich.

Kurz: Die Erfahrungsstufe beantwortet „**wie viel Detailtiefe**", nicht „**welche Funktionsbereiche interessieren mich überhaupt**". Diese zweite, persönliche Dimension fehlt.

> Der konkrete Auslöser aus der Praxis: „Nicht jeder Nutzer hat Interesse an der Tank-Pflege oder an Ernte-Chargen."

## Vorschlag

Eine **feingranulare, persönliche Modul-Auswahl** als **Ergänzung** zu den Erfahrungsstufen. In den Einstellungen kann der Nutzer einzelne Funktionsbereiche (Module) gezielt **ein- oder ausblenden** — unabhängig von, aber aufbauend auf seiner Erfahrungsstufe.

Leitprinzipien (konsistent mit REQ-021):

1. **Reine Darstellungspräferenz** — keine Zugriffskontrolle, keine Datenlöschung. Das Backend liefert weiterhin alle Daten; nur die Anzeige wird gefiltert.
2. **Tri-State statt simpler An/Aus-Liste** — jedes Modul ist entweder „folgt Erfahrungsstufe" (Standard), „immer einblenden" oder „immer ausblenden". Gespeichert werden nur die bewussten Übersteuerungen, damit ein späterer Stufenwechsel weiterhin auf alle nicht angefassten Module wirkt.
3. **Kern-Module sind geschützt** — Dashboard, Meine Pflanzen, Standorte, Einstellungen und Onboarding lassen sich nie ausblenden.
4. **Konsistenter Wirkungsbereich** — eine Ausblendung entfernt Navigationspunkte, Dashboard-Widgets und Quick-Actions des Moduls gemeinsam.
5. **Nichts geht verloren** — ausgeblendete Module behalten ihre Daten; per URL aufgerufene Seiten zeigen einen Reaktivierungs-Hinweis statt eines Fehlers.

## Nutzersicht (User Stories)

- *„Als Zimmerpflanzen-Liebhaber möchte ich Tankmanagement und Erntechargen komplett ausblenden, damit meine Oberfläche aufgeräumt bleibt."*
- *„Als erfahrener Grower möchte ich gezielt nur die Module sehen, die ich wirklich nutze — statt im Experten-Modus alles."*
- *„Als Einsteiger möchte ich genau das Modul Pflanzenschutz zusätzlich einblenden, ohne meinen gesamten Modus zu wechseln."*
- *„Als Nutzer möchte ich ein ausgeblendetes Modul jederzeit wieder aktivieren, ohne dass meine Daten weg sind."*

## Erwarteter Nutzen

- **Aufgeräumtere Oberfläche** für die breite Masse (Casual User) → weniger Überforderung, höhere Bindung.
- **Personalisierung jenseits der Erfahrungsstufe** → die App passt sich dem *Interesse*, nicht nur dem *Kenntnisstand* an.
- **Geringe technische Komplexität** — baut auf der vorhandenen Erfahrungsstufen-Mechanik (REQ-021) und der `UserPreference`-API (REQ-020) auf; im Kern ein additives Präferenzfeld plus Frontend-Filter.

## Abgrenzung (was dieser Request NICHT ist)

- **Keine Rechteverwaltung** — das ist Sache von REQ-024 (Mandanten/RBAC). Ausgeblendet ≠ gesperrt.
- **Kein Ersatz für REQ-021** — die Erfahrungsstufen bleiben; dieser Request ergänzt sie um eine zweite, persönliche Achse.
- **Keine Backend-Funktionseinschränkung** — alle APIs bleiben unverändert nutzbar.

## Beispiel-Module zum Ein-/Ausblenden

Tankmanagement, Erntechargen/Ernte, Pflanzenschutz (IPM), Düngung & Nährstoffpläne, Substrate, Kalkulatoren, Pflanzdurchläufe, Vermehrung, Mischkultur & Fruchtfolge, Sensorik, Umgebungssteuerung/Aktorik, Smart-Home, KI-Funktionen. (Vollständiger Katalog: REQ-042 § 1.3.)

## Umsetzung

Die vollständige technische Spezifikation liegt in **[REQ-042 — Modulare Feature-Sichtbarkeit](../req/REQ-042_Modulare-Feature-Sichtbarkeit.md)** (Datenmodell, API, Frontend-Hooks, Einstellungs-Tab, Akzeptanzkriterien).
