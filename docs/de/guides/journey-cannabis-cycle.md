# Cannabis-Grow-Zyklus: von der Keimung bis zum Cure

Dieser Guide führt dich einmal durch den kompletten Anbauzyklus einer Indoor-Cannabis-Pflanze in Kamerplanter — von der Anlage des Durchlaufs bis zum fertig gecurten Ergebnis. Er erfindet keine neuen Funktionen, sondern verkettet die bestehenden Themenseiten zu einem durchgängigen Ablauf, damit du nicht selbst zusammensuchen musst, welche Seite in welcher Phase relevant ist.

!!! info "Baust du in einer Anbauvereinigung an?"
    Diese Seite konzentriert sich auf den fachlichen Anbau-Ablauf. Betreibst du stattdessen eine **Anbauvereinigung** (Cannabis-Social-Club) mit mehreren Mitgliedern, Rollen-Trennung und Dokumentationspflichten, ergänze diese Seite um den Guide [CanG-konforme Dokumentation für Anbauvereinigungen](compliance-anbauvereinigung.md).

---

## Der Zyklus im Überblick

| Etappe | Was passiert | Zuständige Seite(n) |
|--------|-------------|---------------------|
| 1 | Durchlauf mit Klonen oder Sämlingen anlegen | [Pflanzdurchläufe](../user-guide/planting-runs.md) |
| 2 | Durch die Wachstumsphasen führen | [Wachstumsphasen](../user-guide/growth-phases.md) |
| 3 | Nährlösung mischen und dosieren | [Dünge-Logik](../user-guide/fertilization.md), [Nährlösung mischen](nutrient-mixing.md) |
| 4 | Klima und VPD im Zielkorridor halten | [Sensorik](../user-guide/sensors.md), [VPD-Optimierung](vpd-optimization.md) |
| 5 | Erntereife prüfen und Karenzzeit beachten | [Erntemanagement](../user-guide/harvest.md) |
| 6 | Trocknen und curen | [Nachernte: Trocknung, Curing & Lagerung](post-harvest.md) |
| 7 | Für den nächsten Durchgang vermehren | [Vermehrungsmanagement](../user-guide/propagation.md) |

---

## 1. Durchlauf anlegen

Lege für deine Cannabis-Gruppe zuerst einen [Pflanzdurchlauf](../user-guide/planting-runs.md) an — entweder vom Typ **Monokultur** (Samen derselben Sorte) oder **Klon** (Stecklinge einer Mutterpflanze). Der Durchlauf gruppiert alle Pflanzen für gemeinsame Phasenwechsel und Gießtermine, spart dir also Einzelarbeit bei jeder größeren Gruppe.

Trage im Erstellungsdialog Standort, Bereich und optional bereits eine Substratcharge ein. Wählst du den Typ „Klon", kannst du die Quellpflanze (Mutterpflanze) direkt hinterlegen. Danach erzeugt Kamerplanter auf Knopfdruck alle Einzelpflanzen mit fortlaufender ID.

**Weiter geht's:** Sobald die Pflanzen angelegt sind, ordnest du im Tab **Düngung & Bewässerung** direkt einen passenden Nährstoffplan zu (Details in Schritt 3).

## 2. Wachstumsphasen im Blick behalten

Cannabis läuft in Kamerplanter typischerweise über den vorgefertigten **Indoor-Standard-Zyklus**: Jungpflanze → Vegetativ → Blüte → Spülung → Reife (Ernte erlaubt). Den aktuellen Phasenstand siehst du im Tab **Phasen** deines Durchlaufs oder auf der Detailseite jeder Pflanze — siehe [Wachstumsphasen](../user-guide/growth-phases.md).

