# Agrarbiologische Prüfung der Bodenwasser-Bilanz mit Quellen (F-29, #3002)

| Feld | Wert |
|------|------|
| Datum | 2026-11-27 |
| Bezug | GitHub #3002; Feature F-29 „Bodenwasser-Bilanz im Gießbedarf“ (`project/features/soil-water-balance.md`, Roadmap R-27); REQ-037 §3.1, §3.3, §5, §7; REQ-053 E-10 (§32.2), R-008, GP-FR-113/114/117, §15.1 |
| Grundlage | Strukturiertes Review von `agrobiology-requirements-reviewer` vom 2026-11-27 (ohne Websuche, alle Zahlen aus dem Gedächtnis, vom Agenten selbst als „FAIL für die Übernahme der Zahlenwerte ohne Gegenlesen, PASS für die Modellstruktur“ eingestuft). Dieses Dokument ist der Gegenlese-Durchgang mit Quellen. |
| Methode | E-10: je Wert drei voneinander unabhängige Quellen, sonst bleibt der Wert `null`. Regeln wie in `spec/analysis/agrobiology-soil-hazards-research-2888.md` §0 (Unabhängigkeit, Prüftiefe, Belegklassen). |
| Status | Recherche, keine Entscheidung — Vorschläge für den Betreiber. Kein Code, keine REQ und keine Feature-Datei wurde geändert. |

## 0. Lesehinweise zur Methode

- **Regeln.** Es gelten die Regeln aus `agrobiology-soil-hazards-research-2888.md` §0: Mehrere Seiten oder Dokumente derselben Institution zählen als **eine** Quelle. Eine Quelle, die erkennbar eine andere wiedergibt, zählt mit ihr zusammen als eine. „verifiziert“ heißt: Text der Quelle selbst gelesen (HTML oder per `pdftotext` aus dem PDF). „Suchauszug“ heißt: Aussage nur aus dem Treffertext einer Suche oder aus zweiter Hand; Suchauszüge zählen nicht zum Belegstatus.
- **Belegklassen.** **3/3** = drei unabhängige, verifizierte Quellen. **3/3 (Spanne)** = der vorgeschlagene Wert liegt in den Spannen dreier unabhängiger Quellen (Betreiberentscheid vom 2026-11-22 zur Bodengefahren-Recherche: Spannen zählen). **2/3**, **1/3**, **widersprüchlich**, **nicht gefunden** wie dort. Ein Wert unter 3/3 ist nach E-10 nicht verwendbar und bleibt `null`.
- **Zusammengehörige Quellen in dieser Recherche.**
  - British Columbia: Irrigation Management Guide, Factsheet 577.100-3 und die Farmwest-Seite [Q5] sowie das Trickle Irrigation Manual [Q6] sind eine Quelle.
  - Alberta Agdex 563-1 nennt für seine Spannen Howell 2003 als Quelle; beide zählen zusammen als eine [Q18]. Howell 2003 selbst war nicht abrufbar.
  - Die Tabelle der University of Wisconsin nennt als Quelle ein USDA-NRCS-Dokument; sie zählt mit NRCS zusammen [Q7, Q10].
  - Die hessischen und rheinland-pfälzischen nFK-Tabellen gehen beide auf die Tabellen der Ad-hoc-AG Boden zurück (Kartieranleitung); sie zählen zusammen als eine deutsche Tabellenlinie [Q12, Q13]. Die Geisenheimer Werte stammen laut Quellenzeile von ALB Bayern und sind eine zweite deutsche Linie [Q11].
- **Arbeitsweise.** Fundstellen wurden über Websuche ermittelt, zum Teil durch Hilfsagenten. Jede hier als „verifiziert“ geführte Quelle wurde danach für dieses Dokument erneut abgerufen und im Volltext gelesen; die Zitate stammen aus diesem Abruf.
- **Was sich öffnen ließ.** FAO-56 (Kapitel 6, 7, 8, 10), FAO-Paper 25 (Kapitel II), die FAO-Schulungshefte 3 und 4, NRCS NEH Part 652 (Kapitel 2 und 3, über einen Spiegel), die Dokumente aus British Columbia, Colorado, Utah, Oregon, Nebraska, Texas, Iowa, Connecticut, Geisenheim, HLNUG, LGB Rheinland-Pfalz, GD NRW, Bayerische Gartenakademie, IGZ, LWK Niedersachsen, DWD, WMO, RHS und die Substrat-Arbeiten.
- **Was sich nicht öffnen ließ.** Howell 2003 im Original; die Bodenkundliche Kartieranleitung KA5 selbst (nur über Landesämter); KTBL-Arbeitsblatt 703 (Zugriff abgewiesen); University of Minnesota, University of Missouri, UF/IFAS (HTTP 403 oder Umleitungsschleife); FAO-Paper 217 (Gewächshaus); Chalker-Scott 2007 im Original; ECMWF-Verifikationsberichte wurden nicht selbst gelesen. LfL Bayern, LLH Hessen, DLR Rheinland-Pfalz, AGES, UC ANR, Cornell und UMass lieferten zu den Fragen keine geöffnete Fundstelle.
- **Einheiten.** 1 mm Wasser = 1 L/m². Vol.-% = mm je dm Bodentiefe. 1 in/ft = 83,3 mm/m = 8,33 mm/dm; 0,01 in/in = 1 mm/dm.
- **Abweichung des Reviews von diesem Branch.** Das Review meldete, die Feature-Datei habe nur 130 Zeilen und enthalte die Abschnitte „Re-run 2026-11-27“ und „Offene Betreiberentscheidungen“ nicht. Der Agent las einen älteren Stand. Auf diesem Branch hat `project/features/soil-water-balance.md` 253 Zeilen; „Re-run 2026-11-27“ steht ab `:110`, „Offene Betreiberentscheidungen (Re-run 2026-11-27)“ ab `:216`. Die 15 Parameter des Reviews entsprechen der Liste ab `:237` in Reihenfolge und Inhalt.

---

## 1. Modellrahmen

### 1.1 Das Speichermodell des Reviews

Der Speicher hat den Füllstand S in mm und die Kapazität C in mm:

- **Tagesschritt:** S(t) = min(C, max(0, S(t−1) + Regen + Gießen − ETc)). Was über C hinausgeht, ist Überlauf und geht verloren.
- **Kapazität im Boden:** C = nFK [mm/dm] × Wurzeltiefe [dm].
- **Kapazität im Substrat:** C = leicht verfügbares Wasser [%] / 100 × Füllvolumen [L] / Fläche [m²].
- **Bedarf:** wenn die Entleerung D = C − S die Schwelle p × C erreicht. Empfohlene Menge = D.

### 1.2 Prüfung gegen die Quellen

| Aussage des Reviews | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Tägliche Bilanz mit Überlauf: Zufluss über die Kapazität hinaus geht am selben Tag verloren | FAO-56 Kap. 8, Gl. 85, 86, 88: „the total amount of water above field capacity is assumed to be lost the same day by deep percolation, following any ET for that day“; Grenzen „0 ≤ Dr,i ≤ TAW“ [Q1] (verifiziert) | Colorado State: „Dc = Dp + ETc − P − Irr (if Dc is negative, then set it to 0.0)“; „Any excess water in the root zone is assumed to be lost through SRO or DP.“ [Q8] (verifiziert) | Geisenheim: „Fallen Regenmengen die das Gesamtdefizit übersteigen, … wird das Gesamtdefizit gleich Null gesetzt“ [Q11] (verifiziert) | **3/3** |
| Kapazität = (Feldkapazität − Welkepunkt) × Wurzeltiefe | FAO-56 Gl. 82: „TAW = 1000(θFC − θWP) Zr“ [Q1] (verifiziert) | British Columbia Gl. 5.1: „SWS = RD × AWSC“ [Q5] (verifiziert) | Geisenheim Tab. 2: „durchwurzeltes Bodenvolumen × Wassergehalt bei 100 % nFK“ [Q11] (verifiziert) | **3/3** |
| Leicht verfügbarer Anteil = p × Kapazität; bewässert wird spätestens, wenn er aufgebraucht ist | FAO-56 Gl. 83 „RAW = p TAW“; „irrigations should be applied before or at the moment when the readily available soil water is depleted“ [Q1] (verifiziert) | Colorado State Gl. 3: „dMAD = (MAD / 100) × AWC × Drz“; „irrigation water should be applied when the soil water deficit (Dc) approaches dMAD“ [Q8] (verifiziert) | British Columbia: „The total amount of water stored in the soil is multiplied by the AC to obtain the maximum soil water deficit“ [Q5] (verifiziert) | **3/3** |
| Empfohlene Menge höchstens die Entleerung | FAO-56: „the net irrigation depth should be smaller than or equal to the root zone depletion (Ii ≤ Dr,i)“ [Q1] (verifiziert) | Colorado State: „The net irrigation amount equal to Dc can be applied to bring the soil water deficit to zero.“ [Q8] (verifiziert) | British Columbia: MSWD „is also the maximum amount that can be applied at one time before the risk of deep percolation occurs“ [Q5] (verifiziert) | **3/3** |
| Ohne Stresskoeffizient Ks entleert sich der Speicher unterhalb der Schwelle zu schnell (sichere Richtung) | FAO-56: unterhalb RAW sinkt ETc mit Ks (Gl. 84), Example 37: Ks fällt in zehn Tagen von 1,00 auf 0,62 [Q1] (verifiziert) | Colorado State Gl. 5, mit Verweis auf FAO-56 [Q8] (verifiziert, nicht unabhängig) | — | **1/3** (Folgerung aus der Formel, keine Zahl nötig) |

**Korrekturen und Ergänzungen zum Review:**

1. Das Review ließ die Gleichungsnummern offen. Sie lauten: Gl. 82 (TAW), 83 (RAW), 84 (Ks), 85 (Tagesbilanz), 86 (Grenzen), 87 (Anfangsentleerung), 88 (Tiefenversickerung) [Q1].
2. FAO-56 enthält in Kapitel 8 eine eigene Aussage zu kleinen Regenmengen, die das Review nicht nannte: „Daily precipitation in amounts less than about 0.2 ETo is normally entirely evaporated and can usually be ignored“ [Q1]. Das ist die einzige Regel zum wirksamen Tagesregen in FAO-56 Kapitel 8 (siehe Parameter 5).
3. FAO-56 rechnet mit „P − RO“ (Niederschlag minus Abfluss) und mit der Nettogabe „that infiltrates the soil“. Das Minimalmodell setzt Abfluss und Kapillaraufstieg auf null. Colorado State begründet dieselbe Vereinfachung: Die drei Größen „are difficult to estimate in the field“ [Q8].
4. FAO-56 Tab. 22, Fußnote 1: „The smaller values for Zr may be used for irrigation scheduling“ [Q1]. Das stützt die niedrige Wurzeltiefe als Planungswert (Parameter 1).

**Ergebnis:** Die Modellstruktur des Reviews ist mit 3/3 belegt und bleibt unverändert.

---

## 2. Die 15 Parameter

Reihenfolge wie in der Feature-Datei. Die vier vorab zu klärenden Parameter sind (7), (9), (4) und (10); sie stehen in der Entscheidungsvorlage (§7) zuerst.

### (1) Wurzelraumtiefe je Kultur und Phase

**Hintergrund.** Die Wurzeltiefe Zr bestimmt, wie viel Bodenwasser die Pflanze erreicht. Sie wächst mit der Pflanze. Im Garten benetzt eine Gießgabe nur die oberen Dezimeter. Das Datenmodell hat einen Wert je Art (`Species.effective_root_depth_cm`, `species.py:520`), keinen je Phase.

| Größe | Quelle 1 | Quelle 2 | Quelle 3 | weitere | Belegklasse |
|---|---|---|---|---|---|
| Wurzeltiefe ausgewachsener Gemüsekulturen | FAO-56 Tab. 22 („Maximum Root Depth“): Salat, Spinat, Sellerie, Knoblauch, Radies 0,3–0,5 m; Zwiebel 0,3–0,6; Brokkoli 0,4–0,6; Kohl 0,5–0,8; Möhre 0,5–1,0; Paprika 0,5–1,0; Tomate 0,7–1,5; Gurke 0,7–1,2; Erdbeere 0,2–0,3 [Q1] (verifiziert) | NRCS NEH 652 Tab. 3–4 („depths shown are for 80% of the roots“): Salat, Zwiebel, Spinat, Sellerie, Gurke, Paprika, Erdbeere 1–2 ft; Radies 1 ft; Kohl, Möhre, Brokkoli 2 ft; Tomate 3 ft [Q7] (verifiziert) | British Columbia Tab. 5.1: 0,45 m Kohl, Blumenkohl, Gurke, Salat, Zwiebel, Radies; 0,6 m Bohne, Möhre, Spinat, Erdbeere, Tomate, Kartoffel; 0,9 m Paprika, Kürbis, Aubergine [Q5] (verifiziert) | Utah State: „Shallow (6-12 inches)“ Radies, Brokkoli, Salat, Zwiebel, Paprika; „Moderate (18-24 inches)“ Kohl, Gurke, Möhre, Tomate, Bohne [Q9] (verifiziert) | **3/3** je Kultur als Spanne; die Quellen streuen bei derselben Kultur um den Faktor 2–3 (Tomate 0,45–1,5 m) |
| Tiefe in frühen Stadien | Geisenheim Tab. 8: fast alle Gemüsekulturen in Stadium 1 und 2 „0-30 cm“, Radies „0-15 cm“, spätere Stadien „0-60 cm“; Kopfsalat durchgehend 0–30 cm [Q11] (verifiziert; laut Fußnote aus N-Probennahmetiefen geschätzt) | Colorado State Tab. 2: „Vegetables“ Seedling 6–12 in, Vegetative 18 in, Mature 18–24 in [Q8] (verifiziert) | — | — | **2/3** für „Jungpflanze 15–30 cm“; 15 cm allein ist nur der untere Rand einer Quelle und der Radies-Wert der anderen |
| Tiefe, bis zu der im Garten gegossen werden soll | RHS: „Aim to moisten soil to a depth of 20-30cm (8-12in) – where the roots grow“ [Q23] (verifiziert) | Iowa State: „Apply enough water to moisten the soil 6 to 12 inches deep, where most vegetable roots are located.“ [Q24] (verifiziert) | Bayerische Gartenakademie: „Die meisten Wurzeln liegen in etwa 15 cm Tiefe.“ [Q15] (verifiziert) | Oregon State: „Most vegetables have an effective rooting depth of 12-20 inches“; 70 % des Wassers aus der oberen Hälfte [Q21] (verifiziert) | **3/3 (Spanne)** für 15–30 cm als Hauptwurzel- und Gießzone |

