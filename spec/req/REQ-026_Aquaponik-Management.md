# Spezifikation: REQ-026 - Aquaponik-Management

```yaml
ID: REQ-026
Titel: Aquaponik-Management — Fisch-Pflanzen-Kreislaufsysteme
Kategorie: Aquaponik
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story (Hobby-Aquaponiker):** "Als Hobby-Aquaponiker mit einem Tilapia-Salat-DWC-System möchte ich meinen Stickstoffkreislauf (Ammoniak → Nitrit → Nitrat) überwachen und bei kritischen Wasserwerten sofort gewarnt werden — damit meine Fische und Pflanzen gesund bleiben und ich rechtzeitig eingreifen kann."

**User Story (Kommerzieller Betreiber):** "Als Betreiber einer Forellen-Kräuter-Aquaponikanlage möchte ich die tägliche Futtermenge temperaturkorrigiert berechnen lassen, Nährstoffdefizite (Eisen, Kalium, Calcium) erkennen und die erlaubten Ergänzungsmittel dokumentieren — damit mein System stabil produziert und ich keine fischgiftigen Substanzen versehentlich einsetze."

**User Story (Einsteiger — Cycling):** "Als Aquaponik-Einsteiger, der seine erste Anlage einrichtet, möchte ich den Cycling-Fortschritt meines Biofilters verfolgen und wissen, wann ich die Besatzdichte erhöhen und die Futtermenge steigern kann — damit ich keine Fische durch Ammoniak- oder Nitrit-Spikes verliere."

**Beschreibung:**

Das System führt **Aquaponik** als eigenständiges Anwendungsgebiet ein, in dem Fischzucht und Pflanzenanbau in einem geschlossenen Wasser-Nährstoff-Kreislauf gekoppelt sind. Fische scheiden Ammoniak aus, Bakterien im Biofilter wandeln diesen über Nitrit zu pflanzenverfügbarem Nitrat um, und die Pflanzen reinigen das Wasser für die Fische.

REQ-026 baut auf der bestehenden Tank-Infrastruktur (REQ-014), der Sensorik (REQ-005), der Dünge-Logik (REQ-004) und der Standortverwaltung (REQ-002) auf. Die zentrale Neuerung sind **Fisch-Entitäten**, der **Stickstoffkreislauf** als Kernüberwachungskonzept und eine **Sicherheitsschicht**, die fischgiftige Substanzen (synthetische Dünger, Chlor, Kupfer-Pestizide) in Aquaponik-Systemen blockiert.

**Kernkonzepte:**

**Stickstoffkreislauf (Nitrogen Cycle):**
Der biologische Kern jedes Aquaponik-Systems:
1. Fische scheiden **Ammoniak** (NH3/NH4+) über Kiemen und Urin aus
2. **Nitrosomonas**-Bakterien im Biofilter oxidieren Ammoniak zu **Nitrit** (NO2-)
3. **Nitrobacter/Nitrospira**-Bakterien oxidieren Nitrit zu **Nitrat** (NO3-)
4. Pflanzen nehmen **Nitrat** als Stickstoffquelle auf und reinigen so das Wasser

**TAN vs. freies Ammoniak — kritische Unterscheidung:**
Ammoniak existiert im Wasser als Gleichgewicht zwischen ionisiertem Ammonium (NH4+, relativ ungiftig) und unionisiertem Ammoniak (NH3, hochgiftig). Das Verhältnis ist **stark pH- und temperaturabhängig**:
- Bei pH 7.0 / 25°C: nur ca. 0.6% des TAN liegt als giftiges NH3 vor
- Bei pH 8.0 / 25°C: ca. 5.4% als NH3
- Bei pH 9.0 / 25°C: ca. 36% als NH3

Das System muss daher **TAN (Total Ammonia Nitrogen)** zusammen mit pH und Temperatur erfassen und daraus den freien NH3-Anteil berechnen. Der sichere Grenzwert für freies NH3 liegt bei **<0.02 mg/L**. Die TAN-Grenzwerte variieren artspezifisch (siehe Seed-Daten).

**Berechnung des freien Ammoniaks (Emerson et al. 1975):**
```
fraction_NH3 = 1 / (10^(pKa - pH) + 1)
wobei pKa = 0.09018 + 2729.92 / T_kelvin
free_NH3 = TAN × fraction_NH3
```

**Testvektor:** pH 7.0, 25°C (298.15K) → pKa ≈ 9.245 → fraction ≈ 0.0057 → bei TAN 1.0 mg/L → NH3 = 0.0057 mg/L

**Systemtypen:**

| Systemtyp | Beschreibung | Biofilter | Substrat | Geeignet für |
|-----------|-------------|-----------|----------|-------------|
| `media_bed` | Growbed mit Blähton als kombiniertes Grow- und Filtermedium | Integriert im Substrat | clay_pebbles (REQ-019) | Hobby, Einsteiger |
| `dwc` | Deep Water Culture — schwimmende Pflanzflöße | Separater Biofilter nötig | none (REQ-019) | Salat, Kräuter |
| `nft` | Nutrient Film Technique — dünner Wasserfilm | Separater Biofilter nötig | none (REQ-019) | Kräuter, Blattgemüse |
| `hybrid` | Kombination aus Media-Bed und DWC/NFT | Media-Bed + optional separat | Gemischt | Fortgeschritten |
| `wicking_bed` | Dochtbewässerung aus Reservoir | Separater Biofilter nötig | Erde/Coco über Reservoir | Outdoor, robust |

**Biofilter-Management:**

Ein Biofilter muss **eingefahren (cycling)** werden, bevor Fische in voller Besatzdichte eingesetzt werden können. Die Nitrifikationsbakterien benötigen 4–8 Wochen, um sich ausreichend zu vermehren.

| Status | Beschreibung | Dauer | Fische erlaubt? |
|--------|-------------|-------|-----------------|
| `new` | Biofilter frisch befüllt, keine Bakterien | — | Nein (nur Ammoniakquelle) |
| `cycling` | Bakterien bauen sich auf, Ammonia- und Nitrit-Spikes | 4–8 Wochen | Wenige (≤25% Zielbbesatz) |
| `cycled` | Stabile Nitrifikation, keine Spikes | — | Ja (volle Besatzdichte) |
| `dormant` | Winterruhe, Bakterien inaktiv bei <10°C | Winter | Reduziert |

**Cycling-Erkennung:** Der Status wird anhand der Wassertest-Historie automatisch erkannt:
- `new → cycling`: Erster TAN-Messwert >0.5 mg/L
- `cycling`: Ammonia-Peak → Nitrit-Peak → beide fallen → Nitrat steigt
- `cycling → cycled`: TAN <0.25 mg/L UND NO2 <0.1 mg/L für ≥7 aufeinanderfolgende Tage bei ≥80% der `daily_feed_target_g` UND Wassertemperatur >15°C
- `cycled → dormant`: Wassertemperatur <10°C für ≥7 Tage
- `dormant → cycling`: Wassertemperatur >15°C UND Fütterung wieder aufgenommen (Biofilter muss sich reaktivieren)

**Feststoff-Management und Mineralisierung:**

Fischfeststoffe (Kot, Futterreste) enthalten ca. 60–70% der Gesamtnährstoffe, aber in partikulärer, pflanzenunsichtbarer Form. Ohne mechanische Separation und biologische Mineralisierung gehen diese Nährstoffe verloren und Systeme (insbesondere NFT/DWC) verstopfen.

- **Separation:** Mechanische Entfernung von Feststoffen vor dem Growbed (Swirl Filter, Sedimentationsbecken, Trommelfilter)
- **Mineralisierung:** Aerober Abbau der Feststoffe zu pflanzenverfügbaren Ionen in einem separaten Tank (12–24h Verweildauer)
- **Wasserfluss:** Fishtank → Clarifier (Separation) → Biofilter → Growbed → Sump → Fishtank
- Bei Media-Bed-Systemen übernimmt das Substrat teilweise die Filter- und Mineralisierungsfunktion

**Nährstoffdefizite und erlaubte Supplementierung:**

Aquaponik-Systeme haben systembedingte Nährstoffdefizite, da Fischfutter nicht alle pflanzlichen Bedürfnisse abdeckt:

| Nährstoff | Defizit-Häufigkeit | Symptom | Erlaubtes Ergänzungsmittel | Zielwert |
|-----------|-------------------|---------|---------------------------|----------|
| Eisen (Fe) | Sehr häufig | Zwischenadern-Chlorose (junge Blätter) | Fe-DTPA (bis pH 7.5) oder Fe-EDDHA (bis pH 9.0). **Kein Fe-EDTA** (instabil >pH 6.5) | 2–5 ppm |
| Kalium (K) | Häufig | Blattrandnekrose, schwache Fruchtbildung | KOH oder K2CO3 (hebt gleichzeitig pH) | 150–300 ppm |
| Calcium (Ca) | Häufig (bei Osmose/Regenwasser) | Blütenend-Fäule (Tomaten), Tip-Burn (Salat) | Ca(OH)2 (hebt gleichzeitig pH). Alternierend mit KOH für gleichzeitige K+Ca-Versorgung | 40–120 ppm |
| Magnesium (Mg) | Mäßig | Intervenale Chlorose (alte Blätter) | MgSO4 (Bittersalz) — pH-neutral, fischsicher | 15–50 ppm |
| Mangan (Mn) | Bei pH >7.0 | Intervenale Chlorose, kleinere Blätter | MnSO4 — nur bei Mangelsymptomen | 0.5–2 ppm |
| Zink (Zn) | Bei pH >7.0 | Intervenale Chlorose, kleinblättrig, gestaucht | ZnSO4 — nur bei Mangelsymptomen | 0.03–0.1 ppm |
| Bor (B) | Selten, aber kritisch | Hohlstängel, Blütenabwurf, Korkbildung | H3BO3 (Borsäure) — **sehr enger Toxizitätsbereich!** Überdosierung >1 ppm schädigt Pflanzen UND Fische | 0.1–0.5 ppm |
| Kupfer (Cu) | Selten | Welke junger Triebe, chlorotische Blätter | Monitoring — Ergänzung nur unter Aufsicht! Fischgiftig >0.1 ppm. Kupfer-PSM sind verboten (REQ-010). | 0.02–0.06 ppm |
| Phosphat (PO4) | Selten (meist ausreichend durch Futter) | Violette Blätter, gehemmtes Wurzelwachstum | Monitoring — Ergänzung selten nötig. **Achtung Akkumulation:** Bei >80 ppm Teilwasserwechsel oder Pflanzen mit hohem P-Bedarf (Tomaten, Paprika) einsetzen. Phosphat-Überangebot reduziert Eisenverfügbarkeit (Fe-P-Präzipitation) und fördert Algenblüten. | 10–60 ppm |

**Kritische Regel zur pH-Korrektur:** In Aquaponik-Systemen dürfen **keine Säuren** als pH-Down verwendet werden (Einsteiger: Hard-Block). Der pH senkt sich natürlich durch die Säureproduktion bei der Nitrifikation. Wenn der pH zu hoch ist, läuft die Nitrifikation bereits — abwarten ist die korrekte Maßnahme. pH-Up erfolgt alternierend mit KOH (Kalium) und Ca(OH)2 (Calcium), um Pflanzen gleichzeitig mit K und Ca zu versorgen.

**Ausnahme für Experten (REQ-021 Erfahrungsstufe "expert"):** Phosphorsäure (H3PO4) in Kleinstmengen (max 0.5 mL/100L) ist bei sehr hartem Leitungswasser (KH >15°dH) zulässig, wenn die Nitrifikation den pH nicht ausreichend senkt. pH darf dabei nie unter 6.5 gesenkt werden. Salpetersäure (HNO3) fügt gleichzeitig Nitrat hinzu — ebenfalls nur für Experten.

**pH-Zielbereich — Kompromisszone:**
Der Default-Bereich 6.8–7.2 ist ein Kompromiss, der keine der drei Systemkomponenten optimal bedient:
- Fische bevorzugen pH 7.0–8.0
- Pflanzen-Nährstoffverfügbarkeit ist optimal bei pH 5.5–6.5
- Nitrifikationsbakterien arbeiten optimal bei pH 7.0–8.0

Die Defaults können systemtyp-abhängig angepasst werden:
- **Media-Bed** (bessere Pufferung durch Substrat): 6.4–7.0
- **DWC/NFT** (geringere Pufferung): 6.8–7.2 (Standard)
- **Kalkstein-Media-Bed** (natürliche pH-Anhebung): 7.0–7.5

**Alkalitäts-Management (KH):**
Nitrifikation verbraucht Alkalität (ca. 7.1 mg CaCO3 pro mg NH4-N oxidiert). Bei KH <4°dH (71 ppm CaCO3) besteht **pH-Crash-Gefahr** — der pH kann abrupt von 6.8 auf <5.0 fallen, was Biofilter-Bakterien tötet und eine Ammoniak-Kaskade auslöst. KH-Überwachung und Nachpufferung (via KOH/Ca(OH)2) sind Pflichtprogramm.

**Fisch-Pflanzen-Kompatibilität (Temperaturzonen):**

Die Wassertemperatur muss sowohl für Fische als auch für Pflanzen geeignet sein. Es gibt drei Temperaturzonen:

| Zone | Temperatur | Fischarten | Geeignete Pflanzen | Ungeeignete Pflanzen |
|------|-----------|------------|-------------------|---------------------|
| Warmwasser | 24–30°C | Tilapia, Wels | Tomaten, Paprika, Basilikum, Gurke, Okra, Aubergine, Chili | Salat (schosst >25°C), Erdbeeren, Kohl |
| Temperiert | 18–24°C | Zander, Karpfen/Koi, Goldfisch, Barsch | Salat, Kräuter, Tomaten (bedingt), Paprika (bedingt) | — (breiteste Auswahl) |
| Kaltwasser | 8–18°C | Forelle, Saibling | Salat, Pak Choi, Kohl, Kresse, Petersilie, Dill, Erdbeeren | Tomaten, Paprika, Gurke (Wurzelzone zu kalt) |

**Hinweis Wurzelzonen-Temperatur:** Bei Media-Bed-Systemen kann die Wassertemperatur 5–10°C unter der Lufttemperatur liegen (Verdunstungskühlung). DWC-Systeme haben weniger Differenz.

**Hinweis DO-Sättigung und Temperatur:** Die maximale Sauerstoff-Sättigung im Wasser sinkt mit steigender Temperatur: bei 15°C ~10.1 mg/L, bei 25°C ~8.2 mg/L, bei 30°C ~7.5 mg/L. In Warmwasser-Systemen (Tilapia, 28°C) ist der Puffer zwischen physikalischer Sättigung (~7.8 mg/L) und Stress-Schwelle (3.0 mg/L) nur 4.8 mg/L — intensive Belüftung ist Pflicht. In Kaltwasser-Systemen (Forelle, 14°C) liegt die Sättigung bei ~10.3 mg/L, aber das Forellen-Minimum (5.0 mg/L) ist absolut höher. EC-Gehalt der Nährstofflösung reduziert die DO-Sättigung zusätzlich (Salting-Out-Effekt, analog REQ-014).

**Saisonale Aspekte (Outdoor-Aquaponik DACH):**

Outdoor-Aquaponik im DACH-Raum ist nur saisonal (April–Oktober) oder im beheizten Gewächshaus ganzjährig praktikabel.

| Saison | Futtermenge | Wassertemperatur | Pflanzen | Biofilter |
|--------|-----------|-----------------|----------|-----------|
| Frühling | Langsam steigern (Ramp-up) | Steigend | Blattsalate, Kräuter | Reaktivierung (Cycling!) |
| Sommer | Maximum | >25°C (DO-Achtung!) | Fruchtgemüse, Tomaten. **Salat schosst** bei >25°C und >14h Tageslicht — hitzetolerante Sorten wählen oder verschatten. Photoperiode >16h im DACH-Hochsommer (Juni/Juli) beachten. | Volle Kapazität |
| Herbst | Reduzieren | Fallend | Kohl, Wintersalate | Kapazität sinkt |
| Winter | Minimal/Stopp | <10°C | Keine (oder winterharte) | Dormant |

**Saisonaler Futter-Ramp-up-Plan** (Frühling / nach Dormanz):

Der Ramp-up ist **temperaturabhängig** — bei niedrigen Wassertemperaturen dauert die Biofilter-Reaktivierung länger:
- **Basis-Plan (Wassertemperatur ≥20°C):** Woche 1–2: 25%, Woche 3–4: 50%, Woche 5–6: 75%, ab Woche 7: 100%
- **Bei 15–20°C:** Ramp-up-Dauer verdoppelt (≈14 Wochen)
- **Wasserqualitäts-Gate:** Ramp-up nur weiter steigern, wenn TAN <0.5 mg/L UND NO2 <0.5 mg/L. Bei Spikes: aktuelle Stufe beibehalten bis Werte stabil.

Ein Biofilter, der im Winter inaktiv war, muss im Frühling **erneut eingefahren werden**. Wird sofort voll gefüttert, kommt es zu Ammoniak- und Nitrit-Spikes.

**Regulatorische Hinweise (DACH):**

| Bereich | Regelung | Auswirkung |
|---------|---------|-----------|
| Tierschutz (DE) | TierSchG §2 — artgerechte Haltung | Besatzdichte-Grenzen, Sauerstoff-Mindestversorgung |
| Sachkunde (DE) | TierSchG §11 — Sachkundenachweis | Gewerbliche Fischhaltung genehmigungspflichtig, Hobby ausgenommen |
| Invasive Arten (EU) | EU-VO 1143/2014 | Die gesamte **Gattung *Clarias*** (inkl. *C. gariepinus* und *C. batrachus*) ist auf der Unionsliste invasiver gebietsfremder Arten gelistet (Durchführungsverordnung (EU) 2016/1141). In DE unter Auflagen in geschlossenen RAS möglich (TierSchG + FischSeuchV), in AT generell verboten, CH eigene Regelung (Freisetzungsverordnung). System warnt bei regulatorisch kritischen Arten. |
| Wasserrecht (DE) | WHG — Wasserhaushaltsgesetz | Geschlossene Kreislaufanlagen: keine Einleitungsgenehmigung nötig. Bei Gewässerentnahme/-einleitung: genehmigungspflichtig |
| Lebensmittelrecht (EU) | EU-VO 853/2004 | Bei gewerblichem Vertrieb von Fisch/Gemüse: Hygieneanforderungen, HACCP-Pflicht |

### 1.1 Szenarien

**Szenario 1: Tilapia-Salat DWC-System (Hobby, Warmwasser)**
```
SETUP: Warmwasser-Aquaponik-System mit:
  - Fischtank: 500L mit 15 Tilapia (Oreochromis niloticus)
  - Biofilter: MBBR mit K1-Medien (40L), cycled
  - Clarifier: Swirl Filter (30L)
  - DWC-Growbed: 4 m² mit Salat, Basilikum, Pak Choi
  - Sump: 100L Rücklauftank

