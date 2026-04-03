# Fachliches Review: Naehrstoffplan Guzmania lingulata / Gardol Gruenpflanzenduenger

**Reviewer:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Geprueftes Dokument:** `spec/knowledge/nutrient-plans/guzmania_gardol.md` v1.0
**Referenzdokumente:**
- `spec/knowledge/plants/guzmania_lingulata.md`
- `spec/knowledge/products/gardol_gruenpflanzenduenger.md`
**Gegen-Modell geprueft:** `src/backend/app/domain/models/nutrient_plan.py`, `src/backend/app/common/enums.py`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit | 4 / 5 | Weitgehend korrekt; ein kritischer Fehler bei Ethylen-Induktion (Timing), ein fachlicher Hinweis zu Trichomer-Schutzwirkung |
| Monokarp-Lebenszyklus-Abbildung | 5 / 5 | Vorbildlich: null-Neustart, alle Phasen is_recurring: false, Kindel als neue Instanz klar beschrieben |
| NPK / EC Plausibilitaet | 5 / 5 | Extrem niedrige Dosen korrekt und begruendet; Vergleichswerte valide |
| Trichterbewässerung | 4 / 5 | Fachlich korrekt; ein fehlender Aspekt (Trichter-Volumen bei adulter Pflanze vs. Kindel-Phase, Skalierungsregel nicht im JSON) |
| Substrat-Wahl ORCHID_BARK | 5 / 5 | Korrekt; gut begruendet; Enum-Wert stimmt mit Backend uberein |
| RO-Wasser-Pflicht | 5 / 5 | 100%-Pflicht korrekt gesetzt und mehrfach erklaert |
| Herzfaeule-Risiko | 5 / 5 | Explizit als haeufigste Todesursache dokumentiert, Temperaturgrenze klar |
| Gardol-Limitationen | 5 / 5 | Ehrlich benannt: nicht erste Wahl, Orchideenduenger als Ideal genannt |
| Lueckenlos-Pruefung (104 Wochen) | 5 / 5 | Korrekt (8+52+16+28=104); kein Wochensprung |
| Konsistenz Tabellen vs. JSON | 4 / 5 | Ein technischer Feldfehler (FoliarParams: falscher Feldname im JSON); ein logischer Hinweis (GERMINATION JSON-Volume) |
| Technische JSON-Korrektheit | 3 / 5 | Zwei Modell-Abweichungen identifiziert (Feldfehler + Channel-ID-Encoding) |

**Gesamteinschaetzung:** Der Plan ist fachlich sehr solide und deutlich besser als der Durchschnitt von Hobbyisten-Pflegeanweisungen. Die Besonderheiten der Gattung Guzmania -- monokarper Zyklus, Trichterbewässerung, Trichom-Sensitivitaet, Schwachzehrer-Status -- werden korrekt und vollstaendig abgebildet. Es gibt zwei technische Fehler, die vor dem Datenbankimport korrigiert werden muessen, sowie zwei fachliche Hinweise mit niedrigem Schweregard. Der Plan ist importbereit nach Behebung der technischen Fehler.

---

## Pruefpunkt 1: Monokarp-Lebenszyklus

**Befund: BESTANDEN**

Der monokarpe Lebenszyklus ist vorbildlich abgebildet:

- `cycle_restart_from_sequence: null` korrekt gesetzt (Tabelle Zeile 25 und JSON Zeile 304).
- Alle vier Phaseneintraege tragen `is_recurring: false`.
- Die Beschreibung "Kindel = neue Pflanzeninstanz" ist fachlich praezise: im Kamerplanter-Datenmodell ist das die richtige Architektur (neue PlantInstance mit eigenem NutrientPlan ab GERMINATION W1).
- Verwendung von DORMANCY als Platzhalter fuer terminale Seneszenz ist pragmatisch korrekt, da das PhaseName-Enum kein SENESCENCE kennt. Die Begruendung im Dokument ist transparent.
- Die Phasen Kindel-Bildung und Seneszenz (Steckbrief Phasen 4+5) werden im Naehrstoffplan sinnvoll zu einer DORMANCY-Phase zusammengefasst -- der ernaehrungsphysiologische Unterschied zwischen Kindel-Bildung und terminaler Seneszenz rechtfertigt keine separate Phaseneinteilung, da in beiden Teilphasen keine Duengung erfolgt.

