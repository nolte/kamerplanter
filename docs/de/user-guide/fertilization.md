# Dünge-Logik

Kamerplanter berechnet präzise Mischverhältnisse für Nährstofflösungen, überwacht dein EC-Budget und erinnert dich an Gießtermine. Ob Hydroponik mit EC-Kalkulation oder organische Freilanddüngung — das System unterstützt beide Ansätze.

---

## Voraussetzungen

- Mindestens ein angelegter Dünger unter **Düngung → Düngemittel**
- Mindestens eine Pflanze mit laufender Wachstumsphase
- Empfohlen: Wasserquelle auf der Site konfiguriert (für automatische EC-Berechnung)

!!! info "Rechner teils nur ab einer bestimmten Erfahrungsstufe sichtbar"
    Einige der unten beschriebenen Rechner-Bereiche (Wasser-Mischer, EC-Budget-Rechner, Ausbringungskanäle) sind erst ab der UI-Erfahrungsstufe **Fortgeschritten** bzw. **Experte** sichtbar. Findest du eine Karte oder einen Abschnitt nicht, prüfe deine Erfahrungsstufe unter **Einstellungen**.

---

## Grundkonzepte verstehen

### Elektrische Leitfähigkeit (EC)

Die elektrische Leitfähigkeit (EC) misst die Konzentration gelöster Nährstoffe im Gießwasser in Millisiemens pro Zentimeter (mS/cm). Sie ist der wichtigste Kennwert für die Nährstoffdosierung:

- **Zu niedrig**: Pflanze hungert, Mangelerscheinungen möglich
- **Optimal**: Pflanze wächst bestmöglich
- **Zu hoch**: Salz-Stress, Wurzelschäden, Nährstoff-Blockaden

Typische EC-Zielbereiche, gegen die Kamerplanter deine berechnete End-EC validiert:

<!-- Quelle: src/backend/app/domain/engines/ec_budget_engine.py EC_MAX_TABLE (REQ-004-A §4.2) -->

| Substrat | Sämling (mS/cm) | Vegetativ (mS/cm) | Blüte (mS/cm) | Ausspülung (mS/cm) |
|----------|-----------------|--------------------|--------------|--------------------|
| Hydroponik | 0,8 – 1,2 | 1,6 – 2,4 | 1,8 – 2,8 | 0,0 – 0,3 |
| Coco | 0,8 – 1,0 | 1,6 – 2,0 | 1,8 – 2,4 | 0,0 – 0,3 |
| Erde | 0,4 – 0,6 | 0,8 – 1,4 | 1,0 – 1,6 | 0,0 – 0,3 |

