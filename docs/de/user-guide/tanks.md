# Tankmanagement

Tanks verwalten deine Wassertanks, Nährstoffreservoirs und Gießwasserbehälter. Du erfasst Füllstände, dokumentierst Befüllungen mit vollständigen Mischrezepten und planst Wartungsarbeiten wie Wasserwechsel und Sonden-Kalibrierungen.

---

## Voraussetzungen

- Mindestens eine angelegte Location (Tanks werden einer Location zugeordnet)
- Für EC-gesteuerte Befüllungen: Nährstoffpläne unter **Düngung** angelegt

---

## Tank-Typen verstehen

Kamerplanter unterscheidet fünf Tank-Typen:

| Typ | Beschreibung | Typische Verwendung |
|-----|-------------|-------------------|
| **Nährstoff** | Fertig gemischte Nährlösung | Drip-Systeme, Hydroponik |
| **Bewässerung** | Aufbereitetes Wasser, ggf. pH-korrigiert | Erde- und Coco-Kulturen |
| **Reservoir** | Vorratstank für Rohwasser | Regenwassersammler, RO-Wasser |
| **Rezirkulation** | Rücklauftank bei geschlossenen Systemen | NFT, Ebb & Flow |
| **Stammlösung** | Konzentrierte A/B-Tanks | Automatisierte Dosierung |

!!! danger "Stammlösungen niemals direkt mischen"
    Konzentrierte A- und B-Stammlösungen dürfen niemals direkt miteinander in Kontakt kommen — nur über Wasser verdünnt. Kamerplanter warnt beim Anlegen von Stammlösungs-Tanks.

!!! info "Hydroponik-Begriffe: DWC und NFT"
    **DWC** (Deep Water Culture) ist ein Hydroponik-System, bei dem die Wurzeln permanent in einer sauerstoffangereicherten Nährlösung hängen — dafür braucht ein **Nährstoff**-Tank meist eine Luftpumpe (siehe Ausstattung unten) und eine regelmäßige Messung des gelösten Sauerstoffs. **NFT** (Nutrient Film Technique) lässt einen dünnen Nährlösungsfilm über die Wurzeln fließen und wieder in einen **Rezirkulations**-Tank zurücklaufen — hier ist vor allem die Umwälzpumpe entscheidend.

---

## Einen neuen Tank anlegen

### Schritt 1: Zur Tankübersicht navigieren

Klicke in der Navigation auf **Standorte** und öffne eine Site. Im Tab **Tanks** siehst du alle Tanks dieser Site.

Alternativ: Navigiere zu **Standorte → Tanks** für eine site-übergreifende Übersicht.

### Schritt 2: Neuen Tank erstellen

Klicke auf **Tank hinzufügen**.

### Schritt 3: Tank konfigurieren

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Bezeichnung des Tanks | "DWC Reservoir Zelt A" |
| Typ | Tank-Typ (siehe oben) | Nährstoff |
| Volumen (L) | Fassungsvermögen | 100 |
| Material | Kunststoff, Edelstahl, Glas oder IBC-Container | Kunststoff |
| Location | Welchem Bereich ist der Tank zugeordnet? | "Growzelt A" |
| Installationsdatum | Optional, für die Wartungshistorie | 01.03.2026 |
| Notizen | Freitext, z. B. Herstellerhinweise | — |

### Ausstattung (optional)

Beim Anlegen und in der Bearbeitung kannst du zusätzlich per Schalter angeben, welche Ausstattung der Tank hat — sie erscheint als Eigenschafts-Chip auf der Detailseite:

| Ausstattung | Relevanz |
|-------------|---------|
| Deckel | Verdunstungs- und Lichtschutz |
| Luftpumpe | Sauerstoffanreicherung, wichtig für DWC |
| Umwälzpumpe | Zirkulation, wichtig für NFT/Rezirkulation |
| Heizung | Konstante Wassertemperatur |
| Lichtdicht | Verhindert Algenwachstum durch Lichteinfall |
| UV-Sterilisator | Reduziert Pathogene im Wasserkreislauf |
| Ozongenerator | Zusätzliche Desinfektion |

