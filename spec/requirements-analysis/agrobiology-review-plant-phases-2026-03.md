# Agrobiologisches Review: Wachstumsphasen & i18n-Phasenbeschreibungen
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-08
**Fokus:** Botanische Korrektheit der Wachstumsphasen, Phasendauern, Reihenfolge und i18n-Texte
**Analysierte Dateien:**
- `src/backend/app/migrations/seed_data/plant_info.yaml` (S5: growth_phases, 11 Species)
- `src/frontend/src/i18n/locales/de/translation.json` (Abschnitte `enums.phaseDescription` und `enums.phaseDescriptions`)
- `src/frontend/src/i18n/locales/en/translation.json` (gleiche Abschnitte)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Phasenvollstandigkeit | 4/5 | Meiste Species gut abgedeckt; Sellerie und Erdbeere haben strukturelle Lucken |
| Phasenreihenfolge (sequence_order) | 4/5 | Logisch konsistent; Dahlie-Zyklus beginnt korrekt mit Dormanz |
| Typische Dauern | 3/5 | Mehrere Phasendauern weichen deutlich von der Literatur ab |
| i18n-Texte botanisch | 4/5 | Grosstenteils korrekt; einige Fehler in Fachterminologie |
| Konsistenz zwischen Species | 4/5 | Gleiche Phasennamen werden konsistent verwendet |
| Requirement-Profile (PPFD, VPD) | 3/5 | Mehrere problematische Parameterwerte |

**Gesamteinschatzung:** Die Phasendefinitionen sind fachlich solide und erheblich besser als viele kommerzielle Pflanzendatenbanken. Die grossten Probleme liegen bei einzelnen Phasendauern (Helianthus-Vegetativphase zu kurz, Sellerie-Knollenbildung falsch strukturiert), vereinzelten botanischen Fehlern in den i18n-Texten (Heliotropismus nur in Jugendphase, nicht als Erwachsenenphase) und einem konzeptionellen Problem bei der Erdbeere (Keimungsphase als Standard-Anbauweg irrelevant). Die YAML-Struktur und das Phasensystem sind grundsatzlich praxistauglich.

---

## 1. Species-by-Species-Analyse

### 1.1 Chlorophytum comosum (Grünlilie)

**Phasen:** establishment (30d) -> vegetative (180d) -> flowering (60d) -> mature (365d)

**Bewertung:** Botanisch korrekt und vollstandig fur eine mehrjahrige Indoor-Zimmerpflanze.

#### Befunde

**[HINWEIS H-001] Phasenname "flowering" unprdzise fur Nutzererwartung**
Die Phase heisst `flowering` (display_name: "Blüte & Kindel"), beschreibt aber im Wesentlichen den Zeitraum, in dem Auslaeufer mit Kindeln gebildet werden. Bei *Chlorophytum comosum* sind die Bluten selbst botanisch unscheinbar und ephemer — die Kindel-Bildung ist der eigentliche Pflegeaspekt. Der Name trifft den Kern nicht prazise.

Vorschlag: Phase in `runner_formation` (display_name: "Ausläuferbildung & Kindel") umbenennen, oder den display_name entsprechend prazisieren.

**[HINWEIS H-002] Fehlende Repotting-Phase**
Grünlilien bilden sehr schnell Wurzelballen und mussen regelmasig umgetopft werden (jahrlich bei jungen Pflanzen). Eine Phase oder ein Trigger fur Umtopfen existiert nicht. Kein Blockerbefund, da dies als Task modelliert werden kann.

**i18n DE/EN:** Korrekt. Die Beschreibung der "flowering"-Phase erklart Auslaeufer und Kindel korrekt.

---

### 1.2 Guzmania lingulata (Guzmanie)

**Phasen:** pup_establishment (60d) -> vegetative (365d) -> pre_bloom (60d) -> flowering (90d) -> senescence (180d)

**Bewertung:** Hervorragend modelliert. Der Lebenszyklus einer monokarpen Bromeliacee (einmalig bluhend, dann absterbend mit Kindeln) ist korrekt abgebildet.

#### Befunde

**[WARNUNG W-001] Vegetative Phase: Dauer unrealistisch lang**
`duration_days: 365` fur die vegetative Phase. In der Praxis dauert die Aufbauphase einer Guzmania-Kindel bis zur Blutenbereitschaft typischerweise 2-3 Jahre (730-1095 Tage), nicht 1 Jahr. Mit nur 365 Tagen wird ein unrealistisch schneller Lebenszyklus suggeriert. Empfehlung: 730 Tage oder alternativ als range angeben.

**[HINWEIS H-003] Apfel-Ethylen-Methode in i18n korrekt, aber ohne Einschranken**
DE: "Ein reifer Apfel neben der Pflanze kann durch Ethylen-Abgabe die Blütenbildung fördern." Dies ist botanisch korrekt (Ethylen als Blutungshormon bei Bromeliaceen). Jedoch fehlt der Hinweis, dass dies nur bei Pflanzen funktioniert, die reif genug fur die Blute sind (typischerweise nach 2+ Jahren). Ohne diesen Kontext weckt der Tipp falsche Erwartungen.

**[HINWEIS H-004] pre_bloom Licht-PPFD unverandert gegenuber vegetative**
`light_ppfd_target: 200` in pre_bloom, identisch mit vegetative Phase. In der Praxis kann hoheres Licht (250-300 µmol/m²/s) die Blüteninduktion unterstutzen. Kein schwerwiegender Fehler, da Guzmania grundsatzlich lichtsensibel ist.

**i18n DE/EN:** Korrekt und praxisnah.

---

### 1.3 Monstera deliciosa (Monstera)

