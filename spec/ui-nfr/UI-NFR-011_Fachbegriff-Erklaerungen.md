---
ID: UI-NFR-011
Titel: Kontextuelle Fachbegriff-Erklärungen — Pflicht-Tooltips und Glossar
Kategorie: Usability / Barrierefreiheit
Unterkategorie: Fachterminologie, Kontexthilfe, Onboarding
Fokus: Frontend
Technologie: React 18, TypeScript, MUI, react-i18next
Status: Entwurf
Priorität: Hoch
Version: 1.1
Tags: [ui, tooltips, glossar, fachbegriffe, usability, i18n, barrierefreiheit]
Abhängigkeiten: [NFR-010, REQ-021]
Betroffene Module: [Frontend]
---

# UI-NFR-011: Kontextuelle Fachbegriff-Erklärungen — Pflicht-Tooltips und Glossar

## Abgrenzung zu bestehenden NFRs

| Dokument | Fokus | Definiert |
|---|---|---|
| NFR-010 (UI-Vollständigkeit) | CRUD-Masken, helperText auf Feldern | **Was** pro Formularfeld angezeigt wird |
| REQ-021 (UI-Erfahrungsstufen) | Feld-Sichtbarkeit nach Erfahrungsstufe | **Welche** Felder sichtbar sind |
| **UI-NFR-011 (dieses Dokument)** | Fachbegriff-Erklärungen, Tooltip-System, Glossar | **Wie** Fachbegriffe im gesamten UI erklärt werden |

NFR-010 definiert `helperText` als kurzen Hilfetext unterhalb eines Formularfeldes. UI-NFR-011 geht darüber hinaus: Jeder Fachbegriff im gesamten UI — in Formularen, Tabellenspalten, Chips, Dashboards und Kalkulatoren — **MUSS** kontextuell erklärt werden. Die Erklärungen sind mehrstufig (Kurztext, Langtext, Einsteiger-Tipp) und über ein zentrales Glossar verwaltet.

---

## 1. Business Case

### 1.1 User Stories

**Als** Hobby-Gärtner ohne Fachwissen
**möchte ich** bei jedem Fachbegriff im System (VPD, EC, PPFD, NPK, etc.) auf einen Blick eine verständliche Erklärung sehen
**um** das System nutzen zu können, ohne vorher ein Agrarbuch lesen zu müssen.

**Als** fortgeschrittener Nutzer
**möchte ich** die Tooltips dezent sehen (nur Icon, kein automatischer Popup)
**um** nicht bei jedem bekannten Begriff unterbrochen zu werden.

**Als** Entwickler
**möchte ich** eine zentrale, wiederverwendbare Glossar-Datenstruktur
**um** Fachbegriff-Erklärungen konsistent über alle Seiten hinweg pflegen zu können, ohne sie in jeder Komponente einzeln zu definieren.

**Als** Übersetzer/Redakteur
**möchte ich** alle Fachbegriff-Erklärungen an einer zentralen Stelle (i18n-Datei) pflegen
**um** Konsistenz zwischen Sprachen sicherzustellen.

### 1.2 Geschäftliche Motivation

Die UI-Analyse (test-reports/ui-hobby-gardener-analysis.md) identifiziert **16 unerklärte Fachbegriffe** im aktuellen UI. Für einen Einsteiger, der "meine Basilikum-Pflanze eintragen" möchte, stellen diese eine unüberwindbare Hürde dar:

| Fachbegriff | Was ein Einsteiger versteht | Realität |
|-------------|----------------------------|----------|
| VPD (kPa) | Nichts | Dampfdruckdefizit — zentrale Klimametrik |
| EC (mS/cm) | Nichts | Elektrische Leitfähigkeit — Nährstoffkonzentration |
| PPFD (µmol/m²/s) | Nichts | Lichtintensität für Pflanzen |
| NPK-Ratio | Vielleicht "Dünger-Zahlen" | Stickstoff-Phosphor-Kalium-Verhältnis |
| Allelopathie | Nichts | Biochemische Pflanzenwechselwirkung |
| GDD | Nichts | Akkumulierte Wärmeeinheiten |
| DLI | Nichts | Tageslichtsumme |
| Vernalisation | Nichts | Kältereiz für Blütenbildung |

Ohne Erklärungen verliert das System seine größte potenzielle Zielgruppe (Hobby-Gärtner, Einsteiger, Bildung).

---

## 2. Pflicht-Anforderung: Jeder Fachbegriff wird erklärt

### 2.1 Definition "Fachbegriff"

Ein Fachbegriff im Sinne dieser NFR ist jedes Wort oder jede Abkürzung im UI, das/die **nicht zum allgemeinen Sprachgebrauch** gehört und **domänenspezifisches Wissen** voraussetzt.