### Schritt 4: Sensoren verknüpfen (optional)

Wenn du einen Sensor für Füllstand, EC, pH oder weitere Wasserwerte im Tank hast, kannst du diesen über **Sensor hinzufügen** (im Bearbeiten-Tab) dem Tank zuordnen. Die aktuellen Sensorwerte erscheinen dann in der Tank-Detailansicht.

!!! tip "Home-Assistant-Entity per Autovervollständigung wählen"
    Im Sensor-Dialog schlägt dir ein Autocomplete-Feld passende Home-Assistant-Entities vor (inklusive aktuellem Zustand). Wählst du eine Entity aus, übernimmt Kamerplanter automatisch die Entity-ID und schlägt passend zum Entity-Typ auch gleich die Messgröße und einen Sensornamen vor. Alternativ trägst du die Entity-ID manuell ein (z. B. `sensor.tank_ec`) oder verknüpfst ein MQTT-Topic.

---

## Aktuellen Tankzustand erfassen

Der Tankzustand gibt Auskunft über den aktuellen Füllstand, EC- und pH-Wert sowie die Wassertemperatur.

### Neuen Messwert eintragen

1. Öffne einen Tank.
2. Klicke auf **Zustand erfassen** (Tab **Messungen**).
3. Trage die aktuellen Werte ein:

| Parameter | Beschreibung |
|-----------|-------------|
| pH-Wert | Aktueller pH-Wert |
| EC (mS/cm) | Elektrische Leitfähigkeit der Lösung |
| TDS (ppm) | Gesamtgelöste Feststoffe |
| Wassertemperatur (°C) | Temperatur der Lösung |
| Füllstand (%) oder Volumen (L) | Aktuelle Füllmenge |
| Gelöster Sauerstoff (mg/L) | Sauerstoffgehalt im Wasser — essenziell für die Wurzelaktivität in Hydroponik, optimal 5–8 mg/L |
| ORP (mV) | Redoxpotenzial — elektrochemisches Maß der Wasserqualität, optimal 300–500 mV |

4. Speichern. Der Wert erscheint in der Zustandshistorie.

!!! tip "Gelöster Sauerstoff bei DWC besonders wichtig"
    Sinkt der gelöste Sauerstoff unter 6 mg/L, warnt Kamerplanter bei Nährstoff- und Rezirkulationstanks vor einem erhöhten Risiko für Wurzelfäule. Ein niedriges ORP (unter 250 mV) weist auf ein erhöhtes Keimrisiko hin, Werte unter 650 mV gelten als suboptimal für die Desinfektionswirkung.

!!! tip "Regelmäßige Messungen"
    In der Tank-Detailansicht siehst du einen Graphen der EC- und pH-Verläufe über Zeit. Regelmäßige Messungen helfen, Trends früh zu erkennen — z.B. ansteigenden EC durch Wasserverdunstung.

---

## Tankbefüllung dokumentieren

Jede Befüllung des Tanks — ob Vollwechsel, Auffüllen oder Nachdosierung — wird als unveränderliches Ereignis historisiert. So kannst du später nachvollziehen, was deine Pflanzen wann bekommen haben.

### Schritt 1: Befüllung erfassen

Klicke in der Tank-Detailansicht auf **Befüllung erfassen** (Tab **Befüllungen**).

### Schritt 2: Befüllungs-Typ wählen

| Typ | Beschreibung |
|-----|-------------|
| **Vollwechsel** | Kompletter Austausch der Lösung |
| **Auffüllen** | Nachfüllen von verdunstetem Wasser |
| **Korrektur / Nachdosierung** | EC- oder pH-Korrektur ohne Vollwechsel |

### Schritt 3: Daten eintragen

**Basiswerte:**
- Volumen (L) des befüllten Wassers
- Wasserquelle (Leitungswasser, Osmosewasser, Regenwasser, gemischt)
- Mischverhältnis RO/Leitungswasser (falls gemischt, in %)

**Mischrezept (optional):**
Verknüpfe ein bestehendes Mischrezept aus deinen Nährstoffplänen. Das übernimmt automatisch alle Dünger und Dosierungen.

