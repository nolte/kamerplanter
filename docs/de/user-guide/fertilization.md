# Dünge-Logik

Kamerplanter berechnet präzise Mischverhältnisse für Nährstofflösungen, überwacht Ihr EC-Budget und erinnert Sie an Gießtermine. Ob Hydroponik mit EC-Kalkulation oder organische Freilanddüngung — das System unterstützt beide Ansätze.

---

## Voraussetzungen

- Mindestens ein angelegter Dünger unter **Düngung → Dünger**
- Mindestens eine Pflanze mit laufender Wachstumsphase
- Empfohlen: Wasserquelle auf der Site konfiguriert (für automatische EC-Berechnung)

---

## Grundkonzepte verstehen

### Elektrische Leitfähigkeit (EC)

Die Elektrische Leitfähigkeit (EC) misst die Konzentration gelöster Nährstoffe im Gießwasser in Millisiemens pro Zentimeter (mS/cm). Sie ist der wichtigste Kennwert für die Nährstoffdosierung:

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

Das **EC-Budget** ist die Differenz zwischen dem EC-Zielwert der aktuellen Phase und dem EC-Wert Ihres Ausgangswassers. Dieses Budget verteilt Kamerplanter auf die einzelnen Düngerkomponenten.

**Beispiel:**
- EC-Ziel für Blüte: 1,8 mS/cm
- Leitungswasser-EC: 0,4 mS/cm
- EC-Budget für Dünger: 1,4 mS/cm

!!! tip "Osmosewasser hat quasi keine Basis-EC"
    Mit reinem Osmosewasser (EC ≈ 0) steht das gesamte EC-Budget für Dünger zur Verfügung. Das gibt mehr Kontrolle, bedeutet aber auch mehr Verantwortung — insbesondere bei Calcium und Magnesium.

---

## Dünger anlegen

### Schritt 1: Zum Bereich Düngung navigieren

Klicken Sie in der Navigation auf **Düngung → Dünger**.

### Schritt 2: Neuen Dünger anlegen

Klicken Sie auf **Dünger hinzufügen**.

### Schritt 3: Dünger-Daten ausfüllen

| Feld | Beschreibung |
|------|-------------|
| Name | Produktname (z.B. "Canna Coco A") |
| Typ | Basisdünger, Supplement, Booster, Biologisch |
| NPK-Verhältnis | Stickstoff/Phosphor/Kalium-Anteile |
| EC-Beitrag | EC-Erhöhung pro ml/L (steht auf dem Etikett oder Datenblatt) |
| Mischpriorität | Reihenfolge beim Mischen (niedrigere Zahl = früher) |
| Dosierung (ml/L) | Standarddosierung pro Liter Wasser |

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

Navigieren Sie zu **Düngung → Nährstoffpläne** und klicken Sie auf **Neuer Plan**.

### Schritt 2: Plan benennen und Substrat wählen

Geben Sie einen Namen ein (z.B. "Tomaten Hochbeet 2026") und wählen Sie das Substrat-Typ (Erde, Coco, Hydroponik). Das Substrat beeinflusst die EC-Toleranz und CalMag-Empfehlungen.

### Schritt 3: Phaseneinträge hinzufügen

Für jede Wachstumsphase fügen Sie die Dünger-Dosierungen ein:

1. Klicken Sie auf **Phase hinzufügen**.
2. Wählen Sie die Phase (Keimung, Vegetativ, Blüte, usw.).
3. Tragen Sie für jeden Dünger die Dosierung in ml/L ein.
4. Das System berechnet sofort die Gesamt-EC und zeigt an, ob das Budget eingehalten wird.

!!! warning "EC-Budget-Überschreitung"
    Wenn Ihre eingegebenen Dosierungen das EC-Budget überschreiten, erscheint eine Warnung. Kamerplanter gibt dann einen Anpassungsvorschlag, bei dem die einzelnen Komponenten proportional reduziert werden.

### Schritt 4: Plan einem Pflanzdurchlauf zuweisen

1. Öffnen Sie den gewünschten **Pflanzdurchlauf** unter **Durchläufe**.
2. Klicken Sie auf **Nährstoffplan zuweisen**.
3. Wählen Sie den Plan aus der Liste.

Alle Pflanzen in diesem Durchlauf nutzen von nun an diesen Plan für ihre Gießempfehlungen.

---

## Gießereignis erfassen (Feeding Event)

