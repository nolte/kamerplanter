# CanG-konforme Dokumentation für Anbauvereinigungen

Betreibst du Kamerplanter für eine **Anbauvereinigung** (Cannabis Social Club) nach dem deutschen Cannabis-Gesetz (CanG), musst du den Anbau lückenlos dokumentieren, Rollen zwischen Vorstand, Anbauverantwortlichen und Mitgliedern trennen und gesetzliche Aufbewahrungsfristen einhalten. Diese Seite erfindet dafür keine neuen Funktionen, sondern zeigt, wie du bereits vorhandene Kamerplanter-Bausteine — Mandanten, Pflanzdurchläufe, Erntechargen, Karenzzeit-Sperre und Aufbewahrungsfristen — für diesen Zweck kombinierst.

!!! warning "Keine Rechtsberatung"
    Diese Seite beschreibt, welche Dokumentationsfunktionen Kamerplanter dir bietet — sie ersetzt keine rechtliche Beratung durch eine Anwältin, einen Steuerberater oder die zuständige Behörde. Ob deine Vereinsstruktur und Dokumentation den Anforderungen des Cannabis-Gesetzes und des Pflanzenschutzgesetzes (PflSchG) im Einzelfall genügen, kläre mit fachkundiger Stelle.

---

## Überblick: Was diese Seite verkettet

| Anforderung | Zuständige Kamerplanter-Funktion | Seite(n) |
|-------------|-----------------------------------|----------|
| Verein als eigener, isolierter Bereich | Mandant (Tenant) vom Typ „Organisation" | [Mandanten & Gärten](../user-guide/tenants.md) |
| Chargen-Rückverfolgbarkeit | Pflanzdurchlauf + Erntecharge | [Pflanzdurchläufe](../user-guide/planting-runs.md), [Erntemanagement](../user-guide/harvest.md) |
| Karenzzeit-Einhaltung | Automatische Karenzzeit-Sperre bei der Ernte | [Integrierter Pflanzenschutz (IPM)](../user-guide/pest-management.md) |
| Aufbewahrungsfristen | Retention-Matrix nach CanG/PflSchG | [Datenaufbewahrung & Anonymisierung](data-retention.md) |
| Rollen-Trennung im Verein | Admin / Gärtner / Beobachter + Standort-Zuweisung | [Mandanten & Gärten](../user-guide/tenants.md) |
| Zentrale Mitglieder-Anmeldung | OIDC-Auto-Join über den Vereins-Identity-Provider | [Mandanten & Gärten](../user-guide/tenants.md), [Konto & Anmeldung](../user-guide/account.md) |

---

## 1. Den Verein als Mandanten einrichten

Lege für deine Anbauvereinigung einen eigenen [Mandanten (Tenant)](../user-guide/tenants.md) vom Typ **Organisation** an. Alle Ressourcen des Vereins — Standorte, Pflanzdurchläufe, Ernten, Behandlungen — sind dann vollständig von den persönlichen Mandanten deiner Mitglieder isoliert: Kein Mitglied sieht die privaten Zimmerpflanzen eines anderen, und niemand außerhalb des Vereins sieht Vereinsdaten.

Bilde deine Anbauräume (Vegetations-Raum, Blüte-Raum, Trocknungsraum) als eigene Standorte innerhalb dieses Mandanten ab — siehe [Standorte & Substrate](../user-guide/locations-substrates.md).

## 2. Chargen anlegen und rückverfolgbar dokumentieren