**Pflicht-Erklärung (MUSS):**
- Alle Abkürzungen: VPD, EC, PPFD, DLI, GDD, NPK, CEC, IPM, PPFD, DO, rH
- Alle Messeinheiten mit domänenspezifischer Bedeutung: kPa, mS/cm, µmol/m²/s, mol/m²/d, meq/100g
- Alle fachspezifischen Enum-Werte: Allelopathie-Score, Vernalisation, Seneszenz, Dormanz, Photoperiodismus, Hardiness Zones
- Alle anbautechnischen Begriffe: Flushing, Runoff, CalMag, Mixing Priority, Starkzehrer/Mittelzehrer/Schwachzehrer
- Alle biologischen Fachbegriffe: Epiphyt, Lithophyt, Geophyt, Binomialnomenklatur

**Empfohlene Erklärung (SOLL):**
- Fachbegriffe in Enum-Labels: `trap_crop`, `companion`, `monoculture`, `clone_run`
- Feldnamen mit nicht-offensichtlicher Bedeutung: `base_temp`, `air_porosity_percent`, `bulk_density_g_per_l`
- Status-Begriffe: `vegetative`, `flowering`, `senescence`, `dormancy`

### 2.2 Wo Erklärungen erscheinen MÜSSEN

| UI-Element | Erklärungsform | Pflicht |
|-----------|---------------|---------|
| Formular-Feldlabel | Info-Icon (?) mit Tooltip | **MUSS** für jeden Fachbegriff |
| Tabellenspalten-Header | Info-Icon (?) mit Tooltip | **MUSS** für Fachbegriff-Spalten |
| Status-Chips / Badges | Tooltip bei Hover | **MUSS** für fachspezifische Status |
| Dashboard-Widgets | Info-Icon im Widget-Header | **MUSS** für Fachmetrik-Widgets |
| Kalkulator-Eingabefelder | Info-Icon (?) mit Tooltip + helperText | **MUSS** |
| Kalkulator-Ergebnisse | Inline-Erklärung unter dem Wert | **SOLL** |
| Dropdown-/Select-Optionen | Tooltip bei Hover auf Option | **SOLL** |
| Fehlermeldungen mit Fachbegriffen | Fachbegriff im Fehlertext verlinkt | **SOLL** |

---

## 3. Glossar-Datenstruktur

### 3.1 Mehrstufiges Erklärungsmodell

Jeder Glossareintrag hat drei Erklärungsebenen, die je nach Kontext und Erfahrungsstufe (REQ-021) angezeigt werden:

```typescript
interface GlossaryEntry {
  /** Eindeutiger Schlüssel (lowercase, snake_case) */
  term: string;
  /** Kurze Erklärung in Alltagssprache (max. 80 Zeichen) — für Tooltips */
  short: string;
  /** Ausführliche Erklärung mit Kontext (max. 300 Zeichen) — für erweiterte Tooltips */
  long: string;
  /** Einsteiger-Tipp: praxisnaher Hinweis (max. 200 Zeichen) — nur im beginner-Modus */
  beginnerTip?: string;
  /** Maßeinheit (falls zutreffend) */
  unit?: string;
  /** Typischer Wertebereich (falls zutreffend) */
  typicalRange?: string;
  /** Kategorie für Glossar-Seite */
  category: 'klima' | 'licht' | 'naehrstoffe' | 'substrat' | 'wachstum' | 'pflanzenschutz' | 'taxonomie' | 'allgemein';
  /** Verwandte Begriffe (Querverweise im Glossar) */
  relatedTerms?: string[];
}
```

### 3.2 Verwaltung über i18n

Alle Erklärungen werden als i18n-Schlüssel verwaltet (nicht hardcoded):

```
glossary.<term>.short
glossary.<term>.long
glossary.<term>.beginnerTip
glossary.<term>.unit
glossary.<term>.typicalRange
```

