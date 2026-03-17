# Standorte und Substrate

Standorte beschreiben, wo Ihre Pflanzen wachsen — vom gesamten Garten bis zum einzelnen Topfplatz. Substrate definieren das Wachstumsmedium. Beide Konzepte bilden die räumliche Grundlage für alle anderen Funktionen in Kamerplanter.

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

**Site** ist Ihre übergeordnete Anlage — zum Beispiel "Mein Garten" oder "Wohnung Berlin". Auf Site-Ebene hinterlegen Sie die Wasserquelle, die Klimazone und die Gesamtfläche.

**Location** ist ein konkreter Bereich innerhalb der Site — zum Beispiel "Growzelt A", "Hochbeet 1" oder "Südbalkon". Locations können auch weitere Locations enthalten: Sie können "Haus" → "Wohnzimmer" → "Fensterbank Süd" abbilden.

**Slot** ist ein einzelner Pflanzplatz — zum Beispiel "Topf 3" oder "Reihe 2, Position 4". Slots sind immer die unterste Ebene und können genau einer Pflanze zugeordnet werden.

!!! tip "Tipp: Wie tief strukturieren?"
    Für einfache Setups (Balkon, ein Growzelt) reicht es, Sites und Locations anzulegen. Slots sind nützlich, wenn Sie viele Pflanzen im gleichen Bereich haben und jeden Platz einzeln verfolgen möchten.

---

## Eine neue Site anlegen

### Schritt 1: Zur Standortverwaltung navigieren

Klicken Sie in der linken Navigation auf **Standorte**. Die Übersichtsseite zeigt alle Ihre Sites mit einer Karte und einer Listensicht.

### Schritt 2: Neue Site erstellen

Klicken Sie auf **Site hinzufügen** (oben rechts). Ein Formular öffnet sich.

### Schritt 3: Grunddaten ausfüllen

Füllen Sie folgende Felder aus:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Name der Site | "Mein Indoor-Garten" |
| Klimazone | Standort-Klimazone | "Cfb (Gemäßigt ozeanisch)" |
| Gesamtfläche (m²) | Gesamte Anbaufläche | 12 |
| Zeitzone | Zeitzone für Aufgaben und Kalender | "Europe/Berlin" |

!!! note "Erfahrungsstufen"
    Je nach Ihrer Erfahrungsstufe (Einsteiger / Mittelstufe / Experte, einstellbar in den Kontoeinstellungen) sehen Sie mehr oder weniger Felder. Experten sehen zusätzlich Felder für die Wasserquellen-Konfiguration, GPS-Koordinaten und die Frostdaten.

### Schritt 4: Wasserquelle konfigurieren (optional, ab Mittelstufe)

Wenn Sie Ihr Leitungswasser oder eine Umkehrosmose-Anlage nutzen, hinterlegen Sie die Wasserwerte. Das System berechnet daraus später automatisch Ihr EC-Budget und CalMag-Bedarf:

- **Leitungswasser-EC** (mS/cm): Typisch 0,3–0,8 in Deutschland
- **Leitungswasser-pH**: Typisch 7,0–8,0
- **Hat RO-Anlage**: Aktivieren Sie dies, wenn Sie eine Umkehrosmose-Anlage haben

!!! tip "Wasserwerte herausfinden"
    Den EC-Wert Ihres Leitungswassers finden Sie auf der Website Ihres Wasserversorgers oder Sie messen ihn selbst mit einem günstigen EC-Messgerät.

### Schritt 5: Speichern

Klicken Sie auf **Speichern**. Die Site erscheint nun in der Übersicht.

---

## Locations und Slots anlegen

### Location innerhalb einer Site anlegen

1. Öffnen Sie eine Site durch Klick auf ihren Namen.
2. Im Tab **Standorte** sehen Sie den Standortbaum.
3. Klicken Sie auf **Location hinzufügen**.
4. Wählen Sie einen **Location-Typ** aus der Liste (siehe Tabelle unten).
5. Vergeben Sie einen eindeutigen Namen.
6. Optional: Wählen Sie eine übergeordnete Location (für verschachtelte Strukturen).

**Verfügbare Location-Typen:**

| Typ | Beschreibung |
|-----|-------------|
| Growzelt | Abgeschlossenes Growzelt mit kontrolliertem Klima |
| Gewächshaus | Glashaus oder Folientunnel |
| Hochbeet | Erhöhtes Beet im Freien |
| Freilandbeet | Bodenebenes Beet im Garten |
| Balkon | Balkon oder Terrasse |
| Fensterbank | Innenfensterbank |
| Zimmer | Ganzes Zimmer als Bereich |
| Hydroponik-System | NFT, DWC, Aeroponik oder vergleichbar |
| Regal | Regal oder Shelving-System |
| Sonstiges | Benutzerdefinierter Typ |

### Slot innerhalb einer Location anlegen

1. Öffnen Sie eine Location durch Klick auf ihren Namen im Baum.
2. Klicken Sie auf **Slot hinzufügen**.
3. Geben Sie eine Bezeichnung ein (z.B. "Topf 1" oder "Reihe A, Platz 3").
4. Optional: Tragen Sie die Kapazität (Topfgröße in Liter) ein.

---

## Substrate verwalten

