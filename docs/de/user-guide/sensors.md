# Sensorik und Messdaten

Kamerplanter ist für vier Datenquellen für Klima-, Substrat- und Lichtdaten ausgelegt (REQ-005 v2.7): automatische IoT/MQTT-Sensoren, Home Assistant, eine Wetter-API für Freiland-Standorte und manuelle Eingabe. Aktuell produktiv nutzbar sind **Home Assistant** (automatisches Auslesen) und die **manuelle Eingabe am Tank** — die übrigen Quellen sind spezifiziert, aber noch nicht umgesetzt (Details unten).

---

## Voraussetzungen

- Mindestens ein angelegter Standort (Site oder Location)
- Für automatische Daten: Sensoren in Home Assistant eingebunden und Kamerplanter mit Home Assistant verbunden — siehe [Home Assistant Integration](../guides/home-assistant-integration.md)

---

## Die Datenquellen im Überblick

Die Spezifikation sieht eine vierstufige Fallback-Kette vor. Aktuell ist davon **nur ein automatischer Weg (Home Assistant) sowie die manuelle Eingabe am Tank** tatsächlich umgesetzt — ein automatischer Wechsel zwischen den Stufen findet nicht statt:

```
1. Automatisch (IoT/MQTT) — geplant
2. Home Assistant REST API — REAL, umgesetzt
3. Wetter-API (nur Freiland) — geplant
4. Manuelle Eingabe — REAL, aktuell nur am Tank
```

**1. Automatisch (IoT/MQTT) — geplant**
Das Sensor-Datenmodell hat bereits ein `mqtt_topic`-Feld für eine künftige direkte MQTT-Anbindung. Diese Ingestion ist **noch nicht implementiert** — das Feld hat aktuell keine Wirkung und muss nicht ausgefüllt werden.

**2. Home Assistant (automatisch)**
Ein Hintergrundjob fragt alle 5 Minuten die aktuellen Werte aller aktiven Sensoren mit hinterlegter HA-Entity-ID ab und schreibt sie in die Zeitreihen-Datenbank (Quelle `ha_auto`). Das ist der einzige aktuell implementierte automatische Weg.