Beispiel (`de.json`):
```json
{
  "glossary": {
    "vpd": {
      "short": "Dampfdruckdefizit — wie „durstig" die Luft ist",
      "long": "Das VPD misst, wie stark die Luft Feuchtigkeit aufnehmen kann. Hoher VPD = trockene Luft = Pflanze verdunstet mehr. Optimale Werte sind artabhängig: Tropische Pflanzen mögen 0,4–0,8 kPa, Nutzpflanzen im Wachstum 0,8–1,2 kPa, Kakteen tolerieren über 1,5 kPa. Zu hoch: Blätter welken. Zu niedrig: Schimmelgefahr.",
      "beginnerTip": "Im Zimmer normalerweise kein Problem. Nur bei geschlossenen Growzelten relevant.",
      "unit": "kPa (Kilopascal)",
      "typicalRange": "0,4–1,6 kPa (artabhängig)"
    },
    "ec": {
      "short": "Leitfähigkeit — wie viel Dünger im Wasser ist",
      "long": "EC misst die Nährstoffkonzentration im Gießwasser. Gesamt-EC = Leitungswasser-EC + Dünger-EC. Deutsches Leitungswasser hat ca. 0,3–0,8 mS/cm. Für Topfpflanzen Gesamt-EC 1,0–2,0 mS/cm anstreben. Hydroponik präziser: Netto-EC (nur Dünger) nach Pflanzenart einstellen.",
      "beginnerTip": "Ohne EC-Messgerät: Halte dich an die Dosierungsempfehlung auf der Dünger-Flasche. Lieber etwas weniger als zu viel.",
      "unit": "mS/cm (Millisiemens pro Zentimeter)",
      "typicalRange": "0,5–3,5 mS/cm"
    },
    "ppfd": {
      "short": "Lichtmenge für Pflanzen — wie hell es wirklich ist",
      "long": "PPFD misst die Lichtintensität, die Pflanzen tatsächlich nutzen können. Anders als Lux (für menschliche Augen) erfasst PPFD nur das pflanzenrelevante Lichtspektrum.",
      "beginnerTip": "Faustregel: Südfenster mit Direktsonne im Sommer ≈ 200–400 (wenige Stunden). Ost-/Westfenster: 100–200. Nordfenster: unter 50. Für Tomaten und Chili oft zu wenig — Growlampe empfehlenswert.",
      "unit": "µmol/m²/s",
      "typicalRange": "100–1500 µmol/m²/s"
    },
    "npk": {
      "short": "Stickstoff-Phosphor-Kalium — die drei Hauptnährstoffe",
      "long": "Die drei Zahlen auf jeder Düngerflasche: N (Stickstoff, für Blattwachstum), P (Phosphor, für Wurzeln und Blüten), K (Kalium, für Fruchtbildung und Widerstandskraft).",
      "beginnerTip": "Für Anfänger reicht ein Universaldünger — die NPK-Werte stehen auf der Flasche."
    },
    "gdd": {
      "short": "Wachstumsgradtage — akkumulierte Wärme seit dem Pflanzen",
      "long": "GDD misst, wie viel verwertbare Wärme eine Pflanze seit dem Start erhalten hat. Jeder Tag über einer Basistemperatur (z.B. 10°C) trägt Gradtage bei. Tomaten brauchen ca. 1000–1500 GDD bis zur Ernte.",
      "beginnerTip": "Musst du nicht selbst berechnen — das System trackt das automatisch."
    },
    "dli": {
      "short": "Tageslichtmenge — wie viel Licht pro Tag",
      "long": "DLI fasst die gesamte Lichtmenge eines Tages zusammen. Wichtig für die Lichtplanung: Kräuter brauchen 12–20, Tomaten 20–40 mol/m²/d.",
      "beginnerTip": "Sonnige Fensterbank im Sommer ≈ 10–15 mol/m²/d. Im Winter nur 3–5.",
      "unit": "mol/m²/d",
      "typicalRange": "5–40 mol/m²/d"
    },
    "allelopathie": {
      "short": "Biochemische Wechselwirkung zwischen Pflanzenarten",
      "long": "Manche Pflanzen hemmen oder fördern das Wachstum benachbarter Pflanzen durch chemische Stoffe im Boden oder in der Luft. Beispiel: Walnussbäume hemmen Tomaten.",
      "beginnerTip": "Relevanter Effekt erst bei Mischkultur. Bei Einzelpflanzen auf der Fensterbank unwichtig."
    },
    "vernalisation": {
      "short": "Kältereiz — eine Pflanze braucht Kälte, um zu blühen",
      "long": "Zweijährige Pflanzen (z.B. Petersilie, Kohl, Sellerie) und Wintergetreide brauchen mehrere Wochen Kälte (0–7°C), bevor sie im Frühling Blüten bilden können. Obstbäume brauchen ähnlich eine Kälteperiode (Chill-Hours), um die Knospenruhe zu brechen.",
      "beginnerTip": "Betrifft v.a. Petersilie und Kohl im zweiten Jahr. Die meisten Zimmerpflanzen und einjährige Gemüse brauchen das nicht."
    },
    "dormanz": {
      "short": "Winterruhe — die Pflanze macht Pause",
      "long": "Viele mehrjährige Pflanzen reduzieren im Winter ihr Wachstum auf ein Minimum. In dieser Phase brauchen sie weniger Wasser, keinen Dünger und kühlere Temperaturen.",
      "beginnerTip": "Kakteen und Sukkulenten brauchen eine kühle Winterruhe (10–15°C, kaum gießen). Tropische Zimmerpflanzen haben keine echte Dormanz, wachsen aber im Winter langsamer wegen weniger Licht — dann weniger gießen und nicht düngen."
    },
    "seneszenz": {
      "short": "Alterungsphase — die Pflanze stirbt natürlich ab",
      "long": "Natürlicher Alterungsprozess am Ende des Lebenszyklus. Bei einjährigen Pflanzen nach der Samenreife, bei Stauden als herbstlicher Blattabwurf.",
      "beginnerTip": "Gelbe Blätter an Tomaten im Herbst sind normal — die Pflanze ist am Lebensende."
    },
    "photoperiodismus": {
      "short": "Reaktion der Pflanze auf die Tageslänge",
      "long": "Manche Pflanzen blühen nur bei bestimmten Tageslängen. Kurztagspflanzen (z.B. Cannabis, Weihnachtsstern) brauchen eine ununterbrochene Dunkelperiode über einer kritischen Schwelle (oft 12–14h). Selbst kurze Lichtunterbrechungen in der Nacht können die Blüte verhindern. Langtagspflanzen (z.B. Spinat) brauchen >14h Licht.",
      "beginnerTip": "Wichtig bei Cannabis-Anbau (Blüte durch 12/12 Lichtumstellung). Achtung: Kein Licht während der Dunkelphase!"
    },
    "hardiness_zones": {
      "short": "Winterhärtezonen — wie viel Frost hält die Pflanze aus?",
      "long": "USDA-System mit Zonen 1–13. Deutschland liegt in Zone 6–8. Eine Pflanze in Zone 7 übersteht Temperaturen bis ca. -15°C.",
      "beginnerTip": "Nur relevant für Outdoor-Pflanzen und Überwinterung. Für reine Zimmerpflanzen unwichtig."
    },
    "flushing": {
      "short": "Substrat durchspülen — Salzreste auswaschen",
      "long": "Vor der Ernte wird das Substrat mit klarem Wasser gespült, um Düngerreste auszuwaschen. Verbessert Geschmack und Qualität, besonders bei Kräutern und Cannabis.",
      "beginnerTip": "Einfach 1 Woche vor der Ernte nur noch mit klarem Wasser gießen."
    },
    "runoff": {
      "short": "Ablaufwasser — was unten aus dem Topf herauskommt",
      "long": "Die Analyse des Ablaufwassers (EC und pH) zeigt, ob die Pflanze die Nährstoffe aufnimmt oder ob sich Salze im Substrat anreichern.",
      "beginnerTip": "Für Fensterbank-Pflanzen nicht nötig. Erst bei Hydroponik oder intensiver Düngung relevant."
    },
    "calmag": {
      "short": "Calcium-Magnesium-Ergänzung zum Basisdünger",
      "long": "Weiches Wasser enthält wenig Calcium und Magnesium. CalMag gleicht das aus und wird IMMER VOR dem Basisdünger ins Wasser gegeben (Reihenfolge wichtig!).",
      "beginnerTip": "Nur bei Hydroponik oder sehr weichem Wasser nötig. Die meisten Leitungswässer haben genug."
    },
    "cec": {
      "short": "Speicherkapazität — wie viel Nährstoffe das Substrat halten kann",
      "long": "CEC (Kationenaustauschkapazität) misst, wie gut ein Substrat Nährstoffe binden und wieder abgeben kann. Hohe CEC = länger düngewirksam. Blähton ≈ 2–5, Kokos ≈ 40–100, Erde ≈ 100–200 meq/100g.",
      "beginnerTip": "Gute Blumenerde hat eine hohe CEC — du musst seltener düngen."
    },
    "ipm": {
      "short": "Integrierter Pflanzenschutz — Vorbeugung vor Chemie",
      "long": "Dreistufiger Ansatz: 1) Vorbeugen (gesunde Pflanzen, Hygiene), 2) Beobachten (regelmäßig kontrollieren), 3) Eingreifen (Nützlinge vor Spritzmitteln).",
      "beginnerTip": "Gesunde Pflanzen werden seltener krank. Regelmäßig nach Schädlingen schauen reicht für den Anfang."
    },
    "lux_vs_ppfd": {
      "short": "Lux = für menschliche Augen, PPFD = für Pflanzen",
      "long": "Lux misst die Helligkeit für das menschliche Auge und gewichtet Grünlicht am stärksten. Pflanzen nutzen vor allem Rot- und Blaulicht. Eine Natriumdampflampe und eine LED können identische Lux-Werte haben, aber völlig unterschiedliche PPFD-Werte liefern. Faustformel für weißes LED-Licht: PPFD ≈ Lux / 70.",
      "beginnerTip": "Smartphone-Lux-Apps geben nur einen groben Anhaltspunkt. Für präzise Pflanzenbeleuchtung ist ein PPFD-Messgerät nötig — oder verlass dich auf die Herstellerangaben deiner Growlampe."
    },
    "substrat": {
      "short": "Das Material, in dem die Pflanze wurzelt",
      "long": "Substrat ist der Oberbegriff für alles, worin Pflanzen wachsen: Blumenerde, Kokos, Perlite, Blähton, Steinwolle. Verschiedene Substrate speichern Wasser und Nährstoffe unterschiedlich gut.",
      "beginnerTip": "Für die meisten Zimmerpflanzen reicht normale Blumenerde. Kakteen brauchen durchlässigere Erde (Kakteenerde).",
      "category": "substrat"
    },
    "cultivar_sorte": {
      "short": "Eine gezüchtete Sorte innerhalb einer Pflanzenart",
      "long": "Ein Cultivar (= Sorte) ist eine vom Menschen gezüchtete Variante einer Art. Beispiel: 'Tiny Tim' ist ein Cultivar von Solanum lycopersicum (Tomate). Cultivars haben spezifische Eigenschaften wie Fruchtgröße, Farbe oder Wuchsform.",
      "beginnerTip": "Beim Samenkauf steht die Sorte meist auf der Tüte — z.B. 'Cherry-Tomate Tiny Tim'.",
      "category": "taxonomie"
    },
    "standort_location_slot": {
      "short": "Drei-Ebenen-System: Standort → Bereich → Stellplatz",
      "long": "Standort = der Gesamtort (z.B. 'Meine Wohnung'). Location = ein Bereich am Standort (z.B. 'Fensterbank Süd'). Slot = ein einzelner Stellplatz für eine Pflanze innerhalb einer Location.",
      "beginnerTip": "Für den Anfang reicht ein Standort mit einer Location. Slots brauchst du nur bei vielen Pflanzen.",
      "category": "allgemein"
    },
    "pflanzdurchlauf": {
      "short": "Eine Gruppe von Pflanzen, die zusammen angebaut werden",
      "long": "Ein Pflanzdurchlauf (PlantingRun) fasst Pflanzen zusammen, die zur gleichen Zeit am gleichen Ort angebaut werden. Beispiel: '5 Tomaten auf dem Balkon, Sommer 2026'.",
      "beginnerTip": "Stell dir einen Durchlauf wie ein Projekt vor: Alle Pflanzen, die du zusammen betreust.",
      "category": "allgemein"
    },
    "mischkultur": {
      "short": "Verschiedene Pflanzenarten zusammen anbauen",
      "long": "Mischkultur (Companion Planting) nutzt positive Wechselwirkungen zwischen Pflanzenarten. Klassiker: Tomaten + Basilikum (Basilikum hält Schädlinge fern). Manche Kombinationen schaden sich gegenseitig.",
      "beginnerTip": "Tomate + Basilikum ist ein guter Start. Tomate + Fenchel vermeiden.",
      "category": "wachstum"
    },
    "fruchtfolge": {
      "short": "Jedes Jahr andere Pflanzen am selben Platz anbauen",
      "long": "Fruchtfolge (Crop Rotation) bedeutet, dass auf einer Fläche jährlich die Pflanzenfamilie wechselt. Das beugt Bodenmüdigkeit und Krankheiten vor. Faustregel: Gleiche Familie frühestens nach 3 Jahren am selben Platz.",
      "beginnerTip": "Ab dem zweiten Gartenjahr relevant. Tomaten nicht dort pflanzen, wo letztes Jahr Tomaten oder Kartoffeln standen.",
      "category": "wachstum"
    },
    "ph_wert": {
      "short": "Säuregrad des Bodens oder Gießwassers",
      "long": "Der pH-Wert gibt an, wie sauer oder basisch ein Medium ist. Skala 0–14: unter 7 = sauer, 7 = neutral, über 7 = basisch. Die meisten Pflanzen mögen leicht sauren bis neutralen Boden (pH 5,5–7,0). Heidelbeeren brauchen sauren Boden (pH 4,0–5,0).",
      "beginnerTip": "Normale Blumenerde hat meist den richtigen pH-Wert. Erst bei Problemen (gelbe Blätter trotz Düngung) den pH prüfen.",
      "category": "substrat"
    },
    "staunaesse": {
      "short": "Zu viel Wasser im Topf — Wurzeln ertrinken",
      "long": "Staunässe entsteht, wenn überschüssiges Gießwasser nicht abfließen kann. Die Wurzeln bekommen keinen Sauerstoff und faulen. Häufigste Ursache für Pflanzentod bei Zimmerpflanzen.",
      "beginnerTip": "Immer Töpfe mit Abzugsloch verwenden. Überschüssiges Wasser aus dem Untersetzer nach 30 Minuten wegkippen.",
      "category": "allgemein"
    },
    "drainage": {
      "short": "System zum Abführen von überschüssigem Wasser",
      "long": "Drainage sorgt dafür, dass Gießwasser durch das Substrat abfließen kann. Besteht aus: Abzugsloch im Topf + durchlässiges Substrat + optional Blähton-Schicht am Topfboden.",
      "beginnerTip": "Loch im Topf = wichtigste Drainage. Ohne Loch besteht Staunässe-Gefahr.",
      "category": "substrat"
    },
    "umtopfen": {
      "short": "Pflanze in einen größeren Topf mit frischer Erde setzen",
      "long": "Umtopfen ist nötig, wenn die Wurzeln den Topf komplett ausfüllen (Wurzeln wachsen aus dem Abzugsloch). Beste Zeit: Frühling. Neuer Topf sollte 2–4 cm größer sein als der alte.",
      "beginnerTip": "Zeichen zum Umtopfen: Wurzeln wachsen unten raus, Wasser läuft sofort durch, Pflanze wächst nicht mehr.",
      "category": "allgemein"
    },
    "dif": {
      "short": "Temperatur-Unterschied zwischen Tag und Nacht",
      "long": "DIF beschreibt die Differenz zwischen Tag- und Nachttemperatur. Positiver DIF (Tag wärmer als Nacht) fördert Streckungswachstum. Negativer DIF (Nacht wärmer) hält Pflanzen kompakt. In professionellen Gewächshäusern wird DIF gezielt zur Wuchssteuerung eingesetzt.",
      "beginnerTip": "Für Zimmerpflanzen: Nachts darf es 3–5°C kühler sein als tagsüber — das ist natürlich und gut für die Pflanze.",
      "category": "klima"
    },
    "hysterese": {
      "short": "Schaltschwellen-Abstand, der Gerätependeln verhindert",
      "long": "Hysterese bedeutet, dass ein Gerät bei einem höheren Wert einschaltet als es ausschaltet. Beispiel: Befeuchter AN bei 50% rH, AUS erst bei 60% rH. Ohne Hysterese würde das Gerät im Sekundentakt ein- und ausschalten.",
      "beginnerTip": "Wird automatisch vom System gesteuert. Nur relevant, wenn du eigene Automatisierungsregeln erstellst.",
      "category": "klima"
    },
    "mixing_priority": {
      "short": "Reihenfolge, in der Dünger ins Wasser gerührt wird",
      "long": "Beim Anmischen einer Nährlösung ist die Reihenfolge wichtig: Erst CalMag, dann Basisdünger, zuletzt Additive. Falsche Reihenfolge kann zu Ausfällungen führen (sichtbar als Trübung oder Bodensatz).",
      "beginnerTip": "Nur bei Hydroponik relevant. Bei Flüssigdünger für Zimmerpflanzen einfach ins Wasser geben.",
      "category": "naehrstoffe"
    }
  }
}
```

