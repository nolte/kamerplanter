# Recherche Bodengefahren, Wirtskreise und Nachpflanzen (R-001 … R-004)

| Feld | Wert |
|------|------|
| Datum | 2026-11-15 |
| Bezug | GitHub #2888; REQ-054 §5.2 (`soil_hazards[]`), §5.5 (Bodenpathogene), §6 H-10/H-11 und Notiz „Übernommen aus REQ-053 §11.3“; REQ-053 §11.3 „ausgefallen“, GP-FR-131 |
| Methode | E-10: je Wert drei voneinander unabhängige Quellen (Fachliteratur, Landesanstalten/Kammern/JKI, RHS, AHDB, UC IPM, US-Extension-Services, Reviews). Wo weniger als drei unabhängige Quellen gefunden wurden, steht der Wert als **„nicht belegt (n/3)“**. |
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
| empfohlene Pause nach Befall | 3–4 J. (Tara-Böden 3–5) | LfL Merkblatt „Nematoden im Feldgemüsebau“: „Wirtspflanzen sollten maximal alle drei Jahre angebaut werden“ — [LfL p_37956](https://www.lfl.bayern.de/mam/cms07/publikationen/daten/merkblaetter/p_37956.pdf) (verifiziert) | NDSU: „Heavily infested fields need a three- to four-year rotation“ (verifiziert) | AGES: „Ein vierjähriger Fruchtwechsel ist wesentlich“ (verifiziert) | **3/3** |

**Vorschlag:** `soil_persistence_years = 4`, `max_survival_years = 12`. Begründung: oberer Rand der drei übereinstimmenden Beratungsempfehlungen (3, 3–4, 4); bei 50 % Abnahme pro Jahr bleiben nach 4 Jahren ≈ 6 % der Ausgangsdichte.

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

| hazard | soil_persistence_years (Vorschlag) | max_survival_years (Vorschlag, informativ) | affected_families (Ebene) | Belegstatus Sperrdauer / Überdauerung / Wirte |
|--------|-----------------------------------|---------------------------------------------|---------------------------|-----------------------------------------------|
| `clubroot` | 7 | 20 | Brassicaceae (Familie) | 2/3 · 3/3 · 3/3 |
| `cyst_nematode` | 4 | 12 | Brassicaceae, Amaranthaceae (Familie; Ausnahme resistente Zwischenfruchtsorten) | 3/3 · 1/3 · 3/3 |
| `root_knot_nematode` | 3 | — (unbekannt) | Solanaceae, Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Cucurbitaceae, Amaranthaceae, Rosaceae; *Allium* bei *M. hapla* (Familie; Nichtwirt Poaceae) | 2/3 · 0/3 · 3/3 |
| `white_rot` | 15 | 20 | Amaryllidaceae, nur Gattung *Allium* | 0/3 · 2/3 · 3/3 |
| `pea_root_rot` | 8 | 12 | Fabaceae: *Pisum*, *Lens*, *Vicia* (Gattung); *Glycine* ausgenommen, *Phaseolus* offen | 2/3 · 0/3 · 1/3 |
| `sclerotinia` | 5 | 10 | Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Solanaceae, Cucurbitaceae, Lamiaceae, Rosaceae (Familie; Nichtwirt Poaceae 1/3) | 1/3 · 2/3 · 2/3 |
| `verticillium` | 4 | 14 | Solanaceae, Rosaceae, Cucurbitaceae, Asteraceae (2/3); Amaranthaceae, Brassicaceae (1/3); Lamiaceae (0/3) (Familie; Nichtwirt Poaceae) | 1/3 · 0/3 · 2/3 |
| `juglone` | 5 (1 bei entferntem Wurzelwerk; unbefristet solange Baum steht) | — | Art-/Gattungsliste: *Solanum lycopersicum, S. tuberosum, S. melongena, Capsicum annuum, Brassica oleracea, Asparagus officinalis, Rheum rhabarbarum, Malus, Pyrus, Rubus fruticosus, Vaccinium* (keine Familiensperre) | 1/3 · 3/3 („mehrjährig“) · 1/3 |

### 6.2 Wirtskreise

| pathogen | host_families (Katalog, APG IV) | Ebene | Belegstatus |
|----------|----------------------------------|-------|-------------|
| *Plasmodiophora brassicae* | Brassicaceae | Familie | 3/3 |
| *Heterodera schachtii* | Brassicaceae, Amaranthaceae | Familie | 3/3 |
| *Meloidogyne* spp. (*hapla*, *incognita*) | Solanaceae, Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Cucurbitaceae, Amaranthaceae, Rosaceae, Amaryllidaceae (*M. hapla*) | Familie | 3/3 (Liste), Nichtwirt Poaceae 2/3 |
| *Sclerotinia sclerotiorum* | Brassicaceae, Fabaceae, Apiaceae, Asteraceae, Solanaceae, Cucurbitaceae, Lamiaceae, Rosaceae | Familie | 2/3 |
| *Verticillium dahliae* / *albo-atrum* | Solanaceae, Rosaceae, Cucurbitaceae, Asteraceae; Amaranthaceae, Brassicaceae (1/3) | Familie | 2/3 bzw. 1/3 |
| *Stromatinia cepivora* | Amaryllidaceae → *Allium* | Gattung | 3/3 |
| *F. oxysporum* f. sp. *lycopersici* | Solanaceae → *Solanum lycopersicum* | Art | 1/3 |
| *F. oxysporum* f. sp. *conglutinans* | Brassicaceae (alle *B. oleracea*-Formen, *Raphanus*) | Familie | 1/3 |
| *F. oxysporum* f. sp. *pisi* | Fabaceae → *Pisum sativum* | Art | 1/3 |
| *F. oxysporum* f. sp. *cepae* | Amaryllidaceae → *Allium cepa*, *A. sativum* | Gattung | 2/3 |
| *F. oxysporum* f. sp. *cucumerinum* / *niveum* / *melonis* | Cucurbitaceae → *Cucumis sativus* / *Citrullus lanatus* / *Cucumis melo* | Art | 1/3 |
| *F. oxysporum* an Kartoffel | — (kein Hazard) | — | 0/3 |
| Erbsen-Fußkrankheitskomplex | Fabaceae → *Pisum*, *Lens*, *Vicia* | Gattung | 1/3 |
| Juglon (*Juglans nigra*, *J. cinerea*, schwächer *J. regia*) | siehe Artliste 6.1 | Art | 1/3 |

### 6.3 Nicht dreifach belegte Werte (Kurzliste für die Nachrecherche)

Halbwertszeit Kohlhernie; Pausenempfehlung Kohlhernie (2/3); Überdauerung Rübenzystennematode als Zahl; Überdauerung Wurzelgallenälchen; Pause Weißfäule; Überdauerung und Wirtsliste Erbsen-Komplex; Pause Sklerotinia; alle Zahlen und drei Wirtsfamilien bei Verticillium; alle *F.-oxysporum*-formae speciales außer *cepae*; Juglon-Zahl und Artliste; sämtliche Aussagen in R-003 und R-004 (höchstens 1/3 verifiziert). Dreifach belegt sind: Überdauerung und Wirte Kohlhernie, Pause und Wirte Rübenzystennematode, Wirtsliste *Meloidogyne*, Wirte Weißfäule, „Juglon wirkt mehrjährig nach“.
