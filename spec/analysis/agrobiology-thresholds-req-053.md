# Agrarbiologische Fachprüfung der Schwellenwerte in REQ-053 (WP 0.7)

| Feld | Wert |
|---|---|
| Datum | 2026-10-15 |
| Bezug | REQ-053 v1.4 — O-17 (Fachprüfung Sonnenklassen, Bezugsdatum, Erreichbarkeit), E-10 (Werte nur mit Quelle je Wert), WP 0.7 |
| Geprüfte Stellen | §10.2 GP-FR-157/160/164/166 · §11.2 GP-FR-060/061/062/073 · §16.2 GP-FR-130/131 · Recherchepunkte R-001…R-013 aus `agrobiology-review-req-053.md` und R-001…R-024 aus `agrobiology-review-req-054.md` |
| Rolle | Agrarbiologie-Reviewer mit Websuche |
| Methode | Jede Annahme wurde gegen mindestens eine extern abrufbare Quelle geprüft (Landwirtschaftskammern, Landesanstalten, Extension-Dienste von Hochschulen, RHS, FAO, Fachzeitschriften). PDF-Quellen wurden heruntergeladen und per `pdftotext` gelesen; HTML-Quellen per Abruf. Ratgeber-Portale (gartenjournal, Plantura, utopia) gelten **nicht** als belastbar und werden nur als „tertiär" zur Einordnung genannt, nie als alleiniger Beleg. Status: `confirmed` = REQ-053-Wert durch mindestens eine belastbare Quelle gedeckt; `corrected` = belastbare Quelle nennt einen anderen Wert oder eine nötige Ergänzung; `unverified` = keine belastbare Quelle gefunden, Wert bleibt konfigurierbar und als unverifiziert gekennzeichnet. |
| Nicht erfunden | Kein Wert in diesem Bericht ist ohne Quelle gesetzt. Wo Quellen streuen, steht die Spanne und die Überschneidung. |

Corrected-Punkte (6): `deep_shade`-Schwelle (A), Fabaceae-Pause mit Spezies-Override (C), Obergrenze Pflanzabstand 1 500 cm (D), Interaktionsradius für Gehölze (E), R-003/053 Pausenwerte, R-005/053 Tropf-Effizienz. Alle übrigen Zeilen sind `confirmed` oder `unverified`; die Liste der unverifizierten Punkte steht am Ende.

---

## A. Sonnenklassen (GP-FR-157, GP-FR-160, GP-FR-164)

Leitquelle: RHS „Shade gardening" definiert alle Klassen mit Bezug „at midsummer".

| Wert | REQ-053-Annahme | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| `full_sun` | ≥ 6 h direkte Sonne | RHS: „More than six hours of direct sun per day at midsummer." Proven Winners (Gärtnerei, tertiär): ≥ 6 h. Die Grenze liegt bei 6 h; ob 6,0 h selbst noch Vollsonne ist, entscheidet die Konvention (RHS: „more than"). | RHS, Shade gardening, https://www.rhs.org.uk/advice/profile?PID=934 (abgerufen 2026-10-15) | confirmed |
| `partial_shade` | 3–6 h | RHS: „Three to six hours per day of direct sun at midsummer." Andere Quellen setzen 4–6 h (Proven Winners, utopia, tertiär); die RHS-Spanne ist die einzige mit Institutionsrang. | RHS, a. a. O. | confirmed |
| `shade` | < 3 h | RHS kennt keine Klasse „shade" mit Stundenwert zwischen Halbschatten und Tiefschatten; der Bereich < 3 h ist bei RHS nur negativ definiert (nicht mehr Halbschatten). Die Obergrenze 3 h ist damit gedeckt, eine Untergrenze fehlt in REQ-053. | RHS, a. a. O. | confirmed (Obergrenze) |
| `deep_shade` | in GP-FR-157 ergänzt, **ohne Schwelle** | RHS: „if a site receives less than two hours of direct sun per day, it must be considered to be heavy shade." → `deep_shade` < 2 h; `shade` damit 2 h ≤ x < 3 h. | RHS, a. a. O. | corrected (Schwelle ergänzen) |
| Referenzdatum | 21. Juni statt Äquinoktium | RHS bezieht alle Stundenwerte auf „midsummer". Der 21. Juni ist die naheliegende Operationalisierung von „Hochsommer" (Sonnenhöchststand). Gartenplaner-Praxis empfiehlt zusätzlich Beobachtungen zu Äquinoktium und Solstitien (Plews Garden Design; tertiär), das ändert den Referenzpunkt der Klassen nicht. | RHS, a. a. O.; Plews Garden Design, https://plewsgardendesign.co.uk/is-yours-a-shady-or-a-sunny-garden (tertiär) | confirmed |
| Morgen-/Nachmittagssonne — fachlich relevant? | nicht modelliert | RHS: „Midday sun supplies considerably more light than morning or evening sun." Die *Lichtmenge* je Stunde ist also tageszeitabhängig; eine reine Stundenzählung über- oder unterschätzt Ost- und Westlagen. Die Behauptung „Nachmittagssonne stresst stärker" fand sich nur in Blogs. | RHS, a. a. O. | confirmed (Relevanz der Mittagsstunden) / unverified (Hitzestress-Gewichtung) |
| Hilfetext GP-FR-157 „mehr als 6 Stunden direktes Sonnenlicht an einem Sommertag" | Glossartext | Deckt sich wörtlich mit RHS („more than six hours … at midsummer"). | RHS, a. a. O. | confirmed |
| Lichtbedarf Fruchtgemüse vs. Blatt-/Wurzelgemüse (R-017 aus REQ-054, betrifft `light_requirement`) | nicht in REQ-053 | „Fruchtgemüse 6–8 h, Blattgemüse 3–4 h, Wurzelgemüse 4–6 h" fand sich nur in Ratgeber-Blogs, die sich auf Extension-Dienste berufen, ohne dass die Primärquelle auffindbar war. | — | unverified |

---

## B. Erreichbarkeits-Richtwerte (GP-FR-166)

