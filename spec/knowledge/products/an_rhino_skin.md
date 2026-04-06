# Rhino Skin — Advanced Nutrients

> **Produkttyp:** SUPPLEMENT
> **Einsatzzweck:** Kaliumsilikat-Supplement zur Stärkung der Zellwände, Stängelstabilität und Stressresistenz — MUSS als ERSTES Produkt in die Nährlösung gegeben werden (mixing_priority: 5)

---

## 1. Produktübersicht

Rhino Skin ist das Silikat-Supplement von Advanced Nutrients und nimmt eine Sonderstellung in der gesamten Produktlinie ein: Es ist das **einzige Produkt mit alkalischem pH-Effekt** und muss **immer als ERSTES** in die Nährlösung gemischt werden (mixing_priority: 5). Diese Anforderung ist nicht optional — eine falsche Mischungsreihenfolge führt zu Silikat-Ausfällung und Nährstoff-Lockout.

Rhino Skin liefert Silizium in Form von Kaliumsilikat (K₂SiO₃). Silizium ist zwar kein essentielles Pflanzenelement, wird aber als „quasi-essentiell" (beneficial element) eingestuft: Es wird in die Zellwände eingebaut, bildet eine physische Barriere gegen Pathogene und Schädlinge, stärkt Stängel und Äste gegen das Gewicht schwerer Blüten und verbessert die Toleranz gegenüber abiotischem Stress (Hitze, Trockenheit, Salzstress).

**Kritischer Hinweis:** Rhino Skin hat in der AN-Formulierung einen **pH von 5.7** (pH Perfect kompatibel), nicht den typischen pH von 11+ von reinem Kaliumsilikat. Dies ist ein wesentlicher Unterschied zu generischen Silikat-Produkten.

---

## 2. Zusammensetzung & Nährstoffanalyse

### 2.1 Deklarierte Nährstoffe

| Nährstoff | Gehalt | Form |
|-----------|--------|------|
| Stickstoff (N) | 0 % | — |
| Phosphor (P₂O₅) | 0 % | — |
| Kalium (K₂O) | 0.4 % | Wasserlöslich |

**Abgeleitet aus:** Kaliumsilikat

### 2.2 Weitere Inhaltsstoffe (Non-Plant-Food)

| Inhaltsstoff | Gehalt | Form |
|-------------|--------|------|
| Siliziumdioxid (SiO₂) | 0.15 % | Aus Kaliumsilikat |

**Hinweis:** Der Silizium-Gehalt wird je nach Quelle zwischen 0.15 % SiO₂ und 1.0 % Si angegeben. Die Diskrepanz erklärt sich durch die unterschiedliche Bezugsgröße (SiO₂ vs. elementares Si) und regionale Label-Anforderungen.

### 2.3 Physikalische Eigenschaften

| Eigenschaft | Wert |
|-------------|------|
| Aggregatzustand | Flüssigkeit (klar bis leicht trüb) |
| Farbe | Farblos bis leicht gelblich |
| pH-Wert (Konzentrat) | **5.7** (pH Perfect Formulierung) |
| pH-Effekt auf Lösung | **ALKALISCH** — hebt den pH der Nährlösung |
| Dichte | <!-- DATEN FEHLEN --> |
| EC-Beitrag | ~0.0 mS/cm pro ml/L (vernachlässigbar) |
| Mischbarkeit | Wasserlöslich, benötigt 10–30 Min. Solubilisierung |

**Wichtig zum pH-Verständnis:** Obwohl das Konzentrat einen pH von 5.7 hat (AN-spezifische Formulierung), wirkt Kaliumsilikat in der Nährlösung **alkalisch**. Das liegt daran, dass SiO₃²⁻-Ionen als Protonenakzeptoren wirken und den pH anheben. Der `PhEffect.ALKALINE` im Datenmodell ist korrekt.

---

## 3. Anwendung

### 3.1 Dosierung nach Phase