**Phasen:** juvenile (365d) -> vegetative (365d) -> climbing (365d) -> mature (365d)

**Bewertung:** Sehr gute Modellierung der schrittweisen Entwicklung von der ungefensterten Jungpflanze zur ausgewachsenen Kletterpflanze. Die Abfolge ist botanisch korrekt (Heterophyllie: Juvenilblatter ohne Fenestrierung -> adulte Blatter mit Fenestrierung und Lobus).

#### Befunde

**[FEHLER F-001] Fehlende Blutephase fur Monstera indoor**
*Monstera deliciosa* blüht indoor unter guten Bedingungen und bildet essbare Früchte (Philodendron-Kochbanane / "Mexican Breadfruit"). Weder eine `flowering`-Phase noch ein `allows_harvest: true`-Flag existieren. Da das System `allows_harvest` phasengebunden hat, kann die Fruchtbildung (indoor selten, aber moeglich) nicht abgebildet werden.

Korrekte Erganzung: Optional eine `flowering` oder `fruiting`-Phase mit `allows_harvest: true` und langer Phasendauer (365d, sehr selten indoor) erganzen, oder zumindest im i18n-Text auf die Moglichkeit der Fruchtbildung hinweisen.

**[WARNUNG W-002] "Climbing"-Phasenbeschreibung in i18n technisch unvollstandig**
DE: "Regelmäßiges Aufleiten und Ausgeizen fördern geordnetes Wachstum." Das Wort "Ausgeizen" (Entfernung von Seitentrieben) ist fachlich falsch fur Monstera — Monstera hat keine Seitentriebe im Sinne der Gurkenpflege. Bei Monstera spricht man von "Ausgeizen" allenfalls im Kontext von Luftwurzeln fuhren. Korrekt ware: "Regelmassiges Aufleiten der Luftwurzeln und Triebe fordert geordnetes Wachstum."

**[HINWEIS H-005] Alle 4 Phasen mit duration_days: 365 identisch**
Die gleichmassige Verteilung ist eine vereinfachende Annahme, die der Praxis nicht entspricht. Die juvenile Phase kann bei optimalen Bedingungen deutlich kurzer (6-12 Monate), die mature Phase deutlich langer (jahrzehntelang) dauern. Da es sich um Richtwerte handelt, kein schwerwiegender Fehler.

**i18n DE/EN:** Bis auf den "Ausgeizen"-Fehler korrekt und anschaulich.

---

### 1.4 Spathiphyllum wallisii (Einblatt)

**Phasen:** establishment (60d) -> vegetative (180d) -> flowering (60d) -> mature (365d)

**Bewertung:** Korrekt und vollstandig. Das Phasenmodell ist identisch zum Chlorophytum-Modell, was fur eine vergleichbare tropische Zimmerpflanze sinnvoll ist.

#### Befunde

**[FEHLER F-002] Spathiphyllum: Blute durch Licht allein nicht auslosbar — Beschreibung irreführend**
i18n DE: "Das charakteristische weiße Hochblatt erscheint bei ausreichend Licht und guter Pflege."

Dies ist fachlich zu vereinfachend. *Spathiphyllum wallisii* blüht primär als Reaktion auf einen Temperaturruckgang (kuhlere Nachte, ca. 15-17°C) oder Trockenstress. Gartnereien setzen zur Blütenindduktion Gibberellin ein. Licht allein loest die Blüte nicht aus — im Gegenteil: stark erhöhter Lichtbedarf kann Blattverbrennungen verursachen, ohne die Blute zu forden.

Korrekte Formulierung: "Das charakteristische weiße Hochblatt erscheint typischerweise bei leichtem Trocken- oder Kaltestress sowie guter Grundpflege. Kuhlere Nachte (15-17 °C) uber einige Wochen konnen die Blütenbildung auslosen."

EN: Identischer Fehler: "The characteristic white spathe appears with sufficient light and good care."

**[HINWEIS H-006] Fehlende Ruhephase im Modell**
Im Gegensatz zum Freiland hat *Spathiphyllum* indoor keine echte Dormanz. Jedoch zeigt die Pflanze im Winter bei reduciertem naturlichen Licht eine Wachstumsverlangsamung, die eine angepasste Pflege erfordert. Dies konnte als Hinweis in der mature-Phase dokumentiert sein.

**i18n DE/EN:** Ausser dem Blüten-Auslöser-Fehler korrekt.

---

### 1.5 Fragaria x ananassa (Gartenerdbeere)

**Phasen:** germination (14d) -> vegetative (90d) -> flowering (21d) -> ripening (28d) -> recovery (45d) -> dormancy (90d)

**Bewertung:** Strukturell richtig fur eine mehrjahrige Pflanze mit Winterruhe. Die Phasendauern sind realitatsnahe.

#### Befunde

**[FEHLER F-003] Keimungsphase fur Erdbeere als Standard-Startpunkt fachlich falsch**
Die Phase `germination` ist mit `display_name: "Keimung/Etablierung"` und `duration_days: 14` modelliert. Der Standard-Anbauweg fur *Fragaria x ananassa* ist jedoch ausschliesslich vegetativ (Tochterauslaufer, Jungpflanzen), nicht uber Samen. Erdbeersamen sind:
- extrem langsam keimend (2-6 Wochen, nicht 14 Tage)
- bei modernen Sortenhy briden (F1) nicht sortenecht
- fur den Hobbygartner praktisch irrelevant als Vermehrungsweg

Die Keimungsphase als Startpunkt des Zyklus suggeriert falsches Verstandnis. Fur den normalen Anbau sollte der Einstiegspunkt `establishment` (Einpflanzung von Jungpflanzen/Ableger) heissen, nicht `germination`.