FLOW: Fishtank → Swirl Filter → MBBR → DWC → Sump → Fishtank
TEMPERATUR: 26°C (optimal für Tilapia UND schnelles Salatswachstum)
FUTTERMENGE: 75g/Tag (3% der geschätzten Biomasse von 2.5kg)
TAN-PRODUKTION: ~2.2g/Tag (75g × 32% Protein × 0.092, omnivore Futter)

TÄGLICHE ROUTINE:
  1. Wassertest: pH, TAN, NO2, NO3, Temperatur (manuell oder Sensor)
  2. Fütterung: System empfiehlt 75g basierend auf Biomasse und Temperatur
  3. Sichtkontrolle: Fischverhalten, Pflanzenwuchs
  4. Wöchentlich: Fe-DTPA nachdosieren (2 ppm), KH prüfen
```

**Szenario 2: Forellen-Kräuter NFT-System (kommerziell, Kaltwasser)**
```
SETUP: Kaltwasser-Anlage im Gewächshaus:
  - Fischtank: 2000L mit 40 Regenbogenforellen (Oncorhynchus mykiss)
  - Biofilter: Trickle Filter (200L Lavastein)
  - Clarifier: Trommelfilter
  - Mineralisierungs-Tank: 100L (aerob, 24h Verweildauer)
  - NFT-Kanäle: 12 m² mit Petersilie, Dill, Kresse, Minze
  - Sump: 200L

TEMPERATUR: 14°C (Forellen-Optimum, ideal für Kräuter-Wurzelzone)
FUTTERMENGE: 120g/Tag (2% von 6kg Biomasse, reduziert wegen Kaltwasser)
BESONDERHEITEN:
  - Forellen sind NO2-empfindlich (<0.1 mg/L!) — engmaschiges Monitoring
  - DO muss >7 mg/L bleiben (Forellen-Minimum)
  - Supplementierung: Fe-EDDHA (stabiler bei pH-Schwankungen),
    Ca(OH)2 und KOH alternierend
  - Regulatory Note: Sachkundenachweis erforderlich (gewerblich)
```

**Szenario 3: Media-Bed Mischkultur (Goldfisch + Tomaten/Basilikum)**
```
SETUP: Einfachstes Aquaponik-System (Hobby-Einsteiger):
  - Fischtank: 300L mit 10 Goldfischen (Carassius auratus)
  - Growbed: 2 m² Blähton-Media-Bed (dient gleichzeitig als Biofilter)
  - Kein separater Biofilter, kein Clarifier nötig (Media-Bed übernimmt)
  - Optional: Wurmkompost im Media-Bed (Eisenia fetida)

TEMPERATUR: 20°C (Goldfisch-Optimum, Tomaten bedingt möglich)
FUTTERMENGE: 15g/Tag (1.5% von 1kg Biomasse)
VORTEILE:
  - Einfachste Konfiguration (Einsteiger-freundlich)
  - Media-Bed = Biofilter + Growbed + Mineralisierung
  - Goldfische sind extrem robust (DO >3 mg/L, TAN bis 2 mg/L)
  - Wurmkompost verbessert Mineralisierung und Fe/K-Verfügbarkeit direkt im Substrat
    (Systeme mit Vermicompost: Eisen- und Kalium-Defizite treten seltener auf)
VERMICOMPOST-HINWEIS:
  - Eisenia fetida: Temperaturoptimum 15–25°C, stirbt ab >35°C
  - Nicht geeignet für Warmwasser-Media-Bed über 30°C Wassertemperatur
  - Reduziert Supplementierungshäufigkeit signifikant (Fe, K)
```

**Szenario 4: Biofilter-Cycling (neue Anlage einfahren)**
```
TIMELINE: Neues System ohne Fischbestand

TAG 1: System befüllt, Biofilter mit Ammoniakquelle gestartet (fishless cycling)
  → cycling_status: new → cycling
  → Futtermenge: 0g (noch keine Fische)

TAG 7-14: Ammoniak-Peak (TAN steigt auf 4-8 mg/L)
  → System zeigt: "Nitrosomonas-Bakterien bauen sich auf"
  → Warnung: "Ammoniak kritisch hoch — KEINE Fische einsetzen!"

TAG 14-28: Nitrit-Peak (NO2 steigt auf 2-5 mg/L, TAN beginnt zu fallen)
  → System zeigt: "Nitrobacter-Bakterien bauen sich auf"
  → Cycling-Fortschritt: ~50%

TAG 28-42: Stabilisierung (TAN <0.25, NO2 <0.1, NO3 steigt)
  → System zeigt: "Cycling fast abgeschlossen"
  → Cycling-Fortschritt: ~80%

TAG 42+: TAN <0.25 UND NO2 <0.1 für 7 aufeinanderfolgende Tage
  → cycling_status: cycling → cycled
  → System empfiehlt: "Biofilter bereit — Fische einsetzen (25% Zielbesatz, Ramp-up)"
```

**Szenario 5: Ammoniak-Spike Emergency (Biofilter-Crash)**
```
AUSLÖSER: Überfütterung ODER Biofilter-Crash (z.B. Medikament im Wasser)

ERKENNUNG:
  - Wassertest: TAN 3.5 mg/L bei pH 7.2, Temp 26°C
  → pKa = 0.09018 + 2729.92/299.15 = 9.216
  → fraction = 1/(10^(9.216-7.2)+1) = 0.00955
  → Berechnung: free NH3 = 3.5 × 0.00955 = 0.033 mg/L
  → ÜBER dem sicheren Grenzwert (0.02 mg/L)!

SYSTEM-REAKTION:
  1. Alarm: "Freies Ammoniak 0.031 mg/L — KRITISCH für Fische!"
  2. Sofortmaßnahme 1: "Fütterung sofort stoppen (0g bis TAN <0.5)"
  3. Sofortmaßnahme 2: "Teilwasserwechsel empfohlen (max. 20% Systemvolumen)"
  4. Sofortmaßnahme 3: "Belüftung maximieren (DO senkt Ammoniak-Toxizität)"
  5. Ursachenanalyse: "Mögliche Ursachen:
     - Überfütterung (letzte 3 Tage: 120g/Tag statt empfohlen 75g)
     - Toter Fisch im Tank (Ammoniak-Quelle)
     - Biofilter-Crash (Medikament, Chlor, Temperaturschock)"
  6. Cycling-Status: Wenn NO2 ebenfalls steigt → cycling_status zurück auf 'cycling'