| Phase | ml/L | EC-Beitrag (mS/cm) | Frequenz | Hinweise |
|-------|------|---------------------|----------|----------|
| Sämling | 1.0 | ~0.0 | Jede Bewässerung | Halbe Dosis |
| Vegetativ | 2.0 | ~0.0 | Jede Bewässerung | Stängelaufbau |
| Blüte Woche 1 | 2.0 | ~0.0 | Jede Bewässerung | Gewicht-Unterstützung |
| Blüte Woche 2 | 2.0 | ~0.0 | Jede Bewässerung | |
| Blüte Woche 3 | 2.0 | ~0.0 | Jede Bewässerung | |
| Blüte Woche 4 | 2.0 | ~0.0 | Jede Bewässerung | |
| Blüte Woche 5 | 2.0 | ~0.0 | Jede Bewässerung | |
| Blüte Woche 6 | 2.0 | ~0.0 | Jede Bewässerung | |
| Blüte Woche 7 | — | — | — | 1 Woche vor Flush absetzen |
| Flush | — | — | — | Nicht anwenden |

### 3.2 Anwendungsmethode

- **Primär:** Fertigation (Bewässerungslösung)
- **Foliar:** Möglich (1 ml/L), aber Fertigation bevorzugt. Silikat wird primär über die Wurzeln aufgenommen und über den Transpirationsstrom in die Zellwände eingebaut.
- **Tank-tauglich:** Ja — mineralisch, keine Verstopfungsgefahr. Allerdings: Lösung mindestens 10–30 Minuten vor Anwendung anmischen, damit sich das Silikat vollständig solubilisiert.

### 3.3 Mischungsreihenfolge & Kompatibilität

**KRITISCH — mixing_priority: 5 — IMMER ZUERST!**

Die Mischungsreihenfolge für Rhino Skin ist die wichtigste Regel im gesamten Nährstoff-Management:

```
1. RHINO SKIN (Priority 5) ← ZUERST in Wasser!
   ↓ 10-30 Minuten warten, umrühren
2. CalMag / Sensi A / Micro (Priority 10)
   ↓ umrühren
3. Sensi B / Grow / Bloom (Priority 15-20)
   ↓ umrühren
4. Big Bud / Overdrive (Priority 30)
5. B-52, Bud Candy, Nirvana (Priority 40)
6. Biologicals (Priority 50)
7. pH-Adjustierung (falls nötig)
```

**Warum ZUERST?**

Kaliumsilikat (K₂SiO₃) reagiert mit Calcium (Ca²⁺) und Magnesium (Mg²⁺) unter Bildung unlöslicher Silikate:

```
Ca²⁺ + SiO₃²⁻ → CaSiO₃ ↓ (Calciumsilikat, unlöslich)
Mg²⁺ + SiO₃²⁻ → MgSiO₃ ↓ (Magnesiumsilikat, unlöslich)
```

Wenn Rhino Skin NACH CalMag oder Base-Nährstoffen hinzugefügt wird:
- Das konzentrierte Silikat trifft auf konzentrierte Ca²⁺/Mg²⁺-Ionen
- Es bilden sich sofort unlösliche Silikat-Niederschläge (weiße Trübung)
- Sowohl Silizium ALS AUCH Calcium/Magnesium werden aus der Lösung entfernt (Lockout)
- Die Pflanze erhält weder Si noch Ca/Mg

Wenn Rhino Skin ZUERST in Wasser gelöst wird:
- Das Silikat wird stark verdünnt
- Wenn danach CalMag hinzugefügt wird, sind die Si-Konzentrationen niedrig genug
- Keine signifikante Ausfällung bei korrekter Verdünnung
- Alle Elemente bleiben in Lösung

**Wartezeit:** Nach Zugabe von Rhino Skin **mindestens 10 Minuten** umrühren und warten, bevor weitere Produkte hinzugefügt werden. Manche Grower empfehlen 30 Minuten. Bei Tank-Systemen: 2 Stunden vor Anwendung anmischen.

