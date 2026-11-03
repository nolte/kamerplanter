# Agrarbiologisches Review: REQ-053 Welle 8 (E-17, #2411 / #2494)

> **Herkunft und Status.** Berichtstext des Agenten `agrobiology-requirements-reviewer` vom 2026-11-03, vom Orchestrator
> unverändert in diese Datei übernommen, weil der Agent weder Schreibzugriff noch Websuche hatte. **Alle Zahlenwerte sind
> Fachwissen aus dem Kopf und nach der Drei-Quellen-Regel nicht verifiziert.** Die genannten Quellen sind
> Recherche-Empfehlungen, keine abgerufenen URLs. Vor jeder Implementierung, die einen dieser Werte benutzt, müssen R-001 bis
> R-012 mit Websuche geschlossen werden; bis dahin gilt E-10 (Wert ohne Quelle bleibt `null`).

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

## Offene Recherchepunkte: Verifizierung ausstehend

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