Vorschlag: Phase umbenennen in `establishment` (display_name: "Einpflanzung/Etablierung") und die i18n-Beschreibung auf die Etablierung von Jungpflanzen ausrichten. Keimung aus Samen als seltenen Sonderfall dokumentieren.

**[HINWEIS H-007] Dormanz: Temperatur 0°C Nacht fachlich grenzwertig**
`temperature_night_c: 0.0` fur die Dormanzphase. Wahrend Erdbeerpflanzen kurze Frostperioden bis -10°C (mit Laubschicht) uberstehen, ist 0°C als Sollwert fur eine Topfkultur (kein Bodenschutz) kritisch. Topferdbeeren beginnen bei 0°C Wurzelfrostschaden zu nehmen. Empfehlung: `temperature_night_c: 2.0` als sicherer Mindestwert.

**[WARNUNG W-003] i18n Keimungstext beschreibt Lichtkeimung — botanisch teilweise korrekt, aber missverstandlich**
DE: "Samen nur auf die Oberfläche drücken (Lichtkeimer)..."

*Fragaria* ist ein Lichtkeimer, das ist korrekt. Jedoch ist die Beschreibung im Kontext eines Standardanbau-Systems irrefuhrend, da Aussaat aus Samen fur Gartenerdbeeren kaum praktiziert wird. Wenn die Keimphase beibehalten wird, sollte ein Hinweis auf den unüblichen Anbauweg stehen.

**[HINWEIS H-008] Fehlende Auslaeuferphase im Zyklus**
Die Bildung von Auslaeufer-Tochtern (Stolonen) ist der praxisrelevanteste Vermehrungsaspekt bei Erdbeeren. Die vegetative Phase erwahnt sie im i18n-Text ("Ausläufer für stärkere Fruchternte entfernen"), aber es fehlt ein dedizierter Parameter oder Phasen-Flag fur Stolonen-Produktion.

---

### 1.6 Helianthus annuus (Sonnenblume)

**Phasen:** germination (10d) -> seedling (18d) -> vegetative (42d) -> flowering (21d) -> ripening (32d) -> senescence (10d)

**Bewertung:** Phasenabfolge korrekt. Schwerwiegende Probleme bei der Phasendauer und einem botanischen Fehler im i18n-Text.

#### Befunde

**[FEHLER F-004] Vegetative Phase 42 Tage zu kurz — biologisch nicht belastbar**
`duration_days: 42` fur die vegetative Phase von *Helianthus annuus*. Bei Standardsorten betragt die Zeit von Keimung bis zur Blutenoffnung typischerweise 70-120 Tage (je nach Sorte). Die Summe der Phasen ergibt: 10 + 18 + 42 + 21 = 91 Tage bis zur Blutenoffnung (ohne Samenreife). Das ist fur fruhe Sorten (z.B. 'Pacino') gerade noch vertretbar, fur die meisten gartnerischen Hauptsorten (z.B. 'Russian Giant': 80-100 Tage bis Blüte allein) aber deutlich zu kurz.

Die vegetative Phase sollte mindestens 55-70 Tage betragen. Empfehlung: `duration_days: 60` als Mittelwert.

**[FEHLER F-005] Heliotropismus nur in Jugendphase korrekt — Beschreibung in flowering-Phase fachlich falsch**
i18n DE: "Der Blütenkorb öffnet sich und folgt dem Sonnenlauf (Heliotropismus)."
i18n EN: "The flower head opens and follows the sun (heliotropism)."

Dies ist ein klassischer botanischer Fehler. *Helianthus annuus* zeigt Heliotropismus (circadiane Bewegung der Pflanze mit der Sonne) ausschliesslich in der vegetativen Jugendphase (Streckungs- und Blattentfaltungsphase). Reife, ausgewachsene Blütenköpfe sind statisch und zeigen keinen Heliotropismus mehr — sie bleiben nach der Blütenentwicklung dauerhaft nach Osten ausgerichtet (wo sie durch die Morgensonne aufgewarmt werden und Bestauber anlocken).

Korrekte Formulierung DE: "Der Blütenkorb öffnet sich. Reife Blütenköpfe sind dauerhaft nach Osten ausgerichtet und profitieren von der Morgensonne — Heliotropismus findet nur in der Jugendphase des Stangels statt."

EN entsprechend korrigieren.

**[HINWEIS H-009] Seneszenz-Phase: PPFD 400 µmol/m²/s trotz absterbender Pflanze unrealistisch**
`light_ppfd_target: 400` in der Seneszenz-Phase, obwohl die einjahrige Pflanze abstirbt und keine Photosynthese mehr betreibt. Dieser Wert ist irrelevant und konnte als 0 oder null modelliert werden.

**i18n DE/EN:** Bis auf Heliotropismus-Fehler gut. Die Schnecken-Warnung in der Keimphase ist praxisnah und wertvoll.

---

### 1.7 Viola x wittrockiana (Garten-Stiefmutterchen)

**Phasen:** germination (12d) -> seedling (35d) -> vegetative (28d) -> flowering (90d) -> senescence (21d)

**Bewertung:** Botanisch korrekt. Zweijahrige Pflanze, die typischerweise im Sommer ausgesaet und im Herbst/Frühjahr blüht. Das Modell bildtet einen Anbau-Zyklus ab.

#### Befunde