Nach jedem Düngen dokumentieren Sie ein Gießereignis. Das hilft beim Verfolgen der tatsächlichen Nährstoffgabe und der Substrat-EC über die Zeit.

### Schnell erfassen über den Pflanzdurchlauf

1. Öffnen Sie einen **Pflanzdurchlauf**.
2. Klicken Sie auf **Gießen bestätigen** (oder **Gießen — schnell**).
3. Bestätigen Sie die vorgeschlagene Menge und EC — oder passen Sie sie an.

### Detailliert erfassen

1. Navigieren Sie zu **Düngung → Gießereignisse**.
2. Klicken Sie auf **Neues Ereignis**.
3. Wählen Sie Pflanze(n) oder Pflanzdurchlauf.
4. Tragen Sie die tatsächlich verwendeten Mengen ein.
5. Hinterlegen Sie optional Ist-EC, pH und Abfluss-EC (für Runoff-Analyse).

!!! tip "Runoff-EC messen"
    Bei Topf- und Coco-Kulturen gibt die Abfluss-EC (das Wasser, das unten aus dem Topf läuft) Auskunft über die Salzakkumulation im Substrat. Ist die Abfluss-EC deutlich höher als die Eingabe-EC, ist es Zeit für einen Spülgang.

---

## Spülprotokoll (Flushing)

Vor der Ernte kann ein Spülgang helfen, überschüssige Salze aus dem Substrat zu waschen. Kamerplanter führt Sie durch diesen Prozess.

!!! note "Wissenschaftlicher Stand"
    Das Flushing ist in Gärtner-Kreisen weit verbreitet, der wissenschaftliche Nachweis für verbesserten Geschmack ist aber umstritten. Bei Living Soil und organischer Düngung wird ausdrücklich davon abgeraten, da das Mikrobiom geschädigt wird.

1. Öffnen Sie die Pflanze und klicken Sie auf **Spülprotokoll starten**.
2. Das System schlägt eine Dauer vor (abhängig vom Substrat-Typ).
3. Während des Spülens wechseln Sie zu reinem, pH-adjustiertem Wasser.
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

---

## CalMag: Wann und wie viel?

CalMag-Supplemente (Calcium-Magnesium) sind bei weichem Leitungswasser und Osmosewasser wichtig, da diese Wasser-Typen kaum natürliche Mineralien enthalten.

Kamerplanter berechnet automatisch den CalMag-Bedarf, wenn Sie die Wasserquelle auf Ihrer Site hinterlegt haben:

- **100% Osmosewasser**: Volles CalMag-Supplement (ca. 0,5–1,5 ml/L je nach Phase)
- **50/50 Mischung (RO + Leitungswasser)**: Halbe CalMag-Menge
- **Hartes Leitungswasser** (EC > 0,5 mS/cm): Oft kein CalMag nötig

---

## Häufige Fragen

??? question "Was ist der Unterschied zwischen einem Nährstoffplan und einem Gießereignis?"
    Ein **Nährstoffplan** ist das Rezept — er definiert für jede Phase, welche Dünger in welcher Menge verwendet werden sollen. Ein **Gießereignis** ist die Aufzeichnung einer tatsächlich durchgeführten Düngung. Das eine ist die Planung, das andere die Dokumentation.

??? question "Muss ich jeden Gießvorgang erfassen?"
    Nein, das ist optional. Kamerplanter funktioniert auch ohne vollständige Gieß-Dokumentation. Wenn Sie aber die Runoff-EC verfolgen oder die Nährstoffgabe optimieren möchten, lohnt sich eine konsequente Erfassung.

??? question "Warum schlägt das System CalMag vor, obwohl ich hartes Wasser habe?"
    Wenn Coco Coir als Substrat eingestellt ist, empfiehlt Kamerplanter immer CalMag — unabhängig von der Wasserhärte. Coco Coir bindet Calcium und Magnesium aktiv, weshalb der Bedarf höher ist als bei Erde.

??? question "Kann ich einen bestehenden Nährstoffplan für neue Pflanzdurchläufe wiederverwenden?"
    Ja. Beim Zuweisen eines Plans zu einem Pflanzdurchlauf wählen Sie aus allen vorhandenen Plänen. So können Sie einen bewährten Plan für mehrere Durchläufe nutzen.

---

## Siehe auch

- [Tankmanagement](tanks.md)
- [Wachstumsphasen](growth-phases.md)
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md)
- [Guides: VPD-Optimierung](../guides/vpd-optimization.md)
