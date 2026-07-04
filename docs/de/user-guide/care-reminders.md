# Pflegeerinnerungen

Kamerplanter erinnert dich automatisch daran, welche Pflanzen heute Wasser, Dünger oder andere Pflege brauchen — ohne dass du Cron-Ausdrücke oder Workflow-Templates kennen musst. Ein Fingertipp genügt zur Bestätigung. Das System lernt aus deinem Pflegeverhalten und passt Intervalle automatisch an.

---

## Voraussetzungen

- Mindestens eine Pflanze ist angelegt
- Der Pflanzinstanz wurde ein Care Profile (Pflegeprofil) zugewiesen (wird automatisch beim ersten Zugriff erstellt)

---

## Pflegeerinnerungen im Aufgaben-Bereich

Pflegeerinnerungen haben keinen eigenen Menüpunkt — sie erscheinen zusammen mit deinen sonstigen Aufgaben unter **Aufgaben** (`/aufgaben/queue`). Wähle im Filter **Quelle** die Option **Pflege**, um ausschließlich automatische Pflegeerinnerungen zu sehen.

Die Karten sind nach Dringlichkeit sortiert und farblich markiert:

| Farbe | Bedeutung |
|-------|-----------|
| Rot | Überfällig |
| Orange | Heute fällig |
| Gelb | Bald fällig (in den nächsten 1–2 Tagen) |

!!! note "Kein grüner Zustand"
    Kürzlich gepflegte Pflanzen erzeugen keine Karte — sie erscheinen erst wieder, sobald eine Erinnerung bald fällig, heute fällig oder überfällig ist. Es gibt also nur die drei oben genannten Dringlichkeitsstufen, keine eigene „alles in Ordnung"-Anzeige je Pflanze.

### Pflege bestätigen

Jede Pflegekarte bietet drei Aktionen:

1. **Bearbeiten** (Stift-Symbol) — öffnet das Pflegeprofil dieser Pflanze.
2. **Erledigt** (Häkchen-Symbol) — bestätigt die Pflege. Das System merkt sich den Zeitpunkt und berechnet den nächsten Termin.
3. **Später** (Schlummer-Symbol) — verschiebt die Erinnerung standardmäßig um einen Tag, ohne den Zeitpunkt der letzten Bestätigung zu verändern.

!!! tip "Adaptives Lernen"
    Wenn du eine Pflanze konsequent 8 statt 7 Tage nach der letzten Bestätigung gießt, passt das System das Intervall nach 3 aufeinanderfolgenden Bestätigungen automatisch an. Der Lerneffekt ist auf ±1 Tag pro Schritt begrenzt und kann das Intervall maximal um ±30 % gegenüber dem Basisintervall verändern.

---

## Pflegeprofile

Jede Pflanze hat ein **Care Profile** (Pflegeprofil) mit den Pflegeintervallen für diese spezifische Pflanze. Das Profil wird automatisch aus den Stammdaten der Art bzw. botanischen Familie generiert und kann danach angepasst werden.

### Pflegeprofil öffnen

1. Navigiere zu **Pflanzen** > gewünschte Pflanze
2. Klicke auf den Tab **Pflege**
3. Klicke auf **Pflegeprofil bearbeiten**

Im Bearbeiten-Dialog aktivierst oder deaktivierst du jeden Erinnerungstyp einzeln (Schalter) und passt sein Intervall über einen Schieberegler an; für Gießen wählst du zusätzlich die Gießmethode, für Düngen die Aktivmonate.

### Pflegestil-Presets

Das System kennt vordefinierte Pflegestile für typische Zimmerpflanzengruppen. Über das Feld **Pflegestil** im Bearbeiten-Dialog wählst du einen der folgenden neun Presets — die Basiswerte gelten für den Sommer, im Winter wird das Gießintervall mit dem Winter-Faktor multipliziert:

<!-- Quelle: src/backend/app/domain/engines/care_reminder_engine.py (CARE_STYLE_PRESETS) -->

