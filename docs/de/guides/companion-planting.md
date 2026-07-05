# Mischkultur & Fruchtfolge

Kamerplanter unterstützt dich bei zwei eng verwandten Anbau-Entscheidungen: **welche Pflanzenarten sich gegenseitig fördern oder schaden** (Mischkultur) und **welche botanische Familie nach welcher auf demselben Stellplatz angebaut werden sollte** (Fruchtfolge). Beide Themen werden über globale Stammdaten gepflegt und teilweise automatisch beim Anlegen einer Pflanze geprüft.

---

## Voraussetzungen

- Pflanzenarten mit zugeordneter botanischer Familie in den Stammdaten
- Für die automatische Prüfung: ein Standort mit angelegten Stellplätzen

---

## Was ist Mischkultur — und warum funktioniert sie?

Pflanzen beeinflussen sich gegenseitig auf verschiedene Weisen:

| Mechanismus | Beispiel | Effekt |
|------------|---------|--------|
| **Schädlingsabwehr** | Tagetes neben Tomate | Nematoden werden durch Wurzelausscheidungen vertrieben |
| **Aromawirkung** | Basilikum neben Tomate | Ätherische Öle verwirren die Weiße Fliege |
| **Stickstoffbindung** | Bohnen neben Mais | Knollenbakterien fixieren Luftstickstoff |
| **Wurzelraumnutzung** | Zwiebel + Karotte | Verschiedene Tiefen, keine Nährstoffkonkurrenz |
| **Schattenwirkung** | Salat unter Tomate | Blattsalat gedeiht im Halbschatten, Boden bleibt feucht |
| **Bestäuberlockung** | Phacelia neben Gemüsebeet | Wildbienen werden angezogen |

!!! tip "Mischkultur ist kein Wundermittel"
    Mischkultur unterstützt, ersetzt aber keine gute Bodenpflege, Bewässerung und
    Fruchtfolge. Behandle sie als eine Maßnahme von mehreren.

---

## Klassische Kombinationen

### Die drei Schwestern (Mais, Bohne, Kürbis)

Eine der ältesten Mischkulturen der Welt — entwickelt von den Haudenosaunee (Irokesen):

```
Mais         → Rankhilfe für Bohnen, schattiert Kürbis-Boden
Bohne        → Stickstoffbindung für Mais und Kürbis
Kürbis       → Große Blätter beschatten den Boden, halten Feuchtigkeit
```

