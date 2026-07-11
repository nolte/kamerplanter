# Aquaponik

Aquaponik verbindet Fischhaltung und Pflanzenanbau in einem geschlossenen Wasserkreislauf: Deine Fische liefern über ihre Ausscheidungen den Dünger für die Pflanzen, die Pflanzen reinigen im Gegenzug das Wasser für die Fische. Auf dieser Seite legst du ein Aquaponik-System an, überwachst den Stickstoffkreislauf und behältst die für die Fischsicherheit entscheidenden Wasserwerte im Blick. <!-- REQ-026 -->

---

## Was ist Aquaponik?

In einem Aquaponik-System leben Fische in einem Tank, dessen Wasser durch einen Biofilter (ein Behälter mit nützlichen Bakterien) und ein Pflanzenbeet (Growbed) zirkuliert, bevor es zu den Fischen zurückfließt. Die Fischausscheidungen enthalten Ammoniak, das über zwei Bakteriengruppen im Biofilter in pflanzenverfügbaren Dünger umgewandelt wird — diesen Prozess nennt man **Stickstoffkreislauf** (siehe unten). Die Pflanzen nehmen den entstandenen Dünger auf und filtern damit gleichzeitig das Wasser, sodass die Fische darin gesund bleiben.

Kamerplanter unterscheidet fünf Systemtypen, je nachdem wie Fischtank, Biofilter und Growbed miteinander verbunden sind:

| Systemtyp | Beschreibung | Geeignet für |
|-----------|-------------|-------------|
| **Media-Bed** | Growbed mit Blähton, das gleichzeitig als Biofilter dient — kein separater Biofilter nötig | Einsteiger, Hobby-Anlagen |
| **Deep Water Culture (DWC)** | Pflanzen schwimmen auf Flößen in einem separaten Wasserbecken | Salat, Kräuter |
| **Nutrient Film Technique (NFT)** | Ein dünner Wasserfilm fließt über die Wurzeln | Kräuter, Blattgemüse |
| **Hybrid** | Kombination aus Media-Bed und DWC/NFT | Fortgeschrittene Anlagen |
| **Wicking-Bed** | Dochtbewässerung aus einem Reservoir | Outdoor, robuste Anlagen |

DWC, NFT, Hybrid und Wicking-Bed benötigen jeweils einen **separaten Biofilter**, da hier kein Substrat vorhanden ist, das die Bakterien beherbergen könnte. Nur beim Media-Bed übernimmt das Blähton-Substrat diese Funktion mit.

---

## Der Stickstoffkreislauf einfach erklärt

Der Stickstoffkreislauf ist das biologische Herzstück jedes Aquaponik-Systems. Er läuft in drei Schritten ab:

