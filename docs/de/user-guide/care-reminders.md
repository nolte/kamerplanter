# Pflegeerinnerungen

Kamerplanter erinnert dich automatisch daran, welche Pflanzen heute Wasser, Duenger oder Pflege brauchen — ohne dass du Cron-Ausdruecke oder Workflow-Templates kennen musst. Ein Fingertipp genuegt zur Bestaetigung. Das System lernt aus deinem Pflegeverhalten und passt Intervalle automatisch an.

---

## Voraussetzungen

- Mindestens eine Pflanze ist angelegt
- Der Pflanzinstanz wurde ein Care Profile zugewiesen (wird automatisch beim ersten Zugriff erstellt)

---

## Der Pflege-Kalender

Navigiere zu **Pflege** > **Heute faellig**, um alle Pflanzen zu sehen, die heute Aufmerksamkeit brauchen. Die Karten sind nach Dringlichkeit sortiert:

| Farbe | Bedeutung |
|-------|-----------|
| Rot | Ueberfaellig (Pflanze leidet moeglicherweise) |
| Orange | Heute faellig |
| Gelb | Bald faellig (1–2 Tage) |
| Gruen | Kuerzlich gepflegt |

### Pflege bestaetigen

1. Klicke auf die Pflegekarte der Pflanze
2. Klicke auf den grossen **Erledigt**-Button
3. Fertig — das System merkt sich den Zeitpunkt und berechnet den naechsten Termin

!!! tip "Adaptives Lernen"
    Wenn du eine Pflanze konsequent 8 statt 7 Tage nach der letzten Bestaetigung giesst, passt das System das Intervall nach 3 aufeinanderfolgenden Bestaedigungen automatisch an. Der Lerneffekt ist auf ±1 Tag pro Schritt begrenzt und kann das Intervall maximal um ±30% veraendern.

---

## Care Profiles

Jede Pflanze hat ein **Care Profile** mit den Pflegeintervallen fuer diese spezifische Pflanze. Das Profil wird automatisch aus den Stammdaten der Art generiert und kann danach angepasst werden.

### Care Profile oeffnen

1. Navigiere zu **Pflanzen** > gewuenschte Pflanze
2. Klicke auf den Tab **Pflege**
3. Klicke auf **Care Profile bearbeiten**

### Pflege-Stile (Care Style Presets)

Das System kennt vordefinierte Pflege-Stile fuer typische Pflanzengruppen:

| Pflege-Stil | Giessen (Sommer) | Winter-Faktor | Typische Pflanzen |
|-------------|-----------------|---------------|-------------------|
| `tropical` | Alle 7 Tage | 1,5× | Monstera, Philodendron, Ficus |
| `succulent` | Alle 14 Tage | 2,5× | Echeveria, Haworthia, Aloe |
| `orchid` | Alle 7 Tage (Tauchbad) | 1,5× | Phalaenopsis, Dendrobium |
| `calathea` | Alle 5 Tage | 1,3× | Calathea, Maranta, Ctenanthe |
| `herb_tropical` | Alle 3 Tage | 1,5× | Basilikum, Minze, Koriander |
| `mediterranean` | Alle 10 Tage | 2,0× | Rosmarin, Lavendel, Thymian |
| `fern` | Alle 4 Tage | 1,3× | Nephrolepis, Adiantum, Asplenium |
| `cactus` | Alle 21 Tage | 3,0× | Kakteen (Cactaceae) |
| `custom` | Frei konfigurierbar | Frei | — |

!!! warning "Nicht alle Sukkulenten sind Kakteen"
    Kakteen (Cactaceae) und Sukkulenten wie Echeveria oder Haworthia gehoeren verschiedenen Familien an. Der Pflege-Stil `cactus` gilt nur fuer echte Kakteen. Echeveria und Haworthia nutzen `succulent`. Lithops und andere Mesembs (Aizoaceae) brauchen eine noch spezifischere Logik und sollten mit `custom` konfiguriert werden.

### Giesshinweise

Das Care Profile zeigt nicht nur *wann*, sondern auch *wie* gegossen werden soll:

