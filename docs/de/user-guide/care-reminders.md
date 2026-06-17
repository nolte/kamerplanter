# Pflegeerinnerungen

Kamerplanter erinnert dich automatisch daran, welche Pflanzen heute Wasser, Dünger oder Pflege brauchen — ohne dass du Cron-Ausdrücke oder Workflow-Templates kennen musst. Ein Fingertipp genügt zur Bestätigung. Das System lernt aus deinem Pflegeverhalten und passt Intervalle automatisch an.

---

## Voraussetzungen

- Mindestens eine Pflanze ist angelegt
- Der Pflanzinstanz wurde ein Care Profile (Pflegeprofil) zugewiesen (wird automatisch beim ersten Zugriff erstellt)

---

## Der Pflege-Kalender

Navigiere zu **Pflege** > **Heute fällig**, um alle Pflanzen zu sehen, die heute Aufmerksamkeit brauchen. Die Karten sind nach Dringlichkeit sortiert:

| Farbe | Bedeutung |
|-------|-----------|
| Rot | Überfällig (Pflanze leidet möglicherweise) |
| Orange | Heute fällig |
| Gelb | Bald fällig (1–2 Tage) |
| Grün | Kürzlich gepflegt |

### Pflege bestätigen

1. Klicke auf die Pflegekarte der Pflanze
2. Klicke auf den großen **Erledigt**-Button
3. Fertig — das System merkt sich den Zeitpunkt und berechnet den nächsten Termin

!!! tip "Adaptives Lernen"
    Wenn du eine Pflanze konsequent 8 statt 7 Tage nach der letzten Bestätigung gießt, passt das System das Intervall nach 3 aufeinanderfolgenden Bestätigungen automatisch an. Der Lerneffekt ist auf ±1 Tag pro Schritt begrenzt und kann das Intervall maximal um ±30% verändern.

---

## Care Profiles

Jede Pflanze hat ein **Care Profile** (Pflegeprofil) mit den Pflegeintervallen für diese spezifische Pflanze. Das Profil wird automatisch aus den Stammdaten der Art generiert und kann danach angepasst werden.

### Care Profile öffnen

1. Navigiere zu **Pflanzen** > gewünschte Pflanze
2. Klicke auf den Tab **Pflege**
3. Klicke auf **Care Profile bearbeiten**

### Pflege-Stile (Care Style Presets)

Das System kennt vordefinierte Pflege-Stile für typische Pflanzengruppen:

| Pflege-Stil | Gießen (Sommer) | Winter-Faktor | Typische Pflanzen |
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
    Kakteen (Cactaceae) und Sukkulenten wie Echeveria oder Haworthia gehören verschiedenen Familien an. Der Pflege-Stil `cactus` gilt nur für echte Kakteen. Echeveria und Haworthia nutzen `succulent`. Lithops und andere Mesembs (Aizoaceae) brauchen eine noch spezifischere Logik und sollten mit `custom` konfiguriert werden.

### Gießhinweise

Das Care Profile zeigt nicht nur *wann*, sondern auch *wie* gegossen werden soll:

| Pflege-Stil | Gießmethode |
|-------------|-------------|
| `tropical` | Von oben gießen, bis Wasser unten herausläuft. Überschuss nach 30 Min. wegkippen. |
| `orchid` | Tauchbad: Topf 10–15 Min. in zimmerwarmes Wasser, dann abtropfen lassen. |
| `calathea` | Von oben mit kalkarmem Wasser gießen. Blätter nicht benetzen. |
| `cactus` | Kräftig durchgießen, vollständig austrocknen lassen. |

!!! info "Wasserqualität"
    Für Calatheen und Orchideen empfiehlt das System Regenwasser oder gefiltertes Wasser — diese Pflanzen reagieren empfindlich auf Kalk im Leitungswasser (braune Blattspitzen).

---

## Automatische Erinnerungstypen

Das System generiert täglich Erinnerungen für folgende Pflegeaufgaben:

| Erinnerungstyp | Auslöser | Priorität |
|----------------|---------|------------|
| **Gießen** | Intervall seit letzter Bestätigung | Hoch |
| **Düngen** | Intervall + nur in Aktivmonaten | Mittel |
| **Umtopfen** | Monate seit letztem Umtopfen | Niedrig |
| **Schädlingskontrolle** | Festes Intervall (Standard: 14 Tage) | Mittel |
| **Standort-Check** | Saisonal: Oktober + März | Mittel |
| **Luftfeuchte-Check** | Heizperiode (Okt–März) | Mittel |
| **Winterschutz** | Oktober (Nordhalbkugel) | Hoch |
| **Frühjahrs-Auspacken** | März (Nordhalbkugel) | Hoch |
| **Knollen ausgraben** | Vor erstem Frost (Oktober) | Kritisch |

