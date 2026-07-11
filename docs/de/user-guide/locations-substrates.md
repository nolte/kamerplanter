# Standorte und Substrate

Standorte beschreiben, wo deine Pflanzen wachsen — vom gesamten Garten bis zum einzelnen Topfplatz. Substrate definieren das Wachstumsmedium. Beide Konzepte bilden die räumliche Grundlage für alle anderen Funktionen in Kamerplanter.

---

## Voraussetzungen

- Ein Kamerplanter-Konto mit mindestens einem Mandanten (wird beim Onboarding automatisch angelegt)
- Für Substrate: Mindestens ein angelegter Standort

---

## Standort-Hierarchie verstehen

Kamerplanter organisiert Standorte in einer Baumstruktur mit drei Ebenen:

```
Site (Anlage)
  └── Location (Bereich)
        └── Slot (Pflanzplatz)
```

**Site** ist deine übergeordnete Anlage — zum Beispiel "Mein Garten" oder "Wohnung Berlin". Auf Site-Ebene hinterlegst du die Wasserquelle, die Klimazone und die Gesamtfläche.

**Location** ist ein konkreter Bereich innerhalb der Site — zum Beispiel "Growzelt A", "Hochbeet 1" oder "Südbalkon". Locations können auch weitere Locations enthalten: du kannst "Haus" → "Wohnzimmer" → "Fensterbank Süd" abbilden.

**Slot** ist ein einzelner Pflanzplatz — zum Beispiel "TENT01_A1" für Platz A1 im Growzelt 1. Slots sind immer die unterste Ebene und können genau einer Pflanze zugeordnet werden.

!!! tip "Tipp: Wie tief strukturieren?"
    Für einfache Setups (Balkon, ein Growzelt) reicht es, Sites und Locations anzulegen. Slots sind nützlich, wenn du viele Pflanzen im gleichen Bereich hast und jeden Platz einzeln verfolgen möchtest.

---

## Eine neue Site anlegen

### Schritt 1: Zur Standortverwaltung navigieren

Klicke in der linken Navigation auf **Standorte**. Die Übersichtsseite zeigt alle deine Sites mit einer Karte und einer Listensicht.

### Schritt 2: Neue Site erstellen

Klicke auf **Site hinzufügen** (oben rechts). Ein Formular öffnet sich.

### Schritt 3: Grunddaten ausfüllen {#grunddaten-ausfüllen}

Fülle folgende Felder aus:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Name der Site | "Mein Indoor-Garten" |
| Typ | Legt fest, welche Funktionen für diese Site verfügbar sind (siehe Tabelle unten) | "Außenbereich" |
| Breitengrad / Längengrad (GPS) | GPS-Koordinaten der Site — beide Felder gemeinsam ausfüllen oder beide leer lassen | 52,52 / 13,40 |
| Klimazone | Standort-Klimazone im USDA-Winterhärtezonen-Format | "8a" |
| Gesamtfläche (m²) | Gesamte Anbaufläche | 12 |
| Zeitzone | Zeitzone für Aufgaben und Kalender | "Europe/Berlin" |

**Verfügbare Site-Typen:**

| Typ | Beschreibung |
|-----|-------------|
| Außenbereich | Freiland — schaltet Wetterquellen und die [Überwinterungsautomatik](overwintering.md) frei |
| Gewächshaus | Glashaus oder Folientunnel — schaltet Wetterquellen und die [Überwinterungsautomatik](overwintering.md) frei |
| Innenbereich | Zimmer oder Wohnbereich ohne direkten Außenklimabezug |
| Fensterbrett | Fensterplatz mit indirektem Außenklimabezug |
| Balkon | Balkon — als frostgefährdeter Außenstandort schaltet er wie Außenbereich und Gewächshaus GPS-Koordinaten, Wetterquellen und die [Überwinterungsautomatik](overwintering.md) frei |
| Growzelt | Abgeschlossenes Growzelt mit kontrolliertem Klima |