**Korrekturen zum Review.**

- Kohl hat in FAO-56 0,5–0,8 m, nicht „etwa 30–50 cm“ wie die Blattgemüse-Zeile des Reviews.
- Fruchtgemüse: FAO-56 nennt 0,5–1,5 m (Paprika 0,5–1,0; Tomate 0,7–1,5); die Spanne des Reviews (50–150 cm) trifft zu.
- Für Kräuter, Beeren, Obst und Rasen gab das Review „keine belastbare Angabe“. FAO-56 Tab. 22 nennt: Minze 0,4–0,8 m, Beerensträucher 0,6–1,2 m, Äpfel/Kirschen/Birnen 1,0–2,0 m, Rasen 0,5–1,0 m [Q1]; NRCS: Rasen 1–2 ft, Obstbäume 4–5 ft [Q7].
- Der 30-cm-Deckel galt im Review als „ohne Quelle“. Er ist jetzt belegt (dritte Tabellenzeile).
- Der Zusatz „`RootDepth`-Enum“ im Review ist irreführend: `RootDepth` (`enums.py:559`) gehört zur Pflanzenfamilie (`BotanicalFamily.typical_root_depth`, `botanical_family.py:35`), nicht zur Art.
- „Die Seeds haben ihn für nahezu alle 210 Arten“ stimmt für die Steckbriefe, nicht für die Seed-Dateien: `effective_root_depth_cm` kommt in den Seed-YAML 129-mal vor (Zählung per `grep` über `src/backend/app/migrations/seed_data/*.yaml`).

**Vorschlag.** Zr = min(Art-Wert, Fülltiefe des Beets, 30 cm). Der Deckel von 30 cm ist **3/3 (Spanne)**. Zulässiger Bereich einer späteren Konfiguration: 10–100 cm.

Die Jungphasen-Stufe „höchstens 15 cm“ des Reviews ist **2/3** und bleibt nach E-10 `null`. Ersatz ohne Zahl: In den Phasen `germination` und `seedling` verschiebt die Bilanz keine Erinnerung; dort gilt das Intervall. Dazu RHS: nach der Aussaat „water consistently to keep the surface moist“ [Q23].

**Sichere Richtung.** Niedrig. Eine zu hohe Wurzeltiefe überschätzt die Reserve, die Erinnerung kommt zu spät.

**Entscheidungsvorlage.**
- **Vorschlag:** Zr = min(Art-Wert, Fülltiefe, 30 cm); in Keim- und Sämlingsphase keine Verschiebung durch die Bilanz.
- **Alternative:** Art-Wert ungekürzt, nur durch die Fülltiefe begrenzt — Folge: bei Tomate 60 cm und mehr, die Bilanz rechnet mit Wasser in einer Tiefe, die im Garten nicht aufgefüllt wird; Erinnerungen im Hochsommer zu selten.
- **Alternative:** Jungphasen 15 cm — Folge: früherer Bedarf bei Jungpflanzen; der Wert ist nur 2/3 belegt und müsste vom Betreiber als eigene Festlegung getragen werden.

### (2) `water_holding_capacity_percent` und die Umrechnung in mm

**Hintergrund.** Die Container-Kapazität umfasst auch Wasser, das die Pflanze nicht oder nur schwer erreicht. Das Seed-Schema trennt beide Größen: `water_holding_capacity_percent` ist „Water-filled porosity at container capacity“ (`substrates.schema.yaml:145`), `easily_available_water_percent` „The fraction of held water a plant can actually extract“ (`:150`). Fast alle Seed-Substrate tragen den zweiten Wert (27 Nennungen bei 28 Einträgen in `substrates.yaml`, Zählung per `grep`); die Invariante „leicht verfügbar ≤ gehalten“ wird getestet (`test_substrate_invariants.py:171`).

| Größe | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Definition „easily available water“ (EAW) nach De Boodt und Verdonck 1972 | Altland, Owen, Fonteno 2010: „easily available water (EAW) being water occurring between 10 and 50 cm tension …, and water buffering capacity (WBC) being water occurring between 50 and 100 cm tension“ [Q26] (verifiziert) | Yafuso et al. 2019: „Water held in substrate below 50 cm of tension has been defined as easily plant available water, 50 to 100 cm describes water-buffering capacity“ [Q27] (verifiziert) | Basiri Jahromi et al. 2020: „easily available water (−1 to −5kPa) and water buffering capacity (−5 to −10 kPa)“ [Q28] (verifiziert) | **3/3** für die Definition; alle drei geben De Boodt und Verdonck wieder. Die Zusammenfassung des Originals bei der ISHS enthält die Definition nicht [Q33] (verifiziert) |
| Gehaltenes Wasser ist nicht vollständig verfügbar | Bilderback et al. 2005: Richtwerte „container capacity (CC) (45% to 65%), available water (AW) (25% to 35%)“; „Unavailable water determined as percent volume at 1500 kPa“ [Q29] (verifiziert) | Purdue HO-287-W: Wasser unter −1500 kPa „is assumed to be unavailable to plants“; Ultra-Mikroporen 22,1 und 27,8 % des Volumens in zwei Mischungen [Q31] (verifiziert) | Fields, Fonteno, Jackson 2014: Druckplatten-Werte seien „artificially high“; „the available water content may be only 5 to 10% less than the substrate container capacity“ [Q30] (verifiziert) | **widersprüchlich** in der Größe: nicht verfügbar 5–10 % oder 22–35 % des Volumens. Einig sind die Quellen, dass ein Abzug nötig ist |
| Prüfverfahren EN 13041 | SIS, Kurzbeschreibung von EN 13041:2011: „instrumental method for the routine determination of the physical properties, dry bulk density, water volume, air volume, shrinkage value and total pore space“; nicht anwendbar auf „preformed materials such as mineral wool slabs“ [Q32] (verifiziert) | — | — | **1/3**; die Saugspannung des Verfahrens steht nicht auf der Seite |
| Richtwert für EAW (z. B. 20–30 Vol.-%) | — | — | — | **nicht gefunden** |

**Korrekturen zum Review.**

- „WHC statt EAW: Kapazität etwa doppelt so hoch“ ist nur durch eine Quelle gedeckt (Bilderback: 45–65 % gegen 25–35 %). Fields et al. widersprechen der Größe. Die Aussage wird zu: „WHC ist höher als das verfügbare Wasser; um wie viel, ist in der Literatur strittig.“
- „EN-13041-Prüfverfahren“ als zweite Quelle der EAW-Definition ist nicht belegt: Die Norm bestimmt Wasser- und Luftvolumen; dass sie EAW definiert, zeigt die geöffnete Seite nicht.
- Zwei Größen heißen ähnlich und sind verschieden: „available water“ (bis 1500 kPa, Bilderback) und „easily available water“ (1–5 kPa, De Boodt und Verdonck). Die Schema-Beschreibung (`:150`) legt nicht fest, welche gemeint ist. Welche Definition die Seed-Werte tragen, gehört zu REQ-019 / #1175 und ist hier nicht geprüft.

**Vorschlag.** Speicherkapazität = `easily_available_water_percent` / 100 × Volumen [L] / Fläche [m²]; Volumen = Fläche × Fülltiefe, begrenzt auf Zr. Fehlt der Wert, ist die Substratstufe nicht nutzbar; `water_holding_capacity_percent` ist kein Ersatz. Die Regel braucht keine neue Zahl. Belegklasse der Regel: **3/3** für „nicht die Container-Kapazität verwenden“.

**Sichere Richtung.** Der kleinere Wert (EAW). Wer WHC einsetzt, überschätzt die Reserve.

**Entscheidungsvorlage.**
- **Vorschlag:** EAW × Volumen je Fläche; ohne EAW keine Substratstufe.
- **Alternative:** WHC verwenden — Folge: Reserve überschätzt, Erinnerung zu spät; nicht empfohlen.
- **Zu bestätigen:** REQ-019 muss festlegen, ob `easily_available_water_percent` die Definition 1–5 kPa trägt.

### (3) Pflanzenverfügbares Wasser je Bodenart (`soil_texture`)

**Hintergrund.** Die nutzbare Feldkapazität (nFK) ist die Differenz zwischen Feldkapazität und Welkepunkt. Sie hängt von Bodenart, Humus, Lagerungsdichte und Steingehalt ab. Das Enum `SoilTexture` (`enums.py:2316`) folgt den USDA-Klassen. Deutsche Tabellen nutzen andere Klassen (Bodenschätzung, Kartieranleitung); eine Zuordnung zu den USDA-Klassen ist nicht eins zu eins möglich.

**Quellen mit USDA-Klassen, in mm/dm (= Vol.-%).**

| `soil_texture` | FAO-56 Tab. 19 [Q1] | NRCS NEH 652 Tab. 2–1 [Q7] | Colorado State Tab. 1 [Q8] | British Columbia Tab. 5.8 [Q5] | Utah State [Q9] |
|---|---|---|---|---|---|
| sand | 5–11 | 1–3 („Sand“, „Coarse sand“); 5–7 („Fine sand“) | 5–7 („Coarse sands“); 7–8 („Fine sands“) | 8,3 | 2,1–6,2 |
| loamy_sand | 6–12 | 6–8 | 7–10 | 10,0 | 6,2–11,7 |
| sandy_loam | 11–15 | 11–13 | 10–13 | 12,5 | 10,8–15,0 |
| loam | 13–18 | 16–18 | 18–21 | 17,5 | 14,2–18,3 |
| silt_loam | 13–19 | 19–21 | 17–21 | 20,8 | 13,3–20,8 („Clay/Silt Loam“) |
| clay_loam | keine Zeile („Silt clay loam“ 13–18) | 19–21 | 13–17 | 20,0 | 13,3–20,8 („Clay/Silt Loam“) |
| clay | 12–20 | 14–16 | 11–13 | 20,0 | 12,5–18,3 |

Alle fünf verifiziert. University of Wisconsin [Q10] (verifiziert, zählt mit NRCS): Coarse Sand 2,1–6,2; Loamy Sand 9,2; Sandy Loam 10,0–11,7; Silt Loam 16,7–20,8; Clay 10,0–12,5.

**Deutsche Tabellen, andere Klassen.**

| Quelle | Werte in mm/dm |
|---|---|
| Geisenheim Tab. 1, „Wassergehalt bei 100% nFK“, Quelle ALB Bayern [Q11] (verifiziert) | Sand 9; schwach lehmiger Sand 13; stark lehmiger Sand 16; sandiger Lehm 19; schluffiger Lehm 22; toniger Lehm 17; lehmiger Ton 14; Ton 10 |
| HLNUG Kennwerttabelle, mittlere Packungsdichte, „in Anlehnung an AG Boden 1982 und 1994“ [Q12] (verifiziert) | Ss 9; Sl2 16; Sl3 17; Ls2 17; Lu 19; Ut3 24; Uu 25; Lt2 15; Tl 14; Tt 15 (lockerer gelagert höher: Ss 11, Lu 24, Tt 20) |
| LGB Rheinland-Pfalz Tab. 1, mittlere Packungsdichte, mit Bezug auf KA5 [Q13] (verifiziert) | Ss 11; Sl2 15; Sl3 16; Ls2 19; Lu 18; Ut3 24; Uu 27; Lt2 15; Tl 11; Tt 10 |
| Bayerische Gartenakademie [Q15] (verifiziert) | „Ein Sandboden kann je 10 cm Bodenschicht ca. 5 l/m² speichern, ein Lehmboden ca. 22 l/m² und ein Tonboden ca. 13 l/m².“ |

Humus erhöht die nFK: HLNUG nennt Zuschläge von 0,5–2 mm/dm (Humusstufe h2) bis 3,5–16 mm/dm (Humusstufe h5, je nach Bodenart) [Q12]. Steine senken sie (Parameter 11).

**Bewertung des Entwurfs aus dem Review.**

| `soil_texture` | Entwurf des Reviews | Liegt in den Spannen von | Vorschlag nach Gegenlesen | Belegklasse |
|---|---|---|---|---|
| sand | 7 | FAO-56, Colorado State (zwei Quellen; NRCS und Utah liegen darunter) | **5** — in FAO-56 (5–11), NRCS „Fine sand“ (5–7), Colorado State (5–8), Utah State (2,1–6,2); Gartenakademie nennt ca. 5 | **3/3 (Spanne)**; für Grobsand nennen NRCS und Utah noch weniger (1–3) |
| loamy_sand | 8 | FAO-56, NRCS, Colorado State, Utah State | **8** (unverändert) | **3/3 (Spanne)** |
| sandy_loam | 12 | FAO-56, NRCS, Colorado State, Utah State | **12** (unverändert) | **3/3 (Spanne)** |
| loam | 14 | nur FAO-56 (Utah beginnt bei 14,2) | **16** — in FAO-56 (13–18), NRCS (16–18), Utah State (14,2–18,3) | **3/3 (Spanne)**; der Entwurfswert 14 ist 1/3 |
| silt_loam | 15 | FAO-56, Utah State | **17** — in FAO-56 (13–19), Colorado State (17–21), Utah State (13,3–20,8) | **3/3 (Spanne)**; der Entwurfswert 15 ist 2/3 |
| clay_loam | 13 | Colorado State (13–17) | **kein Wert** — NRCS 19–21 und British Columbia 20 stehen gegen Colorado State 13–17; FAO-56 hat keine Zeile | **widersprüchlich**, bleibt `null` nach E-10 |
| clay | 13 | FAO-56, Colorado State, Utah State | **13** (unverändert); Gartenakademie nennt ca. 13 | **3/3 (Spanne)** |
| unknown | – | – | kein Wert, nächste Stufe | – |

Bei 30 cm Wurzeltiefe ergeben die Vorschlagswerte C = 15 mm (sand) bis 51 mm (silt_loam).

**Korrekturen zum Review.** Die erinnerten FAO-56-Spannen stimmen (Tab. 19 gelesen). Geändert sind drei Vorschlagswerte: sand 7 → 5, loam 14 → 16, silt_loam 15 → 17; clay_loam 13 → `null`. Die Werte für loam und silt_loam steigen, weil der niedrigere Entwurfswert nur in einer oder zwei Spannen liegt; die sichere Richtung bleibt gewahrt, weil beide neuen Werte am unteren Rand aller deutschen Tabellen liegen (Lehm 17–22, Schluff 22–27).

**Sichere Richtung.** Niedrig.