```

## 2. ArangoDB-Modellierung

### Nodes:

- **`:FishSpecies`** — Fischart-Stammdaten (globale Seed-Daten, nicht tenant-scoped)
  - Collection: `fish_species`
  - Properties:
    - `scientific_name: str` (z.B. "Oreochromis niloticus")
    - `common_name_de: str` (z.B. "Nil-Tilapia")
    - `common_name_en: str` (z.B. "Nile Tilapia")
    - `temperature_zone: Literal['coldwater', 'temperate', 'warmwater']`
    - `temperature_min_c: float` (Überlebensminimum)
    - `temperature_max_c: float` (Überlebensmaximum)
    - `temperature_optimal_min_c: float` (Optimalbereich Start)
    - `temperature_optimal_max_c: float` (Optimalbereich Ende)
    - `temperature_lethal_low_c: float` (Letal-Temperatur unten)
    - `temperature_lethal_high_c: float` (Letal-Temperatur oben)
    - `ph_min: float`
    - `ph_max: float`
    - `do_minimum_mgl: float` (Überlebens-Minimum Gelöstsauerstoff)
    - `do_optimal_mgl: float` (Optimal-DO)
    - `do_stress_mgl: float` (Stress-Schwelle DO)
    - `max_tan_mgl: float` (Artspezifischer TAN-Grenzwert)
    - `max_nitrite_mgl: float` (Artspezifischer NO2-Grenzwert)
    - `max_nitrate_mgl: float` (Artspezifischer NO3-Grenzwert)
    - `fcr_hobby: Optional[float]` (Feed Conversion Ratio — Hobby-Betrieb, null bei Zierfischen)
    - `fcr_professional: Optional[float]` (FCR — Professionell, null bei Zierfischen)
    - `feed_type: Literal['carnivore', 'omnivore', 'herbivore']`
    - `max_stocking_density_kg_per_1000l: float` (konservatives Hobby-Maximum)
    - `max_stocking_density_professional_kg_per_1000l: Optional[float]` (professionelles RAS-Maximum, null bei Zierfischen)
    - `growth_rate_g_per_day: Optional[float]` (bei Optimaltemperatur)
    - `market_weight_g: Optional[float]` (Ziel-Schlachtgewicht)
    - `time_to_market_days: Optional[int]` (Tage bis Schlachtgewicht)
    - `schooling: bool` (Schwarmfisch — braucht Artgenossen)
    - `min_group_size: int` (Mindestgruppengröße)
    - `regulatory_notes: list[RegulatoryNote]` (siehe unten)
    - `notes_de: Optional[str]` (Freitext-Hinweise, Deutsch)
    - `notes_en: Optional[str]` (Freitext-Hinweise, Englisch)

  ```python
  class RegulatoryNote(BaseModel):
      country: str  # ISO 3166-1 alpha-2: "DE", "AT", "CH"
      regulation: str  # z.B. "EU-VO 1143/2014", "TierSchG §11"
      requirement: str  # z.B. "Haltung genehmigungspflichtig"
      hobby_exempt: bool  # Hobby-Ausnahme vorhanden?
  ```

- **`:FishStock`** — Fischbestand in einem bestimmten Tank
  - Collection: `fish_stocks`
  - Properties:
    - `name: str` (z.B. "Tilapia Kohorte März 2026")
    - `species_key: str` (Referenz auf fish_species)
    - `count: int` (aktuelle Anzahl lebender Fische)
    - `initial_count: int` (Anfangsbesatz)
    - `avg_weight_g: float` (geschätztes Durchschnittsgewicht)
    - `total_biomass_kg: float` (count × avg_weight_g / 1000)
    - `stocking_date: date` (Besatzdatum)
    - `mortality_count: int` (kumulative Verluste)
    - `last_weighed_at: Optional[date]` (letzte Gewichtsschätzung)
    - `notes: Optional[str]`

- **`:AquaponicSystem`** — Gesamtsystem-Konfiguration, verbindet Fischtank, Biofilter, Growbed
  - Collection: `aquaponic_systems`
  - Properties:
    - `name: str` (z.B. "Tilapia-Salat DWC")
    - `system_type: Literal['media_bed', 'dwc', 'nft', 'hybrid', 'wicking_bed']`
    - `total_volume_liters: float` (Gesamtwasservolumen aller Tanks)
    - `grow_area_m2: float` (Gesamtanbaufläche)
    - `cycling_status: Literal['new', 'cycling', 'cycled', 'dormant']`
    - `cycling_start_date: Optional[date]`
    - `cycled_since: Optional[date]` (wann stabil)
    - `biofilter_type: Optional[Literal['media_bed_integrated', 'mbbr', 'trickle', 'fluidized_bed']]`
    - `biofilter_volume_liters: Optional[float]`
    - `biofilter_media_ssa_m2_per_m3: Optional[float]` (Specific Surface Area: Blähton ~300, K1 ~650)
    - `has_clarifier: bool` (Feststoff-Separation vorhanden)
    - `clarifier_type: Optional[Literal['swirl', 'settling', 'drum', 'screen']]`
    - `has_mineralization: bool` (Mineralisierungs-Tank vorhanden)
    - `has_vermicompost: bool` (Wurmkompost im Growbed)
    - `daily_feed_target_g: float` (Soll-Futtermenge pro Tag)
    - `turnover_rate_per_hour: Optional[float]` (Soll: 1–2x/h)
    - `outdoor: bool` (Outdoor-System — saisonale Logik aktiv)
    - `backup_power: bool` (Notstromversorgung vorhanden)
    - `ph_target_min: float` (Default: 6.8)
    - `ph_target_max: float` (Default: 7.2)
    - `notes: Optional[str]`

- **`:WaterTest`** — Wassertest-Ergebnis (immutable, Insert-only)
  - Collection: `water_tests`
  - Properties:
    - `tested_at: datetime`
    - `ph: float`
    - `ammonia_tan_mgl: float` (Total Ammonia Nitrogen)
    - `nitrite_mgl: float`
    - `nitrate_mgl: float`
    - `temperature_c: float`
    - `dissolved_oxygen_mgl: Optional[float]`
    - `kh_dh: Optional[float]` (Karbonathärte in °dH)
    - `gh_dh: Optional[float]` (Gesamthärte in °dH)
    - `iron_ppm: Optional[float]`
    - `potassium_ppm: Optional[float]`
    - `calcium_ppm: Optional[float]`
    - `magnesium_ppm: Optional[float]`
    - `phosphate_ppm: Optional[float]`
    - `free_ammonia_mgl: float` (**berechnet** via Emerson-Formel aus TAN + pH + Temp)
    - `source: Literal['manual', 'sensor', 'test_kit']`
    - `notes: Optional[str]`

- **`:FishFeedingEvent`** — Fütterungsereignis (immutable)
  - Collection: `fish_feeding_events`
  - Properties:
    - `fed_at: datetime`
    - `feed_brand: Optional[str]` (z.B. "Coppens Tilapia Grower")
    - `feed_type: Literal['pellet', 'flake', 'live', 'frozen', 'paste']`
    - `protein_percent: Optional[float]` (Proteingehalt des Futters)
    - `amount_g: float` (Futtermenge in Gramm)
    - `water_temp_c: float` (Wassertemperatur bei Fütterung — für FCR-Korrektur)
    - `fish_response: Literal['eager', 'normal', 'reduced', 'refused']`
    - `notes: Optional[str]`

- **`:SupplementationEvent`** — Nährstoff-Ergänzung in Aquaponik-System (immutable)
  - Collection: `supplementation_events`
  - Properties:
    - `applied_at: datetime`
    - `supplement_type: Literal['fe_dtpa', 'fe_eddha', 'koh', 'k2co3', 'ca_oh_2', 'mgso4', 'mnso4', 'h3bo3', 'znso4']`
    - `amount_ml: Optional[float]` (Flüssigkeit)
    - `amount_g: Optional[float]` (Feststoff)
    - `target_parameter: str` (z.B. "iron", "potassium", "calcium", "ph")
    - `measured_before: Optional[float]` (Messwert vor Supplementierung)
    - `measured_after: Optional[float]` (Messwert nach Supplementierung)
    - `notes: Optional[str]`

### Edge-Collections:
```
has_fish_stock:        aquaponic_systems  -> fish_stocks               // System enthält Fischbestand
stock_of_species:      fish_stocks        -> fish_species              // Bestand gehört zu Art
system_has_tank:       aquaponic_systems  -> tanks (REQ-014)           // System nutzt Tank (fish_tank, biofilter, sump, etc.)
                                                                       // Edge-Property: tank_role: Literal['fish_tank', 'biofilter', 'sump', 'clarifier', 'mineralization', 'growbed_reservoir']
system_has_growbed:    aquaponic_systems  -> slots (REQ-002)           // System versorgt Growbed-Slots
water_test_for:        water_tests        -> aquaponic_systems         // Wassertest gehört zu System
feeding_for_stock:     fish_feeding_events -> fish_stocks              // Fütterung für Bestand
supplementation_for:   supplementation_events -> aquaponic_systems     // Supplementierung für System
compatible_fish_plant: fish_species       -> species (REQ-001)         // Fisch-Pflanzen-Kompatibilität
                                                                       // Edge-Properties: temperature_match: float (0.0-1.0), nutrient_match: float (0.0-1.0), notes: str
incompatible_fish_plant: fish_species     -> species (REQ-001)         // Fisch-Pflanzen-Inkompatibilität
                                                                       // Edge-Property: reason: str (z.B. "Temperaturzone inkompatibel")
```

### Empfohlene Erweiterungen bestehender Modelle:

**REQ-014 (Tankmanagement):** Neue `tank_role`-Zuordnung via `system_has_tank`-Edge statt neuer TankType-Enum-Werte. Bestehende TankTypes (`nutrient`, `recirculation`, `reservoir`) werden wiederverwendet. Die Rolle des Tanks im Aquaponik-System (Fischtank, Biofilter, Sump, Clarifier, Mineralisierung) wird über die Edge-Property `tank_role` auf `system_has_tank` bestimmt.

**REQ-014 TankState:** Neue optionale Felder:
- `ammonia_tan_mgl: Optional[float]`
- `nitrite_mgl: Optional[float]`
- `nitrate_mgl: Optional[float]`
- `kh_dh: Optional[float]`
- `gh_dh: Optional[float]`

**Klarstellung WaterTest vs. TankState:** Ein `WaterTest` (REQ-026) ist das primäre, immutable Event mit erweitertem Parameterumfang (TAN, NO2, NO3, KH, GH, Fe, K, Ca, Mg, PO4 + berechnetes free_ammonia). Bei Erfassung eines WaterTests in einem Aquaponik-System wird der zugehörige `TankState` (REQ-014) automatisch mit den überlappenden Parametern (pH, Temperatur, DO, EC sowie die neuen Felder ammonia_tan_mgl, nitrite_mgl, nitrate_mgl, kh_dh, gh_dh) aktualisiert. WaterTest ist die Quelle, TankState die abgeleitete Zustandssicht.

**REQ-005 (Sensorik):** Neue Sensorparameter:
- `ammonia` (TAN in mg/L, Range 0–20)
- `nitrite` (NO2 in mg/L, Range 0–20)
- `nitrate` (NO3 in mg/L, Range 0–500)
- `kh` (Karbonathärte in °dH, Range 0–30)

**REQ-004 (Dünge-Logik):** Neues Feld auf Fertilizer:
- `aquaponic_safe: bool` (Default: false) — bestimmt, ob ein Dünger in Aquaponik-Systemen verwendet werden darf. Chelat-Eisen (Fe-DTPA, Fe-EDDHA) ist technisch synthetisch aber fischsicher → `aquaponic_safe=true`.

### AQL-Beispielqueries:

**1. Stickstoffkreislauf-Verlauf (Ammonia/Nitrit/Nitrat über Zeit):**
```aql
FOR test IN water_tests
  FILTER test._key IN (
    FOR v, e IN 1..1 OUTBOUND @system_key water_test_for
    RETURN v._key
  )
  FILTER test.tested_at >= @start AND test.tested_at <= @end
  SORT test.tested_at ASC
  RETURN {
    tested_at: test.tested_at,
    ammonia_tan: test.ammonia_tan_mgl,
    free_ammonia: test.free_ammonia_mgl,
    nitrite: test.nitrite_mgl,
    nitrate: test.nitrate_mgl,
    ph: test.ph,
    temperature: test.temperature_c
  }
```

**2. Fisch-Pflanzen-Kompatibilität via Graph-Traversal:**
```aql
FOR species IN fish_species
  FILTER species._key == @fish_species_key
  LET compatible = (
    FOR v, e IN 1..1 OUTBOUND species compatible_fish_plant
    RETURN {
      species_key: v._key,
      common_name: v.common_name,
      temperature_match: e.temperature_match,
      nutrient_match: e.nutrient_match,
      notes: e.notes
    }
  )
  LET incompatible = (
    FOR v, e IN 1..1 OUTBOUND species incompatible_fish_plant
    RETURN {
      species_key: v._key,
      common_name: v.common_name,
      reason: e.reason
    }
  )
  RETURN {
    fish: species.common_name_de,
    temperature_zone: species.temperature_zone,
    compatible: compatible,
    incompatible: incompatible
  }
```

**3. Systeme mit kritischen Wasserwerten (Alarm-Dashboard):**
```aql
FOR sys IN aquaponic_systems
  LET latest_test = FIRST(
    FOR v, e IN 1..1 INBOUND sys._id water_test_for
    SORT v.tested_at DESC
    LIMIT 1
    RETURN v
  )
  LET fish_stock = FIRST(
    FOR v, e IN 1..1 OUTBOUND sys._id has_fish_stock
    LET sp = FIRST(
      FOR s, e2 IN 1..1 OUTBOUND v._id stock_of_species
      RETURN s
    )
    RETURN { stock: v, species: sp }
  )
  FILTER latest_test != null AND fish_stock != null
  FILTER latest_test.free_ammonia_mgl > 0.02
     OR latest_test.nitrite_mgl > fish_stock.species.max_nitrite_mgl
     OR (latest_test.kh_dh != null AND latest_test.kh_dh < 4)
     OR (latest_test.dissolved_oxygen_mgl != null
         AND latest_test.dissolved_oxygen_mgl < fish_stock.species.do_stress_mgl)
  RETURN {
    system: sys.name,
    cycling_status: sys.cycling_status,
    alerts: {
      free_ammonia: latest_test.free_ammonia_mgl,
      nitrite: latest_test.nitrite_mgl,
      kh: latest_test.kh_dh,
      do: latest_test.dissolved_oxygen_mgl,
      species_limits: {
        max_nitrite: fish_stock.species.max_nitrite_mgl,
        do_stress: fish_stock.species.do_stress_mgl
      }
    }
  }