**Kompatibilität:**

- Kompatibel mit AN pH Perfect System (pH 5.7 Formulierung)
- **INKOMPATIBEL mit konzentriertem CalMag bei direkter Mischung**
- **INKOMPATIBEL mit konzentriertem H₃PO₄ (Phosphorsäure)** — bildet unlösliches Calciumphosphat in Anwesenheit von Ca
- Bei Fremdherstellern als Base: Zuerst Rhino Skin + Wasser mischen, dann Base hinzufügen

### 3.4 Dosierungs-Schema (AN Feeding Chart)

| Woche | Phase | Rhino Skin ml/L | Position in Mischung |
|-------|-------|----------------|---------------------|
| 1–4 | Vegetativ | 2.0 | IMMER ZUERST |
| 5 (Bloom W1) | Transition | 2.0 | IMMER ZUERST |
| 6–8 (Bloom W2–4) | Peak Blüte | 2.0 | IMMER ZUERST |
| 9–10 (Bloom W5–6) | Spätblüte | 2.0 | IMMER ZUERST |
| 11 (Bloom W7) | Reife | — | Absetzen |
| 12 (Bloom W8) | Flush | — | — |

---

## 4. Wirkungsweise

### 4.1 Silikat-Deposition in Zellwänden

Silizium wird von der Pflanze als monosilicische Säure (H₄SiO₄) über die Wurzeln aufgenommen und mit dem Transpirationsstrom in die oberirdischen Pflanzenteile transportiert. Dort polymerisiert es und wird als amorphes Siliziumdioxid (SiO₂·nH₂O) in die Zellwände, die Cuticula und die Trichome eingelagert:

- **Epidermale Silizifizierung:** Eine Schicht aus amorphem SiO₂ wird unter der Cuticula abgelagert. Diese „Silica-Barriere" ist physisch undurchdringbar für viele pilzliche Hyphen.
- **Zellwand-Verstärkung:** Si wird in die Cellulose-Matrix der Zellwand eingebaut und erhöht deren mechanische Festigkeit um das 2–3-fache.
- **Trichom-Härtung:** Silizium wird bevorzugt in Trichomen akkumuliert und macht diese mechanisch widerstandsfähiger.

### 4.2 Mechanische Stabilität

- **Stängelsteifigkeit:** Silikat-verstärkte Stängel können das 2–3-fache Gewicht tragen im Vergleich zu unbehandelten Pflanzen. In der Blüte, wenn schwere Blüten die Äste belasten, verhindert Silizium Abknicken und Bruch.
- **Wurzelstabilität:** Auch Wurzeln profitieren von der Silikat-Einlagerung — stabilere Wurzelstruktur in Hydroponiksystemen.
- **Reduzierter Bedarf an Stützstrukturen:** SCROG-Netze und Pflanzenstützen werden weniger notwendig.

### 4.3 Biotischer Stress (Pathogen-Abwehr)

Silizium aktiviert die pflanzeneigene Immunabwehr:

- **Physische Barriere:** Die Silica-Schicht unter der Cuticula verhindert das Eindringen von Pilzhyphen (Botrytis, Pythium, Fusarium, Mehltau).
- **SAR-Induktion:** Silizium triggert die Systemisch Erworbene Resistenz (SAR) — die Pflanze produziert Phytoalexine und PR-Proteine.
- **Papilla-Verstärkung:** An Infektionsstellen bildet die Pflanze Silizium-verstärkte Papillen, die das Pathogen blockieren.
- **Relevanz für IPM (REQ-010):** Silizium-behandelte Pflanzen benötigen weniger Fungizid-Behandlungen → weniger Karenz-Konflikte.

### 4.4 Abiotischer Stress