Diese Werte sind identisch mit der Tabelle im [Nährlösungs-Mischleitfaden](../guides/nutrient-mixing.md#ec-ziel-substrat) — beide werden aus derselben Quelle im Code abgeleitet, damit sie nicht auseinanderdriften.

### EC-Budget

Das **EC-Budget** ist die Differenz zwischen dem EC-Zielwert der aktuellen Phase und dem EC-Wert deines Ausgangswassers. Dieses Budget verteilt Kamerplanter auf die einzelnen Düngerkomponenten.

**Beispiel:**
- EC-Ziel für Blüte: 1,8 mS/cm
- Leitungswasser-EC: 0,4 mS/cm
- EC-Budget für Dünger: 1,4 mS/cm

!!! tip "Osmosewasser hat quasi keine Basis-EC"
    Mit reinem Osmosewasser (EC ≈ 0) steht das gesamte EC-Budget für Dünger zur Verfügung. Das gibt mehr Kontrolle, bedeutet aber auch mehr Verantwortung — insbesondere bei Calcium und Magnesium.

### Alkalinität und pH-Reserve {#alkalinitaet-und-ph-reserve}

Im **Nährstoff-Rechner** (**Düngung → Nährstoff-Berechnungen → Mischprotokoll**) gibst du zusätzlich die **Alkalinität** deines Wassers ein (Karbonathärte, gemessen in ppm CaCO₃ — steht oft auf dem Datenblatt deines Wasserversorgers oder lässt sich mit einem KH-Tröpfchentest ermitteln). Je höher die Alkalinität, desto mehr Säure ist später für die pH-Korrektur nötig.

Aus der Alkalinität berechnet Kamerplanter die **pH-Reserve** — den Teil deines EC-Budgets, der für die spätere pH-Korrektur reserviert bleibt und daher nicht mehr für Dünger zur Verfügung steht:

| Alkalinität | Einstufung | pH-Reserve |
|-------------|-----------|-----------|
| < 50 ppm | Weich | 0,02 mS/cm |
| 50–150 ppm | Mittel | 0,03 mS/cm |
| > 150 ppm | Hart | 0,05 mS/cm |

Das Mischprotokoll zeigt dir nach der Berechnung drei transparente Kennwerte:

- **Netto-EC-Budget** (`ec_net`): Ziel-EC minus Basiswasser-EC — der Spielraum, der grundsätzlich für Dünger zur Verfügung steht.
- **pH-Reserve** (`ec_ph_reserve`): der davon abgezogene, für die pH-Korrektur reservierte Anteil (siehe Tabelle oben).
- **Rezept gültig**: ob die berechnete End-EC innerhalb der Obergrenze für Substrat und Phase liegt.

!!! note "Warum die berechneten Dosierungen manchmal niedriger ausfallen als früher"
    Kamerplanter zieht die pH-Reserve jetzt korrekt vom verfügbaren EC-Budget ab, bevor die Dünger-Dosierungen berechnet werden. Früher blieb dieser Puffer unberücksichtigt, wodurch die End-EC nach der pH-Korrektur das eigentliche Ziel leicht überschreiten konnte. Die neuen ml/L-Werte sind dadurch etwas niedriger, aber genauer — deine Nährlösung trifft ihr EC-Ziel jetzt zuverlässiger.

    Ausführliche Erklärung der gesamten Berechnung: [Nährlösung mischen](../guides/nutrient-mixing.md).

---

## Dünger anlegen

### Schritt 1: Zum Bereich Düngung navigieren

Klicke in der Navigation auf **Düngung → Düngemittel**.

### Schritt 2: Neuen Dünger anlegen

Klicke auf **Dünger hinzufügen**.

### Schritt 3: Dünger-Daten ausfüllen

| Feld | Beschreibung |
|------|-------------|
| Name | Produktname (z.B. "Canna Coco A") |
| Typ | Basisdünger, Supplement, Booster, Biologisch, **CalMag** |
| NPK-Verhältnis | Stickstoff/Phosphor/Kalium-Anteile |
| EC-Beitrag | EC-Erhöhung pro ml/L (steht auf dem Etikett oder Datenblatt) |
| Mischpriorität | Freie Zahl von 1–100. Niedrigere Zahl = früher einmischen (Standardwert: 50) |
| Max. Dosierung (ml/L) | Obergrenze laut Hersteller, ab der Kamerplanter die berechnete Dosis kappt und warnt |
| Tanksicher | Ob der Dünger unverändert im Vorratstank gelagert werden darf |
| Dosierung (ml/L) | Standarddosierung pro Liter Wasser |

!!! tip "Eigener Dünger-Typ CalMag"
    Wähle den Typ **CalMag** für reine Calcium-Magnesium-Supplemente. Kamerplanter berücksichtigt Dünger dieses Typs automatisch an der richtigen Stelle der Mischfolge (siehe unten) und in der CalMag-Bedarfsberechnung.

#### Zusätzliche Felder für organische Freilanddünger

Bei Düngern für den Freilandeinsatz (Kompost, Hornspäne, Pflanzenjauchen) trägst du zusätzlich diese Felder ein — sie werden für die [Flächendosierung](#flaechendosierung-berechnen-naehrstoff-rechner) benötigt:

| Feld | Beschreibung |
|------|-------------|
| Flächen-Dosierung (g/m²) | Ausbringungsmenge in Gramm pro Quadratmeter für Feststoffdünger (z.B. Hornspäne) |
| Flächen-Dosierung (L/m²) | Ausbringungsmenge in Liter pro Quadratmeter für Kompost oder Flüssigdünger |
| Verdünnungsverhältnis | Für Jauchen und Brühen, z.B. "1:10" (1 Teil Konzentrat auf 10 Teile Wasser) |
| Freisetzungsgeschwindigkeit | Sofort, Wochen, Monate oder ganze Saison — wie schnell die Nährstoffe pflanzenverfügbar werden |

!!! danger "Mischfolge beachten — kritisch!"
    Die Reihenfolge beim Mischen von Düngern ist chemisch bedeutsam. Falsche Mischfolge kann zu Ausfällungen führen, die Nährstoffe unverfügbar machen. Kamerplanter sortiert deine ausgewählten Dünger beim Berechnen einer Mischanleitung automatisch nach ihrer **Mischpriorität** (Feld oben) — es gibt keine fest im Code verankerte Reihenfolge.

    **Empfohlene Mischpriorität-Konvention** (frei anpassbar je Dünger):
    1. Wasser mit Zimmertemperatur (18–22 °C)
    2. Silizium-Zusätze (falls verwendet)
    3. **CalMag** (immer vor Sulfaten!)
    4. Basis A (Calcium + Mikronährstoffe)
    5. Basis B (Phosphor + Schwefel + Magnesium)
    6. Weitere Supplemente und Booster
    7. pH-Korrektur (pH Down / pH Up) — immer zuletzt

    Damit diese Reihenfolge tatsächlich eingehalten wird, muss die Mischpriorität jedes Düngers entsprechend gesetzt sein (z. B. CalMag = 10, Basis A = 20, Basis B = 30). Die Vorbelegung neuer Dünger ist 50 — passe sie beim Anlegen an, wenn dein Dünger zuerst oder zuletzt eingemischt werden soll.

---

## Dünger-Bestand, Unverträglichkeiten und Verwendung

Auf der Detailseite eines Düngers (**Düngung → Düngemittel** → Dünger anklicken) findest du drei weitere Bereiche:

### Bestand (Tab „Bestand")

Hier erfasst du einzelne Gebinde/Käufe dieses Düngers:

| Feld | Beschreibung |
|------|-------------|
| Aktuelles Volumen (ml) | Restmenge in der Flasche/im Kanister |
| Kaufdatum | Wann wurde das Gebinde gekauft? |
| Ablaufdatum | Mindesthaltbarkeitsdatum, falls angegeben |
| Chargennummer | Herstellerchargen-Nummer |
| Kosten/Liter (€) | Für Kostenübersicht und Durchschnittspreis |

Kamerplanter zeigt eine Zusammenfassung (Gesamt-Volumen, Ø Kosten/Liter, Anzahl Einträge) sowie eine Warnung, wenn ein Gebinde innerhalb der nächsten 30 Tage abläuft.

### Unverträglichkeiten

Ist ein Dünger als unverträglich mit einem anderen hinterlegt (z. B. CalMag mit einem Sulfat-Supplement), erscheint auf der Detailseite eine Warnung mit Grund und Schweregrad.

!!! info "Unverträglichkeiten derzeit nur über die API pflegbar"
    Das Anlegen und Entfernen von Unverträglichkeits-Einträgen zwischen zwei Düngern ist aktuell nur über die REST-API (`POST /fertilizers/{key}/incompatibilities`) möglich — die Oberfläche zeigt bestehende Einträge nur an. Wende dich bei Bedarf an deine Betreiber:in oder trage die Kombination als Notiz im Freitextfeld des Düngers ein.

### Verwendung in Nährstoffplänen

Der Abschnitt „Verwendung" zeigt dir, in welchen Nährstoffplänen dieser Dünger eingesetzt wird — als Gantt-Diagramm über die Phasen der jeweiligen Pläne hinweg. So siehst du auf einen Blick, in welchen Plänen und Phasen ein Dünger vorkommt, bevor du ihn löschst oder seine Dosierung änderst.

---

## Nährstoffplan erstellen

Ein Nährstoffplan definiert die Dosierungen aller Dünger für jede Wachstumsphase. Er ist das Herzstück der Dünge-Logik.

### Schritt 1: Neuen Nährstoffplan anlegen

Navigiere zu **Düngung → Nährstoffpläne** und klicke auf **Neuer Plan**.

### Schritt 2: Plan benennen und Substrat wählen

Gib einen Namen ein (z.B. "Tomaten Hochbeet 2026") und wähle den Substrat-Typ (Erde, Coco, Hydroponik). Das Substrat beeinflusst die EC-Toleranz und CalMag-Empfehlungen.

### Schritt 3: Phaseneinträge hinzufügen

Der neue Plan öffnet sich auf dem Tab **Phaseneinträge** — er zeigt die Phasen als Gantt-Zeitleiste. Für jede Wachstumsphase fügst du die Dünger-Dosierungen ein:

1. Klicke auf **Phase hinzufügen**.
2. Wähle die Phase (Keimung, Vegetativ, Blüte, usw.).
3. Trage für jeden Dünger die Dosierung in ml/L ein.
4. Das System berechnet sofort die Gesamt-EC und zeigt an, ob das Budget eingehalten wird.

!!! warning "EC-Budget-Überschreitung"
    Wenn deine eingegebenen Dosierungen das EC-Budget überschreiten, erscheint eine Warnung. Kamerplanter gibt dann einen Anpassungsvorschlag, bei dem die einzelnen Komponenten proportional reduziert werden.

### Schritt 4: Plan einem Pflanzdurchlauf zuweisen

1. Öffne den gewünschten **Pflanzdurchlauf** unter **Durchläufe** und wechsle zum Tab **Düngung & Bewässerung**.
2. Klicke auf **Nährstoffplan zuweisen**.
3. Wähle den Plan aus der Liste.

Alle Pflanzen in diesem Durchlauf nutzen von nun an diesen Plan für ihre Gießempfehlungen.

---

## Ausbringungskanäle (Multi-Channel Delivery) {#ausbringungskanaele-multi-channel-delivery}

Ab der Erfahrungsstufe **Fortgeschritten** kannst du für einen Phaseneintrag statt einer einzelnen Dosierung mehrere **Ausbringungskanäle** definieren — zum Beispiel eine automatische Fertigation über den Tropf-Tank plus eine gelegentliche Blattdüngung. Jeder Kanal hat eine eigene Anwendungsmethode, eigene Dünger-Dosierungen und optional einen eigenen Zeitplan.

### Kanal anlegen

1. Öffne den Nährstoffplan und klicke bei einem Phaseneintrag auf **Kanal hinzufügen**.
2. Vergib eine **Kanal-ID** und wähle die **Ausbringungsmethode**:

| Methode | Bedeutung | Typische Parameter |
|---------|-----------|--------------------|
| Fertigation | Automatisierte Dosierung über einen Tank | Durchläufe/Tag, Pumpendauer (s), Durchfluss (ml/min), optional verknüpfter Tank |
| Gießen (Drench) | Manuelles Gießen mit Gießkanne oder Schlauch | Volumen pro Gießvorgang (L) |
| Blattsprühung | Foliar-Düngung über den Blattapparat | Volumen pro Sprühvorgang (L) |
| Oberflächendüngung | Feststoffdünger aufstreuen | Gramm pro Pflanze, Gramm pro m² |

3. Trage optional Ziel-EC und Ziel-pH für diesen Kanal ein.
4. Aktiviere bei Bedarf einen **eigenen Gießplan** für den Kanal (Wochentage oder Intervall, bevorzugte Uhrzeit, Erinnerung Stunden vorher) — ohne eigenen Plan gilt der Plan-Standard.
5. Weise dem Kanal über **Düngemittel** die gewünschten Dünger mit ml/L-Dosierung zu (optional als „optional" markierbar, falls ein Dünger bei Bedarf weggelassen werden darf).

### Kanal-Validierung

Kamerplanter prüft die Kanäle gegen das EC-Budget der Phase und zeigt auf dem Tab **Validierung** an, ob alle Kanäle gültig sind oder ob es Probleme gibt (inklusive Toleranzbereich).

### Gießvorgang aus einem Kanal protokollieren

Über den Button **„Gießvorgang für diesen Kanal protokollieren"** öffnest du direkt ein vorausgefülltes Gießprotokoll-Formular (Anwendungsmethode, Ziel-EC/-pH und Dünger-Dosierungen sind bereits übernommen) — siehe [Gießprotokoll](watering-log.md).

!!! note "Bestehende Einzeldünger-Pläne bleiben gültig"
    Pläne ohne Ausbringungskanäle funktionieren unverändert weiter (Legacy-Modus). Über **„Zu Multi-Kanal konvertieren"** kannst du einen bestehenden Phaseneintrag in einen Standard-Ausbringungskanal umwandeln — das lässt sich nicht rückgängig machen.

---

## Plan duplizieren und validieren

- **Klonen**: Klicke in der Nährstoffplan-Liste auf das Kopier-Symbol, um eine Kopie eines Plans mit neuem Namen anzulegen — praktisch, um einen bewährten Plan als Ausgangspunkt für eine Variante zu nutzen.
- **Validieren**: Der Tab **Validierung** in der Plan-Detailansicht prüft automatisch, sobald du ihn öffnest, ob der Plan vollständig ist (alle Phasen abgedeckt) und ob die EC-Budgets je Phase eingehalten werden.
- **Dosierungsrechner**: Der Tab **Dosierungsrechner** berechnet dir die exakten Mengen dieses Plans für einen konkreten Standort bzw. ein konkretes Gießvolumen — nützlich, um vor dem Anmischen schnell die tatsächlich benötigte Menge zu ermitteln.

---

## Gießvorgang protokollieren

Nach jedem Gießen oder Düngen dokumentierst du den Vorgang im **Gießprotokoll**. Das hilft beim Verfolgen der tatsächlichen Nährstoffgabe und der Substrat-EC über die Zeit. Details zu Feldern, Erfassung und Auswertung findest du auf der Seite [Gießprotokoll](watering-log.md) — hier nur die beiden Einstiegspunkte:

### Schnell erfassen über den Pflanzdurchlauf

1. Öffne einen **Pflanzdurchlauf** und wechsle zum Tab **Düngung & Bewässerung** — dort siehst du die kommenden Gießtermine aus dem Gießplan.
2. Klicke bei einem Termin auf **Schnell bestätigen** oder öffne **Gießen bestätigen**, um vorher Ist-EC/-pH und Volumen anzupassen.

### Detailliert erfassen

1. Öffne den Menüpunkt **Gießprotokoll** (eigener Menüpunkt auf oberster Ebene, nicht unter Düngung).
2. Klicke auf **Gießvorgang erfassen**.
3. Wähle Pflanze(n) und/oder Stellplätze, Anwendungsmethode, Volumen und optional Dünger mit Dosierung.
4. Hinterlege optional EC/pH vorher und nachher sowie Abfluss-EC/-pH (für Runoff-Analyse).

!!! tip "Runoff-EC messen"
    Bei Topf- und Coco-Kulturen gibt die Abfluss-EC (das Wasser, das unten aus dem Topf läuft) Auskunft über die Salzakkumulation im Substrat. Ist die Abfluss-EC deutlich höher als die Eingabe-EC, ist es Zeit für einen Spülgang.

---

## Spülung berechnen (Flushing) {#spulung-berechnen-flushing}

Vor der Ernte kann ein Spülgang helfen, überschüssige Salze aus dem Substrat zu waschen. Kamerplanter bietet dafür einen **Rechner** — es gibt aktuell keinen Button an der Pflanze, der einen Spülgang „startet" oder automatisch Gieß-Aufgaben anlegt.

!!! note "Wissenschaftlicher Stand"
    Das Flushing ist in Gärtner-Kreisen weit verbreitet, der wissenschaftliche Nachweis für verbesserten Geschmack ist aber umstritten. Bei Living Soil und organischer Düngung wird ausdrücklich davon abgeraten, da das Mikrobiom geschädigt wird.

### Rechner bedienen

1. Öffne **Düngung → Nährstoff-Berechnungen** und die Karte **Spülung**.
2. Trage die aktuelle EC deiner Nährlösung und die Anzahl Tage bis zur geplanten Ernte ein.
3. Klicke auf **Berechnen**.

Das Ergebnis zeigt die empfohlene Spüldauer, den Starttag (heute + verbleibende Tage minus Spüldauer) und einen Tag-für-Tag-Plan mit Ziel-EC, Aktion (z. B. „Vierteldosis-Spülung") und Dosierungs-Prozentsatz — die letzten 40 % der Spüldauer laufen mit reinem Wasser (0 mS/cm).

!!! info "Substrat aktuell nicht auswählbar"
    Die Karte hat derzeit kein Substrat-Auswahlfeld — der Rechner geht serverseitig von Coco als Substrat aus (Spüldauer 10–21 Tage). Für Hydroponik oder Erde orientiere dich stattdessen an der Tabelle unten.

**Empfohlene Spüldauer nach Substrat:**

<!-- Quelle: src/backend/app/domain/engines/nutrient_engine.py FlushingProtocol.FLUSH_DURATIONS -->

| Substrat | Spüldauer |
|---------|----------|
| Hydroponik / Blähton / Perlite / Steinwolle | 7–14 Tage |
| Coco | 10–21 Tage |
| Erde / Living Soil | 14–30 Tage |

!!! warning "Werte weichen von früheren Angaben ab"
    Frühere Versionen dieser Seite nannten für Erde 21–42 Tage — das entsprach nicht dem tatsächlich hinterlegten Wert. Die Tabelle oben ist jetzt konsistent mit dem [Nährlösungs-Mischleitfaden](../guides/nutrient-mixing.md#flush-substrat).

---

## Organische Freilanddüngung

Für Freilandgärten mit Erde, Hochbeet-Mix oder Living Soil empfiehlt Kamerplanter eine flächenbasierte organische Düngung statt der EC-Kalkulation.

### Dünger-Kategorien im Freiland

| Kategorie | Typische Produkte | Wann einsetzen |
|-----------|------------------|----------------|
| Kompost | Reifkompost | Frühjahr (2–4 L/m²) |
| Hornprodukte | Hornspäne, Hornmehl | Frühjahr/Sommer |
| Pflanzenjauchen | Brennnesseljauche, Beinwelljauche | Mai–August |
| Mineralische Ergänzung | Gesteinsmehl, Algenkalk | Frühjahr |

### Empfehlung nach Nährstoffbedarf

Kamerplanter zeigt in der Pflanzendetailansicht den Nährstoffbedarf der Pflanze (aus den Stammdaten) und gibt darauf basierend eine Düngeempfehlung:

| Nährstoffbedarf | Beispielpflanzen | Empfehlung |
|----------------|-----------------|-----------|
| Starkzehrer | Tomate, Kürbis, Kohl | Kompost 3–4 L/m² + Hornspäne 80 g/m² |
| Mittelzehrer | Möhre, Salat, Fenchel | Kompost 2–3 L/m² + Hornspäne 40 g/m² |
| Schwachzehrer | Kräuter, Bohnen, Erbsen | Kompost 1–2 L/m², kein weiterer Dünger |
| N-Fixierer | Bohnen, Erbsen, Lupinen | Kein N-Dünger! Nur P und K bei Bedarf |

!!! warning "N-Fixierer nicht mit Stickstoff düngen"
    Hülsenfrüchte wie Bohnen und Erbsen binden selbst Stickstoff aus der Luft. Stickstoffdünger schadet hier mehr als er nützt und unterdrückt die natürliche N-Fixierung.

#### Flächendosierung berechnen (Nährstoff-Rechner) {#flaechendosierung-berechnen-naehrstoff-rechner}

Statt Dosierungen von Hand aus den Tabellen oben abzuleiten, lässt du sie dir im **Nährstoff-Rechner** exakt berechnen:

1. Öffne **Düngung → Nährstoff-Berechnungen** und wähle die Karte **Flächendosierung (Freiland)**.
2. Trage die Keys der gewünschten Dünger ein (kommagetrennt), z.B. Kompost und Hornspäne.
3. Gib entweder die **Beetfläche in m²** direkt ein, oder trage stattdessen einen **Standort** ein. Ist eine Fläche eingetragen, hat sie Vorrang — der Standort wird dann ignoriert. Bleibt das Flächenfeld leer, übernimmt Kamerplanter die hinterlegte Fläche des gewählten Standorts.
4. Wähle optional den **Nährstoffbedarf** der Pflanze (Stark-/Mittel-/Schwachzehrer, N-Fixierer) — das liefert zusätzliche Hinweise, ersetzt aber nicht die Mengenberechnung selbst.
5. Klicke auf **Berechnen**.

Das Ergebnis zeigt je Dünger die Gesamtmenge in Gramm bzw. Liter für die angegebene Fläche, das hinterlegte Verdünnungsverhältnis, die Freisetzungsgeschwindigkeit und ergänzende Hinweise.

!!! tip "Fläche kommt aus dem Standort oder wird manuell eingegeben"
    Wenn du bereits eine Beetgröße unter **Standorte → Standorte** hinterlegt hast, kannst du das Flächenfeld leer lassen und stattdessen den Standort-Key eintragen — die Fläche wird automatisch übernommen.

---

## CalMag: Wann und wie viel?

CalMag-Supplemente (Calcium-Magnesium) sind bei weichem Leitungswasser und Osmosewasser wichtig, da diese Wasser-Typen kaum natürliche Mineralien enthalten.

Kamerplanter berechnet automatisch den CalMag-Bedarf, wenn du die Wasserquelle auf deiner Site hinterlegt hast:

- **100% Osmosewasser**: Volles CalMag-Supplement (ca. 0,5–1,5 ml/L je nach Phase)
- **50/50 Mischung (RO + Leitungswasser)**: Halbe CalMag-Menge
- **Hartes Leitungswasser** (EC > 0,5 mS/cm): Oft kein CalMag nötig

---

## Wasser-Mischer und EC-Budget-Rechner {#wasser-mischer-und-ec-budget-rechner}

Auf **Düngung → Nährstoff-Berechnungen** findest du neben dem Mischprotokoll und der Flächendosierung zwei weitere Karten, die je nach Erfahrungsstufe sichtbar sind:

### Wasser-Mischer (ab Stufe Fortgeschritten)

Gibst du die EC deines Leitungswassers, dessen Alkalinität und deine gewünschte Ziel-EC des Mischwassers ein, berechnet der Wasser-Mischer rückwärts den benötigten **Osmosewasser-Anteil (%)**, um genau diese Ziel-EC zu erreichen — und zeigt dazu die resultierende effektive Wasser-EC.

### EC-Budget-Rechner (ab Stufe Experte)

Der EC-Budget-Rechner ist die ausführlichste Variante des Mischprotokolls: Zusätzlich zu Ziel-EC, Substrat, Phase und Volumen kannst du hier CalMag- und Silizium-Dünger mit fester Dosierung vorab abziehen, die Anzahl bereits durchlaufener Substrat-Zyklen angeben (für den automatischen Coco-CalMag-Boost) und einen **gemessenen EC-Wert samt Wassertemperatur** eintragen.

!!! tip "EC-Temperaturkorrektur (EC@25)"
    Die elektrische Leitfähigkeit hängt von der Wassertemperatur ab — ein und dieselbe Nährlösung zeigt bei 30 °C eine höhere EC als bei 20 °C. Trägst du im EC-Budget-Rechner deinen gemessenen EC-Wert **und** die Wassertemperatur ein, rechnet Kamerplanter automatisch auf die Referenztemperatur 25 °C um (`EC@25 = EC_gemessen / (1 + 0,02 × (T − 25))`) und zeigt diesen korrigierten Wert im Ergebnis an. So bleiben Messungen bei unterschiedlichen Temperaturen vergleichbar.

Das Ergebnis zeigt eine farbige EC-Budget-Leiste (Basiswasser/Silizium/CalMag/Dünger/pH-Reserve), Warnungen, eine Dosierungstabelle und eine nummerierte Mischanleitung — identisch zur Berechnungslogik des Mischprotokolls, nur mit mehr Eingabemöglichkeiten.

---

## Häufige Fragen

??? question "Was ist der Unterschied zwischen einem Nährstoffplan und einem Gießprotokoll-Eintrag?"
    Ein **Nährstoffplan** ist das Rezept — er definiert für jede Phase, welche Dünger in welcher Menge verwendet werden sollen. Ein **Gießprotokoll-Eintrag** ist die Aufzeichnung einer tatsächlich durchgeführten Gießung oder Düngung. Das eine ist die Planung, das andere die Dokumentation — Details dazu im [Gießprotokoll](watering-log.md).

??? question "Muss ich jeden Gießvorgang erfassen?"
    Nein, das ist optional. Kamerplanter funktioniert auch ohne vollständige Gieß-Dokumentation. Wenn du aber die Runoff-EC verfolgen oder die Nährstoffgabe optimieren möchtest, lohnt sich eine konsequente Erfassung.

??? question "Warum schlägt das System CalMag vor, obwohl ich hartes Wasser habe?"
    Wenn Coco Coir als Substrat eingestellt ist, empfiehlt Kamerplanter immer CalMag — unabhängig von der Wasserhärte. Coco Coir bindet Calcium und Magnesium aktiv, weshalb der Bedarf höher ist als bei Erde.

??? question "Kann ich einen bestehenden Nährstoffplan für neue Pflanzdurchläufe wiederverwenden?"
    Ja. Beim Zuweisen eines Plans zu einem Pflanzdurchlauf wählst du aus allen vorhandenen Plänen. So kannst du einen bewährten Plan für mehrere Durchläufe nutzen.

??? question "Warum ist meine berechnete Dosierung im Mischprotokoll jetzt niedriger als früher?"
    Kamerplanter zieht seit Kurzem die pH-Reserve korrekt vom EC-Budget ab, bevor die Dünger-Dosierungen berechnet werden. Diese Reserve war vorher nicht berücksichtigt, wodurch die tatsächliche End-EC nach der pH-Korrektur das Ziel leicht überschreiten konnte. Die neuen, etwas niedrigeren ml/L-Werte treffen dein EC-Ziel dafür zuverlässiger.

??? question "Was ist Alkalinität und wo finde ich den Wert für mein Wasser?"
    Alkalinität (auch Karbonathärte oder KH genannt) beschreibt, wie stark dein Wasser einer pH-Änderung entgegenwirkt — in ppm CaCO₃ gemessen. Den Wert findest du oft im Wasserwerte-Datenblatt deines örtlichen Wasserversorgers, oder du misst ihn selbst mit einem KH-Tröpfchentest aus dem Aquaristik-Fachhandel. Leitungswasser liegt meist zwischen 50 und 250 ppm.

??? question "Kann ich für einen Freilanddünger sowohl g/m² als auch L/m² hinterlegen?"
    Ja. Beide Felder sind unabhängig voneinander und optional — nutze g/m² für Feststoffe (z.B. Hornspäne) und L/m² für Flüssig- oder Kompostdünger. Die Flächendosierung im Nährstoff-Rechner berücksichtigt automatisch, welches Feld für den jeweiligen Dünger gepflegt ist.

---

## Siehe auch

- [Meiner Pflanze geht es schlecht — Symptom-Diagnose](plant-health-troubleshooting.md)
- [Gießprotokoll](watering-log.md)
- [Tankmanagement](tanks.md)
- [Wachstumsphasen](growth-phases.md)
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md)
- [Guides: VPD-Optimierung](../guides/vpd-optimization.md)