**Messwerte nach Befüllung:**
- Gemessener EC-Wert nach dem Mischen
- Gemessener pH-Wert nach der pH-Korrektur

**Plan-Zielwerte:**
Falls ein Nährstoffplan verknüpft ist, zeigt Kamerplanter den Soll-EC-Wert daneben. Du siehst auf Anhieb, ob dein Ist-Wert dem Plan entspricht.

### Schritt 4: Speichern

Die Befüllung wird in der Befüllungshistorie gespeichert. Ein neuer Tankzustand mit den gemessenen Werten wird automatisch angelegt.

---

## Wasserquellen-Defaults

Wenn du deine Wasserquelle auf der Site konfiguriert hast (Leitungswasser-EC, ob RO-Anlage vorhanden usw.), schlägt Kamerplanter die Basis-EC und das Mischverhältnis automatisch vor:

1. **Explizit eingetragen** im Befüllungsformular (höchste Priorität)
2. **Aus dem Nährstoffplan** (wenn plan verknüpft)
3. **Aus dem Site-Wasserprofil** (aus der Site-Konfiguration)
4. **Manuelle Eingabe** (wenn keine der obigen Quellen Daten liefert)

Die Quelle der Standardwerte wird im Formular angezeigt, sodass du immer weißt, woher die Vorbelegung stammt.

---

## Betreiber-/API-Funktionen für Tanks

Die folgenden vier Funktionen sind im Backend bereits vollständig implementiert, aber noch **ohne Bedienoberfläche** — du erreichst sie aktuell nur über die REST-API. Sie sind hier dokumentiert, damit du weißt, dass es sie gibt, falls du (oder deine Betreiber:in) sie per API oder eigenem Skript nutzen willst.

!!! info "Nur über API: EC-Verdünnungsrechner"
    `POST /tanks/{key}/ec-dilution` berechnet, wie viel Osmosewasser du einem Tank mit zu hoher EC hinzufügen musst, um eine Ziel-EC zu erreichen. Eingaben: aktuelle EC, Ziel-EC, aktuelles Volumen (Standard: Nennvolumen des Tanks) und die EC deines Verdünnungswassers (Standard 0,02 mS/cm). Die Antwort enthält die benötigte Menge Osmosewasser, das resultierende Endvolumen und ob die Verdünnung mit dem aktuellen Tankvolumen überhaupt machbar ist.

!!! info "Nur über API: Tank-Verknüpfung (feeds-from)"
    `POST /tanks/{key}/feeds-from` verknüpft einen Tank mit einem Quelltank, aus dem er gespeist wird — zum Beispiel ein Nährstofftank, der aus einem größeren RO-Reservoir befüllt wird. Diese Kante wird bislang nirgends in der Oberfläche angezeigt oder gepflegt.

!!! info "Nur über API: Befüllungsstatistiken"
    `GET /tanks/{key}/fills/stats` liefert aggregierte Kennzahlen zur Befüllungshistorie eines Tanks: Anzahl Befüllungen je Typ, Gesamtvolumen und durchschnittliche EC-Abweichung vom Zielwert.

!!! info "Nur über API: Live-Sensorwerte direkt von Home Assistant"
    `GET /tanks/{key}/states/live` fragt für alle am Tank hinterlegten Home-Assistant-Sensoren live den aktuellen Zustand ab, ohne einen neuen Tankzustand zu speichern. Ein Button zum Live-Abrufen in der Tank-Detailansicht ist geplant, aber noch nicht mit der Oberfläche verbunden — bis dahin siehst du aktuelle Werte, indem du regelmäßig einen neuen Zustand erfasst (siehe oben).

---

## Wartungsaufgaben planen

Tanks benötigen regelmäßige Wartung. Kamerplanter plant diese Wartungsaufgaben automatisch und erinnert dich rechtzeitig.

### Verfügbare Wartungsarten

<!-- Quelle: src/backend/app/common/enums.py MaintenanceType (6 Werte) -->

