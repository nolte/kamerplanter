# Sensorik und Messdaten

Kamerplanter erfasst Klimadaten, Substrat-Werte und Lichtdaten aus vier verschiedenen Quellen. Das System funktioniert sowohl mit teuren Smart-Home-Sensoren als auch völlig ohne Hardware — reine manuelle Eingabe ist vollständig unterstützt.

---

## Voraussetzungen

- Mindestens ein angelegter Standort
- Für automatische Daten: Sensoren physisch installiert und mit Home Assistant oder MQTT verbunden

---

## Die vier Datenquellen

Kamerplanter nutzt folgende Datenquellen in einer Fallback-Kette. Das System wechselt automatisch zur nächst verfügbaren Quelle, wenn eine Quelle ausfällt:

```
Automatisch (IoT/MQTT) → Home Assistant REST API → Wetter-API (Freiland) → Manuelle Eingabe
```

**1. Automatisch (IoT/MQTT)**
Sensoren (z.B. SCD40, AHT20, Xiaomi Bodensensor) senden Daten direkt per MQTT oder über Home Assistant an Kamerplanter. Keine Benutzeraktion erforderlich.

**2. Home Assistant (halbautomatisch)**
Home Assistant liefert Sensorwerte über seine REST API. Das ist sinnvoll, wenn deine Sensoren bereits in Home Assistant integriert sind.

**3. Wetter-API (nur Freiland)**
Für Freilandstandorte (Garten, Balkon) kann Kamerplanter Klimadaten vom Deutschen Wetterdienst (DWD), Open-Meteo oder OpenWeatherMap abrufen. Kein Sensor nötig.

**4. Manuelle Eingabe**
Du trägst Messwerte selbst ein. Kamerplanter erinnert dich mit Aufgaben, wann eine Messung fällig ist.

!!! note "Jede Messung hat eine Herkunfts-Kennzeichnung"
    In der Detailansicht siehst du immer, woher ein Messwert stammt: Sensor, Home Assistant, Wetter-API oder manuell. So weißt du, wie belastbar der Wert ist.

---

## Sensoren an einen Standort binden

### Schritt 1: Site oder Location öffnen

Navigiere zu **Standorte** und öffne die Site oder Location, zu der der Sensor gehört.

### Schritt 2: Sensor hinzufügen

Klicke auf **Sensor hinzufügen** (Icon in der Site-Detailseite oben rechts oder im Tab Sensoren).

### Schritt 3: Sensor konfigurieren

Fülle das Formular aus:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Bezeichnung des Sensors | "Temp/RH Growzelt A" |
| Typ | Was misst der Sensor? | Temperatur + Luftfeuchte |
| Datenquelle | Woher kommen die Daten? | Home Assistant |
| Entity-ID (HA) | Home Assistant Entity-Name | `sensor.growzelt_a_temperature` |
| MQTT-Topic | Bei MQTT-Anbindung | `kamerplanter/growzelt/temp` |

### Schritt 4: Verbindung testen

Klicke auf **Verbindung prüfen**. Kamerplanter versucht, den aktuellen Wert abzurufen. Bei Erfolg erscheint der Messwert.

---

## Messwerte manuell eingeben

Wenn du keine Sensoren verwendest oder ein Sensor ausgefallen ist, kannst du Messwerte manuell eintragen.

### Schritt 1: Zur Pflanze oder zum Standort navigieren

Öffne eine Pflanze oder einen Standort und suche den Tab **Messwerte** oder **Sensordaten**.

### Schritt 2: Messung erfassen

Klicke auf **Messung hinzufügen** und trage die Werte ein:

**Klimaparameter:**
- Temperatur (°C)
- Relative Luftfeuchte (%)
- VPD (wird automatisch berechnet, wenn Temperatur und Luftfeuchte bekannt sind)
- CO2 (ppm) — optional

**Substrat-Parameter:**
- Bodenfeuchte (%)
- Substrat-Temperatur (°C)
- EC im Substrat (mS/cm)
- pH-Wert

**Lichtparameter:**
- PPFD (µmol/m²/s) — Photosynthetische Photonenflussdichte
- DLI (mol/m²/d) — Tageslichtintegral (wird aus PPFD × Beleuchtungsstunden berechnet)

!!! tip "VPD automatisch berechnen lassen"
    Das Dampfdruckdefizit (VPD) musst du nicht selbst messen. Wenn du Temperatur und Luftfeuchte eingibst, berechnet Kamerplanter den VPD-Wert automatisch nach der Tetens-Formel.

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

Kamerplanter vergleicht den aktuellen VPD-Wert mit dem Zielwert der aktuellen Wachstumsphase und gibt bei Abweichungen einen Hinweis.

**CO2-Konzentration (ppm)**
Normale Raumluft: ca. 400–500 ppm. Pflanzen profitieren von 800–1500 ppm (bei ausreichend Licht). Über 1500 ppm bringt kaum weiteren Vorteil, kann aber bei Menschen Beschwerden verursachen.

### Substrat-Parameter

**Bodenfeuchte (%)**
Zeigt an, wie viel Wasser im Substrat vorhanden ist. Zu trocken führt zu Welken, zu nass begünstigt Wurzelfäule.