```

**4. Futtermenge vs. Nährstoffproduktion (Zeitraum-Analyse):**
```aql
FOR sys IN aquaponic_systems
  FILTER sys._key == @system_key
  LET feedings = (
    FOR stock IN 1..1 OUTBOUND sys has_fish_stock
      FOR evt IN 1..1 INBOUND stock feeding_for_stock
      FILTER evt.fed_at >= @start AND evt.fed_at <= @end
      COLLECT date = DATE_FORMAT(evt.fed_at, "%yyyy-%mm-%dd") INTO daily
      RETURN {
        date: date,
        total_feed_g: SUM(daily[*].evt.amount_g),
        estimated_tan_g: SUM(daily[*].evt.amount_g) * 0.032 * 0.092  // Default 32% Protein × 0.092
      }
  )
  RETURN { system: sys.name, daily_feedings: feedings }
```

**5. Biofilter-Cycling-Status aller Systeme:**
```aql
FOR sys IN aquaponic_systems
  FILTER sys.cycling_status IN ['new', 'cycling']
  LET tests = (
    FOR v IN 1..1 INBOUND sys._id water_test_for
    SORT v.tested_at DESC
    LIMIT 14
    RETURN { date: v.tested_at, tan: v.ammonia_tan_mgl, no2: v.nitrite_mgl, no3: v.nitrate_mgl }
  )
  LET stable_days = LENGTH(
    FOR t IN tests
    FILTER t.tan < 0.25 AND t.no2 < 0.1
    RETURN 1
  )
  RETURN {
    system: sys.name,
    status: sys.cycling_status,
    started: sys.cycling_start_date,
    stable_days: stable_days,
    progress_percent: MIN([stable_days / 7 * 100, 100]),
    latest_values: FIRST(tests)
  }
```

### Seed-Daten:

```json
// fish_species collection — 8 Arten
[
  {
    "_key": "tilapia_nile",
    "scientific_name": "Oreochromis niloticus",
    "common_name_de": "Nil-Tilapia",
    "common_name_en": "Nile Tilapia",
    "temperature_zone": "warmwater",
    "temperature_min_c": 18, "temperature_max_c": 34,
    "temperature_optimal_min_c": 26, "temperature_optimal_max_c": 30,
    "temperature_lethal_low_c": 12, "temperature_lethal_high_c": 38,
    "ph_min": 6.5, "ph_max": 8.5,
    "do_minimum_mgl": 2.0, "do_optimal_mgl": 5.0, "do_stress_mgl": 3.0,
    "max_tan_mgl": 2.0, "max_nitrite_mgl": 1.0, "max_nitrate_mgl": 200,
    "fcr_hobby": 1.8, "fcr_professional": 1.3,
    "feed_type": "omnivore",
    "max_stocking_density_kg_per_1000l": 25,
    "max_stocking_density_professional_kg_per_1000l": 80,
    "growth_rate_g_per_day": 3.0,
    "market_weight_g": 500, "time_to_market_days": 180,
    "schooling": true, "min_group_size": 5,
    "regulatory_notes": [
      {"country": "DE", "regulation": "Keine Einschränkung", "requirement": "Hobby: frei, gewerblich: Sachkundenachweis §11 TierSchG", "hobby_exempt": true}
    ],
    "notes_de": "Robusteste Aquaponik-Fischart. Hohe Toleranz gegenüber Wasserqualitätsschwankungen. Sehr effiziente Futterverwertung."
  },
  {
    "_key": "trout_rainbow",
    "scientific_name": "Oncorhynchus mykiss",
    "common_name_de": "Regenbogenforelle",
    "common_name_en": "Rainbow Trout",
    "temperature_zone": "coldwater",
    "temperature_min_c": 8, "temperature_max_c": 18,
    "temperature_optimal_min_c": 12, "temperature_optimal_max_c": 16,
    "temperature_lethal_low_c": -0.5, "temperature_lethal_high_c": 22,
    "ph_min": 6.5, "ph_max": 8.0,
    "do_minimum_mgl": 5.0, "do_optimal_mgl": 8.0, "do_stress_mgl": 6.0,
    "max_tan_mgl": 0.5, "max_nitrite_mgl": 0.1, "max_nitrate_mgl": 80,
    "fcr_hobby": 1.3, "fcr_professional": 1.0,
    "feed_type": "carnivore",
    "max_stocking_density_kg_per_1000l": 30,
    "max_stocking_density_professional_kg_per_1000l": 60,
    "growth_rate_g_per_day": 2.5,
    "market_weight_g": 350, "time_to_market_days": 150,
    "schooling": true, "min_group_size": 5,
    "regulatory_notes": [
      {"country": "DE", "regulation": "TierSchG §11", "requirement": "Gewerbliche Haltung: Sachkundenachweis erforderlich", "hobby_exempt": true}
    ],
    "notes_de": "Empfindlich gegen hohe Temperaturen und Nitrit. Benötigt hohe DO-Werte (>7 mg/L optimal). Ideal für Kaltwasser-Kräuter-Systeme. Kalt-eurytherm: überlebt bei fließendem Wasser auch knapp unter 0°C (Lethaltemperatur bezieht sich auf Eiskristallbildung)."
  },
  {
    "_key": "carp_common",
    "scientific_name": "Cyprinus carpio",
    "common_name_de": "Karpfen / Koi",
    "common_name_en": "Common Carp / Koi",
    "temperature_zone": "temperate",
    "temperature_min_c": 4, "temperature_max_c": 35,
    "temperature_optimal_min_c": 20, "temperature_optimal_max_c": 28,
    "temperature_lethal_low_c": 2, "temperature_lethal_high_c": 38,
    "ph_min": 6.5, "ph_max": 9.0,
    "do_minimum_mgl": 2.0, "do_optimal_mgl": 5.0, "do_stress_mgl": 4.0,
    "max_tan_mgl": 1.0, "max_nitrite_mgl": 0.5, "max_nitrate_mgl": 300,
    "fcr_hobby": 2.2, "fcr_professional": 1.5,
    "feed_type": "omnivore",
    "max_stocking_density_kg_per_1000l": 15,
    "max_stocking_density_professional_kg_per_1000l": 40,
    "growth_rate_g_per_day": 2.0,
    "market_weight_g": 1500, "time_to_market_days": 365,
    "schooling": false, "min_group_size": 1,
    "regulatory_notes": [],
    "notes_de": "Eurythermer Fisch mit breitestem Temperaturbereich. Sehr robust. Koi gehören taxonomisch zu Cyprinus rubrofuscus (Lacépède 1803), nicht zu C. carpio — beide Arten haben identische Haltungsparameter. Koi sind reine Zierfische (kein Verzehr)."
  },
  {
    "_key": "catfish_european",
    "scientific_name": "Silurus glanis",
    "common_name_de": "Europäischer Wels",
    "common_name_en": "European Catfish / Wels",
    "temperature_zone": "temperate",
    "temperature_min_c": 10, "temperature_max_c": 28,
    "temperature_optimal_min_c": 20, "temperature_optimal_max_c": 26,
    "temperature_lethal_low_c": 4, "temperature_lethal_high_c": 32,
    "ph_min": 6.5, "ph_max": 8.5,
    "do_minimum_mgl": 2.0, "do_optimal_mgl": 5.0, "do_stress_mgl": 3.0,
    "max_tan_mgl": 2.0, "max_nitrite_mgl": 0.5, "max_nitrate_mgl": 200,
    "fcr_hobby": 1.6, "fcr_professional": 1.2,
    "feed_type": "carnivore",
    "max_stocking_density_kg_per_1000l": 20,
    "max_stocking_density_professional_kg_per_1000l": 60,
    "growth_rate_g_per_day": 4.0,
    "market_weight_g": 2000, "time_to_market_days": 300,
    "schooling": false, "min_group_size": 1,
    "regulatory_notes": [
      {"country": "DE", "regulation": "Heimische Art", "requirement": "Keine Einschränkung. Hinweis: Gattung Clarias (inkl. C. gariepinus, C. batrachus) ist auf der Unionsliste invasiver Arten (EU-VO 1143/2014, DVO 2016/1141) — Silurus glanis als heimische Alternative.", "hobby_exempt": true}
    ],
    "notes_de": "Heimische Alternative zur Gattung Clarias (EU-VO 1143/2014 verbietet gesamte Gattung, inkl. C. gariepinus und C. batrachus). Effiziente Futterverwertung, robust."
  },
  {
    "_key": "perch_european",
    "scientific_name": "Perca fluviatilis",
    "common_name_de": "Europäischer Flussbarsch",
    "common_name_en": "European Perch",
    "temperature_zone": "temperate",
    "temperature_min_c": 8, "temperature_max_c": 28,
    "temperature_optimal_min_c": 18, "temperature_optimal_max_c": 24,
    "temperature_lethal_low_c": 4, "temperature_lethal_high_c": 30,
    "ph_min": 6.5, "ph_max": 8.5,
    "do_minimum_mgl": 3.0, "do_optimal_mgl": 6.0, "do_stress_mgl": 4.0,
    "max_tan_mgl": 0.5, "max_nitrite_mgl": 0.3, "max_nitrate_mgl": 150,
    "fcr_hobby": 1.6, "fcr_professional": 1.2,
    "feed_type": "carnivore",
    "max_stocking_density_kg_per_1000l": 15,
    "max_stocking_density_professional_kg_per_1000l": 40,
    "growth_rate_g_per_day": 1.5,
    "market_weight_g": 250, "time_to_market_days": 240,
    "schooling": true, "min_group_size": 5,
    "regulatory_notes": [],
    "notes_de": "Heimische Art, guter Kompromiss-Temperaturbereich. Hochwertiges Futter nötig (carnivore). Empfindlicher als Karpfen."
  },
  {
    "_key": "goldfish",
    "scientific_name": "Carassius auratus",
    "common_name_de": "Goldfisch",
    "common_name_en": "Goldfish",
    "temperature_zone": "temperate",
    "temperature_min_c": 2, "temperature_max_c": 30,
    "temperature_optimal_min_c": 18, "temperature_optimal_max_c": 22,
    "temperature_lethal_low_c": 0, "temperature_lethal_high_c": 34,
    "ph_min": 6.0, "ph_max": 8.5,
    "do_minimum_mgl": 2.0, "do_optimal_mgl": 5.0, "do_stress_mgl": 3.0,
    "max_tan_mgl": 2.0, "max_nitrite_mgl": 0.5, "max_nitrate_mgl": 200,
    "fcr_hobby": null, "fcr_professional": null,
    "feed_type": "omnivore",
    "max_stocking_density_kg_per_1000l": 10,
    "max_stocking_density_professional_kg_per_1000l": null,
    "growth_rate_g_per_day": 0.3,
    "market_weight_g": null, "time_to_market_days": null,
    "schooling": true, "min_group_size": 3,
    "regulatory_notes": [],
    "notes_de": "Idealer Einstiegsfisch für Hobby-Aquaponik. Extrem robust, breiter Temperaturbereich. Kein Verzehrfisch — reiner Zierfisch. FCR nicht anwendbar (Zierfisch, kein Wachstumsziel). Futtermenge orientiert sich an Wasserqualität und Pflanzenbedarf, nicht an Gewichtszunahme. In gut belüfteten Systemen bis 15 kg/1000L möglich, für Einsteiger 5–10 kg/1000L empfohlen."
  },
  {
    "_key": "zander",
    "scientific_name": "Sander lucioperca",
    "common_name_de": "Zander",
    "common_name_en": "Pike-perch / Zander",
    "temperature_zone": "temperate",
    "temperature_min_c": 8, "temperature_max_c": 28,
    "temperature_optimal_min_c": 18, "temperature_optimal_max_c": 22,
    "temperature_lethal_low_c": 2, "temperature_lethal_high_c": 30,
    "ph_min": 6.5, "ph_max": 8.5,
    "do_minimum_mgl": 4.0, "do_optimal_mgl": 7.0, "do_stress_mgl": 5.0,
    "max_tan_mgl": 0.5, "max_nitrite_mgl": 0.3, "max_nitrate_mgl": 100,
    "fcr_hobby": 1.5, "fcr_professional": 1.1,
    "feed_type": "carnivore",
    "max_stocking_density_kg_per_1000l": 20,
    "max_stocking_density_professional_kg_per_1000l": 50,
    "growth_rate_g_per_day": 2.0,
    "market_weight_g": 800, "time_to_market_days": 365,
    "schooling": false, "min_group_size": 1,
    "regulatory_notes": [
      {"country": "DE", "regulation": "TierSchG §11", "requirement": "Gewerbliche Haltung: Sachkundenachweis", "hobby_exempt": true}
    ],
    "notes_de": "Hoher Marktwert im DACH-Raum. Wird in kommerziellen Aquaponik-Anlagen eingesetzt (z.B. ECF Farm Berlin). Guter Kompromiss-Temperaturbereich für Salat/Kräuter."
  },
  {
    "_key": "char_arctic",
    "scientific_name": "Salvelinus alpinus",
    "common_name_de": "Seesaibling",
    "common_name_en": "Arctic Char",
    "temperature_zone": "coldwater",
    "temperature_min_c": 2, "temperature_max_c": 18,
    "temperature_optimal_min_c": 8, "temperature_optimal_max_c": 14,
    "temperature_lethal_low_c": 0, "temperature_lethal_high_c": 22,
    "ph_min": 6.5, "ph_max": 8.0,
    "do_minimum_mgl": 5.0, "do_optimal_mgl": 8.0, "do_stress_mgl": 6.0,
    "max_tan_mgl": 0.5, "max_nitrite_mgl": 0.1, "max_nitrate_mgl": 80,
    "fcr_hobby": 1.3, "fcr_professional": 1.0,
    "feed_type": "carnivore",
    "max_stocking_density_kg_per_1000l": 25,
    "max_stocking_density_professional_kg_per_1000l": 50,
    "growth_rate_g_per_day": 1.5,
    "market_weight_g": 300, "time_to_market_days": 240,
    "schooling": true, "min_group_size": 5,
    "regulatory_notes": [],
    "notes_de": "Heimische Kaltwasser-Art der Alpenregion. Ähnlich wie Forelle, aber etwas toleranter gegen Wasserqualitätsschwankungen. Hoher Marktwert in der Alpenregion."
  }
]
```

### ArangoDB-Graph-Definition:

```json
{
  "graph": "kamerplanter_graph",
  "edgeDefinitions_extend": [
    { "collection": "has_fish_stock", "from": ["aquaponic_systems"], "to": ["fish_stocks"] },
    { "collection": "stock_of_species", "from": ["fish_stocks"], "to": ["fish_species"] },
    { "collection": "system_has_tank", "from": ["aquaponic_systems"], "to": ["tanks"] },
    { "collection": "system_has_growbed", "from": ["aquaponic_systems"], "to": ["slots"] },
    { "collection": "water_test_for", "from": ["water_tests"], "to": ["aquaponic_systems"] },
    { "collection": "feeding_for_stock", "from": ["fish_feeding_events"], "to": ["fish_stocks"] },
    { "collection": "supplementation_for", "from": ["supplementation_events"], "to": ["aquaponic_systems"] },
    { "collection": "compatible_fish_plant", "from": ["fish_species"], "to": ["species"] },
    { "collection": "incompatible_fish_plant", "from": ["fish_species"], "to": ["species"] }
  ]
}
```

### Seed-Daten für compatible_fish_plant / incompatible_fish_plant Edges:

Die initialen Kompatibilitäts-Edges werden **automatisch generiert** basierend auf Temperaturzonen-Überlappung:

```
Algorithmus (Seed-Generierung):
FÜR JEDE FishSpecies f:
  FÜR JEDE Species p (mit root_zone_temp Anforderung aus REQ-001):
    fish_range = (f.temperature_optimal_min_c, f.temperature_optimal_max_c)
    plant_range = (p.root_zone_temp_min, p.root_zone_temp_max)
    overlap = min(fish_range[1], plant_range[1]) - max(fish_range[0], plant_range[0])
    total = max(fish_range[1], plant_range[1]) - min(fish_range[0], plant_range[0])
    temperature_match = max(0, overlap / total)

    WENN temperature_match > 0.3:
      → compatible_fish_plant Edge (temperature_match, nutrient_match=0.5 default)
    SONST:
      → incompatible_fish_plant Edge (reason = "Temperaturzone inkompatibel: {f.zone} vs. {p.zone}")