**Keine Korrekturen erforderlich.**

---

## Pruefpunkt 2: NPK und EC -- Plausibilitaet fuer epiphytische Bromelie

**Befund: BESTANDEN**

Die gewahlten Werte sind fachlich korrekt und angemessen konservativ:

- Dosierung 1 ml/L Gardol (1/4 der Herstellerdosis von 4 ml/L) ergibt geschaetzte EC ~0,06 mS/cm.
- Ziel-EC der Gesamtloesung 0,3 mS/cm ist plausibel fuer eine tropische Bromelie. Literaturwerte (Henny & Chen, IFAS; Griffith, BSI Journal) bestaetigen EC 0,2--0,5 mS/cm als sicheren Bereich.
- Zum Vergleich: Hydroponik-Salat (Schwachzehrer) benoetigt EC 1,2--2,0 mS/cm -- Guzmania liegt damit 4--10x darunter, was der naturlichen Naehrstoffarmut des Epiphyten-Lebensraums entspricht.
- NPK-Ziel 1:1:1 (vegetativ) und 1:2:1 (Bluete) sind biologisch korrekt. Die Diskrepanz zu Gardols tatsaechlichem Verhaeltnis 1,5:1:1,5 (N und K ueberschuessig, P unterdurchschnittlich) ist bei dieser Mikrodosis physiologisch irrelevant und wird im Plan korrekt erlaeutert.
- Iron (Fe) ist im Steckbrief mit 1 ppm angegeben (Vegetativ/Bluete), fehlt aber in den JSON-Phasendaten. Das Modell bietet das Feld `iron_ppm` (Zeile 105, nutrient_plan.py). Dies ist eine Informationsluecke, kein Fehler (Gardol enthaelt Spurenelemente, aber EC-Beitrag einzelner Elemente ist nicht deklariert).

**Keine Korrekturen erforderlich. Empfehlung: iron_ppm: 1.0 in VEGETATIVE und FLOWERING JSON erganzen (optional, sobald Spurenelement-Daten von Gardol bestaetigt).**

---

## Pruefpunkt 3: Trichterbewässerung -- Fachliche Korrektheit

**Befund: BESTANDEN mit einem Hinweis**

Die Trichterbewässerung (phytotelma-Prinzip) ist korrekt beschrieben:

- Drei Aufnahme-Routen korrekt identifiziert: Trichter (phytotelma), Trichome (Blattoberflaeche), Verankerungswurzeln (Substrat).
- Trichter-Volumen 50 ml (1/4 Fuellstand) fachlich korrekt. Ein zu voller Trichter beguestigt anaerobe Faulnisbedingungen; ein zu leerer Trichter reduziert die Naehrstoffaufnahme.
- Austauschhaeufigkeit 4--6 Wochen ist konservativ und sicher. Praxiserfahrung zeigt, dass viele Quellen 1--4 Wochen empfehlen; der Plan liegt am sicheren Ende der Spanne.
- Temperaturgrenze 18 C fuer Trichterwasser ist korrekt und als kritische Sicherheitsregel exponiert.
- Kalkempfindlichkeit der Trichome korrekt und ausfuehrlich erklaert (Saugschuppen, irreversibler Verstopfungsschaden).

**Hinweis H-001 (niedrige Prioritaet):** Die Empfehlung, bei Blattduengung (Channel blatternährung) die Loesung "fein zu spruehen", ist korrekt, aber ein praezisierender Hinweis zur Vermeidung stehender Tropfenbildung fehlt. Stehende Wasserreste auf den Blaettern koennen bei geringer Luftzirkulation zu Blattflecken (Helminthosporium) fuehren. Dieser Hinweis ist im Steckbrief (Abschnitt 5.2) dokumentiert, fehlt aber im entsprechenden Delivery-Channel-Notes-Feld des Plans.

