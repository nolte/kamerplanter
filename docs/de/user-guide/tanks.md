# Tankmanagement

Tanks verwalten Ihre Wassertanks, Nährstoffreservoirs und Gießwasserbehälter. Sie erfassen Füllstände, dokumentieren Befüllungen mit vollständigen Mischrezepten und planen Wartungsarbeiten wie Wasserwechsel und Sonden-Kalibrierungen.

---

## Voraussetzungen

- Mindestens eine angelegte Location (Tanks werden einer Location zugeordnet)
- Für EC-gesteuerte Befüllungen: Nährstoffpläne unter **Düngung** angelegt

---

## Tank-Typen verstehen

Kamerplanter unterscheidet fünf Tank-Typen:

| Typ | Beschreibung | Typische Verwendung |
|-----|-------------|-------------------|
| **Nährstofflösung** | Fertig gemischte Lösung | Drip-Systeme, Hydroponik |
| **Gießwasser** | Aufbereitetes Wasser, ggf. pH-korrigiert | Erde- und Coco-Kulturen |
| **Reservoir** | Vorratstank für Rohwasser | Regenwassersammler, RO-Wasser |
| **Rezirkulation** | Rücklauftank bei geschlossenen Systemen | NFT, Ebb & Flow |
| **Stammlösung** | Konzentrierte A/B-Tanks | Automatisierte Dosierung |

!!! danger "Stammlösungen niemals direkt mischen"
    Konzentrierte A- und B-Stammlösungen dürfen niemals direkt miteinander in Kontakt kommen — nur über Wasser verdünnt. Kamerplanter warnt beim Anlegen von Stammlösungs-Tanks.

---

## Einen neuen Tank anlegen

### Schritt 1: Zur Tankübersicht navigieren

Klicken Sie in der Navigation auf **Standorte** und öffnen Sie eine Site. Im Tab **Tanks** sehen Sie alle Tanks dieser Site.

Alternativ: Navigieren Sie zu **Standorte → Tanks** für eine site-übergreifende Übersicht.

### Schritt 2: Neuen Tank erstellen

Klicken Sie auf **Tank hinzufügen**.

### Schritt 3: Tank konfigurieren

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| Name | Bezeichnung des Tanks | "DWC Reservoir Zelt A" |
| Typ | Tank-Typ (siehe oben) | Nährstofflösung |
| Volumen (L) | Fassungsvermögen | 100 |
| Location | Welchem Bereich ist der Tank zugeordnet? | "Growzelt A" |
| Bewässerungssystem | Welches System nutzt der Tank? | Tropfsystem |

### Schritt 4: Sensoren verknüpfen (optional)

Wenn Sie einen Sensor für Füllstand, EC oder pH im Tank haben, können Sie diesen über **Sensor verknüpfen** dem Tank zuordnen. Die aktuellen Sensorwerte erscheinen dann in der Tank-Detailansicht.

---

## Aktuellen Tankzustand erfassen

Der Tankzustand gibt Auskunft über den aktuellen Füllstand, EC- und pH-Wert sowie die Wassertemperatur.

### Neuen Messwert eintragen

1. Öffnen Sie einen Tank.
2. Klicken Sie auf **Zustand erfassen** (Tab **Zustand**).
3. Tragen Sie die aktuellen Werte ein:

| Parameter | Beschreibung |
|-----------|-------------|
| Füllstand (%) oder Volumen (L) | Aktuelle Füllmenge |
| EC (mS/cm) | Elektrische Leitfähigkeit der Lösung |
| pH-Wert | Aktueller pH-Wert |
| Wassertemperatur (°C) | Temperatur der Lösung |

4. Speichern. Der Wert erscheint in der Zustandshistorie.

!!! tip "Regelmäßige Messungen"
    In der Tank-Detailansicht sehen Sie einen Graphen der EC- und pH-Verläufe über Zeit. Regelmäßige Messungen helfen, Trends früh zu erkennen — z.B. ansteigenden EC durch Wasserverdunstung.

---

## Tankbefüllung dokumentieren

Jede Befüllung des Tanks — ob Vollwechsel, Auffüllen oder Nachdosierung — wird als unveränderliches Ereignis historisiert. So können Sie später nachvollziehen, was Ihre Pflanzen wann bekommen haben.

### Schritt 1: Befüllung erfassen

Klicken Sie in der Tank-Detailansicht auf **Befüllung erfassen** (Tab **Befüllungen**).

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
Verknüpfen Sie ein bestehendes Mischrezept aus Ihren Nährstoffplänen. Das übernimmt automatisch alle Dünger und Dosierungen.

**Messwerte nach Befüllung:**
- Gemessener EC-Wert nach dem Mischen
- Gemessener pH-Wert nach der pH-Korrektur

**Plan-Zielwerte:**
Falls ein Nährstoffplan verknüpft ist, zeigt Kamerplanter den Soll-EC-Wert daneben. Sie sehen auf Anhieb, ob Ihr Ist-Wert dem Plan entspricht.

### Schritt 4: Speichern

