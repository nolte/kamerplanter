# Hydroponik-Setup: NFT & DWC einrichten

Diese Journey führt dich durch die Ersteinrichtung eines substratlosen Hydroponik-Systems in Kamerplanter — vom Standort über den Tank und die Nährlösung bis zu Sensoren und Umgebungssteuerung. Sie verkettet ausschließlich bereits bestehende Kamerplanter-Seiten; neue Funktionen beschreibt sie nicht. Wo eine Funktion nur teilweise oder noch gar nicht umgesetzt ist, sagt dir diese Seite das ehrlich.

<!-- Zielgruppe: ZG-006 Hydroponik- und Vertical-Farming-Betreiber -->

---

## Für wen ist diese Journey?

Für alle, die ein NFT- oder DWC-System betreiben — im Keller, Grow-Zelt oder als kleine Urban-Farm — und dabei [EC](../reference/glossary.md#elektrische-leitfahigkeit-ec), pH und Füllstand im Blick behalten wollen.

## Voraussetzungen

- Ein Mandant in Kamerplanter (wird beim Onboarding automatisch angelegt)
- Für automatische Sensordaten: eine funktionierende Home-Assistant-Integration — siehe [Home Assistant Integration](home-assistant-integration.md)

---

## Was sind NFT und DWC?

Beide Systeme kommen ohne festes Substrat aus — die Pflanzenwurzeln stehen direkt im Kontakt mit der Nährlösung:

- **DWC** (Deep Water Culture) — die Wurzeln hängen permanent in einer sauerstoffangereicherten Nährlösung. Eine Luftpumpe mit Ausströmerstein ist hier unverzichtbar, da stehendes Wasser ohne Belüftung schnell zu Wurzelfäule führt.
- **NFT** (Nutrient Film Technique) — ein dünner Nährlösungsfilm fließt kontinuierlich über die Wurzeln in einer geneigten Rinne und läuft in einen Rezirkulationstank zurück. Hier ist die Umwälzpumpe die kritische Komponente: Fällt sie aus, trocknen die Wurzeln innerhalb weniger Stunden aus.

Der Ablauf durch diese Journey ist für beide Systeme identisch — die Unterschiede liegen vor allem in der Tank-Ausstattung (Schritt 2).

---

## Schritt 1: Standort und Substrat vorbereiten

Lege zunächst einen [Standort](../user-guide/locations-substrates.md) für dein System an — zum Beispiel eine Location vom Typ „Grow-Zelt", „Zimmer" oder „Regal", je nachdem, wo dein Aufbau steht.

Auch wenn NFT und DWC ohne klassisches Substrat auskommen, verwaltet Kamerplanter sie trotzdem über die [Substratverwaltung](../user-guide/locations-substrates.md#substrate-verwalten) — mit zwei speziell dafür vorgesehenen Substrat-Typen:

- **Kein Substrat** — für vollständig substratlose Systeme wie reine DWC-Aufbauten
- **Hydrolösung** — für Systeme, in denen die Nährlösung selbst als „Medium" geführt wird

Setzt du stattdessen Anzuchtwürfel oder -matten zur Keimung ein (z. B. um Sämlinge später ins NFT-System zu setzen), nutzt du dafür die Typen **Steinwollwürfel** bzw. **Steinwollmatte**. Auch Tonkugeln (**Blähton**) sind als Substrat-Typ hinterlegt, falls du einzelne Pflanzen in Netztöpfen mit Blähton stützt.

---

## Schritt 2: Tank(s) konfigurieren

Als Nächstes richtest du im [Tankmanagement](../user-guide/tanks.md) die Tanks für dein System ein. Kamerplanter unterscheidet dafür fünf Tank-Typen — für Hydroponik sind vor allem drei davon relevant, siehe [Tank-Typen verstehen](../user-guide/tanks.md#tank-typen-verstehen):

| Dein System | Tank-Typ | Wichtige Ausstattung |
|-------------|----------|----------------------|
| DWC | Nährstoff | Luftpumpe (Sauerstoffanreicherung) |
| NFT | Rezirkulation | Umwälzpumpe (Zirkulation) |
| Beide (Vorratsbehälter) | Reservoir | Deckel, ggf. Lichtdicht (gegen Algen) |

Trage beim Anlegen Volumen, Material und die passende Ausstattung ein — die Ausstattungs-Chips erscheinen danach auf der Tank-Detailseite. Verknüpfe anschließend deine EC-, pH- und Füllstand-Sensoren über **Sensor hinzufügen** direkt am Tank (mehr dazu in Schritt 4).

!!! danger "Stammlösungen niemals direkt mischen"
    Nutzt du konzentrierte A/B-Stammlösungen für eine automatisierte Dosierung, lege dafür eigene Tanks vom Typ **Stammlösung** an. Diese dürfen niemals direkt miteinander in Kontakt kommen — nur über Wasser verdünnt. Kamerplanter warnt dich beim Anlegen entsprechender Tanks.

---

## Schritt 3: Nährlösung mischen — EC-Budget und Mischfolge

Sobald der Tank steht, geht es an die Nährlösung selbst. [Nährlösung mischen](nutrient-mixing.md) erklärt Schritt für Schritt, wie Kamerplanter dein EC-Budget berechnet — auf Basis deiner Ziel-EC und der EC deines Mischwassers. Außerdem skaliert der Guide Herstellerrezepte proportional und führt dich durch die korrekte Mischfolge (Silikat vor CalMag vor Basisdüngern — sonst drohen Ausfällungen).

Für Hydroponik-Systeme ohne Substratpufferung sind die EC-Zielwerte enger gefasst als bei Erde oder Coco — die passenden Bereiche je Wachstumsphase findest du unter [EC-Zielwerte nach Phase und Substrat](nutrient-mixing.md#ec-ziel-substrat).

!!! tip "Rezirkulation braucht mehr Aufmerksamkeit als Drain-to-Waste"
    In einem rezirkulierenden System (NFT, DWC) konzentriert sich die Nährlösung über Zeit durch Verdunstung — die EC steigt schleichend an, ohne dass neue Nährstoffe hinzukommen. Plane deshalb regelmäßige Kontrollmessungen ein, statt dich allein auf die letzte Befüllung zu verlassen (siehe [Aktuellen Tankzustand erfassen](../user-guide/tanks.md#aktuellen-tankzustand-erfassen)).

---

## Schritt 4: Sensoren für EC, pH und Füllstand einrichten

Mit eingerichtetem Tank und gemischter Lösung geht es an die laufende Überwachung. [Sensorik und Messdaten](../user-guide/sensors.md) erklärt, wie du [Sensoren an einen Standort bindest](../user-guide/sensors.md#sensoren-an-einen-standort-binden) und welche [Messgrößen](../user-guide/sensors.md#messgroessen-im-formular) zur Auswahl stehen. Für ein Hydroponik-System sind vor allem diese relevant:

| Messgröße | Wofür |
|-----------|-------|
| `ec_ms` | Nährstoffkonzentration der Lösung |
| `ph` | Nährstoffverfügbarkeit |
| `water_temp_celsius` | Wurzelzonen-Temperatur |
| `dissolved_oxygen_mgl` | Sauerstoffversorgung der Wurzeln (besonders kritisch bei DWC) |
| `orp_mv` | Redoxpotenzial als Wasserqualitäts-Indikator |
| `fill_level_percent` | Füllstand — frühzeitige Warnung vor leerem Tank |

!!! info "Aktueller Stand: Home Assistant oder manuelle Eingabe am Tank"
    Von den vier in der Spezifikation vorgesehenen Datenquellen sind aktuell zwei tatsächlich nutzbar: die automatische Abfrage über **Home Assistant** (alle 5 Minuten) und die **manuelle Eingabe** direkt am Tank — siehe [Aktuellen Tankzustand erfassen](../user-guide/tanks.md#aktuellen-tankzustand-erfassen). Eine direkte MQTT-Anbindung ohne Home Assistant dazwischen ist im Datenmodell vorgesehen, aber noch nicht implementiert. Betreibst du bereits ESPHome- oder Shelly-basierte Sonden, bindest du sie am einfachsten über Home Assistant ein und wählst sie anschließend im Sensor- bzw. Tank-Formular über die HA-Entity-Autocomplete aus.

---

## Schritt 5: Umgebungssteuerung — Aktoren und Automatisierung (Ausblick)

Der letzte Baustein einer vollautomatischen Anlage ist der geschlossene Regelkreis: Sensor misst, Regel bewertet, Aktor schaltet — zum Beispiel eine Umwälzpumpe, ein CO₂-Doser oder ein Luftbefeuchter.

!!! note "Teilweise verfügbar"
    Die Regel-Engine, Zeitpläne, Hysterese und der volle Prioritäts-Regelkreis von [Umgebungssteuerung & Aktorik](../user-guide/actuator-control.md) laufen bereits im Backend. In der Oberfläche kannst du bislang Aktoren anlegen, direkt ein-/ausschalten und eine Notabschaltung auslösen — Zeitpläne, Regeln und phasengebundene Profile sind aktuell nur über die API einrichtbar (siehe [Für technische Nutzer / Self-Hoster](../user-guide/actuator-control.md#fuer-technische-nutzer-self-hoster)).

    Bis eine eigene Oberfläche dafür existiert, steuerst du Pumpen, Luftbefeuchter und Dosiergeräte direkt über die Aktor-Karten, über Home Assistant oder von Hand und protokollierst wichtige Ereignisse (Wasserwechsel, Kalibrierung) manuell über die [Tank-Wartungsplanung](../user-guide/tanks.md#wartungsaufgaben-planen).

---

## Wo diese Journey an Grenzen stößt: Ertrag und Kosten

Für den semi-professionellen oder gewerblichen Betrieb sind Kennzahlen wie Ertrag pro Watt, Ertrag pro Liter oder die Produktionskosten pro Kopfsalat oft mindestens so wichtig wie die reine Klima- und Nährstoffsteuerung.

!!! warning "Ressourcen- und Kostenanalytik noch nicht verfügbar"
    Kamerplanter dokumentiert Ernten aktuell mit Gewicht und Qualitätsbewertung (siehe [Erntemanagement](../user-guide/harvest.md)), aber es gibt noch **keine** automatische Berechnung von Ertrag pro Watt, Ertrag pro Liter oder Produktionskosten pro Einheit (Strom-, Nährstoff-, Wasser- und Substratkosten). <!-- ZG-006: Yield/Kosten-Analytik, Ressourcen-Dashboard geplant, nicht terminiert -->
    Für eine Kosten- oder Ertragskennzahl je Kultur musst du aktuell selbst rechnen — zum Beispiel mit den in Kamerplanter erfassten Erntegewichten und deinen eigenen Verbrauchsdaten außerhalb der App.

---

## Häufige Fragen

??? question "Brauche ich zwingend Home Assistant für ein Hydroponik-Setup?"
    Nein. Du kannst EC, pH, Wassertemperatur, Füllstand und die weiteren Tankwerte jederzeit manuell erfassen — siehe [Aktuellen Tankzustand erfassen](../user-guide/tanks.md#aktuellen-tankzustand-erfassen). Home Assistant lohnt sich vor allem, sobald du mehrere Tanks oder ein größeres System hast und die manuelle Eingabe zu aufwändig wird.

??? question "Wie verhindere ich, dass meine NFT-Rinne bei Pumpenausfall trockenfällt?"
    Kamerplanter selbst kann eine ausgefallene Pumpe heute noch nicht automatisch erkennen und gegensteuern (siehe Schritt 5). Richte dafür bis zur Umsetzung der Umgebungssteuerung eine eigene Absicherung in Home Assistant ein (z. B. eine Benachrichtigung bei Stromausfall der Pumpe) und trage eine Kontrollaufgabe in Kamerplanter ein.

??? question "Was mache ich bei steigender EC durch Verdunstung?"
    Miss regelmäßig und dokumentiere die Werte am Tank. Steigt die EC über den Zielbereich, verdünnst du mit frischem Wasser oder Osmosewasser — Details zur Mischlogik findest du unter [Nährlösung mischen](nutrient-mixing.md).

---

## Siehe auch

- [Standorte & Substrate](../user-guide/locations-substrates.md)
- [Tankmanagement](../user-guide/tanks.md)
- [Nährlösung mischen](nutrient-mixing.md)
- [Sensorik und Messdaten](../user-guide/sensors.md)
- [Umgebungssteuerung & Aktorik](../user-guide/actuator-control.md)
- [Home Assistant Integration](home-assistant-integration.md)
- [Glossar](../reference/glossary.md)