| Pflege-Stil | Giessmethode |
|-------------|-------------|
| `tropical` | Von oben giessen, bis Wasser unten herauslaeuft. Ueberschuss nach 30 Min. wegkippen. |
| `orchid` | Tauchbad: Topf 10–15 Min. in zimmerwarmes Wasser, dann abtropfen lassen. |
| `calathea` | Von oben mit kalkarmem Wasser giessen. Blaetter nicht benetzen. |
| `cactus` | Kraeftig durchgiessen, vollstaendig austrocknen lassen. |

!!! info "Wasserqualitaet"
    Fuer Calatheen und Orchideen empfiehlt das System Regenwasser oder gefiltertes Wasser — diese Pflanzen reagieren empfindlich auf Kalk im Leitungswasser (braune Blattspitzen).

---

## Automatische Erinnerungstypen

Das System generiert taeglich Erinnerungen fuer folgende Pflegeaufgaben:

| Erinnerungstyp | Ausloser | Prioritaet |
|----------------|---------|------------|
| **Giessen** | Intervall seit letzter Bestaetigung | Hoch |
| **Duengen** | Intervall + nur in Aktivmonaten | Mittel |
| **Umtopfen** | Monate seit letztem Umtopfen | Niedrig |
| **Schaedlingskontrolle** | Festes Intervall (Standard: 14 Tage) | Mittel |
| **Standort-Check** | Saisonal: Oktober + Maerz | Mittel |
| **Luftfeuchte-Check** | Heizperiode (Okt–Maerz) | Mittel |
| **Winterschutz** | Oktober (Nordhalbkugel) | Hoch |
| **Fruehjahrs-Auspacken** | Maerz (Nordhalbkugel) | Hoch |
| **Knollen ausgraben** | Vor erstem Frost (Oktober) | Kritisch |

### Duenge-Schutz (Dormanz-Guard)

Duengungs-Erinnerungen werden **nicht** generiert, wenn:
- Der aktuelle Monat ausserhalb der `Aktivmonate` des Pflege-Stils liegt (z.B. November–Februar fuer die meisten Zimmerpflanzen)
- Die Pflanze sich in einer Ruhephase befindet (Winterruhe, Seneszenz, Abhaertungsphase)

!!! tip "Warum kein Duenger im Winter?"
    Bei reduziertem Licht im Winter sinkt die Photosynthese-Rate. Zimmerpflanzen koennen die Naehrstoffe nicht verwerten — Duenger akkumuliert als Salz im Substrat und schaedigt die Wurzeln.

---

## Saisonale Anpassung

Das System passt Giessintervalle automatisch an die Jahreszeit an:

- **Nordhalbkugel**: Winter = November–Februar, Sommer = Mai–August
- **Suedhalbkugel**: Winter = Mai–August, Sommer = November–Februar

Die Hemisphare wird aus dem Standort der Pflanze abgeleitet (`Site.hemisphere`). Das effektive Giessintervall berechnet sich als:

```
Effektives Intervall = Basis-Intervall × Winter-Faktor
```

!!! example "Beispiel: Monstera im Winter"
    - Basis-Intervall (Sommer): 7 Tage
    - Winter-Faktor (`tropical`): 1,5×
    - Effektives Intervall (Winter): 10–11 Tage

---

## Ueberwinterungsmanagement

Fuer Pflanzen, die Winterschutz brauchen, bietet Kamerplanter ein vollstaendiges Ueberwinterungs-System.

### Winterhaerte-Ampel

Jede Pflanze bekommt eine farbige Bewertung basierend auf ihrer Frostempfindlichkeit und deiner Klimazone:

| Ampel | Bedeutung | Typische Pflanzen |
|-------|-----------|-------------------|
| Gruen | Winterhart — kein Schutz noetig | Stachelbeere, Apfelbaum, Tulpen |
| Gelb | Schutzbeduerftiger — Mulch oder Vlies | Rosen, Lavendel, Stauden |
| Rot | Muss frostfrei ueberwintern | Oleander, Zitrus, Dahlien |

!!! warning "Dahlien und Knollen"
    Dahlien, Gladiolen und Canna muessen vor dem ersten Frost ausgegraben werden. Das System sendet eine **Kritische Erinnerung** mit dem Knolle-Ausgraben-Hinweis sobald die Temperaturprognose auf Frost hinweist.

### Knollen-Zyklus verfolgen