```

Hinweis: Pflanzenarten ohne `root_zone_temp`-Daten werden mit der Lufttemperatur-Präferenz approximiert. Die `nutrient_match`-Scores werden manuell für häufige Kombinationen gepflegt (z.B. Tilapia+Salat=0.9, Forelle+Tomate=0.3).

## 3. Technische Umsetzung (Python)

### Enumerationen:

```python
from enum import StrEnum

class AquaponicSystemType(StrEnum):
    MEDIA_BED = "media_bed"         # Blähton-Growbed (= Biofilter)
    DWC = "dwc"                     # Deep Water Culture
    NFT = "nft"                     # Nutrient Film Technique
    HYBRID = "hybrid"               # Kombination
    WICKING_BED = "wicking_bed"     # Dochtbewässerung

class CyclingStatus(StrEnum):
    NEW = "new"                     # Frisch, keine Bakterien
    CYCLING = "cycling"             # Einfahrphase, Spikes
    CYCLED = "cycled"               # Stabil
    DORMANT = "dormant"             # Winterruhe

class TemperatureZone(StrEnum):
    COLDWATER = "coldwater"         # 8-18°C
    TEMPERATE = "temperate"         # 18-24°C
    WARMWATER = "warmwater"         # 24-30°C

class BiofilterType(StrEnum):
    MEDIA_BED_INTEGRATED = "media_bed_integrated"  # Blähton = Biofilter
    MBBR = "mbbr"                   # Moving Bed Biofilm Reactor (K1)
    TRICKLE = "trickle"             # Rieselfilter (Lava, Bioballs)
    FLUIDIZED_BED = "fluidized_bed" # Wirbelbett (Sand)

class ClarifierType(StrEnum):
    SWIRL = "swirl"                 # Radialstrom-Separator
    SETTLING = "settling"           # Sedimentationsbecken
    DRUM = "drum"                   # Trommelfilter
    SCREEN = "screen"               # Netzfilter

class FeedType(StrEnum):
    PELLET = "pellet"
    FLAKE = "flake"
    LIVE = "live"
    FROZEN = "frozen"
    PASTE = "paste"

class FishFeedingResponse(StrEnum):
    EAGER = "eager"                 # Gierig, sofort gefressen
    NORMAL = "normal"               # Normal
    REDUCED = "reduced"             # Reduzierte Aufnahme
    REFUSED = "refused"             # Verweigert — Warnsignal!

class SupplementType(StrEnum):
    FE_DTPA = "fe_dtpa"             # Eisen-Chelat (stabil bis pH 7.5)
    FE_EDDHA = "fe_eddha"           # Eisen-Chelat (stabil bis pH 9.0)
    KOH = "koh"                     # Kaliumhydroxid (K + pH-up)
    K2CO3 = "k2co3"                 # Kaliumcarbonat (K + pH-up)
    CA_OH_2 = "ca_oh_2"             # Calciumhydroxid (Ca + pH-up)
    MGSO4 = "mgso4"                 # Bittersalz (Mg, pH-neutral)
    MNSO4 = "mnso4"                 # Mangansulfat (nur bei Mangel)
    H3BO3 = "h3bo3"                 # Borsäure (enger Toxizitätsbereich!)
    ZNSO4 = "znso4"                 # Zinksulfat (nur bei Mangel, enger Toxizitätsbereich!)

class TankRole(StrEnum):
    FISH_TANK = "fish_tank"
    BIOFILTER = "biofilter"
    SUMP = "sump"
    CLARIFIER = "clarifier"
    MINERALIZATION = "mineralization"
    GROWBED_RESERVOIR = "growbed_reservoir"
```

### Logik-Anforderungen:

**1. NitrogenCycleEngine:**

```python
import math
from pydantic import BaseModel, Field
from typing import Optional

class WaterQualityEvaluation(BaseModel):
    """Ergebnis einer Wasserwert-Bewertung."""
    parameter: str
    value: float
    limit: float
    severity: Literal['ok', 'warning', 'critical']
    message_de: str
    message_en: str

class CyclingProgress(BaseModel):
    """Fortschritt des Biofilter-Cycling."""
    status: CyclingStatus
    progress_percent: float  # 0-100
    stable_days: int
    days_required: int  # 7
    estimated_completion: Optional[date]
    phase_description_de: str

class NitrogenCycleEngine:
    """Überwacht den Stickstoffkreislauf und berechnet freies Ammoniak."""

    @staticmethod
    def calculate_free_ammonia(tan_mgl: float, ph: float, temp_c: float) -> float:
        """
        Berechnet freies (unionisiertes) Ammoniak aus TAN, pH und Temperatur.
        Formel: Emerson et al. (1975)
        """
        t_kelvin = temp_c + 273.15
        pka = 0.09018 + 2729.92 / t_kelvin
        fraction_nh3 = 1.0 / (10 ** (pka - ph) + 1)
        return round(tan_mgl * fraction_nh3, 4)

    @staticmethod
    def calculate_do_saturation(temp_c: float) -> float:
        """
        Berechnet maximale DO-Sättigung bei gegebener Temperatur (Benson & Krause 1984).
        DO_sat = 14.6 - 0.3943*T + 0.007714*T² - 0.0000646*T³
        Beispiele: 15°C → ~10.1 mg/L, 25°C → ~8.2 mg/L, 30°C → ~7.5 mg/L
        """
        t = temp_c
        return 14.6 - 0.3943 * t + 0.007714 * t**2 - 0.0000646 * t**3

    def evaluate_water_quality(
        self,
        water_test: WaterTest,
        fish_species: FishSpecies,
    ) -> list[WaterQualityEvaluation]:
        """
        Artspezifische Grenzwertprüfung aller Wasserparameter.
        Prüft: TAN/free NH3, NO2, NO3, pH, DO, Temperatur, KH, GH.

        Temperatur-Schwellenstufen (artspezifisch):
        - temperature_c < lethal_low oder > lethal_high: **critical** (unmittelbare Lebensgefahr)
        - temperature_c < temperature_min oder > temperature_max: **warning** (Stressbereich)
        - temperature_c außerhalb optimal_min/optimal_max: **info** (suboptimal)

        GH-Bewertung:
        - GH <4°dH: warning (Ca/Mg-Mangel bei Osmose-/Regenwasser)
        - GH >20°dH: warning (Stress bei empfindlichen Arten)

        DO-Bewertung:
        - Absoluter Wert vs. artspezifische Schwellen
        - Zusätzlich: Warnung wenn DO < 70% der temperaturabhängigen Sättigung

        Gibt Liste von Bewertungen zurück (ok, info, warning, critical).
        """
        ...

    def detect_cycling_phase(
        self,
        water_tests: list[WaterTest],
    ) -> CyclingProgress:
        """
        Erkennt die aktuelle Cycling-Phase aus der Wassertest-Historie.
        Sucht nach: Ammonia-Peak → Nitrit-Peak → Stabilisierung.
        """
        ...

    def check_alkalinity_crash_risk(
        self,
        kh_dh: float,
        daily_feed_g: float,
    ) -> Optional[WaterQualityEvaluation]:
        """
        Prüft ob die Alkalität für die aktuelle Futtermenge ausreicht.
        Nitrifikation verbraucht ~7.1 mg CaCO3 pro mg NH4-N oxidiert.
        Warnung bei KH <4°dH.
        """
        ...
```

**2. StockingDensityCalculator:**

```python
class StockingValidation(BaseModel):
    """Ergebnis der Besatzdichte-Prüfung."""
    current_density_kg_per_1000l: float
    max_density_kg_per_1000l: float
    utilization_percent: float
    status: Literal['ok', 'warning', 'overstocked']
    fish_plant_ratio_g_feed_per_m2: float
    message_de: str

class StockingDensityCalculator:
    """Berechnet Besatzdichte und Fisch-Pflanzen-Verhältnis."""

    # Empfohlene Feed-Rate pro m² Growbed nach Systemtyp
    FEED_PER_M2 = {
        'media_bed': 80,   # g/Tag — Media-Bed hat geringere Kapazität
        'dwc': 100,        # g/Tag
        'nft': 60,         # g/Tag — NFT hat dünneren Wasserfilm
        'hybrid': 90,
        'wicking_bed': 50,
    }

    def calculate_max_fish(
        self,
        tank_volume_l: float,
        species: FishSpecies,
    ) -> int:
        """Maximale Fischanzahl bei Durchschnittsgewicht."""
        ...

    def calculate_fish_plant_ratio(
        self,
        daily_feed_g: float,
        grow_area_m2: float,
        system_type: AquaponicSystemType,
    ) -> float:
        """Feed/m² Ratio — Ziel: FEED_PER_M2[system_type]."""
        ...

    def validate_stocking(
        self,
        fish_stock: FishStock,
        tank_volume_l: float,
        species: FishSpecies,
        system: AquaponicSystem,
    ) -> StockingValidation:
        """Vollständige Besatzdichte-Prüfung inkl. Fisch-Pflanzen-Ratio."""
        ...
```

**3. FeedingRateCalculator:**

```python
class FeedingRecommendation(BaseModel):
    """Tagesaktuelle Fütterungsempfehlung."""
    recommended_g: float
    base_rate_percent: float  # Prozent der Biomasse
    temperature_factor: float  # Q10-Korrektur
    cycling_factor: float  # Ramp-up-Faktor (0.25-1.0)
    species_name: str
    biomass_kg: float
    water_temp_c: float
    notes: list[str]

class RampUpSchedule(BaseModel):
    """Futter-Ramp-up-Plan nach Cycling/Dormanz."""
    weeks: list[dict]  # [{week: 1, percent: 25, daily_g: 18.75}, ...]
    target_daily_g: float
    reason: str  # "post_cycling" | "post_dormancy" | "new_stock"