**Entscheidungsvorlage.**
- **Vorschlag:** Tabelle sand 5, loamy_sand 8, sandy_loam 12, loam 16, silt_loam 17, clay 13 mm/dm; clay_loam und unknown ohne Wert. Zu bestätigen ist, dass „Wert in drei Spannen“ auch hier als 3/3 gilt (wie am 2026-11-22 für die Bodengefahren entschieden).
- **Alternative:** je Klasse das Minimum über alle Quellen (sand 1, loamy_sand 6, sandy_loam 10, loam 13, silt_loam 13, clay 10) — Folge: noch frühere Erinnerungen; auf Sand eine Kapazität von 3 mm bei 30 cm, die Bilanz meldet dort praktisch täglich Bedarf.
- **Alternative:** Stufe bleibt leer, bis der Betreiber die Tabelle bestätigt (heutiger Stand, R-008) — Folge: Beete ohne Substrat rechnen nur mit dem Standort-Standardwert.
- **Für clay_loam:** `null` und Rückfall auf den Standardwert — oder 15 mm/dm (Colorado State Mittelwert, Utah State, HLNUG und LGB für Lt2) mit dem Vorbehalt, dass zwei der vier Stützen deutsche Klassen sind.

### (4) Bedarfsschwelle (Vorab-Parameter)

**Hintergrund.** Ab einer Entleerung von p × C nimmt die Pflanze Wasser nicht mehr schnell genug auf. Das Datenmodell hat keine artabhängige Fraktion.

| Quelle | Aussage | Prüftiefe |
|---|---|---|
| FAO-56 Tab. 22 [Q1] | p bei ETc ≈ 5 mm/Tag: Sellerie, Spinat, Erdbeere 0,20; Salat, Zwiebel, Knoblauch, Radies, Paprika 0,30; Möhre, Kartoffel, Erbse 0,35; Tomate 0,40; Kohl, Brokkoli, Blumenkohl, Bohne, Aubergine 0,45; Gurke, Zucchini, Rote Bete 0,50. Text: „A value of 0.50 for p is commonly used for many crops.“ Anpassung „p = pTable 22 + 0.04 (5 − ETc)“, begrenzt auf 0,1–0,8; für Tonböden 5–10 % weniger, für Sandböden 5–10 % mehr | verifiziert |
| Geisenheim [Q11] | „Die Bewässerung für Gemüsekulturen setzt bei Bodenfeuchten von 60% nutzbarer Feldkapazität (nFK) ein“ — entspricht p = 0,40 | verifiziert |
| NRCS NEH 652 Tab. 3–3 [Q7] | MAD in % der AWC, lehmige Böden, vier Stadien: „Vegetables 1 to 2 ft root depth 35 30 30 35“; „3 to 4 ft root depth 35 40 40 40“; „Lettuce 40 50 40 20“; „Onions 40 30 30 30“; „Spinach 25 25 25 25“ | verifiziert |
| British Columbia Tab. 5.2 [Q5] | „Availability Coefficients“: Erbse 0,35; Kartoffel 0,35; Tomate 0,40; „Others 0.50“ | verifiziert |
| Texas A&M Tab. 2 [Q20] | „Vegetable crops 25 to 50“ % zulässige Entleerung (nach Jensen 1980) | verifiziert |
| Oregon State [Q21] | „For most crops, MAD is between 40-60% of the available water capacity.“ „Onions can only lose 30% of the AWC.“ | verifiziert |
| LWK Niedersachsen [Q17] | Ackerbau: 80–50 % nFK „optimales Wasserangebot“, 50–30 % nFK „beregnen“ | verifiziert |

**Auswertung.** p = 0,40 liegt in der Gemüse-Spanne von FAO-56 (0,20–0,50), ist der Geisenheimer Wert, liegt in der Spanne von Texas A&M (25–50 %) und zwischen den Werten aus British Columbia (0,35–0,50) und NRCS (30–40). Belegklasse **3/3 (Spanne)**. Für flach wurzelnde und empfindliche Kulturen ist 0,30 ebenso belegt (FAO-56 Salat/Zwiebel/Paprika; NRCS Gemüse mit 1–2 ft Wurzeltiefe 30–35; Oregon State Zwiebel): **3/3 (Spanne)**.

**Korrekturen zum Review.** Die erinnerten Einzelwerte (Tomate 0,40, Salat 0,30, Zwiebel 0,30, Möhre 0,35, Gurke 0,50, Kohl 0,45) stimmen. Die Gesamtspanne in FAO-56 reicht bei Gemüse von 0,20 bis 0,50, nicht „0,2–0,6“; 0,6 und mehr gelten für Feldkulturen. Die Untergrenze „nicht unter 0,3“ hat keine Quelle: FAO-56 nennt 0,20 für Sellerie, Spinat und Erdbeere, NRCS 25 % für Spinat.

**Vorschlag.** Bedarf, wenn D ≥ 0,40 × C. Einheitlich für alle Kulturen. **3/3 (Spanne).** Für Substrate gilt dieselbe Schwelle auf C = EAW; das ist strenger als im Boden, weil EAW bereits der leicht verfügbare Teil ist.

**Rechenprobe.** loam 16 mm/dm × 3 dm = 48 mm; Schwelle 19 mm. Bei ETc 4 mm/Tag entsteht Bedarf nach etwa fünf Tagen, die Empfehlung beträgt rund 19 L/m². Dazu passen: Gartenakademie „Minimum 10 Liter je m² und Gießgang“ [Q15]; Iowa State und Connecticut „1 inch of water per week“ [Q24, Q25]; Geisenheim, Einzelgabe bei 0–30 cm: 8 mm (Sand) bis 20 mm (schluffiger Lehm) [Q11].

**Sichere Richtung.** Niedrig (früherer Bedarf).

**Entscheidungsvorlage.**
- **Vorschlag:** p = 0,40.
- **Alternative:** p = 0,30 — Folge: für Salat, Zwiebel, Spinat, Paprika näher an den Quellen; etwa ein Viertel kleinere, dafür häufigere Gaben; bei Tomate und Kohl früher als nötig.
- **Alternative:** jedes Defizit ist Bedarf (p = 0) — Folge: tägliche kleine Gaben; widerspricht den Gießempfehlungen unter Parameter 8.
- **Nicht vorgeschlagen:** die ETc- und Bodenart-Korrektur aus FAO-56; sie ist nur dort belegt (1/3).

### (5) Effektiver Niederschlag im Speichermodell

**Hintergrund.** Der Code kürzt Regen heute so: über 5 mm zählen 80 % der gesamten Menge, bis 5 mm zählt alles (`evapotranspiration_calculator.py:262-265`, Konstanten `:40-41`, Kommentar `:38-39` „FAO-56 rule-of-thumb“). REQ-037 nennt dieselbe Regel „grobe FAO-Faustregel“ (`:303-304`).

**Woher die Regel stammt.**

| Fundstelle | Aussage | Prüftiefe |
|---|---|---|
| FAO-56 Kap. 8 [Q1] | Einzige Aussage zum Tagesregen: „Daily precipitation in amounts less than about 0.2 ETo is normally entirely evaporated and can usually be ignored“. Keine 5-mm-Schwelle, kein 80-%-Faktor. | verifiziert (Kapitel 8 vollständig gelesen) |
| British Columbia, Guide Kap. 3, Factsheet 577.100-3, Farmwest [Q5] | „if rainfall is less than 5 mm, the effective precipitation (EP) is zero. If rainfall is over 5 mm, only 75% of it will be considered as EP“; „EP = (RAIN − 5) × 0.75“. Für kühle, nasse Perioden soll der volle Regen gelten. | verifiziert |
| FAO-Paper 25, Kap. II §3.5 [Q2] | Länderregeln, Reis: Burma „Rainfall below 0.5 in is considered as ineffective. Above 0.5 in, 80 percent of the amount in excess is considered as effective.“; Vietnam „Daily rainfall below 5 mm and above 50 mm is disregarded.“; Indien „rainfall less than 0.25 in (6.25 mm) on any day is considered as ineffective“. Zu einer ähnlichen Regel: „This approach would appear to be rather arbitrary.“ | verifiziert |
| FAO-Schulungsheft 3, Kap. 3 [Q3] | Nur Monatswerte (Tab. 6: 60 mm/Monat → 26 mm wirksam). | verifiziert |

**Befund.** Die Regel im Code ist in keiner geöffneten Quelle belegt (**nicht gefunden**). Alle gefundenen Tagesregeln zählen Regen **unter** der Schwelle mit null und oberhalb nur den **Überschuss** über die Schwelle. Der Code macht es umgekehrt. Die Zuschreibung zu FAO-56 ist falsch. Die Unstetigkeit, die das Review zeigt, ist nachgerechnet: 5,0 mm ergeben 5,0 mm wirksam, 5,1 mm ergeben 4,08 mm.

**Regen im Speichermodell.**

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| In der Tagesbilanz zählt der gemessene Regen voll; den Verlust regelt die Kapazität | Geisenheim: „Dem Wasserverbrauch werden Regen und Bewässerungsmengen gegenübergestellt.“ [Q11] (verifiziert) | LWK Niedersachsen: „Tagesbilanz berechnen = GrasverdunstungFAO56 x kc-Faktor – Regen“ [Q17] (verifiziert) | Colorado State: „P is the gross precipitation for the current day“ [Q8] (verifiziert) | **3/3** |
| Die Tagesbilanz ist selbst ein Verfahren zur Bestimmung des wirksamen Regens | FAO-Paper 25 §2.2: „Any amount in excess of this capacity is a surplus and will be a deep percolation loss or run-off.“ [Q2] (verifiziert) | FAO-56 Gl. 88 [Q1] (verifiziert) | — | 2/3 (FAO zählt als eine Quelle: **1/3**) |

**Vorschlag.** Im Speichermodell entfällt die 5-mm-/80-%-Regel; gemessener und vorhergesagter Regen gehen ungekürzt ein, der Überlauf begrenzt die Gutschrift. **3/3.** Pro Standort und Tag zählt eine Regenquelle: der Messwert, sonst die Prognose; ein `rainfall`-Pflegeereignis mit Menge wird nicht dazugezählt (Konstruktion, keine Zahl).

Die Regel „Regen unter 0,2 × ET₀ ignorieren“ wird nicht übernommen: **1/3** (nur FAO-56), und British Columbia setzt die Schwelle fünfmal so hoch.

**Sichere Richtung.** Weniger gutschreiben. Volle Gutschrift mit Überlauf ist auf flachen Beeten unkritisch; auf Hanglagen überschätzt sie den Zufluss (Abfluss wird nicht modelliert).

**Entscheidungsvorlage.**
- **Vorschlag:** Regel entfällt im Speicher; sie bleibt nur im Rückfall (Parameter 13), dort ohne die Zuschreibung „FAO“.
- **Alternative:** im Speicher die Form aus British Columbia, EP = (Regen − 5) × 0,75 — Folge: stetig und vorsichtiger; aber 1/3 belegt, für ein trockenes Klima formuliert, und Regen wird neben dem Überlauf ein zweites Mal gekürzt.
- **Folgearbeit außerhalb von F-29:** Kommentar im Code (`:38-39`, Docstring `:250-251`) und REQ-037 `:303`, `:430` nennen FAO als Herkunft; das ist zu berichtigen.

### (6) Anfangsfüllstand und Verhalten nach Datenlücken

**Hintergrund.** Ohne Startwert ist die Bilanz unbestimmt.

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Voller Speicher darf nur nach einem füllenden Ereignis angenommen werden; sonst ist der Start zu schätzen oder zu messen | FAO-56: „Following heavy rain or irrigation, the user can assume that the root zone is near field capacity“; sonst aus gemessener Bodenfeuchte (Gl. 87) [Q1] (verifiziert) | Geisenheim: „Die Bodenfeuchte zum Kalkulationsbeginn muss bekannt sein und als Ausgangsdefizit in die Berechnung einfließen. … Größere Defizite sind durch Vorabbewässerung auszugleichen.“ [Q11] (verifiziert) | British Columbia Factsheet: Start mit vollem Speicher nach „irrigation or rainfall that fills the entire root zone“ [Q5] (verifiziert) | **3/3** |
| Voller Speicher im Frühjahr wegen der Winterniederschläge | Colorado State, Rechenbeispiel: Annahme „reasonable because actual precipitation from January 15 to May 30, 2008, was 2.56 inches, which was greater than AWC for the top foot of soil“ [Q8] (verifiziert) | Geisenheim rechnet das Frühjahrsdefizit aus, statt es zu unterstellen [Q11] (verifiziert) | — | **1/3** für eine Kalenderregel |
| Lückenlänge (2 Tage fortschreiben, ab 3 Tagen unbekannt) | — | — | — | **nicht gefunden**; Geisenheim setzt nach einem füllenden Regen „die Kalkulation zwei bis drei Tage“ aus, das meint die Sickerzeit, nicht eine Datenlücke [Q11] |

**Korrektur zum Review.** Der Vorschlag „S₀ = C im Frühjahr (März–Mai), sonst S₀ = Schwelle“ stützt sich auf eine Kalenderregel, die keine Quelle so nennt (1/3). Die Quellen binden den vollen Speicher an ein Ereignis, nicht an eine Jahreszeit.

**Vorschlag.**
- Start eines Runs: S₀ = C − p × C („genau an der Schwelle“). Die erste Gießgabe mit Menge oder ein füllender Regen hebt den Stand.
- S = C wird nur durch ein füllendes Ereignis gesetzt: Zufluss, der die Entleerung übersteigt.
- Datenlücke: Tage ohne Wetterdaten rechnen mit Regen = 0 und der zuletzt bekannten ETc; die Herkunft „Lücke“ steht am Tag. Wie viele Tage fortgeschrieben wird, ist eine technische Festlegung ohne agronomische Quelle.

Belegklasse: Regel „voll nur nach füllendem Ereignis“ **3/3**; Startwert an der Schwelle ist Konstruktion in sicherer Richtung.

**Sichere Richtung.** Niedriger Startstand.

**Entscheidungsvorlage.**
- **Vorschlag:** Start an der Schwelle; voll nur nach füllendem Ereignis.
- **Alternative:** Start mit S₀ = C in den Monaten März bis Mai (Vorschlag des Reviews) — Folge: keine erste Erinnerung im Frühjahr; in einem trockenen Frühjahr überschätzt.
- **Alternative:** immer S₀ = C — Folge: Sommerpflanzungen ohne Angießen werden überschätzt.
- **Zu bestätigen:** nach wie vielen Tagen ohne Daten die Bilanz als unbekannt gilt (Review: ab dem dritten Tag; keine Quelle).