**[FEHLER F-006] Keimtemperatur-Angabe im Requirement-Profile zu hoch**
`temperature_day_c: 16.0` und `temperature_night_c: 14.0` fur die Keimphase. *Viola x wittrockiana* ist ein klassischer Kaltkeimer — optimale Keimtemperatur liegt bei 12-16°C, aber die Nachttemperatur sollte 10-12°C nicht uberschreiten. Mit 14°C Nacht wird korrekterweise eine kuhle Keimung beschrieben.

Der i18n-Text gibt korrekt "kühle 14–16 °C" an. Die YAML-Werte sind damit weitgehend konsistent. Kein schwerwiegender Fehler, aber die Tag-Temperatur von 16°C ist das Maximum, nicht das Optimum (besser: 12-14°C tagsüber).

**[WARNUNG W-004] Fehlende Vernalisierungsphase im Phasenmodell**
*Viola x wittrockiana* ist zweijahrig und vernalisationsbedurtig (Kaltereiz zur Blütenindduktion, `vernalization_required: true` in der lifecycle_config, 30 Tage). Diese Vernalisierungsperiode ist im Phasenmodell nicht abgebildet — sie fiele typischerweise zwischen seedling und vegetative, also in den Winter des ersten Jahres. Das Modell springt von seedling direkt zu vegetative, ohne die kuhle Uberwinterungsphase zu adressieren.

Vorschlag: Erganzung einer `overwintering`- oder `vernalization`-Phase zwischen seedling und vegetative mit ca. 60-90 Tagen, kuhlen Temperaturen (5-10°C) und stark reduzierter Pflege.

**[HINWEIS H-010] Seneszenz-Beschreibung fachlich korrekt aber unvollstandig**
DE: "Stark zurückschneiden und kühl halten kann bei zweijährigen Sorten eine Herbstblüte fördern." Dies ist korrekt, aber ohne Erklarung, dass dies nur bei echter zweijahrigen Natur (nicht Sommerblüher-Sorten) funktioniert. Viele moderne Sorten sind tatsachlich einjahrig-behandelt und regenerieren nicht zuverlaessig.

---

### 1.8 Dahlia pinnata (Dahlie)

**Phasen:** dormancy (135d) -> sprouting (30d) -> hardening_off (10d) -> vegetative (42d) -> flowering (75d) -> senescence (18d)

**Bewertung:** Hervorragend modelliert. Der Zyklus beginnt korrekt mit der Knollenruhe (wie die Pflanze typischerweise im Handel angeboten wird), und schliesst mit Seneszenz/Knollenreife.

#### Befunde

**[WARNUNG W-005] Vegetative Phase 42 Tage zu kurz fur Dahlie**
Analoges Problem wie bei Helianthus: 42 Tage vegetatives Wachstum fur *Dahlia pinnata* ist zu kurz. Vom Austrieb im Frühling bis zur ersten Blüte vergehen typischerweise 90-110 Tage (8-12 Wochen), davon entfallen auf die vegetative Phase nach dem Austrieb realistisch 60-80 Tage. Empfehlung: `duration_days: 70`.

**[HINWEIS H-011] Dormanz: Temperatur und Feuchtigkeit biologisch korrekt, aber VPD = 0.0 fragwurdig**
`vpd_target_kpa: 0.0` in der Dormanzphase. Dieser Wert ist fur eine eingelagerte Knolle nicht sinnvoll — VPD ist ein Wert fur transpirierende, lebende Pflanzenteile. Fur Lagerungsphasen sollte der Parameter als `null` oder nicht anwendbar modelliert werden.

**[HINWEIS H-012] Dahlien: Kurztagspflanze (short_day in lifecycle_config), aber photoperiod_hours: 16.0 in vegetative Phase**
Die lifecycle_config deklariert `photoperiod_type: short_day` (Blütenbildung unter Kurztag) und `critical_day_length_hours: 12.0`. In der vegetativen Phase ist `photoperiod_hours: 16.0` korrekt — lange Tage halten Dahlie in der vegetativen Phase. In der flowering-Phase ist `photoperiod_hours: 14.0` — diese Reduktion ist plausibel fur den Herbst-Bluteeinsatz. Das System ist innerlich konsistent.

**i18n DE/EN:** Ausgezeichnet praxisnah, besonders die Hinweise zu Disbudding (Ausgeizen bei grossblumigen Sorten) und zur Knollenlagerung.

---

### 1.9 Petunia x hybrida (Garten-Petunie)

**Phasen:** germination (10d) -> seedling (28d) -> vegetative (18d) -> hardening_off (10d) -> flowering (150d) -> senescence (18d)

**Bewertung:** Korrekte Abfolge fur eine einjahrige Sommerblume mit Voranzucht. Phasendauern plausibel.

#### Befunde

**[WARNUNG W-006] Vegetative Phase 18 Tage extrem kurz**
`duration_days: 18` fur die vegetative Phase der Petunie. Von der Pikierung bis zur Auspflanzungsreife vergehen typischerweise 4-6 Wochen (28-42 Tage), in denen die Pflanze vegetativ wachst und sich verzweigt. 18 Tage ist fachlich zu knapp. Empfehlung: `duration_days: 35`.

**[HINWEIS H-013] Germination: PPFD 100 µmol/m²/s bei Lichtkeimer — korrekt aber zu prazisieren**
`light_ppfd_target: 100` fur die Keimphase. Petunien sind Lichtkeimer und benotigen tatsachlich Licht zur Keimung, aber 100 µmol/m²/s ubersteigt die Notwendigkeit deutlich — fur die reine Keimindduktion reichen diffuses Licht oder 10-20 µmol/m²/s. Der hohere Wert schadet nicht, ist aber als Mindestwert suggestiv.