class FeedingRateCalculator:
    """Berechnet temperaturkorrigierte Fütterungsempfehlungen."""

    # Basis-Fütterungsrate (% der Biomasse/Tag) bei Optimaltemperatur
    BASE_FEED_RATE = {
        'warmwater': 0.03,   # 3% (Tilapia, Wels)
        'temperate': 0.025,  # 2.5% (Karpfen, Zander)
        'coldwater': 0.02,   # 2% (Forelle, Saibling)
    }

    # Default-Proteingehalt nach Futter-Typ (für TAN-Berechnung, vgl. P-004)
    DEFAULT_PROTEIN_BY_FEED_TYPE = {
        'carnivore': 0.45,   # 45% Protein (Forelle, Zander, Barsch, Wels)
        'omnivore': 0.32,    # 32% Protein (Tilapia, Karpfen, Goldfisch)
        'herbivore': 0.28,   # 28% Protein
    }

    def calculate_daily_feed(
        self,
        total_biomass_kg: float,
        water_temp_c: float,
        species: FishSpecies,
        cycling_status: CyclingStatus,
    ) -> FeedingRecommendation:
        """
        Temperaturkorrigierte Fütterungsempfehlung.

        Temperatur-Korrekturfaktor (asymmetrische Kurve):
        - water_temp < optimal_min:
            temp_factor = 2^((water_temp - optimal_min) / 10)  (Q10-Reduktion)
        - optimal_min <= water_temp <= optimal_max:
            temp_factor = 1.0  (Optimum)
        - water_temp > optimal_max:
            temp_factor = max(0, 1 - (water_temp - optimal_max) / (max_temp - optimal_max))
            (linearer Abfall wegen Hitzestress)
        - water_temp >= max_temp:
            temp_factor = 0  (Fütterung stoppen!)

        Bei cycling_status != 'cycled': Ramp-up-Faktor anwenden.
        Bei fish_response='refused': Empfehlung 0g + Warnung.
        """
        ...

    def calculate_tan_production(
        self, daily_feed_g: float, protein_percent: float = 32.0,
    ) -> float:
        """
        Geschätzte TAN-Produktion aus Futtermenge und Proteingehalt.
        Formel: TAN = Futter × Proteingehalt × 0.092
        (Protein → Stickstoff: ÷6.25, davon ~57.5% als TAN ausgeschieden)
        Fallback ohne Proteinangabe: 3% des Futtergewichts (≈ 32% Protein).
        Karnivores Futter (45% Protein) → ~4.1%, nicht 3%!
        """
        return daily_feed_g * (protein_percent / 100) * 0.092

    def calculate_ramp_up_schedule(
        self,
        target_feed_g: float,
        reason: str,
        water_temp_c: float = 25.0,
    ) -> RampUpSchedule:
        """
        Temperaturabhängiger Ramp-up-Plan nach Cycling oder Dormanz.

        Basis-Plan (≥20°C): Woche 1-2: 25%, Woche 3-4: 50%, Woche 5-6: 75%, ab Woche 7: 100%.
        Temperaturkorrektur: ramp_duration_weeks = 7 / temp_factor (Q10-basiert).
        Bei 15-20°C: ≈14 Wochen. Bei <15°C: Ramp-up nicht starten (zu kalt).

        Wasserqualitäts-Gate: Jede Stufe nur weiter steigern wenn
        TAN <0.5 mg/L UND NO2 <0.5 mg/L. Bei Spikes: aktuelle Stufe beibehalten.
        """
        ...
```

**4. AquaponicsSafetyValidator:**

```python
class SafetyViolation(BaseModel):
    """Sicherheitsverletzung in Aquaponik-System."""
    violation_type: Literal['synthetic_fertilizer', 'chlorine', 'copper_pesticide', 'excessive_water_change', 'temperature_incompatible', 'fe_edta_ph']
    severity: Literal['warning', 'block']
    message_de: str
    message_en: str

class AquaponicsSafetyValidator:
    """Verhindert fischgiftige Substanzen in Aquaponik-Systemen."""

    def validate_fertilizer_safe(
        self,
        fertilizer: Fertilizer,
        system: AquaponicSystem,
    ) -> Optional[SafetyViolation]:
        """
        Prüft ob ein Dünger in Aquaponik-Systemen eingesetzt werden darf.
        Blockiert alle Dünger mit aquaponic_safe=false.
        Spezialfall: Fe-EDTA warnt bei System-pH >6.5 (instabil, wirkt nicht).
        """
        ...

    def validate_no_chlorine(
        self,
        water_source: str,
        chlorine_ppm: Optional[float],
        chloramine_ppm: Optional[float],
    ) -> Optional[SafetyViolation]:
        """
        Warnt bei gechlortem Wasser — differenziert zwischen:
        - Freies Chlor (>0.003 ppm gefährlich für Fische, >0.05 ppm für Biofilter):
          Kann durch Abstehen (24-48h) oder Vitamin C entfernt werden.
        - Chloramin (>0.003 ppm gefährlich): Kann NICHT durch Abstehen entfernt
          werden — erfordert Aktivkohlefilter oder Ascorbinsäure-Behandlung.
        Siehe auch REQ-014 Chlor/Chloramin-Differenzierung.
        """
        ...

    def validate_no_copper_pesticide(
        self,
        treatment: Treatment,  # REQ-010
        system: AquaponicSystem,
    ) -> Optional[SafetyViolation]:
        """
        Blockiert kupferbasierte Pflanzenschutzmittel in Aquaponik.
        Kupfer ist bereits in geringen Konzentrationen (>0.1 ppm) fischgiftig.
        """
        ...

    def validate_water_change_rate(
        self,
        change_volume_l: float,
        system_volume_l: float,
    ) -> Optional[SafetyViolation]:
        """
        Warnt bei Wasserwechsel >20% des Systemvolumens.
        Große Wasserwechsel verursachen Fischstress (pH/Temperatur-Schock).
        """
        ...

    def validate_temperature_compatibility(
        self,
        fish_species: FishSpecies,
        plant_species: Species,
    ) -> Optional[SafetyViolation]:
        """
        Prüft Temperaturzonen-Kompatibilität zwischen Fisch und Pflanze.
        Nutzt compatible_fish_plant / incompatible_fish_plant Edges.
        """
        ...
```

**5. BiofilterManager:**

```python
class BiofilterDimensioning(BaseModel):
    """Biofilter-Dimensionierungsempfehlung."""
    required_surface_area_m2: float
    current_surface_area_m2: Optional[float]
    status: Literal['sufficient', 'marginal', 'insufficient']
    daily_tan_production_g: float
    filter_capacity_g_tan_per_day: float

class BiofilterManager:
    """Verwaltet Biofilter-Status und Dimensionierung."""

    # Spezifische Oberfläche (SSA) pro Filtermedium
    SSA_M2_PER_M3 = {
        'media_bed_integrated': 300,   # Blähton
        'mbbr': 650,                   # K1/K3 Medien
        'trickle': 200,                # Lavastein
        'fluidized_bed': 1000,         # Sand
    }

    # Nitrifikationskapazität (mg TAN/m²/Tag) bei 25°C
    NITRIFICATION_RATE_MG_PER_M2_PER_DAY = 0.5  # Konservativ

    def estimate_required_surface_area(
        self,
        daily_feed_g: float,
        temp_c: float,
        filter_type: BiofilterType,
    ) -> BiofilterDimensioning:
        """
        Berechnet benötigte Biofilter-Oberfläche.
        TAN-Produktion = daily_feed_g × (protein_percent/100) × 0.092
        Kapazität = SSA × Volume × Nitrifikationsrate × Temp-Faktor
        Temperatur-Faktor: Q10-Regel, aber:
        - Nitrifikation <5°C = 0 (praktischer Stopp)
        - Zwischen 5–10°C: <10% der Nominalkapazität
        - Referenztemperatur: 25°C
        """
        ...

    def track_maturation(
        self,
        water_tests: list[WaterTest],
        system: AquaponicSystem,
    ) -> CyclingStatus:
        """
        Bestimmt Cycling-Status aus Wassertest-Verlauf.
        Delegiert an NitrogenCycleEngine.detect_cycling_phase.
        Aktualisiert system.cycling_status bei Status-Wechsel.
        """
        ...

    def calculate_turnover_rate(
        self,
        pump_flow_lph: float,
        system_volume_l: float,
    ) -> float:
        """
        Berechnet Umwälzrate (Soll: 1-2x/h).
        turnover = pump_flow_lph / system_volume_l
        """
        return pump_flow_lph / system_volume_l if system_volume_l > 0 else 0

    def seasonal_reactivation_plan(
        self,
        dormant_since: date,
        current_temp_c: float,
    ) -> Optional[RampUpSchedule]:
        """
        Erzeugt Futter-Ramp-up-Plan für Frühlings-Reaktivierung.
        Nur wenn cycling_status='dormant' und temp >15°C.
        """
        ...
```

**6. FishHealthMonitor:**

```python
class HealthAlert(BaseModel):
    """Gesundheitswarnung für Fischbestand."""
    alert_type: Literal['mortality_rate', 'feeding_refusal', 'water_quality', 'temperature_stress']
    severity: Literal['info', 'warning', 'critical']
    message_de: str
    message_en: str
    recommended_action: str

class FishHealthMonitor:
    """Überwacht Fischgesundheit basierend auf Mortalität, Fressverhalten und Wasserqualität."""

    # Schwellenwerte
    MORTALITY_RATE_WARNING = 0.02     # >2% pro Woche = Warnung
    MORTALITY_RATE_CRITICAL = 0.05    # >5% pro Woche = kritisch
    REFUSED_FEEDING_THRESHOLD = 2     # 2+ aufeinanderfolgende "refused" = Alarm

    def evaluate_fish_health(
        self,
        fish_stock: FishStock,
        recent_feedings: list[FishFeedingEvent],
        recent_water_tests: list[WaterTest],
        fish_species: FishSpecies,
    ) -> list[HealthAlert]:
        """
        Integrierte Gesundheitsbewertung:
        1. Mortalitätsrate: % Verlust pro Woche (mortality_count / initial_count)
        2. Fressverhalten: 2+ aufeinanderfolgende 'refused' Events → Gesundheitsalarm
        3. Wasserqualität: DO < stress_threshold, TAN > species max
        4. Temperatur: Außerhalb Stressbereich → Warnung
        """
        ...

    def calculate_mortality_rate(
        self,
        fish_stock: FishStock,
        period_days: int = 7,
    ) -> float:
        """
        Berechnet Mortalitätsrate (% Verlust pro Zeitraum).
        rate = mortality_in_period / count_at_period_start × 100
        """
        ...
```

### Pydantic-Modelle (API-Schemas):

```python
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, date
from typing import Optional

# --- Create/Update Schemas ---

class AquaponicSystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    system_type: AquaponicSystemType
    total_volume_liters: float = Field(..., gt=0)
    grow_area_m2: float = Field(..., gt=0)
    biofilter_type: Optional[BiofilterType] = None
    biofilter_volume_liters: Optional[float] = Field(None, gt=0)
    has_clarifier: bool = False
    clarifier_type: Optional[ClarifierType] = None
    has_mineralization: bool = False
    has_vermicompost: bool = False
    daily_feed_target_g: float = Field(0, ge=0)
    outdoor: bool = False
    backup_power: bool = False
    ph_target_min: float = Field(6.8, ge=5.0, le=9.0)
    ph_target_max: float = Field(7.2, ge=5.0, le=9.0)

    @model_validator(mode='after')
    def validate_biofilter(self):
        if self.system_type != AquaponicSystemType.MEDIA_BED and self.biofilter_type is None:
            raise ValueError(
                "DWC/NFT/Hybrid/Wicking-Bed benötigen einen separaten Biofilter "
                "(biofilter_type muss gesetzt sein). Nur Media-Bed hat integrierten Biofilter."
            )
        if self.has_clarifier and self.clarifier_type is None:
            raise ValueError("Clarifier-Typ muss angegeben werden wenn has_clarifier=true.")
        return self

class FishStockCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    species_key: str
    count: int = Field(..., gt=0)
    avg_weight_g: float = Field(..., gt=0)
    stocking_date: date

class WaterTestCreate(BaseModel):
    ph: float = Field(..., ge=0, le=14)
    ammonia_tan_mgl: float = Field(..., ge=0)
    nitrite_mgl: float = Field(..., ge=0)
    nitrate_mgl: float = Field(..., ge=0)
    temperature_c: float = Field(..., ge=0, le=45)
    dissolved_oxygen_mgl: Optional[float] = Field(None, ge=0)
    kh_dh: Optional[float] = Field(None, ge=0)
    gh_dh: Optional[float] = Field(None, ge=0)
    iron_ppm: Optional[float] = Field(None, ge=0)
    potassium_ppm: Optional[float] = Field(None, ge=0)
    calcium_ppm: Optional[float] = Field(None, ge=0)
    magnesium_ppm: Optional[float] = Field(None, ge=0)
    phosphate_ppm: Optional[float] = Field(None, ge=0)
    source: Literal['manual', 'sensor', 'test_kit'] = 'manual'
    notes: Optional[str] = None

class FishFeedingEventCreate(BaseModel):
    feed_brand: Optional[str] = None
    feed_type: FeedType = FeedType.PELLET
    protein_percent: Optional[float] = Field(None, ge=0, le=100)
    amount_g: float = Field(..., gt=0)
    water_temp_c: float = Field(..., ge=0, le=45)
    fish_response: FishFeedingResponse = FishFeedingResponse.NORMAL
    notes: Optional[str] = None

class SupplementationEventCreate(BaseModel):
    supplement_type: SupplementType
    amount_ml: Optional[float] = Field(None, gt=0)
    amount_g: Optional[float] = Field(None, gt=0)
    target_parameter: str
    measured_before: Optional[float] = None
    measured_after: Optional[float] = None
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_amount(self):
        if self.amount_ml is None and self.amount_g is None:
            raise ValueError("Entweder amount_ml oder amount_g muss angegeben werden.")
        return self