- **Hitzetoleranz:** Si stabilisiert die Zellmembranen und die Photosynthese-Komplexe unter Hochtemperatur-Bedingungen.
- **Salztoleranz:** Si reduziert die Na⁺-Aufnahme und verbessert das K⁺/Na⁺-Verhältnis in den Pflanzengeweben.
- **Trockenstress:** Si reduziert die Transpirationsrate durch Cuticula-Verdickung, ohne die Photosynthese signifikant zu beeinträchtigen.
- **UV-Stress:** Die Silica-Schicht reflektiert UV-Strahlung und schützt die darunter liegenden Zellen.

### 4.5 Trichom-Enhancement

Silizium wird bevorzugt in Trichomen eingelagert:

- Erhöhte Trichom-Dichte und -Größe
- Mechanisch stabilere Trichomköpfe → weniger Verlust bei Handling
- Möglicherweise erhöhte Terpenoid-Retention in stabilisierten Trichomen

---

## 5. Anwendungsfenster & Phasen

| KA-Phase (PhaseName) | Rhino Skin | Begründung |
|-----------------------|-----------|------------|
| GERMINATION | Optional (1 ml/L) | Früher Zellwandaufbau |
| SEEDLING | **Ja** (1 ml/L) | Stängelstabilität |
| VEGETATIVE | **Ja** (2 ml/L) | Maximaler Stängelaufbau |
| FLOWERING Woche 1–6 | **Ja** (2 ml/L) | Gewichtsunterstützung, Pathogenabwehr |
| FLOWERING Woche 7 | Nein | 1 Woche vor Flush absetzen |
| HARVEST | Nein | — |

Rhino Skin wird wie B-52 über fast den gesamten Lebenszyklus eingesetzt. Es ist eines der „Always-On"-Supplements.

---

## 6. Lagerung & Haltbarkeit

| Parameter | Empfehlung |
|-----------|------------|
| Lagertemperatur | 5–30 °C |
| Lichtschutz | Nicht kritisch (anorganische Lösung) |
| Haltbarkeit | Unbegrenzt bei korrekter Lagerung (mineralische Lösung) |
| Frostschutz | Nicht einfrieren — Silikat kann bei niedrigen Temperaturen gelieren |
| Besonderheit | Flasche fest verschließen — CO₂ aus der Luft kann den pH senken und Silikat-Gel bilden |
| Hinweis | Bei Gelierung (dickflüssig, trüb) nicht mehr verwenden |

---

## 7. Sicherheitshinweise

- **Nicht zum Verzehr geeignet**
- **Hautkontakt:** Silikat-Lösungen sind leicht alkalisch — längeren Hautkontakt vermeiden, mit Wasser abwaschen
- **Augenkontakt:** **Sofort mit reichlich Wasser spülen** — Silikat kann Augenreizungen verursachen. Bei anhaltender Reizung Arzt konsultieren.
- **pH-Warnung:** Obwohl Rhino Skin einen pH von 5.7 hat, ist die konzentrierte Lösung alkalisch wirkend. Unverdünnt nicht auf Pflanzen auftragen.
- **Kindersicher aufbewahren**
- **GHS-Einstufung:** Nicht als Gefahrstoff eingestuft (bei AN-Formulierung mit pH 5.7)
- **Generische Kaliumsilikat-Warnung:** Reines Kaliumsilikat (pH 11+) ist ÄTZEND. Rhino Skin ist NICHT reines Kaliumsilikat!
- **SDS:** https://www.advancednutrients.com/safety-data-sheets-library/

---

## 8. Praxistipps

1. **10-30 Minuten Solubilisierung:** Rhino Skin ZUERST in Wasser geben und mindestens 10 Minuten umrühren/warten, bevor weitere Produkte hinzugefügt werden. In großen Tanks (60L+) 30 Minuten einplanen. Die Silizium-Ionen benötigen Zeit, um ihre Bindungen im Wasser zu stabilisieren.

2. **Trübungstest:** Wenn nach Zugabe aller Nährstoffe die Lösung milchig-weiß wird, ist Silikat ausgefallen. Lösung verwerfen! Ursache ist meist: (a) Rhino Skin nicht ZUERST hinzugefügt, (b) zu wenig Wartezeit, oder (c) zu hoch konzentrierte Lösung.

