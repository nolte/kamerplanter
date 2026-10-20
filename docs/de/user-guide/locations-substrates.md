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
| Beet | Nein | Bodenbeet im Freien |
| Hochbeet | Nein | Erhöhtes, eingefasstes Beet |
| Gewächshausbeet | Nein | Beet innerhalb eines Gewächshauses |
| Frühbeet | Nein | Abgedeckter Kasten für die frühe Anzucht |
| Pflanzkübel / Topf-Gruppe | Nein | Beweglicher Kübel oder eine Gruppe von Töpfen, die wie ein Beet geplant wird |
| Regal | Ja | Regal oder Shelving-System |
| Topf-/Container-Gruppe | Nein | Gruppierung mehrerer Töpfe oder Container an einem Ort |

!!! info "Für technische Nutzer"
    Die sechzehn oben aufgeführten Typen sind vorinstallierte System-Typen. Kamerplanter unterstützt intern bereits eigene, zusätzliche Location-Typen. Diese Einstellung ist derzeit nur über die API verfügbar — eine eigene Verwaltungsseite in der Oberfläche gibt es noch nicht.

### Frostexposition einer Location festlegen {#frostexposition-einer-location-festlegen}

Ob eine Pflanze als frostexponiert gilt, richtet sich normalerweise nach dem **Typ der übergeordneten Site**: Außenbereich, Gewächshaus und Balkon gelten automatisch als frostexponiert, Innenbereich, Fensterbrett und Growzelt dagegen nicht (siehe [Verfügbare Site-Typen](#eine-neue-site-anlegen)). Für jede einzelne Location innerhalb einer Site kannst du diese Einstufung im Feld **Frostexposition** gezielt übersteuern — das ist z. B. nützlich, wenn eine einzelne Location abweichend vom Rest der Site liegt.

Im Formular zum Anlegen oder Bearbeiten einer Location findest du dazu drei Optionen:

| Option | Wirkung |
|--------|---------|
| Vom Standort erben (Standard) | Übernimmt die Einstufung des übergeordneten Site-Typs — entspricht dem bisherigen Verhalten ohne Übersteuerung. |
| Außenbereich – frostexponiert | Die Location gilt unabhängig vom Site-Typ als frostexponiert. |
| Innen – geschützt | Die Location gilt als geschützt, selbst wenn die übergeordnete Site als Außenbereich, Gewächshaus oder Balkon angelegt ist. |

Die Frostexposition einer Location bestimmt sowohl, ob Pflanzen an dieser Location einen [Überwinterungsplan](overwintering.md) erhalten, als auch, ob sie von der [Saison-Automatik](season-automation.md) erfasst werden — Winter-Einzug, Dormanz-Pflege und Frühjahrs-Rückholung. Beides folgt konsistent derselben Einstufung: Eine Location, die als frostexponiert gilt, bekommt die volle Automatik, auch wenn sie auf einem ansonsten als Innenbereich angelegten Standort liegt; eine als geschützt eingestufte Location wird nicht in Winterruhe versetzt, selbst wenn andere Locations desselben Standorts frostexponiert sind. <!-- REQ-047 -->

!!! example "Balkon unter einer beheizten Wohnung"
    Liegt dein Balkon unter einer anderen, beheizten Wohnung, ist er oft spürbar wärmer als ein freistehender Balkon. Trotzdem markiert Kamerplanter ihn standardmäßig als frostexponiert, sobald die Site als Typ „Balkon" angelegt ist. Möchtest du das für diese eine Location übersteuern, öffnest du sie und wählst bei **Frostexposition** die Option **„Innen – geschützt"** — Pflanzen an dieser Location bekommen dann keinen Überwinterungsplan mehr, auch wenn andere Bereiche derselben Site weiterhin als frostexponiert gelten. Umgekehrt kannst du eine besonders exponierte Location (z. B. eine freistehende Fensterbank in einem unbeheizten Treppenhaus) auch dann als frostexponiert markieren, wenn die übergeordnete Site als Innenbereich angelegt wurde.

!!! tip "Übersteuerung jederzeit rückgängig machen"
    Du kannst beim Bearbeiten einer Location jederzeit zwischen allen drei Optionen wechseln — auch zurück auf **„Vom Standort erben"**. Das entfernt die Übersteuerung vollständig; die Location übernimmt danach wieder automatisch die Einstufung des übergeordneten Site-Typs.

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

## Beetansicht {#beetansicht}

Öffnest du einen Standort, dessen Typ ein Beet ist (Beet, Hochbeet, Gewächshausbeet, Frühbeet oder Pflanzkübel), erscheint statt der normalen Standortseite die Beetansicht. Sie bündelt alles Wichtige zu einem Beet an einer Stelle.

### Übersicht oberhalb der Tabs

Über den Tabs siehst du auf einen Blick: Fläche, Typ, Status, Bodentyp, Sonnenexposition, aktive Pflanzen, offene Aufgaben, letzte Pflege, nächste Fälligkeit und wer für das Beet zuständig ist. Mit der **Saison-Auswahl** wechselst du das Jahr; es steht in der Adresse als `?year=`.

!!! warning "Noch nicht implementiert"
    Die Anzeige der Vorjahreskultur in der Übersicht ist noch nicht umgesetzt. Bis dahin zeigt Kamerplanter dort eine Platzhalterzeile. Auch **Beet räumen** wird erst in einer späteren Version verfügbar sein.

### Die Tabs

Der aktive Tab steht in der Adresse (z. B. `#plan` oder `#soil`), sodass du Links auf einen bestimmten Tab teilen kannst.

| Tab | Inhalt |
|-----|--------|
| Plan | Beetrahmen mit Plätzen, Reihen bzw. Zonen und Pflanzenmarkern. Tippst du auf eine Pflanze, bietet das Beet **Position korrigieren** und **Umpflanzen nach …** an. Zum Bearbeiten des Beetrahmens wechselst du über **Im Gartenplan öffnen** in den Gartenplan. |
| Pflege | Offene und überfällige Aufgaben des Beets und seiner Pflanzen, Erledigen, Vorschläge und Pflegeprotokoll (siehe [Pflege am Beet](#pflege-am-beet)). |
| Pflanzung | Geplante und stehende Pflanzen des Beets, die Schaltfläche **Bepflanzen** und die Aktionen an einer Pflanze (siehe [Beet bepflanzen](#beet-bepflanzen)). |
| Historie | Zeitstrahl, was in den Jahren zuvor im Beet stand, und die Liste aller Pflegeeinträge und Pflanzungen (siehe [Historie des Beets](#historie-des-beets)). |
| Boden | Bodenprofil des Beets (siehe unten). |
| Stammdaten | Die bisherige Standortseite, unverändert. |

### Beet bepflanzen {#beet-bepflanzen}

Im Tab **Pflanzung** öffnest du mit **Bepflanzen** den Pflanzdialog. Er ist ab der Rolle „grower" verfügbar und setzt voraus, dass das Beet im Gartenplan eingezeichnet ist. Das Beet darf nicht stillgelegt sein.

1. **Art und Sorte wählen.** Deine Favoriten stehen oben. Unter der Auswahl siehst du Endhöhe und Endbreite der Art und ob sie eine Rankhilfe braucht.
2. **Hinweise lesen.** Sobald du eine Art gewählt hast, prüft Kamerplanter die **Fruchtfolge** und die **Nachbarn** im Beet. Jeder Hinweis hat eine Stärke (unauffällig, Info, Warnung, kritisch) und einen Grund, zum Beispiel „Die Familie Solanaceae stand vor 1 Jahr(en) in diesem Beet. Die Anbaupause beträgt 4 Jahre". Ein Hinweis sperrt nichts. Dazu kommt der Hinweis **Standort**, siehe [Sonne und Schatten am Beet](#sonne-und-schatten-am-beet).
3. **Anzahl und Anordnung wählen.** Entweder **So viele wie passen** oder eine feste Anzahl. Die Anordnung ist **Raster**, **Reihen**, **Versetzt**, **Fläche** (für Direktsaat) oder **Freie Positionen** (für Gehölze).
4. **Abstände prüfen.** Kamerplanter füllt den Pflanzabstand und den Reihenabstand aus dem Steckbrief der Art vor und schreibt dazu, woher der Wert kommt. Fehlt er dort, nimmt Kamerplanter den Wert, den du zuletzt für diese Art verwendet hast. Gibt es auch den nicht, bleibt das Feld leer, und du trägst den Abstand selbst ein. Unter **Mehr Optionen** stellst du Reihenrichtung und Randabstände ein.
5. **Vorschau ansehen.** Das Beet zeigt sofort, wo die Pflanzen stehen würden, und darunter steht, wie viele es sind und wie viele höchstens passen. Der Server bestätigt die Zahl kurz darauf. Weicht seine Antwort ab, gilt seine.
6. **Planen oder erfassen.** **Pflanzung planen** legt einen geplanten Durchlauf an und reserviert die Plätze ab dem Pflanzdatum. Hast du schon gepflanzt, schaltest du **Ich habe schon gepflanzt** ein. Dann entstehen die Pflanzen sofort auf den berechneten Positionen.

**Mehrere Arten (Mischkultur).** Mit **Weitere Art hinzufügen** nimmst du bis zu vier Arten in dieselbe Pflanzung auf. Stehen alle in Reihen, verteilt Kamerplanter die Reihen **abwechselnd** auf die Arten, etwa Möhre in jeder zweiten Reihe und Zwiebel dazwischen. Die Reihen- und Randeinstellungen von Art 1 gelten dann für alle, nur der Abstand in der Reihe bleibt je Art. Verträgt sich eine Kombination laut Kamerplanter nicht, erscheint ein Hinweis.

**Freie Positionen.** Wählst du **Freie Positionen**, tippst du die Pflanzplätze ins Beet. Ziehen verschiebt einen Platz, eine Nummer unter der Vorschau löscht ihn. Liegen zwei Plätze näher beieinander als der Mindestabstand, bekommen beide einen **gelben Ring**. Das ist ein Hinweis, du kannst trotzdem pflanzen.

**Trotzdem pflanzen.** Ab der Stärke **Warnung** schaltest du **Trotzdem pflanzen** ein und nennst einen **Grund**. Der Grund wird an der Pflanzung gespeichert, das Beet trägt danach in der Übersicht den Hinweis **Fruchtfolge-Hinweis**, solange die Pflanzung läuft.

**Topfvolumen.** Bei Arten mit empfohlenem Topfvolumen kannst du unter **Mehr Optionen** das Volumen deines Topfs eintragen. Ist er kleiner als empfohlen, warnt Kamerplanter.

**Position korrigieren.** An einer stehenden Pflanze (im Tab **Pflanzung** oder nach einem Tipp im Plan) verschiebst du mit **Position korrigieren** den Platz: per Ziehen, mit den Pfeilschaltflächen in 1-cm-Schritten oder durch Eintippen der Koordinaten. Das Pflegeprotokoll hält die Korrektur mit der Pflanze fest. Pflanzen in einer Fläche haben keinen einzelnen Platz und lassen sich nicht verschieben.

**Umpflanzen nach …** In ein anderes Beet verschiebst du nicht per Ziehen. **Umpflanzen nach …** legt die Aufgabe „Umpflanzen" für die Pflanze an, mit dem Zielbeet im Text. Du erledigst sie, sobald du die Pflanze versetzt hast.

!!! warning "Noch nicht implementiert"
    Der Hinweis **Fruchtfolge-Hinweis** erscheint bisher nur in der Beetübersicht, nicht am Beet im Gartenplan. Er wird nur für Pflanzungen gesetzt, die du trotz eines Hinweises begonnen hast. Geplante, noch leere Plätze zeigt der Plan als gestrichelte Kreise ohne Art und Datum. Die zuletzt verwendeten Abstände merkt sich dein Browser, nicht dein Konto. Ein Beet ohne Platz im Gartenplan lässt sich noch nicht über den Dialog bepflanzen. <!-- REQ-053 GP-FR-132, GP-FR-061 -->

### Pflanzenzustand und Pflanzen-Info {#pflanzenzustand}

Im Tab **Plan** zeigt jede stehende Pflanze ihren Zustand direkt am Marker. Du musst nichts öffnen, um zu sehen, ob du hier etwas tun musst.

- **Scheibe:** Die Farbe zeigt die Wachstumsphase, der Buchstabe die Art. Bei starkem Hineinzoomen zeigt ein Bogen um die Scheibe, wie weit die Phase fortgeschritten ist.
- **Ring:** Er zeigt den Zustand der Pflanzung. Gestrichelt und blass heißt geplant, gepunktet mit Saatpunkten gesät, durchgezogen wächst, ein doppelter Ring bedeutet in Ernte, und ein Kreuz auf leerem Ring bedeutet ausgefallen.
- **Zeichen oben rechts:** Es erscheint höchstens eines, und zwar das dringendste: Dreieck für einen offenen Befund, Sechseck mit Stern für Frostgefahr, Kreis mit Ausrufezeichen für eine überfällige Aufgabe, Tropfen für fälliges Gießen und Quadrat mit Haken für erntereif. Alle weiteren Gründe stehen in der Pflanzen-Info.

Ring und Zeichen unterscheiden sich auch ohne Farbe, du erkennst sie also in Graustufen und bei Rot-Grün-Schwäche. Unter dem Plan erklärt die aufklappbare **Legende** alle Zeichen.

**Pflanzen-Info.** Bleibst du mit der Maus 0,3 Sekunden auf einer Pflanze, erscheint eine Info-Blase mit Art, Sorte, Phase und Fortschritt, Alter, Platz, letzter Pflege, nächster Aufgabe und den Gründen für den Handlungsbedarf. Die Blase bleibt stehen, solange du mit dem Zeiger auf Pflanze oder Blase bleibst, und verschwindet mit **Esc**. Mit der Tastatur erreichst du dieselbe Info über den Fokus auf dem Marker. Auf dem Touchscreen tippst du die Pflanze an, dann öffnet sich unten ein Blatt mit Titelbild und der Schaltfläche **Details**. Das Überfahren löst keine Abfrage aus: Kamerplanter lädt die Zustände aller Pflanzen eines Beets einmal, nach jeder Aktion am Beet und wenn du zum Tab zurückkehrst.

!!! warning "Noch nicht implementiert"
    **Frostgefahr** wird noch nicht angezeigt, sie kommt mit den Standortmerkmalen des Beets. **Fälliges Gießen** entsteht bisher nur aus einer Gießaufgabe, die heute fällig ist, nicht aus dem Bewässerungsbedarf. Die Ebene „Pflanzenzustand" mit dem Filter „nur Pflanzen mit Handlungsbedarf" im Gartenplan folgt später, und geplante Plätze zeigt der Plan weiter ohne Art und Datum. <!-- REQ-053 GP-FR-190, GP-UX-061 -->

### Pflege am Beet {#pflege-am-beet}

Der Tab **Pflege** zeigt alle offenen Aufgaben, die am Beet oder an einer Pflanze in diesem Beet hängen. **Überfällige** Aufgaben stehen oben und sind rot markiert, darunter die übrigen offenen Aufgaben. Wer die Rolle „viewer" hat, sieht die Liste nur lesend.

**Aufgabe erledigen.** Tippe auf **Erledigt**. Es öffnet sich ein kurzer Dialog, der nur nach dem fragt, was zur Art der Aufgabe passt:

| Art der Aufgabe | Felder |
|-----------------|--------|
| Gießen, Spülen | Menge (Liter, Milliliter oder Liter pro m²) und Wasserquelle |
| Düngen | Produkt (aus dem Katalog oder als Freitext), Menge und Einheit |
| Bodenverbesserung, Kalken | Material, Menge und Einheit |
| Mulchen | Material und Dicke in Zentimetern |
| Abdecken, Abdeckung entfernen | Material (Vlies, Netz, Folie, Frostschutz) |
| Ernten | Gewicht |
| Alle anderen | Notiz |

Alle Felder sind freiwillig. Du kannst also auch ohne Eingabe auf **Erledigen** tippen. Unter **Wann** steht standardmäßig der aktuelle Zeitpunkt; du kannst bis zu 365 Tage zurückdatieren, aber nie in die Zukunft. Die Angaben landen im Pflegeprotokoll des Beets. Ein doppelter Tipp zählt nur einmal.

**Rückgängig.** Nach jeder Aktion erscheint acht Sekunden lang eine Meldung mit **Rückgängig**. Damit öffnest du die Aufgabe wieder und nimmst den Protokolleintrag zurück. Als Autor geht das zehn Minuten lang, die Rolle „lead" kann es jederzeit.

**Neue Aufgabe.** Mit **Neue Aufgabe** legst du eine Aufgabe für das Beet an. Wählst du **Jede Pflanze im Beet**, bekommt jede dort stehende Pflanze eine eigene Aufgabe, und die Aufgabe für das ganze Beet entfällt. Die angebotenen Kategorien richten sich nach dem Beet: Spülen, EC-Kontrolle und pH-Korrektur gibt es nur bei Beeten mit Substrat, Anhäufeln, Umbrechen und Kalken nicht bei reinen Substratbeeten, Lüften nur in Gewächshaus, Frühbeet und Zelt.

**Pflege ohne Aufgabe protokollieren.** Mit **Pflege protokollieren** hältst du fest, was du gerade getan hast („Ich habe gemulcht"), ohne dass dafür eine Aufgabe existiert. Pflanzenschutz-Behandlungen protokollierst du hier nicht, sondern über das Pflanzenschutz-Formular; das Pflegeprotokoll ist dafür kein Nachweis.

**Vorschläge.** Aufgaben, die das System vorschlägt, stehen in einem eigenen Abschnitt **Vorschläge** mit dem Grund. Mit **Jetzt erledigen** führst du den Vorschlag aus und erledigst ihn dabei, mit **Verwerfen** lehnst du ihn ab. Ohne deine Entscheidung passiert nichts.

!!! warning "Teilweise verfügbar: Vorschläge"
    Das System erzeugt noch keine Vorschläge. Der Abschnitt ist vorbereitet und erscheint, sobald Vorschläge vorliegen. Ein eigenes **Annehmen** ohne gleichzeitiges Erledigen ist noch nicht möglich. <!-- REQ-053 GP-FR-086 -->

**Mehrere Beete auf einmal.** Auf der Gartenplan-Seite findest du über der Beetliste die Schaltfläche **Aufgaben auf mehreren Beeten erledigen**. Du wählst eine Aufgabenart (zum Beispiel Gießen) und die Beete. Kamerplanter sucht alle offenen Aufgaben dieser Art auf diesen Beeten und ihren Pflanzen und erledigt sie in einem Schritt, mit denselben Angaben für alle. Pro Schritt sind höchstens 200 Aufgaben möglich; was nicht erledigt werden konnte, meldet Kamerplanter dir.

**Aufgaben-Zähler im Plan.** Auf dem Gartenplan zeigt jedes Beet mit offenen Aufgaben eine Zahl in der oberen rechten Ecke, rot, wenn Aufgaben überfällig sind. Ein Tipp darauf öffnet den Pflege-Tab des Beets. Per Tastatur erreichst du ihn über die Schaltfläche **Pflege** in den Eigenschaften des gewählten Beets oder über die Zahl in der Spalte „Offene Aufgaben" der Beetliste. <!-- REQ-053 GP-FR-083, GP-FR-088, GP-FR-089, GP-FR-090 -->

!!! info "Farbe nach Priorität"
    Der Zähler unterscheidet bisher nur „offen" und „überfällig". Eine Färbung nach Priorität der Aufgaben folgt, sobald der Plan die Priorität mitliefert.

### Sonne und Schatten am Beet {#sonne-und-schatten-am-beet}

Wie viel direktes Sonnenlicht ein Beet bekommt, hältst du mit fünf **Kacheln** fest. Jede Kachel zeigt ein Symbol, den Namen und die Definition:

| Kachel | Bedeutung |
|--------|-----------|
| Volle Sonne | mehr als 6 Stunden direktes Sonnenlicht an einem Sommertag |
| Halbschatten | 3–6 Stunden |
| Schatten | 2–3 Stunden |
| Tiefschatten | weniger als 2 Stunden |
| Unbekannt | noch nicht erfasst (Standard) |

Die Stundenwerte folgen der Definition der Royal Horticultural Society, bezogen auf den Hochsommer.

- **In der Beetansicht:** Neben der Sonnenexposition in der Übersicht öffnet **Sonne ändern** die Kacheln. Das geht ab der Rolle „grower".
- **Im Gartenplan:** Wählst du ein Beet, zeigt das Eigenschaften-Feld die Kacheln. Wählst du mehrere Beete (Rahmenauswahl oder Umschalttaste), setzt **Sonne für alle gewählten Beete setzen** den Wert auf einmal. Gesperrte Beete bleiben unverändert. Der Schritt lässt sich mit **Rückgängig** zurücknehmen und gilt erst, wenn du den Plan speicherst.

**Standort-Hinweis beim Bepflanzen.** Im Pflanzdialog vergleicht Kamerplanter die Sonne des Beets mit dem **Lichtbedarf** der Art (Volle Sonne, Halbschatten oder Schatten) und zeigt eine Ampel mit Klartext, etwa „Beet: Schatten — Tomate braucht Vollsonne". Grün heißt gut geeignet, gelb bedingt geeignet, rot schlecht geeignet. Gelb gibt es auch, wenn das Beet eine Stufe schattiger ist als der Bedarf und die Art laut Steckbrief so viel Schatten verträgt; fehlt diese Angabe, steht dort „Toleranz unbekannt". Ist die Sonne des Beets oder der Lichtbedarf der Art nicht erfasst, erscheint kein Hinweis. Der Hinweis sperrt nichts und verlangt keinen Grund.

!!! note "Frostrisiko"
    Das Frostrisiko eines Beets (niedrig, normal, hoch) wird künftig neben der Sonne am Beet gepflegt. Bestehende Angaben aus **Frostexposition** übernimmt Kamerplanter dafür automatisch (ja wird hoch, nein wird niedrig); die Frostexposition selbst bleibt bis dahin die maßgebliche Einstellung. <!-- REQ-053 GP-FR-157, GP-FR-160, GP-FR-162 -->

### Historie des Beets {#historie-des-beets}

Der Tab **Historie** hat zwei Teile: oben den **Zeitstrahl**, darunter die **Liste**.

**Zeitstrahl.** Er zeigt für jedes Jahr, welche Pflanzenfamilien im Beet standen, mindestens die letzten fünf Jahre, bei langen Anbaupausen bis zu zehn. Jede Familie hat eine eigene Farbe und steht immer auch mit ihrem Namen auf dem Eintrag. Gründüngung und Brache sind gekennzeichnet. Der Zeitstrahl ist die Grundlage der Fruchtfolge-Prüfung. Für Töpfe, Zelte und Regale ist diese Prüfung aus; die Historie bleibt trotzdem erhalten.

**Was stand hier?** Wenn du ein Jahr nachtragen willst, in dem du die App noch nicht genutzt hast, tippe bei dem Jahr auf **{Jahr} nachtragen** oder oben auf **Was stand hier?**. Du wählst Jahr, Pflanzenfamilie (oder eine Art, die ihre Familie mitbringt), die Rolle (Hauptkultur, Gründüngung oder Brache) und optional die Saison. Erlaubt sind die letzten zehn Jahre bis zum Vorjahr. Danach erscheint die Meldung mit **Rückgängig**. Einen nachgetragenen Eintrag nimmst du später mit dem **x** am Eintrag zurück, als Autor oder in der Rolle „lead". Er bleibt dann als storniert im Pflegeprotokoll stehen. Beobachter (Rolle „viewer") sehen den Zeitstrahl nur lesend.

**Liste.** Die neuesten Einträge stehen oben, 50 pro Seite; mit **Mehr laden** holst du die nächsten. Die Liste mischt Pflegeeinträge mit Pflanzungsereignissen: Pflanze gesetzt oder entfernt, Durchlauf gestartet oder abgeschlossen. Du kannst nach **Kategorie**, **Zeitraum**, **Pflanze** und **Person** filtern. Korrekturen sind zunächst ausgeblendet: ersetzte Einträge und „Position korrigiert". Mit **Korrekturen anzeigen** siehst du sie wieder, jeweils als „Korrigiert" oder „Korrektur" gekennzeichnet.

!!! info "Wer nach Personen filtern darf"
    Der Personenfilter ist ein Aktivitätsprofil und deshalb eingeschränkt. In den Rollen „viewer" und „grower" filterst du nur nach dir selbst. Die Rolle „lead" und Mitglieder mit dem Verwaltungsbereich `management` können nach jedem Mitglied filtern. Ausgeschiedene Mitglieder erscheinen als „anonymisiert" und sind nicht filterbar.

**Historie aller Beete.** Über **Historie aller Beete** öffnest du die Pflegehistorie des ganzen Mandanten unter `/standorte/historie`. Sie zeigt die letzten 90 Tage, solange du keinen anderen Zeitraum wählst, und kennt dieselben Filter plus **Beet**. Die Pflanze lässt sich wählen, sobald ein Beet gewählt ist.

### Bodenprofil pflegen

Im Tab **Boden** hältst du fest: Füllung, Bodentyp (mit Fingerprobe als Hilfe, falls du den Typ nicht kennst), Drainage, Standortfeuchte, Bedingungen sowie pH-Wert, EC (elektrische Leitfähigkeit) und Humusgehalt. Wählst du optional ein [Substrat](#substrate-verwalten), übernimmt Kamerplanter dessen pH und EC als Vorgabe. Als Betrachter (Rolle „viewer") siehst du das Profil nur lesend.

### Status des Beets ändern

- **Geplant → Aktiv**: möglich ab der Rolle „grower".
- **Stilllegen und Reaktivieren**: nur mit der Rolle „lead".
- Zum Stilllegen brauchst du einen **Grund**, und das Beet darf keine Pflanzen mehr enthalten. Der Grund landet im Pflegeprotokoll.

!!! tip "Tipp: Beet erst leeren, dann stilllegen"
    Sind noch Pflanzen im Beet, lehnt Kamerplanter das Stilllegen ab. Entferne oder ernte sie vorher.

---

## Beetliste im Gartenplan {#beetliste-im-gartenplan}

Unter dem Plan auf der Gartenplan-Seite listet eine Tabelle deine Beete: Name (als Link zur Beetansicht), Typ, Fläche, Status, Zuständige, Pflanzen, offene Aufgaben (mit überfälligen) und nächste Fälligkeit. Stillgelegte Beete sind standardmäßig ausgeblendet. Der Schalter **Meine Beete** filtert auf deine Beete und setzt voraus, dass dir Beete zugewiesen sind.

Klickst du auf eine Zeile oder drückst die Eingabetaste, wird das Beet im Plan ausgewählt und die Ansicht zoomt darauf. Die Zahl in der Spalte „Offene Aufgaben" ist ein Link zum Pflege-Tab des Beets. Ab der Rolle „grower" findest du über der Tabelle die Schaltfläche **Aufgaben auf mehreren Beeten erledigen** (siehe [Pflege am Beet](#pflege-am-beet)).

---

## Feldmodus im Garten {#feldmodus-im-garten}

Der Feldmodus ist für das Smartphone im Beet gedacht: große Schaltflächen (mindestens 64 Pixel), starker Kontrast für Sonnenlicht und nur das, was du draußen brauchst. Auf einem schmalen Bildschirm (unter 600 Pixel Breite) öffnet die Gartenplan-Seite direkt im Feldmodus. Auf jedem Gerät wechselst du über **Feldmodus** bzw. **Planungsmodus** oben auf der Seite; die Adresse trägt dann `?mode=field` bzw. `?mode=plan`.

**Meine Beete · heute fällig.** Der Feldmodus startet mit der Liste deiner Beete. Beete, die dir zugewiesen sind, stehen oben (markiert mit **Meins**), danach Beete mit überfälligen oder heute fälligen Aufgaben, dann die übrigen nach ihrer nächsten Fälligkeit. Überfällig ist eine Aufgabe, deren Fälligkeitstag vor dem heutigen Tag liegt; eine Aufgabe, die heute fällig ist, zählt noch nicht als überfällig. Stillgelegte Beete fehlen in der Liste. Der Tab **Karte** zeigt den Plan ohne Werkzeuge, Raster und Griffe. Mit **Vergrößern**, **Verkleinern** und **Ganzer Plan** änderst du die Ansicht. Tippst du auf ein Beet oder knapp daneben, zoomt die Karte auf das Beet und öffnet es.

**Das Beet-Blatt.** Ein Tipp auf ein Beet öffnet unten ein Blatt mit dem Namen des Beets, dem Schnellprotokoll, den Aufgaben und den Pflanzen. Die Aufgaben stehen in der Reihenfolge **Überfällig**, **Heute fällig**, **Später**. Die Pflanzen siehst du nach Art, Anzahl und Phase gruppiert; die Phasenfarbe hat immer einen schwarzen Rand und den Namen daneben.

- **Erledigt** öffnet den kurzen Dialog mit den freiwilligen Feldern (Menge, Notiz). **Fertig** speichert. Das sind zwei Tipps nach der Beetauswahl. Ein doppelter Tipp zählt nur einmal, und die Schaltflächen bleiben gesperrt, bis die Antwort da ist.
- **Schnellprotokoll:** **Gegossen**, **Gesät** und **Gejätet/Gemulcht** speichern mit einem Tipp einen Pflegeeintrag. **Geerntet** und **Notiz** öffnen das kurze Formular (Menge bzw. Text; für die Notiz kannst du die Spracheingabe deiner Tastatur nutzen). **Gepflanzt** öffnet den Pflanzdialog mit eingeschaltetem **Ich habe schon gepflanzt**; die Pflanzen entstehen sofort. Das geht nur bei einem Beet, das im Plan eingezeichnet ist.
- Nach **Erledigt** und nach jedem Schnellprotokoll siehst du acht Sekunden lang **Rückgängig**. Damit nimmst du den Eintrag zurück.
- **Pflanzen zeigen** listet die einzelnen Pflanzen einer Gruppe. **Position korrigieren** verschiebt eine Pflanze mit den Pfeilen in 10-cm-Schritten; ziehen kannst du den Marker erst, nachdem du ihn eine halbe Sekunde gehalten hast. **Foto** nimmt ein Bild für die Galerie der Pflanze auf.

Löschen, Beet räumen, Export und Import gibt es im Feldmodus nicht – dafür wechselst du in den Planungsmodus. Wer die Rolle „viewer" hat, sieht Aufgaben und Pflanzen nur lesend. Dein Browser merkt sich Mandant, Standort, Tab und Kartenausschnitt, nicht dein Konto; meldet sich jemand anderes auf dem Gerät an, beginnt der Feldmodus für diese Person neu. Zeigt ein gemerkter Kartenausschnitt auf dem aktuellen Bildschirm kaum noch etwas vom Plan – etwa nach dem Drehen des Smartphones –, öffnet die Karte mit dem ganzen Plan.

!!! warning "Noch nicht implementiert"
    Ohne Verbindung zeigt der Feldmodus einen Hinweis und sperrt **Erledigt** und das Schnellprotokoll; Einträge werden noch nicht zwischengespeichert und später gesendet. Fotos hängen vorerst an einer Pflanze, nicht am Beet. Für **Gepflanzt** gibt es kein **Rückgängig**. Die Hilfe per GPS, der QR-Code am Beet und die Ebene „zuletzt gegossen" folgen später. <!-- REQ-053 GP-UX-020…031, GP-FR-149 -->

---

## Im Gartenplan schneller arbeiten {#plan-komfort}

Dieser Abschnitt beschreibt die Hilfen, die dir im Planungsmodus Handarbeit abnehmen.

**Beet aus einer Vorlage.** In der Werkzeugleiste setzt **Aus Vorlage** ein Beet mit einem Klick auf den Plan. Du wählst eine Vorlage, drehst sie bei Bedarf mit **Drehen** in 90-Grad-Schritten und klickst dorthin, wo das Beet liegen soll (bei einem Rechteck die untere linke Ecke, bei einem Kreis der Mittelpunkt). Eine gestrichelte Vorschau zeigt, wo es landet. Ohne Maus setzt **In die Bildmitte setzen** das Beet in die Mitte der Ansicht. Das Beet bekommt Name, Typ, Form und Höhe der Vorlage und wird sofort gespeichert; ungespeicherte Änderungen speichert Kamerplanter vorher mit. Dieser Schritt lässt sich nicht mit **Rückgängig** zurücknehmen. Wenn du das Beet nicht willst, löschst du es. Mit **Esc** oder einem anderen Werkzeug beendest du die Vorlagenwahl.

**Standardgrößen.** Im Dialog **Mit Maßen hinzufügen** füllt eine Standardgröße Form, Maße, Beettyp und Höhe auf einen Schlag aus, zum Beispiel das Hochbeet 1,2 × 2,4 m, das Hochbeet 2 × 1 × 0,8 m oder einen Kübel. Du kannst danach jeden Wert noch ändern. Die Höhe ist optional.

**Als Vorlage speichern.** Ist genau ein Beet gewählt, speichert **Als Vorlage speichern** seine Form, seinen Typ und seine Höhe als eigene Vorlage deines Gartens. Pflanzen, Aufgaben und Notizen gehören nicht dazu, und Pflanzabstände oder Bodenwerte trägt die Vorlage nur, wenn du sie selbst einträgst. Vorlagen legen Gärtner und die Leitung an.

**Einrasten an anderen Objekten.** Beim Verschieben und Zeichnen rastet der Plan an Ecken und Kanten anderer Objekte ein, bevor er am Raster einrastet. Eine grüne Linie zeigt die Kante, an der du gerade bist. Mit der Alt-Taste oder dem Schalter **Einrasten** schaltest du das Einrasten aus. Mit Stift und Finger ist der Fangbereich größer.

**Ausrichten und verteilen.** Hast du mindestens zwei Beete oder Objekte gewählt, richtet **Ausrichten** sie an der linken, rechten, oberen oder unteren Kante oder an der Mitte aus. Ab drei Objekten verteilt der Menüpunkt **Gleichmäßig verteilen** sie mit gleichen Abständen. Gesperrte Objekte bleiben stehen und zählen nicht mit. Jede dieser Aktionen ist ein einziger Schritt für **Rückgängig**.

**Übersichtskarte.** Ist der Garten sehr viel größer als der sichtbare Ausschnitt (mehr als das Vierfache), erscheint unten rechts im Plan eine kleine Karte mit dem Ausschnitt als Rechteck. Ein Klick darauf springt die Ansicht an diese Stelle. Mit der Tastatur bewegst du den Plan weiter mit den Pfeiltasten.

**Automatisch speichern.** Der Schalter **Automatisch speichern** neben **Speichern** sichert deine Änderungen zwei Sekunden nach der letzten Änderung. Er ist standardmäßig aus und gilt nur für dich in diesem Browser. Bei einem Konflikt oder einem abgelehnten Speichern pausiert er und sagt es dir. Im Feldmodus gibt es ihn nicht, dort wird jede Aktion sofort gesendet.

**Mehrfach duplizieren.** Über das Menü **⋯** oder das Kontextmenü legt **Mehrfach duplizieren** mehrere Kopien der gewählten Beete in einer Reihe an: Anzahl, Richtung, Abstand und ein Namensschema wie „Parzelle {n}" (bis zu 100 Kopien). Das ist praktisch für die Parzellen eines Gemeinschaftsgartens. Kamerplanter prüft vorher, ob die Kopien ganz in den Garten passen und ob die Höchstzahl von 500 Beeten und Objekten reicht; wenn nicht, entsteht nichts. Alle Kopien lassen sich mit einem **Rückgängig** zurücknehmen. Pflanzplätze, Pflanzen und Aufgaben werden nicht mitkopiert; ein Pflanzraster legst du danach für jedes Beet an. <!-- REQ-053 GP-FR-025, GP-FR-029, GP-FR-043, GP-FR-044, GP-FR-045, GP-FR-154, GP-UX-004, GP-UX-014 -->

---

## Plan exportieren und Sicherung einspielen {#plan-export-import}

Auf der Gartenplan-Seite öffnet **Export & Import** zwei Dialoge.

**Plan exportieren** gibt es als PDF (Plan im Maßstab zum Ausdrucken), als SVG (Vektorgrafik) und als Sicherung (JSON). Du wählst Papier, Ausrichtung, Maßstab und die Ebenen; eine Vorschau zeigt, was herauskommt. Mit **Automatisch** nimmt Kamerplanter den feinsten Maßstab, der aufs Blatt passt, und schlägt A3 vor, wenn A4 zu grob würde. Passt ein fest gewählter Maßstab nicht aufs Blatt, sagt dir der Dialog das und lässt dich einen gröberen Maßstab oder A3 wählen. Auf dem Handy gibt es nur PDF und Sicherung mit den Standardoptionen. Der Export enthält keine Namen von Mitgliedern und keine Zuweisungen.

Die **Sicherung** enthält Beete, Gartenobjekte, Pflanzplätze, Bodenprofile, Standortmerkmale und die Gartengrenze, aber keine Pflanzen und keine Aufgaben.

**Sicherung einspielen** führt in drei Schritten durch den Import. Das darf nur die Leitung.

1. **Datei wählen:** Die Datei darf höchstens 5 MB groß sein. Kamerplanter prüft sie sofort, ohne etwas zu schreiben.
2. **Prüfbericht:** Du siehst, wie viel angelegt und gelöscht würde, welche Verweise nicht übernommen werden (zum Beispiel eine Bewässerungszone, die es hier nicht gibt) und welche Probleme die Datei hat, etwa überlappende Beete. Bei Problemen geht es nicht weiter.
3. **Modus:** *Hinzufügen* legt die Sicherung zusätzlich zum bestehenden Plan an. *Ersetzen* tauscht den Plan dieses Standorts aus. Dafür tippst du den Namen des Standorts ein. Vorher speichert Kamerplanter den bisherigen Plan als Snapshot im Änderungsprotokoll. Lade dir zur Sicherheit trotzdem vorher eine aktuelle Sicherung herunter.

!!! warning "Beete mit aktiven Pflanzen"
    Ein Beet, in dem eine Pflanze steht, wird nie gelöscht. Solange es solche Beete gibt, weist *Ersetzen* die Datei ab. Wählst du die Option, diese Beete zu behalten, bleiben sie samt den Standorten darüber bestehen, und der Rest wird ersetzt.

Alle Schlüssel werden beim Einspielen neu vergeben. Verknüpfungen zu Home Assistant und zu Aktoren übernimmt Kamerplanter nie; die richtest du danach neu ein. Wer gerade ungespeicherte Änderungen am Plan hat, speichert oder verwirft sie zuerst. Im Feldmodus sind Export und Import ausgeblendet.

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
- [Saison-Automatik](season-automation.md) — wie die Frostexposition einer Location die Jahreszeiten-Automatik steuert
- [Überwinterung](overwintering.md) — der automatisch erstellte Überwinterungsplan je Pflanze
- [Pflanze per Foto identifizieren](plant-identification.md#standort-zuweisen-optional) — Standort, Bereich und Stellplatz direkt beim Anlegen einer Pflanze zuweisen