---

## Pruefpunkt 4: Substrattyp ORCHID_BARK

**Befund: BESTANDEN**

- `recommended_substrate_type: "orchid_bark"` entspricht exakt dem Enum-Wert `SubstrateType.ORCHID_BARK = "orchid_bark"` in `src/backend/app/common/enums.py` (Zeile 81).
- Biologische Begruendung korrekt: Orchideenrinde bietet hohe Luftdurchlaessigkeit, geringe Wasserkapazitaet und saueres Milieu -- alle drei Eigenschaften sind fuer Bromelien als Epiphyten optimal.
- Alternative Substrate (Kokosfaser + Perlite) werden im Steckbrief und den Hinweistexten erwaehnt und sind ebenfalls fachlich korrekt.
- Der Unterschied zu normaler Blumenerde (zu dicht, Staunaesse) ist im Steckbrief klar begruendet.

**Keine Korrekturen erforderlich.**

---

## Pruefpunkt 5: RO-Wasser 100%-Pflicht

**Befund: BESTANDEN**

- `water_mix_ratio_ro_percent: 100` korrekt gesetzt.
- Der Kommentar in Zeile 24 erklaert praezise: Kalkablagerungen verstopfen Trichome irreversibel. Die Regel "Leitungswasser nur bei <5 dH akzeptabel" ist fachlich korrekt (5 deutsche Haertegrade entsprechen ca. 89 mg/L CaCO3, was als "weiches Wasser" gilt).
- Wichtige Praezisierung: Der Begriff "RO-Wasser" im Feld `water_mix_ratio_ro_percent` ist im Kamerplanter-System ein Proxy fuer "weiches Wasser" (Regenwasser, destilliertes Wasser, RO-Filterwasser). Das Dokument erklaert diesen Kontext korrekt.
- Der CalMag-Disclaimer ("kein CalMag-Supplement noetig -- Bromelien sind extreme Schwachzehrer") ist korrekt: Bei EC 0,3 mS/cm Gesamtloesung und den im Duenger enthaltenen Spurenmengen ist CalMag-Supplementierung kontraproduktiv.

**Keine Korrekturen erforderlich.**

---

## Pruefpunkt 6: Herzfaeule-Risiko

**Befund: BESTANDEN**

Das Herzfaeule-Risiko (Heart Rot, Trichterfaeule) ist umfassend dokumentiert:

- In Abschnitt 1.1 Giessplan-Hinweis (Zeile 38) als Inline-Warnung.
- In Abschnitt 3.1 Channel-Notes (Zeile 76) im primaren Delivery Channel.
- In Abschnitt 7 als dedizierter Sicherheitsabschnitt mit Symptomdiagnose und Heillosigkeit ("nicht heilbar").
- In den Notes aller relevanten Phaseneintraege (GERMINATION JSON Zeile 331, VEGETATIVE JSON Zeile 379).
- Im Steckbrief Abschnitt 5.2 als primaere Krankheit dokumentiert.
- Die Temperaturgrenze 18 C wird konsistent in allen relevanten Kontexten wiederholt.

**Hinweis zur Vollstaendigkeit:** Die Empfehlung, den Trichter im Winter "trocken oder minimal befuellt" zu halten (Abschnitt 7), deckt sich mit der Best Practice. Allerdings ist anzumerken, dass in der DORMANCY-Phase (W77--104) die Trichterstruktur der absterbenden Mutterpflanze ohnehin kollabiert -- der Risikofaktor Trichterfaeule betrifft in dieser Phase primaer die noch lebenden Kindel, die noch keinen voll entwickelten Trichter haben. Dieser Aspekt fehlt. Schweregard: niedrig.

---

## Pruefpunkt 7: Gardol als Ersatz fuer Orchideenduenger

**Befund: BESTANDEN**

Die Limitationen werden fair und vollstaendig kommuniziert:

- Abschnitt 4 (Zeile 140) explizit: "Ein Orchideenduenger (z.B. COMPO NPK 3-4-5) waere ideal -- Gardol auf 1/4-Dosis ist ein akzeptabler Ersatz, aber nicht die erste Wahl."
- Dieselbe Aussage ist in den VEGETATIVE-Notes des JSON (Zeile 372) enthalten -- konsistent.
- Das Produktdatenblatt gardol_gruenpflanzenduenger.md Abschnitt 8 bestaetigt tank_safe: false, was im Kontext der Bromelienpflege durch die Niedrigdosis-Strategie umgangen wird, aber korrekt bleibt.
- Die NPK-Mismatch-Analyse (6-4-6 vs. idealem Orchideen-NPK 3-4-5) ist fachlich korrekt: Bromelien benoetigen proportional mehr P relativ zu N, was Gardol bei der gegebenen Formulierung nicht optimal liefert. Bei 1/4-Dosis-Anwendung ist die absolute Differenz jedoch physiologisch tolerierbar.

**Fachlicher Hinweis H-002:** Das Produktdatenblatt nennt einen moeglichen organischen Stickstoffanteil (3% org. N von Gesamt 6% N, vgl. Abschnitt 2.1, Zeile 32). Falls dieser Harnstoff-Anteil tatsaechlich vorhanden ist, koennte er bei Trichteranwendung zu einer leichten pH-Verschiebung (Ammonisierung, pH-Anstieg auf >6,5) im Trichterwasser fuehren, was den praeferierten pH-Bereich 5,0--6,0 fuer Bromelien verlassen wuerde. Der Plan setzt Ziel-pH 5,5 an, prueft diesen Wert aber nicht gegen die Produktunsicherheit. Schweregrad: niedrig (da organischer N-Anteil nur in Community-Quellen belegt, nicht offiziell deklariert).

---

## Pruefpunkt 8: Lueckenlos-Pruefung (104 Wochen)

**Befund: BESTANDEN**

Die im Dokument enthaltene Eigenberechnung ist korrekt:

```
Phase         | week_start | week_end | Dauer (Wochen)
GERMINATION   |     1      |    8     |      8
VEGETATIVE    |     9      |   60     |     52
FLOWERING     |    61      |   76     |     16
DORMANCY      |    77      |   104    |     28
Gesamt:                               8+52+16+28 = 104
```

Keine Luecken (W8->W9 angrenzend, W60->W61 angrenzend, W76->W77 angrenzend).
Kein Ueberlapp.
Modelvalidierung bestaetigt: `week_end > week_start` fuer alle Eintraege (Validator Zeile 123--128, nutrient_plan.py).

Biologische Plausibilitaet der Phasendauern:
- GERMINATION 8 Wochen (56 Tage): Der Steckbrief gibt 30--60 Tage an. 56 Tage liegt am oberen Ende, ist aber korrekt -- frisch abgetrennte Kindel koennen bis zu 8 Wochen zur Wurzelbildung benoetigen, besonders bei suboptimalen Bedingungen.
- VEGETATIVE 52 Wochen (~1 Jahr): Der Steckbrief gibt 365--730 Tage (1--2 Jahre) an. 52 Wochen entsprechen der Untergrenze. Dies ist eine konservative Schaetzung und fuer einen Template-Plan sinnvoll.
- FLOWERING 16 Wochen (112 Tage): Der Steckbrief gibt 60--120 Tage an. 112 Tage entsprechen dem oberen Ende der Spanne und umfassen sowohl die Blueteinduktion als auch die sichtbare Bluetenstandphase. Akzeptabel.
- DORMANCY 28 Wochen (196 Tage): Der Steckbrief gibt Kindel-Bildung 90--180 Tage + Seneszenz 90--365 Tage. Das Zusammenfassen auf 28 Wochen deckt die untere Haelfte der Spanne ab. Plausibel fuer einen Standard-Template.

Gesamtlebenszyklus 104 Wochen = ~2 Jahre; Steckbrief gibt 2--3 Jahre an. Der Plan bildet das Minimum ab, was fuer einen Template-Plan sinnvoll ist (schnellste Biotyp-Variante).

**Keine Korrekturen erforderlich.**

---

## Pruefpunkt 9: Konsistenz Tabellen vs. JSON