Fuer Pflanzen mit Knollen oder Zwiebeln (Dahlien, Gladiolen, Canna, Tulpen) kannst du den vollstaendigen Jahreszyklus dokumentieren:

1. Auspflanzen → Bluehen → Ausgraben → Trocknen → Einlagern → Kontrollieren → Vorziehen

Navigiere zu **Pflanzen** > gewuenschte Pflanze > Tab **Ueberwinterung**, um den Status zu verwalten.

### Freiland-Pflege-Stile

Ergaenzend zu den Zimmerpflanzen-Stilen gibt es Presets fuer Freilandpflanzen:

| Pflege-Stil | Winter-Aktion | Typische Pflanzen |
|-------------|--------------|-------------------|
| `outdoor_perennial` | Winterschutz pruefen (Mulch, Vlies) | Rittersporn, Phlox, Stauden |
| `frost_tender_tuber` | AUSGRABEN + frostfrei lagern | Dahlie, Gladiole, Canna |
| `frost_tender_container` | Ins Winterquartier (5–12°C, hell) | Oleander, Zitrus, Olive |
| `fruit_tree` | Kalkanstrich, Stammschutz | Apfel, Birne, Kirsche |
| `spring_bulb` | Im Boden lassen (winterhart) | Tulpe, Narzisse, Krokus |

---

## Familienbasierte Pflegezuordnung

Das System kennt die Pflegeanforderungen von 10 Pflanzenfamilien und ordnet neue Pflanzen automatisch dem passenden Care Style zu:

| Familie | Auto-Stil |
|---------|-----------|
| Araceae (Aronstabgewaechse) | `tropical` |
| Cactaceae (Kakteengewaechse) | `cactus` |
| Marantaceae (Marantengewaechse) | `calathea` |
| Orchidaceae (Orchideen) | `orchid` |
| Crassulaceae (Dickblattgewaechse) | `succulent` |
| Asphodelaceae (Affodillgewaechse) | `succulent` |
| Lamiaceae (Lippenbluetengewaechse) | `mediterranean` |
| Polypodiaceae / Pteridaceae (Farne) | `fern` |
| Liliaceae / Amaryllidaceae (Liliengewaechse) | `outdoor_perennial` |
| Solanaceae (Nachtschattengewaechse) | `outdoor_annual_veg` |

!!! tip "Automatische Zuweisung"
    Wenn du eine neue Pflanzinstanz anlegst, weist das System automatisch den passenden Care Style basierend auf der botanischen Familie zu. Du kannst den Stil jederzeit manuell ueberschreiben.

---

## Haeufige Fragen

??? question "Die Erinnerung erscheint zu spaet — kann ich das anpassen?"
    Ja. Oeffne das Care Profile der Pflanze und reduziere das Intervall. Alternativ wird das System nach ein paar Bestaedigungen das Muster erkennen und das Intervall automatisch anpassen.

??? question "Ich habe eine Pflanze vergessen zu giessen — wie setze ich den Zaehler zurueck?"
    Bestatige die Pflege manuell im Pflege-Dashboard. Das System setzt den Timer auf "jetzt" zurueck, egal wie lange die letzte Bestaetigung zurueckliegt.

??? question "Warum bekomme ich im Dezember keine Duenge-Erinnerung fuer meine Monstera?"
    Richtig so — Monstera (care_style: `tropical`) bekommt den Duenge-Aktiv-Zeitraum Maerz–Oktober. Im Dezember ist dieser Zeitraum abgelaufen, da Zimmerpflanzen im Winter bei geringem Licht keine Naehrstoffe aufnehmen koennen.

??? question "Meine Dahlie hat eine gruene Ampel — aber ich weiss, dass sie Schutz braucht."
    Die Ampel berechnet sich aus dem `frost_sensitivity`-Wert der Art UND deiner Klimazone. Pruefe, ob die richtige Klimazone bei deinem Standort eingestellt ist. Du kannst den Care Style auch manuell auf `frost_tender_tuber` setzen.

---

## Siehe auch

- [Pflanzdurchlaeufe](planting-runs.md)
- [Wachstumsphasen](growth-phases.md)
- [Standorte & Substrate](locations-substrates.md)
- [Kalender](calendar.md)
