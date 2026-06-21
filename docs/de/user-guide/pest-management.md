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
- **Klimaüberwachung**: Hinweis bei dauerhaft hoher Luftfeuchte (> 70 % rH), die Schimmelpilzen begünstigt

!!! tip "Prävention lohnt sich"
    Schädlinge und Krankheiten, die frühzeitig erkannt werden, lassen sich mit biologischen Mitteln behandeln. Wer zu spät handelt, ist oft auf chemische Mittel angewiesen, die Karenzzeiten von Wochen auslösen.

### Stufe 2: Monitoring (Befallskontrollen)

Regelmäßige Inspektionen sind das wichtigste Werkzeug zur Früherkennung. Kamerplanter hilft bei der Planung und Dokumentation.

### Stufe 3: Intervention

Wenn ein Befall festgestellt wurde, wähle die passende Behandlung. Kamerplanter überwacht die Karenzzeit und blockiert bei Bedarf die Ernte.

---

## Befallskontrolle (Inspektion) durchführen

### Schritt 1: Inspektion starten

1. Navigiere zu **Pflanzenschutz (IPM)** in der Navigation oder öffne eine Pflanze und wechsle zum Tab **Pflanzenschutz**.
2. Klicke auf **Neue Inspektion**.

### Schritt 2: Befallsstärke einschätzen

Bewerte die Befallsstärke:

| Stufe | Beschreibung |
|-------|-------------|
| Kein Befall | Keine Anzeichen von Schädlingen oder Krankheiten |
| Niedrig | Vereinzelte Anzeichen, keine Ausbreitung |
| Mittel | Sichtbarer Befall, lokale Ausbreitung |
| Hoch | Starker Befall, weitreichende Ausbreitung |
| Kritisch | Akute Pflanzenschädigung, sofortige Maßnahmen nötig |

### Schritt 3: Schädlinge oder Krankheiten dokumentieren

Wenn du einen Befall entdeckt hast, wähle aus der Liste. Klicke auf den Namen eines Schädlings, um die [Schädlings-Detailseite](pest-detail.md) mit Steckbrief, Referenzbildern und Gegenmaßnahmen aufzurufen.

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

Wenn das Tier oder die Krankheit nicht in der Liste ist, kannst du sie manuell eingeben.

### Schritt 4: Fotos hinzufügen (optional)

Füge Fotos der befallenen Stellen hinzu. Das hilft bei der Verlaufsbeobachtung und späteren Diagnose.

### Schritt 5: Inspektion speichern

Die Inspektion wird in der Inspektionshistorie der Pflanze gespeichert und ist im Kalender sichtbar.

---

## Behandlung erfassen

### Schritt 1: Behandlung anlegen

1. Navigiere zu **Pflanzenschutz (IPM) → Behandlungen** oder klicke in der Inspektion auf **Behandlung einleiten**.
2. Klicke auf **Behandlung hinzufügen**.

### Schritt 2: Behandlungsmittel und -methode wählen

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Mittel / Präparat | Name des eingesetzten Mittels | "Neem-Öl 2 %", "Spidex (Phytoseiulus persimilis — Raubmilbe)" |
| Typ | Kulturell, Biologisch, Chemisch, Mechanisch | Biologisch |
| Wirkstoff | Aktiver Bestandteil | "Azadirachtin" |
| Karenzzeit (Tage) | Wartezeit bis zur Ernte | 14 |
| Dosierung | Menge und Konzentration | "5 ml/L" |
| Ausbringungsmethode | Sprühen, Gießen, Streuen, Freisetzung | Sprühen |

### Schritt 3: Ausbringung dokumentieren

Trage das Ausbringungsdatum und die behandelten Pflanzen ein. Das System berechnet automatisch das frühestmögliche Erntedatum.

!!! danger "Karenzzeit läuft sofort"
    Sobald du eine Behandlung mit Karenzzeit eingetragen hast, ist die Ernte der betroffenen Pflanzen gesperrt, bis die Karenzzeit abgelaufen ist. Kamerplanter zeigt das frühestmögliche Erntedatum deutlich an.

---

## Karenzzeit verstehen und überwachen

Die **Karenzzeit** (auch Pre-Harvest Interval, PHI) ist die gesetzlich vorgeschriebene Wartezeit zwischen der letzten Anwendung eines Pflanzenschutzmittels und der Ernte. Diese Wartezeit schützt Verbraucher vor Rückständen im Erntegut.

**Wo siehst du laufende Karenzzeiten?**