### 9.1 Konsistente Felder (geprueft)

| Feld | Tabelle | JSON | Status |
|------|---------|------|--------|
| cycle_restart_from_sequence | null | null | OK |
| water_mix_ratio_ro_percent | 100 | 100 | OK |
| recommended_substrate_type | ORCHID_BARK | orchid_bark | OK |
| GERMINATION week_start/end | 1--8 | 1/8 | OK |
| VEGETATIVE week_start/end | 9--60 | 9/60 | OK |
| FLOWERING week_start/end | 61--76 | 61/76 | OK |
| DORMANCY week_start/end | 77--104 | 77/104 | OK |
| VEGETATIVE target_ec_ms | 0,3 | 0.3 | OK |
| FLOWERING target_ec_ms | 0,3 | 0.3 | OK |
| VEGETATIVE Gardol ml/L | 1,0 | 1.0 | OK |
| DORMANCY NPK | (0,0,0) | [0.0, 0.0, 0.0] | OK |
| DORMANCY interval_days | 14 Tage | 14 | OK |
| is_recurring | false (alle) | false (alle) | OK |

### 9.2 Gefundene Inkonsistenzen

**FEHLER F-001 (Kritisch -- Import blockiert): FoliarParams Feldname falsch**

Im JSON VEGETATIVE Delivery Channel "blatternaehrung" (Zeile 407--413) wird verwendet:

```json
"method_params": {
  "method": "foliar",
  "volume_per_feeding_liters": 0.02
}
```

Das Datenmodell `FoliarParams` in `src/backend/app/domain/models/nutrient_plan.py` Zeile 33--35 definiert:

```python
class FoliarParams(BaseModel):
    method: Literal["foliar"] = "foliar"
    volume_per_spray_liters: float = Field(default=0.5, gt=0, le=10)
```

Das korrekte Feld heisst `volume_per_spray_liters`, nicht `volume_per_feeding_liters`. `volume_per_feeding_liters` ist das Feld von `DrenchParams`. Der Pydantic-Discriminator wird den Wert ignorieren oder einen Validierungsfehler werfen. Dies betrifft nur den VEGETATIVE-Phaseneintrag (der einzige mit FOLIAR-Channel).

Korrekte Formulierung:
```json
"method_params": {
  "method": "foliar",
  "volume_per_spray_liters": 0.02
}
```

**FEHLER F-002 (Technisch -- Importwarnung): Channel-ID URL-Encoding in Tabellen**

In Abschnitt 3.2 Tabellen-Header (Zeile 90) und im Delivery-Channel-Hinweis der VEGETATIVE-Phase (Zeile 189) wird die Channel-ID als `blattern%C3%A4hrung` angegeben (URL-encoded). Im JSON selbst wird korrekt `blatternaehrung` (Zeile 396) und `blatternaehrung` (Zeile 18 des VEGETATIVE JSON) verwendet.

Das Datenmodell `DeliveryChannel.channel_id` hat `max_length=50` und erwartet einen String -- URL-Encoding ist kein gueltiger Bezeichner fuer dieses Feld. Die Tabelle ist inkorrekt; das JSON ist korrekt. Die Tabelle muss auf `blatternaehrung` korrigiert werden.

**INKONSISTENZ I-001 (Niedrig): GERMINATION JSON volume_per_feeding_liters**

Im JSON GERMINATION Delivery Channel "wasser-pur" (Zeile 351--353):

```json
"method_params": {
  "method": "drench",
  "volume_per_feeding_liters": 0.05
}
```

Das entspricht 50 ml. Die Tabelle 5.1 (Zeile 256) gibt fuer W1--8 "Substrat 30--50 ml" an. Der Notes-Text in Zeile 153 sagt "30-50 ml (kleines Kindel)".

50 ml ist das Maximum der empfohlenen Spanne -- das ist akzeptabel als Default, aber nicht optimal fuer ein frisch abgetrenntes Kindel in einem 8-cm-Topf. Der Wert sollte 0.03 bis 0.04 L betragen oder mit einem Hinweis versehen werden. Alternativ koennte die Spanne als Note dokumentiert werden, da das JSON-Feld einen Einzelwert erfordert.