**[FEHLER F-007] Flowering-Phase: pH 6.0 inkonsistent mit rest des Petunien-Profils**
In der `flowering`-Phase ist `target_ph: 6.0`, wahrend alle anderen Phasen `target_ph: 5.8` angeben. Petunien bevorzugen leicht saures Substrat (pH 5.5-6.0), wobei 5.8 als Optimum gilt. Der Wechsel zu 6.0 in der Blutephase ist biologisch nicht begrundet und wirkt wie ein Datenfehler.

**i18n DE/EN:** Korrekt. Hinweis auf klebrige Bluten (DE: "klebrige, verblühte Blüten entfernen") ist ein wertvoller Praxistipp.

---

### 1.10 Tigridia pavonia (Tigerblume)

**Phasen:** sprouting (21d) -> vegetative (40d) -> hardening_off (10d) -> budding (18d) -> flowering (52d) -> corm_ripening (35d) -> dormancy (165d)

**Bewertung:** Ausgezeichnet detailliert modelliert. Die Trennung von `budding` (Knospenbildung) und `flowering` ist botanisch sinnvoll und nicht selbstverstandlich fur ein System dieser Art.

#### Befunde

**[FEHLER F-008] Terminologie: "Zwiebeln" im i18n-Text fur Tigridia fachlich falsch — Tigridia hat Knollen (Kormus)**
i18n DE sprouting: "Tigerblumen-Knollen ab April 5 cm tief pflanzen..."
i18n EN sprouting: "Plant tiger flower bulbs 5 cm deep from April..."

Im englischen Text wird "bulbs" verwendet, im deutschen korrekt "Knollen". *Tigridia pavonia* bildet jedoch Kormi (Singular: Kormus), keine echten Zwiebeln (Bulben). Kormi sind verdickte Sprossachsen, Zwiebeln sind schuppenblattmodifizierte Strukturen. In der botanischen Fachliteratur wird fur Tigridia korrekt "corm" (engl.) bzw. "Knolle" oder "Kormus" (dt.) verwendet.

Im deutschen Text ist "Knollen" akzeptabel (gamaess Volkssprache). Im englischen Text sollte "bulbs" zu "corms" korrigiert werden — insbesondere da die Phasenbezeichnung bereits korrekt `corm_ripening` heisst.

**[HINWEIS H-014] Fehlende Initialpflanzung aus Samen als alternativer Einstieg**
*Tigridia pavonia* wird gelegentlich aus Samen gezogen (Blute nach 2-3 Jahren). Das Modell beginnt korrekt mit dem Standard-Anbauweg (Knollen), aber fur Vollstandigkeit ware ein Hinweis sinnvoll.

**[HINWEIS H-015] Dormanz-Temperatur 10-12°C korrekt abgebildet und konsistent mit i18n**
"Tigridia wärmer als Dahlien lagern" ist korrekt — Tigridia-Kormi sind kaelteempfindlicher als Dahlienknollen. Sehr gute praxisnahe Differenzierung.

**i18n DE/EN:** Qualitativ hochwertig. Die Differenzierung in der Lagertemperatur zwischen Dahlia (4-7°C) und Tigridia (10-12°C) zeigt fachliche Tiefe.

---

### 1.11 Apium graveolens var. rapaceum (Knollensellerie)

**Phasen:** germination (21d) -> seedling (49d) -> vegetative (75d) -> tuber_formation (75d) -> harvest (7d)

**Bewertung:** Strukturell die schwachste Modellierung der gesamten Sammlung. Mehrere biologische und konzeptionelle Probleme.

#### Befunde

**[FEHLER F-009] allows_harvest: true in der vegetativen Phase biologisch falsch fur Knollensellerie**
`allows_harvest: true` in der `vegetative`-Phase mit dem Kommentar im i18n-Text: "äußere Stiele können bereits als Stangensellerie geerntet werden."

Das ist botanisch und kulinarisch problematisch: Die angebaute Varietat ist *Apium graveolens var. rapaceum* (Knollensellerie), nicht *Apium graveolens var. dulce* (Stangensellerie). Stangensellerie und Knollensellerie sind verschiedene Varietaten mit unterschiedlichem Kulturziel. Die Blattstiele von Knollensellerie konnen zwar essbar sein, aber "als Stangensellerie ernten" ist fachlich eine Varietatsverwechslung. Die vegetative Phase von Knollensellerie produziert keine marktfahigen Stangen.

Korrekte Formulierung: Die Blattstiele von Knollensellerie konnen als Suppengrun verwendet werden, sind aber nicht mit Stangensellerie gleichzusetzen.

**[FEHLER F-010] Harvest-Phase: duration_days 7 Tage unrealistisch kurz und fachlich falsch konzipiert**
`duration_days: 7` und `is_terminal: true` fur die Erntephase. Knollensellerie wird nicht an einem Tag oder in einer Woche geerntet — die Ernte erfolgt bei Freilandanbau typischerweise uber mehrere Wochen (Oktober-November), und die Knollen konnen bei geeigneten Bedingungen auch im Boden uberwintern und wahrend des Winters bei Bedarf geerntet werden.

Konzeptionell: Die `harvest`-Phase als 7-Tage-terminal-Phase suggeriert eine Schlag-Ernte (alles auf einmal). Fur Sellerie ware eine `storage`-Phase nach der Ernte sinnvoller, da die Knollen bei 0-4°C und hoher Luftfeuchtigkeit monatelang lagern.

**[FEHLER F-011] Vernalisierungsrisiko nicht im Phasenmodell abgebildet — kritisch fur Sellerie**
*Apium graveolens var. rapaceum* ist eine Schosser-empfindliche Pflanze (lifecycle_config: `vernalization_required: true`, 42 Tage, `critical_day_length_hours: 14.0`). Temperaturen unter 10°C uber mehrere Tage beim Sämling losen Schossen (vorzeitige Blütenbildung) aus. Dieses kritische Risiko ist in der seedling-Phase im YAML nicht durch einen Stress-Marker abgebildet.