!!! info "Warum USDA-Zonen und nicht Köppen-Klimaklassifikation?"
    Kamerplanter erwartet für die Klimazone das **USDA-Winterhärtezonen-Format** (eine Zahl von 1–13, optional mit Zusatz „a" oder „b", z. B. „8a"), nicht die Köppen-Klimaklassifikation (z. B. „Cfb"). Der Grund: Die Winterhärte-Angaben der Pflanzenarten in den Stammdaten (`hardiness_zones`) nutzen ebenfalls dieses Format — nur so lässt sich später automatisch prüfen, ob eine Art an deinem Standort im Freien überwintern kann. Die passende Zone für deinen Wohnort findest du z. B. über die offizielle [USDA Plant Hardiness Zone Map](https://planthardiness.ars.usda.gov/) oder vergleichbare europäische Winterhärtezonen-Karten.

!!! tip "Warum GPS-Koordinaten wichtig sind"
    Erst mit hinterlegten GPS-Koordinaten kann Kamerplanter für Außenbereich-, Gewächshaus- und Balkon-Sites automatisch Wetterdaten abrufen und Frostwarnungen berechnen — ein Balkon gilt dabei als frostgefährdeter Außenstandort und wird deshalb genau wie Außenbereich und Gewächshaus behandelt. Trägst du bei einem anderen Typ (z. B. Innenbereich) trotzdem Koordinaten ein, bleiben sie vorerst ungenutzt — schaltest du den Typ später auf Außenbereich, Gewächshaus oder Balkon um, greifen sie automatisch.

!!! tip "Die Klimazone kann automatisch ermittelt werden"
    Für Außenbereich- und Gewächshaus-Sites mit GPS-Koordinaten berechnet Kamerplanter diese Zone bereits automatisch im Hintergrund aus den langjährigen Klimadaten deines Standorts und hält dieses Feld damit synchron — du musst sie in diesem Fall nicht selbst nachschlagen. Details zur Berechnung, zum manuellen Übersteuern und zum aktuellen Stand der Weboberfläche unter [Klimazonen & Winterhärte](../guides/climate-zones.md). <!-- REQ-039 -->

!!! note "Erfahrungsstufen"
    Je nach deiner Erfahrungsstufe (Einsteiger / Mittelstufe / Experte, einstellbar in den Kontoeinstellungen) siehst du mehr oder weniger Felder. Name und Typ siehst du bereits als Einsteiger; die GPS-Koordinaten, die Wasserquellen-Konfiguration, die Klimazone und die Gesamtfläche kommen ab der Mittelstufe hinzu; die Zeitzone ist ein Experten-Feld.

### Schritt 4: Wasserquelle konfigurieren (optional, ab Mittelstufe)

Wenn du dein Leitungswasser oder eine Umkehrosmose-Anlage nutzt, hinterlege die Wasserwerte. Das System berechnet daraus automatisch dein EC-Budget (EC = elektrische Leitfähigkeit, ein Maß für die Nährsalzkonzentration deiner Nährlösung — mehr dazu unter [Dünge-Logik](fertilization.md)), den CalMag-Bedarf und Mischungsempfehlungen.

#### Leitungswasser-Profil

| Feld | Einheit | Typischer Bereich (DE) | Beschreibung |
|------|---------|----------------------|-------------|
| EC | mS/cm | 0,3–0,8 | Elektrische Leitfähigkeit — zeigt den Gesamtmineralgehalt |
| pH | — | 7,0–8,0 | Säuregrad des Wassers |
| Gesamthärte (GH) | ppm CaCO3 | 100–350 | Summe aller gelösten Mineralien (Ca + Mg) |
| Karbonathärte (KH) | ppm CaCO3 | 80–250 | Pufferkapazität des Wassers (Alkalinity) |
| Calcium (Ca) | mg/L | 30–120 | Wichtig für CalMag-Berechnung |
| Magnesium (Mg) | mg/L | 5–30 | Wichtig für CalMag-Berechnung |
| Chlor | mg/L | 0–0,3 | Bei > 0,1 mg/L Wasser abstehen lassen oder filtern |
| Chloramin | mg/L | 0 | In Deutschland selten eingesetzt |

!!! info "Umrechnung deutscher Wasserhärte"
    Deutsche Wasserwerke geben die Härte oft in °dH (Grad deutscher Härte) an. So rechnest du um:

    - **Gesamthärte**: °dH × 17,848 = ppm CaCO3 (z.B. 11,6 °dH = 207 ppm)
    - **Karbonathärte**: °dH × 17,848 = ppm CaCO3 (z.B. 9,1 °dH = 162 ppm)

#### Zusätzliche Optionen

- **Hat RO-Anlage**: Aktiviere dies, wenn du eine Umkehrosmose-Anlage hast. Das System berechnet dann Mischungsverhältnisse aus Leitungs- und RO-Wasser.
- **Messdatum**: Datum der Wasseranalyse. Kamerplanter warnt dich, wenn die Analyse älter als 12 Monate ist.
- **Quellennotiz**: Freitext für die Herkunft der Werte (z.B. "Hamburg Wasser Trinkwasseranalyse 2025").

!!! tip "Wasserwerte herausfinden"
    Dein lokales Wasserwerk stellt die Trinkwasseranalyse in der Regel kostenlos bereit — oft als PDF-Download auf der Website. Deutsche Wasserversorger sind nach Trinkwasserverordnung (TrinkwV §21) verpflichtet, diese Daten zu veröffentlichen.

    **Beispiele:**

    - **Hamburg**: [hamburgwasser.de/wasser](https://www.hamburgwasser.de/wasser) — PLZ-Suche unter "Mein Trinkwasser"
    - **Berlin**: berliner-wasserbetriebe.de — Wasserqualität nach PLZ
    - **München**: swm.de — Trinkwasseranalyse nach Versorgungsgebiet

    Alternativ kannst du die Werte selbst messen: Ein EC/TDS-Messgerät (TDS = Total Dissolved Solids, zu Deutsch Gesamtgehalt gelöster Feststoffe; ab ca. 15 EUR) liefert den EC-Wert, ein pH-Messgerät den pH. Für Calcium und Magnesium sind Tropfentests (GH/KH-Test aus der Aquaristik, ab ca. 8 EUR) eine günstige Option.

!!! warning "Warum genaue Wasserwerte wichtig sind"
    Kamerplanter berechnet aus deinen Wasserwerten das **EC-Budget** (wie viel Platz für Dünger bleibt) und die **CalMag-Korrektur** (ob zusätzliches Calcium/Magnesium nötig ist). Ungenaue Werte führen zu falschen Düngeempfehlungen — im schlimmsten Fall zu Über- oder Unterdüngung.

### Schritt 5: Speichern

Klicke auf **Speichern**. Die Site erscheint nun in der Übersicht.

!!! info "Für technische Nutzer"
    Neben Name, Typ, GPS-Koordinaten, Klimazone, Fläche und Zeitzone kennt eine Site im Hintergrund auch durchschnittliche Frost-Termine (letzter Frost im Frühjahr, erster Frost im Herbst, Datum der Eisheiligen). Diese Einstellung ist derzeit nur über die API verfügbar — im Site-Formular ist sie noch nicht editierbar. Der Nutzen: Ist für eine Site eine GPS-Position hinterlegt, kann Kamerplanter daraus die tatsächliche Tageslänge an deinem Standort berechnen und automatische, photoperiodisch ausgelöste Phasenübergänge (z. B. den Blüteeinsatz bei Freiland-Kurztagspflanzen) korrekt auswerten — siehe [Automatische Phasenübergänge](growth-phases.md#automatische-phasenübergänge). Frost-Termine fließen zusätzlich in den Aussaatkalender ein.

!!! tip "GPS-Koordinaten ermöglichen Wetterquellen"
    Für Sites vom Typ Außenbereich, Gewächshaus oder Balkon schaltet eine hinterlegte GPS-Position zusätzlich den Abschnitt **Wetterquelle** auf der Standort-Detailseite frei — dort wählst und priorisierst du öffentliche Wetterdienste oder eine Home-Assistant-Quelle, siehe [Wetterquellen je Standort](weather-sources.md).

---

## Locations und Slots anlegen

### Location innerhalb einer Site anlegen

1. Öffne eine Site durch Klick auf ihren Namen.
2. Im Tab **Standorte** siehst du den Standortbaum.
3. Klicke auf **Location hinzufügen**.
4. Wähle einen **Location-Typ** aus der Liste (siehe Tabelle unten).
5. Vergib einen eindeutigen Namen.
6. Optional: Wähle eine übergeordnete Location (für verschachtelte Strukturen).

**Verfügbare Location-Typen:**

<!-- Quelle: src/backend/app/migrations/seed_data/location_types.yaml -->

| Typ | Innenbereich? | Beschreibung |
|-----|:---:|-------------|
| Zone | — | Freie Unterteilung ohne feste Zuordnung, z.B. für grobe Bereichsplanung |
| Zuhause | Nein | Oberste Ebene für den privaten Wohnbereich |
| Garten | Nein | Gesamter Außenbereich |
| Gewächshaus | Nein | Glashaus oder Folientunnel |
| Gebäude | Ja | Gebäude als Bereich, z.B. Nebengebäude oder Schuppen |
| Zimmer | Ja | Ganzes Zimmer als Bereich |
| Balkon | Nein | Balkon |
| Terrasse | Nein | Terrasse |
| Grow-Zelt | Ja | Abgeschlossenes Growzelt mit kontrolliertem Klima |
| Beet | Nein | Boden- oder Hochbeet im Freien |
| Regal | Ja | Regal oder Shelving-System |
| Topf-/Container-Gruppe | Nein | Gruppierung mehrerer Töpfe oder Container an einem Ort |

!!! info "Für technische Nutzer"
    Die zwölf oben aufgeführten Typen sind vorinstallierte System-Typen. Kamerplanter unterstützt intern bereits eigene, zusätzliche Location-Typen. Diese Einstellung ist derzeit nur über die API verfügbar — eine eigene Verwaltungsseite in der Oberfläche gibt es noch nicht.

### Slot innerhalb einer Location anlegen

1. Öffne eine Location durch Klick auf ihren Namen im Baum.
2. Klicke auf **Slot hinzufügen**.
3. Kamerplanter schlägt automatisch eine **Stellplatz-ID** im Format `BEREICH_POSITION` vor (z.B. "TENT01_A1"); du kannst sie anpassen, sie wird beim Speichern automatisch in Großbuchstaben umgewandelt.
4. Trage die **Kapazität** ein — die maximale Anzahl Pflanzen, die dieser Stellplatz gleichzeitig aufnehmen kann (1–20, Standard: 1).

---

## Substrate verwalten

Ein Substrat beschreibt das Wachstumsmedium, in dem deine Pflanzen wurzeln. Kamerplanter unterscheidet 14 Substrat-Typen, unterstützt eigene Substrat-Mischungen und verwaltet konkrete **Chargen** eines Substrats (z.B. "Bio-Erde, angemischt März 2026") getrennt vom allgemeinen Substrat-Typ.

### Neues Substrat anlegen

1. Navigiere zu **Standorte → Substrate**.
2. Klicke auf **Substrat hinzufügen**.
3. Wähle den **Substrat-Typ** (siehe Tabelle).
4. Vergib einen Namen (Deutsch und Englisch, z.B. "Bio-Erde" / "Organic Soil").
5. Optional: Trage Basis-pH, Basis-EC, Wasserretention, Luftporosität und Pufferkapazität ein.

**Verfügbare Substrat-Typen:**

<!-- Quelle: src/backend/app/common/enums.py (SubstrateType) -->

| Typ | Beschreibung |
|-----|-------------|
| Erde | Standard-Gartenerde oder Blumenerde |
| Kokos | Kokos-Substrat (Coco Coir) |
| Blähton | Tongranulat, meist für Hydro-Systeme (z.B. Zeer/Hydrokultur) |
| Perlit | Vulkanisches Mineral, meist als Drainage-Beimischung |
| Lebende Erde | Erde mit aktivem Mikrobiom (Living Soil) |
| Torf | Torfbasiertes Substrat |
| Steinwollmatte | Mineralwolle-Matte für Hydroponik |
| Steinwollwürfel | Kleiner Mineralwolle-Anzuchtwürfel für Stecklinge und Keimung |
| Vermiculit | Blähmineral, meist zur Beimischung oder Anzucht |
| Kein Substrat | Für substratlose Systeme (z.B. reine Aeroponik) |
| Orchideenrinde | Grobe Rindenstücke für Epiphyten |
| PON-Mineralsubstrat | Mineralisches Semi-Hydro-Substrat (LECA-ähnlich) |
| Sphagnum-Moos | Torfmoos, häufig für Orchideen und Fleischfressende Pflanzen |
| Hydrolösung | Reine Nährlösung ohne festes Substrat (z.B. DWC) |

!!! warning "Kokos und CalMag"
    Kokos-Substrat bindet Calcium und Magnesium. Bei Kokos-Substraten wird CalMag grundsätzlich empfohlen, auch bei hartem Leitungswasser. Kamerplanter weist dich darauf hin, wenn ein Nährstoffplan für Kokos-Pflanzen kein CalMag enthält.

### Eigene Substrat-Mischungen anlegen

Statt einen einzelnen Substrat-Typ zu verwenden, kannst du eigene Mischungen aus mehreren bereits angelegten Substraten zusammenstellen (z.B. 70 % Erde + 20 % Perlit + 10 % Vermiculit):

1. Klicke in der Substrat-Übersicht auf **Mischung anlegen**.
2. Wähle mindestens zwei vorhandene Substrate aus (reine Mischungen können nicht selbst wieder gemischt werden).
3. Verteile die Anteile in Prozent — mit **Gleichmäßig verteilen** teilst du sie automatisch gleich auf. Die Summe muss genau 100 % ergeben.
4. Klicke auf **Vorschau**, um die berechneten Eigenschaften der Mischung zu sehen (Basis-pH, Basis-EC, Wasserretention, Luftporosität u.a. — jeweils als gewichteter Mittelwert der Komponenten).
5. Vergib einen Namen (Deutsch/Englisch) und klicke auf **Speichern**.

### Substratchargen (Wiederverwendung, Zuweisung)

Eine **Charge** ist eine konkrete, physische Menge eines Substrats mit eigenem Verlauf — zum Beispiel ein bestimmter Sack Erde, der über mehrere Anbauzyklen wiederverwendet wird. Zu jeder Charge erfasst Kamerplanter:

| Feld | Beschreibung |
|------|-------------|
| Chargen-ID | Frei wählbare Bezeichnung, z.B. "ERDE-2026-03" |
| Volumen (Liter) | Menge dieser Charge |
| Angemischt am | Datum der Herstellung/des Kaufs |
| Zuletzt aufgefrischt | Datum der letzten Nährstoff-/pH-Auffrischung |
| Zyklen genutzt | Wie oft die Charge bereits für einen Anbauzyklus verwendet wurde |
| Aktueller pH / EC | Letzte gemessene Werte inklusive Verlauf |

**Zur Wiederverwendung vorbereiten:** Nach Abschluss eines Anbauzyklus prüfst du, ob eine Charge erneut einsetzbar ist:

1. Öffne die Substratcharge in der Detailansicht.
2. Klicke auf **Wiederverwendbarkeit prüfen**. Das System vergleicht den bisherigen Verlauf mit den zulässigen Wiederverwendungs-Zyklen des Substrat-Typs.
3. Ist eine Aufbereitung nötig, zeigt Kamerplanter die notwendigen Schritte (z.B. Spülen, Nachdüngen) inklusive geschätzter Dauer und dem frühestmöglichen Datum, ab dem die Charge wieder einsatzbereit ist.
4. Klicke auf **Wiederverwendung vorbereiten**, um den Aufbereitungsschritt zu protokollieren.

!!! info "Für technische Nutzer"
    Kamerplanter kann eine Substratcharge technisch bereits einem Slot zuordnen. Diese Einstellung ist derzeit nur über die API verfügbar — eine Oberfläche dafür gibt es noch nicht. Bis dahin trägst du den Substrat-Bezug beim Anlegen eines Pflanzdurchlaufs im Feld **Substratcharge** ein (siehe [Pflanzdurchläufe](planting-runs.md)).

---

## Tipps für die Standortstruktur

!!! example "Beispiel: Balkon-Gärtner"
    - Site: "Wohnung Berlin"
    - Location: "Südbalkon" (Typ: Balkon)
    - Location: "Küche" (Typ: Zimmer)
    - Slots: "Topf Tomate", "Topf Basilikum", "Topf Petersilie"

!!! example "Beispiel: Indoor-Grower mit zwei Zelten"
    - Site: "Indoor-Garden"
    - Location: "Vegi-Zelt" (Typ: Grow-Zelt)
      - Location: "Ebene 1"
        - Slots: "Topf 1" bis "Topf 6"
    - Location: "Blüte-Zelt" (Typ: Grow-Zelt)
      - Slots: "Platz 1" bis "Platz 9"

---

## Häufige Fragen

??? question "Kann ich einen Slot in eine andere Location verschieben?"
    Ja. Öffne den Slot, klicke auf **Bearbeiten** und wähle eine neue übergeordnete Location. Eine laufende Pflanze bleibt dabei mit dem Slot verbunden.

??? question "Was passiert, wenn ich eine Location lösche, die noch Pflanzen enthält?"
    Kamerplanter lässt das Löschen nicht zu, solange noch Pflanzen oder Slots in der Location vorhanden sind. Entferne zuerst alle Pflanzen und Slots.

??? question "Kann ich die Standorthierarchie auch flacher halten?"
    Ja. Du kannst Pflanzen direkt einer Location zuweisen, ohne zwingend Slots zu erstellen. Slots sind sinnvoll, wenn du viele Pflanzen in einem Bereich präzise verfolgen möchtest.

??? question "Wie hinterlege ich meinen eigenen Substrat-Mix?"
    Nutze die Funktion **Mischung anlegen** in der Substrat-Übersicht (siehe [Eigene Substrat-Mischungen anlegen](#eigene-substrat-mischungen-anlegen)). Dort kombinierst du mehrere vorhandene Substrate mit prozentualen Anteilen — Kamerplanter berechnet die resultierenden Eigenschaften automatisch.

---

## Siehe auch

- [Tankmanagement](tanks.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Dünge-Logik](fertilization.md)
- [Wachstumsphasen](growth-phases.md)
- [Wetterquellen je Standort](weather-sources.md)