### 3.3 Mindest-Glossarumfang

Das System **MUSS** beim Release mindestens folgende Fachbegriffe in DE und EN erklären:

| Kategorie | Pflicht-Begriffe (MUSS) | Anzahl |
|-----------|------------------------|--------|
| Klima | VPD, rH, DIF, Hysterese | 4 |
| Licht | PPFD, DLI, Photoperiodismus, Lux vs. PPFD | 4 |
| Nährstoffe | EC, NPK, CalMag, Flushing, Runoff, Mixing Priority, Starkzehrer/Mittelzehrer/Schwachzehrer | 7 |
| Substrat | CEC, pH, Drainage, Air Porosity, Substrat, Staunässe | 6 |
| Wachstum | GDD, Vernalisation, Dormanz, Seneszenz, Allelopathie, Mischkultur, Fruchtfolge | 7 |
| Pflanzenschutz | IPM, Karenzzeit, Nützlinge | 3 |
| Taxonomie | Binomialnomenklatur, Cultivar vs. Varietät, Hardiness Zones | 3 |
| Allgemein | Standort/Location/Slot, Pflanzdurchlauf, Umtopfen, pH-Wert | 4 |
| **Gesamt** | | **38** |

Darüber hinaus **SOLL** das System weitere Begriffe erklären, darunter: Perlite/Vermiculite, Vollspektrum-Licht, Überwinterung, Abhärtung/Hardening Off, Steckling/Cutting, Wurzelballen.