1. **Ammoniak (TAN)** — Fische scheiden über Kiemen und Urin Ammoniak aus. Kamerplanter erfasst diesen Wert als **TAN** (*Total Ammonia Nitrogen*, Gesamt-Ammonium-Stickstoff).
2. **Nitrit (NO₂⁻)** — Eine erste Bakteriengruppe (*Nitrosomonas*) im Biofilter wandelt Ammoniak zu Nitrit um. Nitrit ist ebenfalls giftig für Fische, weil es die Sauerstoffaufnahme im Blut blockiert.
3. **Nitrat (NO₃⁻)** — Eine zweite Bakteriengruppe (*Nitrobacter*/*Nitrospira*) wandelt Nitrit zu Nitrat um. Nitrat ist für Fische weitgehend ungiftig und der wichtigste Stickstoffdünger für deine Pflanzen.

!!! danger "TAN und freies Ammoniak sind nicht dasselbe"
    Der gemessene TAN-Wert besteht aus zwei Formen: dem harmlosen Ammonium (NH₄⁺) und dem hochgiftigen freien Ammoniak (NH₃). Wie viel davon als giftiges NH₃ vorliegt, hängt stark von **pH-Wert und Wassertemperatur** ab — bei hohem pH und hoher Temperatur ist ein deutlich größerer Anteil giftig, selbst wenn der TAN-Wert gleich bleibt. Kamerplanter berechnet das **freie Ammoniak** automatisch aus deinem TAN-, pH- und Temperatur-Messwert. Der sichere Grenzwert für freies Ammoniak liegt bei **unter 0,02 mg/L** — darüber wird es für deine Fische lebensgefährlich.

---

## Voraussetzungen

- Mindestens ein Standort ist angelegt (das Aquaponik-System wird darüber verwaltet).
- Aquaponik ist ein Experten-Funktionsbereich und standardmäßig ausgeblendet. Stelle deine [Erfahrungsstufe](onboarding.md) auf **Experte** oder blende das Modul **Aquaponik** unter [Module & Funktionen](module-visibility.md) manuell ein.
- Zum Anlegen und Bearbeiten von Systemen, Wassertests, Fischbeständen und Fütterungen benötigst du mindestens die Mandantenrolle **Grower** (siehe [Mandanten & Gärten](tenants.md)).

---

## Ein neues Aquaponik-System anlegen

### Schritt 1: Zur Aquaponik-Übersicht navigieren

Klicke in der Navigation auf **Aquaponik**. Du siehst eine Liste deiner bisherigen Systeme (zu Beginn leer) sowie den Button **System anlegen**.

### Schritt 2: Grunddaten eintragen

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Bezeichnung des Systems | „Tilapia-Salat DWC" |
| Systemtyp | Einer der fünf Systemtypen (siehe oben) | Deep Water Culture (DWC) |
| Gesamtwasservolumen | Wasservolumen aller Tanks zusammen, in Litern | 630 |
| Anbaufläche | Gesamte Growbed-Fläche in m² | 4 |

### Schritt 3: Biofilter & Betrieb konfigurieren

Diese Werte legen fest, wie das System den Stickstoffkreislauf verarbeitet und in welchem pH-Bereich es betrieben werden soll.

| Feld | Beschreibung |
|------|-------------|
| Biofiltertyp | Bei DWC, NFT, Hybrid und Wicking-Bed pflichtig — bei Media-Bed optional, weil das Substrat den Biofilter integriert. Zur Auswahl stehen: Integriert (Blähton), MBBR (K1-Medien), Rieselfilter (Lava) und Wirbelbett (Sand). |
| Soll-Futtermenge pro Tag | Deine geplante tägliche Futtermenge in Gramm — dient als Referenzwert für spätere Auswertungen |
| pH-Zielbereich (min/max) | Voreingestellt auf 6,8–7,2 |

!!! info "Warum der pH-Zielbereich ein Kompromiss ist"
    Fische bevorzugen pH 7,0–8,0, Pflanzen nehmen Nährstoffe am besten bei pH 5,5–6,5 auf, und die Nitrifikationsbakterien im Biofilter arbeiten optimal bei pH 7,0–8,0. Der Standardbereich 6,8–7,2 ist ein Kompromiss, der allen drei Systemkomponenten ausreichend gerecht wird.

### Schritt 4: Notizen und Speichern

Optional kannst du Freitext-Notizen hinterlegen (z. B. Herstellerangaben zum Filter). Klicke abschließend auf **Speichern** — das System erscheint sofort in deiner Übersicht.

---

## Biofilter-Cycling: dein System einfahren

Bevor du Fische in voller Besatzdichte einsetzen kannst, muss sich im Biofilter eine Bakterienkultur aufbauen, die Ammoniak zuverlässig zu Nitrat abbaut. Diesen Vorgang nennt man **Cycling** (Einfahren) — er dauert in der Regel **4–8 Wochen**.

Kamerplanter zeigt dir für jedes System den aktuellen Cycling-Status:

| Status | Bedeutung | Fische erlaubt? |
|--------|-----------|-----------------|
| **Neu** | Biofilter frisch befüllt, noch keine Bakterien vorhanden | Nein — nur als Ammoniakquelle für das Einfahren |
| **Fährt ein** | Bakterien bauen sich auf; typische Ammoniak- und Nitrit-Spitzen | Nur wenige, robuste Fische (höchstens 25 % der Zielbesatzdichte) |
| **Eingefahren** | Stabile Nitrifikation, keine Spitzen mehr messbar | Ja, volle Besatzdichte |
| **Winterruhe** | Bakterien sind bei Wassertemperaturen unter 10 °C inaktiv | Reduziert — das System muss im Frühling erneut einfahren |

In der System-Detailansicht siehst du den **Einfahrfortschritt** als Fortschrittsbalken mit begleitendem Text. Als eingefahren gilt der Biofilter, wenn TAN unter 0,25 mg/L **und** Nitrit unter 0,1 mg/L an **7 aufeinanderfolgenden Tagen** gemessen wurden.

!!! warning "Keine Fische vor dem Einfahren einsetzen"
    Setzt du Fische ein, bevor der Biofilter eingefahren ist, drohen Ammoniak- und Nitrit-Spitzen, die für die Tiere lebensgefährlich sind. Starte neue Anlagen wenn möglich **fischlos** (mit einer reinen Ammoniakquelle) oder mit nur wenigen, robusten Fischen und engmaschiger Wasserkontrolle.

---

## Wassertests erfassen und die Werte verstehen

Regelmäßige Wassertests sind die wichtigste Routine in der Aquaponik — sie zeigen dir frühzeitig, ob der Stickstoffkreislauf funktioniert und ob die Werte für deine Fische sicher sind.

### Schritt 1: Wassertest erfassen

Öffne ein System und klicke auf **Wassertest erfassen**.

### Schritt 2: Stickstoffkreislauf-Werte eintragen

Diese Werte entscheiden über die Sicherheit deiner Fische — Ammoniak und Nitrit sollten nach dem Einfahren bei 0 liegen.

| Feld | Bedeutung | Richtwert |
|------|-----------|----------|
| Ammoniak (TAN) | Gesamt-Ammonium-Stickstoff — Fischabfall, aus dem der Kreislauf startet | 0–0,5 mg/L (0 nach dem Einfahren) |
| Nitrit | Giftiges Zwischenprodukt des Stickstoffkreislaufs | 0–0,1 mg/L (0 nach dem Einfahren) |
| Nitrat | Ungiftiges Endprodukt, wichtigster Pflanzendünger im System | 5–150 mg/L (systemabhängig) |
| pH-Wert | Säuregrad des Wassers, beeinflusst zusammen mit der Temperatur den Anteil des giftigen freien Ammoniaks | 6,8–7,2 (Standardbereich) |

### Schritt 3: Weitere Wasserwerte eintragen

| Feld | Bedeutung | Richtwert |
|------|-----------|----------|
| Wassertemperatur | Beeinflusst Fischstoffwechsel, Sauerstofflöslichkeit und Ammoniak-Toxizität | Fisch- und pflanzenabhängig |
| Gelöstsauerstoff | Sauerstoffgehalt im Wasser — Fische und Biofilterbakterien brauchen ihn zum Atmen | 5–9 mg/L |
| Karbonathärte (KH) | Puffert das Wasser gegen plötzliche pH-Stürze | Ab 4 °dH sicher, darunter droht ein pH-Crash |
| Eisen | Häufigstes Nährstoffdefizit in Aquaponik-Systemen | 2–5 ppm |

### Schritt 4: Quelle wählen und speichern

Wähle, wie du die Werte ermittelt hast (**Manuell**, **Sensor** oder **Test-Kit**), ergänze optional Notizen und speichere. Der Test erscheint sofort in der Verlaufsansicht.

!!! note "Freies Ammoniak wird automatisch berechnet"
    Du trägst nur den TAN-Wert ein — Kamerplanter berechnet daraus zusammen mit pH-Wert und Temperatur automatisch den Anteil des giftigen **freien Ammoniaks** und zeigt ihn als eigenen Messwert in der Wasserqualitäts-Übersicht an.

### Wasserqualität auf einen Blick

In der System-Detailansicht siehst du alle zuletzt gemessenen Werte als farbige Chips mit Symbol:

| Farbe & Symbol | Bedeutung |
|-----------------|-----------|
| Grün, Häkchen | Wert im sicheren Bereich |
| Blau, Info-Symbol | Wert außerhalb des Optimalbereichs, aber unkritisch |
| Gelb/Orange, Warndreieck | Wert im Stressbereich für deine Fischart — beobachten und ggf. gegensteuern |
| Rot, Ausrufezeichen | Kritischer Wert — sofortiges Handeln nötig |

Kritische Werte werden zusätzlich als auffällige Warnmeldung oben in der System-Detailansicht angezeigt.

!!! danger "Ammoniak-Spitze — was tun?"
    Zeigt dir Kamerplanter einen kritischen Ammoniak- oder Nitrit-Wert an, handle sofort:

    1. **Fütterung stoppen**, bis sich die Werte erholt haben.
    2. **Teilwasserwechsel** durchführen (maximal 20 % des Systemvolumens auf einmal).
    3. **Belüftung maximieren** — mehr gelöster Sauerstoff mindert die Giftwirkung von Ammoniak.

    Mögliche Ursachen sind Überfütterung, ein toter Fisch im Tank oder ein Biofilter-Ausfall (z. B. durch Chlor oder Medikamentenreste im Wasser).

!!! danger "Niemals Säuren zur pH-Absenkung verwenden"
    In Aquaponik-Systemen darfst du **keine Säuren** als pH-Senker einsetzen — sie können deine Fische und die Biofilterbakterien schädigen. Der pH-Wert sinkt durch die Nitrifikation ohnehin von selbst; ist er zu hoch, ist meist Abwarten die richtige Maßnahme. Muss der pH-Wert angehoben werden, geschieht das mit Kaliumhydroxid (KOH) oder Calciumhydroxid (Ca(OH)₂) im Wechsel — das versorgt die Pflanzen gleichzeitig mit Kalium und Calcium.

---

## Fischbestand und Fütterung

In der System-Detailansicht siehst du eine Übersicht deines aktuellen Fischbestands: Name, Anzahl und geschätzte Gesamtbiomasse je Bestand. Die Fischarten stammen aus einem globalen Artenkatalog mit artspezifischen Grenzwerten für Temperatur, pH, Sauerstoff, Ammoniak und Nitrit.

<!-- Quelle: src/backend/app/migrations/seed_data/fish_species.yaml (8 Fischarten) -->

| Fischart | Temperaturzone | Optimaltemperatur |
|----------|-----------------|-------------------|
| Nil-Tilapia | Warmwasser | 26–30 °C |
| Regenbogenforelle | Kaltwasser | 12–16 °C |
| Karpfen / Koi | Temperiert | 20–28 °C |
| Europäischer Wels | Temperiert | 20–26 °C |
| Europäischer Flussbarsch | Temperiert | 18–24 °C |
| Goldfisch | Temperiert | 18–22 °C |
| Zander | Temperiert | 18–22 °C |
| Seesaibling | Kaltwasser | 8–14 °C |

!!! tip "Fischart passend zur gewünschten Pflanzenauswahl wählen"
    Die Wassertemperatur muss zu Fischen **und** Pflanzen passen. Warmwasserfische wie Tilapia harmonieren mit Fruchtgemüse (Tomaten, Paprika, Basilikum), Kaltwasserfische wie Forelle eher mit Blattsalaten und Kräutern, die eine kühlere Wurzelzone vertragen.

Das Anlegen eines neuen Fischbestands sowie das Erfassen von Fütterungen und Verlusten (Mortalität) sind derzeit **noch nicht** über die Bedienoberfläche möglich — siehe den Abschnitt für technische Nutzer unten.

---

## Für technische Nutzer / Self-Hoster

Die folgenden Funktionen sind im Backend bereits vollständig implementiert, aber noch **ohne Bedienoberfläche** — du erreichst sie aktuell nur über die REST-API. Schreibende Aufrufe erfordern mindestens die Mandantenrolle **Grower** (Löschen eines Systems: **Admin**).

!!! info "Nur über API: Fischbestand verwalten"
    `POST /aquaponics/systems/{key}/fish-stocks` legt einen neuen Fischbestand an, `PATCH`/`DELETE` auf derselben Route bearbeiten oder entfernen ihn. `POST .../fish-stocks/{stock_key}/mortality` erfasst Verluste. `GET .../biomass-history` und `GET .../mortality-rate` liefern die jeweilige Verlaufsauswertung.

!!! info "Nur über API: Fütterung protokollieren und auswerten"
    `POST /aquaponics/systems/{key}/feeding-events` protokolliert eine Fütterung, `GET` auf derselben Route listet die Historie. `GET .../feeding-recommendation` liefert eine temperaturkorrigierte Tages-Empfehlung je nach Fischart, Biomasse und Cycling-Status. `GET .../fcr-analysis` wertet das Futterverwertungsverhältnis (*Feed Conversion Ratio*, FCR) über einen Zeitraum aus.

!!! info "Nur über API: Nährstoffdefizite und Supplementierung"
    `GET /aquaponics/systems/{key}/deficiency-check` prüft, ob Eisen, Kalium, Calcium und weitere Nährstoffe im Mangelbereich liegen. `POST`/`GET .../supplementation` protokolliert bzw. listet Ergänzungsmittel-Gaben (z. B. Fe-DTPA, Kaliumhydroxid).

!!! info "Nur über API: Sicherheits- und Gesundheitsstatus"
    `GET /aquaponics/systems/{key}/safety-status` fasst zusammen, ob alle Wasserwerte im fischsicheren Bereich liegen. `GET .../fish-health` liefert artspezifische Gesundheitswarnungen samt Handlungsempfehlung. `GET .../alerts` liefert dieselben Wasserqualitäts-Bewertungen, die auch in der Detailansicht als Chips angezeigt werden, als Rohdaten.

!!! info "Nur über API: Cycling-Status manuell setzen und Verlaufsdiagramm"
    `POST /aquaponics/systems/{key}/cycling-status` überschreibt den automatisch erkannten Einfahrstatus manuell. `GET .../nitrogen-cycle-chart` liefert den Ammoniak-/Nitrit-/Nitrat-Verlauf über die Zeit als Datenreihe für eigene Auswertungen.

!!! info "Nur über API: Systemdaten bearbeiten oder löschen"
    `PATCH /aquaponics/systems/{key}` bearbeitet die Grunddaten eines bestehenden Systems. `DELETE /aquaponics/systems/{key}` löscht es unwiderruflich — dafür ist die Mandantenrolle **Admin** erforderlich.

Der globale, mandantenunabhängige Fischarten-Katalog (Temperaturzonen, artspezifische Grenzwerte, Fisch-Pflanzen-Kompatibilität) steht unter `GET /fish-species` sowie `GET /fish-species/{species_key}/compatible-plants` zur Verfügung.

---

## Häufige Fragen

??? question "Warum sehe ich Aquaponik nicht in der Navigation?"
    Aquaponik ist ein Experten-Funktionsbereich und standardmäßig ausgeblendet. Stelle deine Erfahrungsstufe auf **Experte** oder blende das Modul unter [Module & Funktionen](module-visibility.md) manuell ein.

??? question "Wie lange dauert das Einfahren eines neuen Systems?"
    In der Regel 4–8 Wochen, abhängig von der Wassertemperatur. Bei Wassertemperaturen unter 15 °C dauert es deutlich länger, da sich die Bakterienkultur langsamer aufbaut.

??? question "Kann ich vorhandene Tanks aus dem Tankmanagement in einem Aquaponik-System nutzen?"
    Fischtank, Biofilter, Sump und weitere Tank-Rollen eines Aquaponik-Systems bauen auf der bestehenden [Tankmanagement](tanks.md)-Infrastruktur auf. Die konkrete Verknüpfung einzelner Tanks zu einem Aquaponik-System ist aktuell nur über die API möglich.

??? question "Was mache ich, wenn der pH-Wert zu niedrig ist?"
    Ein zu niedriger pH-Wert (unter 6,5) kann bei geringer Karbonathärte (KH) auf einen drohenden pH-Crash hindeuten — sinkt die Alkalinität unter 4 °dH, kann der pH-Wert abrupt einbrechen, was die Biofilterbakterien schädigt. Puffere in diesem Fall mit Kaliumhydroxid (KOH) oder Calciumhydroxid (Ca(OH)₂) nach.

---

## Siehe auch

- [Tankmanagement](tanks.md)
- [Sensorik](sensors.md)
- [Dünge-Logik](fertilization.md)
- [Standorte und Substrate](locations-substrates.md)
