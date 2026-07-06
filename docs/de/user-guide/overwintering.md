# Überwinterung

Für jede deiner Freiland- oder Gewächshaus-Pflanzen, die nicht winterhart ist, erstellt Kamerplanter automatisch einen passenden Überwinterungsplan — abgeleitet aus dem Steckbrief der Pflanzenart und der Winterhärte deines Standorts. Du musst dafür kein Profil anlegen; du kannst das Ergebnis aber jederzeit einsehen und bei Bedarf anpassen. <!-- REQ-047 -->

---

## Voraussetzungen

- Die Pflanze steht an einem Standort vom Typ **Außenbereich** (Freiland) oder **Gewächshaus**.
- Der Pflanze ist eine Pflanzenart zugeordnet (Stammdaten) — daraus leitet Kamerplanter die Frostempfindlichkeit ab.

---

## Den automatischen Plan ansehen

1. Öffne **Pflanzen** > deine Pflanze.
2. Wechsle zum Tab **Pflege**.
3. Scrolle zum Abschnitt **Überwinterung**.

Ist die Pflanze an deinem Standort **nicht winterhart**, zeigt dir dieser Abschnitt den automatisch erstellten Plan: Winterhärte-Einstufung, Schutzmaßnahme und deren Monat, Gießvorgabe für die Winterruhe sowie — je nach Art — die Frühjahrsmaßnahme, die Bedingungen im Winterquartier oder die Kontrollintervalle für eingelagerte Knollen. Ein Badge **„Automatisch aus Steckbrief"** kennzeichnet, dass der Plan von Kamerplanter selbst erzeugt wurde.

!!! tip "Gilt diese Pflanze überhaupt als gefährdet?"
    Ist deine Pflanze an deinem Standort **winterhart** (grüne Ampel), erscheint im Abschnitt „Überwinterung" stattdessen der Hinweis, dass kein Winterschutz nötig ist — es wird bewusst **kein** Plan angelegt und **keine** Winterschutz-Erinnerung erzeugt. Mehr zur Winterhärte-Einstufung unter [Klimazonen & Winterhärte](../guides/climate-zones.md).

Der Winter-Pfad zeigt dir außerdem, wie die Pflanze überwintert:

| Winter-Pfad | Bedeutung |
|-------------|-----------|
| **In-situ (Schutz vor Ort)** | Die Pflanze bleibt an ihrem Standort und wird dort geschützt (z. B. mit Mulch oder Vlies). |
| **Verlagern (Winterquartier)** | Die Pflanze muss ins Winterquartier umziehen, oder ihre Knollen müssen ausgegraben und eingelagert werden. |

Ist die Winterruhe für diese Pflanze gerade aktiv, zeigt ein zusätzliches Badge **„Winterruhe-Pflege aktiv"** an, dass gerade der reduzierte Gieß- und Düngeplan gilt (siehe [Saison-Automatik](season-automation.md#was-sich-wahrend-der-winterruhe-andert)).

---

## Den Plan anpassen

Passt der automatisch erstellte Plan nicht zu deinen Bedingungen — zum Beispiel, weil dein Standort besonders geschützt liegt oder du eine andere Schutzmaßnahme bevorzugst — kannst du einzelne Werte übersteuern:

### Schritt 1: Anpassen öffnen

Klicke im Abschnitt „Überwinterung" auf **Anpassen**.

### Schritt 2: Werte ändern

Im Dialog kannst du unter anderem folgende Werte ändern:

- Winterhärte-Einstufung und Schutzmaßnahme (mit passendem Monat)
- Gießvorgabe für die Winterruhe
- Frühjahrsmaßnahme und deren Monat
- Temperatur- und Lichtbedingungen im Winterquartier
- Kontrollintervall und Status einer eingelagerten Knolle oder Zwiebel

