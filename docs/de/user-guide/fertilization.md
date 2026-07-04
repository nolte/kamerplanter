# Dünge-Logik

Kamerplanter berechnet präzise Mischverhältnisse für Nährstofflösungen, überwacht dein EC-Budget und erinnert dich an Gießtermine. Ob Hydroponik mit EC-Kalkulation oder organische Freilanddüngung — das System unterstützt beide Ansätze.

---

## Voraussetzungen

- Mindestens ein angelegter Dünger unter **Düngung → Dünger**
- Mindestens eine Pflanze mit laufender Wachstumsphase
- Empfohlen: Wasserquelle auf der Site konfiguriert (für automatische EC-Berechnung)

---

## Grundkonzepte verstehen

### Elektrische Leitfähigkeit (EC)

Die elektrische Leitfähigkeit (EC) misst die Konzentration gelöster Nährstoffe im Gießwasser in Millisiemens pro Zentimeter (mS/cm). Sie ist der wichtigste Kennwert für die Nährstoffdosierung:

- **Zu niedrig**: Pflanze hungert, Mangelerscheinungen möglich
- **Optimal**: Pflanze wächst bestmöglich
- **Zu hoch**: Salz-Stress, Wurzelschäden, Nährstoff-Blockaden

Typische EC-Zielwerte:

| Phase | Hydroponik / Coco | Erde |
|-------|------------------|------|
| Sämling | 0,4–0,8 mS/cm | 0,4–0,6 mS/cm |
| Vegetativ | 1,2–1,8 mS/cm | 0,8–1,2 mS/cm |
| Blüte | 1,6–2,2 mS/cm | 1,0–1,4 mS/cm |
| Spätblüte | 0,6–1,0 mS/cm | — |

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

Klicke in der Navigation auf **Düngung → Dünger**.

### Schritt 2: Neuen Dünger anlegen

Klicke auf **Dünger hinzufügen**.

### Schritt 3: Dünger-Daten ausfüllen

| Feld | Beschreibung |
|------|-------------|
| Name | Produktname (z.B. "Canna Coco A") |
| Typ | Basisdünger, Supplement, Booster, Biologisch, **CalMag** |
| NPK-Verhältnis | Stickstoff/Phosphor/Kalium-Anteile |
| EC-Beitrag | EC-Erhöhung pro ml/L (steht auf dem Etikett oder Datenblatt) |
| Mischpriorität | Reihenfolge beim Mischen (niedrigere Zahl = früher) |
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
    Die Reihenfolge beim Mischen von Düngern ist chemisch bedeutsam. Falsche Mischfolge kann zu Ausfällungen führen, die Nährstoffe unverfügbar machen. Kamerplanter erzwingt die korrekte Reihenfolge automatisch.

    **Korrekte Mischfolge:**
    1. Wasser mit Zimmertemperatur (18–22 °C)
    2. Silizium-Zusätze (falls verwendet)
    3. **CalMag** (immer vor Sulfaten!)
    4. Basis A (Calcium + Mikronährstoffe)
    5. Basis B (Phosphor + Schwefel + Magnesium)
    6. Weitere Supplemente und Booster
    7. pH-Korrektur (pH Down / pH Up) — immer zuletzt

---

## Nährstoffplan erstellen

Ein Nährstoffplan definiert die Dosierungen aller Dünger für jede Wachstumsphase. Er ist das Herzstück der Dünge-Logik.

### Schritt 1: Neuen Nährstoffplan anlegen

Navigiere zu **Düngung → Nährstoffpläne** und klicke auf **Neuer Plan**.

### Schritt 2: Plan benennen und Substrat wählen

Gib einen Namen ein (z.B. "Tomaten Hochbeet 2026") und wähle den Substrat-Typ (Erde, Coco, Hydroponik). Das Substrat beeinflusst die EC-Toleranz und CalMag-Empfehlungen.

### Schritt 3: Phaseneinträge hinzufügen

Für jede Wachstumsphase fügst du die Dünger-Dosierungen ein:

1. Klicke auf **Phase hinzufügen**.
2. Wähle die Phase (Keimung, Vegetativ, Blüte, usw.).
3. Trage für jeden Dünger die Dosierung in ml/L ein.
4. Das System berechnet sofort die Gesamt-EC und zeigt an, ob das Budget eingehalten wird.