### (7) Zufluss durch Gießen, mit und ohne Menge (Vorab-Parameter)

**Hintergrund.** Gießen ist der einzige steuerbare Zufluss. acceptance-6 sagt heute „nur gemessene Niederschlagsmengen gehen in die Bilanz ein“ und nennt das Gießen nicht (`soil-water-balance.md:68`). Ohne diesen Zufluss wächst die Entleerung trotz Gießen.

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Bewässerung ist Zufluss der Bilanz | FAO-56 Gl. 85: „Ii net irrigation depth on day i that infiltrates the soil“ [Q1] (verifiziert) | Geisenheim: „Die tatsächlich ausgebrachte Bewässerungsmenge wird vom Gesamtdefizit abgezogen“ [Q11] (verifiziert) | Colorado State Gl. 2: „Irr is the net irrigation amount infiltrated into the soil“ [Q8] (verifiziert) | **3/3** |

**Wirkungsgrade.**

| Verfahren | FAO-Schulungsheft 4 [Q4] | British Columbia Tab. 6.1 [Q5] | Alberta Agdex 563-1, Spannen nach Howell 2003 [Q18] | Nebraska EC732 Tab. 2 [Q19] | Texas A&M Tab. 4 [Q20] | Belegklasse |
|---|---|---|---|---|---|---|
| Tropf | 90 % | 85–95, typisch 92 | 70–95, Design 88 | „Surface drip 85 - 95“ | 80–95, „typically designed at 90 percent“ | **3/3 (Spanne)** für 0,88 |
| Sprinkler, von Hand versetzt | 75 % | 60–75, typisch 72 | 60–85, Design 67 | „Hand move 65 - 85“ | 55–75 | **3/3 (Spanne)** für 0,70; 0,75 liegt am oberen Rand zweier Spannen |
| Gießen von Hand | — | — | — | — | — | **1/3**: UC Master Gardeners: „sprinkler systems and hand watering are 50 to 70 percent efficient“ [Q22] (verifiziert; ohne Messquelle) |

Alle fünf Tabellen verifiziert.

**Korrekturen zum Review und zu REQ-053.**

- „Hand 0,8“ ist nicht belegt. Die einzige gefundene Angabe liegt bei 0,5–0,7.
- „Howell 2003, Tropf 70–95 %, Designwert 88 %“ (REQ-053 `:1038`): Die Spanne nennt Alberta mit Howell als Quelle; den Designwert 88 setzt Alberta selbst („The efficiency values included in the ‚Design‘ column … are used for the irrigation management products“) [Q18].
- Der Entscheidungsstand in REQ-053 §32.6 Nr. 4 (`:2339`) und der Code (`irrigation_zone_demand_calculator.py:37-40`) führen nur Tropf 0,88; alle anderen Typen sind `null`. Das Review zitierte den älteren Wortlaut aus GP-FR-114 (`:1038`).

**Vorschlag.**
- **Mit Menge:** Gutschrift = Menge [L] / bewässerte Fläche [m²] × `application_efficiency` der Zone, wenn dort ein Wert steht (heute: Tropf 0,88 oder vom Nutzer gesetzt). Steht keiner, wird die Menge ungekürzt gutgeschrieben und der Tag trägt die Kennzeichnung „Wirkungsgrad unbekannt“. Die Gutschrift endet bei C.
- **Ohne Menge:** keine Gutschrift, symmetrisch zum `rainfall`-Ereignis ohne Menge. Die Erinnerung bietet die empfohlene Menge als vorbelegten Wert an.
- **Verteilte Gießrunden** (`allocation = by_area`): gutschreiben, aber nie als gemessen kennzeichnen (GP-FR-117).

Belegklasse: Gießen als Zufluss **3/3**; Tropf 0,88 **3/3 (Spanne)**; ein eingebauter Wirkungsgrad für Handgießen bleibt `null` nach E-10.

**Sichere Richtung.** Weniger gutschreiben. Die ungekürzte Gutschrift ohne Wirkungsgrad geht in die unsichere Richtung; der Deckel C begrenzt den Fehler auf eine Gabe.

**Entscheidungsvorlage.**
- **Vorschlag:** wie oben.
- **Alternative zur Menge ohne Wirkungsgrad:** nur gutschreiben, wenn die Zone einen Wirkungsgrad trägt — Folge: Handgießen füllt den Speicher erst, nachdem jemand einen Wert gesetzt hat; bis dahin Rückfall auf die Tagesbilanz.
- **Alternative zum Gießen ohne Menge:** die zuletzt empfohlene Menge gutschreiben — Folge: Der Gießkreislauf schließt sich mit einem Tipp; gutgeschrieben wird, was nicht belegt ist, und eine kleinere Gabe bleibt unbemerkt.
- **Alternative:** Gießen zählt nicht — Folge: Die Entleerung wächst trotz Gießen, die Bilanz ist nach der ersten Gabe falsch.

### (8) Untergrenze und Deckel der Empfehlung

**Hintergrund.** Eine Empfehlung soll durchdringen und nie mehr nennen, als der Speicher aufnimmt.

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Empfehlung höchstens die Entleerung | FAO-56 „Ii ≤ Dr,i“ [Q1] | Colorado State [Q8] | British Columbia [Q5] (alle verifiziert, Wortlaut in §1.2) | **3/3** |
| Seltener und durchdringend statt oft und wenig | Bayerische Gartenakademie: „Richtig gießen heißt also seltener gießen und dabei mehr Wasser auszubringen.“ [Q15] (verifiziert) | RHS: „water less often but more thoroughly“ [Q23] (verifiziert) | Iowa State: „one thorough watering per week is preferable to frequent light watering“ [Q24] (verifiziert) | **3/3** |
| Kleinste sinnvolle Gabe | Gartenakademie: „Minimum 10 Liter je m² und Gießgang“ (Obst); „Ein Liter Wasser … dringt etwa 1 cm tief in den Boden ein.“ [Q15] (verifiziert) | Geisenheim Tab. 1: kleinste Einzelgabe 8 mm (Sand, 0–30 cm) [Q11] (verifiziert) | British Columbia: Regen unter 5 mm in Trockenzeiten nicht wirksam [Q5] (verifiziert; gilt für Regen) | **2/3** für „rund 8–10 mm“; 5 mm als Untergrenze einer Gießgabe: **1/3** |
| Größte Einzelgabe | IGZ (Feller): „Ausbringung von maximal 20 bis 25 mm pro Einzelgabe“ [Q16] (verifiziert) | Gartenakademie: Böden können im Sommer nicht „mehr als 20 bis 25 Liter je m² aufnehmen“ [Q15] (verifiziert) | Geisenheim: „hohe Gaben (z. B. >30 mm) auf mehrere Tage zu verteilen“ [Q11] (verifiziert) | **2/3** für 20–25 mm, mit Geisenheim (30 mm) als abweichender dritter Angabe |

**Korrektur zum Review.** Die Untergrenze „mindestens 5 mm“ ist als Gießuntergrenze nur 1/3 belegt; die Quellen für Gießgaben nennen 8–10 mm. Sie wird nicht als Konstante gebraucht: Mit p = 0,40 und Zr = 30 cm ist die kleinste Empfehlung 6 mm (sand), sonst 10–20 mm.

**Vorschlag.** Empfehlung = D, höchstens C. Keine eigene Untergrenze; sie folgt aus p × C. Der heutige Deckel „Tagesbedarf höchstens WHC“ (`evapotranspiration_calculator.py:269-271`, REQ-037 Szenario 4 `:483-486`) entfällt. Belegklasse **3/3**. Ein Hinweis „in zwei Gaben aufteilen“ oberhalb von 25 mm bleibt nach E-10 ohne Zahl (2/3).

**Sichere Richtung.** D ≤ C; ein höherer Deckel führt zu Versickerung und Auswaschung.

**Entscheidungsvorlage.**
- **Vorschlag:** Empfehlung = D ≤ C, ohne Untergrenze.
- **Alternative:** Untergrenze 10 mm — Folge: auf Sand entsteht erst bei 10 mm Entleerung eine Empfehlung, das sind zwei Drittel der Kapazität; nur 2/3 belegt.

### (9) Regenexposition je Standorttyp und Ort (Vorab-Parameter)

**Hintergrund.** Der Regenmesser misst am Standort, nicht am Beet. Der Task rechnet heute alle Standorte der Typen `outdoor`, `greenhouse` und `balcony` (`WEATHER_RELEVANT_SITE_TYPES`, `enums.py:482`; `irrigation_tasks.py:63`) und zieht dort Niederschlag ab (`:146`). Ein Feld für die Regenexposition gibt es nicht.

| Aussage | Quelle | Prüftiefe |
|---|---|---|
| Überdachte Plätze bekommen keinen Regen und sind unabhängig vom Wetter zu gießen | Bayerische Gartenakademie: „Werden Obstgehölze in Kübeln regengeschützt gehalten, zum Beispiel auf dem Balkon oder auf der überdachter Terrasse, sollten diese im Sommer wöchentlich …, andernfalls zweimal durchdringend gegossen werden.“ [Q15] | verifiziert |
| Verdunstung im Gewächshaus gegenüber außen | Fernandes, Corá, Araújo 2003: „Usually, evapotranspiration inside a greenhouse is around 60 to 80% of that verified outside“ [Q34]; Orgaz et al. 2005: „30–40% lower than outdoors“ [Q35]; Jaafar und Ahmad 2019: „greenhouse EToPM was found equal to 60% of outdoor EToPM“ [Q36] | alle verifiziert (Q36 nur Zusammenfassung) |

Dass Regen ein Beet unter Glas, Folie oder Dach nicht erreicht, ist eine Tatsache und braucht keine Zahl. Die Verdunstung im Gewächshaus liegt bei 60–80 % des Außenwerts: **3/3 (Spanne)**, gemessen in Folien- und Kunststoffgewächshäusern in Brasilien, Südspanien und im Libanon. Für ein mitteleuropäisches Kleingewächshaus ist der Wert nicht geprüft.

**Korrektur zum Review.** Annahme 6 des Reviews („Gewächshaus-ET₀ aus Außenwetter überschätzt den Verbrauch … nicht belegt“) ist jetzt belegt. Die Richtung ist sicher gegen Trockenstress und unsicher gegen Staunässe.

**Vorschlag.** Regenanteil je Ort, zweiwertig:

| Ort | Regenanteil |
|---|---|
| Freiland (`outdoor`): Beet, Hochbeet, Kübel | 1 |
| Standorttyp `greenhouse`; Ortstypen `greenhouse_bed`, `cold_frame`, `tent` | 0 |
| Standorttyp `balcony` | 0, bis der Ort ausdrücklich als regenexponiert markiert ist |

Dazu ein überschreibbares Feld je Ort nach dem Muster von `Location.frost_exposed` (`site.py:654`; dieses Feld wird gerade durch `microclimate.frost_risk` abgelöst, `site.py:443-445`, ein Regen-Pendant gehört deshalb in `SiteConditions`). Die Ableitung allein aus `location_type_key` ist nicht tragfähig, weil die Typen nutzererweiterbar sind (REQ-053 `:321`). Ein Teilfaktor für „teilüberdacht“ und ein ET-Faktor für das Gewächshaus werden nicht eingebaut.

Belegklasse: Konstruktion; keine Zahl.

**Sichere Richtung.** Kein Regen gutschreiben.

**Entscheidungsvorlage.**
- **Vorschlag:** wie oben, mit Feld je Ort.
- **Alternative:** nur nach Standorttyp — Folge: ein Gewächshausbeet oder Frühbeet auf einem Freiland-Standort bekommt Regen gutgeschrieben; ein offener Balkon bekommt keinen.
- **Alternative:** so lassen — Folge: mit F-30 verschiebt gemessener Regen Erinnerungen für Pflanzen unter Glas und Dach.
- **Nicht vorgeschlagen:** ET₀ im Gewächshaus mit 0,6–0,8 multiplizieren. Der Wert ist 3/3 für andere Klimate und Bauarten; ohne ihn rechnet die Bilanz zu früh, nicht zu spät.

### (10) Ausschluss erdloser Systeme und Substrate (Vorab-Parameter)

**Hintergrund.** In rezirkulierenden Systemen liegt das Wasser im Tank. Inerte Substrate haben einen kleinen Puffer und werden nach Strahlung, Zeit und Drainanteil bewässert.

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Substratkultur wird in vielen kleinen Gaben je Tag nach Strahlungssumme und Drain gesteuert | Wageningen UR: „give the smallest possible quantity with the highest possible frequency (at least more than 10x per day)“; „irrigated according to the radiation sum“ [Q39] (verifiziert) | British Columbia Trickle Manual Kap. 9: „Irrigate a minimum of 6 to 7 times per day (use overdrain as a guide)“; „Daily requirement: ml/day = 3 x solar radiation (joules/cm2)“ [Q6] (verifiziert) | UF/IFAS HS1274: Perlit brauche „a dozen or more shorter events daily“ (Suchauszug, nicht gezählt) | **2/3** |

Keine Zahl geht in den Code; die Liste ist eine Zuordnung von Enum-Werten.

**Vorschlag.** Kein Speicher, wenn eines gilt:

- `Location.irrigation_system` ∈ {`hydro`, `nft`, `ebb_flow`, `mist`} (`enums.py:498-504`, Feld `site.py:645`);
- `soil_profile.growing_medium_kind` = `mineral_substrate` (`enums.py:2306`; REQ-053 `:1114` ordnet es REQ-004-A zu);
- `SubstrateType` ∈ {`clay_pebbles`, `rockwool_slab`, `rockwool_plug`, `perlite`, `vermiculite`, `pon_mineral`, `hydro_solution`, `none`} (`enums.py:507-521`);
- `orchid_bark` und `sphagnum` (Zimmerpflanzen-Substrate, kein Freiland-Modell).

Eingeschlossen bleiben `native_soil`, `raised_bed_mix` und `potting_mix` mit `SubstrateType` `soil`, `living_soil`, `peat` und `coco`, jeweils nur mit EAW-Wert.

**Sichere Richtung.** Ausschließen. Ein fälschlich ausgeschlossener Boden fällt auf die Tagesbilanz zurück.