---

## Pruefpunkt 10: Ethylen-Induktion -- Fachliche Praezision

**Befund: HINWEIS**

**Hinweis H-003 (Fachlich, niedrige Prioritaet):** Die Empfehlung zur Ethylen-Induktion ("reifer Apfel in Tuete mit Pflanze fuer 10 Tage", Zeile 210, FLOWERING Notes) ist grundsaetzlich korrekt, aber das Timing stimmt nicht mit dem Phasen-Mapping ueberein.

Die Ethylen-Behandlung ist eine Methode zur *Induktion* der Bluete, d.h. sie muss *vor* der FLOWERING-Phase angewendet werden -- idealerweise am Ende der VEGETATIVE-Phase (W55--60), wenn die Pflanze adult ist (12+ Blaetter). Im Naehrstoffplan ist die Empfehlung in den FLOWERING-Phase-Notes platziert, also zu einem Zeitpunkt, zu dem die Pflanze bereits blueht oder gerade zu bluehen beginnt.

Korrekte Platzierung: Die Ethylen-Empfehlung gehoert in die Notes der VEGETATIVE-Phase (W41--60 Abschnitt oder explizit W55--60 als Uebergangsempfehlung). Im Steckbrief Abschnitt 2.4 (Zeile 195) ist es korrekt dem Uebergang Vegetativ->Bluete zugeordnet ("Ethylen-Trick: reifer Apfel in Tuete mit Pflanze fuer 10 Tage kann Bluete ausloesen"). Der Naehrstoffplan ist hier inkonsistent mit dem Steckbrief.

---

## Zusammenfassung: Erforderliche Korrekturen

### Kritische Korrekturen (vor Import behoeben)

| ID | Typ | Ort | Beschreibung |
|----|-----|-----|--------------|
| F-001 | Feldfehler | JSON VEGETATIVE, method_params Foliar | `volume_per_feeding_liters` -> `volume_per_spray_liters` |
| F-002 | Bezeichner-Fehler | Tabellen Abschnitt 3.2 + VEGETATIVE Channel-Hinweis | `blattern%C3%A4hrung` -> `blatternaehrung` |

### Empfohlene Korrekturen (vor Veroffentlichung)

| ID | Typ | Ort | Beschreibung |
|----|-----|-----|--------------|
| I-001 | Inkonsistenz | GERMINATION JSON volume_per_feeding_liters | 0.05 L zu hoch fuer Kindel; 0.03 L empfohlen oder Note hinzufuegen |
| H-003 | Fachlich | FLOWERING Notes + VEGETATIVE Notes | Ethylen-Empfehlung aus FLOWERING in VEGETATIVE (W55-60) verschieben |

### Optionale Verbesserungen (backlog)

| ID | Typ | Beschreibung |
|----|-----|--------------|
| H-001 | Vollstaendigkeit | Blattduengung Channel-Notes: Hinweis auf Trockenheit der Blattflaeche nach Spruehung |
| H-002 | Datenqualitaet | Gardol org. N-Anteil (3%) gegenueber pH-Verhalten im Trichter klaeren, sobald Etikett verifiziert |
| OPT-1 | Datenvollstaendigkeit | iron_ppm: 1.0 in VEGETATIVE + FLOWERING ergaenzen (nach Spurenelement-Bestaetigung) |

---

## Fachliche Einzelbewertungen

### Biologische Korrektheit: bestaetigte Sachverhalte

Die folgenden fachlichen Aussagen wurden als korrekt bestaetigt:

1. **Epiphyten-Ernaehrung ueber Trichome:** Guzmania lingulata (und alle atmosphaerischen Bromelien) besitzen spezialisierte peltate Trichome (Saugschuppen) zur Absorption von Wasser und geloesten Naehrstoffen ueber die Blattoberflaeche. Diese Trichome verstopfen irreversibel durch CaCO3-Ablagerungen aus hartem Wasser. (Bestaetigt durch: Benzing 2000, "Bromeliaceae: Profile of an Adaptive Radiation")