---

## 4. Shared Component: HelpTooltip

### 4.1 Spezifikation

```typescript
interface HelpTooltipProps {
  /** Glossar-Schlüssel (z.B. "vpd", "ec", "npk") */
  term: string;
  /** Kind-Element, neben dem das Info-Icon erscheint */
  children: React.ReactNode;
  /** Tooltip-Platzierung (Default: "top") */
  placement?: 'top' | 'bottom' | 'left' | 'right';
  /** Nur Icon ohne Kinder anzeigen (für Standalone-Nutzung in Tabellen-Headern) */
  iconOnly?: boolean;
}
```

### 4.2 Darstellungsregeln

| Erfahrungsstufe (REQ-021) | Darstellungsverhalten |
|---------------------------|----------------------|
| `beginner` | Info-Icon (?) prominent (16px, farbig). Tooltip zeigt `short` + `beginnerTip`. Auto-Open beim ersten Besuch einer Seite (einmalig). |
| `intermediate` | Info-Icon (?) dezent (14px, grau). Tooltip zeigt `short` + `long` bei Hover. |
| `expert` | Info-Icon (?) minimal (12px, light grey). Tooltip zeigt `short` bei Hover. Kein Auto-Open. |

### 4.3 Tooltip-Inhalt

Der Tooltip zeigt je nach Konfiguration:

```
┌──────────────────────────────────────────┐
│ 💡 Dampfdruckdefizit — wie „durstig"     │
│    die Luft ist                           │  ← short
│                                          │
│ Das VPD misst, wie stark die Luft        │
│ Feuchtigkeit aufnehmen kann. [...]       │  ← long (intermediate/expert)
│                                          │
│ 🌱 Im Zimmer normalerweise kein Problem. │  ← beginnerTip (nur beginner)
│    Nur bei geschlossenen Growzelten.     │
│                                          │
│ Einheit: kPa · Typisch: 0,4–1,6 kPa    │  ← unit + typicalRange
│                                          │
│ 📖 Im Glossar öffnen                     │  ← Link zur Glossar-Seite
└──────────────────────────────────────────┘
```

### 4.4 Interaktionsverhalten

- **Desktop:** Tooltip öffnet bei Hover (300ms Delay), bleibt offen solange Maus über Tooltip oder Icon
- **Mobile/Touch:** Tooltip öffnet bei Tap auf Info-Icon, schließt bei Tap außerhalb
- **Tastatur:** Fokussierbar via Tab, Tooltip öffnet bei Enter/Space (a11y-konform, WCAG 2.1 Level AA)
- **Glossar-Link:** Klick auf "Im Glossar öffnen" navigiert zur Glossar-Seite mit gescrolltem Anker