**Entscheidungsvorlage.**
- **Vorschlag:** Ausschlussliste wie oben, in REQ-037 §3.3 dokumentiert.
- **Alternative:** mitrechnen — Folge: Die Bilanz führt einen Bodenspeicher für Standorte, an denen es keinen gibt; Erinnerungen ohne Bezug zur Anlage.
- **Zu bestätigen:** ob `coco` eingeschlossen bleibt (Fertigation mit mehreren Gaben am Tag ist dort üblich; das Review stuft es als Grenzfall ein, eine Quelle dazu wurde nicht gesucht).

### (11) Drainage, Wasserregime, Staunässe, Steingehalt, Mulch

**Hintergrund.** Diese Größen wirken auf Kapazität, Zufluss oder Verdunstung.

**Steingehalt.**

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Steine senken die nFK etwa im Verhältnis ihres Volumenanteils | NRCS Tab. 2–2: Loam 16–18 mm/dm ohne Steine, 13–14 bei 20 Vol.-%, 10–11 bei 40 Vol.-% [Q7] (verifiziert) | LGB Rheinland-Pfalz Tab. 4: Korrekturfaktor 0,94 (2 bis < 10 Vol.-%), 0,83 (10 bis < 25), 0,63 (25 bis < 50), 0,38 (50 bis < 75) [Q13] (verifiziert) | GD NRW: nFK „korrigiert durch volumenprozentuale Abschläge für den Grobbodenanteil“ [Q14] (verifiziert) | **3/3** für das Prinzip |
| Zuordnung der Stufen `few` / `many` zu Vol.-% | — | — | — | **nicht gefunden**; die Kartieranleitung hat sechs Stufen [Q13], das Enum drei (`enums.py:2381`) |

**Mulch.**

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegklasse |
|---|---|---|---|---|
| Organischer Mulch senkt die **Bodenverdunstung** | FAO-56 Kap. 10: „reduce the amount of soil water evaporation by about 5% for each 10% of soil surface that is effectively covered by an organic mulch“ (volle Bedeckung: etwa 50 %) [Q1] (verifiziert) | UC Cooperative Extension nach Chalker-Scott: „One study documented a 35% reduction in evaporation when a straw mulch was applied.“ [Q37] (verifiziert, Auszug aus zweiter Hand) | Nebraska G2000: Bodenverdunstung bis 30 % der ET, unter voller Rückstandsdecke 15 % [Q38] (verifiziert; Ackerbau) | **3/3** für „35–50 % weniger Bodenverdunstung“ |
| Wirkung auf die **gesamte** Kulturverdunstung ETc | FAO-56: Kc mid und Kc end ändern sich unter organischem Mulch wenig („may not be very large“); unter Folienmulch Kc „decrease by an average of 10-30%“, Beispielrechnung mit 0,85 [Q1] (verifiziert) | Nebraska G2000: von 30 % auf 15 % der ET, also rund 15 Prozentpunkte [Q38] (verifiziert) | — | **2/3** für „höchstens rund 15 % weniger ETc“ |

**Korrektur zum Review und zu REQ-053.** Das Review hat recht: `mulch_factor` 0,5–1,0 „Verdunstungsmodifikator“ (REQ-053 `:1071`) passt als Faktor auf die Bodenverdunstung, nicht auf ETc. Auf ETc angewandt, kürzt 0,5 den Bedarf um die Hälfte; belegt sind höchstens rund 15 %. Der Eintrag im Wissensbestand (`giess-strategien-substrat.yaml:183`, „Reduziert Verdunstung um 50-70%“) nennt keine Quelle und meint die Bodenverdunstung; FAO-56 nennt 50–80 % für **Folien**mulch.

**Drainage, Wasserregime, Zustand.** Keine Zahlen gesucht und keine gefunden. FAO-56 setzt den Kapillaraufstieg auf null, „when the water table is more than about 1 m below the bottom of the root zone“ [Q1].

**Vorschlag.** Nichts davon geht in Fassung 1 in die Rechnung ein. `drainage = poor` mit staunässeempfindlicher Art und `site_water_regime` ∈ {`moist`, `wet`} erzeugen nur einen Hinweis. Der Steingehalt wird nicht gerechnet, solange nur drei Stufen ohne Volumenanteil vorliegen. Mulch wird nicht gerechnet.

**Sichere Richtung.** Mulch ignorieren (Bedarf leicht überschätzt). Steine ignorieren ist die **unsichere** Richtung: Auf einem steinigen Beet überschätzt die Bilanz die Kapazität um den Steinanteil.

**Entscheidungsvorlage.**
- **Vorschlag:** nichts rechnen; bei `stone_content_class = many` und Stufe „Bodenart“ ein Hinweis „Kapazität vermutlich überschätzt“.
- **Alternative für Steine:** bei `many` die Stufe „Bodenart“ nicht verwenden und auf den Standardwert zurückfallen — Folge: sichere Richtung ohne erfundenen Faktor.
- **Alternative für Mulch:** `mulch_factor` auf ETc anwenden — Folge: Bedarf bis zu 50 % unterschätzt; nicht empfohlen. Der Wertebereich in REQ-053 §15.1 sollte auf die Bodenverdunstung bezogen oder auf 0,85–1,0 begrenzt werden (2/3).

### (12) Standardwert des Standorts

**Hintergrund.** Der Standardwert ist die letzte Stufe der Kette. acceptance-4 verlangt: „Kamerplanter liefert keinen eingebauten Kapazitätswert.“ Die Parameterliste verlangt einen „Hilfetext ohne eingebaute Werte (E-10)“.

**Bereich.** Die gelesenen Tabellen für Mineralböden reichen von 1 mm/dm (NRCS, Sand) bis 28 mm/dm (HLNUG, Schluff bei lockerer Lagerung); Torfe liegen bei 35–65 mm/dm [Q7, Q12].

**Korrekturen zum Review.**
- Untergrenze 3 mm/dm schließt Grobsand aus (NRCS 1–3 mm/dm). Vorschlag: 1–30 mm/dm.
- Der Hilfetext-Entwurf des Reviews nennt Zahlen („Sandiger Boden etwa 7–10, Lehm 13–16 …“). Das widerspricht der Vorgabe der Feature-Datei (`soil-water-balance.md:248`). Die Spanne für Sand ist nach dem Gegenlesen außerdem zu hoch (belegt ab 5).

**Vorschlag.** Einheit mm je dm Bodentiefe (nFK), ein Wert je Standort für alle Beete ohne eigene Bodenart, Bereich 1–30, kein eingebauter Wert, Löschen setzt `null`. Der Hilfetext erklärt die Größe und verweist auf die Tabelle in Parameter 3 dieses Dokuments mit ihren Quellen, sobald der Betreiber sie bestätigt hat; bis dahin nennt er keine Zahl. Belegklasse: Konstruktion.

**Sichere Richtung.** Niedrig.

**Entscheidungsvorlage.**
- **Vorschlag:** nFK in mm/dm, 1–30, ohne Vorgabe.
- **Alternative:** Gesamtwert in mm — Folge: einfacher einzugeben; nicht an die Wurzeltiefe gekoppelt, mit dem 30-cm-Deckel aber gleichwertig (Wert = mm/dm × 3).
- **Zu bestätigen:** ob der Hilfetext die bestätigten Werte aus Parameter 3 mit Quelle nennen darf.

### (13) Rückfall „Faustregel + gemessener 24-h-Regen“

**Hintergrund.** Ohne Kapazität bleibt die Tagesbilanz. Der rollende 24-h-Messwert und die Tagesprognose überlappen.

**Quellen.** Keine Quelle behandelt diese Überlappung; die Regel ist Konstruktion. Zur Faustregel selbst siehe Parameter 5: Die Form im Code ist nicht belegt.

**Vorschlag.** Regenguthaben des Tages R = max(gemessen 24 h, Prognose heute), nie die Summe. Tagesbedarf = ETc − Pe(R) mit der heutigen Regel, damit acceptance-7 („rechnet wie heute“) hält. Ohne frischen Messwert gilt die Prognose wie heute.

**Sichere Richtung.** Das Maximum (weniger Regen als die Summe).

**Entscheidungsvorlage.**
- **Vorschlag:** R = max(gemessen 24 h, Prognose heute); Faustregel unverändert, aber als „hauseigene Regel ohne Quelle“ benannt.
- **Alternative:** die Faustregel im Rückfall durch EP = (Regen − 5) × 0,75 ersetzen — Folge: stetig, vorsichtiger, 1/3 belegt [Q5]; ändert das heutige Ergebnis und damit die Regression aus acceptance-7.
- **Alternative:** gemessen seit Mitternacht + Rest der Prognose — Folge: genauer; die Prognose liegt nur als Tagessumme vor, der Rest ist nicht ableitbar.

### (14) Prognosehorizont der Vorausrechnung

**Hintergrund.** Open-Meteo und DWD liefern sieben Tage (`open_meteo_weather_adapter.py:67`, `dwd_weather_adapter.py:29`). REQ-037 §5 nennt `IRRIGATION_DEMAND_HORIZON_DAYS=3` (`:429`), §3.3 rechnet mit `horizon_days=3` (`:352`); der Task schreibt heute nur den laufenden Tag (`irrigation_tasks.py:155`).

| Aussage | Quelle | Prüftiefe |
|---|---|---|
| Niederschlag ist das am schlechtesten vorhersagbare Element | DWD, agrowetter-Dokumentation 2012: „Bis auf die Niederschlagsvorhersage zeigen alle Elemente … eine deutliche Verbesserung“; Niederschlag ist bis 7,7 Tage besser als das Klimamittel (nur Ja/Nein-Aussage) [Q41] | verifiziert |
| Modelle sagen eher zu viel Regen vorher | DWD: „Die Niederschlagsvorhersagegenauigkeit nimmt mit höheren Schwellenwerten augenscheinlich stark ab. Das heißt, wenn sehr viel Niederschlag prognostiziert wird, so fällt real häufig weniger.“; Modelle neigen dazu, „zu viel Niederschlag zu prognostizieren“ [Q41] | verifiziert |
| Fronten und Schauer | DWD Agrarmeteorologie 2026: „durchziehende Fronten: ca. 4 Tage im Voraus gut vorhersagbar“; Schauer und Gewitter „bestenfalls 30 min bis 1 Std. vorher“ [Q42] | verifiziert (Vortragsfolien) |

Alle drei Fundstellen stammen vom DWD: **1/3**. Eine Trefferquote des Tagesniederschlags je Vorhersagetag als Zahl wurde nicht gefunden (in den DWD-Dokumenten nur als Grafik).

**Vorschlag.** Vorausrechnung drei Tage wie in REQ-037 §5. Der Wert ist eine vorhandene Konfiguration, kein neuer agronomischer Wert. Vorhergesagter Regen füllt künftige Tage ungekürzt, mit Herkunft „Prognose“ je Tag; jede Neuberechnung ersetzt ihn durch Messwerte. Tage ohne Prognose: Regen = 0, ETc des Vortags.

**Sichere Richtung.** Kurz. Die DWD-Aussage zur Überschätzung stützt R7 der Anforderungen: Prognoseregen allein verschiebt keine Erinnerung.

**Entscheidungsvorlage.**
- **Vorschlag:** 3 Tage.
- **Alternative:** 2 Tage — Folge: vorsichtiger; die Anzeige „Bedarf ab“ (F-31) reicht kürzer.
- **Alternative:** Prognoseregen künftiger Tage gar nicht gutschreiben — Folge: Die Vorausrechnung zeigt den Bedarf ohne Regen; sicher, aber sie warnt vor Bedarf, den ein angekündigter Landregen deckt.

### (15) Schwelle „starke Abweichung“ zwischen Messung und Prognose

**Hintergrund.** Punktmessung und Gittervorhersage weichen bei Schauern stark ab. Ein Hinweis soll nur erscheinen, wenn die Abweichung die Bilanz ändert.

| Aussage | Quelle | Prüftiefe |
|---|---|---|
| Messfehler von Niederschlagsmessern | WMO-Nr. 8, Kap. 6: Die gemessene Menge „may be less than the actual precipitation reaching the ground by up to 30 % or more“; Windfehler „typically 2 % to 10 % for rain“; Benetzungsverlust „typically 2 % to 15 % in summer“; Verdunstung „0 % to 4 %“ [Q40] | verifiziert |
| Windfehler des Hellmann-Messers bei Regen | DWD (Richter 1995): an frei gelegenen Stationen im Winter über 15 %, „in den Hochsommermonaten 5 % unterschritten“; geschützte Lage „teilweise nur zwischen 1 und 2 %“ [Q43] | verifiziert (Texterkennung) |

Der Messfehler eines Regenmessers liegt im Sommer bei wenigen Prozent bis etwa 15 %; bei 20 mm sind das höchstens rund 3 mm. Eine Abweichung von 10 mm zur Prognose erklärt der Messfehler nicht. Eine Quelle für die Schwelle selbst gibt es nicht (**nicht gefunden**); sie ist eine Produktentscheidung für einen Hinweis, kein agronomischer Wert in der Rechnung.

**Vorschlag.** Hinweis, wenn |gemessen − Prognose| ≥ 10 mm für einen abgeschlossenen Tag. Der laufende Tag wird nicht verglichen. Kein automatischer Ausgleich (R8). Als Einordnung: 10 mm sind rund zwei bis drei Tage ETc und die halbe Bedarfsschwelle eines Lehmbeets.

**Sichere Richtung.** Nicht automatisch korrigieren.

**Entscheidungsvorlage.**
- **Vorschlag:** 10 mm, nur abgeschlossene Tage.
- **Alternative:** relativ, Faktor 3 und mindestens 5 mm — Folge: empfindlicher bei kleinen Mengen, mehr Hinweise.
- **Zu bestätigen:** dass der Wert als Betreiberfestlegung ohne Quelle gilt (kein E-10-Fall, weil er keine Menge ändert).

---

## 3. Kübel, Töpfe, Zelte

**Argument des Reviews.** ET₀ × Kc ist ein Verbrauch je Quadratmeter Boden eines geschlossenen Bestands. Eine Einzelpflanze im Topf hat ein Vielfaches der Topföffnung an Blattfläche. Das Beet-Modell überschätzt die Reserve eines Topfes; die Erinnerung käme zu spät.

**Belege zur Größenordnung.**