2. **Schwachzehrer-Status epiphytischer Bromelien:** Natur-EC des Phytotelma-Wassers in tropischen Regenwaeldern liegt unter 0,1 mS/cm (Regenwater EC 0,01--0,05 mS/cm + geloesters organisches Material). Der Plan-EC von 0,3 mS/cm ist eine moderate Anreicherung, kein Ueberversorgungsrisiko. Vergleichsliteratur: Griffith (2004), "Growing Bromeliads", BSI.

3. **Monokarpie vs. Perennialitaet:** Die Aussage, dass das "Pflanzensystem durch Kindel-Bildung perennial ist" (Steckbrief Zeile 23), ist botanisch praezise. Die Mutterpflanze ist monokarp; die Art ist klonal perennial. Das Naehrstoffplan-Dokument setzt dies korrekt um (Kindel als neue Instanz mit neuem Zyklus).

4. **Trichterfaeule (Heart Rot) als haeufigste Todesursache:** Bestaetigt durch Clemson University Extension (hgic.clemson.edu) und Henny & Chen (IFAS Extension). Die anaerobe Faulnis im Trichter bei kuehlen Temperaturen wird durch Pythium-Arten und Erwinia-Bakterien verursacht.

5. **Photoperiodismus: Tagesneutral:** Guzmania lingulata ist eine tagneutrale Pflanze (Steckbrief Zeile 25). Die Bluete wird primaer durch Alter (12+ Blaetter, 2+ Jahre) ausgeloest, nicht durch Photoperiode. Ethylen kann als Induktor wirken. Dies ist korrekt abgebildet.

---

## Modell-Kompatibilitaetspruefung

| NutrientPlan-Feld | Wert im Dokument | Modell-Constraint | Status |
|-------------------|------------------|-------------------|--------|
| name (max 200) | "Guzmania lingulata -- Gardol Gruenpflanzenduenger" (50 Zeichen) | max_length=200 | OK |
| water_mix_ratio_ro_percent | 100 | ge=0, le=100 | OK |
| cycle_restart_from_sequence | null | Optional, ge=1 | OK |
| recommended_substrate_type | "orchid_bark" | SubstrateType.ORCHID_BARK | OK |
| is_template | true | bool | OK |
| version | "1.0" | str | OK |
| schedule_mode | "interval" | ScheduleMode.INTERVAL | OK |
| interval_days | 10 | ge=1, le=90 | OK |
| preferred_time | "09:00" | r"^([01]\d\|2[0-3]):[0-5]\d$" | OK |
| times_per_day | 1 | ge=1, le=6 | OK |
| week_start GERMINATION | 1 | ge=1 | OK |
| week_end GERMINATION | 8 | week_end > week_start: 8 > 1 | OK |
| week_start VEGETATIVE | 9 | ge=1 | OK |
| week_end VEGETATIVE | 60 | 60 > 9 | OK |
| week_start FLOWERING | 61 | ge=1 | OK |
| week_end FLOWERING | 76 | 76 > 61 | OK |
| week_start DORMANCY | 77 | ge=1 | OK |
| week_end DORMANCY | 104 | 104 > 77 | OK |
| target_ec_ms | 0.3 | ge=0, le=10 | OK |
| target_ph | 5.5 | ge=0, le=14 | OK |
| ml_per_liter | 1.0 | gt=0, le=50 | OK |
| ml_per_liter (foliar) | 0.5 | gt=0, le=50 | OK |
| volume_per_feeding_liters (drench) | 0.05, 0.10 | gt=0, le=100 | OK |
| volume_per_spray_liters (foliar) | 0.02 (als volume_per_feeding_liters deklariert) | **FELDNAME FALSCH (F-001)** | FEHLER |
| channel_id (max 50) | "trichter-duengung" (17), "blatternaehrung" (15), "wasser-pur" (9) | max_length=50 | OK |
| unique channel_ids pro Phase | alle Phasen: 1--2 Channels | Validator prueft Eindeutigkeit | OK |
| npk_ratio | [0,0,0] / [1,1,1] / [1,2,1] | non-negative floats | OK |
| calcium_ppm | null / 20.0 | Optional, ge=0 | OK |
| magnesium_ppm | null / 10.0 / 15.0 | Optional, ge=0 | OK |
| is_recurring (alle) | false | bool | OK |