| Wert | REQ-053-Annahme | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| Max. Beetbreite bei beidseitigem Zugang | 1,2 m (als „unverifiziert" markiert) | Oregon State Extension: „make beds … a maximum of 4-ft wide if accessible from both sides" (= 1,22 m). Iowa State Extension: „Beds accessible on both sides can be 3 to 4 feet wide." Ministerium Klimaschutz/Umwelt RLP (Umwelt im Alltag, Aug. 2019, Hochbeete): „Bei der Breite gelten 120 cm als sinnvoll (beidseitig zugänglich, sonst schmäler)." | OSU, Raised Bed Gardening, http://extension.oregonstate.edu/sites/extd8/files/documents/12281/raisedbed.pdf; ISU Yard and Garden, https://yardandgarden.extension.iastate.edu/faq/how-do-i-construct-raised-bed-what-good-size-raised-bed-planter; MKUEM RLP 2019, https://mkuem.rlp.de/fileadmin/14/Service/Publikationen/UiA-August_2019_Hochbeete.pdf | confirmed |
| Max. Beetbreite bei einseitigem Zugang | 0,6 m (als „unverifiziert" markiert) | OSU: „a maximum of 2-ft wide if accessed from one side" (= 0,61 m). ISU: „accessible from only one side, the maximum width should be 1 1/2 to 2 feet" (0,46–0,61 m). Der im Review H-001 genannte Wert 0,8 m stammt nur aus einem Ratgeber (gartenjournal, tertiär) und ist nicht gedeckt. | OSU, ISU, a. a. O. | confirmed (0,6 m als Obergrenze) |
| Wegbreite (H-001: ≥ 0,3–0,5 m) | nicht in REQ-053 | OSU: Wege „14 to 16 inches wide" (0,36–0,41 m) zwischen Beeten. Hauptwege für Schubkarre (Ratgeber: 0,6–0,7 m) ohne institutionelle Quelle. | OSU, a. a. O. | confirmed (Nebenweg 0,35–0,40 m) / unverified (Hauptweg) |
| Reichweiten-Begründung | implizit | OSU: „To reach everything in the bed without stepping into it"; Wikipedia Square Foot Gardening: Armreichweite ≈ 2 ft. Begründung ist Armlänge, nicht Kulturtechnik — gilt daher für Hochbeet und Flachbeet gleich. | OSU, a. a. O. | confirmed |

---

## C. Anbaupausen je Familie (GP-FR-131 `BotanicalFamily.rotation_pause_years`)

Belastbare Quellen mit Familientabelle: **LKSH** (Landwirtschaftskammer Schleswig-Holstein, „Fruchtfolge im Garten", PDF-Stand 2020), **SBB** (Südtiroler Bauernbund, Merkblatt „Fruchtfolgen im Gemüsebau", Tabelle 1 „Empfohlene Anbaupausen", Datei vom 2022-11-23), **ÖLN** (Schweizer Fruchtfolgeregelung Gemüsebau 2025 — *Vorschrift*, nennt maximale Belegungen in 7 Jahren, also eine Untergrenze, keine Empfehlung), **AGES** (Kartoffelzystennematoden), **ISIP** (Gemüsebroschüre 2026, Kap. 11 Zwiebel). Plantura ist tertiär und steht nur zur Einordnung.

| Familie | REQ-053-Annahme | Befund (Jahre) | Begründung in den Quellen | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|---|
| Brassicaceae | Default je Familie offen; GP-ACC-047 rechnet mit 4 | LKSH: „Kreuzblütler nur alle 4 Jahre"; SBB: 4–5; SBB Text: „Anbaupausen von mindestens vier Jahren, auf gefährdeten Anbauflächen sogar längere"; ÖLN: max. 3 Belegungen/7 J; Plantura (tertiär): 5–6. **Default 4.** Nach Kohlhernie-Befall: LKSH „Anbaupause von mindestens 7 Jahren … und … aufzukalken". | Kohlhernie (*Plasmodiophora brassicae*), Dauersporen „über viele Jahre"; befällt auch Raps, Radies, Gelbsenf-Gründüngung (LKSH). | LKSH, https://www.lksh.de/fileadmin/PDFs/Gartenbau/Fruchtfolge_im_Garten.pdf (2020); SBB, https://www.sbb.it/public/fileadmin/user_upload/Innovation/Hauptseite_Innovation/INNOProdukte/221123_Fruchtfolge.pdf (2022); ÖLN, https://www.gemuese.ch/media/3ckjp3qd/2025_fruchtfolgeregelung-mit-tabelle-d.pdf (2025) | confirmed (4) |
| Solanaceae | offen | SBB: 4 („Anbaupausen von mindestens vier Jahren zwischen Kartoffelkulturen oder anderen Nachtschattengewächsen"); AGES: „Kartoffeln höchstens alle vier Jahre auf der gleichen Fläche"; ÖLN: max. 3/7 J (Tomate max. 2/7 J); Plantura (tertiär): 4. **Default 4.** | Kartoffelzystennematoden (Zysten „bis zu 20 Jahre" lebensfähig, AGES), Kartoffelkäfer (überwintert im Boden), Rhizoctonia, Kraut- und Knollenfäule (SBB). | SBB 2022; AGES, https://www.ages.at/themen/schaderreger/kartoffelzystennematoden/ (2026) | confirmed (4) |
| Apiaceae | offen | SBB: 4–5; Plantura (tertiär): 3–4; ÖLN: max. 3/7 J. Überschneidung bei **4**. LKSH: keine Zahl, nur Folgekultur-Tabelle. | SBB nennt keine spezifische Ursache; LKSH (Gemüsefliegen): Möhrenfliege überwintert als Puppe im Boden, zwei (selten drei) Generationen; Nematoden (LKSH Fruchtfolge). | SBB 2022; LKSH Gemüsefliegen, https://www.lksh.de/fileadmin/PDFs/Gartenbau/Gemuesefliegen.pdf (o. J.) | confirmed (4; Spanne 3–5) |
| Fabaceae | offen | LKSH: „Erbsen nicht häufiger als alle 6 bis 7 Jahre"; SBB: Erbse 5–6, **Bohne 3–4**; Plantura (tertiär): 5–6; ÖLN: Gemüseerbse max. 2/7 J, Puffbohne 3/7 J. Überschneidung für Erbse bei **6**. Ein einzelner Familienwert deckt Bohne und Erbse nicht: Erbse 6, Bohne 4 (SBB-Obergrenze). | „Fußkrankheit"/Fusarium-Welke, Dauersporen „bis zu 20 Jahren" (LKSH); *Aphanomyces euteiches* „can persist in infested soils 10 years or more" (PNW). | LKSH 2020; SBB 2022; PNW Handbook Pea–Aphanomyces, https://pnwhandbooks.org/node/3169 (rev. 2026) | corrected (Familie 6 mit Spezies-Override *Phaseolus* 4) |
| Alliaceae / Amaryllidaceae | offen | SBB: 4; Plantura (tertiär): 5; ÖLN: Zwiebel/Knoblauch max. 2/7 J, Lauch 3/7 J. **Default 4.** Nach Weißfäule-Befall: ISIP „Anbaupause von ca. 5 Jahren"; Sklerotien überdauern 15–20 Jahre (UC IPM, RHS). | Zwiebelweißfäule (*Sclerotium/Stromatinia cepivorum*): „Wurzelausscheidung der Allium-Pflanzen regen die Sklerotien zur Keimung an" (ISIP); Purpurfleckenkrankheit des Lauchs, Lauchmotte (SBB). | SBB 2022; ISIP 2026, https://www.isip.de/resource/blob/858118/3626a75da6a2b1fd090e50bca6904f78/isip-gemuese-broschuere-2026-kapitel11-zwiebel-data.pdf; UC IPM, https://ipm.ucanr.edu/home-and-landscape/white-rot/; RHS, https://rhs.org.uk/disease/onion-white-rot | confirmed (4) |
| Cucurbitaceae | offen | SBB: 4–5; Plantura (tertiär): 3–4; ÖLN: max. 2/7 J (strengste Regelung der Tabelle). Überschneidung bei **4**. | In den Quellen nicht spezifisch begründet (allgemein bodenbürtige Erreger). | SBB 2022; ÖLN 2025 | confirmed (4; Spanne 3–5), Begründung unverified |
| Asteraceae | offen | SBB: 3; Plantura (tertiär): 3; ÖLN: max. 3/7 J. **Default 3.** | Nicht spezifisch begründet. | SBB 2022; ÖLN 2025 | confirmed (3), Begründung unverified |
| Chenopodiaceae / Amaranthaceae | offen | SBB: 3–4; Plantura (tertiär): 3; ÖLN: max. 3/7 J (Mangold, Rote Bete 2/7 J). **Default 3.** | Rübenzystennematode *Heterodera schachtii* (LfL: Hauptproblem im Rübenbau; Wirtskreis schließt Senf/Ölrettich ein, nur resistente Sorten Note 1–3 senken die Population). | SBB 2022; LfL, https://lfl.bayern.de/ips/blattfruechte/034173/ (Stand 2018) | confirmed (3) |
| Poaceae (Zuckermais) | offen | LKSH-Tabelle: „Gräser — Zuckermais — alle anderen Pflanzenfamilien" (keine Pause genannt); SBB: kein Eintrag; ÖLN: max. 3/7 J; nur Plantura (tertiär) nennt 3. Keine belastbare Empfehlung. | — | LKSH 2020; ÖLN 2025 | unverified (Default `null` → Fallback `rotation_window_years`) |
| Gleiche *Art* (Spezies-Override-Minimum) | — | LKSH: „Dieselbe Pflanzenart ist frühestens nach einer Anbaupause von 3 Jahren wieder auf derselben Fläche anzubauen." | — | LKSH 2020 | confirmed (3 als Untergrenze für `Species.rotation_pause_years`) |
| Obergrenze `rotation_pause_years` 8 (K-004) | 8 | Die Empfehlungen liegen bei 3–7; 8 reicht. **Sperrdauern nach Befall** (Kohlhernie ≥ 7, PCN 15–20, Weißfäule 15–20, Aphanomyces ≥ 10) gehören nicht in dieses Feld, sondern in `soil_persistence_years` (REQ-054 H-10). | — | LKSH; AGES; UC IPM; PNW | confirmed (8), mit Abgrenzung |

Persistenz der Dauerstadien (Belege für die Begründungen und für REQ-054 H-10):

| Erreger | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|
| *Plasmodiophora brassicae* (Kohlhernie) | PNW: „half-life that ranges from three to six years", „may survive upwards of 10 years or longer"; Reading-Review (Dixon): Halbwertszeit ≥ 3,6 Jahre (Wallenhammar 1996), Nachweisbarkeit bis ≥ 18 Jahre. | PNW Handbook, Cabbage–Clubroot (Ocamb, rev. März 2026), https://pnwhandbooks.org/plantdisease/host-disease/cabbage-cauliflower-brassica-sp-clubroot; Dixon, Univ. Reading CentAUR, https://centaur.reading.ac.uk/66432/ (Zeitschriftenfassung J. Plant Growth Regul. 2009; Jahr nicht aus dem Abruf, sondern aus der Zitation) | confirmed |
| *Globodera* spp. (Kartoffelzystennematoden) | AGES: „Diese Zysten überdauern jahrelang (bis zu 20 Jahre) lebensfähig im Boden."; „Aussetzen des Kartoffelanbaues für einen Zeitraum von 15 – 20 Jahren". Dänische Landbrugsstyrelse: 10–20 Jahre. | AGES 2026, a. a. O.; Landbrugsstyrelsen DK, https://lbst.dk/Media/638505994439246645/Kartoffelcystenematoder.pdf | confirmed |
| *Sclerotium cepivorum* (Weißfäule) | UC IPM / RHS: Sklerotien 15–20 Jahre, auch ohne Wirt. | UC IPM, RHS, a. a. O. | confirmed |
| *Aphanomyces euteiches* (Erbsenmüdigkeit) | PNW: „can persist in infested soils 10 years or more"; „Long rotations are the best way to manage the disease." | PNW Handbook, a. a. O. (rev. 2026) | confirmed |
| *Pyrenochaeta lycopersici* (Korkwurzel, Tomate im Gewächshaus) | UMD Extension: Mikrosklerotien bis 15 Jahre; Wirte u. a. Gurke, Aubergine, Salat, Melone, Paprika; „crop rotation alone may not be effective". | UMD Extension, https://extension.umd.edu/resource/corky-root-disease-tomatoes (Okt. 2024) | confirmed |

---

## D. Reihen- und Pflanzabstände, Dreiecksfaktor, Randabstand (GP-FR-060/061/062/073)

| Wert | REQ-053-Annahme | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| Untergrenze Validator 5 cm | 5 cm | LWG Merkblatt 2111: Radieschen und Palerbsen „Abstand in der Reihe 5 cm"; Feldsalat Reihenabstand 10–15 cm. 5 cm ist die kleinste in einer Fachquelle genannte Distanz. | LWG Bayern, Merkblatt 2111 „Fruchtfolge für Gemüsebeete" (2016), https://www.lwg.bayern.de/mam/cms06/gartenakademie/dateien/2111-2016.pdf | confirmed |
| Obergrenze Validator 1 000 cm (Gehölze, Streuobst — W-004) | 1 000 cm | Sachsen (SMUL Merkblatt Streuobstpflanzung 2024): „etwa 10 m", Apfel 12 m, Süßkirsche 12–15 m; RLP (Agrarumwelt 2024): „mindestens 15 m" bzw. „15 m, mindestens jedoch 10 m"; Walnuss 12–15 m (Odenwaldkreis 2024). 1 000 cm schließt Hochstamm-Kirsche und Walnuss aus. | SMUL Sachsen, https://smul-foerderung.sachsen.de/download/20240410_MB_A1_Streuobstpflanzung.pdf (2024); Agrarumwelt RLP, https://www.agrarumwelt.rlp.de/Internet/global/themen.nsf/35d111349ec35202c1257e9d004eb411/72d907504ae1e716c1258879001fe255/$FILE/VN_SONP_GAP-FP_20240617.pdf (2024); Odenwaldkreis, https://odenwaldkreis.de/de/dienstleistungen/umwelt-naturschutz-und-landschaftspflege/streuobst/streuobstaktion/2024-info-zu-wildobst.pdf (2024) | corrected (→ 1 500 cm) |
| Plausibilität Reihenabstand typischer Gemüse | 5–1 000 cm | LWG 2111: Chinakohl 40/35, Paprika 40–50/40–50, Salate 30/30, Spinat 20–25, Steckzwiebeln 25/10, Tomate 50 cm bzw. „1 Reihe/Beet". Alle innerhalb 5–1 000 cm. | LWG 2111 (2016) | confirmed |
| `triangular`: `row_spacing = spacing × 0,866` | 0,866 | √3/2 = 0,8660 ist der Reihenabstand eines gleichseitigen Dreiecksverbands (Höhe des Dreiecks); Dichte 2/(√3·a²) = +15,5 % gegenüber Quadratverband. Praxisbeleg Dreiecksverband (Zuckerrübe, topagrar). Die Zahl ist Geometrie, keine agronomische Setzung. | topagrar, „Höhere Zuckererträge im Dreiecksverband", https://www.topagrar.com/acker/aus-dem-heft/hoehere-zuckerertraege-im-dreiecksverband-9651479.html; Rechner (tertiär) https://www.gartenjournal.net/gartenplaner/rechner/pflanzen-pro-qm | confirmed |
| GP-FR-073: `triangular` 1/(spacing² × 0,866) | Formel | Identisch mit 2/(√3·a²). Korrekt. | Geometrie | confirmed |
| Randabstand Standard `spacing/2` bzw. `row_spacing/2` | spacing/2 | Keine Fachquelle gefunden; Square-Foot-Gardening-Literatur definiert keinen Randabstand; einzige Nennung „half a row width" ist ein Forumsbeitrag (2006). Eingefasste Hochbeete erlauben nach Praxisaussage engere Randpflanzung als offene Beete. | — | unverified (Konvention; konfigurierbar lassen) |
| Warnung `spacing_cm < mature_width_cm × 0,7` (GP-FR-061) | 0,7 | Keine Quelle für den Faktor. | — | unverified |
| Reihenrichtung Nord–Süd (W-002, R-009) | Hinweis | Nur Ratgeber und topagrar-Praxisbericht („Lage … von Nord nach Süd ausgerichtet"); keine Landesanstalt-Quelle gefunden. | topagrar AT, https://www.topagrar.com/oesterreich/die-vielfalt-der-gemuesebeete-13355639.html | unverified (plausibel, nicht institutionell belegt) |

---

## E. Nachbarschaftsfaktor und Interaktionsradius (GP-FR-130)

| Wert | REQ-053-Annahme | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| `adjacency_factor` 1,5 × max(spacing, row_spacing) | 1,5 | Die Herleitung ist rein geometrisch (Diagonale √2 = 1,41 ein, übernächster Dreiecksnachbar √3 = 1,73 aus). Keine Literatur definiert „Nachbarschaft" in Mischkultur metrisch; ATTRA/SARE sprechen von „close proximity" ohne Distanz. | ATTRA Companion Planting (via ECHOcommunity), https://www.echocommunity.org/resources/bff26781-8ced-4f24-946b-19cf72fe765e; SARE FNC10-814, https://projects.sare.org/?p=471670 | unverified (geometrisch konsistent, agronomisch unbelegt) |
| Interaktionsradius `(w_a + w_b)/2 × 1,2` bei bekanntem `mature_width_cm` | 1,2 | Für Kronen-/Schatteneffekte ist 1,0–1,2 × Kronenradius plausibel, aber nicht belegt. Für Wurzelkonkurrenz bei Gehölzen reicht die Wurzel „two to three times the dripline" (UF Extension); Gilman 1988: Mittel 2,9 × Dripline (1,7–3,8). Für Gemüse keine Daten. | UF/IFAS, https://hort.ifas.ufl.edu/woody/root-growth-lateral4.shtml; Gilman, J. Arboriculture 14(4):85, 1988, https://auf.isa-arbor.com/content/14/4/85 | unverified (1,2); corrected für Gehölze (Wurzelreichweite 2–3 × Kronenradius belegt) |
| Beetübergreifend ≤ 50 cm (SHOULD) / Nachbarbeet-Faktor 0,5 (REQ-054) / Allelopathie-Schwelle 30 cm (REQ-054 R-009) | 50 cm / 0,5 / 30 cm | Keine Quelle, die Wirkabstände von Wurzelausscheidungen oder Duftwirkung zwischen Beeten quantifiziert. | — | unverified |
| Wirksamkeit von Mischkultur überhaupt (REQ-054 R-015) | implizit | Meta-Analysen: Letourneau et al. (552 Experimente, 45 Artikel) — Diversifizierung senkt Herbivoren signifikant, Ertrag leicht negativ; Kohl-Intercropping-Meta-Analyse (WUR): Schädlingsschaden −48 % bzw. −53 %, Ertrag −6/−7 %; Leguminosen-Begleitpflanzen (INRAE, 34 Artikel): weniger Unkraut und höherer Ertrag in 52 %/36 % der Fälle. Gartenpaar-Folklore (Bomford 2004): keine konsistenten Effekte. **Systemeffekt belegt, Paarwirkung je Kombination heterogen.** | USFQ/Letourneau, https://research.usfq.edu.ec/en/publications/does-plant-diversity-benefit-agroecosystems-a-synthetic-review/; WUR, https://edepot.wur.nl/632108; INRAE, https://prodinra.inra.fr/record/387698; Bomford 2004, https://orgprints.org/6614/1/6614.pdf | confirmed (System) / unverified (Einzelpaare) |
| Juglon (Walnuss) als Standortgefahr (REQ-054 R-010) | `soil_hazards[juglone]` vorgeschlagen | Extension: Tomate „one of the most sensitive"; Wirkzone „within the drip line … can extend as far as 50 feet from the trunk" bzw. „50 to 60 feet"; nach Fällung 1–2 Jahre (Quellen uneins). → Attribut ist fachlich nötig; Radius 15–18 m vom Stamm. | Cornell CALS, https://cals.cornell.edu/school-integrative-plant-science/school-sections/horticulture-section/outreach-and-extension/pandemic-vegetable-gardening/pandemic-vegetable-gardening-2020-archive/answers-your-midsummer-gardening-questions; Ask Extension, https://ask2.extension.org/kb/faq.php?id=848233; Morton Arboretum, https://mortonarb.org/?p=87881 | confirmed |

---

## F. Recherchepunkte im Einzelnen

### F.1 — R-001…R-013 aus `agrobiology-review-req-053.md`

| R | Behauptung | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| R-001 | Dreiecksraster 2/√3 ≈ 1,155 | Dichtefaktor 2/√3 = 1,1547 (+15,5 %), Reihenabstand √3/2 — Geometrie. | siehe D | confirmed |
| R-002 | Textur-Klassen, Fingerprobe (KA5, LfL) | LfL Schulungsunterlage Fingerprobe (2009): KA5-Diagramm mit 31 Unterarten; LfL-Standard nutzt vereinfacht 8 Unterarten nach Ton-/Schluffanteil; Fingerprobe „für Spezialfragen nicht ausreichend". AGES Fingerprobe-Anleitung. | LfL, https://www.lfl.bayern.de/mam/cms07/zentrale_analytik/dateien/fingerprobe.pdf (2009); AGES Fingerprobe.pdf (ages.at) | confirmed |
| R-003 | Pausen Kohl 4+, Kartoffel 3–4, Erbse bis 6, Zwiebel/Möhre 3–4, Tomate 3–4 | Kohl 4 ✓; Kartoffel/Tomate **4** (nicht 3–4; SBB „mindestens vier", AGES „höchstens alle vier Jahre"); Erbse **6–7** (LKSH), nicht „bis 6"; Zwiebel **4** (SBB); Möhre 4 (SBB 4–5). | siehe C | corrected |
| R-004 | VDLUFA-Gehaltsklassen A–E, Nmin | LHL Hessen (2024): Klassen A (sehr niedrig, 0–1,9 mg P/100 g) bis E (sehr hoch, ≥ 12,0 mg P/100 g), CAL-Methode, bodenartabhängig; LfL Bayern: anzustrebende Klasse C = 10–20 mg P₂O₅/100 g; N über Nmin, nicht über Klassen (LfL Düngebedarfsermittlung). | LHL, https://lhl.hessen.de/sites/lhl.hessen.de/files/2024-03/erlaeuterungen_bodenuntersuchung_acker_und_gruenland.pdf (2024); LfL, https://lfl.bayern.de/mam/cms07/iab/dateien/duengebedarfsermittlung_ackerland_blw-1-2018.pdf (2018) | confirmed |
| R-005 | Mulch senkt Verdunstung; Tropf ~90 %, Beregnung niedriger | FAO-56 Kap. 10: Plastikmulch senkt Bodenverdunstung „50-80%", Kc mid/end −10–30 %; organischer Mulch „about 5% for each 10% of soil surface" bedeckt. Tropf-Effizienz: Alberta/Howell 2003: Tropf 70–95 % (Design 88 %), Oberflächenbewässerung 40–80 % (Design 62 %); USDA FRIS 2013 via UC: Tropf 85–90 %, Beregnung 70–90 %. Die REQ-Formel „Tropf ~90 %" liegt am oberen Rand. | FAO-56, https://www.fao.org/4/X0490E/x0490e0g.htm (1998); Alberta Agdex 563-1, https://www1.agriculture.alberta.ca/$department/deptdocs.nsf/all/agdex13729/$file/563-1.pdf; UC/CDFA, https://secure.cdfa.ca.gov/egov/waterinag/docs/Khaled_Bali_UC.pdf | confirmed (Mulch) / corrected (Tropf 85–90 %, Design 88 %) |
| R-006 | Ziel-pH nach Bodenart; CaCl₂ vs. H₂O | LfL Tabelle 8a (Nov. 2024): Kalkbedarf wird 0 ab pH 5,9 (Sand), 6,4 (schwach lehmiger Sand), 6,9 (stark lehmiger Sand bis schluffiger Lehm), > 7,2 (toniger Lehm bis Ton) — das sind die Zielbereiche für Ackerboden. NRW-Ökolandbau-Tabelle (2025) ist **Grünland** (S 5,0 … utL/tL/T 6,1) und nicht übertragbar. Unterschied CaCl₂/H₂O-Messung nicht geprüft. | LfL, https://www.lfl.bayern.de/mam/cms07/iab/dateien/bas25_tabelle_8a_20241125.pdf (2024); NRW, https://www.oekolandbau.nrw.de/system/files/media/document/file/2025_kalkung-tabelle1.pdf (2025) | confirmed (Ziel-pH) / unverified (Messmethode) |
| R-007 | Rindenmulch bindet N | Natur im Garten (Land Salzburg, Mulchen): Zersetzung bindet Stickstoff → N-Mangel im gemulchten Beet; Ausgleich mit Hornspänen. Mengen (50–60 g/m²) nur von Herstellern. | Land Salzburg, https://www.salzburg.gv.at/umweltnaturwasser_/Documents/Dokumente%20Programm%20Natur%20in%20Salzburg/Natur%20im%20Garten/NiG_Mulchen.pdf | confirmed (Effekt) / unverified (Menge) |
| R-008 | Spülvolumen als Vielfaches des Topfvolumens | Keine Fachquelle gefunden. | — | unverified |
| R-009 | Beetbreite ≤ 1,2 m; Nord-Süd-Reihen | Beetbreite: confirmed (B). Nord-Süd: nur Ratgeber. | siehe B, D | confirmed / unverified |
| R-010 | Obere Regalebenen wärmer; PPFD-Gleichmäßigkeit | Nicht recherchiert (außerhalb der O-17-Fragen; CEA-Literatur erforderlich). | — | unverified |
| R-011 | Sonnenstundenschwellen | RHS: > 6 / 3–6 / < 2 h at midsummer. | siehe A | confirmed |
| R-012 | Magnetische Missweisung Mitteleuropa (geografisch Nord!) | NOAA WMM2025 (v1.2.1) für 51° N / 10° E, Okt. 2026: **+4,17° Ost** (± 0,38°). Ein Kompass zeigt also ≈ 4° östlich von geografisch Nord; `north_angle_deg` muss das dokumentieren, wenn Nutzer per Kompass messen. | NOAA NCEI Geomagnetic Calculator, https://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination (2026) | confirmed |
| R-013 | Zehrerklassen variieren je Quelle | Beleg: Spinat ist bei LKSH **Mittelzehrer**, beim SBB **Schwachzehrer**; Möhre bei beiden Mittelzehrer; Zucchini/Kürbis Starkzehrer bei beiden. Quelle je Steckbrief bleibt Pflicht. | LKSH 2020; SBB 2022 | confirmed |

### F.2 — R-001…R-024 aus `agrobiology-review-req-054.md`

| R | Behauptung | Befund | Quelle (URL, Jahr) | Status |
|---|---|---|---|---|
| R-001 | Dauerstadien persistenter Bodenpathogene — Jahre je Erreger | Kohlhernie HWZ 3–6 J, ≥ 10 J (PNW), bis 18 J (Dixon); PCN bis 20 J (AGES); Weißfäule 15–20 J (UC IPM); Aphanomyces ≥ 10 J (PNW); Fußkrankheit Erbse „bis zu 20 Jahren" (LKSH); Korkwurzel 15 J (UMD). | siehe C (Persistenztabelle) | confirmed |
| R-002 | Familienübergreifende Wirtskreise | *H. schachtii*: Senf/Ölrettich sind Wirte, nur resistente Sorten (Note 1–3) senken Population um 50–75 % (LfL; BBA 1990); Kohlhernie befällt Senf-/Rapsgründüngung (LKSH); *Pyrenochaeta* Wirte über 4 Familien (UMD). *Meloidogyne hapla*-Wirtskreis nicht gefunden. | LfL 2018, a. a. O.; LKSH 2020; UMD 2024 | confirmed (teilweise) / unverified (*M. hapla*) |
| R-003 | Mittel des letzten Frosts = 50 % Risiko; 10 %-Datum; Eisheilige | Statistischer Grundsatz trivial richtig; ein DWD-Perzentilprodukt für Frostdaten wurde nicht gefunden. Zeitungsauswertung (30-Jahres-Spätestwerte je Landeshauptstadt) ist keine Fachquelle. | — | unverified (Produkt) |
| R-004 | Photoperiodisches Schossen (Spinat, Salat, Chinakohl) | Spinat: Langtagpflanze, Blühinduktion ab ca. 12–14 h Tageslänge (Plantura 10–14 h, tertiär; wissen.de ≥ 12 h); LfULG Sachsen Sortenversuche Sommerspinat (2013, 2019): Schossfestigkeit sortenabhängig, Wachstumsstockung > 30 °C. Salat/Chinakohl nicht geprüft. | LfULG, https://www.gartenbau.sachsen.de/download/Spinat_Sommer_2019.pdf (2019); https://www.gartenbau.sachsen.de/download/Spinat_Sommer_13.pdf (2013) | confirmed (Spinat) / unverified (Salat, Chinakohl, exakte Stundenschwelle) |
| R-005 | N-Gutschrift je Leguminosenform | LWK NRW (2022, Demo, „nicht statistisch verifiziert"): N-Fixierung Zwischenfrucht-Erbse ≈ 129 kg N/ha, Ackerbohne 71–93 kg N/ha. DüV Anlage 4 Tab. 3 regelt die Vorfrucht-Anrechnung; Werte nicht abgerufen. | LWK NRW, https://www.oekolandbau.nrw.de/fileadmin/redaktion/PDFs/Fachinfo/Leguminosen/2022/2022-Leguminosentag-03_-_Gerbaulet_-_Stickstoff_binden_und_halten.pdf (2022); DüV Anl. 4, https://www.gesetze-im-internet.de/d_v_2017/anlage_4.html | unverified (konkrete Gutschrift) |
| R-006 | Reifezeit-Streuung; 14-Tage-Puffer | Keine Quelle. | — | unverified |
| R-007 | VDLUFA-Klassen je Nährstoff; N nicht über Klassen | Wie R-004 (053): Klassen für P, K, Mg je Bodenartgruppe; N über Nmin. | LHL 2024; LfL 2018 | confirmed |
| R-008 | Hochbeet: Starkzehrer im ersten Jahr, Salat/Spinat erst ab Jahr 2 (Nitrat) | Nur Bauanleitung/Ratgeber (Holztechnikum Kuchl 2017; toom; utopia); keine Landesanstalt. | Holztechnikum, https://www.holztechnikum.at/wp-content/uploads/2017/07/htk-bauanleitunghochbeet.pdf (2017) | unverified (nur Praxisliteratur) |
| R-009 | Allelopathie-Wirkabstand 30 cm | Keine Quelle. | — | unverified |
| R-010 | Fenchel-Allelopathie; Juglon/Solanaceae; Roggen-Hemmung | Fenchel: keine Quelle. Juglon: confirmed (E). Roggen: MSU Extension empfiehlt ca. 2 Wochen zwischen Einarbeitung und Pflanzung; kleinsamige Direktsaaten besonders empfindlich; Dauer abhängig von C/N und Reifegrad. | MSU Extension, https://canr.msu.edu/news/managing_cereal_rye_cover_crop_to_reduce_crop_injury_and_improve_benefits | unverified (Fenchel) / confirmed (Juglon, Roggen 2 Wochen) |
| R-011 | pH-Grenzen Heidelbeere; Kohlhernie-pH | Heidelbeere: PNW 4,5–5,5; Penn State 4,5–5,0 → harte Grenze > 5,5 belegt. Kohlhernie: Kalkung auf pH ≥ 7 (7,3–7,5) (PNW 2026); ≥ 7,1 (OSU 2014); > 7,2–7,3 (UC Salinas); Kalk tötet den Erreger nicht, verhindert Infektion. | PNW Blueberry pH, https://pnwhandbooks.org/node/2312; Penn State, https://extension.psu.edu/site-selection-and-preparation-for-home-blueberry-plantings; PNW Clubroot 2026; UC ANR, https://ucanr.edu/node/105348 | confirmed |
| R-012 | `usable_fraction` 0,9 / Wegeanteil | Keine Quelle. | — | unverified |
| R-013 | Wartezeit nach Gründüngung | Roggen: ~2 Wochen (MSU); deutsche Fachquelle (LfL/Bioland) mit Wochenangabe nicht gefunden; artabhängig. | MSU, a. a. O. | confirmed (Roggen) / unverified (allgemein) |
| R-014 | Insektenrisiko im Boden (Möhren-, Kohlfliege) | LKSH: „Wie alle Gemüsefliegen überwintert die Kleine Kohlfliege als Puppe im Boden auf vorjährig befallenen Flächen"; 2–3 Generationen; Möhrenfliege 2 (selten 3) Generationen, schlüpft ab Anfang Mai aus der Winterpuppe. → 1-Jahres-Bezug belegt; ein 2-Jahres-Fenster ist nicht belegt. | LKSH Gemüsefliegen, a. a. O. | confirmed (1 Jahr) / unverified (2 Jahre) |
| R-015 | Evidenz Mischkultur je Paar | Systemeffekt belegt (Meta-Analysen), Einzelpaare nicht. | siehe E | confirmed / unverified |
| R-016 | Nachbarbeet-Faktor 0,5 | Keine Quelle. | — | unverified |
| R-017 | Lichtbedarf Fruchtgemüse vs. Blattgemüse; Hitze kühler Kulturen im Gewächshaus | Stundenwerte nur in Blogs (A). Hitzestress: LfULG Sommerspinat > 30 °C Wachstumsstockung (Freiland, nicht Gewächshaus). | LfULG 2019 | unverified |
| R-018 | Kalkung gegen Kohlhernie / Schorf | Kohlhernie: confirmed (R-011). Schorf: nicht geprüft. | siehe R-011 | confirmed / unverified (Schorf) |
| R-019 | Erntedauer Tomate/Zucchini | Nur Ratgeber (Tomate Freiland Juli–Sept./Okt.). | — | unverified |
| R-020 | Kulturdauer temperaturabhängig (GDD) | Univ. Kentucky: GDD-Modelle für Pflücksalat, R² > 0,70; Cornell/SARE: GDD × Tageslänge verbessert Vorhersage. | UKY, https://uknowledge.uky.edu/pss_etds/161; SARE FNE11-718, https://projects.sare.org/project-reports/fne11-718/ | confirmed |
| R-021 | Gewächshaus-Offset zum Freiland | Ratgeber: Gewächshauspflanzung ab Mitte April vs. Freiland nach Mitte Mai (~4 Wochen); keine Fachstelle. | — | unverified |
| R-022 | Tomate im Tunnel: Bodenwechsel, Veredelung | Korkwurzel: Mikrosklerotien 15 J, Fruchtfolge allein unzureichend (UMD); Veredelung als Maßnahme in den Treffern nicht belegt. | UMD 2024 | unverified (Maßnahmen) |
| R-023 | Familien-Pausen | siehe C: alle außer Poaceae belegt. | siehe C | confirmed / unverified (Poaceae) |
| R-024 | Zehrerstufen der Goldfall-Arten | Quellen widersprechen sich (Spinat). Quelle je Steckbrief nötig. | LKSH; SBB | confirmed (Varianz) |

---

## Empfohlene Änderungen an REQ-053

1. **GP-FR-164** — Text ersetzen durch: „Schwellen und Referenzdatum der Sonnenklassen sind Konfiguration am Tenant/Site. Standard (geprüft O-17, RHS): `full_sun` > 6 h, `partial_shade` 3–6 h, `shade` 2–3 h, `deep_shade` < 2 h direkter Sonne im Hochsommer (Referenzdatum 21. Juni). Mittagssonne liefert deutlich mehr Licht als Morgen- oder Abendsonne (RHS); eine Gewichtung nach Tageszeit ist nicht Teil des MVP."
2. **GP-FR-157** — Hilfetexte ergänzen: „Schatten: 2 bis 3 Stunden direkte Sonne", „Tiefschatten: weniger als 2 Stunden direkte Sonne (RHS)". Den Zusatz „Schwellen konfigurierbar, GP-FR-164" beibehalten.
3. **GP-FR-166** — „Richtwerte 1,2 m bei beidseitigem, 0,6 m bei einseitigem Zugang sind **unverifiziert**" ersetzen durch „… sind **belegt** (Oregon State Extension, Iowa State Extension, MKUEM RLP 2019: 4 ft / 2 ft bzw. 120 cm beidseitig)". Optional: Hinweis `bed.path_too_narrow` bei Wegbreite < 0,35 m (OSU 14–16 in) als SHOULD/COULD aufnehmen.
4. **GP-FR-060** — Obergrenze `spacing_cm` und `row_spacing_cm` von 1 000 auf **1 500 cm** anheben (Hochstamm-Kirsche 12–15 m, Walnuss 12–15 m, RLP-Förderung „mindestens 15 m"). `seed-data-validator` in GP-FR-061 entsprechend auf 5–1 500 cm. Randabstand `spacing/2` bleibt Standard, wird aber als „Konvention, nicht fachlich belegt" markiert.
5. **GP-FR-062 / GP-FR-073** — keine Änderung am Faktor 0,866; im Dialogtext (§11.1) die „berechnete Mehrzahl" als „+15,5 % gegenüber Quadratverband" beziffern.
6. **GP-FR-061** — Warnung `spacing_cm < mature_width_cm × 0,7` als „unverifizierter Faktor, konfigurierbar" kennzeichnen.
7. **GP-FR-130** — Ergänzen: „`adjacency_factor` 1,5 und der Interaktionsradius 1,2 × mittlere Reifebreite sind geometrische Konventionen ohne agronomischen Beleg (O-17) und bleiben konfigurierbar. Für Gehölze (`growth_form` Baum/Strauch) ist die Wurzelreichweite mit 2–3 × Kronenradius belegt (Gilman 1988; UF/IFAS); der Interaktionsradius darf dort per Konfiguration auf 2,0 gesetzt werden." Die Schwelle „Beetkanten ≤ 50 cm" bleibt SHOULD und unverifiziert.
8. **GP-FR-131** — Seed-Defaults für `BotanicalFamily.rotation_pause_years` mit Quelle je Wert: Brassicaceae 4 (LKSH, SBB), Solanaceae 4 (SBB, AGES), Apiaceae 4 (SBB), Fabaceae 6 (LKSH, SBB — Erbse) mit `Species.rotation_pause_years` = 4 für *Phaseolus vulgaris* (SBB), Amaryllidaceae 4 (SBB), Cucurbitaceae 4 (SBB), Asteraceae 3 (SBB), Amaranthaceae 3 (SBB), Poaceae `null` (Fallback `rotation_window_years`, unverifiziert). Untergrenze für `Species.rotation_pause_years` = 3 (LKSH „dieselbe Pflanzenart frühestens nach 3 Jahren"). Begründungstexte je Familie wie in Tabelle C („Kohlhernie-Risiko", „Kartoffelzystennematoden", „Möhrenfliege/Nematoden", „Erbsenmüdigkeit/Fußkrankheit", „Zwiebelweißfäule", „Rübenzystennematode").
9. **GP-FR-131 / REQ-054 H-10** — Sperrdauern nach bestätigtem Befall gehören nicht in `rotation_pause_years` (Obergrenze 8): Kohlhernie ≥ 7 Jahre + Kalkung auf pH ≥ 7 (LKSH; PNW), Weißfäule ca. 5 Jahre nach ISIP (Sklerotien bis 15–20 Jahre), Kartoffelzystennematoden 15–20 Jahre (AGES), Aphanomyces ≥ 10 Jahre (PNW). Diese Werte in `soil_persistence_years` (REQ-054) übernehmen.
10. **GP-ACC-047** — `rotation_pause_years(Brassicaceae) = 4` ist belegt; Kriterium unverändert.
11. **§16.3 / Steckbrief** — Zehrerstufe nur mit Quelle je Art übernehmen (Spinat: LKSH Mittelzehrer vs. SBB Schwachzehrer); `seed-data-validator` soll eine fehlende Quelle als Lücke melden, nicht einen Default setzen (E-10).
12. **§9.3 `north_angle_deg`** — Ergänzen: „Bezug ist geografisch Nord. Die magnetische Missweisung beträgt in Deutschland derzeit ≈ +4° Ost (WMM2025, 51° N/10° E, Okt. 2026); wer per Kompass misst, zieht 4° ab. Die Abweichung ist für die Sonnenklassen unerheblich, für die Sonnenstand-Simulation (§29) nicht."

---

## Offen (unverified)

Diese Werte bleiben konfigurierbar und tragen in REQ-053/054 die Kennzeichnung „unverifiziert"; Begründung jeweils: keine belastbare Quelle gefunden.

| Thema | Betroffene Stelle | Grund |
|---|---|---|
| Hitzestress-Gewichtung Nachmittags- vs. Morgensonne | GP-FR-164 | nur Blogs; RHS belegt lediglich die höhere Lichtmenge der Mittagsstunden |
| Lichtbedarf-Stunden Fruchtgemüse (6–8 h) / Blattgemüse (3–4 h) / Wurzelgemüse (4–6 h) | `light_requirement`-Vorbelegung, REQ-054 R-017 | Extension-Primärquelle nicht auffindbar |
| Hauptwegbreite Schubkarre (0,6–0,7 m) | H-001 | nur Ratgeber |
| Randabstand `spacing/2` | GP-FR-060 | keine Fachquelle, nur Forumspraxis |
| Faktor 0,7 in `spacing_cm < mature_width_cm × 0,7` | GP-FR-061 | keine Quelle |
| Reihenrichtung Nord–Süd | W-002 / R-009 | nur Ratgeber und Praxisbericht |
| `adjacency_factor` 1,5; Interaktionsradius 1,2 (Gemüse); Beetkante ≤ 50 cm; Nachbarbeet-Faktor 0,5; Allelopathie-Schwelle 30 cm | GP-FR-130, REQ-054 R-009/R-016 | keine metrische Literatur zu Mischkultur-Wirkabständen |
| Poaceae `rotation_pause_years` | GP-FR-131 | nur tertiäre Quelle (3 Jahre) |
| Begründung der Pausen für Cucurbitaceae, Asteraceae | GP-FR-131 Hinweistext | Quellen nennen Zahl, aber keinen Erreger |
| Spülvolumen Hydroponik (× Topfvolumen) | R-008 (053) | keine Quelle |
| Regal-Etagen: Temperaturgradient, PPFD-Gleichmäßigkeit | R-010 (053) | nicht recherchiert |
| CaCl₂- vs. H₂O-pH-Differenz | R-006 (053) | nicht geprüft |
| Hornspäne-Menge zum N-Ausgleich bei Rindenmulch | R-007 (053) | nur Herstellerangaben (50–60 g/m²) |
| DWD-Perzentil-Frostdatum / 10-%-Risikodatum | REQ-054 R-003 | Produkt nicht gefunden |
| Schossschwelle Salat, Chinakohl | REQ-054 R-004 | nicht geprüft |
| N-Gutschrift je Leguminosenform (kg N/ha) | REQ-054 R-005 | DüV-Tabellenwerte nicht abgerufen; NRW-Demo nicht statistisch gesichert |
| Reifezeit-Streuung, 14-Tage-Puffer | REQ-054 R-006 | keine Quelle |
| Hochbeet-Erstjahr Starkzehrer / Nitrat | REQ-054 R-008 | nur Praxisliteratur |
| Fenchel-Allelopathie | REQ-054 R-010 | keine Quelle |
| `usable_fraction` 0,9 | REQ-054 R-012 | keine Quelle |
| Wartezeit nach Gründüngung (außer Roggen) | REQ-054 R-013 | deutsche Fachquelle mit Wochenangabe fehlt |
| 2-Jahres-Fenster Insektenrisiko | REQ-054 R-014 | nur 1-Jahres-Überwinterung belegt |
| *Meloidogyne hapla* Wirtskreis | REQ-054 R-002 | nicht gefunden |
| Schorf-pH | REQ-054 R-018 | nicht geprüft |
| Erntedauer Tomate/Zucchini | REQ-054 R-019 | nur Ratgeber |
| Gewächshaus-Offset (Wochen) | REQ-054 R-021 | nur Ratgeber (~4 Wochen) |
| Veredelung/Bodenwechsel als Tunnel-Maßnahme | REQ-054 R-022 | Maßnahme nicht belegt; Erregerpersistenz belegt |
