# Überwinterung

Für jede deiner Freiland-, Gewächshaus- oder Balkon-Pflanzen, die nicht winterhart ist, erstellt Kamerplanter automatisch einen passenden Überwinterungsplan — abgeleitet aus dem Steckbrief der Pflanzenart und der Winterhärte deines Standorts. Der Plan entsteht, sobald die Pflanze einem solchen Standort zugeordnet wird — du musst dafür kein Profil anlegen; du kannst das Ergebnis aber jederzeit einsehen und bei Bedarf anpassen. <!-- REQ-047 -->

---

## Voraussetzungen

- Die Pflanze steht an einer Location, die als frostexponiert gilt. Das ist standardmäßig der Fall bei einer Location auf einer Site vom Typ **Außenbereich** (Freiland), **Gewächshaus** oder **Balkon**; Innenbereich, Fensterbrett und Growzelt gelten standardmäßig nicht als frostexponiert. Du kannst diese Einstufung aber für jede einzelne Location übersteuern, siehe [Frostexposition einer Location festlegen](locations-substrates.md#frostexposition-einer-location-festlegen).
- Der Pflanze ist eine Pflanzenart zugeordnet (Stammdaten) — daraus leitet Kamerplanter die Frostempfindlichkeit ab.

---

## Wann der Plan angelegt wird

Kamerplanter legt den Plan sofort an, sobald deine Pflanze einem frostexponierten Standort zugeordnet ist — egal ob du die Pflanze dort neu anlegst oder sie nachträglich von einem anderen Standort dorthin umziehst. Ein eigener Schritt ist dafür nicht nötig.

!!! tip "Sicherheitsnetz zum Saisonwechsel"
    Falls eine Pflanze aus irgendeinem Grund noch keinen Plan hat — zum Beispiel, weil ihr die Pflanzenart nachträglich zugeordnet wurde —, holt Kamerplanter das spätestens beim Übergang deines Standorts in „Winter kündigt sich an" nach (siehe [Saison-Automatik](season-automation.md)).

Ziehst du eine Pflanze von einem Freiland-, Gewächshaus- oder Balkon-Standort in den Innenbereich um, entfernt Kamerplanter einen automatisch erstellten Plan wieder — sie braucht an ihrem neuen, geschützten Standort schließlich keinen Winterschutz mehr. Hast du den Plan zuvor selbst angepasst, bleibt er dagegen erhalten, auch nach einem Umzug nach drinnen; du kannst ihn dann jederzeit manuell löschen (siehe [Alle Überwinterungspläne im Überblick](#alle-uberwinterungsplane-im-uberblick)).

!!! note "Keine Überwinterung für abgeschlossene Pflanzen"
    Ist der Lebenszyklus deiner Pflanze bereits beendet — zum Beispiel, weil eine einjährige oder zweijährige Art nach der Blüte natürlich abgestorben ist, oder weil du sie manuell als geerntet, abgestorben oder abgebrochen markiert hast —, legt Kamerplanter für sie keinen neuen Überwinterungsplan mehr an, selbst wenn sie an einem Freiland-, Gewächshaus- oder Balkon-Standort steht. Ein bereits bestehender Plan bleibt davon unberührt und lässt sich weiterhin wie gewohnt einsehen oder löschen. <!-- REQ-047 -->

---

## Den automatischen Plan ansehen

1. Öffne **Pflanzen** > deine Pflanze.
2. Wechsle zum Tab **Pflege**.
3. Scrolle zum Abschnitt **Überwinterung**.

Was du dort siehst, hängt vom Standort deiner Pflanze und ihrer Winterhärte ab:

| Situation | Anzeige im Abschnitt „Überwinterung" |
|-----------|----------------------------------------|
| Profil bereits vorhanden | Der vollständige Plan (siehe unten) mit Badge „Automatisch aus Steckbrief" oder „Angepasst". |
| Winterhart an deinem Standort (grüne Ampel) | Hinweis, dass kein Winterschutz nötig ist. |
| Schutzbedürftig an einem Freiland-, Gewächshaus- oder Balkon-Standort, aber noch kein Profil vorhanden | Hinweis, dass die Pflanze im Winter Schutz braucht und der Plan automatisch angelegt wird. |
| An einem Innenbereich-, Fensterbrett- oder Growzelt-Standort | Hinweis, dass an diesem Standort keine Freiland-Überwinterung nötig ist. |

Liegt ein Profil vor, zeigt dir der Abschnitt „Überwinterung" den automatisch erstellten Plan: Winterhärte-Einstufung, Schutzmaßnahme und deren Monat, Gießvorgabe für die Winterruhe sowie — je nach Art — die Frühjahrsmaßnahme, die Bedingungen im Winterquartier oder die Kontrollintervalle für eingelagerte Knollen. Ein Badge **„Automatisch aus Steckbrief"** kennzeichnet, dass der Plan von Kamerplanter selbst erzeugt wurde.

!!! tip "Gilt diese Pflanze überhaupt als gefährdet?"
    Ist deine Pflanze an deinem Standort **winterhart** (grüne Ampel), erscheint im Abschnitt „Überwinterung" stattdessen der Hinweis, dass kein Winterschutz nötig ist — es wird bewusst **kein** Plan angelegt und **keine** Winterschutz-Erinnerung erzeugt. Mehr zur Winterhärte-Einstufung unter [Klimazonen & Winterhärte](../guides/climate-zones.md).

Der Winter-Pfad zeigt dir außerdem, wie die Pflanze überwintert:

| Winter-Pfad | Bedeutung |
|-------------|-----------|
| **In-situ (Schutz vor Ort)** | Die Pflanze bleibt an ihrem Standort und wird dort geschützt (z. B. mit Mulch oder Vlies). |
| **Verlagern (Winterquartier)** | Die Pflanze muss ins Winterquartier umziehen, oder ihre Knollen müssen ausgegraben und eingelagert werden. |

!!! tip "Kübelpflanzen werden strenger eingestuft"
    Steht deine Pflanze in einem Kübel oder Topf (also mit hinterlegtem Topfvolumen), stuft Kamerplanter ihre Winterhärte automatisch strenger ein als dieselbe Art im gewachsenen Freiland-Beet: Aus einer eigentlich nur „schutzbedürftigen" Einstufung (In-situ, Schutz vor Ort) wird für Kübelpflanzen automatisch „muss ins Winterquartier" (Verlagern) — der Wurzelballen im Topf friert deutlich schneller durch als im Erdboden. <!-- REQ-047 -->

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

!!! tip "Der hinterlegte Temperaturbereich wird aktiv überwacht"
    Hat das Winterquartier deiner Pflanze einen Sensor oder eine Home-Assistant-Anbindung mit Live-Temperaturwerten, prüft Kamerplanter stündlich, ob die gemessene Temperatur innerhalb des hier hinterlegten Bereichs bleibt — und legt bei einer echten Über- oder Unterschreitung sofort eine Erinnerung mit der Priorität „Hoch" an. Details dazu unter [Saison-Automatik](season-automation.md#was-sich-wahrend-der-winterruhe-andert). <!-- REQ-047 -->

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

Jede Zeile zeigt neben dem Löschen-Symbol ein Sprung-Icon **„Zur Pflanze springen"** bzw. **„Zum Pflanzdurchlauf springen"**, mit dem du direkt zur zugehörigen Pflanzeninstanz oder zum Pflanzdurchlauf wechselst — praktisch, wenn du von hier aus weitere Details nachschlagen willst.

### Pläne filtern

Über der Tabelle stehen dir zusätzlich zur Volltextsuche und Sortierung mehrere kombinierbare Filter zur Verfügung: <!-- REQ-047 -->

- **Winterhärte**: Winterhart / Schutz nötig / Frostfreies Quartier / Ausgraben & einlagern <!-- REQ-022 -->
- **Schutzmaßnahme**: z. B. Mulchen, Vlies, Anhäufeln, Ins Quartier holen, Ausgraben & lagern, Umwickeln
- **Monat der Maßnahme**: zeigt nur die Monate an, die tatsächlich in deinen Plänen vorkommen
- **Herkunft**: Auto (automatisch aus dem Steckbrief erzeugt) oder Manuell (von dir angepasst oder selbst angelegt)
- **Zuordnung**: Pflanze, Pflanzdurchlauf oder Ohne Zuordnung

Alle aktiven Filter wirken gemeinsam (ein Plan muss jeden gewählten Filter erfüllen) und zusätzlich zu Suche und Sortierung. Du kannst jeden Filter einzeln über sein Auswahlfeld oder alle auf einmal über **„Filter zurücksetzen"** wieder entfernen. Deine Filterauswahl steht in der URL — du kannst die gefilterte Ansicht also als Lesezeichen speichern oder mit anderen teilen. Auf schmalen Bildschirmen sind die Filter platzsparend hinter einem Symbol mit Zähler-Badge eingeklappt. Dieses Filterleisten-Muster verwendet Kamerplanter auch an anderer Stelle, zum Beispiel in der [Schädlingsliste](pest-management.md).

---

## Häufige Fragen

??? question "Ich habe noch nie ein Überwinterungsprofil angelegt — trotzdem sehe ich einen Plan. Woher kommt der?"
    Kamerplanter erstellt diesen Plan automatisch, sobald deine Pflanze einem Freiland-, Gewächshaus- oder Balkon-Standort zugeordnet wird — vorausgesetzt, sie gilt an diesem Standort nicht als winterhart. Das gilt sowohl beim Anlegen der Pflanze als auch bei einem späteren Standortwechsel; hatte die Pflanze zuvor noch keine Art zugeordnet, holt spätestens der Übergang deines Standorts in „Winter kündigt sich an" die Plan-Erstellung nach (siehe [Saison-Automatik](season-automation.md)). Du musst dafür nichts einrichten.

??? question "Warum sehe ich für meine winterharte Pflanze keinen Überwinterungsplan?"
    Das ist beabsichtigt. Für Pflanzen, die an deinem Standort winterhart sind, legt Kamerplanter bewusst keinen Plan an und erzeugt keine Winterschutz-Erinnerung, da sie ohne zusätzlichen Schutz auskommen.

??? question "Ich sehe den Hinweis, dass meine Pflanze im Winter Schutz braucht, aber noch keinen Plan. Was bedeutet das?"
    Deine Pflanze gilt an ihrem Standort als schutzbedürftig (gelbe oder rote Ampel), aber der Plan wurde noch nicht angelegt — zum Beispiel, weil ihr gerade erst eine Pflanzenart zugeordnet wurde. Kamerplanter legt den Plan automatisch an; du musst nichts weiter tun.

??? question "Ich habe meine Pflanze nach drinnen umgezogen — wohin ist der Überwinterungsplan verschwunden?"
    Ziehst du eine Pflanze von einem Freiland-, Gewächshaus- oder Balkon-Standort in den Innenbereich, entfernt Kamerplanter einen automatisch erstellten Plan wieder, da an einem Innenstandort keine Freiland-Überwinterung mehr nötig ist. Hast du den Plan zuvor selbst angepasst, bleibt er dir dagegen erhalten und muss bei Bedarf manuell gelöscht werden.

??? question "Was passiert, wenn ich einen Wert anpasse und sich später der Steckbrief der Art ändert?"
    Deine Anpassung bleibt erhalten. Sobald du mindestens einen Wert manuell änderst, überschreibt die Automatik ihn nie wieder — sie ergänzt lediglich Felder, die du nie gesetzt hast.

??? question "Kann ich ein Überwinterungsprofil auch löschen?"
    Ja, über die Tabelle unter **Pflanzen > Überwinterung** mit dem Papierkorb-Symbol. Bleibt die Pflanze an einem Freiland-, Gewächshaus- oder Balkon-Standort und ist sie nicht winterhart, legt Kamerplanter beim nächsten Standortwechsel oder spätestens beim nächsten Übergang in „Winter kündigt sich an" automatisch wieder einen neuen Plan an.

??? question "Warum wird meine Kübelpflanze strenger eingestuft als dieselbe Art im Beet?"
    Weil der Wurzelballen in einem Topf oder Kübel deutlich schneller durchfriert als im gewachsenen Boden. Kamerplanter erkennt ein hinterlegtes Topfvolumen und stuft eine eigentlich nur „schutzbedürftige" Pflanze in diesem Fall automatisch als „muss ins Winterquartier" ein.

??? question "Warum bekommt meine abgeblühte einjährige Pflanze keinen Überwinterungsplan?"
    Das ist beabsichtigt. Hat der Lebenszyklus einer Pflanze bereits geendet — etwa weil eine einjährige oder zweijährige Art nach der Blüte natürlich abgestorben ist oder du sie manuell als geerntet oder abgestorben markiert hast —, legt Kamerplanter keinen neuen Plan mehr für sie an, da sie keinen weiteren Winter mehr erleben wird. Ein bereits bestehender Plan bleibt unangetastet.

---

## Siehe auch

- [Saison-Automatik](season-automation.md) — wie Kamerplanter erkennt, wann der Winter beginnt und endet
- [Klimazonen & Winterhärte](../guides/climate-zones.md) — wie die Winterhärte-Ampel zustande kommt
- [Pflegeerinnerungen](care-reminders.md) — Gieß- und Pflegepläne allgemein
- [Wachstumsphasen](growth-phases.md) — Ruhephasen im Phasenmodell