!!! warning "Schutzmaßnahme muss zur Winterhärte passen"
    Kamerplanter lässt keine Kombination zu, die sich widerspricht — zum Beispiel „winterhart" zusammen mit „muss ausgegraben werden". Das Auswahlfeld für die Schutzmaßnahme zeigt dir automatisch nur Optionen an, die zur gewählten Winterhärte passen.

### Schritt 3: Speichern

Klicke auf **Speichern**. Der Plan trägt danach das Badge **„Angepasst"** statt „Automatisch aus Steckbrief" — und Kamerplanter überschreibt deine Änderungen ab jetzt nicht mehr. Ändert sich später etwas am Steckbrief oder an der Winterhärte-Ampel deines Standorts, ergänzt die Automatik nur noch **fehlende** Angaben, ohne deine bereits gesetzten Werte anzutasten.

---

## Wieder auf Automatik zurücksetzen

Möchtest du zu den automatisch abgeleiteten Werten zurückkehren, klicke im Abschnitt „Überwinterung" auf **Auf Automatik zurücksetzen** und bestätige den Dialog. Kamerplanter verwirft deine manuellen Anpassungen und leitet den Plan erneut vollständig aus dem Steckbrief der Art und der Winterhärte-Ampel deines Standorts ab.

---

## Alle Überwinterungspläne im Überblick

Unter **Pflanzen > Überwinterung** findest du eine Tabelle mit den Überwinterungsplänen all deiner Pflanzen — praktisch, wenn du dir vor dem ersten Frost einen Gesamtüberblick verschaffen willst. Automatisch erstellte Pläne sind mit dem Badge **„Auto"** gekennzeichnet. Über die Schaltfläche **Profil erstellen** kannst du hier zusätzlich manuell einen Plan für eine Pflanze anlegen, die (noch) keinen automatischen Plan hat — zum Beispiel, um schon vor dem Übergang in „Winter kündigt sich an" eigene Werte zu hinterlegen.

---

## Häufige Fragen

??? question "Ich habe noch nie ein Überwinterungsprofil angelegt — trotzdem sehe ich einen Plan. Woher kommt der?"
    Kamerplanter erstellt diesen Plan automatisch, sobald dein Standort in die Stufe „Winter kündigt sich an" wechselt (siehe [Saison-Automatik](season-automation.md)) — vorausgesetzt, deine Pflanze gilt an diesem Standort nicht als winterhart. Du musst dafür nichts einrichten.

??? question "Warum sehe ich für meine winterharte Pflanze keinen Überwinterungsplan?"
    Das ist beabsichtigt. Für Pflanzen, die an deinem Standort winterhart sind, legt Kamerplanter bewusst keinen Plan an und erzeugt keine Winterschutz-Erinnerung, da sie ohne zusätzlichen Schutz auskommen.

??? question "Was passiert, wenn ich einen Wert anpasse und sich später der Steckbrief der Art ändert?"
    Deine Anpassung bleibt erhalten. Sobald du mindestens einen Wert manuell änderst, überschreibt die Automatik ihn nie wieder — sie ergänzt lediglich Felder, die du nie gesetzt hast.

??? question "Kann ich ein Überwinterungsprofil auch löschen?"
    Ja, über die Tabelle unter **Pflanzen > Überwinterung** mit dem Papierkorb-Symbol. Bleibt die Pflanze an einem Freiland- oder Gewächshaus-Standort und ist sie nicht winterhart, erstellt Kamerplanter beim nächsten Übergang in „Winter kündigt sich an" automatisch wieder einen neuen Plan.

---

## Siehe auch

- [Saison-Automatik](season-automation.md) — wie Kamerplanter erkennt, wann der Winter beginnt und endet
- [Klimazonen & Winterhärte](../guides/climate-zones.md) — wie die Winterhärte-Ampel zustande kommt
- [Pflegeerinnerungen](care-reminders.md) — Gieß- und Pflegepläne allgemein
- [Wachstumsphasen](growth-phases.md) — Ruhephasen im Phasenmodell