In den Kamerplanter-Stammdaten sind alle drei Paarungen als kompatibel hinterlegt (Mais + Bohne: 0,9 · Mais + Kürbis: 0,85 · Bohne + Kürbis: 0,8). Lege für jede der drei Arten einen eigenen [Pflanzdurchlauf](../user-guide/planting-runs.md) am selben Standort an — einen eigenen Durchlauf-Typ "Mischkultur" gibt es nicht (siehe [Was ein Pflanzdurchlauf ist](../user-guide/planting-runs.md#was-ist-ein-pflanzdurchlauf)).

### Tomate & Basilikum

Wahrscheinlich die bekannteste Mischkultur im Gewächshaus und Freiland:

- Basilikum wirkt als Schädlingsabwehr (Weiße Fliege, Blattläuse)
- Gemeinsamer Wasserbedarf und Temperaturansprüche erleichtern die Pflege
- Beide benötigen sonnenreichen Standort

**Kompatibilitäts-Score in Kamerplanter:** 0,9 (sehr empfohlen)

### Karotte & Zwiebel

Klassisches Gemüse-Paar (Score 0,9):

- Zwiebeln und Karotten nutzen verschiedene Bodenebenen
- Zwiebelduft stört die Karottenfliegeneiablage
- Karottenkraut stört die Zwiebelfliege

### Tagetes & Ringelblume als Universal-Begleiter

Zwei Kräuter, die sich fast überall einsetzen lassen:

| Pflanze | Wirkung | Empfohlene Nachbarn |
|---------|---------|---------------------|
| **Tagetes** (Studentenblume) | Nematoden, Weiße Fliege, Wurzelausscheidungen halten Schnecken fern | Tomate, Paprika, Salat |
| **Ringelblume** (Calendula) | Blattlaus-Abwehr, lockt Nützlinge an (Schwebefliegen, Marienkäfer) | Fast alle Gemüse |

!!! tip "Tagetes als Beet-Einfassung"
    Pflanze Tagetes rundum um ein Gemüsebeet als lebende Grenze. Selbst wenn du
    keine Daten in Kamerplanter erfasst, profitiert das gesamte Beet von der
    Schutzwirkung.

### Kräuter als Schädlingsabwehr

| Kraut | Wirkung |
|-------|---------|
| Basilikum | Weiße Fliege, Blattläuse |
| Lavendel | Milben, Motten (Duft) |
| Salbei | Kohlfliege, Kohldurchlaufraupe |
| Bohnenkraut | Schwarze Bohnenblattlaus |
| Dill | Karottenfliegenweibchen verwirren; lockt Schwebefliegen an |
| Koriander | Blattläuse vertreiben, Schwebefliegen anlocken |

---

## Schlechte Nachbarn — was du vermeiden solltest

!!! danger "Fenchel: Der Einzelgänger"
    Fenchel verträgt sich mit fast keiner anderen Gartenpflanze. Er sondert
    Allelopathie-Stoffe ab, die das Wachstum von Tomaten, Paprika, Buschbohnen und Salat
    hemmen. Pflanze Fenchel in ein eigenes Beet oder in einem Topf am Rand.

| Inkompatibles Paar | Grund | Empfehlung |
|-------------------|-------|-----------|
| Tomate + Kartoffel | Gleiche Solanaceae-Familie, gemeinsame Krankheiten (Phytophthora) | Mindestens 10 m Abstand halten |
| Fenchel + Tomate | Allelopathie durch Fenchel-Sekundärstoffe | Getrennte Beete |
| Zwiebel + Erbse | Wachstumshemmung bei Erbsen | Verschiedene Beet-Abschnitte |
| Kartoffel + Kürbis | Starke Nährstoffkonkurrenz | Rotationsplanung beachten |

<!-- Quelle: src/backend/app/migrations/seed_data/companion_planting.yaml -->

---

## Kompatibilitäts-Stammdaten pflegen

### Wo du sie findest

- Navigation: **Stammdaten → Mischkultur** — globale Verwaltung, unabhängig von einem konkreten Beet.
- Alternativ direkt am Artendetail: Tab **Mischkultur** (sichtbar ab Erfahrungsstufe "Experte"), vorbelegt mit der jeweiligen Art.

### Bedienung

1. Wähle im Dropdown eine Art aus. Kamerplanter zeigt zwei Karten: **Kompatible Arten** und **Inkompatible Arten**.
2. Klicke auf **Kompatibilität hinzufügen**, wähle die Partnerart und vergib eine **Bewertung** zwischen 0,1 (schwach) und 1,0 (stark) — das ist der Kompatibilitäts-Score, wie z.B. 0,9 bei Tomate/Basilikum.
3. Klicke auf **Inkompatibilität hinzufügen**, wähle die Partnerart und trage einen kurzen **Grund** ein (z.B. "Allelopathie").

!!! note "Familienebene-Fallback"
    Liegt für ein konkretes Artenpaar noch kein Eintrag vor, sucht Kamerplanter bei einer Empfehlungsabfrage automatisch nach einer Kompatibilität auf **Familienebene**. Ein solcher Fallback-Treffer wird im Score um 20 % reduziert (Score × 0,8) und als "Familienebene" statt "Artebene" gekennzeichnet.

!!! info "Wer darf diese Daten pflegen?"
    Kompatibilitäts- und Inkompatibilitäts-Einträge sind globale Stammdaten, die für alle Nutzer:innen sichtbar sind. Nur **Platform-Admins** dürfen sie anlegen oder ändern — normale Nutzerkonten sehen die Bearbeitungsschaltflächen zwar, erhalten beim Speichern aber eine Fehlermeldung ("Nicht autorisiert"). Eigene Beobachtungen zu deinen Pflanzen kannst du unabhängig davon im Pflanzentagebuch festhalten, sobald dafür eine Oberfläche verfügbar ist (siehe [Pflanzdurchläufe: Pflanzentagebuch](../user-guide/planting-runs.md#pflanzentagebuch)).

<!-- Quelle: src/frontend/src/pages/stammdaten/CompanionPlantingPage.tsx, src/backend/app/api/v1/companion_planting/router.py -->

---

## Automatische Prüfung beim Anlegen einer Pflanze (Stellplatz-Nachbarschaft)

Wenn du eine **einzelne Pflanze** über **Pflanzen → Pflanzeninstanzen → Neue Pflanze** anlegst und ihr dabei einen **Stellplatz** zuweist, prüft Kamerplanter automatisch die direkt benachbarten Stellplätze:

- Steht dort bereits eine als **inkompatibel** hinterlegte Art, lehnt Kamerplanter die Anlage mit einer Fehlermeldung ab.
- Steht dort eine **kompatible** Art, wird das intern als Vorteil vermerkt.

!!! warning "Gilt nicht für Pflanzen aus einem Pflanzdurchlauf"
    Die Nachbarschaftsprüfung greift aktuell nur, wenn du eine Pflanze einzeln über die Stammdaten-Seite **Pflanzeninstanzen** anlegst. Werden Pflanzen automatisch aus den Einträgen eines [Pflanzdurchlaufs](../user-guide/planting-runs.md) erzeugt, findet **keine** Kompatibilitätsprüfung statt.

<!-- Quelle: src/backend/app/domain/engines/companion_planting_engine.py, src/backend/app/domain/services/plant_instance_service.py -->

---

## Fruchtfolge

Fruchtfolge bedeutet, auf einem Stellplatz über die Jahre bewusst zwischen botanischen Familien zu wechseln — das beugt einseitiger Nährstoffzehrung und der Anreicherung familienspezifischer Schädlinge und Krankheiten im Boden vor.

### Nachfolger-Stammdaten pflegen

- Navigation: **Stammdaten → Fruchtfolge**. Alternativ am Artendetail: Tab **Fruchtfolge** (Erfahrungsstufe "Experte"), vorbelegt mit der Familie der jeweiligen Art.

1. Wähle eine **Ausgangsfamilie** aus. Kamerplanter zeigt die bereits hinterlegten **Nachfolgerfamilien**.
2. Klicke auf **Nachfolger hinzufügen**, wähle die Zielfamilie und trage die **Wartezeit in Jahren** ein (1–10). Die Wartezeit gibt an, wie lange gewartet werden sollte, bevor auf demselben Stellplatz wieder eine Pflanze der Ausgangsfamilie angebaut wird.

### Automatische Prüfung

Beim Anlegen einer **einzelnen Pflanze** mit Stellplatz prüft Kamerplanter zusätzlich die Anbau-Historie dieses Stellplatzes über einen Standard-Zeitraum von **3 Jahren**:

| Ergebnis | Bedeutung |
|----------|-----------|
| **Kritisch** (blockiert die Anlage) | Dieselbe botanische Familie wurde am selben Stellplatz innerhalb der letzten 3 Jahre bereits angebaut |
| **Warnung** | Zwischen der geplanten und einer zuvor dort angebauten Familie besteht ein hohes gemeinsames Schädlings-/Krankheitsrisiko |
| **Positiv** | Die geplante Familie ist als empfohlener Nachfolger einer zuvor dort angebauten Familie hinterlegt (inkl. Hinweis auf den Stickstoff-Vorteil bei stickstoffbindenden Vorfrüchten) |
| **Kein Hinweis** | Keine passenden Daten für diese Kombination vorhanden |

Ein kritisches Ergebnis blockiert das Anlegen der Pflanze mit einer Fehlermeldung. Wie bei der Mischkultur-Prüfung gilt das nur für einzeln angelegte Pflanzen, nicht für automatisch aus einem Pflanzdurchlauf erzeugte.

<!-- Quelle: src/backend/app/domain/engines/crop_rotation_validator.py, src/backend/app/config/constants.py (DEFAULT_ROTATION_WINDOW_YEARS = 3) -->

---

## Häufige Fragen

??? question "Was bedeutet 'Allelopathie'?"
    Allelopathie beschreibt die Fähigkeit von Pflanzen, chemische Stoffe abzusondern,
    die das Wachstum anderer Pflanzen hemmen oder fördern. Fenchel ist das bekannteste
    Beispiel für negative Allelopathie im Garten.

??? question "Funktioniert Mischkultur auch im Gewächshaus und Innenraum?"
    Ja, aber mit Einschränkungen. Schädlingsabwehr durch Duft wirkt auch drinnen.
    Allerdings ist der Raum oft begrenzt, und manche Begleiter (z.B. hohe Tagetes-Sorten)
    behindern die Luftzirkulation. Die hinterlegten Kompatibilitätsdaten sind primär für
    Freiland-Nutzpflanzen zusammengestellt.

??? question "Woher stammen die Kompatibilitätsdaten?"
    Die mitgelieferten Stammdaten basieren auf gärtnerischen Standardwerken und
    anerkannten Begleitpflanzen-Empfehlungen. Eine Quellenangabe je einzelnem Eintrag
    zeigt die Oberfläche aktuell nicht an.

??? question "Kann ich eigene Kompatibilitätspaare hinzufügen?"
    Nur, wenn du **Platform-Admin** bist — die Daten gelten global für alle Mandanten und sind deshalb schreibgeschützt für normale Nutzerkonten. Eigene, pflanzenbezogene Beobachtungen hältst du stattdessen im Pflanzentagebuch fest.

## Siehe auch

- [Pflanzdurchläufe](../user-guide/planting-runs.md)
- [Standorte & Substrate](../user-guide/locations-substrates.md)
- [Stammdaten: Pflanzenarten](../user-guide/plant-management.md)
- [Pflanzenschutz (IPM)](../user-guide/pest-management.md)
- [GDD-Berechnung](gdd-calculation.md)
