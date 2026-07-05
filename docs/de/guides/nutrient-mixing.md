# Nährlösung mischen

Eine korrekt gemischte Nährlösung ist die Grundlage für gesundes Pflanzenwachstum. Kamerplanter berechnet automatisch EC-Budgets (das verfügbare Leitfähigkeits-Kontingent der Nährstoffe), skaliert Herstellerrezepte und validiert die Mischfolge — so werden Ausfällungen und Wirkungsverluste verhindert.

!!! info "Zwei Begriffe vorab: Fertigation und Drain-to-Waste"
    **Fertigation** ("Fertilizer" + "Irrigation") bezeichnet das automatisierte Ausbringen von Nährlösung über die Bewässerung — meist per Tropfsystem und Pumpe, statt von Hand mit der Gießkanne. In Kamerplanter ist Fertigation eine der [Ausbringungsmethoden](../user-guide/fertilization.md#ausbringungskanaele-multi-channel-delivery) neben Gießen, Blattdüngung und Aufstreuen.

    **Drain-to-Waste** ("zum Abfluss entwässern") ist eine Bewässerungsstrategie ohne Rezirkulation. Du gießt bewusst mit einem Überschuss (meist 10–30 % mehr als das Substrat aufnehmen kann), sodass am Topfboden Ablaufwasser (Runoff) entsteht. Dieses wird verworfen statt wiederverwendet — im Gegensatz zu rezirkulierenden Systemen wie NFT (Nutrient Film Technique) oder Ebb & Flow. Der Vorteil: Salzanreicherung im Substrat wird verhindert, weil überschüssige Nährstoffe ausgespült statt wiederverwendet werden. Mehr dazu im Abschnitt [Ablaufanalyse](#ablaufanalyse-runoff) unten.

!!! danger "Mischfolge einhalten"
    CalMag (Calcium-Magnesium-Supplement) **immer zuerst** in Wasser einrühren, bevor andere Dünger hinzugefügt werden — insbesondere vor Sulfaten und Phosphaten. Falsche Reihenfolge führt zu Calciumsulfat-Ausfällungen (CaSO₄) und unwirksamer Nährlösung.

---

## Voraussetzungen

- EC-Messgerät (Leitfähigkeitsmessgerät)
- pH-Messgerät oder -Tester
- Bekannte EC-Werte des Gieß-/Mischwassers (Leitungswasser oder RO-Wasser)
- Dünger in Kamerplanter angelegt (unter **Düngung → Düngemittel**)

---

## Das EC-Budget-Modell

Das **EC-Budget** (Netto-Leitfähigkeitsspielraum) gibt an, wie viel elektrische Leitfähigkeit die Düngemittel noch beisteuern dürfen — abzüglich der bereits im Gießwasser enthaltenen Grundleitfähigkeit:

```
EC_netto = EC_ziel - EC_mischwasser
```

| Variable | Bedeutung | Beispielwert |
|----------|-----------|-------------|
| `EC_ziel` | Gewünschte End-EC der Nährlösung | 1,8 mS/cm |
| `EC_mischwasser` | EC des verwendeten Gießwassers | 0,4 mS/cm |
| `EC_netto` | Verbleibender Spielraum für Dünger | 1,4 mS/cm |

!!! tip "RO-Wasser für maximale Kontrolle"
    Umkehrosmosewasser (RO-Wasser) hat typisch EC < 0,05 mS/cm und gibt das volle EC-Budget für Nährstoffe frei. Hartes Leitungswasser mit hohem Ca/Mg-Gehalt reduziert das Budget erheblich.

---

## Die 3-stufige EC-Budget-Berechnungspipeline

**Pipeline** bezeichnet hier die mehrstufige Abfolge von Berechnungsschritten, die Kamerplanter intern durchläuft, bevor eine fertige Mischanleitung ausgegeben wird.

### Stufe 1 — Wassergemisch (EC_mix)

Bei Mischbetrieb aus RO- und Leitungswasser berechnet Kamerplanter zuerst die EC des Gemisches:

```
EC_mix = EC_leitungswasser × (1 - RO_Anteil) + EC_RO × RO_Anteil
```

**Beispiel:** 50 % RO (EC 0,02) + 50 % Leitungswasser (EC 0,50):
```
EC_mix = 0,50 × 0,50 + 0,02 × 0,50 = 0,26 mS/cm
```

### Stufe 2 — EC-Aufteilung (Budget-Segmente)

Das EC-Netto-Budget wird in Segmente aufgeteilt (in dieser Reihenfolge):

| Segment | Priorität | Beschreibung |
|---------|-----------|-------------|
| Silikat | 1 (erster Abzug) | Optionales Silikat wird vorab kalkuliert |
| CalMag | 2 | Calcium-Magnesium-Lösung (Pflichtbestandteil bei Coco/Hydro) |
| pH-Reserve | 3 | Puffer für pH-Adjuster (0,02–0,05 mS je nach Wasserhärte) |
| Basisdünger | 4 | Restbudget wird auf Basisdünger verteilt |

!!! tip "So findest du diese Werte im Nährstoff-Rechner"
    Im Mischprotokoll (**Düngung → Nährstoff-Berechnungen → Mischprotokoll**) trägst du die Karbonathärte deines Wassers als **Alkalinität** (ppm CaCO₃) ein. Kamerplanter berechnet daraus automatisch die pH-Reserve und zeigt sie zusammen mit dem Netto-EC-Budget (`ec_net`) und der Gültigkeit des Rezepts (`valid`) im Ergebnis an. Details zur Bedienung: [Dünge-Logik — Alkalinität und pH-Reserve](../user-guide/fertilization.md#alkalinitaet-und-ph-reserve).

### Stufe 3 — Rezeptskalierung

Wenn Herstellerrezepte (ml/L je Dünger) in Kamerplanter hinterlegt sind, skaliert das System proportional:

```
k = EC_netto / EC_rezept_voll
Dosis_i = k × Rezeptdosis_i
```

Ohne Rezeptangaben: Gleichmäßige Verteilung des EC-Budgets auf alle Basisdünger.

---

## Mischfolge — Schritt für Schritt

Die Reihenfolge beim Mischen ist kritisch. Kamerplanter generiert automatisch eine nummerierte Mischanleitung:

```
1. Behälter mit [X] Liter Wasser füllen
2. Silikat hinzufügen — kräftig rühren, 5 Min. warten
3. CalMag hinzufügen — gründlich mischen
4. Basisdünger A hinzufügen — rühren
5. Basisdünger B hinzufügen — rühren
6. pH anpassen (Ziel: [X]) — rühren, 5 Min. warten
7. Endwert EC messen und bestätigen
```

!!! warning "Warum Silikat vor CalMag?"
    Silikat (SiO₄²⁻) bildet mit Calcium-Ionen (Ca²⁺) schwerlösliches Calciumsilikat (CaSiO₃). Daher muss Silikat zuerst ins Wasser, bevor CalMag zugegeben wird — sonst fällt der Wirkstoff aus.

---

## Inkompatibilitäten und Sicherheitsvalidierung

Kamerplanter prüft automatisch folgende Kombinationen:

| Kombination | Risiko | Schweregrad |
|-------------|--------|-------------|
| CalMag + Sulfate (z. B. Epsom) | Gipsfällung (CaSO₄) | Kritisch |
| CalMag + Phosphate | Calciumphosphat-Fällung | Kritisch |
| Silikat + CalMag (falsche Reihenfolge) | CaSiO₃-Fällung | Kritisch |
| Eisenchelat + pH > 7 | Chelat destabilisiert | Warnung |
| Nur-Blattdünger + Fertigationsdünger | Falsche Anwendung | Hinweis |

!!! danger "Kritische Warnungen sofort beachten"
    Erscheint eine rote Warnung in der Mischanleitung, höre sofort auf und prüfe die Dünger-Kombination. Eine ausgefällte Lösung lässt sich nicht mehr retten — komplettes Neuansetzen erforderlich.

---

## EC-Zielwerte nach Phase und Substrat {#ec-ziel-substrat}

Kamerplanter validiert die berechnete End-EC gegen phasen- und substratspezifische Maximalwerte:

<!-- Quelle: src/backend/app/domain/engines/ec_budget_engine.py EC_MAX_TABLE (REQ-004-A §4.2) -->

| Substrat | Sämling (mS) | Vegetativ (mS) | Blüte (mS) | Ausspülung (mS) |
|----------|-------------|----------------|-----------|-----------------|
| Hydroponik | 0,8 – 1,2 | 1,6 – 2,4 | 1,8 – 2,8 | 0,0 – 0,3 |
| Coco | 0,8 – 1,0 | 1,6 – 2,0 | 1,8 – 2,4 | 0,0 – 0,3 |
| Erde | 0,4 – 0,6 | 0,8 – 1,4 | 1,0 – 1,6 | 0,0 – 0,3 |

!!! tip "Frisches Coco: CalMag-Boost automatisch"
    Bei frisch angesetzten Coco-Batches (0 Nutzungszyklen) erhöht Kamerplanter die CalMag-Dosis automatisch um 20 %, da ungenutztes Coco Calcium und Magnesium aus der Lösung aufnimmt (Kationenaustausch).

---

## Flush und Ruhephase: automatisch ohne Düngung {#flush-ruhephase-ohne-duengung}

Ergänzend zur Tabelle oben gilt für zwei Phasen eine feste Regel, die Kamerplanter automatisch anwendet: Für die Phasen **Spülung (Flush)** und **Ruhephase (Winterruhe/Dormanz)** berechnet das Nährstoffprofil der Phase immer **0:0:0** (keine Düngung) — unabhängig vom sonst hinterlegten Rezept. In der Nährstoff-Ansicht der jeweiligen Phase (siehe [Wachstumsphasen](../user-guide/growth-phases.md#npk-profil)) erscheint dafür der Chip „Keine Düngung (Flush / Ruhephase)". Für dein Mischprotokoll bedeutet das: In diesen Phasen entfällt das Ansetzen einer Nährlösung komplett — du gießt nur mit klarem Wasser.

Zusätzlich prüft Kamerplanter den Ziel-pH-Wert jeder Phase auf **Mikronährstoff-Verfügbarkeit**: Liegt der Ziel-pH außerhalb des optimalen Fensters von pH 6,0–6,5, sperren sich Eisen, Mangan, Zink, Kupfer und Bor zunehmend aus der Aufnahme (Chlorose-Risiko — helle, gelbliche Blattadern). Kamerplanter zeigt diese Warnung als „Spurennährstoffe blockiert (pH-Sperre)" in der Nährstoff-Ansicht der Phase an.

---

## EC-Temperaturkorrektur (EC@25)

Die elektrische Leitfähigkeit eines Messwerts hängt von der Wassertemperatur ab — dieselbe Nährlösung zeigt bei wärmerem Wasser eine höhere EC an als bei kühlerem. Damit Messungen bei unterschiedlichen Temperaturen vergleichbar bleiben, korrigiert Kamerplanter optional auf die Referenztemperatur 25 °C:

```
EC@25 = EC_gemessen / (1 + 0,02 × (T − 25))
```

Trägst du im [EC-Budget-Rechner](../user-guide/fertilization.md#wasser-mischer-und-ec-budget-rechner) sowohl deinen gemessenen EC-Wert als auch die Wassertemperatur ein, berechnet Kamerplanter automatisch diesen korrigierten Wert und zeigt ihn zusätzlich zur unkorrigierten Messung an.

!!! example "Beispiel"
    Du misst 1,9 mS/cm bei 30 °C Wassertemperatur. Korrigiert auf 25 °C: `EC@25 = 1,9 / (1 + 0,02 × 5) = 1,9 / 1,1 ≈ 1,73 mS/cm`. Der unkorrigierte Wert würde die Nährlösung stärker erscheinen lassen, als sie bei Referenztemperatur tatsächlich ist.

---

## pH-Wert einstellen

Nach dem Mischen der Dünger pH-Wert messen und korrigieren:

| Substrat | Ziel-pH-Bereich | Hinweis |
|----------|----------------|---------|
| Hydroponik | 5,5 – 6,0 | Nährstoffaufnahme-Optimum |
| Coco | 5,8 – 6,2 | Leicht höher als Hydro |
| Erde | 6,0 – 6,8 | Mikrobielle Aktivität berücksichtigen |
| Lebendige Erde | 6,2 – 7,0 | pH durch Bodenbiologie gepuffert |

Kamerplanter gibt Anweisungen, ob pH Up (Kalilauge) oder pH Down (Phosphorsäure) benötigt wird.

!!! warning "pH erst nach Düngerzugabe einstellen"
    pH-Korrekturen immer als letzten Schritt durchführen — nach dem Einmischen aller Nährstoffe. Dünger verändern den pH und könnten eine erneute Korrektur erfordern.

---

## Ablaufanalyse (Runoff) {#ablaufanalyse-runoff}

Beim Drain-to-Waste-Betrieb (Coco, Rockwool) liefert die Ablaufanalyse wichtige Informationen:

| Messgröße | Zielbereich | Abweichung → Maßnahme |
|-----------|-------------|----------------------|
| Ablauf-EC − Zufuhr-EC | ±0,3 mS/cm | > +0,5: Salzanreicherung → Spülung |
| Ablauf-pH − Zufuhr-pH | ±0,5 | > ±0,5: Substrat-Pufferung prüfen |
| Ablaufmenge / Zufuhr | 10 – 30 % | < 10 %: Wassermenge erhöhen |

!!! example "Typisches Spülsignal"
    Ablauf-EC = 2,8 mS, Zufuhr-EC = 2,0 mS → Delta = +0,8 mS (über Schwellenwert 0,5). Kamerplanter empfiehlt 1–2 Spülgänge mit klarem Wasser (EC < 0,3 mS, pH 6,0).

---

## Ausspülung (Flushing) vor der Ernte {#flush-substrat}

Kamerplanter berechnet automatisch einen Ausspülungsplan über den [Spülungs-Rechner](../user-guide/fertilization.md#spulung-berechnen-flushing). Die empfohlene Spüldauer hängt vom Substrat ab:

<!-- Quelle: src/backend/app/domain/engines/nutrient_engine.py FlushingProtocol.FLUSH_DURATIONS -->

| Substrat | Empfohlene Spüldauer |
|----------|----------------------|
| Hydroponik | 7 – 14 Tage |
| Coco | 10 – 21 Tage |
| Rockwool | 7 – 14 Tage |
| Erde | 14 – 30 Tage |

**Ausspülungsprotokoll (3-Phasen-Reduktion):**

| Zeitabschnitt (% der Spülzeit) | Ziel-EC | Maßnahme |
|---------------------------------|---------|----------|
| Erste 30 % | 50 % der Ursprungs-EC | Reduzierte Nährlösung |
| Mittlere 30 % | 25 % der Ursprungs-EC | Vierteldosis |
| Letzte 40 % | 0,0 mS/cm | Reines Wasser |

---

## Temperatur des Mischwassers

Die Wassertemperatur beeinflusst Löslichkeit und biologische Wirksamkeit:

| Temperatur | Bewertung |
|-----------|-----------|
| < 5 °C | Zu kalt — schlechte Auflösung, Ausfällungsrisiko |
| 5 – 18 °C | Suboptimal — länger rühren |
| 18 – 22 °C | Optimal |
| 22 – 30 °C | Akzeptabel — biologische Produkte können sich schneller abbauen |
| > 35 °C | Nicht für biologische Dünger geeignet |

---

## Häufige Fragen

??? question "Meine Lösung ist weißlich/trüb nach dem Mischen — was ist passiert?"
    Trübung deutet auf Ausfällungen hin. Häufigste Ursache: CalMag wurde nach einem Sulfat oder Phosphat zugegeben. Lösung entsorgen, Behälter mit warmem Wasser spülen, Mischfolge korrigieren und neu ansetzen.

??? question "Kann ich alle Dünger gleichzeitig ins Wasser kippen?"
    Nein. Besonders CalMag und Sulfat/Phosphat dürfen nicht gleichzeitig kontaktieren — das führt sofort zu Ausfällungen. Immer schrittweise vorgehen und zwischen den Zugaben rühren.

??? question "Wie oft sollte ich EC und pH der fertigen Lösung messen?"
    Immer direkt nach dem Mischen. Bei Tankbetrieb (Reservoir) zusätzlich täglich — EC steigt durch Wasserverdunstung und pH driftet durch Pflanzenstoffwechsel.

??? question "Was bedeutet 'nicht tanksicher' bei einem Dünger?"
    Dünger, die nicht tanksicher sind, dürfen nicht im Vorratstank über längere Zeit gelagert werden — sie zersetzen sich oder fallen aus. Sie müssen frisch vor jeder Gabe gemischt werden.

---

## Siehe auch

- [Dünge-Logik](../user-guide/fertilization.md)
- [Gießprotokoll](../user-guide/watering-log.md) — Runoff-Analyse pro Eintrag
- [Tankmanagement](../user-guide/tanks.md)
- [VPD-Optimierung](vpd-optimization.md)
- [Wachstumsphasen](../user-guide/growth-phases.md#npk-profil) — phasenabhängiges Nährstoffprofil