### Dünge-Schutz (Dormanz-Guard)

Düngungs-Erinnerungen werden **nicht** generiert, wenn:
- Der aktuelle Monat außerhalb der `Aktivmonate` des Pflege-Stils liegt (z.B. November–Februar für die meisten Zimmerpflanzen)
- Die Pflanze sich in einer Ruhephase befindet (Winterruhe, Seneszenz, Abhärtungsphase)

!!! tip "Warum kein Dünger im Winter?"
    Bei reduziertem Licht im Winter sinkt die Photosynthese-Rate. Zimmerpflanzen können die Nährstoffe nicht verwerten — Dünger akkumuliert als Salz im Substrat und schädigt die Wurzeln.

---

## Saisonale Anpassung

Das System passt Gießintervalle automatisch an die Jahreszeit an:

- **Nordhalbkugel**: Winter = November–Februar, Sommer = Mai–August
- **Südhalbkugel**: Winter = Mai–August, Sommer = November–Februar

Die Hemisphäre wird aus dem Standort der Pflanze abgeleitet (`Site.hemisphere`). Das effektive Gießintervall berechnet sich als:

```
Effektives Intervall = Basis-Intervall × Winter-Faktor
```

!!! example "Beispiel: Monstera im Winter"
    - Basis-Intervall (Sommer): 7 Tage
    - Winter-Faktor (`tropical`): 1,5×
    - Effektives Intervall (Winter): 10–11 Tage

---

## Überwinterungsmanagement

Für Pflanzen, die Winterschutz brauchen, bietet Kamerplanter ein vollständiges Überwinterungs-System.

### Winterhärte-Ampel

Jede Pflanze bekommt eine farbige Bewertung basierend auf ihrer Frostempfindlichkeit und deiner Klimazone:

| Ampel | Bedeutung | Typische Pflanzen |
|-------|-----------|-------------------|
| Grün | Winterhart — kein Schutz nötig | Stachelbeere, Apfelbaum, Tulpen |
| Gelb | Schutzbedürftig — Mulch oder Vlies | Rosen, Lavendel, Stauden |
| Rot | Muss frostfrei überwintern | Oleander, Zitrus, Dahlien |

!!! warning "Dahlien und Knollen"
    Dahlien, Gladiolen und Canna müssen vor dem ersten Frost ausgegraben werden. Das System sendet eine **Kritische Erinnerung** mit dem Knollen-Ausgraben-Hinweis, sobald die Temperaturprognose auf Frost hinweist.

### Knollen-Zyklus verfolgen

Für Pflanzen mit Knollen oder Zwiebeln (Dahlien, Gladiolen, Canna, Tulpen) kannst du den vollständigen Jahreszyklus dokumentieren:

1. Auspflanzen → Blühen → Ausgraben → Trocknen → Einlagern → Kontrollieren → Vorziehen

Navigiere zu **Pflanzen** > gewünschte Pflanze > Tab **Überwinterung**, um den Status zu verwalten.

### Freiland-Pflege-Stile

Ergänzend zu den Zimmerpflanzen-Stilen gibt es Presets für Freilandpflanzen:

| Pflege-Stil | Winter-Aktion | Typische Pflanzen |
|-------------|--------------|-------------------|
| `outdoor_perennial` | Winterschutz prüfen (Mulch, Vlies) | Rittersporn, Phlox, Stauden |
| `frost_tender_tuber` | AUSGRABEN + frostfrei lagern | Dahlie, Gladiole, Canna |
| `frost_tender_container` | Ins Winterquartier (5–12°C, hell) | Oleander, Zitrus, Olive |
| `fruit_tree` | Kalkanstrich, Stammschutz | Apfel, Birne, Kirsche |
| `spring_bulb` | Im Boden lassen (winterhart) | Tulpe, Narzisse, Krokus |

---

## Familienbasierte Pflegezuordnung

Das System kennt die Pflegeanforderungen von 10 Pflanzenfamilien und ordnet neue Pflanzen automatisch dem passenden Care Style zu:

| Familie | Auto-Stil |
|---------|-----------|
| Araceae (Aronstabgewächse) | `tropical` |
| Cactaceae (Kakteengewächse) | `cactus` |
| Marantaceae (Marantengewächse) | `calathea` |
| Orchidaceae (Orchideen) | `orchid` |
| Crassulaceae (Dickblattgewächse) | `succulent` |
| Asphodelaceae (Affodillgewächse) | `succulent` |
| Lamiaceae (Lippenblütengewächse) | `mediterranean` |
| Polypodiaceae / Pteridaceae (Farne) | `fern` |
| Liliaceae / Amaryllidaceae (Liliengewächse) | `outdoor_perennial` |
| Solanaceae (Nachtschattengewächse) | `outdoor_annual_veg` |

