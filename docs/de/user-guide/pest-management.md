# Integrierter Pflanzenschutz (IPM)

Das IPM-System (Integriertes Pflanzenschutzmanagement, IPM) verfolgt einen dreistufigen Ansatz: Prävention vor Monitoring, Monitoring vor Intervention. Kamerplanter protokolliert Befallskontrollen, verwaltet Behandlungen mit Karenzzeiten und warnt dich rechtzeitig vor dem Erntetermin.

---

## Voraussetzungen

- Mindestens eine angelegte Pflanze oder ein aktiver Pflanzdurchlauf
- Für Karenzzeit-Überwachung: Behandlungen mit angegebenen Mitteln und Ausbringungsdatum

---

## Das IPM-Dreistufenmodell

### Stufe 1: Prävention

Die beste Pflanzenschutzmaßnahme ist die, die du nicht brauchst. Kamerplanter unterstützt präventive Maßnahmen durch:

- **Standort-Hygiene-Aufgaben** (automatisch generiert): Reinigung des Growbereichs, Desinfektion von Werkzeug
- **Fruchtfolge-Warnungen**: Hinweise, wenn die gleiche Pflanzenfamilie zu schnell am selben Standort folgt
- **Klimaüberwachung**: Hinweis bei dauerhaft hoher Luftfeuchte (> 70 % rH), die Schimmelpilze begünstigt

!!! tip "Prävention lohnt sich"
    Schädlinge und Krankheiten, die frühzeitig erkannt werden, lassen sich mit biologischen Mitteln behandeln. Wer zu spät handelt, ist oft auf chemische Mittel angewiesen, die Karenzzeiten von Wochen auslösen.

### Stufe 2: Monitoring (Befallskontrollen)

Regelmäßige Inspektionen sind das wichtigste Werkzeug zur Früherkennung. Kamerplanter hilft bei der Planung und Dokumentation.

### Stufe 3: Intervention

Wenn ein Befall festgestellt wurde, wähle die passende Behandlung. Kamerplanter überwacht die Karenzzeit und blockiert bei Bedarf die Ernte.

---

## Befallskontrolle (Inspektion) durchführen

In der Oberfläche entsteht eine Inspektion (Befallskontrolle) ausschließlich über die Foto-Erkennung: Öffne die betroffene Pflanze und klicke auf **Auf Schädlinge prüfen** — das öffnet den [Foto-Erkennungs-Dialog](pest-detection.md). Legt die Erkennung einen Befall nahe, bietet der Dialog den Schritt **Inspektion anlegen**: Der erkannte Schädling, das Foto und eine aus der Erkennungs-Konfidenz abgeleitete Befallsstärke werden automatisch übernommen.

### Befallsstärke-Stufen

Jede Inspektion wird einer von fünf Stufen zugeordnet:

| Stufe | Beschreibung |
|-------|-------------|
| Kein Befall | Keine Anzeichen von Schädlingen oder Krankheiten |
| Niedrig | Vereinzelte Anzeichen, keine Ausbreitung |
| Mittel | Sichtbarer Befall, lokale Ausbreitung |
| Hoch | Starker Befall, weitreichende Ausbreitung |
| Kritisch | Akute Pflanzenschädigung, sofortige Maßnahmen nötig |

### Häufige Schädlinge und Krankheiten

Klicke auf den Namen eines Schädlings, um die [Schädlings-Detailseite](pest-detail.md) mit Steckbrief, Referenzbildern und Gegenmaßnahmen aufzurufen.

**Häufige Schädlinge:**
- Spinnmilben (Tetranychus urticae)
- Blattläuse (Aphididae)
- Thripse (Thysanoptera)
- Trauermücken (Sciaridae) — besonders bei Coco und Erde
- Weiße Fliegen (Aleyrodidae)

**Häufige Krankheiten:**
- Echter Mehltau (verschiedene Spezies)
- Botrytis cinerea (Grauschimmel) — Pilzerkrankung, befällt vor allem bei hoher Luftfeuchte Blüten und Stängel
- Pythium spp. (Wurzelfäule) — Schlauchpilz, besonders in Hydroponik-Systemen mit zu wenig Sauerstoff im Wasser
- Fusarium oxysporum (Fusarium-Welke) — Bodenpilz, verursacht Welkesymptome durch Verstopfen der Leitgefäße