| Pflegestil | Gießintervall (Sommer) | Winter-Faktor | Gießmethode | Typische Pflanzen |
|-------------|------------------------|----------------|-------------|-------------------|
| Tropisch (`tropical`) | Alle 7 Tage | 1,5× | Von oben gießen | Monstera, Philodendron, Ficus |
| Sukkulente (`succulent`) | Alle 14 Tage | 3,0× | Durchgießen | Echeveria, Haworthia, Aloe |
| Orchidee (`orchid`) | Alle 7 Tage | 2,0× | Tauchen | Phalaenopsis, Dendrobium |
| Calathea (`calathea`) | Alle 5 Tage | 1,5× | Von unten gießen | Calathea, Maranta, Ctenanthe |
| Tropische Kräuter (`herb_tropical`) | Alle 5 Tage | 1,5× | Von oben gießen | Basilikum, Minze, Koriander |
| Mediterran (`mediterranean`) | Alle 10 Tage | 2,0× | Durchgießen | Rosmarin, Lavendel, Thymian |
| Farn (`fern`) | Alle 4 Tage | 1,5× | Von oben gießen | Nephrolepis, Adiantum, Asplenium |
| Kaktus (`cactus`) | Alle 21 Tage | 4,0× | Durchgießen | Kakteen (Cactaceae) |
| Benutzerdefiniert (`custom`) | Startwert 7 Tage, frei änderbar | Startwert 1,5×, frei änderbar | Frei wählbar | — |

!!! warning "Nicht alle Sukkulenten sind Kakteen"
    Kakteen (Cactaceae) und Sukkulenten wie Echeveria oder Haworthia gehören verschiedenen Familien an. Der Pflegestil `cactus` gilt nur für echte Kakteen. Echeveria und Haworthia nutzen `succulent`. Lithops und andere Mesembs (Aizoaceae) brauchen eine noch spezifischere Logik und sollten mit `custom` konfiguriert werden.

!!! info "Wasserqualität"
    Für Calatheen und Orchideen empfiehlt das System Regenwasser oder gefiltertes Wasser — diese Pflanzen reagieren empfindlich auf Kalk im Leitungswasser (braune Blattspitzen).

---

## Automatische Erinnerungstypen

Kamerplanter generiert Erinnerungen für die folgenden sechs Pflegeaufgaben:

<!-- Quelle: src/backend/app/domain/engines/care_reminder_engine.py (ReminderType, should_generate_reminder) -->

| Erinnerungstyp | Auslöser |
|----------------|---------|
| **Gießen** | Intervall seit letzter Bestätigung, saisonal angepasst |
| **Düngen** | Intervall + nur in Aktivmonaten des Pflegestils, nur wenn ein Nährstoffplan zugewiesen ist |
| **Umtopfen** | Monate seit letztem Umtopfen |
| **Schädlingskontrolle** | Festes Intervall (je nach Pflegestil, Standard 14 Tage) |
| **Standort-Check** | Optional aktiviert, saisonal auf bestimmte Monate eingrenzbar |
| **Luftfeuchte-Check** | Optional aktiviert, festes Intervall |

Automatisch erstellte Pflegeaufgaben starten mit der Priorität „Mittel"; ist eine Erinnerung bereits überfällig, wird die nachfolgend erstellte Aufgabe mit „Hoch" angelegt.

### Warum eine Erinnerung ausbleiben kann

Die häufigste Ursache für eine „fehlende" Erinnerung ist einer der folgenden Gründe:

- **Aktiver Gießplan**: Hat die Pflanze über einen Pflanzdurchlauf bereits einen aktiven automatischen Gießplan, unterdrückt Kamerplanter zusätzliche manuelle Gieß- und Düngeerinnerungen für diese Pflanze.
- **Nährstoffplan-Voraussetzung**: Düngeerinnerungen entstehen nur, wenn der Pflanze ein Nährstoffplan zugewiesen ist — unabhängig vom Pflegestil.
- **Ruhephase (Dormanz)**: Befindet sich die Pflanze in einer Ruhephase (Winterruhe, Seneszenz, Abhärtungsphase, Akklimatisierung, Umtopf-Erholung), werden alle Erinnerungen außer der Schädlingskontrolle unterdrückt.
- **Aktivmonate**: Liegt der aktuelle Monat außerhalb der Aktivmonate des Pflegestils (z.B. November–Februar bei den meisten Zimmerpflanzen), entsteht keine Düngeerinnerung.
- **Ein-/Aus-Schalter**: Jeder Erinnerungstyp lässt sich im Pflegeprofil einzeln deaktivieren.

!!! tip "Warum kein Dünger im Winter?"
    Bei reduziertem Licht im Winter sinkt die Photosynthese-Rate. Zimmerpflanzen können die Nährstoffe nicht verwerten — Dünger akkumuliert als Salz im Substrat und schädigt die Wurzeln.

---

## Saisonale Anpassung

Das System passt Gießintervalle automatisch an die Jahreszeit an:

- **Nordhalbkugel**: Winter = Dezember–Februar
- **Südhalbkugel**: Winter = Juni–August

Das effektive Gießintervall berechnet sich in den Wintermonaten als:

```
Effektives Intervall = Basis-Intervall × Winter-Faktor
```

!!! example "Beispiel: Monstera im Winter"
    - Basisintervall (Sommer): 7 Tage
    - Winter-Faktor (`tropical`): 1,5×
    - Effektives Intervall (Winter): 10–11 Tage

---

## Überwinterungsmanagement

!!! warning "Noch nicht implementiert"
    Eine Winterhärte-Ampel (farbige Einstufung nach Frostempfindlichkeit und Klimazone), Frostprognose-gesteuerte Erinnerungen und ein Knollen-Zyklus-Tab werden in einer zukünftigen Version verfügbar sein. Fünf zugehörige Erinnerungstypen (Entblättern, Knollen ausgraben, Lagerkontrolle, Frühjahrs-Auspacken, Winterschutz) sind bereits als Datenmodell angelegt, erzeugen aber noch keine Erinnerungen — es fehlt die Auswertungslogik.

    Für frostempfindliche Freilandpflanzen musst du Ausgrabe- und Einlagerungstermine aktuell selbst im Kalender oder als eigene [Aufgabe](tasks.md) planen.

---

## Freiland-Pflegestile

Ergänzend zu den neun Zimmerpflanzen-Stilen kennt das Datenmodell zehn Freiland-Presets:

<!-- Quelle: src/backend/app/domain/engines/care_reminder_engine.py (CARE_STYLE_PRESETS) -->

| Pflegestil | Gießintervall (Sommer) | Winter-Faktor | Düngung aktiv | Typische Pflanzen |
|-------------|------------------------|----------------|---------------|-------------------|
| `outdoor_annual_veg` | Alle 3 Tage | 1,0× | April–September | Freiland-Gemüse (einjährig) |
| `outdoor_perennial` | Alle 5 Tage | 2,0× | März–September | Stauden |
| `outdoor_annual_ornamental` | Alle 3 Tage | 1,0× | April–September | Stiefmütterchen, Geranie, Lobelie |
| `fruit_tree` | Alle 14 Tage | 1,0× | März–Mai | Apfel, Birne, Kirsche |
| `berry_shrub` | Alle 7 Tage | 1,0× | März–Juni | Himbeere, Johannisbeere, Stachelbeere |
| `rose` | Alle 7 Tage | 1,5× | April–Juli | Beet-, Strauch- und Kletterrosen |
| `frost_tender_tuber` | Alle 5 Tage | 5,0× | Mai–August | Dahlie, Gladiole, Canna |
| `frost_tender_container` | Alle 5 Tage | 4,0× | April–September | Oleander, Zitrus, Olive |
| `winter_vegetable` | Alle 7 Tage | 2,0× | August–September | Grünkohl, Feldsalat, Winterportulak |
| `spring_bulb` | Alle 14 Tage | 1,0× | März–Mai | Tulpe, Narzisse, Krokus |