---

## Empfohlene Korrekturen (Diff-Vorschlaege)

### Korrektur F-001: FoliarParams Feldname

In `/spec/knowledge/nutrient-plans/guzmania_gardol.md`, JSON VEGETATIVE, Delivery Channel "blatternaehrung":

Ersetze:
```json
"method_params": {
  "method": "foliar",
  "volume_per_feeding_liters": 0.02
}
```

Durch:
```json
"method_params": {
  "method": "foliar",
  "volume_per_spray_liters": 0.02
}
```

### Korrektur F-002: Channel-ID URL-Encoding in Tabellen

In `/spec/knowledge/nutrient-plans/guzmania_gardol.md`, Abschnitt 3.2 Tabellenzeile:

Ersetze:
```
| Channel-ID | blattern%C3%A4hrung | ...
```

Durch:
```
| Channel-ID | blatternaehrung | ...
```

Gleiches gilt fuer Zeile 189 (Delivery Channel VEGETATIVE Abschnitt):

Ersetze:
```
**Delivery Channel: blattern%C3%A4hrung (alternativ)**
```

Durch:
```
**Delivery Channel: blatternaehrung (alternativ)**
```

### Korrektur H-003: Ethylen-Empfehlung ins richtige Phasenfenster verschieben

In den VEGETATIVE-Phase-Notes (JSON) den folgenden Satz hinzufuegen:

```
"Ab W50 (Pflanze adult, 12+ Blaetter): Ethylen-Induktion moeglich — reifer Apfel fuer 10 Tage in versiegelter Tuete mit Pflanze um Bluetenbildung zu beschleunigen."
```

In den FLOWERING-Phase-Notes (JSON) den Ethylen-Satz entfernen oder ersetzen durch:

```
"Ethylen-Induktion: muss VOR Bluetenbeginn angewendet worden sein (Ende VEGETATIVE). Sobald Bluetenstand sichtbar, ist Induktion wirkungslos."
```

---

## Datenqualitaets-Notizen (Produktdaten)

Die folgenden Luecken stammen aus dem Gardol-Produktdatenblatt und koennen den Naehrstoffplan nicht praeziser machen, bis das physische Etikett verifiziert ist:

- `ec_contribution_per_ml` fehlt offiziell (Schaetzung 0,06 mS/cm im Plan). Ohne diesen Wert ist die EC-Kalibrierung nur naeherungsweise.
- `ph_effect` des Konzentrats unbekannt (im Modell PhEffect.NEUTRAL angenommen).
- Organischer N-Anteil (3%) aus Community-Quelle nicht offiziell bestaetigt.
- Spurenelement-Zusammensetzung (Fe, Mn, Zn, Cu, B) nicht deklariert.

Diese Luecken sind im Produktdatenblatt mit `<!-- ... -->` korrekt markiert und stellen keinen Fehler des Naehrstoffplans dar.

---

## Abschlussurteil

Der Naehrstoffplan `guzmania_gardol.md` ist **importbereit nach Behebung von F-001 und F-002**. Die biologische Fachkompetenz ist hoch; die kritischen Pflegeaspekte (Monokarpie, Trichterbewässerung, Herzfaeule, Kalkempfindlichkeit, Schwachzehrer-EC) sind vollstaendig und korrekt abgebildet. Die Limitationen des Ersatzprodukts Gardol werden transparent kommuniziert. Der Plan ist ein geeignetes Referenzdokument fuer die Kategorie "tropische Zimmer-Bromelien" im Kamerplanter-System.

**Status: FREIGEGEBEN fuer Import nach Behebung F-001 und F-002.**

---

*Dokumentversion: 1.0*
*Reviewer: Agrarbiologie-Experte (Subagent)*
*Erstellt: 2026-03-01*