---

## 5. Glossar-Seite

### 5.1 Route

`/glossar` (DE) / `/glossary` (EN)

### 5.2 Funktionalität

- Alphabetisch sortierte Liste aller Glossareinträge
- **Suchfeld** (Echtzeit-Filter, durchsucht `term`, `short`, `long`)
- **Kategorie-Filter** (Tabs oder Chips: Klima, Licht, Nährstoffe, Substrat, Wachstum, Pflanzenschutz, Taxonomie, Alle)
- Jeder Eintrag zeigt: Begriff, Kurztext, Langtext, ggf. Einheit + Wertebereich
- **Anker-Links** (z.B. `/glossar#vpd`) für direkte Verlinkung aus Tooltips
- **Verwandte Begriffe** als klickbare Querverweise (z.B. VPD → rH, Temperatur)
- i18n-fähig (DE/EN)

### 5.3 Responsive Design

| Breakpoint | Layout |
|-----------|--------|
| `>= 1024px` | 2-Spalten-Layout (Kategorie-Filter links, Begriffsliste rechts) |
| `< 1024px` | 1-Spalte, Kategorie als horizontale Chip-Leiste oben |

---

## 6. Prüfregeln für Code-Reviews

### 6.1 Pflicht-Check bei jedem neuen Formularfeld

Wenn ein Formularfeld mit einem Fachbegriff als Label hinzugefügt wird, **MUSS** es mit einer `HelpTooltip`-Komponente umschlossen sein. Ein Formularfeld ohne `HelpTooltip` für einen Fachbegriff ist ein Review-Blocker.

```tsx
// ❌ FALSCH — Fachbegriff ohne Erklärung
<TextField label="VPD (kPa)" />

// ✅ KORREKT — Fachbegriff mit Tooltip
<HelpTooltip term="vpd">
  <TextField label="VPD (kPa)" />
</HelpTooltip>
```

### 6.2 Pflicht-Check bei jeder neuen Tabellenspalte

```tsx
// ❌ FALSCH — Fachbegriff-Spalte ohne Erklärung
<DataTable columns={[{ field: 'ec', headerName: 'EC (mS/cm)' }]} />

// ✅ KORREKT — Fachbegriff-Spalte mit Tooltip im Header
<DataTable columns={[{
  field: 'ec',
  renderHeader: () => (
    <HelpTooltip term="ec" iconOnly>EC (mS/cm)</HelpTooltip>
  )
}]} />
```

### 6.3 Pflicht-Check bei neuem Glossareintrag

Jeder neue Glossareintrag **MUSS** mindestens `short` und `long` in DE und EN haben. `beginnerTip` ist **SOLL** für alle Begriffe der Kategorie Nährstoffe, Klima und Licht.

---

## 7. Akzeptanzkriterien

### Funktional:
- [ ] Mindestens 38 Fachbegriffe mit `short` und `long`-Erklärung in DE und EN vorhanden
- [ ] `HelpTooltip`-Komponente ist als Shared Component unter `src/frontend/src/components/shared/` verfügbar
- [ ] Info-Icon (?) neben **allen** Feldern mit Fachbegriffen in Create-/Edit-Dialogen
- [ ] Info-Icon (?) in **allen** Tabellenspalten-Headern mit Fachbegriffen
- [ ] Glossar-Seite existiert als eigenständige Route (`/glossar` bzw. `/glossary`)
- [ ] Glossar ist durchsuchbar (Echtzeit-Filter)
- [ ] Glossar ist nach Kategorien filterbar
- [ ] Jeder Tooltip enthält einen Link zur Glossar-Seite
- [ ] Tooltip-Darstellung passt sich an Erfahrungsstufe an (REQ-021)
- [ ] Im Einsteiger-Modus zeigt der Tooltip `beginnerTip` an (falls vorhanden)
- [ ] Im Experten-Modus ist das Info-Icon dezent (kleiner, heller)

### Technisch:
- [ ] Alle Glossareinträge als i18n-Schlüssel verwaltet (`glossary.<term>.*`)
- [ ] Glossar-Daten werden beim App-Start einmalig geladen (kein erneuter Fetch pro Tooltip)
- [ ] Tooltip ist a11y-konform (WCAG 2.1 Level AA): fokussierbar, Screen-Reader-Unterstützung via `aria-describedby`
- [ ] Tooltip-Delay: 300ms auf Desktop, sofort bei Touch
- [ ] HelpTooltip hat vitest-Tests (Sichtbarkeit, Interaktion, i18n, Erfahrungsstufen-Anpassung)
- [ ] Kein Performance-Impact: Tooltips werden lazy gerendert (nur bei Interaktion)