!!! info "Nur über die API auswählbar"
    Diese zehn Freiland-Presets stehen aktuell **nicht** im Auswahlfeld „Pflegestil" des Pflegeprofil-Dialogs zur Verfügung — die Oberfläche bietet nur die neun Zimmerpflanzen-Stile aus der obigen Tabelle. Ebenso ordnet die automatische Familienzuordnung (siehe unten) keiner Pflanze einen Freiland-Stil zu. Ein Freiland-Preset lässt sich aktuell ausschließlich über die technische API setzen.

---

## Familienbasierte Pflegezuordnung

Das System kennt die Pflegeanforderungen von 10 Pflanzenfamilien und ordnet neuen Pflanzen automatisch den passenden Care Style zu:

<!-- Quelle: src/backend/app/domain/engines/care_reminder_engine.py (FAMILY_CARE_MAP) -->

| Familie | Auto-Stil |
|---------|-----------|
| Araceae (Aronstabgewächse) | `tropical` |
| Marantaceae (Marantengewächse) | `calathea` |
| Orchidaceae (Orchideen) | `orchid` |
| Cactaceae (Kakteengewächse) | `cactus` |
| Crassulaceae (Dickblattgewächse) | `succulent` |
| Asphodelaceae (Affodillgewächse) | `succulent` |
| Polypodiaceae (Tüpfelfarngewächse) | `fern` |
| Lamiaceae (Lippenblütengewächse) | `herb_tropical` |
| Oleaceae (Ölbaumgewächse) | `mediterranean` |
| Moraceae (Maulbeergewächse) | `tropical` |

Für alle nicht gelisteten Familien greift der Fallback-Stil `tropical`, sofern keine artspezifische Gießanleitung (Watering-Guide) vorliegt.

!!! tip "Automatische Zuweisung"
    Wenn du eine neue Pflanzinstanz anlegst, weist das System automatisch den passenden Care Style basierend auf der botanischen Familie zu. Du kannst den Stil jederzeit manuell überschreiben.

---

## Häufige Fragen

??? question "Die Erinnerung erscheint zu spät — kann ich das anpassen?"
    Ja. Öffne das Pflegeprofil der Pflanze und reduziere das Intervall über den Schieberegler. Alternativ wird das System nach ein paar Bestätigungen das Muster erkennen und das Intervall automatisch anpassen.

??? question "Ich habe eine Pflanze vergessen zu gießen — wie setze ich den Zähler zurück?"
    Bestätige die Pflege manuell über **Erledigt** in der Aufgaben-Übersicht (Quelle „Pflege"). Das System setzt den Zeitpunkt auf „jetzt" zurück, egal wie lange die letzte Bestätigung zurückliegt.

??? question "Warum bekomme ich im Dezember keine Düngeerinnerung für meine Monstera?"
    Richtig so — Monstera (`tropical`) hat den Dünge-Aktiv-Zeitraum März–September. Im Dezember ist dieser Zeitraum abgelaufen, da Zimmerpflanzen im Winter bei geringem Licht keine Nährstoffe aufnehmen können.

??? question "Was ist der Unterschied zwischen „Später" und „Überspringen"?"
    „Später" (Snooze) verschiebt eine Pflegeerinnerung um einen Tag, ohne den Zeitpunkt deiner letzten Bestätigung zu verändern — die Erinnerung kommt am nächsten Tag wieder. Ein „Überspringen" wie bei regulären Aufgaben gibt es für Pflegeerinnerungen aktuell nicht; nutze dafür „Später" oder bestätige die Pflege regulär.

---

## Siehe auch

- [Aufgaben](tasks.md)
- [Pflanzdurchläufe](planting-runs.md)
- [Wachstumsphasen](growth-phases.md)
- [Kalender](calendar.md)