Die i18n-Beschreibung ergreift das Thema korrekt: "Temperaturen unter 10 °C unbedingt vermeiden — Kältereiz löst vorzeitige Blütenbildung (Schossen) aus." Das ist ein wertvoller Hinweis. Jedoch fehlt er als Parameter (z.B. `min_temperature_critical_c: 10`) in der requirement_profile.

**[WARNUNG W-007] Gesamtzyklusdauer unrealistisch**
Summe aller Phasen: 21 + 49 + 75 + 75 + 7 = 227 Tage (~7,5 Monate). In der Praxis betragt der Anbau von Knollensellerie von der Aussaat bis zur Ernte typischerweise 6-7 Monate in gemassigten Breiten (Aussaat Februar/Marz indoor, Ernte Oktober/November). Das passt mit 227 Tagen (knapp 7,5 Monate) einigermasen. Jedoch:
- seedling: 49 Tage (7 Wochen) ist fur Sellerie realistisch.
- vegetative: 75 Tage in Verbindung mit tuber_formation: 75 Tage — die Grenze zwischen diesen Phasen ist im Feld kaum erkennbar, da Blattaufbau und Knollenbildung simultan verlaufen (ab ca. Woche 10-12 nach dem Pikieren).

Empfehlung: Die vegetative und tuber_formation-Phase konnen beibehalten werden, aber der Ubergang ist fliessend, nicht diskret. Dies sollte in der i18n-Dokumentation kommuniziert werden.

**i18n DE/EN:** Inhaltlich weitgehend korrekt, aber mit den genannten Variety-Verwechslungs-Fehler in der vegetativen Phase. Der Schossen-Hinweis ist ausgezeichnet.

---

## 2. Ubergreifende Befunde: enums.phaseDescription (generische Beschreibungen)

Die generischen Phasenbeschreibungen unter `enums.phaseDescription` (ohne Species-Bezug) weisen auf einen spezifischen Kontext hin:

**[WARNUNG W-008] Generische Beschreibungen sind cannabis-/Growbox-zentriert**
Die Beschreibungen fur `ripening`, `harvest`, `drying`, `curing`, `flushing` beziehen sich explizit auf Trichome, Pistillen, "Potenz" und "Burping" — das sind ausschliesslich cannabis-relevante Konzepte, die fur Gemuse, Krauter oder Zierpflanzen nicht relevant sind. Diese Texte erscheinen als Fallback, wenn keine art-spezifische Beschreibung (phaseDescriptions) existiert.

Da das System fur alle Pflanzen verwendet wird, sollten die generischen Fallback-Texte neutraler formuliert sein oder der Kontext (nur fur Cannabis/Growbox) explizit kommuniziert werden.

DE `ripening`: "Früchte/Blüten reifen aus, Trichome verfärben sich. [...] Erntezeitpunkt durch Trichom-Farbe und Pistillen-Zustand bestimmen." — fachlich korrekt fur Cannabis, aber fur Erdbeere oder Sellerie als Fallback irrelevant.

**[HINWEIS H-016] i18n-Strukturfehler: Einige Schlusselpaare in phaseDescription falsch eingezogen**
In `de/translation.json` enden die Eintrage `germination` bis `senescence` korrekt mit `}` nach dem letzten Eintrag, aber die nachfolgenden Einruckungsschlüssel (`establishment`, `pup_establishment`, `pre_bloom` usw.) sind auf der gleichen Ebene wie die vorherigen, aber AUSSERHALB der schliesenden `}` des `phaseDescription`-Objekts — d.h. sie befinden sich faktisch innerhalb des phaseDescription-Objekts aber nach einem fehlplatzierten Komma/Struktur. Dies ist kein JSON-Fehler (der Parser akzeptiert es), aber die konsistente Einruckung fehlt. Die Einruckung springt von 4 Leerzeichen auf 4 ohne das erwartete Komma nach `senescence`.

---

## 3. Parameter-Prufung: Requirement-Profile

### 3.1 PPFD-Werte

| Species | Phase | PPFD (µmol/m²/s) | Bewertung |
|---------|-------|------------------|-----------|
| Chlorophytum comosum | vegetative | 200 | Korrekt (Zimmerpflanze, Halbschatten) |
| Guzmania lingulata | vegetative | 150 | Korrekt (Bromeliacee, schwaches Licht) |
| Monstera deliciosa | climbing | 300 | Korrekt (tropische Folienpflanze, indirekt) |
| Spathiphyllum wallisii | flowering | 200 | Erhoht fur Schattenpflanze — Spathiphyllum blüht typischerweise schon bei 100-150 µmol/m²/s |
| Fragaria x ananassa | vegetative | 400 | Korrekt (Fruchtpflanze) |
| Helianthus annuus | flowering | 700 | Korrekt (Vollsonnenpflanze, Freiland) |
| Viola x wittrockiana | flowering | 350 | Korrekt (Kuhlhauspflanze) |
| Dahlia pinnata | flowering | 600 | Korrekt |
| Petunia x hybrida | flowering | 600 | Korrekt |
| Tigridia pavonia | vegetative | 650 | Korrekt (Vollsonnenpflanze) |
| Apium graveolens var. rapaceum | tuber_formation | 350 | Korrekt |