!!! info "Manuelle Inspektion ohne Foto — nur über API"
    Eine Oberfläche zum manuellen Anlegen einer Inspektion ohne Foto (freie Auswahl von Schädling, Befallsstärke und Notizen) gibt es aktuell nicht. Gespeicherte Inspektionen sind bislang auch nicht in einer eigenen Verlaufsansicht in der Oberfläche einsehbar. Beide Funktionen stehen bereits über die API zur Verfügung (siehe [Für technische Nutzer: API-Zugriff](#fur-technische-nutzer-api-zugriff)).

---

## Behandlungsmittel verwalten (Stammdaten)

Behandlungsmittel (Präparate/Methoden) sind Stammdaten, die für alle Pflanzen wiederverwendbar sind:

1. Navigiere zu **Pflanzenschutz (IPM) → Behandlungen**.
2. Klicke auf **Behandlung hinzufügen**.

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Mittel / Präparat | Name des Mittels | "Neem-Öl 2 %", "Spidex (Phytoseiulus persimilis — Raubmilbe)" |
| Typ | Kulturell, Biologisch, Chemisch, Mechanisch | Biologisch |
| Wirkstoff | Aktiver Bestandteil | "Azadirachtin" |
| Karenzzeit (Tage) | Wartezeit bis zur Ernte | 14 |
| Dosierung | Menge und Konzentration | "5 ml/L" |
| Ausbringungsmethode | Sprühen, Gießen, Streuen, Freisetzung | Sprühen |
| Schutzausrüstung | Empfohlene Schutzmaßnahmen | Handschuhe, Atemschutz |

Klicke auf den Namen einer Behandlung, um die [Behandlungs-Detailseite](treatment-detail.md) mit Wirkweise, Dosierung, Karenzzeit und Sicherheitshinweisen aufzurufen.

!!! info "Behandlung an einer Pflanze dokumentieren — nur über API"
    Eine konkrete Anwendung eines Behandlungsmittels an einer Pflanze (Ausbringungsdatum, Dosierung, betroffene Pflanze) lässt sich in der Oberfläche noch nicht erfassen. Der entsprechende API-Endpunkt ist bereits nutzbar (siehe [Für technische Nutzer: API-Zugriff](#fur-technische-nutzer-api-zugriff)). Sobald ein Eintrag über die API angelegt wurde, greift die Karenzzeit-Sperre bei der Ernte automatisch (siehe unten).

---

## Karenzzeit verstehen und überwachen

Die **Karenzzeit** (auch Pre-Harvest Interval, PHI) ist die gesetzlich vorgeschriebene Wartezeit zwischen der letzten Anwendung eines Pflanzenschutzmittels und der Ernte. Diese Wartezeit schützt Verbraucher vor Rückständen im Erntegut.

**Wo siehst du eine laufende Karenzzeit?**

Es gibt aktuell keine eigene Anzeige laufender Karenzzeiten in der Pflanzenansicht. Die Karenzzeit wirkt dort, wo es zählt: Versuchst du, für eine Pflanze mit noch nicht abgelaufener Karenzzeit eine **Erntecharge** anzulegen, blockiert das System die Ernte mit einer Fehlermeldung und nennt das frühestmögliche Erntedatum (Karenzzeit-Sperre, HTTP 422). Den aktuellen Stand kannst du zusätzlich per API abfragen (siehe [Für technische Nutzer: API-Zugriff](#fur-technische-nutzer-api-zugriff)).

!!! danger "Karenzzeit läuft sofort"
    Sobald eine Behandlung mit Karenzzeit für eine Pflanze erfasst wurde, ist die Ernte der betroffenen Pflanze gesperrt, bis die Karenzzeit abgelaufen ist — unabhängig davon, ob der Eintrag über die API oder (künftig) über eine Oberfläche angelegt wurde.

**Fehlerhafte Karenzzeit-Angabe — was tun?**

Es gibt derzeit keine Bearbeitungsfunktion für bereits erfasste Behandlungsanwendungen. Wende dich bei einer irrtümlichen Eintragung an dein Betreiber-/Support-Team, um den Eintrag korrigieren zu lassen.

---

## Resistenzmanagement

!!! warning "Wirkstoff-Rotation beachten"
    Schädlinge entwickeln Resistenzen, wenn dieselbe Wirkstoffgruppe zu oft eingesetzt wird. Kamerplanter weist eine neue Behandlungsanwendung zurück, wenn du dasselbe Mittel (oder denselben Wirkstoff) mehr als dreimal in 90 Tagen einsetzt (siehe [Behandlung an einer Pflanze dokumentieren](#behandlungsmittel-verwalten-stammdaten)).

Wenn diese Warnung erscheint:
1. Wähle ein Mittel mit einem anderen Wirkstoffmechanismus.
2. Warte mindestens 2 Behandlungszyklen, bevor du zum ursprünglichen Mittel zurückkehrst.

---

## Nützlinge

Nützlinge (z. B. Raubmilben — *Phytoseiulus persimilis* — gegen Spinnmilben, Schlupfwespen gegen Trauermücken) sind in Kamerplanter als **Stammdaten** hinterlegt: Erkennt die Schädlingserkennung anhand eines Fotos einen Nützling statt eines Schädlings, weist sie eindeutig darauf hin, damit er nicht versehentlich bekämpft wird.

!!! warning "Noch nicht implementiert"
    Eine eigene Dokumentation von Nützlings-**Freisetzungen** (Freisetzungsdatum, Menge, Standort) wird es erst in einer künftigen Version geben. Aktuell lässt sich der Einsatz von Nützlingen nur behelfsweise über die [Behandlungsmittel-Stammdaten](#behandlungsmittel-verwalten-stammdaten) erfassen (Typ „Biologisch", Ausbringungsmethode „Freisetzung", Karenzzeit 0 Tage).

**Wichtig bei Nützlingen:**
- Nützlinge haben **keine Karenzzeit** — Ernten sind jederzeit möglich.
- Vermeide nach dem Freisetzen von Nützlingen chemische Spritzungen, da diese auch die Nützlinge töten.

---

## Befallshistorie eines Standorts auswerten

!!! warning "Noch nicht implementiert"
    Eine Auswertung, welche Schädlinge und Krankheiten in welchem Standortbereich über die Zeit aufgetreten sind, wird es erst in einer künftigen Version geben. Bis dahin lässt sich der Verlauf nur pflanzenweise über die Schädlings-Detailseiten und die IPM-API nachvollziehen.

---

## Häufige Fragen

??? question "Was ist der Unterschied zwischen Karenzzeit und Wartezeit?"
    Im deutschen Sprachgebrauch werden beide Begriffe oft synonym verwendet. In Kamerplanter entspricht **Karenzzeit** dem englischen "Pre-Harvest Interval (PHI)" — die Mindestzeit zwischen letzter Anwendung und Ernte.

??? question "Kann ich eine Behandlung ohne Karenzzeit eintragen?"
    Ja. Für Behandlungen ohne Karenzzeit (z.B. Nützlingsfreisetzung, mechanische Maßnahmen wie Absammeln) trägst du 0 Tage ein. Diese Behandlungen blockieren keine Ernte.

??? question "Wie erkenne ich Spinnmilben?"
    Spinnmilben sind mit bloßem Auge kaum erkennbar. Typische Anzeichen: feine, silbrige Sprenkel auf den Blattoberflächen, feine Gespinste auf der Blattunterseite. Zur sicheren Diagnose empfiehlt sich eine 10×-Lupe.

??? question "Ich habe Neem-Öl ohne Karenzzeit-Angabe — welchen Wert trage ich ein?"
    Neem-Öl als biologisches Mittel gilt in Deutschland als relativ unbedenklich, aber es empfiehlt sich eine Wartezeit von 7 bis 14 Tagen. Nutze den Wert, der auf deinem Produkt angegeben ist, oder frage beim Hersteller nach.

---

## Für technische Nutzer: API-Zugriff

Einige IPM-Funktionen stehen bereits als REST-Endpunkte zur Verfügung, auch wenn die grafische Oberfläche dafür noch fehlt. Dieser Abschnitt richtet sich an technische Nutzer und Self-Hoster, die eigene Integrationen oder Skripte anbinden möchten. Eine angemeldete Sitzung (Bearer-Token) ist erforderlich.

| Endpunkt | Zweck |
|----------|-------|
| `POST .../ipm/plants/{plant_key}/inspections` | Inspektion manuell anlegen (freie Auswahl von Schädling, Befallsstärke und Notizen) |
| `GET .../ipm/plants/{plant_key}/inspections` | Gespeicherte Inspektionen einer Pflanze abrufen |
| `POST .../ipm/plants/{plant_key}/treatment-applications` | Behandlungsanwendung an einer Pflanze dokumentieren (löst die Karenzzeit-Sperre aus) |
| `GET .../ipm/plants/{plant_key}/harvest-safety` | Aktuellen Karenzzeit-Status einer Pflanze abfragen |

---

## Siehe auch

- [Schädlings-Detailseite](pest-detail.md) — Steckbrief, Referenzbilder, IPM-Gegenmaßnahmen und Nützlinge pro Schädling
- [Behandlungs-Detailseite](treatment-detail.md) — Wirkweise, Dosierung, Karenzzeit und Sicherheitshinweise für ein konkretes Behandlungsmittel
- [Schädlingserkennung per Foto](pest-detection.md) — Foto hochladen und automatisch einschätzen lassen
- [Ernte](harvest.md)
- [Aufgaben](tasks.md)
- [Standorte und Substrate](locations-substrates.md)