1. In der Pflanzendetailansicht im Tab **Pflanzenschutz** — ein roter Hinweis erscheint, wenn eine Karenzzeit aktiv ist
2. In der Aufgaben-Übersicht — automatisch erstellte Aufgabe "Ernte möglich ab [Datum]"
3. Im Kalender — Karenzzeit-Ablauf als Ereignis sichtbar

**Karenzzeit überschrieben — was tun?**

Wenn du eine Behandlung irrtümlich eingetragen hast, kannst du sie öffnen und das Ausbringungsdatum korrigieren. Wenn du ein falsches Mittel eingetragen hast, kontaktiere das Support-Team oder nutze die Kommentarfunktion, um den Fehler zu dokumentieren.

---

## Resistenzmanagement

!!! warning "Wirkstoff-Rotation beachten"
    Schädlinge entwickeln Resistenzen, wenn dieselbe Wirkstoffgruppe zu oft eingesetzt wird. Kamerplanter warnt dich, wenn du dasselbe Mittel (oder denselben Wirkstoff) mehr als dreimal in 90 Tagen einsetzt.

Wenn eine Warnung erscheint:
1. Öffne die Behandlungshistorie der Pflanze.
2. Wechsle zu einem Mittel mit einem anderen Wirkstoffmechanismus.
3. Warte mindestens 2 Behandlungszyklen, bevor du zum ursprünglichen Mittel zurückkehrst.

---

## Nützlinge einsetzen

Für biologische Bekämpfung kannst du Nützlinge dokumentieren:

1. Navigiere zu **Pflanzenschutz → Nützlinge**.
2. Klicke auf **Nützling freigesetzt**.
3. Wähle den Nützling aus der Liste (z.B. Raubmilben — *Phytoseiulus persimilis* — gegen Spinnmilben, Schlupfwespen gegen Trauermücken).
4. Trage Freisetzungsdatum, Menge und Standort ein.

**Wichtig bei Nützlingen:**
- Nützlinge haben **keine Karenzzeit** — Ernten sind jederzeit möglich.
- Vermeide nach dem Freisetzen von Nützlingen chemische Spritzungen, da diese auch die Nützlinge töten.

---

## Befallshistorie eines Standorts auswerten

Unter **Pflanzenschutz → Befallshistorie** siehst du, welche Schädlinge und Krankheiten in welchem Bereich aufgetreten sind. Das hilft bei der Planung präventiver Maßnahmen für den nächsten Zyklus.

---

## Häufige Fragen

??? question "Was ist der Unterschied zwischen Karenzzeit und Wartezeit?"
    Im deutschen Sprachgebrauch werden beide Begriffe oft synonym verwendet. In Kamerplanter entspricht **Karenzzeit** dem englischen "Pre-Harvest Interval (PHI)" — die Mindestzeit zwischen letzter Anwendung und Ernte.

??? question "Kann ich eine Behandlung ohne Karenzzeit eintragen?"
    Ja. Für Behandlungen ohne Karenzzeit (z.B. Nützlingsfreisetzung, mechanische Maßnahmen wie Absammeln) trägst du 0 Tage ein. Diese Behandlungen blockieren keine Ernte.

??? question "Wie erkenne ich Spinnmilben?"
    Spinnmilben sind mit bloßem Auge kaum erkennbar. Typische Anzeichen: feine, silbrige Sprenkel auf den Blattoberflächen, feine Gespinste auf der Blattunterseite. Zur sicheren Diagnose empfiehlt sich eine 10×-Lupe.

??? question "Ich habe Neem-Öl ohne Karenzzeit-Angabe — welchen Wert trage ich ein?"
    Neem-Öl als biologisches Mittel gilt in Deutschland als relativ unbedenklich, aber es empfiehlt sich eine Wartezeit von 7–14 Tagen. Nutze den Wert, der auf deinem Produkt angegeben ist, oder frage beim Hersteller nach.

---

## Siehe auch

- [Schädlings-Detailseite](pest-detail.md) — Steckbrief, Referenzbilder, IPM-Gegenmaßnahmen und Nützlinge pro Schädling
- [Behandlungs-Detailseite](treatment-detail.md) — Wirkweise, Dosierung, Karenzzeit und Sicherheitshinweise für ein konkretes Behandlungsmittel
- [Schädlingserkennung per Foto](pest-detection.md) — Foto hochladen und automatisch einschätzen lassen
- [Ernte](harvest.md)
- [Aufgaben](tasks.md)
- [Standorte und Substrate](locations-substrates.md)