3. **Nicht überdosieren:** Mehr als 2 ml/L Rhino Skin bringt keinen Zusatznutzen. Silizium wird von der Pflanze bedarfsgerecht aufgenommen — Überschuss wird einfach nicht absorbiert und erhöht nur den pH der Nährlösung.

4. **pH-Korrektur NACH Rhino Skin:** Rhino Skin hebt den pH. Die pH-Adjustierung (Down) immer NACH allen anderen Nährstoffen durchführen. Bei pH Perfect AN-Base wird der pH automatisch korrigiert.

5. **Kontinuierliche Anwendung:** Silizium-Deposition in den Zellwänden ist ein kumulativer Prozess. Einzelne Anwendungen haben wenig Effekt — nur kontinuierliche Zufuhr über Wochen zeigt Ergebnisse. Nicht intermittierend einsetzen.

6. **Nicht mit konzentrierten Säuren mischen:** Rhino Skin NIEMALS mit pH-Down oder anderen Säuren direkt mischen (ohne Verdünnung). Silikat + Säure = sofortige Gelierung.

7. **Coco-Besonderheit:** In Coco-Substrat kann Si an die Kationenaustausch-Sites des Kokos binden. Eine leicht erhöhte Dosierung (2.5 ml/L) kann sinnvoll sein, ist aber selten nötig.

8. **SCROG/LST-Reduktion:** Grower, die kontinuierlich Rhino Skin verwenden, berichten von 30–50 % weniger Bedarf an Pflanzenstützen und SCROG-Netzen in der Blüte.

---

## 9. Alternativen & Vergleich

| Produkt | Hersteller | Si-Gehalt | K₂O | pH (Konzentrat) | Mischung ZUERST? | Preis |
|---------|-----------|-----------|-----|-----------------|-----------------|-------|
| **Rhino Skin** | Advanced Nutrients | 0.15 % SiO₂ | 0.4 % | 5.7 | Ja | Premium |
| Silica Blast | Botanicare | 0.5 % Si | — | ~10.5 | Ja | Mittel |
| Pro-TeKt | Dyna-Gro | 3.7 % Si | 7.8 % | ~11.5 | Ja | Budget |
| Armor Si | General Hydroponics | 0.5 % Si | 3.6 % | ~10+ | Ja | Mittel |
| Power Si Original | Power Si | 0.6 % Si | — | <!-- DATEN FEHLEN --> | Ja | Premium |
| Mills Vitalize | Mills | 0.2 % Si | 0.35 % | ~7.0 | Ja | Premium |

**Wesentlicher Unterschied:** Rhino Skin hat einen deutlich niedrigeren Si-Gehalt als Pro-TeKt (0.15 % vs. 3.7 %) und ist dafür pH-stabil bei 5.7. Generische Silikat-Produkte (pH 10–12) erfordern eine aggressivere pH-Korrektur. Für Grower im AN pH Perfect-Ökosystem ist Rhino Skin die nahtloseste Lösung; für preisbewusste Grower ist Pro-TeKt die kosteneffektivste Alternative.

---

## 10. KA-Datenmodell-Mapping

Mapping auf das Kamerplanter `Fertilizer`-Modell (`src/backend/app/domain/models/fertilizer.py`):