```

## 4. API-Endpunkte

Router: `/api/v1/t/{tenant_slug}/aquaponics`

### 4.1 Aquaponic Systems CRUD (6 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/systems` | Neues Aquaponik-System erstellen | Mitglied |
| `GET` | `/systems` | Alle Systeme des Tenants | Mitglied |
| `GET` | `/systems/{system_key}` | System-Details inkl. Status, Stocks, letzte Wasserwerte | Mitglied |
| `PATCH` | `/systems/{system_key}` | System-Konfiguration aktualisieren | Mitglied |
| `DELETE` | `/systems/{system_key}` | System entfernen (nur wenn kein Fischbestand) | Admin |
| `POST` | `/systems/{system_key}/cycling-status` | Cycling-Status manuell setzen (Override) | Mitglied |

### 4.2 Fish Species Stammdaten (4 Endpunkte, global)

Router: `/api/v1/fish-species` (nicht tenant-scoped, Seed-Daten)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/` | Alle Fischarten (Filter: temperature_zone, feed_type) | Mitglied |
| `GET` | `/{species_key}` | Fischart-Details | Mitglied |
| `GET` | `/{species_key}/compatible-plants` | Kompatible Pflanzenarten (Graph-Traversal) | Mitglied |
| `GET` | `/by-temperature-zone/{zone}` | Fischarten nach Temperaturzone | Mitglied |

### 4.3 Fish Stocks (6 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/systems/{system_key}/fish-stocks` | Neuen Fischbestand anlegen | Mitglied |
| `GET` | `/systems/{system_key}/fish-stocks` | Alle Bestände eines Systems | Mitglied |
| `PATCH` | `/systems/{system_key}/fish-stocks/{stock_key}` | Bestand aktualisieren (Gewicht, Anzahl) | Mitglied |
| `DELETE` | `/systems/{system_key}/fish-stocks/{stock_key}` | Bestand entfernen (Ernte/Umsetzung). Hinweis: Fisch-Ernte-Workflow wird in zukünftiger Erweiterung über REQ-007 (Erntemanagement) abgebildet. Bei Speisefischen: Tierarzneimittel-Rückstandsverordnung (EU-VO 37/2010) definiert Wartezeiten. | Mitglied |
| `POST` | `/systems/{system_key}/fish-stocks/{stock_key}/mortality` | Mortalitätseintrag (Verluste dokumentieren) | Mitglied |
| `GET` | `/systems/{system_key}/fish-stocks/{stock_key}/biomass-history` | Gewichtsverlauf über Zeit | Mitglied |

### 4.4 Water Tests (5 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/systems/{system_key}/water-tests` | Wassertest erfassen (immutable, free_ammonia wird berechnet) | Mitglied |
| `GET` | `/systems/{system_key}/water-tests` | Wassertest-Historie (Pagination + Zeitraum-Filter) | Mitglied |
| `GET` | `/systems/{system_key}/water-quality-status` | Aktuelle Bewertung mit Alarmstufen (artspezifisch) | Mitglied |
| `GET` | `/systems/{system_key}/nitrogen-cycle-chart` | Zeitreihe TAN/NO2/NO3/free-NH3 für Diagramm | Mitglied |
| `GET` | `/systems/{system_key}/cycling-progress` | Biofilter-Cycling-Fortschritt + geschätzte Fertigstellung | Mitglied |

### 4.5 Fish Feeding (4 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/systems/{system_key}/feeding-events` | Fütterung dokumentieren | Mitglied |
| `GET` | `/systems/{system_key}/feeding-events` | Fütterungshistorie (Pagination + Zeitraum) | Mitglied |
| `GET` | `/systems/{system_key}/feeding-recommendation` | Tagesaktuelle Empfehlung (temperaturkorrigiert + Cycling-Faktor) | Mitglied |
| `GET` | `/systems/{system_key}/fcr-analysis` | FCR über Zeitraum (Futtermenge vs. Biomassezuwachs) | Mitglied |

### 4.6 Supplementation (3 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/systems/{system_key}/supplementation-events` | Supplementierung dokumentieren | Mitglied |
| `GET` | `/systems/{system_key}/supplementation-events` | Supplementierungshistorie | Mitglied |
| `GET` | `/systems/{system_key}/deficiency-check` | Aktuelle Nährstoffdefizit-Analyse (Fe, K, Ca, Mg) mit Empfehlung | Mitglied |

### 4.7 Safety & Alerts (2 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/systems/{system_key}/safety-status` | Gesamtbewertung: Wasserwerte, Besatzdichte, Temperatur, Biofilter | Mitglied |
| `GET` | `/systems/{system_key}/alerts` | Aktive Warnungen und Alarme (sortiert nach Severity) | Mitglied |

### 4.8 Fish Health (2 Endpunkte)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/systems/{system_key}/fish-health` | Integrierte Gesundheitsbewertung: Mortalitätsrate, Fressverhalten, Wasserqualität-Stress | Mitglied |
| `GET` | `/systems/{system_key}/fish-stocks/{stock_key}/mortality-rate` | Mortalitätsrate (% pro Woche/Monat) mit Trendanalyse | Mitglied |

### Request/Response-Beispiele:

**POST /systems/{key}/water-tests — Wassertest mit berechneter freier Ammoniak:**
```json
// Request
{
  "ph": 7.2,
  "ammonia_tan_mgl": 1.5,
  "nitrite_mgl": 0.3,
  "nitrate_mgl": 45,
  "temperature_c": 26,
  "dissolved_oxygen_mgl": 6.5,
  "kh_dh": 5.0,
  "source": "test_kit"
}

// Response (201 Created)
{
  "key": "wt_20260227_001",
  "tested_at": "2026-02-27T10:30:00Z",
  "ph": 7.2,
  "ammonia_tan_mgl": 1.5,
  "nitrite_mgl": 0.3,
  "nitrate_mgl": 45,
  "temperature_c": 26,
  "dissolved_oxygen_mgl": 6.5,
  "kh_dh": 5.0,
  "free_ammonia_mgl": 0.0143,
  "source": "test_kit",
  "alerts": [
    {
      "parameter": "nitrite",
      "value": 0.3,
      "limit": 0.1,
      "severity": "critical",
      "message": "Nitrit 0.3 mg/L überschreitet Grenzwert für Regenbogenforelle (max 0.1 mg/L)"
    }
  ]
}
```

**GET /systems/{key}/feeding-recommendation:**
```json
// Response
{
  "recommended_g": 56.25,
  "base_rate_percent": 3.0,
  "temperature_factor": 0.75,
  "cycling_factor": 1.0,
  "species_name": "Nil-Tilapia",
  "biomass_kg": 2.5,
  "water_temp_c": 22,
  "notes": [
    "Wassertemperatur 22°C liegt unter Optimum (26-30°C) — Futtermenge um 25% reduziert (Q10-Korrektur)",
    "Biofilter cycled — volle Fütterung erlaubt"
  ]
}
```

### Fehlerbehandlung:

| HTTP-Status | Bedingung |
|-------------|-----------|
| `400` | Ungültige Eingabewerte (negativer TAN, pH >14, etc.) |
| `404` | System, FishStock oder FishSpecies nicht gefunden |
| `409` | FishStock löschen mit >0 Fischen (erst Mortalität/Ernte dokumentieren) |
| `422` | Validierungsfehler: Biofilter fehlt bei DWC/NFT; Besatzdichte überschritten; fischgiftiger Dünger |

## 5. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt folgt den Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung).

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Fish Species (global) | Mitglied | Admin | Admin |
| Aquaponic Systems | Mitglied | Mitglied | Admin |
| Fish Stocks | Mitglied | Mitglied | Mitglied |
| Water Tests | Mitglied | Mitglied | — (immutable) |
| Feeding Events | Mitglied | Mitglied | — (immutable) |
| Supplementation Events | Mitglied | Mitglied | — (immutable) |

## 6. Abhängigkeiten

**Erforderliche Module:**

| REQ/NFR | Priorität | Beschreibung |
|---------|-----------|-------------|
| REQ-014 (Tankmanagement) | **HOCH** | Tank-Entitäten als Fischtank/Biofilter/Sump, `feeds_from`-Edge für Wasserkaskade, TankState für Wasserwerte |
| REQ-002 (Standortverwaltung) | **HOCH** | Slots als Growbed-Positionen, Location als übergeordnete Zuordnung |
| REQ-001 (Stammdaten) | **HOCH** | Species für Fisch-Pflanzen-Kompatibilitäts-Graph (compatible_fish_plant/incompatible_fish_plant Edges) |
| REQ-023 (Auth) | **HOCH** | JWT-Authentifizierung, User-Referenz für Events |
| REQ-024 (Mandanten) | **HOCH** | Tenant-Scoping für alle Aquaponik-Ressourcen |
| NFR-001 (Architektur) | **HOCH** | 5-Layer-Architektur (API → Service → Engine → Repository → ArangoDB) |
| NFR-003 (Code Standard) | **HOCH** | Source Code in English, Spezifikation in German |

**Optionale Module:**

| REQ/NFR | Priorität | Beschreibung |
|---------|-----------|-------------|
| REQ-004 (Dünge-Logik) | **MITTEL** | `aquaponic_safe`-Feld auf Fertilizer; Supplementierung als Aquaponik-spezifischer Dünge-Modus |
| REQ-005 (Sensorik) | **MITTEL** | Automatische Wassertest-Erfassung via Sensoren (ammonia, nitrite, nitrate als neue Parameter) |
| REQ-007 (Erntemanagement) | **MITTEL** | Fisch-Ernte-Workflow in zukünftiger Erweiterung (HarvestBatch für Fische, Schlachtgewicht-Tracking). Tierarzneimittel-Rückstandsverordnung (EU-VO 37/2010) definiert Wartezeiten für Speisefische. |
| REQ-010 (IPM) | **NIEDRIG** | Kupfer-PSM-Verbot in Aquaponik-Systemen (validate_no_copper_pesticide) |
| REQ-022 (Pflegeerinnerungen) | **NIEDRIG** | Fütterungs-/Wassertest-Erinnerungen als CareProfile-Erweiterung |
| REQ-019 (Substrate) | **NIEDRIG** | Media-Bed = `clay_pebbles`, DWC/NFT = `none` (bereits vorhanden) |

**Wird benötigt von:**
- (aktuell keine — REQ-026 ist eine Leaf-Dependency)

**Grapherweiterungen am Named Graph `kamerplanter_graph`:**
```json
{
  "orphanCollections_add": ["fish_species", "fish_stocks", "aquaponic_systems", "water_tests", "fish_feeding_events", "supplementation_events"],
  "edgeDefinitions_add": [
    { "collection": "has_fish_stock", "from": ["aquaponic_systems"], "to": ["fish_stocks"] },
    { "collection": "stock_of_species", "from": ["fish_stocks"], "to": ["fish_species"] },
    { "collection": "system_has_tank", "from": ["aquaponic_systems"], "to": ["tanks"] },
    { "collection": "system_has_growbed", "from": ["aquaponic_systems"], "to": ["slots"] },
    { "collection": "water_test_for", "from": ["water_tests"], "to": ["aquaponic_systems"] },
    { "collection": "feeding_for_stock", "from": ["fish_feeding_events"], "to": ["fish_stocks"] },
    { "collection": "supplementation_for", "from": ["supplementation_events"], "to": ["aquaponic_systems"] },
    { "collection": "compatible_fish_plant", "from": ["fish_species"], "to": ["species"] },
    { "collection": "incompatible_fish_plant", "from": ["fish_species"], "to": ["species"] }
  ]
}
```

**Celery-Tasks:**
- `check_aquaponics_alerts` — Stündlich: Prüft alle Aquaponik-Systeme auf kritische Wasserwerte (letzte WaterTests vs. artspezifische Grenzwerte), erzeugt Alerts
- `update_cycling_status` — Täglich: Prüft Cycling-Fortschritt, aktualisiert cycling_status bei Zustandswechsel
- `generate_feeding_reminders` — Täglich (06:00 UTC): Erzeugt Fütterungs-Tasks (REQ-006) mit tagesaktueller Empfehlung
- `generate_water_test_reminders` — Täglich: Erzeugt Wassertest-Erinnerungen wenn letzter Test >**1 Tag** (cycling — tägliche Tests empfohlen, da TAN/NO2-Spikes innerhalb von 24h letal sein können) oder >7 Tage (cycled) zurückliegt
- `evaluate_fish_health` — Täglich: Prüft Mortalitätsrate (>2%/Woche = Warnung, >5% = kritisch) und Fressverhalten (2+ aufeinanderfolgende "refused" = Gesundheitsalarm)