| Aussage | Quelle | Prüftiefe |
|---|---|---|
| Wasserverbrauch einer Tomatenpflanze in Substratkultur | British Columbia Trickle Manual Kap. 9: „Feed volumes for tomatoes will start at 0.10 gallons (400 mL)/plant/day and increase to 0.75 gallons (3000 mL)/plant/day.“; Tab. 9.1, Spitzenbedarf Tomate 6,0 L/m²/Tag bei 2,5–3,8 Pflanzen/m²; in Sägemehl „A mature plant will require 1.0 - 1.75 gallons (4-7 litres) per day.“ [Q6] | verifiziert (Gewächshaus, Kanada) |
| Wasserverbrauch im Gefäß, Freiland | University of Missouri G6462: rund 2 bis 2,5 Quarts (1,9–2,4 L) je Pflanze und Tag | Suchauszug (HTTP 403), nicht gezählt |
| Gefäße trocknen schneller aus | RHS: „Plants in containers dry out more quickly than in garden soil“; im Sommer „you may well need to water every day or every other day“ [Q23]; Iowa State: „containers need much more frequent watering than garden beds“, „once or twice a day“ bei kleinen Gefäßen und Hitze [Q24] | verifiziert |
| Kleine, isolierte Bestände verdunsten je Fläche mehr | FAO-56 Kap. 10: bei Wäscheleinen- und Oaseneffekt „the Kc may exceed the grass reference by 100% or more“; Obergrenze „2.5“ [Q1] | verifiziert |

**Einordnung.** Mit 1–3 L je Pflanze und Tag und einer Topföffnung von etwa 0,05 m² (Annahme des Reviews, nicht belegt) ergeben sich 20–60 mm je Topffläche und Tag. ET₀ × Kc liefert im Sommer etwa 5–6 mm. Der Faktor 4–7 des Reviews ist damit in der Größenordnung gestützt, allerdings durch **eine** gezählte Quelle für die Liter (1/3), die aus dem Gewächshaus stammt. Dass Gefäße täglich Wasser brauchen können, ist **2/3** (RHS, Iowa State). FAO-56 begrenzt den Effekt einzelner Pflanzen selbst auf Kc ≤ 2,5; das allein erklärt den Faktor nicht, der Rest folgt aus dem Verhältnis Blattfläche zu Topffläche (Überlegung des Reviews, ohne Quelle).

**Vorschlag (unverändert).** Kübel und Töpfe (`planter`, `Slot.container_volume_l` `site.py:516`, `PlantInstance.container_volume_liters` `plant_instance.py:100`) bleiben in Fassung 1 im Rückfall. Die Topflogik in `watering_service.py` (`suggest_volume` ab `:339`, Substratwert `:422`) wird nicht durch das Beet-Modell ersetzt. Zelte sind ausgeschlossen: `GROW_TENT` gehört nicht zu `WEATHER_RELEVANT_SITE_TYPES` (`enums.py:482`); ein Ortstyp `tent` auf einem Gewächshaus-Standort bekäme sonst Außenwetter.

Hochbeete verhalten sich wie Boden und können mit Substrat × Fülltiefe bilanziert werden, sobald die Fülltiefe vorliegt (§5 Nr. 2).

**Folge für die Spezifikation.** F-29 acceptance-4 nennt „Kübel, Hochbeet, Zelt“ für die Stufe Substrat × Volumen (`soil-water-balance.md:66`), ebenso REQ-053 GP-FR-113 (`:1037`). Beide müssten auf „Hochbeet“ eingeschränkt werden.

**Entscheidungsvorlage.**
- **Vorschlag:** Kübel, Töpfe, Zelte im Rückfall.
- **Alternative:** Kübel mit einem Pauschalfaktor auf ETc — Folge: ein Faktor ohne Quelle; nach E-10 nicht zulässig.

---

## 4. Fehler und Widersprüche in den Spezifikationen

Jede Fundstelle wurde auf diesem Branch nachgeschlagen; korrigierte Zeilennummern sind genannt.

### 4.1 REQ-037 (`spec/req/REQ-037_Evapotranspiration-Bewaesserung.md`)

1. **`:303-304`, `:430` — Faustregel.** `eff_precip = precipitation_mm * 0.8 if precipitation_mm > 5 else precipitation_mm` ist unstetig und nicht monoton (5,0 mm → 5,0 mm; 5,1 mm → 4,08 mm). Der Kommentar „grobe FAO-Faustregel“ ist nicht belegt (Parameter 5). Dieselbe Form im Code: `evapotranspiration_calculator.py:262-265`. Vom Review richtig benannt.
2. **`:31`, `:41`, `:309-312`, Szenario 4 `:483-486` — Deckel.** „Deckelung durch die Wasserhaltefähigkeit“ begrenzt einen Tagesbedarf mit einer Speichergröße. F-29 acceptance-1 schreibt das Kriterium neu. Bestätigt.
3. **`:363` — `substrate_service.water_holding_capacity_mm(run)`.** Die Umrechnung von Prozent in mm ist nirgends definiert; im Code ist der Wert `None` (`irrigation_tasks.py:147`). Bestätigt.
4. **`:393` — `net_demand_mm_capped == 0`.** Null bedeutet „heute kein Bedarf“ und sagt nichts über den Speicher. Bestätigt.
5. **`:397` und REQ-005 `:1919`, `:99`, `:128` — „>5 mm Regen“.** Einzelschwelle auf Prognosedaten ohne Bezug zum Speicher. Bestätigt; R7 der Anforderungen lässt sie unverändert.
6. **Kc-Tabelle — falsche Fundstelle im Review.** Das Review nannte `:403-404`; dort steht die Frontend-Integration. Die Tabelle steht in `:130-139`, der Hinweis in `:141`. Gegen FAO-56 Tab. 12 [Q1] gelesen: Blattgemüse 0,7 / 1,05 / 0,95 und Solanaceen 0,6 / 1,15 / 0,80 stimmen. Abweichend: Wurzelgemüse Mitte 1,05 statt 1,10; Beerensträucher 0,5 / 1,05 / 0,85 statt 0,30 / 1,05 / 0,50; Rasen Mitte 1,00 statt 0,95. Für `cannabis` und `herb` gibt es keine Zeile (Minze: 0,60 / 1,15 / 1,10). Nicht Gegenstand von F-29.
7. **`:347` gegen den Code.** Das Beispiel iteriert über „outdoor“ und „greenhouse“; der Task nimmt auch `balcony` (`irrigation_tasks.py:63`). Vom Review nur am Rand erwähnt.

### 4.2 REQ-053 (`spec/req/REQ-053_Grafische-Garten-Beetplanung.md`)

1. **GP-FR-113 `:1037` (Review: `:1036`).** „`rainfall`-Ereignisse (§12.1) gehen als effektiver Niederschlag ein“ steht gegen §32.6 Nr. 11 (`:2399`: ohne Menge „geht nicht in die Wasserbilanz“) und gegen F-29 acceptance-6. Mit Regenmesser droht Mehrfachzählung. Bestätigt.
2. **GP-FR-113 `:1037`.** „Für `planter`/`raised_bed`/`tent` wird die Einzelgabe durch nutzbare Wasserkapazität × Substratvolumen gedeckelt“ — Kübel und Zelt sollten herausfallen (§3).
3. **GP-FR-114 `:1038` (Review: `:1037`) gegen §32.6 Nr. 4 `:2339`.** Die Anforderungszeile nennt „Tropf 0,88, Sprinkler 0,75, manuell 0,8“; die Entscheidungstabelle und der Code führen nur Tropf 0,88, alle anderen `null`. Die Zeile ist veraltet. Neu gefunden. Außerdem ist „Howell 2003 … Designwert 88 %“ ungenau (Parameter 7).
4. **`mulch_factor` `:1071` (Review: `:1070`).** „0,5–1,0 Verdunstungsmodifikator“ — als Faktor auf ETc nicht belegt (Parameter 11). Bestätigt.
5. **E-10 `:2313` (Review: `:2312`).** Wortlaut: „Agronomische Werte durch Agenten mit Websuche, **Quelle je Wert**, sonst `null`.“ Die strenge Lesart mit drei unabhängigen Quellen steht in §32.6 Nr. 10 (`:2370`) und im Satz „keine Zahl, bis je Punkt drei Quellen vorliegen“ (`:1161`).
6. **R-008 ist doppelt belegt.** F-29 nennt „R-008“ für die Bodenart-Werte. In `agrobiology-thresholds-req-053.md:114` ist R-008 das „Spülvolumen als Vielfaches des Topfvolumens“, in `site.py:290-291` die Ableitung des Ziel-pH aus der Bodenart. Ein eigener Recherchepunkt „nFK je Bodenart“ existiert unter dieser Nummer nicht; dieses Dokument ist die erste Recherche dazu.
7. **§15.1 gegen den Code.** REQ-053 beschreibt `mulch_factor` (`:1071`) und `substrate_replaced_on` (`:1069`); `SoilProfile` (`site.py:264-311`) trägt beide nicht (der Docstring `:271` kündigt `mulch_factor` an). `stone_content_class` ist vorhanden (`:292`). Bestätigt.
8. **`mineral_substrate` `:1114` (Review: `:1113`), Ortstypen nutzererweiterbar `:321` (Review: `:320`), GP-FR-117 `:1041` (Review: `:1040`), GP-FR-118 `:1042` (Review: `:1041`).** Inhalt bestätigt, Zeilen um eins verschoben.

### 4.3 Feature-Datei und Anforderungen

1. **`soil-water-balance.md:68` (acceptance-6).** „Nur gemessene Niederschlagsmengen gehen in die Bilanz ein“ schließt, wörtlich gelesen, das Gießen aus (Parameter 7).
2. **`soil-water-balance.md:66` (acceptance-4).** „Substrat × Volumen (Kübel, Hochbeet, Zelt …)“ — siehe §3.
3. **`soil-water-balance.md:47`, `:57`.** Die Beschreibung nennt eine „FAO-Faustregel“; nach Parameter 5 ist die Herkunft nicht belegt. Ebenso `measured-rain-soil-water-balance.md:16` und R3/R4 dort.
4. **Lokaler Tag.** Der Task rechnet mit dem UTC-Tag (`irrigation_tasks.py:64`, `datetime.now(UTC).date()`); F-28 verlangt den lokalen Tag des Standorts. Die Bilanz braucht eine einheitliche Tagesgrenze für Messwert, Prognose und Gießereignis.

---

## 5. Lücken im Datenmodell

Pfade relativ zu `src/backend/app/`; jede Stelle auf diesem Branch geprüft.

| Nr. | Fehlende Angabe | Stand im Code | Prüfung der Review-Fundstelle |
|---|---|---|---|
| 1 | Regenexposition je Ort | `Location` (`domain/models/site.py:613`) hat kein Feld; `frost_exposed` (`:654`) als Muster, wird durch `SiteConditions.microclimate` (`:432-451`) abgelöst | bestätigt |
| 2 | Fülltiefe oder Substratvolumen des Beets | `Location.height_m` (`site.py:662`) ist die Höhe von Hochbeet oder Kübel (GP-FR-043), nicht die Fülltiefe; `SubstrateBatch.volume_liters` (`domain/models/substrate.py:146`) hängt am Slot | bestätigt |
| 3 | Wurzeltiefe je Phase | ein Wert je Art (`domain/models/species.py:520`); `domain/models/phase.py` ohne Tiefe | bestätigt |
| 4 | Entleerungsfraktion p je Art | fehlt an `Species` | bestätigt |
| 5 | nFK je Bodenart | keine Tabelle; `SoilProfile.soil_texture` (`site.py:276`) ist nur ein Enum | bestätigt |
| 6 | `mulch_factor`, `mulched_at` | in REQ-053 `:1071` und GP-FR-126 (`:1093`) beschrieben, in `SoilProfile` (`site.py:264-311`) nicht vorhanden | bestätigt (Zeilen korrigiert) |
| 7 | Standardwert des Standorts | kein Feld an `Site` (`site.py:800`) | bestätigt |
| 8 | Füllstand, Kapazität, Stufe, Herkunft je Tag | `IrrigationDemand` (`domain/models/irrigation_demand.py:26-50`) hat keines davon; nur `weather_source` | bestätigt |
| 9 | Blattfläche und Pflanzenzahl je Gefäß | nicht vorhanden; `Slot.container_volume_l` (`site.py:516`), `PlantInstance.container_volume_liters` (`domain/models/plant_instance.py:100`) existieren | bestätigt |
| 10 | Mehrere Arten im Run | `_resolve_species_kc` nimmt `entries[0]` (`tasks/irrigation_tasks.py:192-202`, Zugriff `:199`) | bestätigt |
| 11 | Fläche des Runs | `_resolve_area_m2` fällt auf 1,0 m² zurück (`irrigation_tasks.py:205-212`; Review nannte `:205`) | bestätigt |
| 12 | Bodenfeuchte-Sensor am Beet | GP-FR-118 COULD (`REQ-053:1042`); die Sensor-Übersteuerung in `domain/services/watering_service.py:480` wirkt je Pflanze | bestätigt, Zeile korrigiert |
| 13 | Hangneigung | `SiteConditions.slope_deg` (`site.py:451`) existiert; Abfluss wird nicht modelliert | bestätigt |
| 14 | Gießmenge als Bilanzzufluss | `WateringEvent.volume_liters` (`domain/models/watering_event.py:32`), `WateringLog.volume_liters` (`domain/models/watering_log.py:105`), `CareEvent.quantity`/`unit` (`domain/models/care_event.py:160-161`) existieren; kein Weg in den Task | neu |
| 15 | Wirkungsgrad außerhalb einer Zone | `application_efficiency` nur an der Bewässerungszone (`domain/models/irrigation_zone.py:73`); ein Beet ohne Zone hat keinen | neu |
| 16 | Steingehalt als Volumenanteil | `StoneContentClass` hat drei Stufen (`common/enums.py:2381`), keine Vol.-% | neu |
| 17 | Definition von `easily_available_water_percent` | Schema-Beschreibung (`migrations/seed_data/schemas/substrates.schema.yaml:150`) nennt keinen Saugspannungsbereich | neu |

**Berichtigte Fundstellen des Reviews.** `watering_service.py` „ab Zeile 414“: Die Substratlogik beginnt mit `suggest_volume` in `:339`, der Zugriff auf `water_holding_capacity_percent` steht in `:422`. `substrates.schema.yaml:145` und `:148-150` stimmen. `evapotranspiration_calculator.py:38-41`, `:262-265`, `:269-271` stimmen. `enums.py:482`, `:498`, `:507`, `:2316` stimmen.

---

## 6. Minimalmodell für eine erste Fassung

**Enthalten.**