**[WARNUNG W-009] Spathiphyllum: PPFD 200 in flowering-Phase zu hoch**
*Spathiphyllum wallisii* ist eine typische Schattenflurpflanze (Walduntergeschoss). Die Angabe von 200 µmol/m²/s in der Blütephase ist fur den Indoor-Kontext zu hoch. Bei 200 µmol/m²/s drohen Blattrandverbrennungen bei direkter LED-Beleuchtung. Optimum fur Spathiphyllum: 50-100 µmol/m²/s. Empfehlung: `light_ppfd_target: 100` in flowering und mature.

### 3.2 VPD-Werte

Die VPD-Werte (Dampfdruckdefizit, kPa) sind durchgangig plausibel:
- Zimmerpflanzen: 0.5-1.0 kPa — korrekt
- Freilandpflanzen in Blüte: 1.1-1.2 kPa — korrekt
- Keimung/Dormanz: 0.0-0.5 kPa — korrekt

Keine schwerwiegenden Fehler in den VPD-Werten.

### 3.3 Dungeprofile

**[FEHLER F-012] Chlorophytum comosum flowering-Phase: NPK [2,1,2] identisch zur vegetativen Phase**
In der Blüte-/Kindel-Phase einer Zimmerpflanze ware leicht mehr Phosphor fur die Blütenbildung sinnvoll (z.B. [1,2,2] oder [2,2,2]). Die identische NPK-Ratio wie in der vegetativen Phase ist fur eine aktiv bluhende Pflanze suboptimal. Geringer Befund, da Chlorophytum kein Ertragszielpflanze ist.

**[HINWEIS H-017] Fragaria x ananassa ripening: NPK [1,2,4] sehr kaliumreich**
`npk_ratio: [1, 2, 4]` fur die Reifephase. Das hohe Kalium-Verhaltnis (K:N = 4:1) ist fur Erdbeeren in der Fruchtreife fachlich vertretbar und unterstuetzt Zucker-Synthese und Zellwandstaerkung. Kein Fehler, aber am oberen Rand der Literaturwerte (typisch: [1,2,3]).

---

## 4. Konsistenz-Prufung: Phasenbenennungen

| Phasenname | Verwendende Species | Konsistent? |
|------------|---------------------|-------------|
| germination | Fragaria, Helianthus, Viola, Petunia, Apium | Ja |
| seedling | Helianthus, Viola, Petunia, Apium | Ja |
| vegetative | Alle 11 Species | Ja |
| flowering | Chlorophytum, Guzmania, Monstera, Spathiphyllum, Fragaria, Helianthus, Viola, Dahlia, Petunia, Tigridia | Ja |
| ripening | Fragaria, Helianthus | Ja |
| dormancy | Fragaria, Dahlia, Tigridia | Ja |
| senescence | Guzmania, Helianthus, Viola, Dahlia, Petunia | Ja |
| establishment | Chlorophytum, Spathiphyllum | Ja |
| mature | Chlorophytum, Monstera, Spathiphyllum | Ja |
| sprouting | Dahlia, Tigridia | Ja |
| hardening_off | Dahlia, Petunia, Tigridia | Ja |

Phasenbenennungen sind uber alle Species konsistent. Das ist ein grosser Qualitaetsvorzug des Systems.

---

## 5. Priorisierte Korrekturer-Liste

### Rot — Sofortiger Korrekturbedarf (Botanischer Fehler)

| ID | Species | Problem | Datei | Korrektur |
|----|---------|---------|-------|-----------|
| F-001 | Monstera deliciosa | Fehlende Blute-/Fruchtphase mit allows_harvest | YAML | Phase `fruiting` erganzen (optional, IS_TERMINAL: false, selten indoor) |
| F-002 | Spathiphyllum wallisii | Blütenauslöser "Licht" fachlich falsch | i18n DE+EN | Formulierung auf Kaltestress und Trockenheit andern |
| F-003 | Fragaria x ananassa | Keimungsphase als Standard-Anbaustart fachlich falsch | YAML + i18n | Umbenennen in "establishment" / Hinweis auf vegetativen Standardanbau |
| F-004 | Helianthus annuus | Vegetativphase 42d zu kurz | YAML | `duration_days: 60` |
| F-005 | Helianthus annuus | Heliotropismus-Fehler in flowering i18n | i18n DE+EN | Reife Blütenköpfe sind statisch, Ost-ausgerichtet — Heliotropismus nur in Jugendphase |
| F-006 | Apium graveolens | Stangensellerie-Verwechslung in vegetative i18n | i18n DE+EN | Blattstiele sind Suppengrun, kein Stangensellerie |
| F-007 | Petunia x hybrida | pH 6.0 in flowering-Phase inkonsistent (ubrige Phasen: 5.8) | YAML | `target_ph: 5.8` |
| F-008 | Tigridia pavonia | "bulbs" im EN-Text falsch — korrekt: "corms" | i18n EN | "bulbs" zu "corms" |
| F-009 | Apium graveolens | allows_harvest: true in vegetative (Stangensellerie-Verwechslung) | YAML | allows_harvest: false, oder Kommentar prazisieren |
| F-010 | Apium graveolens | Harvest-Phase 7d/terminal konzeptionell falsch fur Sellerie | YAML | duration_days erhohen, Lagerphase erganzen |
| F-011 | Apium graveolens | Schossen-Risiko nicht als Parameter abgebildet | YAML | min_temperature_critical_c: 10 in seedling requirement_profile |
| F-012 | Chlorophytum comosum | NPK in flowering identisch zu vegetative | YAML | NPK auf [1,2,2] anpassen |

### Orange — Wichtige Korrekturen (Dauer/Vollstandigkeit)