Ein Substrat beschreibt das Wachstumsmedium, in dem Ihre Pflanzen wurzeln. Kamerplanter unterscheidet verschiedene Substrat-Typen und ermöglicht die Verwaltung von Substrat-Chargen.

### Neues Substrat anlegen

1. Navigieren Sie zu **Standorte → Substrate**.
2. Klicken Sie auf **Substrat hinzufügen**.
3. Wählen Sie den **Substrat-Typ** (siehe Tabelle).
4. Vergeben Sie einen Namen (z.B. "Bio-Erde Charge März 2026").
5. Optional: Tragen Sie pH-Bereich, EC-Wert und Kapazität ein.

**Verfügbare Substrat-Typen:**

| Typ | Beschreibung | Empfohlener Einsatz |
|-----|-------------|-------------------|
| Erde (SOIL) | Standard-Gartenerde oder Blumenerde | Freiland, Topfpflanzen |
| Bio-Erde | Organisch angereicherte Erde | Zimmerpflanzen, Kräuter |
| Living Soil | Lebende Erde mit Mikrobiom | Biologischer Anbau |
| Coco Coir | Kokos-Substrat | Indoor-Kulturen, Hydroponik-ähnlich |
| Perlite | Vulkanisches Mineral (Drainage) | Immer als Beimischung |
| Rockwool-Platten | Mineralwolle für Hydroponik | Hydro-Systeme, Anzucht |
| Rockwool-Plugs | Kleine Anzuchtblöcke | Stecklinge, Keimung |
| Hochbeet-Mix | Spezielle Hochbeeterde | Hochbeete |
| Torf | Torfbasiert (nicht empfohlen) | Historische Verwendung |
| Vermiculite | Blähmineral | Anzucht, Beimischung |
| PON Mineral | LECA/Blähtongranulat | Semi-Hydroponik |
| Sphagnum | Torfmoos | Orchideen, Epiphyten |

!!! warning "Coco Coir und CalMag"
    Coco Coir bindet Calcium und Magnesium. Bei Coco-Substraten wird CalMag grundsätzlich empfohlen, auch bei hartem Leitungswasser. Kamerplanter weist Sie darauf hin, wenn ein Nährstoffplan für Coco-Pflanzen kein CalMag enthält.

### Substrat einem Slot zuweisen

1. Öffnen Sie den gewünschten Slot.
2. Klicken Sie auf **Substrat zuweisen**.
3. Wählen Sie ein vorhandenes Substrat aus der Liste.
4. Das Substrat ist nun diesem Slot zugeordnet.

### Substrat zur Wiederverwendung vorbereiten

Nach Abschluss eines Anbauzyklus können Sie ein Substrat für die erneute Verwendung vorbereiten:

1. Öffnen Sie das Substrat in der Detailansicht.
2. Klicken Sie auf **Zur Wiederverwendung vorbereiten**.
3. Das System prüft den pH-Standardabweichung und die EC-Drift der bisherigen Nutzung.
4. Bei zu großer Drift erscheint eine Warnung — in diesem Fall empfiehlt sich neues Substrat.

!!! note "Einweg-Substrate"
    Rockwool-Platten und -Plugs sind Einwegsubstrate und werden nach einem Zyklus nicht zur Wiederverwendung angeboten.

---

## Tipps für die Standortstruktur

!!! example "Beispiel: Balkon-Gärtner"
    - Site: "Wohnung Berlin"
    - Location: "Südbalkon" (Typ: Balkon)
    - Location: "Fensterbank Küche" (Typ: Fensterbank)
    - Slots: "Topf Tomate", "Topf Basilikum", "Topf Petersilie"

!!! example "Beispiel: Indoor-Grower mit zwei Zelten"
    - Site: "Indoor-Garden"
    - Location: "Vegi-Zelt" (Typ: Growzelt)
      - Location: "Ebene 1"
        - Slots: "Topf 1" bis "Topf 6"
    - Location: "Blüte-Zelt" (Typ: Growzelt)
      - Slots: "Platz 1" bis "Platz 9"

---

## Häufige Fragen

??? question "Kann ich einen Slot in eine andere Location verschieben?"
    Ja. Öffnen Sie den Slot, klicken Sie auf **Bearbeiten** und wählen Sie eine neue übergeordnete Location. Eine laufende Pflanze bleibt dabei mit dem Slot verbunden.

??? question "Was passiert, wenn ich eine Location lösche, die noch Pflanzen enthält?"
    Kamerplanter lässt das Löschen nicht zu, solange noch Pflanzen oder Slots in der Location vorhanden sind. Entfernen Sie zuerst alle Pflanzen und Slots.

??? question "Kann ich die Standorthierarchie auch flacher halten?"
    Ja. Sie können Pflanzen direkt einer Location zuweisen, ohne zwingend Slots zu erstellen. Slots sind sinnvoll, wenn Sie viele Pflanzen in einem Bereich präzise verfolgen möchten.

??? question "Wie hinterlege ich meinen eigenen Substrat-Mix?"
    Wählen Sie beim Anlegen des Substrats den am besten passenden Typ und beschreiben Sie die Mischung im Notiz-Feld. Für Experten stehen zusätzliche Felder für pH-Bereich, Leitfähigkeit und Bewässerungsstrategie zur Verfügung.

---

## Siehe auch

- [Tankmanagement](tanks.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Dünge-Logik](fertilization.md)