- Freiland-Beete und Hochbeete auf Boden (`native_soil`, `raised_bed_mix`); Gewächshaus- und Frühbeete mit Regenanteil 0.
- Kapazität C = nFK × Zr nach der Kette: Substrat (EAW) × Fülltiefe → Bodenart-Tabelle (Parameter 3, nach Bestätigung) → Standardwert des Standorts → Rückfall.
- Zr = min(Art-Wert, Fülltiefe, 30 cm).
- Eine Schwelle p = 0,40.
- Tagesschritt S = min(C, max(0, S + Regen + Gießen − ETc)); ein Regenwert je Tag (gemessen, sonst Prognose), ungekürzt.
- Gießen mit Menge wird gutgeschrieben, ohne Menge nicht.
- Start an der Schwelle; voll nur nach füllendem Ereignis.
- Rückfall ohne Kapazität: Tagesbilanz wie heute mit R = max(gemessen 24 h, Prognose).
- Vorausrechnung drei Tage; Hinweis ab 10 mm Abweichung an abgeschlossenen Tagen.

**Zunächst entbehrlich, ohne falsche Sicherheit:** artabhängiges p; Wurzeltiefe je Phase; Stresskoeffizient Ks; Prognose über Tag 3; teilüberdachte Orte; Wirkungsgrad für Handgießen.

**Ausdrücklich nicht modellieren.**

- Mulch als Faktor auf ETc.
- Steingehalt, Drainage und Wasserregime als Zahl.
- Kübel und Töpfe über ET₀ × Kc je Topffläche; Zelte; erdlose Systeme.
- Teilfaktoren für „teilüberdacht“; ein ET-Faktor für das Gewächshaus.
- Kapillaraufstieg, Abfluss, Interzeption.
- Gießen ohne Menge als Gutschrift.
- Die 5-mm-/80-%-Regel neben dem Überlauf.
- Die Summe aus Regenmesser, Prognose und `rainfall`-Ereignis.
- Eine Kalenderregel für den vollen Speicher im Frühjahr.

**Annahmen, die bleiben.** Eine Bilanz je Run und Beet, eine Art je Run (§5 Nr. 10). ET₀ der Standort-Wetterquelle gilt für jedes Beet. Der Regenmesser liefert eine Tagessumme (A1 der Anforderungen).

---

## 7. Entscheidungsvorlage

Die vier Vorab-Parameter stehen zuerst. „Überlebt“ heißt: Der Vorschlag des Reviews ist durch die Quellen gedeckt.

| Nr. | Parameter | Vorschlag | Belegklasse | Sichere Richtung | Schicksal des Review-Vorschlags | Vom Betreiber zu bestätigen |
|---|---|---|---|---|---|---|
| **7** | Gießen als Zufluss | mit Menge: L / Fläche × Wirkungsgrad der Zone, ohne Wirkungsgrad ungekürzt und gekennzeichnet; ohne Menge keine Gutschrift | Zufluss 3/3; Tropf 0,88 3/3 (Spanne); Handgießen 1/3 → `null` | weniger gutschreiben | überlebt, außer „Hand 0,8“ (gestrichen) | Gießen zählt; Verhalten ohne Menge; Verhalten ohne Wirkungsgrad |
| **9** | Regenexposition | Freiland 1; Gewächshaus, Frühbeet, Zelt 0; Balkon 0 bis zur Freigabe; Feld je Ort | Konstruktion | kein Regen | überlebt | Zweiwertigkeit; Balkon-Standard; neues Feld |
| **4** | Bedarfsschwelle | D ≥ 0,40 × C | 3/3 (Spanne) | niedrig | überlebt; „nicht unter 0,3“ ohne Quelle | 0,40 oder 0,30 |
| **10** | Ausschluss erdlos | `hydro`/`nft`/`ebb_flow`/`mist`, `mineral_substrate`, inerte und flüssige Substrate | Konstruktion; Begründung 2/3 | ausschließen | überlebt | Liste; `coco` |
| 1 | Wurzelraumtiefe | min(Art-Wert, Fülltiefe, 30 cm); Jungphasen ohne Verschiebung | Deckel 3/3 (Spanne); 15 cm 2/3 → `null` | niedrig | Deckel überlebt und ist jetzt belegt; „15 cm“ ersetzt durch eine Regel ohne Zahl | Deckel 30 cm; Behandlung der Jungphasen |
| 2 | `water_holding_capacity_percent` | nicht verwenden; EAW × Volumen / Fläche | Regel 3/3; Größe des Abzugs widersprüchlich | EAW | überlebt; „etwa doppelt“ gestrichen | Definition von EAW in REQ-019 |
| 3 | nFK je Bodenart | sand 5, loamy_sand 8, sandy_loam 12, loam 16, silt_loam 17, clay 13 mm/dm; clay_loam `null` | je Wert 3/3 (Spanne); clay_loam widersprüchlich | niedrig | korrigiert: sand 7 → 5, loam 14 → 16, silt_loam 15 → 17, clay_loam 13 → `null` | Tabelle; ob „Spanne“ als 3/3 gilt |
| 5 | Effektiver Niederschlag | Regel entfällt im Speicher; Regen ungekürzt, Überlauf begrenzt; eine Regenquelle je Tag | 3/3; die Regel im Code: nicht gefunden | weniger gutschreiben | überlebt; Zuschreibung zu FAO-56 widerlegt | Wegfall; Berichtigung der Herkunft in Code und REQ-037 |
| 6 | Anfangsfüllstand, Lücken | Start an der Schwelle; voll nur nach füllendem Ereignis; Lücken mit Regen 0 fortschreiben | Regel 3/3; Kalenderregel 1/3; Lückenlänge nicht gefunden | niedrig | korrigiert: „S₀ = C im Frühjahr“ → „voll nur nach füllendem Ereignis“ | Startwert; Lückenlänge |
| 8 | Untergrenze, Deckel | Empfehlung = D ≤ C; keine eigene Untergrenze | Deckel 3/3; 5 mm 1/3 → `null` | D ≤ C | korrigiert: „mindestens 5 mm“ gestrichen | Wegfall von Szenario 4 |
| 11 | Drainage, Steine, Mulch | nicht rechnen; Hinweise; bei `many` Hinweis oder Rückfall | Steinprinzip 3/3, Stufen nicht gefunden; Mulch auf ETc 2/3 | Mulch ignorieren; Steine ignorieren ist unsicher | überlebt; ergänzt um die unsichere Richtung bei Steinen | Umgang mit `many`; Bereich von `mulch_factor` |
| 12 | Standort-Standardwert | nFK in mm/dm, 1–30, ohne Vorgabe; Hilfetext ohne Zahl | Konstruktion | niedrig | korrigiert: Bereich 3–30 → 1–30; Hilfetext ohne Zahlen | Einheit; Hilfetext |
| 13 | Rückfall, Doppelzählung | R = max(gemessen 24 h, Prognose heute); Faustregel unverändert | Konstruktion; Faustregel nicht gefunden | Maximum | überlebt | Maximum; Benennung der Faustregel |
| 14 | Prognosehorizont | 3 Tage, Herkunft je Tag | 1/3 (nur DWD); vorhandene Konfiguration | kurz | überlebt | 3 oder 2 Tage |
| 15 | Starke Abweichung | ≥ 10 mm, nur abgeschlossene Tage | nicht gefunden; Produktentscheidung | nicht korrigieren | überlebt als Betreiberfestlegung | Schwelle |
| — | Kübel, Töpfe, Zelte | im Rückfall; nicht über ET₀ × Kc | Größenordnung 1/3 | ausschließen | überlebt | Einschränkung von acceptance-4 und GP-FR-113 auf Hochbeete |

**Zusammenfassung der Korrekturen am Review.**

1. FAO-56 enthält die 5-mm-/80-%-Regel nicht; die einzige Tagesregel dort ist „weniger als 0,2 × ET₀“. Die nächsten belegten Verwandten zählen unter der Schwelle null.
2. nFK: sand 7 → 5, loam 14 → 16, silt_loam 15 → 17, clay_loam 13 → `null`.
3. Wirkungsgrad „Hand 0,8“ ist nicht belegt (einzige Quelle: 0,5–0,7).
4. Der Designwert 88 % stammt von Alberta, nicht von Howell.
5. p bei Gemüse reicht in FAO-56 von 0,20 bis 0,50; die Untergrenze 0,3 hat keine Quelle.
6. Kohl wurzelt nach FAO-56 0,5–0,8 m tief; für Minze, Beerensträucher, Obst und Rasen nennt FAO-56 Werte.
7. Der 30-cm-Deckel ist belegt; die 15-cm-Stufe nur 2/3.
8. „S₀ = C im Frühjahr“ ist eine Kalenderregel ohne Quelle; belegt ist „voll nach füllendem Ereignis“.
9. „Mindestens 5 mm“ je Gabe ist 1/3; Gießquellen nennen 8–10 mm.
10. „WHC etwa doppelt so hoch wie EAW“ ist strittig; EN 13041 belegt die EAW-Definition nicht.
11. Untergrenze des Standardwerts 3 → 1 mm/dm; der Hilfetext darf nach der Feature-Datei keine Zahlen tragen.
12. Die Gewächshaus-Annahme (ET innen 60–80 % von außen) ist jetzt belegt.
13. Fundstellen: REQ-053 um eine Zeile verschoben; die Kc-Tabelle steht in REQ-037 `:130-139`; `watering_service.py:339`/`:422`; die Feature-Datei enthält die als fehlend gemeldeten Abschnitte.
14. `RootDepth` gehört zur Pflanzenfamilie; die Seeds tragen die Wurzeltiefe 129-mal, nicht für „nahezu alle 210 Arten“.

---

## 8. Offene Recherchepunkte

Bezeichnung R-001 … R-012 wie im Review.