| Wartungstyp | Übliches Intervall (Orientierung) | Beschreibung |
|-------------|-----------------------------------|-------------|
| **Wasserwechsel** | 7–14 Tage (DWC), 14 Tage (Drip) | Kompletter Austausch der Nährstofflösung |
| **Reinigung** | Bei sichtbarem Algenbewuchs, nach Ernte | Tankinneres und Leitungen reinigen |
| **Desinfektion** | Zwischen Wachstumszyklen | Sterile Reinigung mit H₂O₂ oder Enzymen |
| **Kalibrierung** | 7–14 Tage (Rezirkulation), 14 Tage (Nährstofftank) | EC- oder pH-Sonde mit Referenz-/Pufferlösung kalibrieren — welche Sonde gemeint ist, hältst du im Notizfeld fest |
| **Filterwechsel** | Herstellerangabe | Vorfilter, Inline-Filter, UV-Lampen |
| **Pumpeninspektion** | Monatlich | Umwälzpumpe, Druckpumpe prüfen |

### Wartungsplan einrichten

1. Öffne den Tank und wechsle zum Tab **Wartung**.
2. Klicke auf **Wartungsplan hinzufügen**.
3. Wähle den Wartungstyp, das Intervall (in Tagen) und wie viele Tage vorher erinnert werden soll.
4. Aktiviere optional **„Aufgabe automatisch erstellen"** — dann legt Kamerplanter bei Fälligkeit automatisch eine Aufgabe an, statt nur im Dashboard/der Tank-Detailansicht zu warnen.

### Durchgeführte Wartung dokumentieren

Wenn du eine Wartung durchgeführt hast:

1. Klicke auf **Wartung erfassen** oder hake die entsprechende Aufgabe ab.
2. Trage Datum, Dauer und eventuelle Beobachtungen ein.
3. Das nächste Wartungsdatum wird automatisch berechnet.

---

## Tank-Warnungen

Kamerplanter generiert automatische Warnungen, wenn:

- Der Füllstand unter 20 % des Volumens sinkt (Warnung: "Tank fast leer")
- Der pH-Wert außerhalb des für den Tank-Typ üblichen Bereichs liegt (z. B. Nährstoff-Tank: 5,5–6,5, Rezirkulation: 5,5–6,3, Bewässerung: 5,8–6,8)
- Der EC-Wert die Obergrenze für den Tank-Typ überschreitet, oder um mehr als 20 % vom Ziel-EC des zugewiesenen Nährstoffplans abweicht
- Der pH-Wert seit der letzten Befüllung stark gedriftet ist
- Eine Wartung (Wasserwechsel, Kalibrierung, Reinigung, …) überfällig ist

Diese Warnungen erscheinen in der Tank-Detailansicht und im Dashboard.

---

## Häufige Fragen

??? question "Wie viele Tanks kann ich anlegen?"
    Es gibt keine Begrenzung. Du kannst so viele Tanks anlegen, wie du physisch hast.

??? question "Muss ich jeden Gießvorgang als Tankbefüllung erfassen?"
    Nein. Tankbefüllungen sind für das Befüllen und Wechseln des Tanks gedacht. Einzelne Gießvorgänge erfasst du im [Gießprotokoll](watering-log.md) — entweder über einen Pflanzdurchlauf oder direkt über den Menüpunkt **Gießprotokoll**.

??? question "Wie kalibriere ich eine pH-Sonde richtig?"
    Reinige die Sonde zuerst mit destilliertem Wasser. Tauche sie in eine Pufferlösung mit bekanntem pH-Wert (z.B. pH 7,0). Wenn der angezeigte Wert abweicht, stelle den Kalibrierwert entsprechend ein. Wiederhole den Vorgang mit einer zweiten Pufferlösung (z.B. pH 4,0). Dokumentiere die Kalibrierung als Wartungseintrag.

??? question "Was ist der Unterschied zwischen EC am Tank und EC an der Pflanze?"
    Die EC am Tank zeigt die Konzentration der Stammlösung. Die EC am Substrat-Abfluss (Runoff) zeigt, wie viel Salz sich im Substrat angesammelt hat. Beide Werte sind wichtig, aber sie messen verschiedene Dinge.

---

## Siehe auch

- [Dünge-Logik](fertilization.md)
- [Gießprotokoll](watering-log.md)
- [Standorte und Substrate](locations-substrates.md)
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md)