Jeder Anbaudurchgang beginnt als [Pflanzdurchlauf](../user-guide/planting-runs.md): Du gruppierst die Pflanzen eines Raums (z. B. „Blüte-Raum 1, Zyklus 2026-03"), dokumentierst Sorte, Startdatum und — bei Klonen — die Quellpflanze. Damit ist die erste Hälfte der Rückverfolgbarkeit (Samen/Steckling → Pflanze) bereits durch die normale Nutzung von Kamerplanter abgedeckt.

Für die Ernte legst du pro Pflanze eine **Erntecharge** an (Menü **Ernte**) mit Erntetyp, Erntedatum, Nassgewicht und optional einer eigenen **Chargen-ID** (z. B. „ERNTE-2026-BLÜTE1-003") — Details in [Erntemanagement](../user-guide/harvest.md#erntecharge-erstellen).

!!! note "Chargen-ID ist ein freies Textfeld, keine automatische Vereins-Chargennummer"
    Kamerplanter vergibt die Chargen-ID nicht automatisch fortlaufend über den ganzen Verein hinweg — das Feld ist eine optionale, frei eintragbare Kennung pro Erntecharge. Lege dir für eine konsistente Vereins-Chargennummerierung ein eigenes Namensschema fest (z. B. Raum-Kürzel + Jahr + laufende Nummer) und trage es bei jeder Ernte manuell ein.

Die Qualitätsbewertung (Erscheinung, Aroma, Farbe, Mängel, Gesamt-Score) trägst du anschließend im Tab **Qualität** derselben Erntecharge nach — auch das ist Teil der Rückverfolgbarkeitskette.

## 3. Karenzzeiten und Behandlungsnachweise

Jede Pflanzenschutzbehandlung mit ihrer Karenzzeit (Pre-Harvest Interval) legst du unter [Integrierter Pflanzenschutz (IPM)](../user-guide/pest-management.md) als Stammdatum für ein Behandlungsmittel an. Sobald für eine Pflanze eine Anwendung dieses Mittels dokumentiert ist, sperrt Kamerplanter automatisch die Erstellung einer Erntecharge, solange die Karenzzeit noch läuft. Das gilt unabhängig davon, ob ein Vorstandsmitglied oder ein Anbauverantwortlicher die Ernte auslöst. Damit verhindert Kamerplanter technisch genau die versehentliche Ernte innerhalb der Wartezeit nach dem Pflanzenschutzgesetz (PflSchG).

!!! info "Behandlungsanwendung an einer Pflanze aktuell nur über die API dokumentierbar"
    Das konkrete Erfassen einer Behandlungsanwendung (welches Mittel, wann, an welcher Pflanze) gibt es in der Oberfläche noch nicht — dafür steht bereits ein API-Endpunkt bereit (siehe [Für technische Nutzer: API-Zugriff](../user-guide/pest-management.md#fur-technische-nutzer-api-zugriff)). Bis die Oberfläche nachgezogen ist, braucht dein Verein entweder eine technisch versierte Person, die den Eintrag über die API anlegt, oder ihr dokumentiert Anwendungen zusätzlich in einem eigenen Protokoll außerhalb von Kamerplanter, bis die Karenzzeit-Sperre technisch greift.

## 4. Aufbewahrungsfristen einhalten

Erntedaten, Behandlungsanwendungen und Inspektionsprotokolle unterliegen in Kamerplanter gesetzlichen Mindestaufbewahrungsfristen, die sich **nicht** unterschreiten lassen:

| Datenkategorie | Mindestfrist | Rechtsgrundlage |
|----------------|-------------|-----------------|
| Erntedaten (Erntecharge, Qualitätsbewertung, Ertragskennzahlen) | 5 Jahre | Cannabis-Gesetz (CanG) |
| Behandlungsanwendungen | 3 Jahre | Pflanzenschutzgesetz (PflSchG) §11 |
| Inspektionsprotokolle | 3 Jahre | Pflanzenschutzgesetz (PflSchG) §11 |

Stellt ein Vereinsmitglied eine Löschanfrage nach Artikel 17 DSGVO, löscht Kamerplanter diese Datensätze **nicht**. Stattdessen entfernt Kamerplanter nur den Bezug zur Person (`user_key` wird geleert) — der Ernte- oder Behandlungsdatensatz selbst bleibt bis zum Ablauf der gesetzlichen Frist bestehen. Details zur vollständigen Retention-Matrix und den zugehörigen Umgebungsvariablen findest du unter [Datenaufbewahrung & Anonymisierung](data-retention.md#gesetzliche-mindestaufbewahrungsfristen).

## 5. Rollen zwischen Mitgliedern trennen

Kamerplanter unterscheidet pro Mandant drei Rollen — Admin, Gärtner, Beobachter (siehe [Mandanten & Gärten](../user-guide/tenants.md#rollen-und-berechtigungen)). Für eine Anbauvereinigung bietet sich folgende Zuordnung an:

| Vereinsfunktion | Kamerplanter-Rolle | Begründung |
|-----------------|---------------------|-----------|
| Vorstand / Vereinsleitung | Admin | Vollzugriff, Mitglieder-Einladung, Rollenverwaltung |
| Anbauverantwortliche (Head-Grower) | Gärtner, mit Standort-Zuweisung auf ihren Raum | Kann Pflanzen, Aufgaben und Ernten in ihrem Raum bearbeiten |
| Kassenwart, Prüfer, Aufsichtsperson | Beobachter | Vollständiger Lesezugriff auf alle Daten, aber keine Änderungen |

Über das [Standort-basierte Schreibrecht](../user-guide/tenants.md#standort-basierte-schreibrechte) weist du einem Anbauverantwortlichen genau seinen Anbauraum zu — Mitglieder anderer Räume können diesen dann nicht versehentlich mitbearbeiten, solange sie nicht selbst Admin sind.

## 6. Zentrale Mitglieder-Anmeldung per Single Sign-On (OIDC)

Betreibt euer Verein bereits ein eigenes Mitgliederverzeichnis (z. B. über Keycloak oder einen anderen OpenID-Connect-Anbieter), kann eure Plattform-Administration diesen als zusätzlichen Anmeldeanbieter einrichten — Mitglieder melden sich dann über den vereinseigenen Provider an, wie in [Konto & Anmeldung](../user-guide/account.md#mit-google-github-oder-einem-anderen-anbieter-anmelden) beschrieben. Ergänzend lässt sich der **OIDC-Auto-Join** konfigurieren, damit neue Mitglieder beim ersten Login automatisch eurem Vereins-Mandanten beitreten, statt manuell eingeladen werden zu müssen — siehe [Mandanten & Gärten — Methode 3: OIDC Auto-Join](../user-guide/tenants.md#mitglieder-einladen).

!!! info "Einrichtung durch die Plattform-Administration"
    Die OIDC-Anbindung eines eigenen Identity-Providers richtet nicht der Vereinsvorstand selbst ein, sondern die technische Administration eurer Kamerplanter-Instanz (Self-Hoster bzw. Betreiber).

---

## Grenzen der aktuellen Umsetzung

Damit du nicht auf Funktionen planst, die es noch nicht gibt: Die folgenden, für Anbauvereinigungen typischen Anforderungen sind aktuell **nicht** vorhanden.

!!! note "Kein dedizierter Behörden-Export"
    Einen fertigen PDF- oder CSV-Export speziell für Behördenkontrollen (Ernte-Protokoll, Behandlungsnachweis, Zeitraum-Zusammenfassung in einem Dokument) gibt es noch nicht. Bei einer Kontrolle exportierst du derzeit den Nährstoffplan als PDF (siehe [Druckansichten & Export](../user-guide/print-export.md)) und stellst Ernte- sowie Behandlungsdaten manuell aus der tabellarischen Erntechargen-Übersicht bzw. über die API zusammen.

!!! note "Kein Abgabe-Protokoll"
    Eine Dokumentation, welches Mitglied wann welche Menge aus dem Verein erhalten hat, ist in Kamerplanter aktuell nicht abgebildet. Du brauchst dafür vorerst ein separates Protokoll außerhalb des Systems.

!!! note "Keine revisionssichere Sperre für nachträgliche Korrekturen"
    Eine Erntecharge selbst kann nach dem Anlegen nicht gelöscht werden — Notizen und Gewichtswerte lassen sich aber jederzeit nachträglich bearbeiten, ohne dass Kamerplanter eine Änderungshistorie dieser Korrekturen protokolliert. Führt euer Verein ein revisionssicheres (unveränderliches) Protokoll als Compliance-Anforderung, ergänzt diese Angaben zusätzlich in einem eigenen, unveränderlichen Ablagesystem.

---

## Häufige Fragen

??? question "Reicht Kamerplanter allein aus, um alle CanG-Dokumentationspflichten zu erfüllen?"
    Kamerplanter deckt die zentralen Bausteine ab — Chargen-Rückverfolgbarkeit, Karenzzeit-Sperre, Aufbewahrungsfristen, Rollen-Trennung. Für vollständige Behörden-Reports und Abgabe-Protokolle braucht ihr aktuell noch ergänzende, manuelle Dokumentation außerhalb des Systems (siehe [Grenzen der aktuellen Umsetzung](#grenzen-der-aktuellen-umsetzung)).

??? question "Können wir mehrere Anbauräume mit unterschiedlichen Anbauverantwortlichen abbilden?"
    Ja. Bildet jeden Raum als eigenen Standort ab und weist ihn über die Standort-Zuweisung dem jeweils verantwortlichen Mitglied zu — siehe Schritt 5 oben.

??? question "Was passiert, wenn ein Mitglied den Verein verlässt?"
    Solange das Mitglied nicht der einzige Admin ist, kann es den Mandanten jederzeit verlassen. Von ihm dokumentierte Ernte- und Behandlungsdaten bleiben im Verein erhalten, da sie dem Mandanten und nicht der Person gehören.

---

## Siehe auch

- [Mandanten & Gärten](../user-guide/tenants.md)
- [Pflanzdurchläufe](../user-guide/planting-runs.md)
- [Erntemanagement](../user-guide/harvest.md)
- [Integrierter Pflanzenschutz (IPM)](../user-guide/pest-management.md)
- [Datenaufbewahrung & Anonymisierung](data-retention.md)
- [Konto & Anmeldung](../user-guide/account.md)
- [Datenschutz & DSGVO](../user-guide/privacy.md)
- [Cannabis-Grow-Zyklus: von der Keimung bis zum Cure](journey-cannabis-cycle.md)