| Nr. | Frage | Stand nach diesem Durchgang | Versuchte Suche |
|---|---|---|---|
| R-001 | nFK je Bodenart | geschlossen für sechs Klassen (3/3 Spanne); offen: clay_loam (widersprüchlich); Zuordnung USDA-Klassen ↔ deutsche Bodenarten; KA5 im Original | FAO-56 Tab. 19, NRCS NEH 652, Extension-Tabellen, HLNUG, LGB, Geisenheim; KA5 selbst nicht frei zugänglich; „Bodenbewertungsinstrument Sachsen“ nur als Suchauszug |
| R-002 | Zr und p je Kultur | geschlossen für Gemüse; offen: Wurzeltiefe von Jungpflanzen (2/3); p je Art im Datenmodell | FAO-56 Tab. 22, NRCS Tab. 3–3/3–4, British Columbia, Utah State, Geisenheim, Colorado State; KTBL-Arbeitsblatt 703 abgewiesen; LfULG-Versuchsberichte nur als Suchauszug |
| R-003 | Herkunft der 5-mm-/80-%-Regel | geklärt: in FAO-56 nicht enthalten; nächste Verwandte British Columbia und FAO-Paper 25 (Burma, Reis). Offen: wer die Form „80 % der Gesamtmenge über 5 mm“ je veröffentlicht hat | FAO-56 Kap. 8, FAO-Paper 25 Kap. II, FAO-Schulungsheft 3; CROPWAT-Dokumentation („fixed percentage“) nur als Suchauszug |
| R-004 | Mulch: Anteil an ETc | Bodenverdunstung 3/3; Wirkung auf ETc 2/3 | FAO-56 Kap. 10, UC-Auszug aus Chalker-Scott, Nebraska G2000; Chalker-Scott 2007 im Original HTTP 403; Übersichtsarbeit in Irrigation Science 2024 hinter Anmeldung |
| R-005 | Wirkungsgrade | Tropf und Sprinkler geschlossen (3/3 Spanne); Handgießen offen (1/3) | fünf Tabellen gelesen; Howell 2003 im Original nicht gefunden; keine Messung zum Gießen mit Kanne oder Schlauch gefunden |
| R-006 | Gewächshaus-ET gegenüber Freiland | 3/3 (Spanne 60–80 %) für Kunststoffgewächshäuser in warmen Klimaten; offen für mitteleuropäische Kleingewächshäuser | SciELO, Orgaz et al., Jaafar und Ahmad; FAO-Paper 217 nicht abrufbar; keine deutsche Quelle gefunden |
| R-007 | Prognosegüte des Tagesniederschlags nach Tag 1/2/3 | offen: keine Zahl je Vorhersagetag; nur qualitative DWD-Aussagen (1/3) | DWD agrowetter-Dokumentation, DWD-Seite zur Vorhersagequalität, DWD-Vortrag 2026; ECMWF-Berichte nicht selbst gelesen; NOAA und BoM HTTP 403 |
| R-008 | Abschlag je Steingehalt | Prinzip 3/3; offen: Zuordnung der drei Enum-Stufen zu Vol.-% | NRCS Tab. 2–2, LGB Tab. 4, GD NRW |
| R-009 | Verbrauch einer Topfpflanze je Tag | 1/3 (British Columbia [Q6], Gewächshaus); offen für Freiland-Kübel | British Columbia Trickle Manual; Missouri G6462 und UF/IFAS HS169 nur als Suchauszug (HTTP 403) |
| R-010 | Zielmenge je Gabe | „selten und durchdringend“ 3/3; kleinste Gabe 2/3 (8–10 mm); größte Gabe 2/3 (20–25 mm) | Gartenakademie, Geisenheim, IGZ, RHS, Iowa State, Connecticut |
| R-011 | Lückenlänge, Start im Sommer | Start geklärt (voll nur nach füllendem Ereignis, 3/3); Lückenlänge ohne Quelle | FAO-56, Geisenheim, British Columbia, Colorado State |
| R-012 | Kc ini bei Gemüse | FAO-56 Tab. 12 gelesen; drei Zeilen der REQ-037-Tabelle weichen ab (§4.1 Nr. 6); nicht Gegenstand von F-29 | FAO-56 Kap. 6 |
| neu | Definition der EAW-Werte in den Substrat-Seeds | offen (REQ-019 / #1175) | nicht gesucht |
| neu | Richtwerte für EAW und Luftkapazität | nicht gefunden | ISHS-Zusammenfassung ohne Zahlen; MDPI-Artikel HTTP 403 |
| neu | Kokossubstrat im Freiland: Bilanz oder Ausschluss | nicht gesucht | — |

---

## 9. Quellen

Prüftiefe „verifiziert“: für dieses Dokument abgerufen und im Volltext gelesen. Jahresangaben in Klammern mit „o. J.“, wo die Seite kein Datum trägt.

| Nr. | Institution, Titel, Jahr | URL | Prüftiefe |
|---|---|---|---|
| Q1 | FAO — Allen, Pereira, Raes, Smith: „Crop evapotranspiration“, Irrigation and Drainage Paper 56, 1998. Kap. 6 (Tab. 12), Kap. 7 (Tab. 19), Kap. 8 (Tab. 22, Gl. 80–88), Kap. 10 (Mulch, kleine Bestände) | <https://www.fao.org/4/X0490E/x0490e0b.htm>, <https://www.fao.org/4/X0490E/x0490e0c.htm>, <https://www.fao.org/4/X0490E/x0490e0e.htm>, <https://www.fao.org/4/X0490E/x0490e0g.htm> | verifiziert |
| Q2 | FAO — „Effective rainfall in irrigated agriculture“, Irrigation and Drainage Paper 25 (Dastane, 1974; Autor und Jahr stehen nicht auf der Seite), Kap. II | <https://www.fao.org/4/X5560E/x5560e03.htm> | verifiziert |
| Q3 | FAO — Irrigation Water Management, Training Manual 3 „Irrigation Water Needs“ (1986; Jahr steht nicht auf der Seite), Kap. 3 | <https://www.fao.org/4/s2022e/s2022e03.htm> | verifiziert |
| Q4 | FAO — Irrigation Water Management, Training Manual 4 „Irrigation Scheduling“ (1989; Jahr steht nicht auf der Seite), Annex I | <https://www.fao.org/4/t7202e/t7202e08.htm> | verifiziert |
| Q5 | B.C. Ministry of Agriculture — B.C. Irrigation Management Guide, Ausgabe 2005, Kap. 3, 5, 6; Factsheet 577.100-3 „Sprinkler Irrigation Scheduling Using a Water Budget Method“, 2004 (über einen Spiegel); Farmwest „Effective Precipitation“ (o. J.) | <https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/agriculture-and-seafood/agricultural-land-and-environment/water/irrigation/irrigation-management-guide/577300-0_irrigmgmtguide_chapter_03_with_titlepage.pdf> (Kap. 5 und 6 mit `chapter_05`, `chapter_06`), <https://www.irrigationtoolbox.com/ReferenceDocuments/Extension/BCExtension/577100-3.pdf>, <https://farmwest.com/climate/calculator-information/et/effective-precipitation/> | verifiziert |
| Q6 | B.C. Ministry of Agriculture — B.C. Trickle Irrigation Manual, 1999, Kap. 9 „Greenhouse Drip Systems“; zählt mit Q5 | <https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/agriculture-and-seafood/agricultural-land-and-environment/water/irrigation/trickle-irrigation-manual/chapter9.pdf> | verifiziert |
| Q7 | USDA-NRCS — National Engineering Handbook, Part 652 Irrigation Guide, 1997, Kap. 2 (Tab. 2–1, 2–2) und Kap. 3 (Tab. 3–3, 3–4); gelesen über einen Spiegel, nicht über nrcs.usda.gov | <https://mail.irrigationtoolbox.com/NEH/Part652_NationalIrrigationGuide/ch2.pdf>, <https://mail.irrigationtoolbox.com/NEH/Part652_NationalIrrigationGuide/ch3.pdf> | verifiziert |
| Q8 | Colorado State University Extension — Andales u. a.: „Irrigation Scheduling: The Water Balance Approach“ (o. J.) | <https://extension.colostate.edu/resource/irrigation-scheduling-the-water-balance-approach/> | verifiziert |
| Q9 | Utah State University Extension — Utah Vegetable Production Guide, „Irrigation“ (o. J.) | <https://extension.usu.edu/vegetableguide/management/irrigation> | verifiziert |
| Q10 | University of Wisconsin Extension — „The important role of soil texture on water“ (o. J.); Tabelle nach USDA-NRCS, zählt mit Q7 | <https://cropsandsoils.extension.wisc.edu/articles/the-important-role-of-soil-texture-on-water> | verifiziert |
| Q11 | Hochschule Geisenheim, Institut für Gemüsebau — „Geisenheimer Bewässerungssteuerung 2021 mit kc-Werten für Penman-Verdunstung“, 22.04.2021 | <https://www.hs-geisenheim.de/fileadmin/redaktion/FORSCHUNG/Institut_fuer_Gemuesebau/Ueberblick_Institut_fuer_Gemuesebau/Geisenheimer_Steuerung/kc-Werte_PENMAN_2021.pdf> | verifiziert |
| Q12 | HLNUG Hessen — „Kennwerttabellen zur Bestimmung der nutzbaren Feldkapazität“ (HLUG 2003, in Anlehnung an AG Boden 1982 und 1994) | <https://www.hlnug.de/static/medien/boden/fisbo/bk/bfd50/extdoc/kenn_nfk.html> | verifiziert |
| Q13 | Landesamt für Geologie und Bergbau Rheinland-Pfalz — „Methodendokumentation BFD50 – Nutzbare Feldkapazität des Bodens“, 2025 | <https://www.lgb-rlp.de/fileadmin/service/lgb_downloads/boden/bfd50_methodenbeschriebe/bfd50_nfk.pdf> | verifiziert |
| Q14 | Geologischer Dienst NRW — „Nutzbare Feldkapazität“ (Auszug IS BK50), 2024 | <https://gd.nrw.de/wms_html/bk50_wms/pdf/NFK.pdf> | verifiziert |
| Q15 | LWG Bayern, Bayerische Gartenakademie — „Bewässerung im Haus- und Kleingarten“, Berichte der Bayerischen Gartenakademie 4, 2017 | <https://lwg.bayern.de/mam/cms06/gartenakademie/dateien/bewaesserung_bericht_4.pdf> | verifiziert |
| Q16 | IGZ Großbeeren — C. Feller: „Bewässerung im Freilandgemüsebau“, Vortrag 2013, bereitgestellt vom LfULG Sachsen | <https://www.landwirtschaft.sachsen.de/download/03_Bewaesserung_Gartenbau_Feller.pdf> | verifiziert |
| Q17 | LWK Niedersachsen — E. Fricke, A. Riedel: „Möglichkeiten der Beregnungssteuerung“, 2017, bereitgestellt vom LBEG | <https://www.lbeg.niedersachsen.de/download/120384> | verifiziert |
| Q18 | Alberta Agriculture and Rural Development — „Irrigation System Application Efficiency Values“, Agdex 563-1, 2011; Spannen nach Howell 2003 | <https://www1.agriculture.alberta.ca/$department/deptdocs.nsf/all/agdex13729/$file/563-1.pdf> | verifiziert |
| Q19 | University of Nebraska–Lincoln Extension — Irmak u. a.: „Irrigation Efficiency and Uniformity, and Crop Water Use Efficiency“, EC732, 2011 | <https://extensionpubs.unl.edu/publication/ec732/2011/pdf/view/ec732-2011.pdf> | verifiziert |
| Q20 | Texas A&M AgriLife Extension — G. Fipps: „Soil Moisture Management“, AGEN-PU-223, 2025 | <https://irrigation.tamu.edu/wp-content/uploads/sites/3/2025/11/Soil-Moisture-Management.pdf> | verifiziert |
| Q21 | Oregon State University Extension — „Irrigation management basics“, EM 9923, 2010 (durchgesehen 2024) | <https://extension.oregonstate.edu/water/irrigation/irrigation-management-basics> | verifiziert |
| Q22 | UC Master Gardeners of San Luis Obispo County — „Drip Irrigation for Home Gardens“ (o. J.) | <https://ucanr.edu/site/uc-master-gardeners-san-luis-obispo-county/drip-irrigation-home-gardens> | verifiziert |
| Q23 | Royal Horticultural Society — „Watering“, „How to water containers“, „Watering vegetables and fruit“ (o. J.) | <https://www.rhs.org.uk/garden-jobs/watering>, <https://www.rhs.org.uk/container-gardening/how-to-water-containers>, <https://www.rhs.org.uk/vegetables/watering> | verifiziert |
| Q24 | Iowa State University Extension — „Watering the Home Vegetable Garden“, „Care of Plants Growing in Containers“ | <https://yardandgarden.extension.iastate.edu/how-to/watering-home-vegetable-garden>, <https://yardandgarden.extension.iastate.edu/how-to/care-plants-growing-containers> | verifiziert |
| Q25 | Connecticut Agricultural Experiment Station — L. Whittinghill: „Irrigating Your Home Vegetable Garden“ (o. J.) | <https://portal.ct.gov/-/media/caes/documents/publications/fact_sheets/environmental-science-and-forestry/irrigating-your-home-vegetable-garden.pdf> | verifiziert |
| Q26 | Altland, Owen, Fonteno: „Developing moisture characteristic curves and their descriptive functions at low tensions for soilless substrates“, J. Amer. Soc. Hort. Sci. 135(6), 2010 | <https://ars.usda.gov/ARSUserFiles/50820500/GPRG/2010PublicationsandSummaries/2010_Developing%20moisture%20characteristics%20curves.pdf> | verifiziert |
| Q27 | Yafuso, Fisher u. a.: „Water and Air Relations in Propagation Substrates“, HortScience 54(11), 2019 | <https://ars.usda.gov/ARSUserFiles/50820500/GPRG/2019PublicationsandSummaries/2019_Water%20and%20Air%20Relations%20in%20Propagation%20Substrates.pdf> | verifiziert |
| Q28 | Basiri Jahromi, Fulcher, Walker, Altland: „Optimizing Substrate Available Water and Coir Amendment Rate in Pine Bark Substrates“, Water 12, 362, 2020 | <https://ars.usda.gov/ARSUserFiles/50820500/GPRG/2020PublicationsandSummaries/2020_Optimizing%20Substrate%20Available%20Water%20and%20Coir.pdf> | verifiziert |
| Q29 | Bilderback, Warren, Owen, Albano: „Healthy Substrates Need Physicals Too!“, HortTechnology 15(4), 2005 | <https://www.ars.usda.gov/ARSUserFiles/11847/bilderback_etal_2005_Hort%20Tech%2015(4)%20pp%20747-751.pdf> | verifiziert |
| Q30 | Fields, Fonteno, Jackson: „Plant Available and Unavailable Water in Greenhouse Substrates: Assessment and Considerations“, Acta Hort. 1034, 2014 | <https://woodsubstrates.cals.ncsu.edu/wp-content/uploads/sites/39/2020/02/plant-available-and-unavailable.pdf> | verifiziert |
| Q31 | Purdue Extension — K. Nemali: „Understanding the Pores of a Soilless Substrate“, HO-287-W | <https://www.extension.purdue.edu/extmedia/HO/HO-287-W.pdf> | verifiziert |
| Q32 | Swedish Institute for Standards — Kurzbeschreibung SS-EN 13041:2011 | <https://www.sis.se/en/produkter/agriculture/fertilizers/ssen130412011/> | verifiziert (nur Geltungsbereich) |
| Q33 | ISHS — De Boodt, Verdonck: „The physical properties of the substrates in horticulture“, Acta Hort. 26, 1972 (Zusammenfassung) | <https://ishs.org/ishs-article/26_5/> | verifiziert (Zusammenfassung ohne die Definition) |
| Q34 | Fernandes, Corá, Araújo: „Reference evapotranspiration estimation inside greenhouses“, Scientia Agricola 60(3), 2003 | <https://scielo.br/j/sa/a/dQYjWhZCtpcmjnGTkj8rR4s/?lang=en> | verifiziert |
| Q35 | Orgaz, Fernández, Bonachela, Gallardo, Fereres: „Evapotranspiration of horticultural crops in an unheated plastic greenhouse“, Agricultural Water Management 72, 2005 | <https://publicacionescajamar.es/wp-content/uploads/2023/03/evapotranspiration-of-horticultural.pdf> | verifiziert |
| Q36 | Jaafar, Ahmad: „Determining reference evapotranspiration in greenhouses from external climate“, 2019 (Zusammenfassung im Repositorium der American University of Beirut) | <https://scholarworks.aub.edu.lb/items/1200337d-68df-4e78-a425-0bff37c04229> | verifiziert (Zusammenfassung) |
| Q37 | University of California Cooperative Extension — „Impact of Mulches on Landscape Plants“ (Auszug aus Chalker-Scott 2007) | <https://ccfruitandnuts.ucanr.edu/sites/default/files/2011-03/80212.pdf> | verifiziert (zweite Hand) |
| Q38 | University of Nebraska–Lincoln Extension — S. van Donk: „Tillage and Crop Residue Affect Irrigation Requirements“, G2000, 2010 | <https://extensionpubs.unl.edu/publication/g2000/2010/html/view> | verifiziert |
| Q39 | Wageningen UR Glastuinbouw — „Cultivation of Tomato“, Technical information sheet No. 8 (o. J.) | <https://edepot.wur.nl/403806> | verifiziert |
| Q40 | WMO — Guide to Instruments and Methods of Observation (WMO-No. 8), Kap. 6 „Measurement of Precipitation“, vorläufige Ausgabe 2018 | <https://old.wmo.int/extranet/pages/prog/www/IMOP/publications/CIMO-Guide/Prelim_2018_ed/8_I_6_en_MR_clean.pdf> | verifiziert |
| Q41 | DWD — „Allgemeine Informationen zur Wettervorhersage“ (agrowetter-Dokumentation), 2012 | <https://www.dwd.de/DE/fachnutzer/landwirtschaft/dokumentationen/agrowetter/Wetter_Modell_Prognoseguete.pdf?__blob=publicationFile&v=2> | verifiziert |
| Q42 | DWD Agrarmeteorologie — B. Plückhahn: „Niederschlagsprognosen … auch nicht mehr das, was sie mal waren?“, Vortragsfolien 2026, bereitgestellt vom RP Darmstadt | <https://rp-darmstadt.hessen.de/sites/rp-darmstadt.hessen.de/files/2026-01/niederschlagsprognosen-auch_nicht_mehr_das_was_sie_mal_waren_b-plueckhahn.pdf> | verifiziert |
| Q43 | DWD — D. Richter: „Ergebnisse methodischer Untersuchungen zur Korrektur des systematischen Meßfehlers des Hellmann-Niederschlagsmessers“, Berichte des DWD, 1995 | <https://dwdbib.dwd.de/retrosammlung/download/pdf/38928> | verifiziert (Texterkennung) |

**Nur als Suchauszug oder aus zweiter Hand, nicht gezählt:** Howell, T. A. (2003), „Irrigation Efficiency“, Encyclopedia of Water Science; University of Missouri Extension G6462; UF/IFAS HS169 und HS1274; ECMWF Newsletter 144 und Technical Memorandum 615; Chalker-Scott (2007), J. Environ. Hort. 25(4); „Bodenbewertungsinstrument Sachsen“ (2022); KTBL-Arbeitsblatt 703; UC IPM (Tabelle zum Wasserhaltevermögen).