!!! tip "Automatische Zuweisung"
    Wenn du eine neue Pflanzinstanz anlegst, weist das System automatisch den passenden Care Style basierend auf der botanischen Familie zu. Du kannst den Stil jederzeit manuell überschreiben.

---

## Benachrichtigungskanäle

Kamerplanter stellt Pflegeerinnerungen über konfigurierbare Kanäle zu. Die Einstellungen befinden sich unter **Einstellungen** > **Benachrichtigungen**.

| Kanal | `channel_key` | Beschreibung | Konfiguration erforderlich |
|-------|---------------|--------------|---------------------------|
| **E-Mail** | `email` | Tägliche Zusammenfassung und dringende Erinnerungen per E-Mail | Keine (immer aktiv, sofern eine E-Mail-Adresse hinterlegt ist) |
| **Browser Push (PWA)** | `pwa` | Web-Push-Benachrichtigungen direkt im Browser oder als installierte PWA | Gerätespezifisch — siehe unten |

### Browser Push (PWA) aktivieren

Der Browser-Push-Kanal ist **pro Gerät** aktiviert. Jedes Gerät (Smartphone, Tablet, Desktop-Browser) muss einzeln abonniert werden.

1. Öffne **Einstellungen** > **Benachrichtigungen**
2. Klicke auf **Auf diesem Gerät aktivieren** neben "Browser Push"
3. Der Browser fragt nach der Berechtigung für Benachrichtigungen — klicke **Zulassen**
4. Das Gerät ist jetzt abonniert und empfängt Erinnerungen
5. Klicke auf **Test senden**, um die Verbindung zu überprüfen

!!! note "Browser-Kompatibilität"
    Browser Push funktioniert mit aktuellen Chromium-basierten Browsern (Chrome, Edge, Brave) und Firefox. Safari unter iOS erfordert iOS 16.4+ und dass die App als PWA zum Startbildschirm hinzugefügt wurde. Die Seite muss über **HTTPS** ausgeliefert werden — auf `http://localhost` ist Push nur zu Entwicklungszwecken verfügbar.

!!! warning "\"Nicht konfiguriert\" nach dem Aktivieren"
    Zeigt der Kanal trotz Aktivierung den Status **Nicht konfiguriert**, wurden die VAPID-Schlüssel vom Betreiber der Instanz noch nicht gesetzt. Bitte wende dich an den Administrator. Für selbst gehostete Instanzen: siehe [Umgebungsvariablen — Browser Push (VAPID)](../reference/environment-variables.md#browser-push-pwa-vapid).

### Tägliche Zusammenfassung und Ruhezeiten

Die Einstellung **Tägliche Zusammenfassung** (Uhrzeit) und **Ruhezeiten** (z.B. 22:00–07:00) gelten für alle Kanäle gleichermaßen — also auch für Browser Push. Dringende Erinnerungen (Kritisch, z.B. Knollen ausgraben vor Frost) ignorieren die Ruhezeiten.

---

## Häufige Fragen

??? question "Die Erinnerung erscheint zu spät — kann ich das anpassen?"
    Ja. Öffne das Care Profile der Pflanze und reduziere das Intervall. Alternativ wird das System nach ein paar Bestätigungen das Muster erkennen und das Intervall automatisch anpassen.

??? question "Ich habe eine Pflanze vergessen zu gießen — wie setze ich den Zähler zurück?"
    Bestätige die Pflege manuell im Pflege-Dashboard. Das System setzt den Timer auf "jetzt" zurück, egal wie lange die letzte Bestätigung zurückliegt.

??? question "Warum bekomme ich im Dezember keine Dünge-Erinnerung für meine Monstera?"
    Richtig so — Monstera (care_style: `tropical`) bekommt den Dünge-Aktiv-Zeitraum März–Oktober. Im Dezember ist dieser Zeitraum abgelaufen, da Zimmerpflanzen im Winter bei geringem Licht keine Nährstoffe aufnehmen können.

??? question "Meine Dahlie hat eine grüne Ampel — aber ich weiß, dass sie Schutz braucht."
    Die Ampel berechnet sich aus dem `frost_sensitivity`-Wert der Art UND deiner Klimazone. Prüfe, ob die richtige Klimazone bei deinem Standort eingestellt ist. Du kannst den Care Style auch manuell auf `frost_tender_tuber` setzen.

---

## Siehe auch

- [Pflanzdurchläufe](planting-runs.md)
- [Wachstumsphasen](growth-phases.md)
- [Standorte & Substrate](locations-substrates.md)
- [Kalender](calendar.md)