Den Übergang in die Blüte kannst du manuell auslösen (z. B. beim Umstellen auf 12/12-Photoperiode) oder, sofern GPS-Koordinaten am Standort hinterlegt sind, automatisch anhand der Tageslänge (photoperiodisch) erkennen lassen. Verlasse dich dabei nicht ausschließlich auf die Automatik. Kontrolliere den Phasenstand deiner Pflanzen weiterhin regelmäßig, denn die automatische Hintergrundprüfung läuft je nach Installation unterschiedlich häufig.

!!! warning "Phasenübergänge sind nicht umkehrbar"
    Warte mit dem Wechsel, bis du wirklich sicher bist — ein einmal ausgelöster Phasenübergang lässt sich nicht rückgängig machen.

## 3. Düngung und Nährlösung planen

Lege für deinen Durchlauf einen Nährstoffplan mit Dosierungen je Phase an ([Dünge-Logik](../user-guide/fertilization.md)) und weise ihn dem Durchlauf zu. Kamerplanter berechnet daraus dein [EC](../reference/glossary.md#elektrische-leitfahigkeit-ec)-Budget je Phase und schlägt dir bei jedem Gießtermin die passende Dosierung vor.

Beim tatsächlichen Anmischen ist die Reihenfolge entscheidend: CalMag (Calcium-Magnesium-Supplement) immer vor Sulfaten und Phosphaten einrühren, sonst drohen Ausfällungen. Die vollständige Mischfolge inklusive EC-Budget-Pipeline, Inkompatibilitäten und pH-Einstellung erklärt der Guide [Nährlösung mischen](nutrient-mixing.md).

!!! tip "Fortgeschrittene Rechner"
    Ab der Erfahrungsstufe Fortgeschritten stehen dir zusätzlich der **Wasser-Mischer** und der **EC-Budget-Rechner** zur Verfügung, mit denen du CalMag/Silizium separat einrechnest und die EC-Temperaturkorrektur nutzt — siehe [Wasser-Mischer und EC-Budget-Rechner](../user-guide/fertilization.md#wasser-mischer-und-ec-budget-rechner).

## 4. Klima und VPD überwachen

Das Dampfdruckdefizit (VPD) ist der wichtigste Klimaparameter für Cannabis — es bestimmt, wie stark deine Pflanze transpiriert und Nährstoffe aufnimmt. Die Zielkorridore je Phase (z. B. 0,8–1,2 kPa vegetativ, 1,0–1,5 kPa Blüte) und die zugrunde liegende Tetens-Formel erklärt der Guide [VPD-Optimierung](vpd-optimization.md).

Damit Kamerplanter den gemessenen Wert mit dem Zielkorridor vergleichen und im Dashboard warnen kann, brauchst du Klimasensoren an deinem Standort — aktuell funktioniert das automatische Auslesen über eine Home-Assistant-Anbindung. Details zur Sensor-Einrichtung, den verfügbaren Messgrößen und dem aktuellen Umsetzungsstand der übrigen Datenquellen findest du unter [Sensorik und Messdaten](../user-guide/sensors.md).

## 5. Erntereife und [Karenzzeit](../reference/glossary.md#karenzzeit-pre-harvest-interval-phi) prüfen

Kamerplanter zeigt dir auf der Pflanzendetailseite ein erwartetes Erntedatum, berechnet aus Pflanzdatum und den geplanten Phasendauern. Die endgültige Entscheidung triffst aber du selbst, anhand der klassischen Reifeindikatoren (Trichom-Farbe, Pistil-Färbung) — Details in [Erntemanagement](../user-guide/harvest.md).

Bevor du eine Erntecharge anlegst, prüft das System automatisch alle laufenden Pflanzenschutzbehandlungen: Liegt eine Behandlung noch innerhalb ihrer Karenzzeit (Pre-Harvest Interval), blockiert Kamerplanter die Ernte und nennt dir das frühestmögliche Datum. Hast du zuvor mit dem [Integrierten Pflanzenschutz (IPM)](../user-guide/pest-management.md) gearbeitet, ist dieses Sicherheitsnetz also bereits aktiv, ohne dass du selbst etwas einstellen musst.

## 6. Trocknen und curen

Nach dem Schnitt dokumentierst du Nassgewicht, Erntetyp und später die Qualitätsbewertung direkt an der Erntecharge (siehe [Erntemanagement](../user-guide/harvest.md)). Die fachliche Anleitung für die Trocknung selbst findest du im Guide [Nachernte: Trocknung, Curing & Lagerung](post-harvest.md). Er nennt Zielwerte für Temperatur, Luftfeuchte und Dauer der Slow-Dry-Methode, das Burping-Schema beim Jar-Curing sowie die Lagerbedingungen danach.

!!! note "Trocknungs-Workflow noch nicht als eigene Oberfläche verfügbar"
    Eine strukturierte Erfassung von Trocknungsschritten mit laufender Gewichts- oder Feuchtemessung gibt es aktuell nicht. Du trägst am Ende lediglich das tatsächliche Trockengewicht an der Erntecharge ein und orientierst dich für den Ablauf selbst an den Richtwerten im Nachernte-Guide.

## 7. Für den nächsten Durchgang vermehren

Willst du eine gut gelaufene Mutterpflanze für den nächsten Zyklus klonen oder die genetische Abstammung deiner Pflanzen nachvollziehbar dokumentieren, ist das im Guide [Vermehrungsmanagement](../user-guide/propagation.md) beschrieben.

!!! warning "Noch nicht implementiert"
    Der dort beschriebene Abstammungsgraph (Mutterpflanze → Klon-Generationen, Kreuzungen, Veredelungen) ist spezifiziert, aber noch nicht umgesetzt. Willst du heute schon nachvollziehen, woher eine Pflanze stammt, legst du die neue Pflanze als eigenständige Pflanzinstanz an und notierst die Herkunft (z. B. Mutterpflanze, Entnahmedatum) vorerst im Freitext-Notizfeld.

---

## Häufige Fragen

??? question "Muss ich alle sieben Etappen nutzen, oder kann ich einzelne überspringen?"
    Du kannst jede Seite unabhängig nutzen. Diese Journey-Seite ist ein Wegweiser, kein Pflichtablauf — wenn du z. B. keine Sensoren hast, überspringst du Schritt 4 einfach und trägst Klimadaten nach eigenem Ermessen ein oder verzichtest darauf.

??? question "Gilt dieser Ablauf auch für andere Indoor-Kulturen als Cannabis?"
    Grundsätzlich ja — Phasenmodell, EC-Budget und VPD-Logik funktionieren genauso für Chili, Basilikum oder andere Indoor-Kulturen. Die konkreten Zielwerte (z. B. VPD-Korridore, NPK-Profile) und die Erntetypen unterscheiden sich aber je nach Pflanzenart.

??? question "Was mache ich, wenn die Ernte wegen der Karenzzeit blockiert wird?"
    Warte bis zum vom System genannten frühestmöglichen Erntedatum. Prüfe im Zweifel im [Integrierten Pflanzenschutz (IPM)](../user-guide/pest-management.md), ob die eingetragene Behandlung und ihre Karenzzeit korrekt sind.

---

## Siehe auch

- [Pflanzdurchläufe](../user-guide/planting-runs.md)
- [Wachstumsphasen](../user-guide/growth-phases.md)
- [Dünge-Logik](../user-guide/fertilization.md)
- [Nährlösung mischen](nutrient-mixing.md)
- [Sensorik und Messdaten](../user-guide/sensors.md)
- [VPD-Optimierung](vpd-optimization.md)
- [Erntemanagement](../user-guide/harvest.md)
- [Nachernte: Trocknung, Curing & Lagerung](post-harvest.md)
- [Vermehrungsmanagement](../user-guide/propagation.md)
- [CanG-konforme Dokumentation für Anbauvereinigungen](compliance-anbauvereinigung.md)