!!! warning "EC-Budget-Überschreitung"
    Wenn deine eingegebenen Dosierungen das EC-Budget überschreiten, erscheint eine Warnung. Kamerplanter gibt dann einen Anpassungsvorschlag, bei dem die einzelnen Komponenten proportional reduziert werden.

### Schritt 4: Plan einem Pflanzdurchlauf zuweisen

1. Öffne den gewünschten **Pflanzdurchlauf** unter **Durchläufe**.
2. Klicke auf **Nährstoffplan zuweisen**.
3. Wähle den Plan aus der Liste.

Alle Pflanzen in diesem Durchlauf nutzen von nun an diesen Plan für ihre Gießempfehlungen.

---

## Gießereignis erfassen (Feeding Event — Dünge-/Bewässerungseintrag)

Nach jedem Düngen dokumentierst du ein Gießereignis. Das hilft beim Verfolgen der tatsächlichen Nährstoffgabe und der Substrat-EC über die Zeit.

### Schnell erfassen über den Pflanzdurchlauf

1. Öffne einen **Pflanzdurchlauf**.
2. Klicke auf **Gießen bestätigen** (oder **Gießen — schnell**).
3. Bestätige die vorgeschlagene Menge und EC — oder passe sie an.

### Detailliert erfassen

1. Navigiere zu **Düngung → Gießereignisse**.
2. Klicke auf **Neues Ereignis**.
3. Wähle Pflanze(n) oder Pflanzdurchlauf.
4. Trage die tatsächlich verwendeten Mengen ein.
5. Hinterlege optional Ist-EC, pH und Abfluss-EC (für Runoff-Analyse).

!!! tip "Runoff-EC messen"
    Bei Topf- und Coco-Kulturen gibt die Abfluss-EC (das Wasser, das unten aus dem Topf läuft) Auskunft über die Salzakkumulation im Substrat. Ist die Abfluss-EC deutlich höher als die Eingabe-EC, ist es Zeit für einen Spülgang.

---

## Spülprotokoll (Flushing)

Vor der Ernte kann ein Spülgang helfen, überschüssige Salze aus dem Substrat zu waschen. Kamerplanter führt dich durch diesen Prozess.

!!! note "Wissenschaftlicher Stand"
    Das Flushing ist in Gärtner-Kreisen weit verbreitet, der wissenschaftliche Nachweis für verbesserten Geschmack ist aber umstritten. Bei Living Soil und organischer Düngung wird ausdrücklich davon abgeraten, da das Mikrobiom geschädigt wird.

1. Öffne die Pflanze und klicke auf **Spülprotokoll starten**.
2. Das System schlägt eine Dauer vor (abhängig vom Substrat-Typ).
3. Während des Spülens wechsle zu reinem, pH-adjustiertem Wasser.
4. Kamerplanter erstellt automatisch Gieß-Aufgaben für den Spülzeitraum.

**Empfohlene Spüldauer (Orientierungswerte):**

| Substrat | Spüldauer |
|---------|----------|
| Hydroponik | 7–14 Tage |
| Coco | 10–21 Tage |
| Erde | 21–42 Tage |
| Living Soil | Kein Flushing empfohlen |

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
4. Wähle optional den **Nährstoffbedarf** der Pflanze (Stark-/Mittel-/Schwachzehrer, Stickstoffsammler) — das liefert zusätzliche Hinweise, ersetzt aber nicht die Mengenberechnung selbst.
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

## Häufige Fragen

??? question "Was ist der Unterschied zwischen einem Nährstoffplan und einem Gießereignis?"
    Ein **Nährstoffplan** ist das Rezept — er definiert für jede Phase, welche Dünger in welcher Menge verwendet werden sollen. Ein **Gießereignis** ist die Aufzeichnung einer tatsächlich durchgeführten Düngung. Das eine ist die Planung, das andere die Dokumentation.

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

- [Tankmanagement](tanks.md)
- [Wachstumsphasen](growth-phases.md)
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md)
- [Guides: VPD-Optimierung](../guides/vpd-optimization.md)
