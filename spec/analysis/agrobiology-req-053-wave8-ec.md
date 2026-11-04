# Agrarbiologisches Review: REQ-053 Welle 8 (E-17, #2411 / #2494)

> **Herkunft und Status.** Berichtstext des Agenten `agrobiology-requirements-reviewer` vom 2026-11-03, vom Orchestrator
> unverändert in diese Datei übernommen, weil der Agent weder Schreibzugriff noch Websuche hatte. Die Zahlen im Hauptteil
> waren Fachwissen aus dem Kopf und sind nicht verifiziert. **Stand 2026-11-03 (WP 8.5):** R-001 bis R-012 sind im
> [Addendum](#addendum-wp-85-recherche-r-001-bis-r-012) bearbeitet. Maßgeblich ist das Addendum, nicht der Hauptteil.
> Wo beide abweichen, gilt das Addendum. E-10 bleibt in Kraft: Ein Wert ohne drei belegte Quellen bleibt `null`.

Gelesen: REQ-053 §15 (GP-FR-120–127), §16.3 (GP-FR-138/139), E-17, Plan E-10, REQ-004 Z. 78–101, Migration v0096.

## Gesamtbewertung

- Fachliche Korrektheit: 3/5. Das Modell ist sauber. Die EC-Skalierung nach Zehrerstufe ist für Boden nicht haltbar, und die REQ-004-Tabelle passt nicht zum N-Deckel.
- Messbarkeit: 3/5. Die Extraktionsmethode ist am Ereignis geführt, am Profil (`ec_ms_cm`, `ph`) teilweise nicht.
- Schema-Spec-Konsistenz: 3/5. REQ-004 nutzt noch das 4-Werte-`nutrient_demand_level` mit `nitrogen_fixer`. REQ-053 §16.3 und v0096 haben das aufgelöst.
- Umsetzbarkeit: 4/5. GP-FR-125 ist mit „nie als Messwert“ und `insufficient_data` vorsichtig angelegt.

Kernproblem von E-17: Im Freilandboden ist EC ein Salzindikator, kein Dosierziel. REQ-004 sagt selbst „Statt EC-Zielwerten …“. EC-Skalierung ist nur für Nährlösung und Substrat sinnvoll. Dort gibt es sie schon über Phase und Rezept (REQ-004-A §5.2).

## Fachlich falsch

**F-001: EC-Zielwert-Skalierung nach Zehrerstufe für Boden/Beet.** Die Zehrerstufe beschreibt den N-Entzug pro Fläche, keine Soll-Leitfähigkeit. Ein Faktor „Starkzehrer × k“ würde zu Mehrdüngung bis in den Salzstress führen, und für k gibt es keine Quelle (E-10).

- Vorschlag: E-17 für Boden entscheiden als „keine EC-Skalierung nach Zehrerstufe“. Die Zehrerstufe steuert nur den Hinweistext in GP-FR-125 und die Fruchtfolge.
- Boden-EC wird nur als Salz-Grenzwert-Hinweis ausgewertet.
- Die EC-Skalierung für Nährlösung bleibt phasenbasiert in REQ-004-A.

**F-002: REQ-004-Tabelle Z. 89–94 hält den N-Deckel nicht ein und nutzt das veraltete Enum.**

- Heavy feeder: Kompost 3–4 L/m² plus Hornspäne 80 g/m². Hornspäne mit etwa 12–14 % N ergeben ca. 10 g N/m² (= 100 kg N/ha).
- Kompost 3–4 L/m² liefert grob 6–15 g N/m² gesamt (Schüttdichte 0,6–0,8 kg/L, 0,3–0,5 % N).
- Dazu kommt Jauche alle 2 Wochen. Die Summe liegt nahe an oder über der organischen Grenze von 170 kg N/ha (= 17 g N/m², DüV).
- Unverifiziert: Schüttdichte, N-Gehalt und die DüV-Geltung für Hausgärten (R-003, R-004, R-005). Die Rechnung zeigt nur, dass die Tabelle gegen eine Gesamt-N-Bilanz geprüft werden muss.
- Die Tabelle nutzt `nitrogen_fixer` als Zehrerstufe. Das widerspricht K-001/§16.3 und muss auf `nutrient_demand` plus `nitrogen_fixing` umgestellt werden.

## Unvollständig

- **U-001 Einheitenfallen nicht gebannt.** 1 g/m² = 10 kg/ha. 1 L/m² = 1 mm Schichtdicke. CAL-P und -K werden als P2O5/K2O angegeben; die Faktoren P2O5 × 0,4364 = P und K2O × 0,8301 = K sind Stöchiometrie, welche Form VDLUFA-Klassen nutzen, ist zu bestätigen (R-007). Produkt-N % ist nicht Nährstoff-N. Kompost: Frisch- gegen Trockenmasse. Jauche: `dilution_ratio` gegen L/m² Konzentrat. `area_m2` des Beets gegen die tatsächlich gedüngte Fläche.
- **U-002 EC-Extraktionsmethode am Profil fehlt.** Salzschwellen gelten für ECe (Sättigungsextrakt), Hobbywerte sind meist 1:2, 1:5 oder Sonde. Eine verlustfreie Umrechnung gibt es nicht, sie hängt von der Textur ab. Das Profil braucht `ec_method`.
- **U-003 `target_ph` ohne Messmethode.** Die Zielbereiche (Sand 5,5–6,5, Lehm 6,0–7,0, Ton 6,5–7,5) gelten nur je Methode. CaCl2 und H2O unterscheiden sich um grob 0,5–0,8 pH. Die Vergleichslogik muss `ph_method` berücksichtigen. Die Zahlen sind unverifiziert (R-008).
- **U-004 P/K-Klassen D/E.** Dann sollten Kompost und P-Dünger nicht empfohlen werden (Kompost reichert P an, R-006). GP-FR-125 sagt dazu nichts.
- **U-005 Holzasche und Kalk** heben den pH. Sie gehören nicht auf Böden über Ziel-pH oder zu Säurepflanzen.
- **U-006 Auswaschung und Textur.** Sandböden brauchen Split-Gaben, Staunässe fördert Denitrifikation. Ein Texturbezug fehlt in GP-FR-123/125.
- **U-007 `humus_percent`** fließt in keine Regel ein. Hoher Humus liefert N nach (R-009).

## Zu ungenau

- **P-001:** Die Schwellen für ok/check/likely_deficit in GP-FR-125 sind nicht definiert. Sie müssen Konfiguration mit `source` sein. Ohne Quelle gilt `null`, dann `insufficient_data`.
- **P-002:** GP-FR-123 deckt `l_per_m2` nicht ab (`quantity_total_l` fehlt). Rundung und Einheit der Gesamtmenge sind offen.
- **P-003:** Die Grenzen der Zehrerstufen in kg N/ha sind nicht quantifiziert. Das ist richtig, solange keine Quelle vorliegt. Konflikte (Mentha/Ocimum/Raphanus) stehen in der Lückendatei.

## Hinweise

- Testwerte aus Mathematik ableiten (Einheiten, Rundung), nicht aus Agronomie.
- Gehaltsklassen A–E sind labor- und CAL-spezifisch. Werte aus `test_kit` oder Sensor bekommen niedrigere `confidence` und keine Klassenzuweisung.

## Plausibilitätsrahmen (alle nicht verifiziert)

- Organisches N: 170 kg N/ha·a (DüV); Geltung für Hausgärten und Kompost-Anrechnung offen (R-004).
- Hornspäne: etwa 12–14 % N, Datenblatt je Produkt (R-003).
- Kompost: 3–5 L/m²/Jahr, N gesamt ca. 0,3–0,5 %, im 1. Jahr nur ein kleiner Teil pflanzenverfügbar (R-005).
- Salzschwellen ECe in dS/m (= mS/cm): Bohne und Möhre ca. 1,0, Zwiebel ca. 1,2, Salat ca. 1,3, Tomate ca. 2,5. Prüfen in FAO Irrigation & Drainage Paper 29 Rev.1 und bei Maas & Hoffman 1977 (R-001).
- pH und Kalk: Zielbereiche sind textur- und methodenabhängig (R-008).
- Auswaschung: Sand braucht Split-Gaben, kein Herbst-N (R-009).

## „Bleibt null“-Liste (E-10)

1. Jeder EC-Skalierungsfaktor je Zehrerstufe im Boden.
2. Jede Soll-EC im Boden (EC ist dort nur Grenzwert).
3. kg-N/ha-Bereiche je Zehrerstufe, bis 3 unabhängige Quellen vorliegen.
4. Nährstoffentzug je Kultur und Spezies.
5. Humus-Mineralisierungsrate und N-Nachlieferung.
6. N-Gutschrift-Menge einer Leguminosen-Vorfrucht. Nur das Flag `nitrogen_fixing` gilt.
7. Eigene Zehrerstufe für Gründüngung und Brache (steht schon so in GP-FR-139).
8. Umrechnungsfaktoren EC (1:2, 1:5) gegen ECe und pH (CaCl2 gegen H2O).
9. Kalkmenge aus pH, Textur und Humus.
10. Freisetzungsgeschwindigkeit je Material, außer Herstellerangabe.
11. Obergrenzen `application_rate` je Produkt ohne Herstellerdatenblatt.
12. Rindenmulch-N-Bindung als Zahl (nur qualitatives Flag).

## Nur Hinweis, nie Berechnung (nicht automatisieren)

- Düngemenge aus Bodenanalyse oder Zehrerstufe vorschlagen oder vorbelegen.
- Kalkbedarf als Menge (nur „Kalkbedarf wahrscheinlich“).
- P/K-Empfehlung aus Gehaltsklassen bei Methode ungleich CAL oder `source` ungleich `lab`.
- N-Bedarf aus Nmin berechnen.
- Umrechnung zwischen EC- oder pH-Methoden.
- `feeding_event` (W-007) ohne sichtbare Bestätigung erzeugen.
- Rechtsaussagen wie „DüV eingehalten“ (nur Warnhinweis auf eine Summe).
- Zehrerstufe für Spezies ohne Steckbriefwert ableiten (kein stiller Default).
- Dosierung für Brühen mit Karenz oder Pflanzenschutzbezug.

## Akzeptanzkriterien-Vorschläge (Welle 8)

**Flächendosierung (GP-FR-123)**

- (U) Beet 3,0 × 1,2 m (`area_m2` = 3,6) und `application_rate_g_per_m2` = 80: Dialog speichert `quantity` = 80, `unit` = `g_per_m2`, `quantity_total_g` = 288.
- (U) `application_rate_l_per_m2` = 3 bei 3,6 m²: `quantity_total_l` = 10,8, kein `quantity_total_g`.
- (U) Rate ≤ 0, NaN oder `area_m2` null: 422 bzw. Dialog deaktiviert, nie ein stiller 0-Wert.
- (U) Produkt-N % × Rate × 10 ergibt kg N/ha, beschriftet als Näherung. Test: 80 g/m² × 13 % = 10,4 g N/m² = 104 kg N/ha. Die Saisonsumme-Warnung nutzt einen konfigurierbaren Schwellwert, Default `null` = keine Warnung, bis R-004 belegt ist.

**Bodenanalyse (GP-FR-122)**

- (U) Zwei Analysen mit unterschiedlichem `extraction_method`: getrennte Serien oder Methodenwechsel markiert, keine Umrechnung.
- (U) P/K mit `source` = `test_kit`: keine Gehaltsklasse A–E.
- (U) EC ohne `ec_method`: keine Salz-Bewertung.

**Nährstoff-Hinweis (GP-FR-125)**

- (U) `nutrient_demand` fehlt: `insufficient_data`.
- (U) Vorfrucht `nitrogen_fixing` = true: nur qualitatives Flag, keine N-Menge.
- (U) P- oder K-Klasse D/E: keine Kompost- oder P-Düngeempfehlung.
- (E) Anzeige „Düngebedarf wahrscheinlich“, keine messwertähnliche Zahl.
- (U) Schwellen mit `source` = null: nur `insufficient_data` (E-10-Test).

**EC / E-17**

- (U) heavy_feeder im Boden-Beet: kein EC-Ziel erzeugt oder verändert. Statischer Test: kein Zehrer-Faktor im Code.
- (U) `ec_ms_cm` über konfiguriertem Schwellwert (Default `null` = keine Bewertung): Hinweis „Salzgehalt prüfen“, keine Dosierung.
- (U) Substrat/Nährlösung: EC-Logik bleibt in REQ-004-A, unverändert.
- (U) green_manure oder fallow: keine Zehrerstufe, keine Skalierung.

**Einheiten-Property-Tests (U):** 1 g/m² = 10 kg/ha; 1 L/m² = 1 mm; P2O5 × 0,4364; K2O × 0,8301; 1 mS/cm = 1 dS/m = 1000 µS/cm. Rundung: Gesamtmenge auf 1 g, Rate auf 0,1.

**Seed/Doku:** `seed-data-validator` lehnt Düngeregel-Zahlen ohne `source` ab. Die Null-Liste liegt als Datei vor. REQ-004 Z. 89–94 auf `nutrient_demand` plus `nitrogen_fixing` umstellen; Mengen nur als „Beispiel, unverifiziert“ oder entfernen, bis R-003 bis R-005 geschlossen sind.

## Offene Recherchepunkte (Ausgangslage vor WP 8.5, Ergebnis im Addendum)

| Nr. | Aussage | Bekannte Quellen | Fehlend | Empfohlene Recherche |
|---|---|---|---|---|
| R-001 | Salzschwellen ECe je Kultur | FAO I&D Paper 29 Rev.1 (Ayers & Westcot); Maas & Hoffman 1977 | 3. Quelle, Wert-Zitate | FAO 29 Tabellen, USDA Salinity Lab, Taiz & Zeiger |
| R-002 | Boden-EC ist Salzindikator, Extraktmethoden nicht linear umrechenbar | Bodenkunde (Scheffer/Schachtschabel) | 2 weitere | VDLUFA-Methodenbuch, LfL Bayern, USDA NRCS |
| R-003 | Hornspäne 12–14 % N | Herstellerdatenblätter, LfL | Datenblatt je Produkt | Hersteller, LWK |
| R-004 | 170 kg N/ha organisch (DüV), Geltung für Hausgärten, Kompost-Anrechnung | DüV (gesetze-im-internet.de/d_v_2017) | Auslegung für Hobby, 2 weitere | BMEL, LWK-Merkblätter |
| R-005 | Kompost: L/m²-Gaben, Schüttdichte, N-Gehalt, 1.-Jahr-Verfügbarkeit | BGK (kompost.de) | 2 weitere | BGK-Merkblätter, LfL, LWK |
| R-006 | P/K-Klassen D/E: keine Düngung, Kompost-P-Anreicherung | VDLUFA-Standpunkte | 2 weitere | VDLUFA, LfL, LWK |
| R-007 | CAL-Werte als P2O5/K2O, Gehaltsklassen A–E | VDLUFA | 2 weitere | VDLUFA-Methodenbuch I, LfL |
| R-008 | pH-Zielbereiche je Textur, CaCl2/H2O-Differenz | VDLUFA | 2 weitere | VDLUFA-Standpunkt Kalk, LfL |
| R-009 | Auswaschung nach Textur, Humus-N-Nachlieferung | Bodenkunde-Lehrbücher | quantitative Werte, 2 Quellen | LfL, LWK |
| R-010 | Zehrerstufen je Art (Konflikte Mentha/Ocimum/Raphanus) | Gemüsebau-Literatur | 2 weitere | LWK-Gemüsebau, Fachbücher |
| R-011 | Holzasche/Kalk: pH-Wirkung | BGK, LfL | 1 weitere | LfL, RHS |
| R-012 | Hydro/Substrat-EC je Kultur (0,8–1,2 / 1,2–2,0 / 2,0–3,5 mS/cm) | Resh; Sonneveld & Voogt | Herstellerdaten | Resh „Hydroponic Food Production“, GHE-Datenblätter |

Recherche-Domains: fao.org, vdlufa.de, kompost.de, gesetze-im-internet.de, lfl.bayern.de, rhs.org.uk.

## Kurzfazit

- Hauptbefund: EC-Skalierung nach Zehrerstufe ist für Freilandboden fachlich nicht haltbar. E-17 sollte für Boden lauten „keine EC-Skalierung, nur Salz-Grenzwert-Hinweis“. Nährlösung und Substrat bleiben phasenbasiert in REQ-004-A. **Das ändert eine Betreiberentscheidung (E-17) und ist daher Betreiberfrage, keine Planentscheidung.**
- REQ-004 Z. 89–94 nutzt noch `nitrogen_fixer` als Zehrerstufe; die Heavy-Feeder-Menge liegt nach grober Rechnung nahe an oder über 170 kg N/ha (unverifiziert).
- Bedingtes PASS, wenn E-17 wie oben entschieden wird. Nächster Schritt: R-004/R-005 mit Websuche schließen, weil die REQ-004-Tabelle daran hängt.

## Addendum WP 8.5: Recherche R-001 bis R-012

Stand 2026-11-03, Websuche und Abruf der Quellseiten durch den Orchestrierungs-Agenten. Dieses Addendum ersetzt die „Plausibilitätsrahmen“-Zahlen des Hauptteils, soweit es sie widerlegt.

### Methode und Lesehilfe

- **[G]** = Seite oder PDF wurde geöffnet und der Text gelesen (PDFs lokal mit `pdftotext`). **[S]** = nur aus einem Suchergebnis-Snippet bekannt, nicht geöffnet. **[O]** = geöffnet, aber nur per OCR eines Scans lesbar. Eine [S]-Quelle zählt für die Drei-Quellen-Regel nicht als belegt.
- Eine Zahl gilt nur dann als belegt, wenn mindestens drei Quellen **[G]** sie tragen (E-10). Gemeinsame Datenherkunft ist je Zeile vermerkt. Fehlt eine Voraussetzung, steht `null` mit Grund.
- **Zählregel nach Gegenprüfung:** Kommerzielle Garten-Portale (Plantura) und Händler zählen nicht als Quelle im Sinne von E-10, sie stehen nur als ergänzende Stimme. Institutionelle Quellen (Landesanstalten, Extension, Gesetzestext, BGK-Unterlagen) zählen. Für qualitative Hinweistexte genügen zwei institutionelle [G]-Quellen mit `source`, Default aus. Quellen aus derselben Region oder Veröffentlichungsreihe sind als verwandt vermerkt. Die LWG-Merkblattseite enthält einen internen Widerspruch (Kohlrabi, siehe R-010), ihre Aussagen tragen daher nur zusammen mit einer zweiten Quelle.
- Alle Werte sind Hinweise für Hausgärten und niemals Berechnungsgrundlage. Nichts aus der „Nur Hinweis, nie Berechnung“-Liste wird dadurch automatisiert. Die Quellen beziehen sich meist auf Landwirtschaft oder Erwerbsgartenbau. Die Spalte „Hausgarten“ sagt, was davon übertragbar ist.
- Kurznamen der Quellen stehen in der Quellenliste am Ende des Addendums.

### Ergebnisübersicht

| Nr. | Ergebnis | Quellen [G] | Status |
|---|---|---|---|
| R-001 | ECe-Schwelle Tomate 2,5 / Salat 1,3 / Bohne 1,0 dS/m in 3–4 Veröffentlichungen, aber nur eine unabhängige Datenlinie. Möhre und Zwiebel `null` | Veröffentlichungen 4 / 4 / 3 / 2 / 2, unabhängige Datenlinien 1 | nach E-10 nicht belegt, abhängig von Betreiberfrage #2643 |
| R-002 | Kein Umrechnungsfaktor zwischen EC-Methoden. Textur- und bodenspezifisch | 1 (nur Abstract gelesen), 2 [S] | `null`, Grund: unter drei Quellen |
| R-003 | Hornspäne N-Gehalt 10–14 %, meist etwa 13 %, Produktetikett maßgeblich | 2 institutionelle + 1 Portal | teilweise, Default `null` |
| R-004 | 170 kg N/ha: Betriebsdurchschnitt landwirtschaftlicher Flächen. Geltung für Hausgärten nicht belegt | 1 Rechtstext, 0 weitere [G] | `null` für Hausgarten-Grenzwert |
| R-005 | Kompost: 3 L/m²·a als Obergrenze in 2 verwandten Quellen (beide Bayern). N gesamt, Schüttdichte, Verfügbarkeit chargenabhängig | 2 / 2 / 1 / 1 | Rate teilweise, Rest `null` |
| R-006 | Klasse D/E: P/K-Düngung meist nicht nötig, Kompost nicht zur Nährstoffversorgung (qualitativ) | 2 tragende (LWG, Hessen) | qualitativ, Hinweis mit `source` |
| R-007 | CAL-Einheit (P2O5/K2O oder P) und Klassengrenzen sind labor-, jahr- und länderabhängig (nur P und K, Mg ist ein eigener Punkt) | 4 | Einheit-Pflicht belegt, Grenzen `null` |
| R-008 | pH-Zielwerte je Textur nur für Acker, nur eine Quelle mit Zahlen (Hessen). Hausgarten und CaCl2/H2O-Differenz `null` | 1 mit Zahlen | `null`, Grund: unter drei Quellen |
| R-009 | Humus-N und Auswaschung: nur qualitative Regeln, je Regel meist nur LWG | 1–2 | Zahlen `null` |
| R-010 | Zehrerstufen je Art: Raphanus teilweise, Basilikum widersprüchlich, Mentha ohne Quelle | 2 / 1 / 0 | `null` |
| R-011 | Holzasche und Kalk: qualitativ (hebt pH, nicht auf Säurepflanzen). Menge und CCE `null` | 2 institutionelle + 1 Portal | qualitativ belegt |
| R-012 | Substrat- und Nährlösungs-EC je Kultur | 0 [G] | `null`, Grund: Quellen nur als Snippet, widersprüchlich, Fachbücher nicht geprüft (offen) |

### R-001: Salzschwellen ECe je Kultur

Schwelle = ECe in dS/m (Sättigungsextrakt) ab der der Ertrag sinkt. Steigung in % je dS/m. Einstufung: S empfindlich, MS mäßig empfindlich.

| Kultur | Schwelle | Steigung | Quellen [G] (was sie konkret sagen) | Hausgarten |
|---|---|---|---|---|
| Tomate | 2,5 | 9,9 (MS) | FAO-29: „Tomato … Fruit yield 2.5 9.9 MS“. DWR-22 (Letey): „Tomatoes 2.5 9.9“. UC-84860: ECsoil 2,5. M&H-1977 [O]: Zeile 2,5 / 9,9 / MS | nur als Orientierung |
| Salat | 1,3 | 13 (MS) | FAO-29: „Lettuce … Top FW 1.3 13 MS“. UC-Cahn: „1.3 dS/m in soil paste extract“, 10 % Verlust bei 2,1. UC-84860: 1,3. M&H-1977 [O]: 1,3 / 13 | nur als Orientierung |
| Bohne | 1,0 | 19 (S) | FAO-29: „Bean, common … Seed yield 1.0 19 S“. DWR-22: „Beans 1.0 19.0“, nach DWR-22 die niedrigste Schwelle unter den dort bewerteten Gemüse- und Feldfrüchten (Möhre liegt nach FAO-29 gleichauf). UC-84860: 1,0 | nur als Orientierung |
| Möhre | `null` | | FAO-29: 1,0 / 14 / S. UC-84860: 1,0. Nur 2 Quellen, M&H-1977-Scan nicht eindeutig lesbar | `null`, Grund: 2 Quellen |
| Zwiebel | `null` | | FAO-29: 1,2 / 16 / S. UC-84860: 1,2. Nur 2 Quellen | `null`, Grund: 2 Quellen |

- **Einschränkung Datenlinie:** Alle Quellen gehen auf die Kompilation von Maas & Hoffman 1977 zurück. FAO-29 übernimmt sie, UC-84860 trägt „FAO 29“ in der Tabellenüberschrift, DWR-22 und UC-Cahn sind abgeleitet. Die Zeile aus M&H-1977 ist per OCR gelesen und für Bohne nicht lesbar. Es gibt mehrere Veröffentlichungen, aber nur eine unabhängige Datenlinie. Wie unabhängig die zugrunde liegenden Einzelversuche sind, wurde nicht geprüft. Spätere Neubewertungen (Maas 1986, Grieve et al. 2012) wurden nicht geprüft und bleiben als offener Prüfpunkt zu R-001. Nach E-10 gelten die Werte daher als nicht belegt, solange der Betreiber die Datenlinie nicht akzeptiert (Frage in #2643, nicht blockierend). Bis dahin höchstens konfigurierbarer Hinweis-Schwellwert mit `source`, Default `null`.
- **Weitere Einschränkungen:** Die Schwellen stammen aus Bewässerungsversalzung. Düngesalze (Nitrat, Kalium) verhalten sich anders. Die Boden-EC im Freiland schwankt stark (Düngegabe, Niederschlag, Winterauswaschung). Eine Einzelmessung ist kein Vergleich mit einer Dauerschwelle.
- Die Schwellen gelten für ECe im Sättigungsextrakt (UC-Cahn: „soil paste extract“). Das Messgerät im Hausgarten liefert das nicht (siehe R-002). Ohne `ec_method` = ECe keine Bewertung.
- Die Schwellen stammen aus Versuchen mit bewässerungsbedingter Versalzung im Erwerbsanbau. Sorte, Klima, Salzart und Bewässerung verschieben sie (UC-Cahn).
- Die Zahlen aus dem Hauptteil (Bohne und Möhre 1,0, Zwiebel 1,2, Salat 1,3, Tomate 2,5) stimmen mit FAO-29 überein. Neu ist die Einschränkung auf Datenlinie und Quellenzahl.

### R-002: Boden-EC ist Salzindikator, Extraktmethoden nicht linear umrechenbar

- Kein Wert. Faktoren zwischen EC 1:5 und ECe hängen von der Textur ab und gelten nur lokal.
- Belege: Spiteri & Sacco 2024 [G, Abstract]: „Models that convert EC of soil:water suspensions … to ECe are soil specific and are not universal models.“ Kargas et al. 2022 (Water 14, 642) [S]: Faktor je nach Boden, in einem Review 5,05–11,7, in grobem Boden höher. Qld-Handbuch Kap. 5 [S]: Umrechnung nach Tongehalt, kann bei hoher Salinität überschätzen. Seiten von Kargas und Qld ließen sich nicht abrufen (403, Zertifikat bzw. leerer Download).
- Ergebnis: Bestätigt U-002 und „bleibt null“ Nr. 8. `ec_method` am Profil ist Pflicht, keine Umrechnung. Hausgarten: Sondenwerte und 1:5-Werte nicht mit ECe-Schwellen vergleichen.
- Status `null`, Grund: nur eine geöffnete Quelle, zwei Snippets. Der Grundsatz („nicht umrechenbar“) ist unstrittig, der Faktor selbst bleibt aus.

### R-003: Hornspäne N-Gehalt

| Quelle [G] | Aussage |
|---|---|
| LWG-Gemüsegarten (Merkblatt 2202, 12/2020) | „Hornmehl (von 10 % N bis 14 % N je nach Hersteller, meist jedoch knapp 13 %)“ |
| Plantura-Horn (Portal, nur ergänzend) | „Hornspäne enthält 9 – 14 % Stickstoff“ |
| BGK-Faltblatt Schweinfurt (Fußnote) | „80 g Hornspäne, -mehl enthalten ca. 10 g Stickstoff“, das sind 12,5 % |

- Wert: 10–14 %, meist knapp 13 % (LWG, BGK-Faltblatt rechnerisch 12,5 %). Die Untergrenze 9 % steht nur beim Portal und wird nicht übernommen. Maßgeblich ist immer das Produktetikett. Ohne Etikettenwert bleibt `product_n_percent` = `null` (kein Default). Der Hauptteil-Wert 12–14 % ist damit nicht widerlegt, sondern nur durch die LWG-Spanne ergänzt.
- Freisetzung (nur LWG): Hornmehl schneller als Späne, Späne mehrere Monate. Das bleibt qualitativer Hinweis mit `source`, Default aus. Die Zeitangaben („6 Wochen“, „Ende August“) sind Einzelquelle und werden nicht übernommen (Nr. 10).
- Dosierhinweise der Quellen: LWG maximal 50 / 100 / 150 g/m² je Bedarf (gering/mittel/hoch) auf Böden mit hohem P/K. BGK-Faltblatt „plus Zugabe von 15–30 g N“ (Stark), 10–20 g N (Mittel). Plantura 30–60 g/m² vor der Saat bei Gemüse. Handelsetiketten reichen bis 200 g/m² [S]. Spannen widersprechen sich, daher keine vorbelegte Menge (Hint-only-Liste).

### R-004: 170 kg N/ha, Geltung im Hausgarten, Kompost-Anrechnung

- **Wortlaut [G]:** DüV § 6 Abs. 4 Satz 1: „im Durchschnitt der landwirtschaftlich genutzten Flächen des Betriebes 170 Kilogramm Gesamtstickstoff je Hektar“ und Jahr. Gelesen wurden nur diese Auszüge (§ 1 Abs. 1, § 6 Abs. 4 Satz 1), keine Gesamtlesung.
- **Geltung im Hausgarten:** Keine geöffnete Quelle sagt, ob die Grenze für Hausgärten gilt. Ergebnis `null`. Das ist keine Rechtsauskunft und keine Auslegung. Die App trifft keine Rechtsaussage („DüV eingehalten“ bleibt auf der Hint-only-Liste).
- **Folge für den Hauptteil:** Wo der Hauptteil (Plausibilitätsrahmen, F-002) mit 170 kg N/ha vergleicht, ist das ein Vergleichsmaßstab aus der Landwirtschaft, kein belegter Hausgarten-Grenzwert.
- **Kompost-Anrechnung [G]:** BGK-Zertifikat Witten, Tabelle 2: Mindestanrechenbarkeit nach DüV im Anwendungsjahr 5 % von N gesamt, danach 4 / 3 / 3 %. Das ist eine landwirtschaftliche Mindestanrechnung, kein Messwert für Pflanzenverfügbarkeit.
- **Dreijahresgrenze Kompost:** Merkblatt Bayern [S]: höchstens 510 kg Gesamt-N je ha in 3 Jahren. Das BGK-Zertifikat [G] nennt für die Bioabfallverordnung 30 t TM bzw. 42 t FM je ha in 3 Jahren. Beides Landwirtschaft.
- **Saisonsumme-Warnung (GP-FR-123):** Schwellwert bleibt Konfiguration, Default `null`. Wer einen Wert einträgt, trägt die Quelle selbst ein.

### R-005: Kompost, L/m², Schüttdichte, N-Gehalt, Verfügbarkeit im 1. Jahr

| Größe | Wert / Aussage | Quellen [G] | Status |
|---|---|---|---|
| Gabe | höchstens 3 L/m²·a, ohne Bezug zur Zehrerstufe | LWG: „maximalen Menge von 3 Liter pro m²“. BGK-Faltblatt Schweinfurt: 3 L für Starkzehrer. Beide Bayern, vermutlich verwandt. Bayreuth, Berlin [S] bestätigen 3 L | nur als Obergrenze-Hinweis, keine Vorbelegung. Die Staffel 3/2/1 L je Zehrerstufe (Faltblatt) wird nicht übernommen, sie wäre eine Menge aus der Zehrerstufe |
| N gesamt | Witten 1,12 % FM (7,07 kg/m³). Hessen-Tab. 8: 12,4 kg/t FM (1,24 %). Weitere Zertifikate [S]: 0,58–1,62 % FM | 2 [G] + 3 [S] | Spanne etwa 0,6–1,6 % FM, Default `null` |
| Schüttdichte | Witten 630 kg/m³ (0,63 kg/L). Weitere [S]: 500–780 kg/m³ | 1 [G] | `null`, Grund: eine Quelle |
| N im 1. Jahr verfügbar | Witten: löslicher N 0,05 % von 1,12 %, DüV-Mindestanrechnung 5 % | 1 [G] | `null` als Zahl, qualitativ „Kompost ist kein N-Lieferant“ (LWG, BGK-Faltblatt, BGK-Zertifikat) |

- **Korrektur zum Hauptteil:** Der dort genannte N-Gehalt 0,3–0,5 % liegt unter den zwei geöffneten Gütezeugnissen (1,12 und 1,24 % FM). Die Zahl „6–15 g N/m² gesamt“ in F-002 ist damit für diese Zeugnisse zu niedrig. Plausibilitätsprobe, keine Berechnungsgrundlage, nur aus einem Gütezeugnis, ohne Aussagekraft für andere Chargen und ohne Vergleich mit einer Grenze: Das Zertifikat Witten ergibt für die Gesamt-N-Menge einer 3-L-Gabe die Größenordnung zweistellig Gramm je m², deutlich über der Hauptteil-Annahme. Die Schüttdichte ist dafür nur eine Quelle (Zeile oben, `null`). Der Hauptteil-Auftrag bleibt: Tabelle gegen eine Gesamt-N-Bilanz prüfen oder Mengen entfernen. Die Mindestanrechnung (5 %) ist kein Messwert, Immobilisierung ist ebenfalls möglich. Keine Zahl zur Verfügbarkeit.
- Hessen-Tab. 8 [G]: „Komposte … dürfen nicht nach Faustzahlen, sondern nur auf Grundlage von Analyseergebnissen ausgebracht werden.“ Das stützt `null` als Default für alle Kompostgehalte.
- Kompost liefert nach LWG [G] Phosphat ganz und Kali weitgehend. Das BGK-Zertifikat [G]: P2O5 und K2O „zu 100 % anrechenbar“, Grunddüngung bei üblicher Gabe weitgehend abgedeckt.
- Sandbeet-Neuanlage (Schweinfurt, einmalig 10–20 L/m²) und Bayreuth [S] (25–45 L/m²) sind Sondergaben und gehören nicht in die Jahresrate.

### R-006: P/K-Klassen D/E, Kompost-P-Anreicherung

| Quelle [G] | Aussage |
|---|---|
| LWG-Gemüsegarten | Hausgartenböden oft „sehr reichlich mit Phosphat und Kali versorgt (Versorgungsstufe D und E), so dass reine Stickstoffdünger empfohlen werden“. Kompost deckt Phosphat „ganz“ |
| Hessen-Landeslabor Erläuterungen | Bei „überversorgten Böden (GK D und E) sollte diese Menge reduziert“ werden. Ziel ist Klasse C |
| BGK-Zertifikat Witten (nur Kontext, trägt D/E nicht) | P2O5 und K2O „zu 100 % anrechenbar“, Grunddüngung bei üblicher Kompostgabe „weitgehend abgedeckt“ |

- Aussage (qualitativ, Hinweis mit `source`): Bei Klasse D/E ist P/K-Düngung meist nicht nötig, und Kompost dient dann nicht der Nährstoffversorgung. Kompost zur Bodenverbesserung ist damit nicht ausgeschlossen. Hessen sagt „Menge reduzieren“, nur LWG „reine N-Dünger“. Das schließt U-004 nur als Hinweistext, ohne Menge.
- Bedingung: Nur wenn die Klasse vom Labor stammt (`source` = `lab`, CAL). Siehe R-007.

### R-007: CAL-Werte als P2O5/K2O, Gehaltsklassen A–E

| Quelle [G] | Aussage |
|---|---|
| LfL Bayern, Verbindliche Hinweise Boden | Angabe „Kalium: mg K2O/100 g Boden“, „Phosphor: mg P2O5/100 g Boden“ |
| Hessen-Landeslabor (ab 2024) | Klassen in mg P/100 g **und** mg P2O5/100 g. „traditionell“ P2O5. VDLUFA schlägt mg P/kg vor. Faktor 1 mg P × 2,2914 = P2O5 |
| RLP-Folien PEDÜ 7 (VDLUFA 1997 und 2018) | Alte Klassen in mg P2O5/100 g (A 0–5 … E ab 35). VDLUFA-Standpunkt 2018: A < 1,5 … E > 12 mg CAL-P/100 g. Trockengebiete abweichend |
| Möller (Sachsen) | „Ergebnisse in mg K (K2O) und P (P2O5) pro 100 g“ |

- Magnesium wird nicht mit CAL, sondern mit CaCl2 extrahiert (Möller [G], LfL [G]). Mg-Klassen gehören nicht in diesen Befund und bleiben ein eigener offener Prüfpunkt, Status `null`.
- Ergebnis: Die Einheit (P oder P2O5, K oder K2O) und die Klassengrenzen hängen von Labor, Bundesland, Jahr, Bodenartgruppe und Nutzung ab. Beispiel Phosphat Klasse C: 3,1–6,0 mg P/100 g (VDLUFA 2018), 3,3–8,0 (Hessen 2024), 10–20 mg P2O5 (VDLUFA 1997). Kali-Klassen unterscheiden zusätzlich nach Bodenartgruppe.
- **Folge:** Keine feste Klassentabelle in der App. Klassen kommen vom Labor als Text (`content_class`) zusammen mit `unit`, `extraction_method`, Labor und Jahr. Eigene Klassenzuweisung aus Zahlen bleibt `null`/verboten (bestätigt Hint-only-Liste und AK „P/K mit `test_kit`: keine Klasse“).
- Faktor P2O5 → P: 0,4364 ist als Kehrwert von 2,2914 aus Hessen [G] belegt. Der Property-Test für P2O5 × 0,4364 prüft auf vier Stellen. Der Faktor K2O → K (0,8301) ist reine Stöchiometrie aus Atommassen und in keiner geöffneten Quelle genannt. Er ist Mathematik, keine Agronomie, und bleibt als Property-Test zulässig.

### R-008: pH-Zielbereiche je Textur, CaCl2/H2O-Differenz

- **Methode:** Laborstandard ist pH in 0,01 M CaCl2 (LfL-Hinweise [G], Möller [G]). Der Hauptteil nennt deshalb zu Recht CaCl2 als Referenz.
- **Zielbereiche (nur Acker, Humus unter 4 %, Klasse C „Erhaltungskalkung“) [G]** nach Hessen-Landeslabor, Bodenartgruppe nach Tongehalt (I leicht bis 12 %, II mittel 13–25 %, III schwer ab 26 %): I 5,6–6,1, II 6,2–6,9, III 6,4–7,2. Grünland liegt je Gruppe etwa 0,6–0,7 niedriger. Klasse D/E: keine Kalkung. LfL Bayern [S] nennt ähnliche Bereiche je Bodenart (Sand 5,4–5,8 bis Ton 6,4–7,2). Die VDLUFA-Standpunkt-Kalkung-PDF war nicht abrufbar (404).
- **Abweichung zum Hauptteil:** Die dortigen Bereiche (Sand 5,5–6,5, Lehm 6,0–7,0, Ton 6,5–7,5) sind durch die Quellen nicht gedeckt. Der Vergleich mit den Acker-Werten dient nur als Hinweis auf die Abweichung, nicht als Maßstab für den Hausgarten.
- **Folge für die App:** Die Referenz ist CaCl2, Hausgarten-Geräte messen meist in H2O oder per Teststreifen. Ohne `ph_method` = CaCl2 und ohne Umrechnung gibt es keinen Soll-Ist-Vergleich, nur die Anzeige des Messwerts.
- **Hausgarten:** Die Tabellen gelten für Ackerbau. Gemüse und Zierpflanzen im Hausgarten haben eigene Ansprüche. Es gibt keine geöffnete Quelle für Hausgartenziele je Textur. `target_ph` je Textur bleibt `null`.
- **CaCl2-H2O-Differenz:** Keine Quelle nannte einen Zahlenwert. Umrechnung bleibt verboten (Hint-only-Liste). Der Hauptteil-Wert „0,5–0,8“ ist nicht belegt und entfällt.
- Status `null`, Grund: nur eine geöffnete Quelle mit Zahlen (Hessen). LfL Bayern ist für die Methode [G], für die Zielbereiche nur [S].

### R-009: Auswaschung nach Textur, Humus-N-Nachlieferung

| Quelle [G] | Aussage |
|---|---|
| LWG-Gemüsegarten | Humus 1,5 %: etwa 4 g N/m²·a aus der organischen Masse. 4–8 %: über 11 g/m². Bei Humus über 4 % im Frühjahr nur 25 % Startgabe. Auf leichten Böden Stickstoff in Teilgaben. Horndünger nicht nach Ende August |
| Sachsen LfULG Tab. 12 (DüV Anl. 4 Tab. 6) | Humus über 4 %: Mindestabschlag 20 kg N/ha (=2 g/m²). Betrifft Ackerbau und Gemüsebau |

- Qualitative Regeln belegt und als Hinweistext zulässig: Bei hohem Humus weniger N, bei leichten Böden Teilgaben, kein Herbst-N.
- Die Teilgaben auf leichten Böden und die Startgabe bei hohem Humus stehen nur bei LWG, die DüV-Tabelle stützt nur den Humusabschlag. Sie bleiben Hinweis mit `source`, Default aus.
- Zahlen: LWG (4 und 11 g/m²) und DüV-Tabelle (20 kg N/ha) messen Verschiedenes und haben je eine Quelle. Eine Auswaschungsmenge je Textur fand sich in keiner geöffneten Quelle. Humus-Mineralisierungsrate und N-Nachlieferung bleiben `null` (Nr. 5).

### R-010: Zehrerstufen je Art

| Art | Quellen [G] | Ergebnis |
|---|---|---|
| Raphanus sativus var. sativus (Radieschen) | LWG: Stufe „gering“. Plantura: Schwachzehrer. Stuttgarter Zeitung [S] ebenso, Gartenjournal [S] Mittelzehrer | 2 [G] einig, dritte nur [S], Gegenstimme [S]: `null` |
| Raphanus sativus var. niger (Rettich) | LWG: „mittel“. Plantura: Mittelzehrer | 2 [G] einig: `null` |
| Ocimum basilicum | Plantura: Starkzehrer („Nur ein relativ kleiner Teil der Kräuter sind Starkzehrer. Dazu gehören zum Beispiel Basilikum“). Hornbach/OBI [S] Kräuter allgemein schwach | 1 [G]: `null` |
| Mentha | in keiner Quelle klassifiziert | `null` |

- N-Mengen je Stufe: Plantura „ungefähr 25 g N/m²“ (stark), „10 bis 25“ (mittel), „weniger als 10“ (schwach). BGK-Faltblatt nennt 15–30 und 10–20 g N. Zwei Quellen mit überlappenden, nicht deckungsgleichen Bereichen, davon eine ein Portal: P-003 bleibt, keine kg-N/ha-Bereiche (Nr. 3).
- Die Konflikte der Lückendatei (Mentha/Ocimum/Raphanus) bleiben damit ohne Wert. Der Steckbrief-Wert gilt weiter, bei fehlendem Wert `insufficient_data`.
- Die Tabellen der LWG-Merkblattseite zeigen eine Art (Kohlrabi) in den beiden Tabellen in unterschiedlicher Stufe. Auch deshalb keine Übernahme ganzer Listen. Der Widerspruch schwächt auch die LWG-Aussagen in R-003, R-005, R-006 und R-009 (siehe Zählregel).

### R-011: Holzasche und Kalk, pH-Wirkung

| Quelle [G] | Aussage |
|---|---|
| UNH Extension | Holzasche ist ein „natural substitute for lime“. Kalkwirkung (CCE) 25–59 % gegenüber 90–95 % bei Kalk, daher 2–4-fache Menge |
| Alberta Agriculture | Holzasche als Kalkungsmittel, CCE 55–65 % |
| Plantura-Asche | pH etwa 10–13. Nicht auf leichten Böden (Überkalkung) und nicht für Rhododendron, Heidelbeere und Säurepflanzen. Schwere, saure Böden geeignet |

- Hinweistext mit `source` zulässig (zwei institutionelle Quellen UNH und Alberta tragen: Asche wirkt als Kalk und hebt den pH). „Nicht bei Säurepflanzen“ und „nicht auf leichten Böden“ stehen nur beim Portal und gelten als ergänzende Stimme. Missouri Extension [S] nennt zusätzlich: erst testen, keine Asche aus Müll, Kohle oder behandeltem Holz (Schwermetalle). Die Quellen UNH und Alberta beziehen sich auf Nordamerika. Holzasche liefert auch K und P, bei P/K-Klasse D/E also zusätzlich ungünstig (Bezug U-004).
- Mengen: Die Quellen widersprechen sich um mehr als eine Größenordnung (Plantura 100–400 g/m² alle 3–4 Jahre, selbst.de [S] höchstens 30 g/m², Küchenfibel [S] 100 mL/m²·a). Die CCE schwankt von 25 bis 65 % (UNH und Alberta) bzw. 10–90 % [S]. Keine Menge, kein Wert. Kalkmenge bleibt Hint-only (Nr. 9).

### R-012: Substrat- und Nährlösungs-EC je Kultur

- Keine Quelle geöffnet, die Seiten ließen sich nicht lesen (Produce Grower leer, UMKC-Deck umgeleitet). Resh und Sonneveld & Voogt sind Fachbücher, die als Quelle zulässig sind. Sie waren in dieser Sitzung nicht zugänglich. Das ist ein Zugangsproblem, daher bleibt R-012 mit Bibliotheksbezug offen.
- Die Messgröße ist je EC-Quelle festzulegen: Nährlösungs-EC, Drain-EC und Substrat-Extrakt-EC (1:1,5, Sättigungsextrakt) sind verschiedene Größen und dürfen nicht als eine geführt werden.
- Aus Snippets [S], widersprüchlich: Tomate 1,5–3,5 mS/cm (UMKC-Folien nach McAvoy) bzw. 2,5–3,5 (Produce Grower). Salat 1,5–2,0, 0,8–1,6 oder 1,2–1,8 (drei Blogs und Händler). Kräuter 0,5–4,0 ohne Ertragsunterschied (Iowa State laut Produce Grower) bzw. 1,0–1,6 (Blogs).
- Ergebnis: Die Hauptteil-Zahlen (0,8–1,2 / 1,2–2,0 / 2,0–3,5 mS/cm) sind nicht bestätigt. Alle Werte `null`, Grund: Quellen nur als Snippet und untereinander widersprüchlich. EC für Nährlösung und Substrat bleibt phasenbasiert in REQ-004-A, unverändert.

### Aktualisierte „Bleibt null“-Liste (E-10)

Die zwölf Punkte des Hauptteils bleiben `null`. Ergänzt um den Stand nach WP 8.5:

1. Jeder EC-Skalierungsfaktor je Zehrerstufe im Boden (Fachentscheidung F-001, keine Quelle).
2. Jede Soll-EC im Boden. Die ECe-Schwellen aus R-001 sind Grenzwerte, keine Soll-Werte.
3. kg-N/ha-Bereiche je Zehrerstufe (R-010: Quellen widersprechen sich).
4. Nährstoffentzug je Kultur und Art.
5. Humus-Mineralisierung und N-Nachlieferung als Zahl (R-009).
6. N-Gutschrift einer Leguminosen-Vorfrucht.
7. Eigene Zehrerstufe für Gründüngung und Brache.
8. Umrechnung zwischen EC-Methoden (R-002) und pH-Methoden (R-008).
9. Kalkmenge aus pH, Textur und Humus (R-008, R-011).
10. Freisetzungsgeschwindigkeit je Material außer Herstellerangabe (R-003).
11. Obergrenzen `application_rate` je Produkt ohne Herstellerdatenblatt (R-003).
12. Rindenmulch-N-Bindung als Zahl.

Neu `null` durch dieses Addendum, mit Grund:

13. ECe-Schwelle Möhre und Zwiebel (R-001: nur zwei Quellen).
14. Hausgarten-Grenzwert 170 kg N/ha und jede Aussage zur Geltung der DüV im Hausgarten (R-004).
15. Kompost: Schüttdichte, N-Gehalt als Default, N-Verfügbarkeit im 1. Jahr (R-005).
16. Numerische Klassengrenzen für P/K und eigene Klassenzuweisung (R-007). Mg-Klassen: eigener offener Prüfpunkt, Methode CaCl2.
17. `target_ph` je Textur für Hausgarten und pH-Differenz CaCl2/H2O (R-008).
18. Zehrerstufe Radieschen, Rettich, Basilikum, Mentha (R-010).
19. Holzasche-Menge und CCE-Zahl (R-011).
20. Substrat- und Nährlösungs-EC je Kultur (R-012).

Zulässig als Hinweistext ohne Zahl, nur mit `source`, Default aus: Kompost ist kein N-Lieferant (R-005), bei Klasse D/E ist P/K-Düngung meist nicht nötig (R-006), Humus über 4 % gleich weniger N und leichte Böden Teilgaben (R-009), Holzasche und Kalk heben den pH (R-011), Horndünger langsam wirkend (R-003). Mit Zahl, nur als konfigurierbarer Hinweis mit `source`, Default `null`: ECe-Schwellen Tomate, Salat, Bohne (R-001, nach E-10 nicht belegt, abhängig von #2643) und die Hornspäne-Spanne (R-003).

### Offene Prüfpunkte nach Gegenprüfung

- **F-001 / Boden-EC ist Salzindikator, Zehrerstufe ist N-Entzug:** plausibel und in REQ-004 selbst so angelegt, aber nicht mit drei Quellen belegt. Bleibt als offener R-Punkt `null`, Grund: nicht recherchiert. Die Entscheidung E-17 stützt sich auf die Hauptteil-Begründung, nicht auf dieses Addendum.
- **U-006 Denitrifikation und Staunässe, Auswaschung nach Textur:** keine geöffnete Quelle, bleibt `null`.
- **Jauche (F-002):** N-Beitrag nicht recherchiert, bleibt `null`. Hessen Tab. 8 [G] nennt Jauche mit 1,1 kg Gesamt-N je m³ (Wirtschaftsdünger der Landwirtschaft, keine Hausgartenjauche), das ist keine Quelle für Pflanzenbrühen.
- **Mg-Klassen (CaCl2):** nicht recherchiert.
- **Maas 1986 und Grieve 2012:** spätere Neubewertungen der Salzschwellen nicht geprüft.
- **Resh, Sonneveld & Voogt:** R-012, Bibliotheksrecherche offen.

### Folgen für Welle 8

- **WP 8.9 (N-Summen-Warnung):** Schwellwert Default `null`, keine Warnung. Es gibt keinen belegten Hausgarten-Grenzwert (R-004).
- **WP 8.10 (Schwellen):** Nur konfigurierbare ECe-Hinweise für Tomate, Salat, Bohne mit `source` und `ec_method` = ECe. Sonst keine Bewertung.
- **WP 8.11 (Klassen/Hinweise):** Klassen nur als Labortext übernehmen. Hinweistexte aus R-006, R-009, R-011 nur mit `source`, Default aus. pH nur anzeigen, kein Soll-Ist-Vergleich ohne `ph_method` = CaCl2.
- **REQ-004 Z. 89–94:** „Heavy feeder 3–4 L/m²“ überschreitet die in zwei verwandten Quellen genannte Obergrenze von 3 L/m². Nach den Gütezeugnissen liegt die Gesamt-N-Menge einer solchen Gabe deutlich über der Hauptteil-Annahme. Daher bleibt die Anweisung des Hauptteils: Tabelle auf `nutrient_demand` plus `nitrogen_fixing` umstellen und Mengen als „Beispiel, unverifiziert“ kennzeichnen oder entfernen.
- **Betreiberfrage (nicht blockierend, #2643):** Genügt für E-10 eine Veröffentlichungsreihe mit gemeinsamer Datenlinie (Maas & Hoffman, FAO-29, UC)?

### Quellenliste

Geöffnet [G], Abruf 2026-11-03:

- **FAO-29:** FAO Irrigation and Drainage Paper 29 Rev. 1, Tabelle A1.1, <http://www.fao.org/4/Y4263E/y4263e0e.htm>
- **M&H-1977 [O]:** Maas & Hoffman, Crop Salt Tolerance, USDA-ARS, <https://www.ars.usda.gov/arsuserfiles/20360500/pdf_pubs/P572.pdf> (Scan, nur per OCR lesbar, einzelne Zeilen unsicher)
- **UC-Cahn:** UC Cooperative Extension, Management of Salinity for Lettuce Production, <https://ccfruitandnuts.ucanr.edu/sites/default/files/2013-08/171001.pdf>
- **UC-84860:** UC-Folien Gemüse-Salztoleranz (Tabelle „FAO Irrigation and Drainage Paper 29, 1985“), <https://ccfruitandnuts.ucanr.edu/sites/default/files/2011-04/84860.pdf>
- **DWR-22 (Letey):** Salinity Water Values that are Protective for Agricultural Crop Production, <https://www.waterboards.ca.gov/waterrights/water_issues/programs/hearings/delta_salinity/exhibits/dwr/dwr22_rev.pdf>
- **Spiteri & Sacco 2024:** Abstract, <https://um.edu.mt/library/oar/handle/123456789/117868>
- **DüV § 1 und § 6:** <https://www.gesetze-im-internet.de/d_v_2017/__1.html>, <https://www.gesetze-im-internet.de/d_v_2017/__6.html>
- **LWG-Gemüsegarten:** Bayerische Gartenakademie, Hinweise zur Düngung im Gemüsegarten, Merkblatt 2202, <https://www.lwg.bayern.de/mam/cms06/gartenakademie/dateien/infoschrift_duengung_leicht_gemacht.pdf>
- **Plantura-Horn:** <https://www.plantura.garden/gartenpraxis/duenger/hornspaene>
- **Plantura-Zehrer:** <https://www.plantura.garden/gemuese/gemuese-anbauen/starkzehrer-mittelzehrer-und-schwachzehrer>
- **Plantura-Asche:** <https://www.plantura.garden/gartenpraxis/duenger/asche-als-duenger>
- **BGK-Faltblatt Schweinfurt:** <https://www.landkreis-schweinfurt.de/fileadmin/inhalt_service-info/SG43_Abfallwirtschaft/Faltblaetter_u.ae/17241_Kompostaktion_2020_Faltblatt_6.2.pdf>
- **BGK-Zertifikat Witten (AHE):** <https://www.ahe.de/downloads/zertifikate/jahreszeugnis_kompost.pdf>
- **LfL Bayern, Verbindliche Hinweise Boden:** <https://www.lfl.bayern.de/mam/cms07/zentrale_analytik/dateien/5_verbindliche-hinweise-boden.pdf>
- **Hessen-Landeslabor:** Erläuterungen Bodenuntersuchung Acker und Grünland, <https://lhl.hessen.de/sites/lhl.hessen.de/files/2024-03/erlaeuterungen_bodenuntersuchung_acker_und_gruenland.pdf>
- **RLP PEDÜ 7:** Düngebedarfsermittlung Grundnährstoffe 2021 (Folien), über <https://www.xn--dngeberatung-dlb.rlp.de/> abgerufen
- **Möller (Sachsen):** Bodenuntersuchungsmethoden, <https://www.landwirtschaft.sachsen.de/download/Bodenuntersuchungsmethoden_MoeLLER_2024_02_23.pdf>
- **Sachsen Tab. 12:** <https://landwirtschaft.sachsen.de/download/Tab_12_Abschlaege_auf_Grund_N-Nachlieferung_aus_d_Bodenvorrat_bei_Ackerkulturen_u_Gemuese_2019_02_25.pdf>
- **UNH Extension:** Guide to Using Wood Ash as a Soil Amendment, <https://extension.unh.edu/resources/files/Resource004042_Rep5718.pdf>
- **Alberta Agriculture:** Wood Ash, an Alternative Liming Material, <https://www1.agriculture.alberta.ca/$department/deptdocs.nsf/all/agdex3435/$file/534-2.pdf>

Nur Snippet [S], nicht geöffnet oder nicht abrufbar: Kargas et al. 2022 (<https://www.mdpi.com/2073-4441/14/4/642>, 403), Qld Salinity Management Handbook Kap. 5, Missouri Extension „Ashes to ashes“ (403), VDLUFA-Standpunkt Kalkung (404), LfL-Merkblatt DüV Gemüse, Merkblatt Bayern 170 kg/510 kg, Landkreis Bayreuth, Berlin Eigenkompostierung, weitere RAL-Zertifikate (Stade, Euskirchen, Hildesheim), Stuttgarter Zeitung, Gartenjournal, Hornbach, OBI, selbst.de, Küchenfibel, Produce Grower, UMKC-Folien, Spider-Farmer- und Rise-Gardens-Blogs, BayWa-Datenblätter.