### Code-Review:
- [ ] Neue Fachbegriff-Felder ohne `HelpTooltip` sind ein Review-Blocker
- [ ] Neue Glossareinträge ohne DE+EN sind ein Review-Blocker
- [ ] ESLint-Regel (empfohlen, nicht blockierend): Warnung bei `<TextField label="...">` ohne umschließendes `<HelpTooltip>`

---

<!-- Quelle: Frontend-Design-Review K-004 (Massentauglichkeit 2026-02-28) -->
## 8. Implementierungspriorität & MVP-Scope

**Begründung:** Keine `HelpTooltip`-Komponente existiert in der Codebasis (Stand 2026-02-28). Felder wie "EC (mS/cm)", "VPD (kPa)", "PPFD", "NPK-Ratio" werden ohne jede Erklärung angezeigt. Das betrifft sämtliche Düngungs-, Sensorik- und Kultivierungsseiten. 16 unerklärte Fachbegriffe wurden im Frontend-Design-Review identifiziert — das ist eine kritische Barriere für Massentauglichkeit. Hobby-Gärtner und Einsteiger (die größte potenzielle Zielgruppe) scheitern an den ersten Formularen.

| Phase | Umfang | Begriffe | Betroffene Seiten | Begründung |
|-------|--------|----------|-------------------|------------|
| **Phase 1 — MVP** | `HelpTooltip`-Skeleton-Komponente, Glossar-i18n-Struktur, 8 kritischste Fachbegriffe | EC, pH, VPD, PPFD, NPK, CalMag, GDD, DLI | Düngungsseiten (NutrientPlanDetail, FertilizerDetail, NutrientCalculations), Phasen-Detail | Diese 8 Begriffe erscheinen auf den meistgenutzten Seiten und sind für Einsteiger völlig unverständlich. HelpTooltip als Komponente ist Voraussetzung für alle weiteren Phasen. |
| **Phase 2 — Nährstoffe & Klima** | Erweiterte Tooltips, alle Nährstoff- + Klima-Begriffe | Flushing, Runoff, Mixing Priority, CEC, rH, DIF, Hysterese, Starkzehrer/Mittelzehrer/Schwachzehrer (15 Begriffe kumulativ) | Sensor-Seiten, Tank-Detail, Substrat-Detail | Komplettiert die Abdeckung der häufigsten Workflow-Seiten. |
| **Phase 3 — Glossar-Seite & Taxonomie** | Glossar-Route (`/glossar`), Suchfeld, Kategoriefilter, verbleibende 23 Begriffe | Allelopathie, Vernalisation, Dormanz, Seneszenz, Photoperiodismus, IPM, Hardiness Zones, Fruchtfolge, Mischkultur, Substrat, Cultivar, Standort/Location/Slot, Pflanzdurchlauf, Drainage, Staunässe, Umtopfen, Lux vs. PPFD, Binomialnomenklatur + weitere | Glossar-Seite, Stammdaten, IPM, Companion Planting | Eigenständige Glossar-Seite als Nachschlagewerk. Alle 38 Pflicht-Begriffe vollständig abgedeckt. |
| **Phase 4 — Code-Review-Automatisierung** | ESLint-Regel (Warnung bei `<TextField label="...">` ohne `<HelpTooltip>`), CI-Integration, Auto-Open-Logik für Einsteiger-Modus | — | Alle Seiten | Stellt sicher, dass zukünftige Formularfelder nicht ohne Erklärung hinzugefügt werden. |

**MVP-Definition (Mindestumfang für erste nutzbare Version):**

| Komponente | Beschreibung |
|-----------|-------------|
| `HelpTooltip.tsx` | Shared Component unter `src/frontend/src/components/shared/`. Props: `term`, `children`, `placement`, `iconOnly`. Liest Glossar-Daten aus i18n. Icon-Größe und Verhalten nach Erfahrungsstufe (REQ-021). |
| `glossary.de.json` | i18n-Namespace `glossary` mit mindestens 8 Einträgen (EC, pH, VPD, PPFD, NPK, CalMag, GDD, DLI). Jeder Eintrag mit `short`, `long`, `beginnerTip`, `unit`, `typicalRange`. |
| `glossary.en.json` | Englische Übersetzung der 8 MVP-Einträge. |
| `useGlossary` | Hook: Lädt Glossar-Daten einmalig beim App-Start (kein erneuter Fetch pro Tooltip). Stellt `getEntry(term)` bereit. |
| Integration | `HelpTooltip` in NutrientPlanDetailPage (EC, pH, NPK), FertilizerDetailPage (NPK), NutrientCalculationsPage (EC, CalMag, VPD) einbauen. |

---

## 9. Abhängigkeiten

| REQ/NFR | Art | Beschreibung |
|---------|-----|-------------|
| REQ-021 | Liest | `experience_level` bestimmt Tooltip-Darstellungsmodus |
| NFR-010 | Erweitert | `helperText` (kurze Feld-Hilfe) wird durch HelpTooltip (ausführliche Fachbegriff-Erklärung) ergänzt |
| NFR-003 | Konform | ESLint-Integration für Code-Review-Prüfregeln |
| Alle REQs | Betroffen | Jedes REQ mit Fachbegriffen im UI muss HelpTooltip verwenden |