| ID | Species | Problem | Empfehlung |
|----|---------|---------|------------|
| W-001 | Guzmania lingulata | Vegetativphase 365d zu kurz (realitat: 730d+) | duration_days: 730 |
| W-002 | Monstera deliciosa | "Ausgeizen" im i18n falsch | "Aufleiten der Triebe" statt "Ausgeizen" |
| W-003 | Fragaria x ananassa | Keimtext irrefuhrend fur Standardanbau | Hinweis auf Jungpflanzen-Anbau |
| W-004 | Viola x wittrockiana | Fehlende Vernalisierungsphase | Phase `overwintering` erganzen |
| W-005 | Dahlia pinnata | Vegetativphase 42d zu kurz | duration_days: 70 |
| W-006 | Petunia x hybrida | Vegetativphase 18d zu kurz | duration_days: 35 |
| W-007 | Apium graveolens | Gesamtzyklusdauer und vegetative/tuber Abgrenzung unprazise | i18n Hinweis auf fliessenden Ubergang |
| W-008 | (generisch) | Generische phaseDescription-Texte cannabis-zentriert | Neutralere Fallback-Texte |
| W-009 | Spathiphyllum wallisii | PPFD 200 in flowering zu hoch fur Schattenflurpflanze | light_ppfd_target: 100 |

### Gelb — Hinweise und Best-Practice-Empfehlungen

| ID | Species | Hinweis |
|----|---------|---------|
| H-001 | Chlorophytum | Phasenname "flowering" ungenau; Kindel-Bildung ist der Hauptaspekt |
| H-002 | Chlorophytum | Umtopf-Bedarf nicht als Parameter abgebildet |
| H-003 | Guzmania | Apfel-Ethylen-Tipp ohne Kontext zu Reifeanforderung |
| H-004 | Guzmania | pre_bloom PPFD unverandert gegenuber vegetative |
| H-005 | Monstera | Alle Phasen gleichlang (365d) — vereinfachend |
| H-006 | Spathiphyllum | Fehlende Winter-Wachstumsverlangsamung im mature-Modell |
| H-007 | Fragaria | Dormanz Nacht 0°C fur Topfkultur zu kalt |
| H-008 | Fragaria | Stolonen-Bildung nicht als Parameter |
| H-009 | Helianthus | Seneszenz PPFD 400 irrelevant fur absterbende Pflanze |
| H-010 | Viola | Seneszenz-Hinweis fur Herbstblute unvollstandig |
| H-011 | Dahlia | VPD = 0.0 in Dormanz konzeptionell unklar |
| H-012 | Dahlia | Kurztagspflanze und Photoperioden-Logik ist intern konsistent |
| H-013 | Petunia | PPFD 100 fur Lichtkeimer-Keimung hoher als notig |
| H-014 | Tigridia | Samen-Anbauweg nicht dokumentiert |
| H-015 | Tigridia | Lagertemperatur-Differenzierung Dahlia vs. Tigridia vorbildlich |
| H-016 | (generisch) | Einruckungsinkonsistenz in phaseDescription (kein Fehler, nur Code-Stil) |
| H-017 | Fragaria | NPK [1,2,4] am oberen Kalium-Rand — vertretbar |

---

## 6. Fehlende Species-Phasendaten (kein growth_phases-Eintrag in S5)

Die YAML-Datei definiert Phasen fur 11 Species. Folgende Species in der Datei haben KEINEN Phaseneintrag in S5 (nur species_enrichment oder nur lifecycle_config):
- Diese Species erben dann die systemgenerischen Phasen (germination, seedling, vegetative, flowering, harvest aus dem allgemeinen CLAUDE.md REQ-003-Modell).

Fur eine vollstandige Review der fehlenden Species waren weitere Seed-Dateien zu analysieren (die Basis-Phasemodelle aus REQ-003 und anderen Seed-Skripten).

---

## 7. Glossar der verwendeten Fachbegriffe

- **PPFD** (Photosynthetic Photon Flux Density): Photosynthetisch aktive Strahlungsintensitat in µmol/m²/s — der korrekte Wert fur Pflanzenwachstum, nicht Lux
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa — beschreibt den "Durst" der Luft; abhangig von Temperatur und Luftfeuchtigkeit
- **EC** (Electrical Conductivity): Elektrische Leitfahigkeit der Nahrlösung in mS/cm — Mass fur die Nahrstoffkonzentration
- **NPK**: Stickstoff (N), Phosphor (P), Kalium (K) — die drei Hauptnahrstoffe
- **Heterophyllie**: Unterschiedliche Blattformen an derselben Pflanze in verschiedenen Entwicklungsstadien (Monstera-Jungeblatter vs. Adulte)
- **Monokarpy**: Einmalige Blüte im Lebenszyklus, dann Absterben der Mutterpflanze (Guzmania)
- **Kormus/Corm**: Verdickte unterirdische Sprossachse (Tigridia, Gladiole) — kein echte Zwiebel (Bulbe)
- **Vernalisation**: Kaltereiz-abhangige Blütenindduktion (Viola, Sellerie) — Voraussetzung fur spatere Blütenbildung
- **Etiolement**: Streckungswachstum durch Lichtmangel — dunner, langer Stängel (Geile)
- **Schossen**: Vorzeitige Blütenbildung durch Kaltereiz bei Sellerie — macht die Knolle wertlos
- **Disbudding/Ausgeizen**: Entfernung von Seitentrieben fur grössere Hauptbluten (korrekt bei Dahlie, NICHT bei Monstera)
- **Heliotropismus**: Bewegung der Pflanze mit der Sonne — nur in der vegetativen Jugendphase bei Helianthus, NICHT bei ausgewachsenen Blütenköpfen