Die Befüllung wird in der Befüllungshistorie gespeichert. Ein neuer Tankzustand mit den gemessenen Werten wird automatisch angelegt.

---

## Wasserquellen-Defaults

Wenn Sie Ihre Wasserquelle auf der Site konfiguriert haben (Leitungswasser-EC, ob RO-Anlage vorhanden usw.), schlägt Kamerplanter die Basis-EC und das Mischverhältnis automatisch vor:

1. **Explizit eingetragen** im Befüllungsformular (höchste Priorität)
2. **Aus dem Nährstoffplan** (wenn plan verknüpft)
3. **Aus dem Site-Wasserprofil** (aus der Site-Konfiguration)
4. **Manuelle Eingabe** (wenn keine der obigen Quellen Daten liefert)

Die Quelle der Standardwerte wird im Formular angezeigt, sodass Sie immer wissen, woher die Vorbelegung stammt.

---

## Wartungsaufgaben planen

Tanks benötigen regelmäßige Wartung. Kamerplanter plant diese Wartungsaufgaben automatisch und erinnert Sie rechtzeitig.

### Verfügbare Wartungsarten

| Wartungstyp | Empfohlenes Intervall | Beschreibung |
|-------------|----------------------|-------------|
| **Wasserwechsel** | 7–14 Tage (DWC), 14 Tage (Drip) | Kompletter Austausch der Nährstofflösung |
| **Reinigung** | Bei sichtbarem Algenbewuchs, nach Ernte | Tankinneres und Leitungen reinigen |
| **Desinfektion** | Zwischen Wachstumszyklen | Sterile Reinigung mit H₂O₂ oder Enzymen |
| **Kalibrierung EC-Sonde** | 7–14 Tage (Rezirkulation), 14 Tage (Nährstofftank) | EC-Sonde mit Referenzlösung kalibrieren |
| **Kalibrierung pH-Sonde** | Wie EC-Sonde | pH-Sonde mit Pufferlösungen kalibrieren |
| **Filterwechsel** | Herstellerangabe | Vorfilter, Inline-Filter, UV-Lampen |
| **Pumpeninspektion** | Monatlich | Umwälzpumpe, Druckpumpe prüfen |

### Wartungsplan einrichten

1. Öffnen Sie den Tank und wechseln Sie zum Tab **Wartung**.
2. Klicken Sie auf **Wartungsplan hinzufügen**.
3. Wählen Sie den Wartungstyp und das Intervall.
4. Das System erstellt automatisch Aufgaben nach dem eingestellten Intervall.

### Durchgeführte Wartung dokumentieren

Wenn Sie eine Wartung durchgeführt haben:

1. Klicken Sie auf **Wartung erfassen** oder haken Sie die entsprechende Aufgabe ab.
2. Tragen Sie Datum, Dauer und eventuelle Beobachtungen ein.
3. Das nächste Wartungsdatum wird automatisch berechnet.

---

## Tank-Warnungen

Kamerplanter generiert automatische Warnungen, wenn:

- Der Füllstand unter 20 % des Volumens sinkt (Warnung: "Tank fast leer")
- Der EC-Wert außerhalb des Zielbereichs der aktuellen Phase liegt
- Der pH-Wert außerhalb des Zielbereichs liegt (Hydroponik: 5,5–6,5)
- Eine Sonden-Kalibrierung überfällig ist
- Ein Wasserwechsel überfällig ist

Diese Warnungen erscheinen in der Tank-Detailansicht und im Dashboard.

---

## Häufige Fragen

??? question "Wie viele Tanks kann ich anlegen?"
    Es gibt keine Begrenzung. Sie können so viele Tanks anlegen, wie Sie physisch haben.

??? question "Muss ich jeden Gießvorgang als Tankbefüllung erfassen?"
    Nein. Tankbefüllungen sind für das Befüllen und Wechseln des Tanks gedacht. Einzelne Gießvorgänge werden als **Gießereignisse** (FeedingEvents) erfasst — entweder über einen Pflanzdurchlauf oder direkt unter **Düngung → Gießereignisse**.

??? question "Wie kalibriere ich eine pH-Sonde richtig?"
    Reinigen Sie die Sonde zuerst mit destilliertem Wasser. Tauchen Sie sie in eine Pufferlösung mit bekanntem pH-Wert (z.B. pH 7,0). Wenn der angezeigte Wert abweicht, stellen Sie den Kalibrierwert entsprechend ein. Wiederholen Sie mit einer zweiten Pufferlösung (z.B. pH 4,0). Dokumentieren Sie die Kalibrierung als Wartungseintrag.

??? question "Was ist der Unterschied zwischen EC am Tank und EC an der Pflanze?"
    Die EC am Tank zeigt die Konzentration der Stammlösung. Die EC am Substrat-Abfluss (Runoff) zeigt, wie viel Salz sich im Substrat angesammelt hat. Beide Werte sind wichtig, aber sie messen verschiedene Dinge.

---

## Siehe auch

- [Dünge-Logik](fertilization.md)
- [Standorte und Substrate](locations-substrates.md)
- [Guides: Nährlösung mischen](../guides/nutrient-mixing.md)