**3. Wetter-API (nur Freiland) — geplant**
Für Freilandstandorte soll Kamerplanter künftig Klimadaten vom Deutschen Wetterdienst (DWD), Open-Meteo oder OpenWeatherMap abrufen können. Siehe Abschnitt [Sensoren für Freiland](#sensoren-fuer-freiland-wetter-api-einrichten) weiter unten.

**4. Manuelle Eingabe — aktuell nur am Tank**

!!! note "Manuelle Messwerte gibt es aktuell nur für Tanks"
    Eine manuelle Eingabemaske für Klimawerte an Pflanze oder Standort existiert noch nicht. Manuell erfasst werden können aktuell EC, pH, Wassertemperatur, Füllstand, TDS, gelöster Sauerstoff und ORP eines **Tanks** — siehe [Tankmanagement](tanks.md#aktuellen-tankzustand-erfassen). Für Standort-Sensoren (Site/Location) kannst du nur einen Sensor mit Home-Assistant-Anbindung anlegen; ohne Home Assistant bleiben deren Messwerte leer.

!!! note "Jede Messung hat eine Herkunfts-Kennzeichnung"
    Jeder gespeicherte Messwert trägt ein Quellen-Feld (`manual`, `ha_auto` u. a.). So lässt sich nachvollziehen, ob ein Wert automatisch oder von Hand erfasst wurde.

---

## Sensoren an einen Standort binden

### Schritt 1: Site oder Location öffnen

Navigiere zu **Standorte** und öffne die Site oder Location, zu der der Sensor gehört.

### Schritt 2: Sensor hinzufügen

Klicke im Abschnitt **Sensoren** auf **Sensor hinzufügen**.

### Schritt 3: Sensor konfigurieren

Fülle das Formular aus:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Sensorname | Bezeichnung des Sensors | „Temp/RH Growzelt A" |
| Messgröße | Was misst der Sensor? Auswahl aus vordefinierten Typen (siehe [Messgrößen](#messgroessen-im-formular)) | Temperatur (°C) |
| HA-Sensor auswählen | Autocomplete mit den in Home Assistant verfügbaren Entities (nur sichtbar, wenn HA konfiguriert ist und Entities gefunden wurden) | „Growzelt A Temp (sensor.growzelt_a_temperature) — 23.4 °C" |
| HA Entity-ID | Freitextfeld, erscheint nur, wenn keine HA-Entities gefunden wurden — manuelle Eingabe des Entity-Namens | `sensor.growzelt_a_temperature` |
| MQTT-Topic | Reserviert für die künftige direkte MQTT-Anbindung (Future, aktuell ohne Wirkung) | `kamerplanter/growzelt/temp` |
| Aktiv | Nur beim Bearbeiten sichtbar. Deaktivierte Sensoren werden vom Home-Assistant-Abfragejob nicht mehr berücksichtigt | ✓ |

!!! info "Kein separates Feld „Datenquelle" und kein Verbindungstest"
    Es gibt kein eigenes Auswahlfeld „Datenquelle" und keinen „Verbindung prüfen"-Button. Ob ein Sensor automatisch versorgt wird, ergibt sich allein daraus, ob eine HA-Entity-ID hinterlegt ist. Der erste tatsächliche Wert erscheint erst mit der nächsten automatischen Abfrage (alle 5 Minuten) oder — bei Tanks — über die Live-Abfrage auf der Tank-Detailseite.

### HA-Entity-Autocomplete

Ist Home Assistant konfiguriert, lädt der Dialog beim Öffnen automatisch die verfügbaren Home-Assistant-Entities. Wählst du eine Entity aus der Liste, übernimmt Kamerplanter automatisch:

- den vorgeschlagenen Sensornamen,
- die passende Maßeinheit,
- eine vorgeschlagene Messgröße (sofern Home Assistant eine `device_class` liefert, aus der sich die Messgröße ableiten lässt),
- die Entity-ID selbst.

Werden keine Home-Assistant-Entities gefunden (z. B. weil keine HA-Integration eingerichtet ist oder Home Assistant aktuell nicht erreichbar ist), blendet der Dialog stattdessen ein Freitextfeld **HA Entity-ID** ein, in das du den Entity-Namen von Hand einträgst.

### Messgrößen im Formular {#messgroessen-im-formular}

Die Messgröße wird aus einer festen Liste gewählt:

| Messgröße | Bedeutung |
|-----------|-----------|
| `temperature_celsius` | Temperatur (°C) |
| `humidity_percent` | Relative Luftfeuchte (%) |
| `vpd_kpa` | VPD — Dampfdruckdefizit (kPa) |
| `co2_ppm` | CO₂-Konzentration (ppm) |
| `ppfd` | PPFD — Photosynthetische Photonenflussdichte (µmol/m²/s) |
| `ph` | pH-Wert |
| `ec_ms` | EC — elektrische Leitfähigkeit (mS/cm) |
| `water_temp_celsius` | Wassertemperatur (°C) |
| `tds_ppm` | TDS — gesamtgelöste Stoffe (ppm) |
| `dissolved_oxygen_mgl` | Gelöster Sauerstoff (mg/L) — relevant für Hydroponik/Aquaponik |
| `orp_mv` | ORP — Redoxpotenzial (mV) |
| `fill_level_percent` | Füllstand (%) |

!!! note "Substratfeuchte (Bodenfeuchte) noch nicht als Messgröße wählbar"
    Eine eigene Messgröße für Substrat-/Bodenfeuchte gibt es aktuell nicht. Willst du Substratfeuchte im Blick behalten, bleibt derzeit nur eine manuelle Notiz an der Pflanze — eine dedizierte Erfassung ist noch nicht umgesetzt.

Die ersten vier Messgrößen (Temperatur, Luftfeuchte, VPD, CO₂) und PPFD sind für Klima-Sensoren an Site/Location typisch. Die übrigen (pH, EC, Wassertemperatur, TDS, gelöster Sauerstoff, ORP, Füllstand) sind vor allem für Tanks relevant — siehe [Tankmanagement](tanks.md). Das Formular erzwingt diese Zuordnung nicht technisch; du kannst z. B. auch an einer Location einen externen EC-Sensor anlegen.

---

## Überwachte Parameter verstehen

### Klima-Parameter

**Temperatur (°C)**
Die Lufttemperatur im Anbaubereich. Optimale Bereiche sind phasenabhängig — in der vegetativen Phase typisch 22–26 °C, in der Blüte 18–24 °C.

**Relative Luftfeuchte (rH, %)**
Zu hohe Luftfeuchte begünstigt Schimmelpilze (Botrytis, Mehltau). Zu niedrige Luftfeuchte erhöht den Wasserstress.

**VPD (kPa) — Dampfdruckdefizit**
Der VPD-Wert ist der wichtigste Klimaparameter für optimales Pflanzenwachstum. Er kombiniert Temperatur und Luftfeuchte zu einem Einzelwert, der beschreibt, wie stark die Luft Feuchtigkeit von den Blättern abzieht:

- **VPD zu niedrig** (< 0,4 kPa): Pflanze transpiriert zu wenig, Nährstoffaufnahme reduziert, Schimmelgefahr
- **VPD optimal** (0,8–1,2 kPa): Bestmögliches Wachstum und Nährstoffaufnahme
- **VPD zu hoch** (> 1,6 kPa): Pflanze schließt Stomata, Nährstoffmangel trotz ausreichender Düngung

Kamerplanter berechnet VPD aus Temperatur und Luftfeuchte (Tetens-Formel) und vergleicht den Wert mit dem Zielwert der aktuellen Wachstumsphase.

**CO2-Konzentration (ppm)**
Normale Raumluft: ca. 400–500 ppm. Pflanzen profitieren von 800–1500 ppm (bei ausreichend Licht). Über 1500 ppm bringt kaum weiteren Vorteil, kann aber bei Menschen Beschwerden verursachen.

### Wasser- und Nährlösungs-Parameter (Tank)

Diese Werte werden in der Praxis am Tank erfasst — automatisch über Home Assistant oder manuell (siehe [Tankmanagement](tanks.md)):

**EC (mS/cm)**
Die elektrische Leitfähigkeit der Nährlösung zeigt die Salzkonzentration. Eine deutlich höhere Abfluss-EC als Eingabe-EC signalisiert Salzakkumulation im Substrat und ist ein Hinweis für einen Spülgang.

**pH-Wert**
Der pH-Wert bestimmt die Verfügbarkeit von Nährstoffen. Außerhalb des optimalen Bereichs (Hydroponik: 5,5–6,5; Erde: 6,0–7,0) können Pflanzen Nährstoffe nicht aufnehmen, selbst wenn genug vorhanden ist.

**Wassertemperatur, TDS, gelöster Sauerstoff, ORP**
Zusätzliche Wasserqualitäts-Kennzahlen, vor allem für Hydroponik-/Aquaponik-Systeme relevant. Gelöster Sauerstoff ist wichtig für die Wurzelgesundheit in Nährlösungssystemen ohne Substrat (z. B. DWC — Deep Water Culture, siehe [Tankmanagement](tanks.md)).

### Licht-Parameter

**PPFD (µmol/m²/s) — Photosynthetische Photonenflussdichte**
Gibt an, wie viel photosynthetisch nutzbares Licht pro Sekunde auf die Pflanze trifft. Grobe Richtwerte:

- Niedrige Lichtpflanzen: 100–300 µmol/m²/s
- Mittlere Lichtpflanzen: 300–600 µmol/m²/s
- Hohe Lichtpflanzen: 600–1200+ µmol/m²/s

**DLI (mol/m²/d) — Tageslichtintegral**
DLI ist kein eigener Sensor-Messwert, sondern wird aus PPFD × Beleuchtungsdauer berechnet — unter anderem als Teil der Photoperioden-Übergangspläne (siehe [Umgebungssteuerung & Aktorik](actuator-control.md)).

---

## Sensoren für Freiland: Wetter-API einrichten {#sensoren-fuer-freiland-wetter-api-einrichten}

!!! warning "Noch nicht implementiert"
    Die Wetter-API-Integration (DWD, OpenWeatherMap, Open-Meteo) ist **spezifiziert (REQ-005 v2.7), aber noch nicht implementiert**. Die folgenden Abschnitte beschreiben das geplante Verhalten im Futur. Aktuell werden Freiland-Messwerte nur über Home Assistant oder manuell am Tank erfasst.

Wenn du keinen Sensor im Freien hast, wirst du künftig Klimadaten vom Wetterdienst abrufen können.

### Schritt 1: Standortkoordinaten hinterlegen

Du wirst unter **Experten-Einstellungen** der Site die GPS-Koordinaten (Breitengrad, Längengrad) hinterlegen können.

### Schritt 2: Wetter-Datenquelle auswählen

Du wirst zwischen folgenden Datenquellen wählen können:

- **Open-Meteo** (empfohlen): Kostenlos, kein API-Key erforderlich
- **Deutscher Wetterdienst (DWD)**: Offizielle deutsche Wetterdaten
- **OpenWeatherMap**: Global, 1000 kostenlose Anfragen/Tag

### Schritt 3: Aktualisierungsintervall festlegen

Du wirst festlegen können, wie oft die Wetterdaten abgerufen werden (empfohlen: stündlich).

!!! note "Wetterdaten als Ergänzung"
    Wetterdaten spiegeln die Bedingungen am Wettermessstandort wider, nicht exakt in deinem Garten. Bei Abweichungen (z. B. durch einen schattigen Standort) werden manuelle Anpassungen weiterhin nötig sein.

---

## Sensor-Ausfälle, Fallback und Interpolation

!!! warning "Noch nicht implementiert"
    Eine automatische Ausfallerkennung für Sensoren, ein automatischer Wechsel auf eine Fallback-Quelle sowie das Überbrücken kurzer Ausfälle durch Interpolation sind **spezifiziert, aber noch nicht umgesetzt**. Aktuell erscheint bei einem ausgefallenen Home-Assistant-Sensor einfach kein neuer Messwert — es gibt weder eine Warnung noch eine automatisch erzeugte Aufgabe noch eine Ersatzberechnung.

Geplant ist folgendes Verhalten: Liefert ein Sensor länger als 6 Stunden keine Daten, wird Kamerplanter dies künftig erkennen, eine Warnung anzeigen, auf die nächste verfügbare Quelle wechseln und eine Aufgabe „Sensor prüfen" anlegen. Kurze Ausfälle (unter 2 Stunden) sollen durch Interpolation der letzten bekannten Werte überbrückt werden.

---

## Datenaufbewahrung

Automatisch erfasste Messwerte werden gestuft heruntergerechnet und irgendwann gelöscht (Rohdaten 90 Tage, danach Stunden- und Tagesmittel, siehe [Datenaufbewahrung & Anonymisierung](../guides/data-retention.md#retention-matrix-sensordaten)).

---

## Häufige Fragen

??? question "Brauche ich zwingend Sensoren, um Kamerplanter zu nutzen?"
    Nein. Sensoren und Home-Assistant-Integration sind optional. Am Tank kannst du EC, pH und weitere Werte jederzeit manuell eintragen. Für Standort-Klimadaten (Temperatur, Luftfeuchte, VPD, CO₂) benötigst du aktuell allerdings eine Home-Assistant-Anbindung — eine manuelle Eingabemaske dafür gibt es noch nicht.

??? question "Wie verbinde ich einen Xiaomi-Sensor mit Kamerplanter?"
    Xiaomi-Sensoren lassen sich am einfachsten über Home Assistant einbinden. Installiere die Xiaomi-Integration in Home Assistant, binde den Sensor ein und wähle ihn anschließend im Kamerplanter-Sensorformular über die HA-Entity-Autocomplete aus.

??? question "Kann ich mehrere Sensoren für denselben Standort haben?"
    Ja. Du kannst beliebig viele Sensoren einem Standort zuordnen. Wenn z. B. Temperatur und Luftfeuchte von verschiedenen Geräten kommen, konfiguriere diese als separate Sensoren.

??? question "Was bedeutet der Hinweis „Veraltet" bei einem Tank?"
    Dieser Hinweis erscheint nur bei der Live-Abfrage auf der Tank-Detailseite: Ist der letzte erfasste Zustand älter als 60 Minuten, zeigt Kamerplanter „Veraltet" an (unter 5 Minuten: „Aktuell", dazwischen: „Vor X Min"). Für Standort-Sensoren (Site/Location) gibt es diese Kennzeichnung aktuell nicht.

---

## Siehe auch

- [Meiner Pflanze geht es schlecht — Symptom-Diagnose](plant-health-troubleshooting.md)
- [Dashboard](dashboard.md)
- [Aufgaben](tasks.md)
- [Tankmanagement](tanks.md)
- [Home Assistant Integration](../guides/home-assistant-integration.md)
- [Datenaufbewahrung & Anonymisierung](../guides/data-retention.md)
- [Guides: VPD-Optimierung](../guides/vpd-optimization.md)