## 7. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **FishSpecies Seed-Daten:** 8 Fischarten mit artspezifischen Grenzwerten geladen (Tilapia, Forelle, Karpfen, Europ. Wels, Barsch, Goldfisch, Zander, Saibling)
- [ ] **AquaponicSystem CRUD:** Vollständiges Erstellen, Lesen, Aktualisieren und Löschen von Systemen
- [ ] **Systemtyp-Validierung:** DWC/NFT/Hybrid/Wicking benötigen separaten Biofilter (biofilter_type Pflicht), Media-Bed nicht
- [ ] **FishStock CRUD:** Bestandsverwaltung mit Mortalitäts-Tracking und Biomasse-Berechnung
- [ ] **Besatzdichte-Prüfung:** Warnung bei Überschreitung der artspezifischen max_stocking_density
- [ ] **WaterTest immutable:** Insert-only (kein Update/Delete), free_ammonia wird automatisch via Emerson-Formel berechnet
- [ ] **Emerson-Formel korrekt:** Testvektor: pH 7.0, 25°C, TAN 1.0 → free NH3 ≈ 0.0057 mg/L (±5%)
- [ ] **Artspezifische Grenzwertprüfung:** Forelle (NO2 <0.1, DO >7) strenger als Tilapia (NO2 <1.0, DO >5)
- [ ] **Cycling-Status-Transitions:** new → cycling → cycled → dormant korrekt basierend auf Wassertest-Historie
- [ ] **Cycling-Erkennung:** 7 aufeinanderfolgende Tage mit TAN <0.25 UND NO2 <0.1 bei ≥80% Zielfutter UND >15°C → cycled
- [ ] **AquaponicsSafetyValidator:** Blockiert synthetische Dünger (aquaponic_safe=false) auf Aquaponik-Systemen mit HTTP 422
- [ ] **Chlor-Warnung:** Warnt bei gechlortem Wasser in Aquaponik-Systemen
- [ ] **Kupfer-PSM-Verbot:** Blockiert kupferbasierte Pflanzenschutzmittel in Aquaponik
- [ ] **FeedingRateCalculator:** Temperaturkorrigierte Empfehlung (asymmetrische Kurve: Q10 unter Optimum, linearer Abfall bei Hitzestress, Stopp bei max_temp)
- [ ] **Ramp-up-Schedule:** Temperaturabhängiger Plan nach Cycling/Dormanz (Basis 7 Wochen bei ≥20°C, länger bei niedrigeren Temperaturen, Wasserqualitäts-Gate)
- [ ] **Fisch-Pflanzen-Kompatibilität:** Graph-Traversal über compatible_fish_plant/incompatible_fish_plant
- [ ] **Temperaturzonen-Match:** Warnung bei Warmwasser-Fisch + Kaltwasser-Pflanze (und umgekehrt)
- [ ] **Alkalitäts-Crash-Warnung:** Warnt bei KH <4°dH + aktiver Fütterung (pH-Crash-Risiko)
- [ ] **Nährstoffdefizit-Analyse:** Erkennt Fe/K/Ca/Mg/Zn/B-Defizite basierend auf Wassertests, inkl. Phosphat-Akkumulationswarnung (>80 ppm)
- [ ] **Supplementierung dokumentiert:** Alle Ergänzungen als immutable Events mit vorher/nachher-Messwert
- [ ] **Regulatorische Hinweise:** FishSpecies.regulatory_notes zeigt länderspezifische Auflagen
- [ ] **Saisonale Logik:** Outdoor-Systeme erhalten saisonale Fütterungsanpassungen und Dormanz-Management
- [ ] **GH-Bewertung:** evaluate_water_quality prüft GH (<4°dH Warnung bei Osmose/Regenwasser, >20°dH Warnung bei empfindlichen Arten)
- [ ] **Temperatur-Schwellenstufen:** critical (letal), warning (Stress), info (suboptimal) artspezifisch
- [ ] **DO-Sättigung:** Warnung wenn DO < 70% der temperaturabhängigen Sättigung (Benson & Krause 1984)
- [ ] **Nitrifikations-Untergrenze:** Biofilter-Kapazität = 0 unter 5°C, <10% zwischen 5–10°C
- [ ] **FishHealthMonitor:** Mortalitätsrate >2%/Woche = Warnung, 2+ refused feedings = Gesundheitsalarm
- [ ] **DEFAULT_PROTEIN_BY_FEED_TYPE:** TAN-Berechnung berücksichtigt feed_type (carnivore 45%, omnivore 32%, herbivore 28%)
- [ ] **Celery-Beat:** 4 Tasks registriert (alerts stündlich, cycling/feeding/water-test täglich)
- [ ] **Alle Collections/Edges im `kamerplanter_graph`** registriert (6 doc + 9 edge)
- [ ] **Wasserwechsel-Limit:** Warnung bei >20% Systemvolumen pro Eingriff

### Testszenarien:

**Szenario 1: Tilapia-DWC-System erstellen mit korrekter Besatzdichte**
```
GIVEN: Tenant "mein-garten", Tank "Fischtank 1" (500L, type=recirculation),
       Tank "MBBR Filter" (40L, type=recirculation),
       Tank "Sump" (100L, type=reservoir),
       DWC-Slots (4 m²)
WHEN: POST /api/v1/t/mein-garten/aquaponics/systems
      Body: { name: "Tilapia-Salat DWC", system_type: "dwc",
              total_volume_liters: 640, grow_area_m2: 4.0,
              biofilter_type: "mbbr", biofilter_volume_liters: 40 }
      + POST fish-stocks: { species_key: "tilapia_nile", count: 15, avg_weight_g: 150 }
THEN:
  - System erstellt mit cycling_status: "new"
  - Besatzdichte: 2.25 kg / 500L = 4.5 kg/1000L (OK, max 25)
  - Fisch-Pflanzen-Ratio: Feed 67.5g / 4m² = 16.9 g/m² (unter 100 g/m² — OK)
  - system_has_tank Edges für alle 3 Tanks erstellt
  - system_has_growbed Edges für DWC-Slots erstellt
```

**Szenario 2: Wassertest mit Ammoniak-Spike — Alarm + Fütterungsstopp**
```
GIVEN: Tilapia-DWC-System (cycling_status: "cycled"),
       Forellen-Species (max_tan: 0.5, max_nitrite: 0.1)
       — ABER System enthält Tilapia (max_tan: 2.0)
WHEN: POST water-tests
      Body: { ph: 7.5, ammonia_tan_mgl: 3.0, nitrite_mgl: 0.2,
              nitrate_mgl: 30, temperature_c: 28, source: "test_kit" }
THEN:
  - pKa = 0.09018 + 2729.92/301.15 = 9.155
  - free_ammonia berechnet: 3.0 × (1/(10^(9.155-7.5)+1)) = 0.065 mg/L
  - Alert: "Freies Ammoniak 0.065 mg/L — KRITISCH (Grenzwert 0.02 mg/L)"
  - TAN 3.0 > Tilapia-Maximum 2.0 → Warnung
  - Fütterungsempfehlung: 0g ("Fütterung stoppen bis TAN <0.5 mg/L")
  - Cycling-Status bleibt "cycled" (einzelner Spike → kein Reset)
```

**Szenario 3: Biofilter-Cycling-Erkennung**
```
GIVEN: Neues Aquaponik-System (cycling_status: "new"),
       14 Wassertests über 6 Wochen:
       Woche 1-2: TAN steigend (0.5 → 4.0), NO2 niedrig
       Woche 3-4: TAN fallend (4.0 → 1.0), NO2 steigend (0.1 → 3.0)
       Woche 5-6: TAN <0.25, NO2 <0.1, NO3 steigend (5 → 40)
WHEN: GET cycling-progress
THEN:
  - Status: "cycling" → "cycled" (nach 7 Tagen stabil)
  - Progress: 100%
  - Message: "Biofilter eingefahren — volle Besatzdichte möglich"
```

**Szenario 4: Synthetischer Dünger auf Aquaponik-Tank blockiert**
```
GIVEN: Aquaponik-System mit Tilapia,
       Dünger "Flora Micro" (aquaponic_safe: false, is_organic: false)
WHEN: System versucht Flora Micro auf Aquaponik-verbundenen Tank anzuwenden
THEN:
  - HTTP 422: "Synthetischer Dünger 'Flora Micro' ist nicht fischsicher
    (aquaponic_safe=false). Nur fischsichere Ergänzungsmittel
    (Fe-DTPA, KOH, Ca(OH)2, MgSO4) sind in Aquaponik erlaubt."
```

**Szenario 5: Forelle + Tomate — Temperatur-Inkompatibilitäts-Warnung**
```
GIVEN: Aquaponik-System mit Regenbogenforelle (coldwater, optimal 12-16°C),
       Pflanze "Tomate" (benötigt Wurzelzone >18°C)
WHEN: GET fish-species/trout_rainbow/compatible-plants
THEN:
  - Tomate erscheint in "incompatible" mit reason: "Temperaturzone inkompatibel:
    Forelle (coldwater, 12-16°C optimal) vs. Tomate (warmwater, >18°C Wurzelzone)"
  - Salat, Kresse, Petersilie erscheinen in "compatible" mit temperature_match: 0.9+
```

**Szenario 6: Saisonaler Ramp-up nach Winter-Dormanz**
```
GIVEN: Outdoor-Aquaponik-System (cycling_status: "dormant" seit November 2025),
       Wassertemperatur steigt auf 16°C im März 2026,
       Fütterung wird wieder aufgenommen
WHEN: POST feeding-events mit amount_g: 75 (volle Menge)
THEN:
  - Warnung: "Biofilter war dormant — Ramp-up-Plan empfohlen"
  - cycling_status: dormant → cycling
  - Fütterungsempfehlung generiert temperaturabhängigen Ramp-up:
    Bei 16°C (unter 20°C): Verlängerter Plan (~14 Wochen statt 7)
    Stufe 1: 18.75g (25%), Stufe 2: 37.5g (50%),
    Stufe 3: 56.25g (75%), Stufe 4: 75g (100%)
    Wasserqualitäts-Gate: Nächste Stufe nur wenn TAN <0.5 UND NO2 <0.5
```

**Szenario 7: Eisenmangel-Erkennung + Supplementierungs-Empfehlung**
```
GIVEN: Aquaponik-System mit ph_target 7.0,
       Wassertest: iron_ppm = 0.5 (unter Zielwert 2-5 ppm),
       Pflanzen zeigen Zwischenadern-Chlorose
WHEN: GET deficiency-check
THEN:
  - Defizit erkannt: "Eisen 0.5 ppm — unter Zielwert (2-5 ppm)"
  - Empfehlung: "Fe-DTPA nachdosieren (fischsicher, stabil bis pH 7.5).
    NICHT Fe-EDTA verwenden (instabil bei System-pH 7.0)."
  - Zusätzlich geprüft: K (OK), Ca (OK), Mg (OK)
```

**Szenario 8: Alkalitäts-Crash-Warnung bei niedriger KH**
```
GIVEN: Aquaponik-System mit daily_feed_target_g: 100,
       Wassertest: kh_dh = 3.0 (unter Schwelle 4.0°dH)
WHEN: POST water-tests (mit kh_dh: 3.0)
THEN:
  - Alert: "Karbonathärte 3.0°dH — pH-Crash-Risiko!
    Nitrifikation verbraucht ~7.1 mg CaCO3 pro mg NH4-N.
    Bei 100g Futter/Tag ≈ 3g TAN/Tag ≈ 21.3g CaCO3-Verbrauch/Tag.
    Nachpuffern mit Ca(OH)2 oder KOH empfohlen."
  - Severity: critical
```

---

**Hinweise für RAG-Integration:**
- Keywords: Aquaponik, Aquaponics, Fisch, Stickstoffkreislauf, Nitrogen Cycle, Ammoniak, Ammonium, Nitrit, Nitrat, Biofilter, Cycling, Einfahren, Besatzdichte, Stocking Density, FCR, Futterverwertung, Feed Conversion, Tilapia, Forelle, Karpfen, Koi, Wels, Barsch, Goldfisch, Zander, Saibling, Media-Bed, DWC, NFT, Wicking Bed, Swirl Filter, Trommelfilter, Mineralisierung, Wurmkompost, Vermicompost, Supplementierung, Chelat-Eisen, Kaliumhydroxid, Calciumhydroxid, Bittersalz, Karbonathärte, Alkalität, pH-Crash, Temperaturzone, Warmwasser, Kaltwasser, Ramp-up, Dormanz, Outdoor-Aquaponik, Fisch-Pflanzen-Verhältnis, Turnover Rate, Notstrom, Sachkundenachweis, Tierschutz, Invasive Art
- Fachbegriffe: TAN (Total Ammonia Nitrogen), NH3 (freies Ammoniak), NH4+ (Ammonium), NO2- (Nitrit), NO3- (Nitrat), Nitrifikation, Nitrosomonas, Nitrobacter, Nitrospira, KH (Karbonathärte), GH (Gesamthärte), SSA (Specific Surface Area), MBBR (Moving Bed Biofilm Reactor), FCR (Feed Conversion Ratio), Q10-Regel, Emerson-Formel, pKa, DO (Dissolved Oxygen), Fe-DTPA, Fe-EDDHA, Fe-EDTA, CaCO3, RAS (Recirculating Aquaculture System)
- Verknüpfung: REQ-014 (Tanks, TankState, feeds_from), REQ-002 (Slots, Locations), REQ-001 (Species für Kompatibilität), REQ-004 (Fertilizer.aquaponic_safe, Supplementierung), REQ-005 (Sensoren: ammonia, nitrite, nitrate), REQ-007 (Fisch-Ernte-Workflow, EU-VO 37/2010), REQ-010 (Kupfer-PSM-Verbot), REQ-019 (clay_pebbles, none), REQ-022 (Fütterungs-/Wassertest-Erinnerungen), REQ-023 (Auth), REQ-024 (Tenant-Scoping)

**Geplante Erweiterungen (v2.0):**
- Süßwassergarnelen (*Macrobrachium rosenbergii*, *Neocaridina davidi*) als neue Tiergruppe: Deutlich andere Wasserparameter (niedrigere TAN-Toleranz, höhere Ca-Anforderung für Häutung, extreme Cu-Empfindlichkeit). Erfordert separate FishSpecies-Einträge mit crustacean-spezifischen Feldern.
- Fisch-Ernte-Workflow (Integration REQ-007): HarvestBatch für Fische, Schlachtgewicht-Tracking, Tierarzneimittel-Wartezeiten