**EC im Substrat (mS/cm)**
Die EC im Substrat (gemessen am Abfluss oder mit Substratsonde) zeigt die Salzkonzentration im Wurzelbereich. Eine deutlich höhere Abfluss-EC als Eingabe-EC signalisiert Salzakkumulation und ist ein Hinweis für einen Spülgang.

**pH-Wert**
Der pH-Wert bestimmt die Verfügbarkeit von Nährstoffen. Außerhalb des optimalen Bereichs (Hydroponik: 5,5–6,5; Erde: 6,0–7,0) können Pflanzen Nährstoffe nicht aufnehmen, selbst wenn genug vorhanden ist.

### Licht-Parameter

**PPFD (µmol/m²/s) — Photosynthetische Photonenflussdichte**
Gibt an, wie viel photosynthetisch nutzbares Licht pro Sekunde auf die Pflanze trifft. Grobe Richtwerte:
- Niedrige Lichtpflanzen: 100–300 µmol/m²/s
- Mittlere Lichtpflanzen: 300–600 µmol/m²/s
- Hohe Lichtpflanzen: 600–1200+ µmol/m²/s

**DLI (mol/m²/d) — Tageslichtintegral**
Das Tageslichtintegral ist die Gesamtlichtmenge über einen Tag. Es wird aus PPFD × Beleuchtungsdauer berechnet. DLI ist besonders wichtig für Freilandgärtner und Gewächshäuser.

---

## Sensoren für Freiland: Wetter-API einrichten

!!! warning "Noch nicht implementiert"
    Die Wetter-API-Integration (DWD, OpenWeatherMap, Open-Meteo) ist **spezifiziert (REQ-005 v2.3) aber noch nicht implementiert**. Die folgenden Abschnitte beschreiben das geplante Verhalten. Aktuell werden Freiland-Messwerte nur über Home Assistant oder manuelle Eingabe erfasst.

Wenn du keinen Sensor im Freien hast, kannst du Klimadaten vom Wetterdienst abrufen.

### Schritt 1: Standortkoordinaten hinterlegen

Öffne deine Site und trage unter **Experten-Einstellungen** die GPS-Koordinaten ein (Breitengrad, Längengrad).

### Schritt 2: Wetter-Datenquelle auswählen

Wähle die bevorzugte Datenquelle:
- **Open-Meteo** (empfohlen): Kostenlos, kein API-Key erforderlich
- **Deutscher Wetterdienst (DWD)**: Offizielle deutsche Wetterdaten
- **OpenWeatherMap**: Global, 1000 kostenlose Anfragen/Tag

### Schritt 3: Aktualisierungsintervall festlegen

Wähle, wie oft die Wetterdaten abgerufen werden sollen (empfohlen: stündlich).

!!! note "Wetterdaten als Ergänzung"
    Wetterdaten spiegeln die Bedingungen am Wettermessstandort wider, nicht exakt in deinem Garten. Bei Abweichungen (z.B. durch einen schattigen Standort) solltest du die Werte manuell anpassen.

---

## Sensor-Ausfälle und Fallbacks

Wenn ein Sensor mehr als 6 Stunden keine Daten liefert, erkennt Kamerplanter diesen Ausfall automatisch:

1. Eine Warnung erscheint in der Standort-Detailansicht
2. Kamerplanter wechselt auf die nächste verfügbare Fallback-Quelle
3. Es wird eine Aufgabe erstellt: "Sensor prüfen — [Sensor-Name]"

Kurze Ausfälle (unter 2 Stunden) werden durch Interpolation der letzten bekannten Werte überbrückt.

---

## Häufige Fragen

??? question "Brauche ich zwingend Sensoren um Kamerplanter zu nutzen?"
    Nein. Kamerplanter funktioniert vollständig mit manuell eingetragenen Messwerten. Sensoren und Smart-Home-Integration sind optional — sie erleichtern die Arbeit, sind aber keine Voraussetzung.

??? question "Wie verbinde ich einen Xiaomi-Sensor mit Kamerplanter?"
    Xiaomi-Sensoren lassen sich am einfachsten über Home Assistant einbinden. Installiere die Xiaomi-Integration in Home Assistant, binde den Sensor ein und verbinde dann Home Assistant mit Kamerplanter über den Entity-Namen.

??? question "Kann ich mehrere Sensoren für denselben Standort haben?"
    Ja. Du kannst beliebig viele Sensoren einem Standort zuordnen. Wenn z.B. Temperatur und Luftfeuchte von verschiedenen Geräten kommen, konfiguriere diese als separate Sensoren.

??? question "Was bedeutet der Hinweis 'Messung veraltet'?"
    Kamerplanter zeigt diesen Hinweis, wenn die letzte Messung eines Parameters älter als das konfigurierte Überwachungsintervall ist. Das ist ein Hinweis, dass eine neue Messung fällig ist.

---

## Siehe auch

- [Dashboard](dashboard.md)
- [Aufgaben](tasks.md)
- [Guides: VPD-Optimierung](../guides/vpd-optimization.md)