```python
Fertilizer(
    product_name="Rhino Skin",
    brand="Advanced Nutrients",
    fertilizer_type=FertilizerType.SUPPLEMENT,
    is_organic=False,                               # Mineralisch (Kaliumsilikat)
    tank_safe=True,
    recommended_application=ApplicationMethod.FERTIGATION,
    npk_ratio=(0.0, 0.0, 0.0),                     # Kein signifikanter NPK-Beitrag
                                                    # (0.4 % K₂O ist vernachlässigbar)
    ec_contribution_per_ml=0.0,                     # Kein EC-Beitrag
    mixing_priority=5,                              # ← NIEDRIGSTE PRIORITÄT = ZUERST MISCHEN!
                                                    # Vor ALLEN anderen Produkten
    ph_effect=PhEffect.ALKALINE,                    # ← EINZIGES alkalisches AN-Produkt
    bioavailability=Bioavailability.IMMEDIATE,       # Mineralisch, sofort verfügbar
    shelf_life_days=None,                           # Unbegrenzt (mineralische Lösung)
    storage_temp_min=5.0,
    storage_temp_max=30.0,
    notes=(
        "Kaliumsilikat — stärkt Zellwände. VOR allen anderen Düngern hinzufügen! "
        "10-30 Min. Solubilisierung vor weiteren Zugaben. "
        "Silikat fällt bei Kontakt mit konzentriertem Ca/Mg aus (weiße Trübung). "
        "pH alkalisch — einziges AN-Produkt mit PhEffect.ALKALINE."
    ),
)
```

**Sonderstellungen im Datenmodell:**

| Feld | Wert | Besonderheit |
|------|------|-------------|
| `mixing_priority` | **5** | Niedrigster Wert aller Produkte = wird zuerst gemischt |
| `ph_effect` | **PhEffect.ALKALINE** | Einziges Produkt mit alkalischer Wirkung |
| `ec_contribution_per_ml` | **0.0** | Kein EC-Beitrag trotz 0.4 % K₂O |
| `npk_ratio` | **(0.0, 0.0, 0.0)** | K₂O: 0.4 % ist unter Abrundungsschwelle |

**MixingSafetyValidator-Relevanz:**

Der `MixingSafetyValidator` in `src/backend/app/domain/engines/nutrient_engine.py` muss bei der Validierung der Mischungsreihenfolge sicherstellen:

1. Rhino Skin (priority 5) wird vor CalMag/Sensi A (priority 10) gemischt
2. Zwischen Rhino Skin und CalMag-Zugabe liegt eine Wartezeit (programmatisch: Hinweis im Plan)
3. Kein Produkt mit `ph_effect=PhEffect.ALKALINE` darf NACH einem CalMag-Produkt ohne Warnung gemischt werden

**NutrientPlanPhaseEntry-Zuordnung:**

| PhaseName | dosage_ml_per_l | Aktiv |
|-----------|----------------|-------|
| SEEDLING | 1.0 | Ja |
| VEGETATIVE | 2.0 | Ja |
| FLOWERING (W1–W6) | 2.0 | Ja |
| FLOWERING (W7+) | — | Nein (Flush-Vorbereitung) |
| HARVEST | — | Nein |

---

## Quellenverzeichnis

- Advanced Nutrients — Rhino Skin Produktseite: https://www.advancednutrients.com/products/rhino-skin/
- Advanced Nutrients — Potassium Silicate Article: https://www.advancednutrients.com/articles/potassium-silicate-for-plants/
- Advanced Nutrients — Feeding Charts: https://www.advancednutrients.com/feeding/
- Advanced Nutrients — Safety Data Sheets: https://www.advancednutrients.com/safety-data-sheets-library/
- Hydrobuilder — Rhino Skin: https://hydrobuilder.com/products/advanced-nutrients-rhino-skin
- HTG Supply — Rhino Skin: https://www.htgsupply.com/products/advanced-nutrients-rhino-skin/
- Planet Natural — Rhino Skin: https://www.planetnatural.com/product/rhino-skin-potassium-silicate/
- Hydrobuilder Learning Center — Mixing Order: https://learn.hydrobuilder.com/mixing-plant-nutrients/
- Rollitup — Silica Mixing Discussion: https://www.rollitup.org/t/silica-in-nutrients-mix-first-or-last.938960/
- 420 Magazine — Silica CalMag Mixing Order: https://www.420magazine.com/community/threads/mixing-mc-si-calmag-nutrient-order.511984/
