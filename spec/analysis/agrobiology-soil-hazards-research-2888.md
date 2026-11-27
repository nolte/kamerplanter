# Recherche Bodengefahren, Wirtskreise und Nachpflanzen (R-001 … R-004)

| Feld | Wert |
|------|------|
| Datum | 2026-11-15 |
| Bezug | GitHub #2888; REQ-054 §5.2 (`soil_hazards[]`), §5.5 (Bodenpathogene), §6 H-10/H-11 und Notiz „Übernommen aus REQ-053 §11.3“; REQ-053 §11.3 „ausgefallen“, GP-FR-131 |
| Methode | E-10: je Wert drei voneinander unabhängige Quellen (Fachliteratur, Landesanstalten/Kammern/JKI, RHS, AHDB, UC IPM, US-Extension-Services, Reviews). Wo weniger als drei unabhängige Quellen gefunden wurden, steht der Wert als **„nicht belegt (n/3)“**. |
| Nachtrag | 2026-11-17, GitHub #3005: Nachrecherche der in §6.3 offenen Werte, Ergebnisse in §7 |
| Korrektur | 2026-11-26, F-18 (#2888): Betreiberentscheidungen vom 2026-11-22 zu §7.12 Punkt 1 (Spannen zählen als 3/3) und Punkt 5 (`soil_persistence_years` = Anbaupause) eingearbeitet; R-001.2, §6.1, §7.2, §7.11 korrigiert. Die Werte stehen in der Wissenstabelle `src/backend/app/migrations/seed_data/soil_hazards.yaml` (REQ-054 §5.2a). |
| Status | Recherche, keine Entscheidung. Planungswerte sind **Vorschläge** für den Betreiber und das REQ-001-Folge-Issue (`soil_persistence_years`, `pathogen_hosts`). |

## 0. Lesehinweise zur Methode

- **Unabhängigkeit.** Mehrere Seiten derselben Institution (z. B. drei UC-IPM-Leitlinien) zählen als **eine** Quelle. Die Liste juglonempfindlicher Pflanzen der University of Wisconsin geht erkennbar auf Purdue HO-193 zurück; beide zählen zusammen als eine Quelle.
- **Prüftiefe.** „verifiziert“ heißt: Text der Quelle selbst gelesen (HTML oder per `pdftotext` aus dem PDF). „Suchauszug“ heißt: Aussage nur aus dem Treffertext der Websuche, Volltext nicht geprüft. Suchauszüge zählen in dieser Recherche **nicht** zum Belegstatus, sie stehen nur als Hinweis in der Tabelle.
- **Zwei Größen je Bodengefahr.** Die Literatur nennt zwei verschiedene Dinge, die im Datenmodell nicht verwechselt werden dürfen:
  1. **maximale Überdauerung** des Erregers ohne Wirt (oft 10–20 Jahre, beschreibt das Restrisiko) und
  2. **empfohlene Anbaupause nach bestätigtem Befall** (Beratungsempfehlung, meist deutlich kürzer).
  H-10 sperrt bis `confirmed_at + soil_persistence_years`. Setzt man dort die maximale Überdauerung ein, ist ein Beet für Kohl oder Zwiebeln praktisch dauerhaft gesperrt. **Vorschlag:** `soil_persistence_years` = Sperrdauer nach Beratungsempfehlung (konservativ am oberen Rand der belegten Spanne); zusätzlich ein rein informatives Feld `max_survival_years`, das nach Ablauf der Sperre eine Warnung statt einer Sperre trägt (H-07-artige Übersteuerung bleibt möglich).
- **Familiennamen** nach APG IV: Chenopodiaceae → **Amaranthaceae**, Alliaceae → **Amaryllidaceae**, Cruciferae → **Brassicaceae**.

### Familien des Katalogs, die für diese Recherche zählen

Ermittelt aus `spec/knowledge/plants/*.md` (Zeile `| Familie | … |`, 210 Steckbriefe). Nur Familien mit Nutz- oder Gartenkulturen:

| Familie | Arten im Katalog (Auszug, vollständig für die Gemüsefamilien) |
|---------|------|
| Brassicaceae | *Brassica oleracea* (botrytis, capitata, gemmifera, gongylodes, italica, sabellica), *Eruca vesicaria*, *Raphanus sativus* var. *sativus*, *Sinapis alba* |
| Solanaceae | *Solanum lycopersicum*, *S. tuberosum*, *S. melongena*, *Capsicum annuum*, *Physalis peruviana*, *Nicotiana tabacum*, *Petunia × hybrida* |
| Amaranthaceae | *Beta vulgaris* subsp. *vulgaris*, *Spinacia oleracea* |
| Amaryllidaceae | *Allium cepa*, *A. porrum*, *A. sativum*, *A. schoenoprasum*; außerdem *Clivia miniata*, *Hippeastrum* (Zierpflanzen, keine *Allium*) |
| Fabaceae | *Pisum sativum*, *Phaseolus vulgaris*, *Vicia faba*, *Lens culinaris*, *Glycine max*, *Medicago sativa*, *Trifolium pratense*, *Lupinus polyphyllus* |
| Cucurbitaceae | *Cucumis sativus*, *C. melo*, *Citrullus lanatus*, *Cucurbita pepo*, *C. maxima*, *Luffa aegyptiaca* |
| Apiaceae | *Daucus carota*, *Apium graveolens* (inkl. var. *rapaceum*), *Pastinaca sativa*, *Petroselinum crispum*, *Anethum*, *Coriandrum*, *Foeniculum*, *Levisticum* |
| Asteraceae | *Lactuca sativa*, *Cichorium intybus*, *Helianthus annuus*, *Calendula*, *Tagetes erecta/patula*, *Dahlia* (5 Sorten), *Echinacea*, *Artemisia dracunculus*, *Matricaria* |
| Rosaceae | *Fragaria × ananassa*, *Rubus idaeus*, *R. fruticosus*, *Malus domestica*, *Pyrus communis*, *Prunus avium*, *P. domestica*, *Rosa* |
| Lamiaceae | *Mentha × piperita*, *Ocimum basilicum*, *Salvia*, *Thymus*, *Origanum*, *Melissa*, *Rosmarinus*, *Lavandula*, *Satureja* |
| Poaceae | *Zea mays*, *Triticum aestivum*, *Hordeum vulgare*, *Avena sativa*, *Sorghum bicolor*, *Oryza sativa* |
| weitere | Asparagaceae (*Asparagus officinalis*), Polygonaceae (*Rheum rhabarbarum*), Ericaceae (*Vaccinium corymbosum*), Grossulariaceae (*Ribes*), Vitaceae (*Vitis*), Boraginaceae (*Phacelia*), Tropaeolaceae (*Tropaeolum*) |

Kein Walnussbaum (*Juglans*) im Katalog: `juglone` ist eine Gefahr von **außerhalb** des Beets (Nachbarbaum, gerodeter Baum), keine Vorkultur.

Befund am Rande: Die Seed-YAML unter `src/backend` trägt `family:` nur für wenige Einträge (grep ergab rund 70 Treffer, darunter 5 mit dem Platzhalter `str`); die Familienzuordnung steht verlässlich nur in den Steckbriefen. `Dracaenaceae` in einem Steckbrief ist kein APG-IV-Name (heute Asparagaceae).

---

## R-001 Überdauerung im Boden (`soil_persistence_years`)

**Fragestellung.** Wie lange bleibt jeder Erreger der REQ-054-Liste ohne Wirt im Boden infektiös, welche Anbaupause empfehlen Beratungsstellen nach bestätigtem Befall, und welcher konservative Planungswert folgt daraus?

### R-001.1 Kohlhernie (`clubroot`, *Plasmodiophora brassicae*)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | 15–20 J. | AHDB: „up to 15 years, with a half-life of approximately 3.5 years“ — [AHDB Clubroot management in OSR](https://ahdb.org.uk/knowledge-library/clubroot-management-in-oilseed-rape-cropping-factors) (verifiziert) | RHS: „resting spores that can contaminate soil for up to 20 years“ — [RHS Club root](https://www.rhs.org.uk/disease/club-root) (verifiziert) | NC State Extension: „more than 10 years“ — [NCSU Clubroot of Brassicas](https://content.ces.ncsu.edu/clubroot-of-brassicas) (verifiziert) | **3/3** (Spanne >10 bis 20 J.) |
| Halbwertszeit | 3,5–4,5 J. | AHDB 3,5 J. (s. o.) | Wallenhammar 1996, zitiert in Dixon 2009, *J. Plant Growth Regul.*: 3–6 J., nach 17,3 J. unter Nachweisgrenze — [Dixon 2009 (Univ. Reading, PDF)](https://centaur.reading.ac.uk/66432/1/Journal%20of%20Plant%20Growth%20Regulation%20EDITED%20DIXON%20Plasmodiophora%20brassicae%20in%20soil%20and%20host%20environments.pdf) (Suchauszug) | LW 2013: 3,6 J. — [lw-heute.de](https://www.lw-heute.de/mediaarchiv/grab_pic.php?id=20485) (Suchauszug) | **1/3** verifiziert (2 Suchauszüge) |
| empfohlene Pause nach Befall | 4–7 J. | AHDB: „a break of at least four years“ (verifiziert) | DLR RLP Gartenakademie: Kreuzblütler „erst nach 4–6 Jahren“, Dauersporen 10–20 J. — [Gartenakademie RLP, Infoblatt Kohlhernie](https://www.gartenakademie.rlp.de/Internet/global/themen.nsf/0/E25577BBDB1120C5C12571DF003E5035/$FILE/Kohlhernie-Gartenakademie.pdf) (Suchauszug) | UT Extension W235, Tab. 1: Kohl und Rettich, Kohlhernie **7** J. ohne anfällige Kultur — [UT W235-E](https://uthort.tennessee.edu/wp-content/uploads/sites/228/2024/01/W235-E-rotation.pdf) (verifiziert) | **2/3** verifiziert (DLR nur Suchauszug) |

Zusatzbefund: Der Abbau ist nicht linear. Kher et al. (2019, bioRxiv-Preprint, nicht begutachtet) beschreiben einen steilen Verlust in den ersten zwei Jahren und danach einen langen Schwanz — [bioRxiv 819524](https://www.biorxiv.org/content/biorxiv/early/2019/10/25/819524.full.pdf) (Suchauszug). Kreuzblütige Unkräuter (Hirtentäschel, Ackersenf) halten die Population während der Pause aufrecht (AHDB, RHS, verifiziert).

**Vorschlag:** `soil_persistence_years = 7`, `max_survival_years = 20`. Begründung: 7 ist der obere Rand der belegten Pausenempfehlungen (UT 7, DLR bis 6, AHDB ≥ 4) und entspricht bei einer Halbwertszeit von 3,5 J. zwei Halbwertszeiten (≈ 25 % Restinokulum). REQ-053 GP-FR-131 nennt bereits „Kohlhernie ≥ 7 J.“; der Wert ist damit konsistent. Nach Ablauf bleibt eine Warnung bis Jahr 20.

### R-001.2 Rübenzystennematode (`cyst_nematode`, *Heterodera schachtii*)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | „jahrelang“ bis > 12 J. | NDSU: „a small percentage of eggs within cysts can survive over 12 years under fallow conditions“ — [NDSU Sugarbeet cyst nematode](https://www.ndsu.edu/agriculture/ag-hub/publications/sugarbeet-cyst-nematode) (verifiziert) | AGES: Zysten „bleiben jahrelang lebensfähig“ — [AGES Rübenzystennematoden](https://www.ages.at/pflanze/pflanzengesundheit/schaderreger-von-a-bis-z/ruebenzystennematoden) (verifiziert, ohne Zahl) | KWS (Züchter): ca. 10 J. — [KWS dzz 05/2017](https://mediamaster.kws.com/01_Products/DE_Deutschland/Sugar_Beet/Downloads/R%C3%BCbenzystennematoden-Ein_verbreitetes_Problem_dzz_05-2017.pdf) (Suchauszug) | Zahl **1/3**; „mehrjährig“ 2/3 |
| Abnahme ohne Wirt | 40–60 %/J. | UNL G1906: „decline about 40 to 60 percent per year“ — [UNL Extension G1906](https://extensionpubs.unl.edu/publication/g1906/na/html/view) (verifiziert) | NDSU: Nichtwirte senken die Ausgangspopulation um 40–60 % in einem Jahr (verifiziert) | — | **2/3** |
| empfohlene Pause nach Befall | 2–3 J. Pause (Rotation 3–4 J., Tara-Böden 3–5; Korrektur 2026-11-26) | LfL Merkblatt „Nematoden im Feldgemüsebau“: „Wirtspflanzen sollten maximal alle drei Jahre angebaut werden“ — [LfL p_37956](https://www.lfl.bayern.de/mam/cms07/publikationen/daten/merkblaetter/p_37956.pdf) (verifiziert) | NDSU: „Heavily infested fields need a three- to four-year rotation“ (verifiziert) | AGES: „Ein vierjähriger Fruchtwechsel ist wesentlich“ (verifiziert) | **3/3 Spanne** für 3 J. Pause (LfL ≥ 2, NDSU 2–3, AGES 3 J.) |

**Vorschlag:** `soil_persistence_years = 3`, `max_survival_years` ohne belegte Zahl (§7.2). Begründung: **Korrektur 2026-11-26** nach Betreiberentscheid 2026-11-22 (§7.12 Punkt 5): `soil_persistence_years` meint die Anbaupause, nicht die Rotationslänge. Die Quellen nennen Rotationen: LfL „maximal alle drei Jahre“ (≥ 2 J. Pause), NDSU „three- to four-year rotation“ (2–3 J. Pause), AGES „vierjähriger Fruchtwechsel“ (3 J. Pause). 3 J. Pause liegt in allen drei Angaben und gilt nach Betreiberentscheid als 3/3 (Belegart Spanne). Die frühere Bewertung (4 J., 3/3) las „Rotation“ als Pause. Bei 50 % Abnahme pro Jahr (2/3) bleiben nach 3 Jahren ≈ 12 % der Ausgangsdichte.

### R-001.3 Wurzelgallenälchen (`root_knot_nematode`, *Meloidogyne* spp.)

Im mitteleuropäischen Freiland praktisch nur *M. hapla*; *M. incognita* im Gewächshaus (LfL p_37956, verifiziert).

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | keine Jahreszahl gefunden | UC IPM: überdauert „primarily as eggs in the soil“, ohne Dauerangabe — [UC IPM Pest Note 7489](https://ipm.ucanr.edu/PMG/PESTNOTES/pn7489.html) (verifiziert) | — | — | **nicht belegt (0/3)** |
| wirksame Pause / Brache | 1–3 J. | UC IPM: „Fallowing for 1 year will lower root knot nematode populations enough … Two fallow years will lower nematode numbers even further“ (verifiziert) | LfL p_37956: „Durch zwei- bis dreijährigen Anbau von Getreide und Mais wird der Befall mit *M. hapla* reduziert“ (verifiziert) | NCDA Nema-Note 12: 2–3 Jahre Spargel, Schwingel, Zwiebel, Getreide oder Tagetes — [NCDA](https://ncagr.gov/nema-note-12/download) (Suchauszug) | **2/3** |

**Vorschlag:** `soil_persistence_years = 3`, `max_survival_years` leer (unbekannt). Begründung: oberer Rand von UC IPM und LfL. **Einschränkung:** die Pause wirkt nur mit Nichtwirten (Poaceae); weil fast alle Gemüsefamilien Wirte sind (R-002), sperrt der Hazard faktisch alle zweikeimblättrigen Gemüse — siehe offene Punkte.

### R-001.4 Mehlkrankheit/Weißfäule (`white_rot`, *Stromatinia cepivora* = *Sclerotium cepivorum*)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | ≥ 15 bis > 20 J. | UC IPM Onion & Garlic: „can survive in the soil for over 20 years“ — [UC IPM White Rot](https://ipm.ucanr.edu/agriculture/onion-and-garlic/White-Rot) (verifiziert) | RHS: „at least 15 years, though they will not always live this long“ — [RHS Onion white rot](https://www.rhs.org.uk/disease/onion-white-rot) (verifiziert) | ISIP Gemüsebroschüre 2026, Kap. 11 Zwiebel: Sklerotien keimen nur auf *Allium*-Wurzelausscheidungen, keine Jahresangabe — [ISIP Kap. 11](https://www.isip.de/resource/blob/858118/3626a75da6a2b1fd090e50bca6904f78/isip-gemuese-broschuere-2026-kapitel11-zwiebel-data.pdf) (verifiziert) | Zahl **2/3** |
| empfohlene Pause | keine Zahl gefunden | — | — | — | **nicht belegt (0/3)** |

Zusatzbefund: 40–60 % der Sklerotien zerfallen in den ersten zwei Monaten, danach bleibt der Rest stabil (Lincoln University, NZ, Dissertation — [core.ac.uk 35461642](https://core.ac.uk/download/35461642.pdf), Suchauszug). Zwei Jahre Überflutung tötete in Oregon alle Sklerotien — für Gärten irrelevant.

**Vorschlag:** `soil_persistence_years = 15`, `max_survival_years = 20`. Begründung: untere Grenze der verifizierten Spanne; Sklerotien keimen ohne *Allium* nicht, eine Pause „verbraucht“ sie also kaum. Praktische Folge: *Allium* in diesem Beet nur noch in Gefäßen mit frischem Substrat (R-004).

### R-001.5 Erbsen-Fußkrankheiten/Leguminosenmüdigkeit (`pea_root_rot`)

Ein Komplex: *Aphanomyces euteiches*, *Fusarium solani* f. sp. *pisi*, *F. oxysporum* f. sp. *pisi* (Welke), *Phoma*, *Rhizoctonia*, *Pythium* (FiBL 1667, verifiziert).

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | > 10 J. (*Aphanomyces*-Oosporen), F.-o.-pisi „more than 10 years“ | Saskatchewan Pulse Growers: *Aphanomyces* kann auch nach 12 J. persistieren — [Saskpulse Aphanomyces](https://saskpulse.com/resources/aphanomyces-root-rot-in-peas-and-lentils-in-western-canada) (Suchauszug) | MOFGA: Welke-Sporen „persist for more than 10 years“ — [MOFGA](https://www.mofga.org/?p=22024) (Suchauszug) | — | **nicht belegt (0/3 verifiziert)** |
| empfohlene Pause | 5–9 J. | FiBL Merkblatt 1667 „Leguminosenmüdigkeit“: Körnererbse weißblühend 6–9 J., buntblühend 5–7 J.; nach schlechtem Bodentest von Leguminosen „für den Zeitraum von 7 bis 8 Jahren dringend abzuraten“ — [FiBL 1667](https://www.fibl.org/fileadmin/documents/shop/1667-leguminosenmuedigkeit.pdf) (verifiziert) | UT W235, Tab. 1: Erbse Fusarium-Welke 5 J., Wurzelfäule („root canker“) 3–4 J. (verifiziert) | Sachsen Gartenbau „Erbse Fruchtfolge“: bis zu 7 J. — [gartenbau.sachsen.de](https://www.gartenbau.sachsen.de/download/Erbse_Fruchtfolge_12_(V11).pdf) (Suchauszug); LFA MV 6–9 J. (Suchauszug) | **2/3** verifiziert |

**Vorschlag:** `soil_persistence_years = 8`, `max_survival_years = 12`. Begründung: FiBL-Empfehlung nach positivem Müdigkeitstest (7–8 J.) und Mitte der Spanne 6–9 J. für weißblühende Erbsen. Liegt über der Familien-Pause Fabaceae 6 aus REQ-053 GP-FR-131, wie es für einen bestätigten Befall sein soll.

### R-001.6 Sklerotinia (`sclerotinia`, *Sclerotinia sclerotiorum*)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | 3–5 bis 10 J. | PNW Plant Disease Handbook (Brokkoli): „Sclerotia can survive three to five years in the soil“ — [PNW 2347](https://pnwhandbooks.org/node/2347) (verifiziert) | Review *Pathogens* 9:27 (2019): „remain dormant for up to 10 years“ — [PMC7168625](https://pmc.ncbi.nlm.nih.gov/articles/PMC7168625) (verifiziert) | AGES Weißstängeligkeit der Sonnenblume: bis zu zehn Jahre — [AGES](https://www.ages.at/pflanze/pflanzengesundheit/schaderreger-von-a-bis-z/weissstaengeligkeit-der-sonnenblume) (Suchauszug); LfL Rapskrankheiten: „über mehrere Jahre lebensfähig“ (Suchauszug) | **2/3** |
| empfohlene Pause | 3–8 J. (≥ 2 zur Reduktion) | PNW: „Rotate with non-hosts for three to eight years“ (verifiziert) | — | — | **nicht belegt (1/3)** |

**Vorschlag:** `soil_persistence_years = 5`, `max_survival_years = 10`. Begründung: oberer Rand der Extension-Angabe zur Überdauerung (3–5) und Untergrenze der Pausenempfehlung, die mit „fünf“ in der Mitte liegt. Wegen des sehr weiten Wirtskreises (R-002) siehe offene Punkte.

### R-001.7 Verticillium-Welke (`verticillium`, *V. dahliae*, *V. albo-atrum*)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | „many years“ bis 14–15 J. | UC IPM Lettuce: „can persist in the soil for an almost indefinite period of time“ — [UC IPM Lettuce Verticillium](https://ipm.ucanr.edu/agriculture/lettuce/verticillium-wilt/) (verifiziert); UC IPM Pepper: „up to 14 years in the absence of a host“ — [UC IPM r604100411](https://ipm.ucanr.edu/PMG/r604100411.html) (Suchauszug) | RHS: „reside in the soil for many years“; für Gehölze „grassing over the area for at least fifteen years“ — [RHS Verticillium wilt](https://www.rhs.org.uk/disease/verticillium-wilt) (verifiziert) | INRAE ephytia: Mikrosklerotien bis 15 J. (Suchauszug); LALLF MV: ca. 10 J. infektiös (Suchauszug) | „mehrjährig“ **2/3**; Zahl **0/3** verifiziert |
| empfohlene Pause | ≥ 3 J., 3–4 J. | UC IPM Potato: Rotation „of at least three years, with longer being better“ — [UC IPM Potato Verticillium](https://ipm.ucanr.edu/agriculture/potato/verticillium-wilt/) (verifiziert); UC IPM Lettuce: „rotating for 3 to 4 years with nonhosts (e.g. small grains)“ (verifiziert) — beides UC IPM, zählt als eine Quelle | — | — | **nicht belegt (1/3)** |

**Vorschlag:** `soil_persistence_years = 4`, `max_survival_years = 14`. Begründung: oberer Rand der UC-Empfehlung; alle Quellen betonen, dass Fruchtfolge allein Verticillium nicht beseitigt („not a curative disease management option“, UC IPM Potato). **Nur 1/3** — vor Code eine zweite und dritte Quelle (z. B. LWK, JKI, AHDB) beschaffen.

### R-001.8 Juglon (`juglone`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| Persistenz nach Fällung | „some years“ / „years“ / „five or more years“, solange Wurzeln zerfallen | Purdue HO-193: „Because decaying roots still release juglone, toxicity can persist for some years after a tree is removed“ — [Purdue HO-193](https://www.extension.purdue.edu/extmedia/ho/ho-193.pdf) (verifiziert) | Penn State Extension: „Juglone toxicity may persist for years after a tree is removed“ — [PSU Landscaping around walnuts](https://extension.psu.edu/landscaping-and-gardening-around-walnuts-and-other-juglone-producing-plants) (verifiziert) | UW–Madison Extension: „juglone can persist until the roots have decomposed, which can take five or more years“ — [UW Landscaping in spite of black walnut](https://hort.extension.wisc.edu/?p=4074) (verifiziert) | „mehrjährig“ **3/3**; Zahl „≥ 5 J.“ **1/3** |
| Gegenposition | wenige Monate | Iowa State: „in just a few months after removing the tree, most of the juglone is gone“ — [ISU Yard & Garden FAQ](https://yardandgarden.extension.iastate.edu/faq/how-long-does-juglone-last-landscape-after-removal-walnut) (verifiziert) | Schmidt 1988 (*J. Chem. Ecol.*): Bodenbakterien bauen Juglon rasch ab — [doi:10.1007/BF01012522](https://doi.org/10.1007%2Fbf01012522) (Suchauszug) | — | — |

Die Positionen widersprechen sich nur scheinbar: Juglon selbst wird im Boden rasch abgebaut, die **Wurzelreste** setzen aber so lange nach, bis sie zersetzt sind. Juglon ist an Wurzel, Knospen und Fruchtschalen gebunden; *Juglans nigra* und *J. cinerea* sind die Hauptverursacher, *J. regia* bildet weniger (PSU, verifiziert).

**Vorschlag:** `soil_persistence_years = 5` mit Pflicht-Hinweis „Wurzeln/Stubben entfernt?“; bei vollständig entferntem Wurzelwerk 1 Jahr (ISU). Belegstatus des Zahlenwerts nur **1/3** (UW); `max_survival_years` entfällt. Solange der Baum steht, gilt die Gefahr unbefristet (`confirmed_at` = Fällung, nicht Feststellung).

### Offene Punkte R-001

1. **Zwei Felder statt einem** (`soil_persistence_years` als Sperre, `max_survival_years` als Warnung) — Betreiberentscheid, weil H-10 bisher nur ein Feld kennt.
2. **Nicht dreifach belegt:** Halbwertszeit Kohlhernie, Pause Weißfäule, Überdauerung/Pause Wurzelgallenälchen, Überdauerung Erbsen-Komplex, Pause Sklerotinia, Zahlen Verticillium, Zahl Juglon. Nachrecherche bevorzugt in deutschen Landesquellen (LWK NRW/Niedersachsen, LTZ Augustenberg, JKI), deren PDFs hier nur als Suchauszug erreichbar waren.
3. **Sperre gegen Familie oder Art:** Für `root_knot_nematode` und `sclerotinia` würde eine Familiensperre fast alle Gemüse treffen. Vorschlag: diese beiden Hazards als **weiche** Gefahr (Strafe in `pest_risk`) statt H-10-Sperre führen — offen.

---

## R-002 Wirtskreise (`pathogen_hosts` → Familien)

**Fragestellung.** Welche Pflanzenfamilien (APG IV) sind Wirte der Erreger, und welche davon kommen im Katalog vor? Wo ist die Familie zu grob und eine Gattungs- oder Artliste nötig?

### Befundtabelle

| Erreger | Wirtsfamilien (im Katalog) | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|---------|---------------------------|----------|----------|----------|-------------|
| *Plasmodiophora brassicae* | **Brassicaceae** (alle Kohlarten, Rettich, Radies, Rauke, Senf; Zierpflanzen Goldlack, Levkoje; Unkräuter) | RHS Club root (verifiziert) | AHDB (verifiziert) | NC State (verifiziert) | **3/3** |
| — symptomlose Nebenwirte | Poaceae, *Trifolium pratense* (Fabaceae) als Wirte ohne Gallen; nicht als Zwischenfrucht nach Befall | NC State (verifiziert) | — | — | **nicht belegt (1/3)** |
| *Heterodera schachtii* | **Brassicaceae**, **Amaranthaceae** (*Beta*, *Spinacia*, Gänsefuß); > 200 Arten in 23 Familien | LfL p_37956: alle Kohlarten, Kohlrübe, Kohlrabi, Rettich, Radies, Rote Rübe, Spinat (verifiziert) | AGES: „Kreuzblütler (Brassicaceae) und Gänsefußgewächse (Chenopodiaceae)“ (verifiziert) | UNL G1906: „Chenopodiaceae and Cruciferae“; NDSU: Zuckerrübe, Rote Bete, Raps; Unkräuter u. a. Portulak (verifiziert) | **3/3** |
| — Nichtwirte („Neutralpflanzen“) | Poaceae, Solanaceae (Kartoffel), Fabaceae (Erbse, Klee), Asteraceae (Sonnenblume), Cannabaceae (Hanf) | AGES (verifiziert) | NDSU: wheat, barley, corn, bean, potato, alfalfa (verifiziert) | — | **2/3** |
| — Ausnahme | resistente Sorten von *Sinapis alba* und *Raphanus sativus* var. *oleiformis* senken die Population, obwohl Brassicaceae | LfL p_37956 (verifiziert) | — | — | 1/3 → **Sortenmerkmal, kein Familienwert** |
| *Meloidogyne* spp. (v. a. *M. hapla*) | nahezu alle zweikeimblättrigen Gemüse: **Solanaceae, Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Cucurbitaceae, Amaranthaceae, Rosaceae** (Erdbeere); *Allium* bei *M. hapla* Wirt | UC IPM Pest Note 7489, Tab. 1: beans, beets, carrots, celery, cole crops, cucumbers, eggplant, lettuce, melons, peas, peppers, potatoes, radish, spinach, squash, strawberry, tomatoes, turnips (verifiziert) | CDFA Pest Rating *M. hapla*: „nearly all temperate vegetables … Most grasses and cereals appear to be non-hosts“, > 500 Wirte — [CDFA](https://blogs.cdfa.ca.gov/Section3162/wp-content/uploads/2019/12/Meloidogyne-hapla.pdf) (verifiziert) | LfL p_37956: „sehr großer Wirtspflanzenkreis“, Getreide/Mais senken *M. hapla* (verifiziert) | **3/3** (Familienliste), Nichtwirt Poaceae **2/3** (CDFA, LfL) |
| *Sclerotinia sclerotiorum* | > 400 (bis > 600) Arten, „almost all dicotyledonous and some monocotyledonous plants“: **Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Solanaceae, Cucurbitaceae, Lamiaceae, Rosaceae** | PNW 2347: Brokkoli, Rettich, Bohne, Möhre, Erbse, Salat, Kartoffel, Paprika, Kürbisgewächse, Pastinake, Sonnenblume, Minze, Apfel, Kirsche (verifiziert) | *Pathogens* 2019 (verifiziert) | Bolton, Thomma & Nelson 2006, *Mol. Plant Pathol.* 7:1–16: > 400 Arten, überwiegend Dikotyle — [OUCI-Eintrag](https://ouci.dntb.gov.ua/works/4LvrLy39) (Suchauszug) | **2/3** |
| — Nichtwirt | Poaceae („thought to not be affected“) | PNW 2347 (verifiziert) | — | — | **nicht belegt (1/3)**; Review nennt einige Monokotyle als Wirte |
| *Verticillium dahliae* / *albo-atrum* | **Solanaceae** (Kartoffel, Tomate, Aubergine, Paprika) | RHS (verifiziert) | UC IPM Potato/Lettuce (verifiziert) | UC IPM Home Garden: Kartoffel, Paprika, Aubergine, Tomate, Kürbisgewächse — [UC IPM cuverticwilt](https://ipm.ucanr.edu/PMG/GARDEN/VEGES/DISEASES/cuverticwilt.html) (verifiziert, gleiche Institution) | **2/3** |
| | **Rosaceae** (Erdbeere; *Rosa*; Gehölze) | RHS (verifiziert) | UC IPM Lettuce: „artichoke, spinach, and strawberry“ (verifiziert) | Ökolandbau-Praxismerkblatt Erdbeere Wurzelfäulen — [oekolandbau.de](https://www.oekolandbau.de/fileadmin/redaktion/dokumente/Forschung/Praxismerkblaetter/06OE148-Erdbeeren_Wurzelfaeulen.pdf) (Suchauszug) | **2/3** |
| | **Cucurbitaceae** | RHS „cucurbits“ (verifiziert) | UC IPM Home Garden (verifiziert) | — | **2/3** |
| | **Asteraceae** (Salat, Artischocke, Chrysantheme; Sonnenblume) | UC IPM Lettuce (verifiziert) | RHS Chrysanthemum (verifiziert) | — | **2/3** |
| | **Amaranthaceae** (Spinat) | UC IPM Lettuce (verifiziert) | — | — | **nicht belegt (1/3)** |
| | **Brassicaceae** (Blumenkohl; v. a. *V. longisporum*) | UC IPM Lettuce nennt cauliflower (verifiziert) | — | — | **nicht belegt (1/3)** |
| | **Lamiaceae** (Minze) | nur Suchauszüge | — | — | **nicht belegt (0/3)** |
| — Nichtwirte | **Poaceae** (Getreide, Mais, Sorghum, Gräser); Koniferen | UC IPM Potato/Lettuce (verifiziert) | RHS „grasses are generally resistant“ (verifiziert) | — | **2/3**; Monokotyle allgemein inkl. Zwiebel (UC Leaflet 2703 via Missouri Botanical Garden) nicht abrufbar → **0/3** |
| *F. oxysporum* f. sp. *lycopersici* | **Solanaceae**, nur *Solanum lycopersicum* | UC IPM Tomato: „The fungus only infects tomato but exists as three races“ — [UC IPM Tomato Fusarium wilt](https://ipm.ucanr.edu/agriculture/tomato/fusarium-wilt/) (verifiziert) | INRAE ephytia: > 10 J. in Pflanzenresten bis 80 cm Tiefe — [ephytia Tomato](https://ephytia.inrae.fr/en/C/5217/Tomato-Biology-epidemiology) (Suchauszug) | — | **nicht belegt (1/3)** |
| *F. oxysporum* f. sp. *conglutinans* | **Brassicaceae** (Kohl, Blumenkohl, Brokkoli, Rosenkohl, Grünkohl, Kohlrabi, Rettich) | Cornell Vegetable Program: „Yellows can attack all members of the cabbage family“ — [Cornell Fusarium Yellows](https://www.vegetables.cornell.edu/pest-management/disease-factsheets/fusarium-yellows) (verifiziert) | PNW Handbook Cabbage Yellows — [PNW](https://pnwhandbooks.org/plantdisease/host-disease/cabbage-cauliflower-brassica-oleracea-yellows-fusarium-wilt) (Suchauszug) | OMAFRA: Persistenz ≥ 10 J. — [Ontario](https://www.ontario.ca/page/fungal-disease-cruciferous-crops) (Suchauszug) | **1/3** verifiziert |
| *F. oxysporum* f. sp. *pisi* | **Fabaceae**, nur *Pisum sativum* | UT W235 (Erbse, Fusarium-Welke 5 J., verifiziert) | NSW DPI: „Fop only affects peas“ — [NSW DPI](https://www.dpi.nsw.gov.au/__data/assets/pdf_file/0003/228036/Management-options-for-Fusarium-wilt-of-snow-peas.pdf) (Suchauszug) | MOFGA (Suchauszug) | Wirt: **1/3** verifiziert |
| *F. oxysporum* f. sp. *cepae* (Basalfäule) | **Amaryllidaceae**, nur *Allium* (Zwiebel, Knoblauch) | UC IPM Home Garden: „survives indefinitely in soil … rotate 3 to 4 years out of onions and garlic“ — [UC IPM basalrot](https://ipm.ucanr.edu/PMG/GARDEN/VEGES/DISEASES/basalrot.html) (verifiziert) | ISIP Kap. 11: „Wirtspflanzen: Allium-Arten“, „Anbaupause von ca. 5 Jahren“ (verifiziert) | UMass / USU: ≥ 4 J. bzw. 3–4 J. — [UMass](https://www.umass.edu/agriculture-food-environment/vegetable/fact-sheets/alliums-fusarium-basal-rot) (Suchauszug) | Wirt **2/3**; Pause 3–5 J. **2/3** |
| *F. oxysporum* f. sp. *cucumerinum* / *niveum* / *melonis* | **Cucurbitaceae**, je Forma eine Art (Gurke / Wassermelone / Melone); begrenzte Kreuzpathogenität | PNW Watermelon Fusarium wilt: überdauert „several years“ — [PNW](https://pnwhandbooks.org/plantdisease/host-disease/watermelon-citrullus-sp-fusarium-wilt) (Suchauszug) | Frontiers Plant Sci. 2023, 10.3389/fpls.2023.1116006: formae speciales wirtsspezifisch, „some cross pathogenicity … within the Cucurbitaceae“ (Suchauszug) | UT W235: Muskmelone Fusarium-Welke 5 J. (verifiziert) | **nicht belegt (1/3)** |
| *F. oxysporum* an Kartoffel | — kein *F.-oxysporum*-Welke-Erreger der Kartoffel gefunden; Kartoffel-Fusariosen (Trockenfäule, *F. sambucinum*/*F. solani*) sind knollen- und lagerbürtig | — | — | — | **nicht belegt (0/3)**; Vorschlag: kein Hazard |
| *Stromatinia cepivora* | **Amaryllidaceae**, nur *Allium* (Zwiebel, Lauch, Knoblauch, Schnittlauch); *Clivia*/*Hippeastrum* nicht betroffen | UC IPM (verifiziert) | RHS (verifiziert) | ISIP Kap. 11: *A. cepa, A. porrum, A. sativum* (verifiziert) | **3/3** |
| *pea_root_rot*-Komplex | **Fabaceae**: *Pisum*, *Lens*, *Vicia faba* stark; Klee als Vorfrucht ungünstig; *Glycine max* trägt nicht bei | FiBL 1667 (verifiziert) | Saskpulse: Ackerbohne, Soja, Kichererbse keine *Aphanomyces*-Wirte (Suchauszug) | — | **nicht belegt (1/3)** für die Artliste |
| Juglon-empfindlich | *Solanum lycopersicum, S. tuberosum, S. melongena, Capsicum annuum* (Solanaceae); *Brassica oleracea* (Kohl); *Asparagus officinalis*; *Rheum rhabarbarum*; *Malus, Pyrus, Rubus fruticosus* (Rosaceae); *Vaccinium* (Ericaceae); *Fragaria* (nur UW) | Purdue HO-193: „Vegetables: asparagus, cabbage, eggplant, pepper, potato, rhubarb, tomato. Fruits: apple, blackberry, blueberry, pear.“ (verifiziert) | UW–Madison (gleiche Liste + strawberry, verifiziert, **nicht unabhängig** von Purdue) | — | **nicht belegt (1/3)** |
| Juglon-tolerant | Zwiebel, Rote Bete, Kürbis/Melone, Möhre, Pastinake, Bohne, Mais; Kirsche, Pflaume, Pfirsich, Quitte, Schwarze Himbeere | PSU Extension (verifiziert) | — | — | **nicht belegt (1/3)** |

### Abbildung auf Katalogfamilien — Folgerungen

1. **Familie reicht** für: Kohlhernie (Brassicaceae), Rübenzystennematode (Brassicaceae + Amaranthaceae), Weißfäule (Gattung *Allium*, nicht ganze Amaryllidaceae).
2. **Gattung/Art nötig** für alle *F. oxysporum*-formae speciales (je eine Kulturart), für den Erbsen-Komplex (*Pisum*, *Lens*, *Vicia*; nicht *Glycine*, *Phaseolus* offen) und für **Juglon**. Juglon ist ausdrücklich **keine Familiensperre**: in Rosaceae sind Apfel, Birne, Brombeere empfindlich, Kirsche, Pflaume, Pfirsich und Schwarze Himbeere tolerant (Purdue vs. PSU). Der REQ-054-Text „juglone sperrt Solanaceae, Rosaceae-Beeren u. a.“ ist für Rosaceae zu grob. **Vorschlag:** `pathogen_hosts` erlaubt neben `families[]` auch `genera[]` und `species_keys[]`; H-10/H-11 prüfen die feinste vorhandene Ebene.
3. **Breite Wirtskreise** (Meloidogyne, Sclerotinia, Verticillium) betreffen 6–8 der 10 Gemüsefamilien des Katalogs. Gemeinsamer Nichtwirt laut Quellen: **Poaceae** (Meloidogyne 2/3, Verticillium 2/3, Sclerotinia 1/3). Im Katalog sind das Mais und Getreide — für Hausgärten selten. Ein harter Ausschluss nach H-11 läuft hier auf „Beet nur für Poaceae und *Allium*“ hinaus.
4. **Gründüngung:** *Sinapis alba* und Ölrettich sind Wirte für *H. schachtii* und *P. brassicae* — außer nematodenresistenten Sorten (nur gegen *H. schachtii*, LfL). REQ-054 K-002 „Senf/Ölrettich sind Wirt“ stimmt also für Normalsorten; ein Sortenmerkmal `nematode_resistant` fehlt im Modell. *Tagetes* (Asteraceae) wirkt gegen *Pratylenchus* und teils *Meloidogyne* (LfL, NCDA) — Asteraceae ist aber zugleich Sclerotinia- und Verticillium-Wirt.

### Offene Punkte R-002

1. Granularität `pathogen_hosts` (Familie/Gattung/Art) — Modellentscheid.
2. Dreifachbeleg fehlt für: Verticillium an Amaranthaceae, Brassicaceae, Lamiaceae; alle formae speciales außer *cepae*; Sclerotinia-Nichtwirt Poaceae; Juglon-Artliste (unabhängige zweite und dritte Quelle).
3. Ob *Phaseolus vulgaris* zum Erbsen-Komplex zählt (Bohnenrassen von *Aphanomyces*), ist offen.

---

## R-003 Ist das Nachpflanzen derselben Kultur in derselben Saison nach nicht bodenbürtigem Ausfall fruchtfolgeneutral?

**Fragestellung.** REQ-053 v1.37 lässt abiotisch und mechanisch ausgefallene Pflanzen bei der Nachpflanz-Prüfung unberücksichtigt. Ist das agronomisch richtig, und wo liegen die Ausnahmen?

### Befundtabelle

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|---------|----------|----------|----------|-------------|
| Fruchtfolge zielt in erster Linie auf **bodenbürtige** Erreger; die Pausenlänge richtet sich nach deren Überdauerung | UT W235: „Rotation length should be based on the amount of time soil-borne pathogens remain viable in the field“ (verifiziert) | — | — | **nicht belegt (1/3)** |
| Für **Blattkrankheiten und Blattschädlinge** genügen 2 Jahre Pause | UT W235: „Two years is considered enough time to reduce the incidence of foliar diseases and insect pests“ (verifiziert) | — | — | **nicht belegt (1/3)** |
| *Alternaria solani* (Dürrfleckenkrankheit) überdauert in **Ernteresten** ≥ 1 Jahr; 2–3 J. Pause empfohlen | Oklahoma State: „resistant spores … capable of persisting for one year and probably longer“ — [OSU](https://extension.okstate.edu/programs/digital-diagnostics/plant-diseases/early-blight-of-tomato) (Suchauszug) | UMaine Bulletin 5087 — [UMaine](https://extension.umaine.edu/ipm/?p=4592) (Suchauszug) | UConn IPM: Fläche 2–3 J. ohne Tomate/Kartoffel/Aubergine — [UConn](https://ipm.cahnr.uconn.edu/early-blight-management-in-fresh-market-tomatoes/) (Suchauszug) | **0/3 verifiziert** (3 übereinstimmende Suchauszüge) |
| *Phytophthora infestans* ist obligat biotroph: überdauert **nicht** im Boden oder in totem Pflanzenmaterial (Nordamerika) | UMaine Bulletin #2427: „it cannot live in soil or dead plant debris“ und „does not overwinter in the soil under our conditions“ — [UMaine #2427](https://extension.umaine.edu/potatoes/wp-content/uploads/sites/49/2012/03/homeowner-late-blight-1.pdf) (verifiziert) | Cornell (McGrath): „an obligate pathogen unlike the early blight pathogen that can survive between crops on infested debris“ — [Cornell Brochure](https://apps.web.maine.gov/dacf/php/gotpests/diseases/factsheets/late-blight-brochure-cornell.pdf) (Suchauszug) | — | **nicht belegt (1/3)** |
| **Ausnahme Mitteleuropa:** *P. infestans* kann als **Oospore im Boden** überwintern; Hauptquelle bleiben Knollen in Erde, Kompost, Abfallhaufen | TLLLR Thüringen, Merkblatt Haus- und Kleingarten „Kraut- und Braunfäule“ (2020): „in Form von Überdauerungsorganen (Oosporen) kann der Erreger den Winter im Boden überstehen“ — [ISIP/TLLLR](https://isip.de/resource/blob/491610/5ef61618a744bc2a8cab49c160564b0b/kraut-und-braunfaeule-data.pdf) (verifiziert) | Kartoffel-Beratungsblatt 2016: Dauersporen bis 4 J. — Quelle laut Suche [lw-heute.de](https://www.lw-heute.de/mediaarchiv/grab_pic.php?id=33281) (Suchauszug) | — | **nicht belegt (1/3)** |

### Bewertung

- **Abiotischer Ausfall** (Frost, Hitze, Trockenheit, Vernachlässigung) und **mechanischer Ausfall** bringen kein Inokulum in den Boden. Die Nährstoffentnahme einer früh eingegangenen Pflanze ist gering. Agronomisch ist das Nachpflanzen derselben Kultur in derselben Saison daher **fruchtfolgeneutral**. Das ist eine Ableitung aus dem Zweck der Fruchtfolge (UT W235), kein direkt dreifach belegter Satz: **nicht belegt (1/3)**. Die geltende Regel aus REQ-053 v1.37 widerspricht dem nicht.
- **Ausnahme Staunässe (`waterlogging`).** Staunässe begünstigt bodenbürtige Wurzelfäulen (*Pythium*, *Phytophthora*); FiBL 1667 nennt hohe Bodenfeuchte und geringen Sauerstoff als Förderfaktor der Leguminosenmüdigkeit (verifiziert). Ein Ausfall durch Staunässe kann also eine Wurzelfäule verdecken. Vorschlag: `waterlogging` bleibt abiotisch, die UI fragt aber „Wurzeln braun/faulig?“ und bietet bei Ja `disease_soil` an.
- **Blattkrankheit (`disease_foliar`).** Kein Fruchtfolge-Thema im engeren Sinn, aber **Rückstände** zählen: Erreger wie *Alternaria solani* überdauern auf Ernteresten am Beet. Für die Nachpflanzung derselben Saison ist der Infektionsdruck ohnehin über die Luft und die Nachbarpflanzen vorhanden; entscheidend ist das **Entfernen** der kranken Pflanze. Vorschlag: `INFO`-Hinweis „Pflanzenreste entfernen, nicht kompostieren“, keine Rotationswarnung. Für die **Folgejahre** gilt die normale Familien-Pause (H-01), die bei Solanaceae mit 4 J. über den 2–3 J. für *Alternaria* liegt.
- ***P. infestans*:** in der Saison kein Bodenproblem; über den Winter in Mitteleuropa Oosporen möglich (TLLLR). Durch die Familien-Pause Solanaceae 4 J. abgedeckt; kein eigener Hazard nötig.
- **Blattschädling (`pest_foliar`).** Neutral für die Nachpflanzung. Ausnahme: Schädlinge, deren Larven oder Puppen im Boden sitzen (z. B. Kohlfliege, Drahtwurm), gehören zu `pest_soil` — Quellenlage hier nicht geprüft.

### Offene Punkte R-003

1. Dreifachbeleg fehlt für alle vier Teilaussagen; am dringendsten für „Blattkrankheit: Rückstände entfernen reicht innerhalb der Saison“ (Literatur zu *Alternaria*, *Septoria lycopersici*, Falscher Mehltau an Salat/Gurke).
2. `pest_soil`-Beispiele und deren Überdauerung sind nicht recherchiert.

---

## R-004 Vorzeitige stressbedingte Seneszenz, „dieselbe Saison“ und frisches Substrat

### R-004.1 Ist vorzeitige Seneszenz ein Ausfall?

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|---------|----------|----------|----------|-------------|
| Schossen ist eine **physiologische** Reaktion auf Tageslänge, Kälte-/Hitzeperioden, Trockenheit und Stress — keine Krankheit | RHS „Bolting in vegetables“: „triggered either by cold spells or by the changes in day length“; „Dry soil can also encourage bolting, particularly with cauliflower, rocket and spinach“ — [RHS](https://www.rhs.org.uk/advice/profile?PID=262) (verifiziert) | Fine Gardening (USDA-Versuche: Tageslänge löst Schossen bei Salat aus) — [Fine Gardening](https://finegardening.com/?p=76904) (Suchauszug, keine Fachquelle) | — | **nicht belegt (1/3)** |
| Vorzeitige Seneszenz kann **Symptom eines bodenbürtigen Erregers** sein (Kartoffel-Frühabsterben durch Verticillium), leicht mit normaler Abreife zu verwechseln | UC IPM Potato: „Wilt causes early senescence of plants“ (verifiziert) | MSU Extension E2576: Früh-Absterben wird mit normaler Seneszenz verwechselt; sichere Diagnose nur durch Isolierung — [MSU E2576](https://sanweb.lib.msu.edu/DMC/extension_publications/e2576/E2576-1995.PDF) (Suchauszug) | — | **nicht belegt (1/3)** |

**Bewertung.** Agronomisch ist vorzeitige Seneszenz ein **Ausfall** (die Kultur liefert nicht mehr), aber kein einheitlicher: Schossen durch Tageslänge oder Hitze ist abiotisch, Frühabsterben durch Welkeerreger ist bodenbürtig. REQ-053 §11.3 erfasst das bereits richtig als `died` mit Ursache. Folgerung für das Nachpflanz-Angebot:

- Ursache `heat`, `drought`, `frost` → Klasse `abiotic` → **kein Rotationshinweis** (REQ-053 v1.37 bleibt).
- Schossen ist in `termination_cause` nicht abbildbar. Vorschlag: neuer Wert `bolting` → `abiotic`; bis dahin wählt der Nutzer `heat`/`drought` oder `unknown`.
- Welke/Vergilben von unten nach oben bei Solanaceae, Brassicaceae, Cucurbitaceae, Rosaceae (Erdbeere) ist **kein** Abiotik-Fall. Die UI soll bei `unknown` und diesen Familien fragen „Welke trotz feuchter Erde, Gefäße im Stängel braun?“ und bei Ja `disease_soil` anbieten.

### R-004.2 Was heißt „dieselbe Saison“?

Keine Fachquelle definiert „dieselbe Saison“ für den Zweck der Nachpflanz-Prüfung: **nicht belegt (0/3)**. Fachlich zählt bei der Fruchtfolge die **Kulturfolge auf der Fläche** (Vor-, Haupt-, Nachkultur), nicht das Kalenderjahr (UT W235 rechnet in „Yrs w/o Susceptible Crop“, verifiziert; REQ-054 §5.5 hat für H-01 bewusst Kalenderjahre gewählt).

Vorschlag (Planungskonvention, Betreiberentscheid):

| Fall | Regel |
|------|-------|
| Sommerkultur, Ausfall und Nachpflanzung im selben Kalenderjahr | dieselbe Saison (heutige Regel, REQ-053 v1.37) |
| Winterkultur (z. B. Knoblauch, Wintersteckzwiebel, Feldsalat), gepflanzt im Herbst Y, ausgefallen im Frühjahr Y+1 | dieselbe Saison, wenn die Nachpflanzung **innerhalb des Anbaufensters der ersetzten Pflanze** liegt (`planted_on` … erwartetes Ende aus §5.5 Nr. 5). Die Kalenderjahr-Grenze allein ist hier falsch: eine im März ersetzte Herbstpflanzung würde sonst als Vorkultur gezählt. |
| Mehrjährige Kultur | nur das Ausfalljahr (heutige Regel: Vorjahre derselben Pflanze zählen weiter) |

Technisch: Kriterium „Nachpflanzdatum ≤ erwartetes Ende des Anbaufensters der ersetzten Pflanze“ statt „gleiches UTC-Kalenderjahr“.

### R-004.3 Hebt frisches Substrat in Kübel oder Hydrokultur die Bodenwarnung auf?

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|---------|----------|----------|----------|-------------|
| Sauberes Substrat in Hochbeet/Gefäß umgeht verseuchten Gartenboden | NC State Clubroot: Hochbeete „allow for the use of clean soil“ (verifiziert) | UW–Madison/Iowa State zu Juglon: Hochbeete mit sauberer Erde als Ausweg (Suchauszug) | — | **nicht belegt (1/3)** |
| Substrat nach **kranken** Pflanzen nicht wiederverwenden (oder sterilisieren); nach gesunden ist Wiederverwendung in Ordnung | LSU AgCenter — [LSU](https://www.lsuagcenter.com/articles/page1671725785873) (Suchauszug) | Oklahoma State Extension 2023 — [OSU](https://extension.okstate.edu/articles/2023/reusing_potting_soil.html) (Suchauszug) | University of Minnesota Extension (Suchauszug) | **0/3 verifiziert** (3 übereinstimmende Suchauszüge) |
| Hydrokultur ist **nicht** automatisch frei von Wurzelerregern: in rezirkulierenden Systemen verbreiten sich *Pythium* und *Fusarium* über die Nährlösung; Desinfektion nötig | University of Kentucky E706 — [UK E706](https://greenhousehort.ca.uky.edu/sites/greenhousehort.ca.uky.edu/files/E706.pdf) (Suchauszug) | Stanghellini, USDA-ARS-Poster — [USDA](https://www.ars.usda.gov/ARSUserFiles/02060000/FNRI2009/FNRI_2009_Posters/Stanghellini-FNRIWP.pdf) (Suchauszug) | Univ. Pretoria, Dissertation — [UP Repository](https://repository.up.ac.za/handle/2263/24109) (Suchauszug) | **0/3 verifiziert** |

**Bewertung und Vorschlag.** Fachlich plausibel und in den Suchauszügen einhellig, aber in dieser Recherche nur 1/3 verifiziert:

- Ein `planter` (Kübel) oder `growing_medium_kind ∈ {potting_mix, soilless}` mit **frisch eingefülltem** Substrat trägt keine Bodengefahr des Beets: `soil_hazards[]` hängt am Substrat, nicht am Ort. Braucht ein Datum `substrate_replaced_on`; liegt es nach `confirmed_at`, ist der Hazard für diesen Behälter aufgehoben.
- **Wiederverwendetes** Substrat nach einem bodenbürtigen Ausfall behält den Hazard.
- **Hydrokultur:** Bodengefahren aus der REQ-054-Liste (Kohlhernie, Nematoden, Weißfäule …) entfallen; Wurzelerreger der Nährlösung (*Pythium*, *Fusarium*) bleiben bis zur Reinigung des Systems. Vorschlag: `disease_soil` in Hydrokultur setzt **keinen** `soil_hazards[]`-Eintrag, sondern einen Hinweis „System reinigen und desinfizieren vor dem Nachpflanzen“.
- Hochbeet auf gewachsenem Boden: Wurzeln erreichen den Unterboden; kein Aufheben, höchstens Abschwächen — **nicht belegt (0/3)**.

### Offene Punkte R-004

1. Neuer `termination_cause`-Wert `bolting` (REQ-053-Änderung).
2. Saisondefinition über das Anbaufenster statt Kalenderjahr — Betreiberentscheid.
3. Substrat-Aussagen und Hydrokultur: Volltexte von LSU, OSU, UK E706 lesen, um auf 3/3 zu kommen.

---

## 5. Vorschlag Ursachenklasse `failure_cause_class`

Wertebereich wie beauftragt: `abiotic | pest_foliar | pest_soil | disease_soil | disease_foliar | mechanical | unknown`.

**Grundsatz:** `termination_cause` (REQ-053 §11.3) bleibt, was der Nutzer beobachtet hat; `failure_cause_class` ist die daraus abgeleitete oder vom Nutzer präzisierte Klasse, die der Nachpflanz-Hinweis und H-10 lesen. Ist die Klasse leer (Altdaten), gilt das heutige Verhalten aus `termination_cause` unverändert weiter.

| `termination_cause` | Vorbelegung `failure_cause_class` | Nutzer kann ändern zu | Nachpflanz-Hinweis (gleiche Familie, gleiche Saison) |
|---------------------|-----------------------------------|------------------------|-------------------------------------------------------|
| `frost` | `abiotic` | — | keiner |
| `heat` | `abiotic` | `disease_soil` (Welke-Rückfrage, R-004.1) | keiner |
| `drought` | `abiotic` | `disease_soil` (Welke trotz feuchter Erde) | keiner |
| `waterlogging` | `abiotic` | `disease_soil` (Wurzeln braun/faulig, R-003) | keiner |
| `neglect` | `abiotic` | — | keiner |
| `mechanical` | `mechanical` | — | keiner |
| `pest` | **keine** Vorbelegung, Pflichtauswahl | `pest_foliar` / `pest_soil` | `pest_foliar`: keiner · `pest_soil`: `WARNING` (überstimmbar) |
| `disease` | **keine** Vorbelegung, Pflichtauswahl | `disease_foliar` / `disease_soil` | `disease_foliar`: `INFO` „Pflanzenreste entfernen, nicht kompostieren“ · `disease_soil`: `WARNING`; bei bestätigtem Erreger der Liste Angebot „als Bodengefahr des Beets übernehmen“ → `soil_hazards[]` |
| `unknown` / leer | `unknown` | jede Klasse | `INFO` (heutiges Verhalten); bei Familien mit Welke-Risiko (Solanaceae, Brassicaceae, Cucurbitaceae, Rosaceae) die Welke-Rückfrage |
| *(neu, R-004)* `bolting` | `abiotic` | — | keiner |

**Wann wird aus `disease_soil` ein `soil_hazards[]`-Eintrag?** Nur mit benanntem Erreger aus der Hazard-Liste und `confirmed = true` (Laborbefund, Beratung oder eindeutiges Schadbild wie Kohlhernie-Wucherungen oder Mehlkrankheit-Myzel mit Sklerotien). `source` hält fest, wer bestätigt hat. Ein unbestätigtes `disease_soil` bleibt eine überstimmbare Warnung am Nachpflanz-Vorgang und erzeugt keine Sperre (D-09 aus REQ-053 bleibt gewahrt). Hydrokultur: kein Eintrag (R-004.3).

**Rückwärtskompatibilität:** `disease`/`pest` ohne Klasse behalten `WARNING` wie seit v1.37. Keine Migration bestehender Pflanzen nötig.

---

## 6. Maschinennahe Zusammenfassung

### 6.1 Bodengefahren

Belegstatus nach der Nachrecherche vom 2026-11-17 (§7). Die Vorschlagswerte sind unverändert; welche davon 3/3 erreichen, steht in §7.11.

| hazard | soil_persistence_years (Vorschlag) | max_survival_years (Vorschlag, informativ) | affected_families (Ebene) | Belegstatus Sperrdauer / Überdauerung / Wirte |
|--------|-----------------------------------|---------------------------------------------|---------------------------|-----------------------------------------------|
| `clubroot` | 7 | 20 (3/3 nur für 15) | Brassicaceae (Familie) | 3/3 Spanne · 3/3 (≥ 15) · 3/3 |
| `cyst_nematode` | 3 (Korrektur 2026-11-26, vorher 4) | — (vorher 12) | Brassicaceae, Amaranthaceae (Familie; Ausnahme resistente Zwischenfruchtsorten) | 3/3 Spanne · widersprüchlich (5–> 12) · 3/3 |
| `root_knot_nematode` | 3 | — (unbekannt) | Solanaceae, Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Cucurbitaceae, Amaranthaceae, Rosaceae; *Allium* bei *M. hapla* (Familie; Nichtwirt Poaceae) | nur „≥ 1 J.“ 3/3 · widersprüchlich · 3/3 |
| `white_rot` | — (FiBL 8–10 J., 1/3; die frühere 15 ist die Überdauerung, Korrektur 2026-11-26) | 20 (3/3 nur für 15) | Amaryllidaceae, nur Gattung *Allium* | 1/3 · 3/3 (≥ 15) · 3/3 |
| `pea_root_rot` | 8 | 12 | Fabaceae: *Pisum*, *Lens*, *Vicia* (Gattung); *Glycine* und *Vicia faba* (für *Aphanomyces*) ausgenommen, *Phaseolus* ausgenommen | widersprüchlich (3–10) · 3/3 (≥ 10) · 3/3 |
| `sclerotinia` | 5 | 10 | Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Solanaceae, Cucurbitaceae, Lamiaceae, Rosaceae (Familie; Nichtwirt Poaceae 3/3) | 3/3 Spanne · 3/3 (4–10) · 2/3 |
| `verticillium` | 4 | 14 (3/3 nur für 10) | Solanaceae, Rosaceae, Cucurbitaceae, Asteraceae (2/3); Amaranthaceae (Spinat), Brassicaceae, Lamiaceae (*Mentha*) (3/3, §7.7) (Familie; Nichtwirt Poaceae widersprüchlich) | 3/3 Spanne · 3/3 (≥ 10) · 3/3 (nach §7.7) |
| `juglone` | 5 (1 bei entferntem Wurzelwerk; unbefristet solange Baum steht) | — | Art-/Gattungsliste: *Solanum lycopersicum, S. tuberosum, S. melongena, Capsicum annuum, Brassica oleracea, Asparagus officinalis, Rheum rhabarbarum, Malus, Pyrus, Rubus fruticosus, Vaccinium* (keine Familiensperre) | widersprüchlich · 2/3 („mehrjährig“) · 3/3 nur Solanaceae-Arten |

### 6.2 Wirtskreise

| pathogen | host_families (Katalog, APG IV) | Ebene | Belegstatus |
|----------|----------------------------------|-------|-------------|
| *Plasmodiophora brassicae* | Brassicaceae | Familie | 3/3 |
| *Heterodera schachtii* | Brassicaceae, Amaranthaceae | Familie | 3/3 |
| *Meloidogyne* spp. (*hapla*, *incognita*) | Solanaceae, Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Cucurbitaceae, Amaranthaceae, Rosaceae, Amaryllidaceae (*M. hapla*) | Familie | 3/3 (Liste), Nichtwirt Poaceae 2/3 |
| *Sclerotinia sclerotiorum* | Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Solanaceae, Cucurbitaceae, Lamiaceae, Rosaceae | Familie | 2/3 |
| *Verticillium dahliae* / *albo-atrum* / *longisporum* | Solanaceae, Rosaceae, Cucurbitaceae, Asteraceae (2/3); Amaranthaceae (Spinat), Brassicaceae, Lamiaceae (*Mentha*) (3/3) | Familie | 2/3 bzw. 3/3 |
| *Stromatinia cepivora* | Amaryllidaceae → *Allium* | Gattung | 3/3 |
| *F. oxysporum* f. sp. *lycopersici* | Solanaceae → *Solanum lycopersicum*, *S. melongena*, weitere *Solanum* | Gattung | 3/3 (Widerspruch UC IPM) |
| *F. oxysporum* f. sp. *conglutinans* | Brassicaceae → alle *B. oleracea*-Formen; *Raphanus* widersprüchlich | Art | 3/3 (Widerspruch UC IPM) |
| *F. oxysporum* f. sp. *pisi* | Fabaceae → *Pisum sativum* | Art | 3/3 |
| *F. oxysporum* f. sp. *cepae* | Amaryllidaceae → *Allium cepa*, *A. sativum* | Gattung | 2/3 |
| *F. oxysporum* f. sp. *cucumerinum* / *niveum* / *melonis* | Cucurbitaceae → *Cucumis sativus* / *Citrullus lanatus* / *Cucumis melo* | Art | 3/3 |
| *F. oxysporum* an Kartoffel | — (kein Hazard) | — | 0/3 |
| Erbsen-Fußkrankheitskomplex | Fabaceae → *Pisum*, *Lens*; *Medicago*, *Trifolium pratense* als Wirt; ohne *Phaseolus*, *Glycine*, *Vicia faba* | Gattung | 3/3 (*Glycine* 2/3, *Vicia faba* widersprüchlich) |
| Juglon (*Juglans nigra*, *J. cinerea*, schwächer *J. regia*) | siehe Artliste 6.1 | Art | 3/3 für die vier Solanaceae-Arten, übrige 1/3 |

### 6.3 Nicht dreifach belegte Werte (Stand nach Nachrecherche #3005)

Ursprüngliche Kurzliste (2026-11-15): Halbwertszeit Kohlhernie; Pausenempfehlung Kohlhernie (2/3); Überdauerung Rübenzystennematode als Zahl; Überdauerung Wurzelgallenälchen; Pause Weißfäule; Überdauerung und Wirtsliste Erbsen-Komplex; Pause Sklerotinia; alle Zahlen und drei Wirtsfamilien bei Verticillium; alle *F.-oxysporum*-formae speciales außer *cepae*; Juglon-Zahl und Artliste; sämtliche Aussagen in R-003 und R-004.

| Wert | Status vorher | Status nach #3005 | Kernaussage | Abschnitt |
|------|---------------|-------------------|-------------|-----------|
| Kohlhernie, Halbwertszeit | 1/3 | **3/3** | 3,5–3,6 J. (mögliche gemeinsame Primärquelle Wallenhammar 1996) | §7.1 |
| Kohlhernie, Pause nach Befall | 2/3 | **3/3 Spanne** | ≥ 4 / 7 / 7–10 J.; 7 J. in allen Angaben | §7.1 |
| Rübenzystennematode, Überdauerung als Zahl | 1/3 | **widersprüchlich** | 5–6 J. bis > 12 J.; „≥ 5 J.“ 3/3 | §7.2 |
| Wurzelgallenälchen, Überdauerung | 0/3 | **widersprüchlich**, Zahl 1/3 | bis 2 J. (AGES) gegen „mehrere Jahre“ | §7.3 |
| Wurzelgallenälchen, Pause | 2/3 | **3/3 nur für ≥ 1 J.** | 1–3 J. Nichtwirt; 3 J. nur 1/3 | §7.3 |
| Weißfäule, Pause | 0/3 | **1/3** | FiBL 8–10 J.; übrige „lange“, ohne Zahl | §7.4 |
| Weißfäule, Überdauerung | 2/3 | **3/3** | ≥ 15 J. (bis > 25) | §7.4 |
| Erbsen-Komplex, Überdauerung | 0/3 | **3/3** | ≥ 10 J. (*Aphanomyces*, *F. o.* f. sp. *pisi*) | §7.5 |
| Erbsen-Komplex, Wirtsliste | 1/3 | **3/3** | *Pisum*, *Lens*, Luzerne, Rotklee; ohne *Phaseolus* (eigene Pathotypen, 3/3); *Vicia faba* widersprüchlich | §7.5 |
| Erbsen-Komplex, Pause | 2/3 | **widersprüchlich** | 3–10 J., kein gemeinsamer Wert; 8 J. 2/3 | §7.5 |
| Sklerotinia, Pause | 1/3 | **3/3 Spanne** | 2–8 J.; 5 J. in drei Angaben | §7.6 |
| Sklerotinia, Nichtwirt Poaceae | 1/3 | **3/3** | Getreide/Gräser erkranken nicht | §7.6 |
| Verticillium, Überdauerung | 0/3 | **3/3** | ≥ 10 J. (LfL widerspricht) | §7.7 |
| Verticillium, Pause | 1/3 | **3/3 Spanne** | Gemüse 3–5 J.; Erdbeere 3–5 J. | §7.7 |
| Verticillium, Amaranthaceae / Brassicaceae / Lamiaceae | 1/3, 1/3, 0/3 | **3/3** | Spinat, Kohlarten, *Mentha*; Basilikum/Salbei 0/3 | §7.7 |
| Verticillium, Nichtwirt Poaceae | 2/3 | **widersprüchlich** | symptomlose Besiedlung belegt | §7.7 |
| *F. oxysporum* formae speciales außer *cepae*, Wirte | 1/3 | **3/3** (mit Gegenstimmen) | *lycopersici* Solanaceae, *conglutinans* *B. oleracea*, *pisi* nur Erbse, Kürbis-formae je eine Art | §7.8 |
| *F. oxysporum* formae speciales, Überdauerung/Pause | 1/3 | **höchstens 2/3** | „viele Jahre“ 3/3, Zahlen nicht | §7.8 |
| Juglon, Dauer nach Fällung | 1/3 („mehrjährig“ 3/3) | **widersprüchlich**, „mehrjährig“ nur noch 2/3 | Penn State nennt den Satz nicht mehr; Iowa State: wenige Monate | §7.9 |
| Juglon, Artliste | 1/3 | **3/3** für Tomate, Kartoffel, Aubergine, Paprika (Beobachtung); übrige 1/3 | | §7.9 |
| R-003, R-004 | ≤ 1/3 | **3/3** für R-003 a–e, R-004.1 a–b, R-004.3 a, b, d, e; Rest 0/3–1/3 oder widerlegt | | §7.10 |

Werte, die mit F-18 eingetragen werden können, und die widersprüchlichen Werte: §7.11.

---

## 7. Nachrecherche #3005 (2026-11-17)

**Methode.** Wie §0, mit einer Verschärfung: jede hier gezählte Quelle wurde am 2026-11-17 im Volltext abgerufen (HTML als Text, PDF per `pdftotext`) und die zitierte Stelle im Text gesucht. Quellen aus der Recherche vom 2026-11-15, die damals verifiziert wurden, zählen weiter, wenn die Aussage dort stand (Ausnahme Penn State, §7.9). Sekundärquellen, die eine bereits gezählte Primärquelle wiedergeben, und mehrere Seiten derselben Institution zählen als eine Quelle. Nicht abrufbare Seiten (Bot-Schutz, HTTP 404, Scan-PDF ohne Textschicht) zählen nicht.

### 7.1 Kohlhernie (`clubroot`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| Halbwertszeit der Dauersporen | 3,5–3,6 J. | AHDB: „half-life of approximately 3.5 years“ — [AHDB Clubroot management in OSR](https://ahdb.org.uk/knowledge-library/clubroot-management-in-oilseed-rape-cropping-factors) | Dixon 2009, *J. Plant Growth Regul.*: „a half life of at least 3.6 years and some spores may exist for at least 18 years“ (Wallenhammar 1996) — [Dixon 2009 (Univ. Reading, PDF)](https://centaur.reading.ac.uk/66432/1/Journal%20of%20Plant%20Growth%20Regulation%20EDITED%20DIXON%20Plasmodiophora%20brassicae%20in%20soil%20and%20host%20environments.pdf) | Weimar (DLR Rheinhessen-Nahe-Hunsrück), LW 29/2013, S. 20: Dauersporen, „die bei einer Halbwertszeit von 3,6 Jahren dort bis zu 20 Jahre überdauern können“ — [lw-heute.de](https://www.lw-heute.de/mediaarchiv/grab_pic.php?id=20485) | **3/3** (3,5–3,6 J.); Einschränkung: nur Dixon nennt die Primärquelle (Wallenhammar 1996), AHDB und LW nennen keine. Gehen beide ebenfalls darauf zurück, wären es weniger unabhängige Messungen. |
| empfohlene Pause nach Befall | ≥ 4 bis 10 J. | AHDB: „In clubroot-affected land, extend the rotation to a break of at least four years“ | UT Extension W235, Tab. 1: Cabbage, Radish — Clubroot **7** — [UT W235-E](https://uthort.tennessee.edu/wp-content/uploads/sites/228/2024/01/W235-E-rotation.pdf) | DLR Rheinpfalz (Schlaghecken, Infoblatt Kohlhernie, Stand 06.11.2004), 8.04: „Auf befallenen Flächen möglichst erst wieder nach 7-10 Jahren wieder Kreuzblütler anbauen“; Übersicht: „ideale Fruchtfolge Regelung gilt, nur alle sieben Jahre Kreuzblütler anzubauen“ — [Gartenakademie RLP, PDF](https://www.gartenakademie.rlp.de/Internet/global/themen.nsf/0/E25577BBDB1120C5C12571DF003E5035/$FILE/Kohlhernie-Gartenakademie.pdf) | **3/3** für „mindestens 4 J.“; **3/3 widerspruchsfrei mit 7 J.** (UT 7, DLR 7–10, AHDB ≥ 4 schließt 7 ein). Der Planungswert 7 J. ist damit belegt. |

Das DLR-Infoblatt nennt außerdem: „Einmal befallene Gartenbeete bleiben für viele Jahre verseucht. Experten rechnen mit 10 und mehr Jahre.“ (stützt die Überdauerung, war bereits 3/3).

### 7.2 Rübenzystennematode (`cyst_nematode`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung (Zahl) | 5–6 J. / bis 10 J. / > 12 J. | NDSU: „a small percentage of eggs within cysts can survive over 12 years under fallow conditions“ — [NDSU Sugarbeet cyst nematode](https://www.ndsu.edu/agriculture/ag-hub/publications/sugarbeet-cyst-nematode) | top agrar 10/2015, S. 60: Eier in den Zysten „können dort bis zu 10 Jahre überdauern“ — [top agrar, PDF](https://www.topagrar.com/dl/2/8/0/5/8/4/9/Nematoden_Rueben.pdf) | SESVanderHave, Technisches Datenblatt Zystennematoden: „kann der Rübennematode im Boden bis zu fünf oder sechs Jahren in Form von Zysten überleben“ — [myagrar.de, PDF](https://www.myagrar.de/media/wysiwyg/pdf/Zystennematoden_sesvanderhave.pdf) | **widersprüchlich** (3 Quellen, Spanne 5–6 bis > 12 J.); „mehrjährig, mindestens 5 J.“ **3/3**. UNL G1906 („can remain viable … for several years“) und AGES („jahrelang“) stützen nur „mehrjährig“. KWS dzz 05/2017 ist nicht mehr abrufbar (HTTP 404). |

Folge: `max_survival_years` bleibt ohne belegte Einzelzahl. Die Anbaupause (3 J., 3/3 Spanne; Korrektur 2026-11-26, vorher „4 J.“) ist davon nicht berührt.

### 7.3 Wurzelgallenälchen (`root_knot_nematode`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | ≈ 1 J. bis „mehrere Jahre“ | AGES Wurzelgallenälchen (*M. hapla*): „Nach Befall bleiben infektionsfähige Stadien bis zu zwei Jahre in der Erde.“ — [AGES](https://www.ages.at/pflanze/pflanzengesundheit/schaderreger-von-a-bis-z/wurzelgallenaelchen) | INRAE ephytia (Gattung allgemein): „remaining for several years in the soil in the form of egg masses“ — [ephytia 7307](https://ephytia.inrae.fr/en/Contents/view/7307) | JKI-Flyer Nematodenschäden an Zwiebeln: „hohe[] natürliche[] Sterblichkeit der Tiere von bis zu 90 % innerhalb von drei Monaten“ bei Nichtwirt-Vorfrucht — [JKI, PDF](https://www.julius-kuehn.de/media/Veroeffentlichungen/Flyer_EP/Nematodenschaeden_an_Zwiebeln_de.pdf) | **widersprüchlich**; Zahl „bis 2 J.“ **1/3** (AGES). Die ephytia-Angabe gilt für die Gattung (überwiegend wärmeliebende Arten), JKI nennt nur den Rückgang. Ein Blogbeitrag der NC State Plant Disease Clinic (2014, „will not survive more than about one year“) ist keine Fachpublikation und zählt nicht. |
| wirksame Pause mit Nichtwirt | ≥ 1 J., Spanne 1–3 J. | UC IPM Pest Note 7489: „Fallowing for 1 year will lower root knot nematode populations enough …“ (verifiziert 2026-11-15) | LfL p_37956: „zwei- bis dreijährigen Anbau von Getreide und Mais“ (verifiziert 2026-11-15) | JKI-Flyer Zwiebeln: „Bei Befall mit M. hapla sollte als Vorfrucht eine Nicht-Wirtspflanze wie Getreide, Gras oder Mais angebaut werden.“ | **3/3** für „mindestens eine Saison/1 J. Nichtwirt“; Planungswert **3 J. nur 1/3** (LfL), 2 J. 2/3 (UC, LfL). NCDA Nema-Note 12 ist nicht mehr abrufbar (HTTP 404). |
| Nichtwirt Poaceae | Getreide, Mais, Gras | CDFA, LfL (verifiziert 2026-11-15) | AGES: „Getreide hingegen ist keine Wirtspflanze“ | JKI-Flyer (s. o.); UW PDDC: „M. hapla … does not infect corn, wheat, oats or rye“ — [UW PDDC](https://pddc.wisc.edu/2015/08/15/root-knot-nematode/) | **3/3** (jetzt CDFA, LfL, AGES, JKI, UW) |

Folge: Für den Replant-Hinweis ist keine konservative Dauer dreifach belegt. 3/3 ist nur die Untergrenze „1 Jahr Nichtwirt“; sie taugt nicht als Warndauer, weil sie das Restrisiko unterschätzt. Empfehlung: Hinweis ohne Zeitangabe.

### 7.4 Weißfäule/Mehlkrankheit (`white_rot`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung | 4–20 J., ≥ 15, > 20, > 25 J. | UC IPM Onion & Garlic: „can survive in the soil for over 20 years“ (verifiziert) | RHS: „Sclerotia can remain in the soil for at least 15 years, though they will not always live this long“ (verifiziert) | FiBL-Merkblatt Zwiebeln (Lichtenhahn, Koller, Schmutz 2003): „Die Sklerotien können bis 20 Jahre im Boden überdauern.“ — [orgprints 2873](https://orgprints.org/2873/1/lichtenhahn-2003-zwiebeln.pdf); außerdem LK NÖ/BOKU Knoblauchbroschüre (2023): „Überlebensraten von 4-20 Jahren im Boden dokumentiert“ — [LK NÖ, PDF](https://blaetterkatalog.lko.at/noe/catalogs/Knoblauchbroschuere_BOKU/pdf/complete.pdf); AUSVEG Fact sheet (2025): „can survive for more than 25 years“ — [AUSVEG, PDF](https://ausveg.com.au/app/uploads/2025/10/Fact-sheet-Common-onion-diseases-and-their-management.pdf) | **3/3** (5 Quellen); obere Werte 15–25 J. |
| empfohlene Pause nach Befall | 8–10 J. bzw. „lange“ | FiBL 2003, Massnahmen bei Befall: „Anbauunterbruch von 8–10 Jahren zu anfälligen Kulturen einhalten. Kein Zwiebelanbau mehr auf befallenen Stellen!“ | LK NÖ/BOKU 2023: Flächen „sollten für einen erneuten Anbau mehrere Jahre gemieden und die Fruchtfolge weit gehalten werden“ (ohne Zahl) | UC IPM: „follow a long-term rotation schedule … Rotation alone will not control white rot“; RHS: „the long survival period makes crop rotation impractical“; AUSVEG: „long rotations between onion crops is required“ (alle ohne Zahl) | Zahl **1/3** (FiBL 8–10 J.); „lange Pause, Fruchtfolge allein unwirksam“ **3/3** |

Korrektur zu §2 (R-002, *F. oxysporum* f. sp. *cepae*): Die ISIP-Angabe „Anbaupause von ca. 5 Jahren“ steht in der Zeile **Wurzel- und Basalfäule (*Fusarium culmorum*, *F. oxysporum*)**, nicht bei der Mehlkrankheit. Sie stützt also *cepae*, nicht `white_rot`. Die Zuordnung in §2 war richtig, für `white_rot` gibt es aus ISIP keine Zahl.

Folge: Sperrdauer ohne dreifach belegte Zahl. Weil die Überdauerung (3/3, ≥ 15 J.) die Beratungspause deutlich übersteigt und alle Quellen von Wiederanbau auf befallenen Stellen abraten, empfiehlt sich ein Hinweis ohne Zeitangabe („auf dieser Stelle keine *Allium* mehr“).

### 7.5 Erbsen-Fußkrankheitskomplex (`pea_root_rot`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| Überdauerung *Aphanomyces euteiches* | > 10 bis 20 J. | Saskatchewan Pulse Growers, „Reducing Root Rot Risk“ (2023): „Aphanomyces has very long-lived resting spores that remain viable for 10+ years“ — [SaskPulse](https://saskpulse.com/?p=3477) | PNW Plant Disease Management Handbook, Pea – Aphanomyces Root Rot: „the pathogen can persist in infested soils 10 years or more“ — [PNW](https://pnwhandbooks.org/plantdisease/host-disease/pea-pisum-sativum-aphanomyces-root-rot) | Hughes & Grau (UW–Madison), APS Plant Health Instructor 2007: „oospores remain dormant and can persist in the soil for more than 10 years“ — [APS](https://apsnet.org/edcenter/pdlessons/Pages/Aphanomyces.aspx); außerdem NDSU PP1790 (2025): „Thick-walled spores can survive in soil for 20 years or more“ — [NDSU PP1790](https://www.ndsu.edu/agriculture/sites/default/files/2025-06/pp1790.pdf) | **3/3** für „≥ 10 J.“ (4 Quellen); „bis 20 J.“ **2/3** (NDSU; Banniza/USask 2015 und Frontiers 2024 gehen beide auf Pfender & Hagedorn 1983 zurück und zählen als eine) |
| Überdauerung *F. oxysporum* f. sp. *pisi* | ≈ 10 bis > 10 J. | NDSU PP1790: „Can survive in soil for 10 years or more“ | Univ. Delaware Weekly Crop Update (2013): „can survive in the soil as long as 10 years as chlamydospores“ (Sekundärquelle, zitiert Illinois) — [UDel](https://sites.udel.edu/weeklycropupdate/?p=5763) | MOFGA: „more than 10 years“ — [MOFGA](https://www.mofga.org/?p=22024) | **3/3** (Spanne „bis 10“ bis „> 10 J.“) |
| Überdauerung *F. solani* f. sp. *pisi* | „many years“ | SaskPulse, „Fusarium Root Rot in Pulse Crops“ (2023): „the spores can survive in the soil for many years“ — [SaskPulse](https://saskpulse.com/resources/fusarium-root-rot-in-pulse-crops/) | LFA MV (Schmidtke), nur „Fusarium spp.“ allgemein: „10 Jahre Überdauerung im Boden möglich“ — [LFA MV](https://www.landwirtschaft-mv.de/serviceassistent/download?id=1601008) | — | Zahl für die forma specialis **0/3** |
| Wirt *Lens* | Linse | SaskPulse: „Peas and lentils are equally susceptible to infection by A. euteiches“ | NDSU PP1790: „Lentils are a host“ | APS/UW, PNW (Wirtslisten) | **3/3** |
| Nichtwirt im Feld *Vicia faba* | Ackerbohne | NDSU PP1790: „Lentils are a host, but chickpeas and faba beans are not“ | Banniza (USask), Tabelle: „Faba bean – Resistant – No“ (keine Oosporen) — [USask](https://harvest.usask.ca/bitstream/10388/12758/1/02%20Banniza.pdf) | Frontiers in Plant Science 2024 (10.3389/fpls.2024.1332976): „faba bean, resistant to A. euteiches (Moussart et al., 2008)“ | **3/3** für *Aphanomyces*; **Widerspruch**: APS/UW und die Grau-Spalte bei Banniza führen Ackerbohne als anfällig (Laborbefunde). LFA MV nennt für Ackerbohne bei Leguminosenmüdigkeit 4–5 J. Pause. Die frühere Annahme „*Vicia* stark“ (§2) ist für *Aphanomyces* nicht haltbar, für den Gesamtkomplex offen. |
| Nichtwirt *Glycine max* | Soja | Banniza (USask): „Soybean – Non-host – No“ | Top Crop Manager 2023 (gibt AAFC/Chatterton wieder): „faba beans, chickpeas and soybeans, are tolerant or resistant“ — [TCM](https://www.topcropmanager.com/quantifying-aphanomyces-severity-in-pea-and-lentil/) | — | **2/3** (Banniza stützt sich teils auf dieselbe AAFC-Linie); NDSU nennt Soja als Wirt des *Fusarium*-Wurzelfäulekomplexes |
| Wirt *Medicago*, *Trifolium pratense* | Luzerne, Rotklee | APS/UW: „alfalfa (Medicago sativa) … red clover (Trifolium pratense)“ | LFA MV: „Luzerne, Gelbklee, Wicken, Linse, Phaseolusbohne, Rot-, Weiß-, Erdklee“ | Frontiers 2024: 97 % der Erbsen-Isolate aus Wisconsin infizieren Luzerne; PNW: „clover, alfalfa“ | **3/3**; Weißklee widersprüchlich (Grau 1991: R; LFA MV: Wirt) |

**Gehört *Phaseolus vulgaris* zum Komplex?** Nein, nicht über die Erbsen-Pathotypen:

| Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|---------|----------|----------|----------|-------------|
| *A. euteiches* bildet an Bohne eine eigene forma specialis; Erbsen-Isolate befallen Bohne kaum und umgekehrt | APS/UW: „isolates obtained from pea are non-pathogenic or weakly pathogenic on bean and alfalfa, and isolates from bean are non-pathogenic or weakly pathogenic on pea“ | Dillard & Abawi, *Plant Disease* 72:912 (1988): „No symptoms were observed on pea … confirming the identity of the pathogen as A. e. f. sp. phaseoli“ — [APS](https://apsnet.org/publications/plantdisease/backissues/Documents/1988Abstracts/PD_72_912C.htm) | Banniza (USask), Tabelle: „Dry bean – Variable – Few“ (Oosporen) | **3/3** |
| *Fusarium solani* an Bohne ist eine eigene forma specialis (*phaseoli*) | UC IPM Dry Beans: „Fusarium solani f. sp. phaseoli (blackeyes, common bean), Fusarium solani f. sp. pisi (garbanzo beans)“ — [UC IPM](https://ipm.ucanr.edu/PMG/r52100211.html) | UNL CropWatch: „f. sp. phaseoli“ — [UNL](https://cropwatch.unl.edu/plantdisease/drybean/fusarium-root-rot) | SaskPulse: „F. solani f. sp. pisi on peas and F. solani f. sp. phaseoli on dry beans“ | **3/3** |
| *F. oxysporum* an Bohne ist eine eigene forma specialis | USU Extension (2022), Tab. 1: „f. sp. phaseoli – Bean“ getrennt von „f. sp. pisi – Pea“ — [USU](https://extension.usu.edu/planthealth/research/fusarium-verticillium-wilts.pdf) | — | — | 1/3 |

Gegenstimmen: PNW, LFA MV und Frontiers führen „common bean“/„Phaseolusbohne“ pauschal als *Aphanomyces*-Wirt, ohne Pathotyp. Ob sich *F. solani* f. sp. *pisi* und f. sp. *phaseoli* kreuzweise infizieren, ist im Volltext nicht belegt. **Folgerung:** *Phaseolus* gehört nicht zur Sperre `pea_root_rot` (Pathotypen getrennt, 3/3); die Familien-Pause Fabaceae und der Art-Override *Phaseolus* 4 J. (REQ-001) bleiben davon unberührt.

**Pause nach Befall (Nachtrag):** SaskPulse empfiehlt für Hochrisikoflächen „until a soil test is negative or at least 8–10 years have elapsed“; mit FiBL 1667 (7–8 J. nach schlechtem Test, verifiziert) und UT W235 (Fusarium-Welke 5 J.; Wurzelfäule 3–4 J.) liegen jetzt **3/3** Pausenangaben vor, aber mit **Spanne 3–10 J.** UT W235 bezieht sich auf Einzelerreger, nicht auf den Komplex; die konservative Komplex-Pause 8 J. stützen **2/3** (FiBL 7–8, SaskPulse 8–10).

### 7.6 Sklerotinia (`sclerotinia`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| empfohlene Pause nach Befall | 2–8 J. | AGES, Rapskrebs und Weißstängeligkeit der Sonnenblume (2022, eine Institution): „Einhaltung eines mindestens vierjährigen (besser sechsjährigen) Fruchtwechsels“ — [AGES Rapskrebs](https://www.ages.at/pflanze/pflanzengesundheit/schaderreger-von-a-bis-z/rapskrebs) | Manitoba Agriculture, Sclerotinia in Sunflowers: „Follow a crop rotation of 5 years between susceptible crops.“ — [Manitoba](https://gov.mb.ca/agriculture/crops/plant-diseases/sclerotinia-sunflowers.html) | PNW 2347: „Rotate with non-hosts for three to eight years“ (verifiziert 2026-11-15); Review *Front. Plant Sci.* (PMC8417578): „a break of 2–3 years may be required … avoidance of infested or adjacent fields for 1–4 years“ — [PMC8417578](https://pmc.ncbi.nlm.nih.gov/articles/PMC8417578/) | **3/3** mit **Spanne 2–8 J.**; der Planungswert **5 J.** liegt in den Angaben von AGES (4–6), Manitoba (5) und PNW (3–8); das Review nennt kürzere Pausen. FiBL 1284 (Sellerie-Komplex, „mindestens 3 Jahren“) gilt für einen Erregerkomplex und zählt nicht. |
| Nichtwirt Poaceae | Getreide, Mais, Gräser | Canola Council of Canada: „Cereals and grasses are not susceptible“ — [CCC](https://www.canolacouncil.org/canola-encyclopedia/diseases/sclerotinia-stem-rot/) | Cornell Vegetable Program (2022): „non-susceptible crops such as grains (corn, rye, wheat, etc.)“ — [Cornell](https://www.vegetables.cornell.edu/pest-management/disease-factsheets/white-mold) | AGES Rapskrebs: „Nicht oder weniger anfällig sind Getreide, Mais, Rüben und Kartoffeln“; Derbyshire et al. 2022 (PMC9276942): „wheat … and barley …, which are both nonhosts“ | **3/3**; Einschränkung: endophytische, symptomlose Besiedlung von Getreide ist beschrieben (Shang et al. 2024, PMC10895550; Tian et al. 2020). Monokotyle Wirte außerhalb der Poaceae: Zwiebel, Knoblauch, Tulpe. |
| max. Überdauerung der Sklerotien | 4–10 J. | AGES: „bis zu zehn Jahre lebensfähig“ | UW–Madison PDDC, White Mold (D0125, 2026): „Sclerotia can survive in soil for at least five years.“ — [UW PDDC](https://pddc.wisc.edu/2015/08/19/white-mold/) | Canola Council: „five years or more“; Manitoba: „up to four years“; Review PMC8417578: „up to 5 years or more“ | **3/3** mit **Spanne 4–10 J.** (vorher 2/3); oberer Wert 10 J. von AGES und dem *Pathogens*-Review (2019) gestützt, also 2/3 |

### 7.7 Verticillium-Welke (`verticillium`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| max. Überdauerung der Mikrosklerotien | > 10 bis 15 J. | Depotter et al., *Mol. Plant Pathol.* 17 (2016): „V. dahliae microsclerotia remain dormant and viable in the soil for more than 10 years (Wilhelm, 1955)“ — [PMC6638321](https://pmc.ncbi.nlm.nih.gov/articles/PMC6638321/) (Dung 2020, PMC7698963, zitiert ebenfalls Wilhelm 1955 und zählt nicht extra) | AHDB, Verticillium stem stripe in OSR: „survive for over 10 years on plant debris in the soil“ — [AHDB](https://ahdb.org.uk/verticillium-stem-stripe) | Pflanzenschutzdienst M-V (Schmidt 2011, auf ISIP): „Mikrosklerotien ca. 10 Jahre lang infektiös“ — [ISIP, PDF](https://isip.de/resource/blob/509444/5acf81ee9132914d3dd4aa764db8b6e1/verticillium-welke-an-gehoelzen-data.pdf); außerdem JLU Gießen, FNR-Bericht 22012602 (2007): „bis zu mehr als 10 Jahre“ — [FNR, PDF](https://www.fnr.de/fileadmin/projektdatenbank/22012602.pdf); HS Osnabrück AGIP-Bericht: „bis zu 10 Jahren“; MSU E2576: „at least 10 years“ | **3/3** („≥ 10 J.“); RHS (≥ 15 J. Grasnarbe für Gehölze) und Hortipendium (10–15 J.) nennen mehr. **Widerspruch:** LfL-Merkblatt Kartoffelkrankheiten (2017): „da die Pilze nicht sehr lange im Boden überdauern können“ |
| empfohlene Pause Gemüse | 3–5 J. | UC IPM (≥ 3 J. bzw. 3–4 J., verifiziert 2026-11-15) | CT Agricultural Experiment Station (Douglas 2008): „Long rotations of four to five years with non-related crops can be helpful but are not usually feasible in home gardens.“ — [CAES, PDF](https://portal.ct.gov/-/media/caes/documents/publications/fact_sheets/plant_pathology_and_ecology/verticilliumwiltofvegetablesandherbaceousornamentals050808pdf.pdf) | Illinois Extension, Verticillium Wilt in Small Fruits: „Do not grow these crops for at least three years where susceptible vegetables were grown“ — [Illinois](https://extension.illinois.edu/plant-problems/verticillium-wilt-small-fruits) | **3/3** mit **Spanne 3–5 J.** (vorher 1/3); alle Quellen betonen die begrenzte Wirkung (Depotter: 4 J. Brache senkten die Mikrosklerotiendichte nicht) |
| empfohlene Pause Erdbeere | 3–5 J., ≥ 4 J. | Penn State Extension (Demchak, 2026): „A rotation schedule of 3 to 5 years also is recommended.“ — [PSU](https://extension.psu.edu/strawberry-disease-verticillium-wilt) | BÖLW Strategiepapier Beerenobst (2024): „Anbaupause von mind. 4 Jahren, besser noch länger“ — [BÖLW, PDF](https://www.boelw.de/fileadmin/user_upload/240221_Strategiepapier_Beerenobst.pdf) | Illinois Extension: „Replant new strawberry beds every three to five years in a new location“ | **3/3**, Spanne 3–5 J. |
| Wirt Amaranthaceae (Spinat) | *Spinacia oleracea* | CAES 2008, Tab. 2 „Susceptible“: „Spinach (Spinacia oleracea)“ | UW–Madison PDDC (D0122, 2026): „… spinach and turnip are susceptible to Verticillium wilt, but show less severe symptoms“ — [UW PDDC](https://pddc.wisc.edu/2015/08/19/verticillium-wilt-of-vegetables/) | du Toit et al. (WSU), *Plant Dis. Manag. Rep.* 3:ST020 (2009): Spinat, „Verticillium wilt; Verticillium dahliae“ — [WSU, PDF](https://wpcdn.web.wsu.edu/extension/uploads/sites/32/du-Toit_spinach-Vert-sd-trtmts-PDMR-3-ST020.pdf) | **3/3** (Spinat); *Beta vulgaris* 2/3 (UW „beet“, Depotter „sugar beet“) |
| Wirt Brassicaceae | Kohlarten, Raps (*V. longisporum*) | Depotter 2016: „cauliflower …, cabbage … and Brussels sprouts“ | CAES 2008: Brussels sprouts, Cabbage, Radish, Rutabaga, Horseradish „Susceptible“ | Agroscope (Michel 2009), Tab. 1: Kreuzblütler werden „von Verticillium longsporum“ befallen; UW PDDC; AHDB („vegetable brassicas“); Pflanzenschutzdienst M-V („Blumenkohl, Chinakohl, Rosenkohl“) | **3/3** |
| Wirt Lamiaceae | *Mentha* | CAES 2008: „Mint (Mentha spp.)“ | Dung (Oregon State), *Plants* 9:1602 (2020): Pfefferminze ‘Black Mitcham’ und Krauseminze „highly susceptible to Verticillium wilt“ — [PMC7698963](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698963/) | Hortipendium „Verticillium Kohl“: besonders anfällig u. a. „Pfefferminze“ — [Hortipendium](https://www.hortipendium.de/Verticillium_Kohl) | **3/3** für *Mentha*; Basilikum und Küchensalbei **0/3** (nur Zier-Salbei bei CAES). Minze-Isolate sind stark wirtsspezialisiert (Dung). |
| Nichtwirt Poaceae | Getreide, Mais, Gräser | UC IPM, RHS (verifiziert 2026-11-15); UW PDDC: „sweet corn are immune to the disease“ | **Gegenbeleg** Dung 2020: „many plants, including several economically important grasses, can be asymptomatic hosts“; Minze-Isolate infizieren Wurzeln von Mais, Gerste, Weizen | **Gegenbeleg** Pflanzenschutzdienst M-V: „Weitere anfällige Kulturpflanzen – Ackerbau-Kulturen: … Getreidearten“; SARE GNE17-144 (2019): Linie 4B befällt symptomlos Hafer | **widersprüchlich** (vorher 2/3). Haltbar ist nur: Getreide und Gräser erkranken nicht und gelten als Fruchtfolgeglieder, können aber symptomlos besiedelt werden. Fünf Jahre Mais senkten *V. dahliae* nicht (Davis et al. 1989). |

### 7.8 *Fusarium oxysporum* formae speciales außer *cepae*

| forma specialis | Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-----------------|---------|----------|----------|----------|-------------|
| *lycopersici* | Wirt nicht nur Tomate: auch *S. melongena*, weitere *Solanum*, symptomlose Träger | McGovern, *Crop Protection* 73:78–92 (2015, Review): „Fol can infect and cause symptoms in S. melogena, S. pimpinellifolium and other Solanum spp. … Amaranthus, Chenopodium, Digitaria, Malva and Oryzopsis spp. were found to be symptomless carriers“ — [UCANR, PDF](https://ccfruitandnuts.ucanr.edu/sites/default/files/2018-11/294665.pdf) | USU Extension 2022, Tab. 1: „f. sp. lycopersici – Eggplant, Pepper, Tomato“ | INRAE ephytia Tomato: „Other plants are likely to harbor it, in particular several other species of Lycopersicon“ — [ephytia](https://ephytia.inrae.fr/en/C/5217/Tomato-Biology-epidemiology) | **3/3** für „Solanaceae, nicht nur Tomate“; **Widerspruch** zu UC IPM („only infects tomato“). PNW zitiert McGovern und zählt nicht extra. |
| *lycopersici* | Überdauerung | McGovern: „from more than 10 years (Katan, 1971) to indefinitely (Agrios, 2005)“ | INRAE ephytia: „for more than ten years, thanks to its chlamydospores“ | CAES Connecticut (2021): „can survive many years“; „Rotate away from tomato and other solanaceous crops for 4-5 years“ — [CAES](https://portal.ct.gov/-/media/caes/documents/publications/fact_sheets/plant_pathology_and_ecology/fusarium-wilt-of-tomato.pdf) | „> 10 J.“ **2/3**; „viele Jahre“ 3/3 |
| *conglutinans* | Wirte Kohl, Blumenkohl, Brokkoli, Rosenkohl, Grünkohl | Cornell Vegetable Program (verifiziert 2026-11-15) | USU 2022: „Broccoli, Brussels Sprouts, Cabbage, Cauliflower, Kale“ | Pacific Pests, Pathogens, Weeds & Pesticides (UQ/SPC, 2023): „broccoli, Brussels sprout, cabbage, cauliflower, and Chinese cabbage“ — [PPPW](https://apps.lucidcentral.org/pppw_v12/text/web_full/entities/cabbage_fusarium_yellows_wilt_132.htm) | **3/3**; **Widerspruch** UC IPM Home Garden: „cauliflower, broccoli, and brussels sprouts are not known to be affected“ |
| *conglutinans* | Rettich ist Wirt | Cornell, PPPW nennen Rettich | du Toit & Pelter, *Plant Health Progress* 2003: „F. oxysporum f. sp. conglutinans … is pathogenic on many Brassica spp. but not on radish“ (Rettich: eigene f. sp. *raphani*) — [WSU, PDF](https://wpcdn.web.wsu.edu/extension/uploads/sites/32/Fusarium-wilt-of-radish-PHP-06-03.pdf) | PNW setzt *raphani* = *conglutinans* | **widersprüchlich** |
| *conglutinans* | Überdauerung | PNW: „chlamydospores which can survive years between hosts“ | UC IPM: „survives indefinitely in the soil“ | PPPW: „can survive in the soil for many years“; Cornell: „many years“ | „viele Jahre“ **3/3**; Zahl **0/3** |
| *pisi* | wirtsspezifisch an Erbse; Linse, Kichererbse mit eigenen formae speciales | USU 2022: „f. sp. pisi – Pea“ | SaskPulse: „F. oxysporum f. sp. pisi … in peas, F. oxysporum f. sp. lentis … in lentils, … f. sp. ciceris … in chickpeas“ | Banniza (USask) 2015: „Relatively host-specific species: Fusarium oxysporum f.sp. pisi or f. sp. lentis“ — [USask](https://harvest.usask.ca/bitstream/10388/8909/1/S.%20Banniza%2c%202015.pdf) | **3/3**; LFA MV: „unklar, wahrscheinlich spezialisiert“. Überdauerung siehe §7.5 (3/3, ≈ 10 J.) |
| *cucumerinum* / *niveum* / *melonis* | je eine Kultur, im Feld kaum Kreuzinfektion | Egel & Martyn, APS Plant Health Instructor (2007/2013): „in the field, the cucurbit wilt fusaria are host-specific and rarely cross-infect“ — [APS](https://apsnet.org/edcenter/pdlessons/Pages/FusariumWatermelon.aspx) | PNW Watermelon: „f. sp. cucumerinum (cucumber), f. sp. melonis (muskmelon), and f. sp. niveum (watermelon)“ — [PNW](https://pnwhandbooks.org/node/3674/print) | USU 2022: „cucumerinum – Cucumber“, „melonis – Cantaloupe“, „niveum – Watermelon“; Cornell Fact Sheet 733.00 (Zitter 1998) für Melone | **3/3**; Ausnahme *niveum* an manchen Sommerkürbissen (nur PNW) |
| Kürbisgewächs-Fusarien | Überdauerung | APS: „may survive in a dormant state in the soil for 15 to 20 years“; Pause Wassermelone „every 5 to 7 years“ | PNW: „may survive several years in soil“; „Rotating 8 to 10 years … may help some“ | Cornell 733.00: „chlamydospores survive so long in the soil“ | Zahl „15–20 J.“ **1/3**; „mehrere Jahre“ 3/3; Pausenzahl widersprüchlich (UT 5, APS 5–7, PNW 8–10) |

### 7.9 Juglon (`juglone`)

| Größe | Wert/Spanne | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-------|-------------|----------|----------|----------|-------------|
| Wirkung nach Fällung | „some years“ / „five or more years“ / „several years“ | Purdue HO-193: „toxicity can persist for some years after a tree is removed“ | UW–Madison Extension: „juglone can persist until the roots have decomposed, which can take five or more years“ — [UW](https://hort.extension.wisc.edu/?p=4074); UW PDDC: Wurzelreste „may continue to exude toxins for several years as they decay“ — [UW PDDC](https://pddc.wisc.edu/tag/peony/) (gleiche Universität, zählt mit UW Extension als **eine** Quelle) | Penn State Extension: Der 2026-11-15 zitierte Satz „Juglone toxicity may persist for years after a tree is removed“ steht in der am 2026-11-17 abgerufenen Fassung **nicht mehr**; die Seite nennt nur raschen Abbau in gut durchlüfteten Böden | „mehrjährig“ **2/3** (vorher irrtümlich 3/3); Zahl „≥ 5 J.“ **1/3** |
| Gegenposition | wenige Monate / Wirkung unbelegt | Iowa State: „juglone breaks down quickly in the soil, so in just a few months after removing the tree, most of the juglone is gone. It is safe to replant the next growing season“ — [ISU](https://yardandgarden.extension.iastate.edu/faq/how-long-does-juglone-last-landscape-after-removal-walnut) | UMD Extension (2023) zu Chalker-Scott (WSU): „there is no conclusive, science-based evidence confirming juglone as the cause for the poor growth of plants growing near black walnut trees“ — [UMD](https://extension.umd.edu/resource/walnut-toxicity-juglone) | — | **widersprüchlich** |
| empfindlich: *Solanum lycopersicum*, *S. tuberosum*, *S. melongena*, *Capsicum annuum* | Solanaceae-Kulturen | Purdue HO-193: „Vegetables: asparagus, cabbage, eggplant, pepper, potato, rhubarb, tomato“ | UW: „Tomatoes, peppers, and potatoes are crops known to be sensitive to juglone“ — [UW Black walnut toxicity](https://hort.extension.wisc.edu/black-walnut-toxicity-to-plants/); PDDC zeigt Welke an Aubergine | Iowa State: „Some plants have been observed to grow poorly near walnuts. This includes members of the tomato family (tomato, potato, eggplant, pepper)“ — [ISU](https://yardandgarden.extension.iastate.edu/faq/what-plants-are-sensitive-juglone-produced-black-walnuts) | **3/3** als *beobachtete* Empfindlichkeit; alle Listen beruhen auf Beobachtung, nicht auf Versuchen (UW, PSU, ISU sagen das ausdrücklich), und die Ursache ist umstritten (UMD/WSU) |
| empfindlich: *Asparagus*, *Brassica oleracea*, *Rheum*, *Malus*, *Pyrus*, *Rubus fruticosus*, *Vaccinium* | übrige Liste | Purdue HO-193 | UW (übernimmt die Purdue-Liste, nicht unabhängig) | — | **1/3** |

Folge: Für Juglon ist keine Zeitangabe nach der Fällung dreifach belegt. 3/3 ist nur die Artliste der vier Solanaceae-Kulturen, und auch die nur als Beobachtung. Hinweis ohne Zeitangabe; solange der Baum steht, gilt die Gefahr ohnehin unbefristet.

### 7.10 Aussagen aus R-003 und R-004

Nicht im Volltext lesbar und daher **nicht gezählt**: Oklahoma State (Early blight, Reusing potting soil; Bot-Schutz), UMN, UMass, MSU canr. Die als „Univ. Kentucky E706“ geführte Datei ist in Wahrheit der *e-GRO Edible Alert* 7(6) (J. Williams-Woodward, University of Georgia, 2022) auf dem UKY-Server; die Quellenangabe in R-004.3 war falsch.

| Nr. | Aussage | Quelle 1 | Quelle 2 | Quelle 3 | Belegstatus |
|-----|---------|----------|----------|----------|-------------|
| R-003 a | Fruchtfolge zielt auf bodenbürtige Erreger; Pausenlänge nach deren Überdauerung | UT W235 (verifiziert 2026-11-15) | RHS „Crop rotation“: „Soil pests and diseases tend to attack specific plant families … the pests tend to decline in the period when their host plants are absent“ — [RHS](https://www.rhs.org.uk/vegetables/crop-rotation) | UConn IPM (MacNab-Tabelle, Penn State 1990; Cornell-Fassung zählt nicht extra): „Different plant diseases will persist in the soil for different lengths of time, so the length of the rotation will vary with the disease being managed.“ — [UConn](https://ipm.cahnr.uconn.edu/having-problems-controlling-vegetable-crop-diseases-try-rotation) | **3/3** (ergänzend LSU AgCenter 2021, Iowa State) |
| R-003 b | Blattkrankheiten/Blattschädlinge: ~2 J. Pause genügen | UT W235 | MacNab-Tabelle (UConn/Cornell): „Early blight \| Two years“, „Spinach \| Downy mildew \| Two years“, „Onion \| Leaf blights \| One to two years“ | Univ. Illinois RPD 900 (1991): „Leaf spots. Practice a 2- to 3-year crop rotation.“ — [Illinois, PDF](https://apps.web.maine.gov/dacf/php/gotpests/diseases/factsheets/disease-home-veg-garden-ill.pdf) | **3/3**, Spanne 1–3 J. (Illinois 2–3) |
| R-003 c | *Alternaria solani* überdauert auf Ernteresten ≥ 1 J.; 2–3 J. Pause | UMaine Bulletin #5087: „can survive for at least one to several years“; Rotation „for three years“ — [UMaine](https://extension.umaine.edu/ipm/?p=4592) | UConn IPM (Hazzard): „overwinters in infected crop debris … it will not survive in the soil during a rotation of 3 years or more into a non-host crop“; „at least 2-3 years“ — [UConn](https://ipm.cahnr.uconn.edu/early-blight-management-in-fresh-market-tomatoes/) | MacNab-Tabelle: „Early blight \| Two years; avoid potato“; Illinois RPD 900: „2- to 3-year crop rotation“ | **3/3** (Pause 2–3 J.) |
| R-003 d | *P. infestans* überdauert in Nordamerika nicht im Boden/in totem Material | UMaine #2427 (verifiziert) | Cornell/NYS IPM Late Blight Brochure: „Late blight can only survive on living tissue“ — [PDF](https://apps.web.maine.gov/dacf/php/gotpests/diseases/factsheets/late-blight-brochure-cornell.pdf) | UConn HGEC: „Phytophthora infestans does not overwinter in our area. It only survives in living plant tissue.“ — [UConn](https://homegarden.cahnr.uconn.edu/factsheets/late-blight-of-tomato-and-potato) | **3/3**; Vorbehalt Penn State: beide Paarungstypen in PA/VA nachgewiesen, Oosporen im Boden möglich — [PSU](https://extension.psu.edu/tomato-potato-late-blight-in-the-home-garden) |
| R-003 e | Mitteleuropa: *P. infestans* kann als Oospore im Boden überwintern | TLLLR-Merkblatt 2020 (verifiziert; ISIP-Kopien sind dasselbe Dokument) | Möbs (LLH Hessen), LW 20/2016: Dauersporen „bis zu vier Jahre im Boden überlebensfähig“, in Deutschland „noch eher von untergeordneter Stellung“ — [lw-heute](https://www.lw-heute.de/mediaarchiv/grab_pic.php?id=33281) | Mohr (DLR Rheinhessen-Nahe-Hunsrück), LW 15/2015: Oosporen als Quelle „nicht ausgeschlossen“ — [lw-heute](https://www.lw-heute.de/mediaarchiv/grab_pic.php?id=28167) | **3/3** (Nebenweg; Hauptquelle Pflanzgut). Zahl „bis 4 J.“ **1/3** |
| R-004.1 a | Schossen ist eine physiologische Reaktion (Tageslänge, Kälte, Hitze, Trockenheit) | RHS Bolting (verifiziert) | Purdue PPDL (Lerner 2021): „will bolt as days grow longer … Hot temperatures … dry soil … bolting is induced by a cold snap“ — [Purdue](https://ag.purdue.edu/department/btny/ppdl/potw-dept-folder/2021/lettuce-bolting.html) | Univ. Delaware Weekly Crop Update (2023): „Bolting response may be related to temperature, daylength, or a combination … high temperature stress … vernalization“ — [UDel](https://sites.udel.edu/weeklycropupdate/?p=22287) | **3/3** für die Ursachen (der Satz „keine Krankheit“ steht in keiner Quelle wörtlich) |
| R-004.1 b | Vorzeitige Seneszenz kann Verticillium-Symptom sein, verwechselbar mit Abreife | UC IPM Potato (verifiziert) | MSU E2576 (1995): „Verticillium wilt causes premature maturation and death of vines … symptoms are difficult to distinguish from normal maturity“ — [MSU](https://sanweb.lib.msu.edu/DMC/extension_publications/e2576/E2576-1995.PDF) | Rowe et al. 1987, *Plant Disease* 71:482–489: Symptome der Potato Early Dying „difficult to distinguish from normal senescence“ — [APS, PDF](https://apsnet.org/publications/plantdisease/backissues/Documents/1987Articles/PlantDisease71n06_482.PDF) | **3/3** |
| R-004.3 a | Sauberes Substrat in Gefäß/Hochbeet umgeht verseuchten Boden | NC State Clubroot (verifiziert) | WSU Skagit (Salyan): „removal of the soil is necessary; replace with disease free/garden soil“ — [WSU, PDF](https://wpcdn.web.wsu.edu/extension/uploads/sites/57/2014/03/113007.pdf) | Univ. Illinois Extension, Container gardens: „use sterilized containers and soil“ — [Illinois](https://extension.illinois.edu/container-gardens/disease-and-insect-problems) | **3/3** mit Einschränkung: keine Quelle sagt wörtlich, dass ein Hochbeet die Bodengefahr aufhebt |
| R-004.3 b | Substrat nach kranken Pflanzen nicht wiederverwenden | LSU AgCenter (Kirk-Ballard 2022): „If plants died from bacterial, fungal or viral disease, then you definitely do not want to reuse the soil“ — [LSU](https://www.lsuagcenter.com/articles/page1671725785873) | Illinois Extension (s. o.) | NC State, Gewächshaus: „If disease is present, plant material and potting media should be discarded“ | **3/3** |
| R-004.3 c | … nach gesunden Pflanzen ist Wiederverwendung in Ordnung | LSU: „if the plants that grew in the soil before were healthy, it is generally OK to reuse the potting soil“ | — | — | **1/3**; NC State rät im Erwerbsanbau generell ab |
| R-004.3 d | Hydrokultur nicht automatisch frei von Wurzelerregern; Ausbreitung über rezirkulierende Nährlösung; Desinfektion nötig | Stanghellini et al. (UC Riverside), USDA-ARS-Poster 2009: „root diseases still occur … rapid dispersal throughout the production system via the recirculating nutrient solution“ — [USDA](https://www.ars.usda.gov/ARSUserFiles/02060000/FNRI2009/FNRI_2009_Posters/Stanghellini-FNRIWP.pdf) | e-GRO Edible Alert 7(6) (UGA 2022): „Root disease is always a concern within any hydroponic system“; „disinfected between runs“ — [PDF](https://greenhousehort.ca.uky.edu/sites/greenhousehort.ca.uky.edu/files/E706.pdf) | Wageningen UR, Technical information sheet No. 6: „If you recirculate the nutrient solution … disinfection of the solution is required“ — [WUR](https://edepot.wur.nl/403803) | **3/3** für *Pythium*/*Phytophthora*; *Fusarium* in der Nährlösung nicht ausdrücklich belegt |
| R-004.3 e | Hochbeet auf gewachsenem Boden: Wurzeln erreichen den Unterboden | UMD Extension (Traunfeld 2019/2024): „Plant roots grew through the raised bed soil into the ground below.“ — [UMD](https://extension.umd.edu/resource/soil-fill-raised-beds/) | Utah State Extension (2012): „no bottom to allow plant roots access to existing soil below the box“ — [USU, PDF](https://extension.usu.edu/yardandgarden/research/raised-bed-gardening.pdf) | Cornell Soil NOW „Raised beds“: „deep enough to prevent roots from reaching into the contaminated soil below“ (Schadstoffkontext) — [Cornell](https://blogs.cornell.edu/soilnow/raised-beds) | **3/3** |
| R-003 Bewertung | Blattkrankheit in der Saison: Entfernen der kranken Pflanze/Reste reicht, nicht kompostieren | Entfernen: UMD Septoria: „Remove infected leaves during the growing season“ — [UMD](https://extension.umd.edu/resource/septoria-leaf-spot-tomatoes); PSU Late blight: „Remove the entire plant and discard in a garbage bag“; UConn HGEC | „reicht“: Gegenbeleg Illinois Septoria: „The fungus survives in infected plant debris left on the soil surface or buried in the soil“ — [Illinois](https://extension.illinois.edu/plant-problems/septoria-leaf-spot-tomato); UMaine 5087 und MacNab (Early blight 2 J.) | „nicht kompostieren“: Gegenbeleg UMD erlaubt Heißkompostierung über 120 °F | „Entfernen“ **3/3**; „reicht“ nur für *P. infestans* haltbar, für *Septoria*/*Alternaria* **widerlegt**; „nicht kompostieren“ **widersprüchlich**. Falscher Mehltau: keine Volltextquelle |
| R-004.2 | Definition „dieselbe Saison“ | — | — | — | weiterhin **0/3** (Planungskonvention, nicht recherchierbar) |

Folgen für §5 und R-004:

- Die Aussage „Blattkrankheit: Pflanzenreste entfernen, keine Rotationswarnung“ gilt in der laufenden Saison. Für Folgejahre stützt R-003 b/c eine 2–3-jährige Pause bei *Alternaria* und *Septoria*; sie liegt unter der Familien-Pause Solanaceae 4 J. und ist dadurch abgedeckt. Den Zusatz „nicht kompostieren“ besser als „nicht auf den Gartenkompost (nur Heißrotte)“ formulieren.
- Widerspruch zu Verticillium: Das LfL-Merkblatt Kartoffelkrankheiten (13. Aufl. 2017) schreibt, „da die Pilze nicht sehr lange im Boden überdauern können“; MSU E2576 nennt „at least 10 years“. Siehe §7.7.

### 7.11 Ergebnis für die Wissenstabelle (F-18)

Die Tabelle selbst entsteht erst im Sprint (F-18); hier steht nur, welche Werte eingetragen werden können. „3/3 Zahl“ heißt: drei unabhängige Quellen nennen dieselbe Zahl oder eine Untergrenze, die sie erfüllt. „3/3 Spanne“ heißt: drei unabhängige Quellen nennen voneinander abweichende Spannen, und der Planungswert liegt in jeder davon. Nach Betreiberentscheid 2026-11-22 zählt „3/3 Spanne“ als 3/3 für die Warndauer; die Wissenstabelle weist die Belegart `range` aus.

**Werte mit 3/3, eintragbar mit F-18:**

| hazard / Erreger | Feld | Wert | Art des Belegs | Abschnitt |
|------------------|------|------|----------------|-----------|
| `clubroot` | `soil_persistence_years` | 7 | 3/3 Spanne (AHDB ≥ 4, UT 7, DLR 7–10) | §7.1 |
| `clubroot` | `max_survival_years` | 15 | 3/3 Zahl als Untergrenze (AHDB bis 15, RHS 20, LW 2013 bis 20, Dixon ≥ 18); 20 J. nur 2/3 (RHS, LW) | R-001.1, §7.1 |
| `clubroot` | Halbwertszeit (informativ) | 3,5–3,6 J. | 3/3 Zahl, mögliche gemeinsame Primärquelle | §7.1 |
| `clubroot` | Wirte | Brassicaceae | 3/3 (R-002) | R-002 |
| `cyst_nematode` | `soil_persistence_years` | 3 | 3/3 Spanne (LfL ≥ 2, NDSU 2–3, AGES 3 J. Pause; Korrektur 2026-11-26 nach Betreiberentscheid zu Punkt 5, vorher 4) | R-001.2 |
| `cyst_nematode` | Wirte | Brassicaceae, Amaranthaceae | 3/3 (R-002) | R-002 |
| `root_knot_nematode` | Wirte | Familienliste R-002 | 3/3 (R-002) | R-002 |
| `root_knot_nematode` | Nichtwirt | Poaceae | 3/3 (neu) | §7.3 |
| `white_rot` | `max_survival_years` | 15 | 3/3 Zahl als Untergrenze (UC > 20, RHS ≥ 15, AUSVEG > 25; FiBL bis 20) | §7.4 |
| `white_rot` | Wirte | Gattung *Allium* | 3/3 (R-002) | R-002 |
| `pea_root_rot` | `max_survival_years` | 10 | 3/3 Zahl als Untergrenze (*Aphanomyces* und *F. o.* f. sp. *pisi*) | §7.5 |
| `pea_root_rot` | Wirte | *Pisum*, *Lens*; *Medicago*, *Trifolium pratense* als Wirt/ungünstige Vorfrucht | 3/3 | §7.5 |
| `pea_root_rot` | ausgenommen | *Phaseolus vulgaris* (eigene Pathotypen) | 3/3 | §7.5 |
| `pea_root_rot` | ausgenommen | *Vicia faba* (für *Aphanomyces*) | 3/3, mit Gegenbelegen aus Laborversuchen | §7.5 |
| `sclerotinia` | `soil_persistence_years` | 5 | 3/3 Spanne (AGES 4–6, Manitoba 5, PNW 3–8; Review kürzer) | §7.6 |
| `sclerotinia` | Nichtwirt | Poaceae | 3/3 (endophytische Besiedlung möglich) | §7.6 |
| `sclerotinia` | Überdauerung (informativ) | 4–10 J. | 3/3 Spanne; 10 J. nur 2/3 | §7.6 |
| `verticillium` | `soil_persistence_years` | 4 | 3/3 Spanne (UC 3–4, CAES 4–5, Illinois ≥ 3) | §7.7 |
| `verticillium` | `max_survival_years` | 10 | 3/3 Zahl als Untergrenze | §7.7 |
| `verticillium` | Wirte | zusätzlich Amaranthaceae (Spinat), Brassicaceae, Lamiaceae (*Mentha*) | 3/3 | §7.7 |
| *F. oxysporum* f. sp. *lycopersici* | Wirte | Solanaceae (Tomate, Aubergine, weitere *Solanum*) | 3/3, Widerspruch UC IPM | §7.8 |
| *F. oxysporum* f. sp. *conglutinans* | Wirte | *Brassica oleracea* (Kohl, Blumenkohl, Brokkoli, Rosenkohl, Grünkohl) | 3/3, Widerspruch UC IPM | §7.8 |
| *F. oxysporum* f. sp. *pisi* | Wirte | nur *Pisum sativum* | 3/3 | §7.8 |
| *F. oxysporum* f. sp. *cucumerinum* / *niveum* / *melonis* | Wirte | je eine Art (Gurke / Wassermelone / Melone) | 3/3 | §7.8 |
| `juglone` | empfindliche Arten | *Solanum lycopersicum*, *S. tuberosum*, *S. melongena*, *Capsicum annuum* | 3/3, nur beobachtet | §7.9 |

R-003/R-004: 3/3 erreicht haben R-003 a–e, R-004.1 a–b, R-004.3 a, b, d und e (§7.10). Das sind fachliche Aussagen, keine Tabellenwerte. Sie stützen die Regeln in §5 und R-004.3 und gehören in die Begründung von REQ-053/REQ-054, nicht in F-18.

**Ohne Zeitangabe für den Replant-Hinweis bleiben** (R5/R10): `root_knot_nematode` (nur „≥ 1 J. Nichtwirt“ 3/3), `white_rot` (Pausenzahl 1/3), `pea_root_rot` (Pausen 3–10 J. ohne gemeinsamen Wert; 8 J. nur 2/3), `juglone` (Dauer nach Fällung widersprüchlich), alle *F.-oxysporum*-formae speciales außer *cepae* (Pausen- und Überdauerungszahlen höchstens 2/3).

**Widersprüchliche Quellen:**

| Wert | Spanne / Gegenposition |
|------|------------------------|
| Überdauerung Rübenzystennematode | 5–6 J. (SESVanderHave), bis 10 J. (top agrar), > 12 J. (NDSU) |
| Überdauerung Wurzelgallenälchen | bis 2 J. (AGES) gegen „several years“ (ephytia, Gattung) |
| Pause Sklerotinia | 1–4 bzw. 2–3 J. (Review) gegen 4–6 J. (AGES), 5 J. (Manitoba), 3–8 J. (PNW) |
| Pause Erbsen-Komplex | 3–5 J. (UT W235, Einzelerreger), 5–9 bzw. 7–8 J. (FiBL), 8–10 J. (SaskPulse) |
| Verticillium-Überdauerung | ≥ 10 J. (sieben Quellen) gegen „nicht sehr lange“ (LfL Kartoffelkrankheiten 2017) |
| Verticillium-Nichtwirt Poaceae | Nichtwirt (UC IPM, RHS, UW) gegen symptomlose Besiedlung (Dung 2020, Pflanzenschutzdienst M-V, SARE) |
| *Vicia faba* und Weißklee als *Aphanomyces*-Wirt | anfällig im Labor (APS/UW, Grau 1991) gegen resistent im Feld (NDSU, USask, Frontiers) |
| *F. o.* f. sp. *lycopersici* nur Tomate | UC IPM gegen McGovern 2015, USU, INRAE |
| *F. o.* f. sp. *conglutinans* an Blumenkohl/Brokkoli und Rettich | UC IPM verneint Blumenkohl/Brokkoli; du Toit & Pelter 2003 verneinen Rettich (eigene f. sp. *raphani*) gegen Cornell, PPPW |
| Juglon nach Fällung | „some years“ / „five or more years“ (Purdue, UW) gegen „a few months“ (Iowa State) und „no conclusive evidence“ (UMD/WSU) |
| Blattkrankheit in der Saison: „Entfernen reicht, nicht kompostieren“ | für *Septoria*/*Alternaria* widerlegt (Illinois, UMaine, MacNab); Heißkompostierung erlaubt (UMD) |

### 7.12 Offene Punkte nach #3005

1. **Pausenwerte als Spanne.** Für `clubroot` 7, `sclerotinia` 5 und `verticillium` 4 nennen die drei Quellen nicht dieselbe Zahl, der Wert liegt aber in jeder Angabe. Ob das als 3/3 für die Warndauer gilt, entscheidet der Betreiber. Diese Recherche nennt die Werte eintragbar und weist den Belegtyp aus. **Entschieden 2026-11-22:** Ein Wert, der in allen drei Quellangaben liegt, gilt als 3/3, auch bei Spannen; die Wissenstabelle führt die Belegart „Spanne“ (`range`).
2. **Nicht gefunden:** Überdauerung Wurzelgallenälchen als Zahl, Pausenzahl Weißfäule (außer FiBL), Überdauerung *F. solani* f. sp. *pisi* und *F. o.* f. sp. *conglutinans* als Zahl, Verticillium an Basilikum und Küchensalbei, Kreuzinfektion *F. solani* f. sp. *pisi*/*phaseoli*, „nach gesunden Pflanzen ist Wiederverwendung in Ordnung“ (1/3), Falscher Mehltau zu R-003, Definition „dieselbe Saison“ (0/3).
3. **Deutsche Landesquellen:** LWK NRW/Niedersachsen und LTZ Augustenberg lieferten zu keinem Wert einen abrufbaren Volltext mit Zahl. Verwendet sind LfL, JKI, DLR RLP, LFA MV, Pflanzenschutzdienst M-V, TLLLR, LLH Hessen, AGES, Agroscope, FiBL, LK NÖ/BOKU.
4. **Nicht mehr abrufbar:** KWS dzz 05/2017, NCDA Nema-Note 12 (HTTP 404); Oklahoma State (Bot-Schutz). Der Penn-State-Satz zur Juglon-Persistenz steht in der aktuellen Fassung nicht mehr.
5. **Rübenzystennematode, Pause:** LfL schreibt „Wirtspflanzen sollten maximal alle drei Jahre angebaut werden“ (2 J. Pause im Dreijahresrhythmus), NDSU „three- to four-year rotation“, AGES „vierjähriger Fruchtwechsel“. Die R-001.2-Bewertung (3/3 für 4 J.) liest „Rotation“ als Pause; eine strengere Lesart ergibt 2–3 J. Pause. Vor dem Eintrag in F-18 klären, ob `soil_persistence_years` die Pause oder die Rotationslänge meint. **Entschieden 2026-11-22:** `soil_persistence_years` meint die Anbaupause; es gilt die strengere Lesart (2–3 J. Pause). Eingetragen ist 3 J. (liegt in allen drei Angaben, 3/3 Spanne); R-001.2, §6.1, §7.2 und §7.11 sind korrigiert.
6. **Korrektur Quellenangabe R-004.3:** „University of Kentucky E706“ ist der e-GRO Edible Alert 7(6) der University of Georgia.
