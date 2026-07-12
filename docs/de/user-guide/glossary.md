# Fachbegriff-Glossar

Das Fachbegriff-Glossar erklärt dir Begriffe wie VPD, EC oder Karenzzeit direkt in der Anwendung — kurz, auf deine Erfahrungsstufe zugeschnitten und ohne dass du die Dokumentation verlassen musst. Die Erklärungen kommen aus der kuratierten Wissensbasis des [KI-Assistenten](ai-assistant.md) und funktionieren auch ohne Anmeldung. <!-- REQ-035 -->

---

## Voraussetzungen

- Der Betreiber deiner Instanz muss KI-Funktionen instanzweit aktiviert haben. Ist das nicht der Fall, ist die Glossar-Seite genauso wenig erreichbar wie der [KI-Assistent](ai-assistant.md) — Details unter [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster).
- Eine Anmeldung ist **nicht** nötig: Das Glossar ist reine Wissensvermittlung ohne Bezug zu deinen konkreten Pflanzen und deshalb auch im anonymen [Light-Modus](light-mode.md) nutzbar.
- Nutzt dein Garten (Mandant) einen Cloud-Provider statt eines lokalen Modells als Standard, ist zusätzlich deine Einwilligung „KI-Verarbeitung über Cloud-Provider" nötig — siehe [Einwilligung erteilen](ai-assistant.md#einwilligung-erteilen). Im Light-Modus entfällt das, da dort ausschließlich lokal verarbeitet wird.

## Das Glossar durchsuchen

### Schritt 1: Glossar öffnen

Öffne im Menü **Glossar**. Du siehst eine Übersicht aller kuratierten Begriffe, gruppiert nach Kategorien wie **Umwelt & Klima**, **Düngung**, **Bewässerung**, **Wachstumsphasen**, **Freiland & Garten** und **Pflanzenschutz**.

### Schritt 2: Begriff auswählen

Tippe auf einen Begriff, um die vollständige Erklärung zu öffnen. Die Erklärung erscheint in derselben KI-Hülle wie beim KI-Assistenten — mit KI-Kennzeichnung, Modellname und einer aufklappbaren Quellenliste. Ein Klick auf **Zurück zur Übersicht** bringt dich zur Begriffsliste zurück.

!!! tip "Verwandte Begriffe direkt weiterverfolgen"
    Unter jeder Erklärung findest du anklickbare Chips mit verwandten Begriffen — zum Beispiel führt „VPD" zu „Blatttemperatur" und „Transpiration". Ein Klick öffnet direkt die nächste Erklärung, sodass du dich von Begriff zu Begriff weiterhangeln kannst, ohne zur Übersicht zurückzuspringen.

## Erklärungen passen sich deiner Erfahrungsstufe an

Die Erklärung, die du siehst, richtet sich nach deiner eingestellten [Erfahrungsstufe](onboarding.md) (Anfänger, Fortgeschritten, Experte). Als Anfänger bekommst du eine einfache Erklärung in Alltagssprache ohne genaue Zahlen; als Experte bekommst du dieselbe Erklärung mit konkreten Wertebereichen — zum Beispiel Ziel-EC-Werte je Wachstumsphase oder Substratabhängigkeiten. Änderst du deine Erfahrungsstufe in den Kontoeinstellungen, passen sich künftig abgerufene Erklärungen entsprechend an.

!!! example "Beispiel: Begriff „EC""
    - **Anfänger:** „EC misst, wie viele Nährstoffe im Wasser sind."
    - **Experte:** „Vegetativ: 1,0–1,4 mS/cm, Blüte: 1,4–1,8 mS/cm, abhängig vom Substrat (Hydro vs. Erde)."

## Wenn die Wissensbasis keinen passenden Treffer hat

Nicht zu jedem Begriff findet die Wissensbasis einen ausreichend relevanten Treffer. In diesem Fall zeigt dir das Glossar ehrlich eine redaktionell gepflegte Kurzdefinition anstelle einer KI-generierten Antwort, gekennzeichnet mit dem Hinweis „Kurzdefinition (kein Wissensbasis-Treffer)". So bekommst du nie eine erfundene oder unsichere Antwort vorgegaukelt.

## Fragezeichen-Symbol an Ort und Stelle

!!! note "Teilweise verfügbar: Fragezeichen-Symbole auf anderen Seiten"
    Das Fragezeichen-Symbol, das dieselbe Erklärung als kompaktes Popover direkt neben einem Fachbegriff öffnet, ist als Baustein bereits fertig gebaut und funktioniert überall dort korrekt, wo es eingebunden ist. Aktuell erscheint es aber noch auf keiner Pflanzen-, Dashboard- oder Substrat-Seite — die schrittweise Einbindung in bestehende Ansichten ist ein eigener, separater Arbeitsschritt. Bis dahin erreichst du dieselben Erklärungen über die Glossar-Übersicht oben. <!-- REQ-035 -->

Sobald das Symbol auf einer Seite eingebunden ist, funktioniert es so: Ein Klick auf das kleine Fragezeichen neben dem Begriff öffnet ein kompaktes Popover mit derselben Erklärung wie in der Glossar-Übersicht — inklusive verwandter Begriffe, Zurück-Navigation innerhalb des Popovers und einem eigenen Schließen-Knopf. Du musst dafür die Seite nicht verlassen.

## Light-Modus & anonyme Nutzung

Das Glossar ist eine der wenigen Funktionen, die vollständig ohne Benutzerkonto auskommt: Weder die Begriffsliste noch die einzelnen Erklärungen benötigen einen Tenant- oder Personenbezug, deshalb ist keine Einwilligung nötig und die Funktion steht im [Light-Modus](light-mode.md) genauso zur Verfügung wie im Voll-Modus. Im Light-Modus wird ausschließlich lokal verarbeitet — es kommt also nie ein externer Cloud-Provider zum Einsatz. Damit das Glossar für alle nutzbar bleibt, ist die Anzahl der Abfragen pro Minute für anonyme Nutzung begrenzt; solltest du sehr viele Begriffe hintereinander in kurzer Zeit öffnen, kann kurzzeitig eine Fehlermeldung erscheinen — warte in dem Fall einen Moment und versuche es erneut.

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

Das Glossar nutzt dieselbe instanzweite KI-Freischaltung wie der [KI-Assistent](ai-assistant.md#fuer-technische-nutzer-self-hoster) (`AI_FEATURES_ENABLED=true`), aber **nicht** die zusätzliche Garten-Freischaltung (Stufe 2) — es braucht also keine mandantenseitige Aktivierung von KI-Funktionen, weil es keine Pflanzendaten verwendet. Details zur Umgebungsvariable stehen unter [Umgebungsvariablen — KI-Assistent](../reference/environment-variables.md#ki-assistent).

Nutzt dein Garten (Mandant) einen Cloud-Provider als Standard-Provider, greift dennoch die reguläre Einwilligungsprüfung „KI-Verarbeitung über Cloud-Provider" (`ai_cloud_processing`), bevor eine Anfrage an den Cloud-Provider geht — siehe [Datenschutz & DSGVO](privacy.md#fuer-technische-nutzer-self-hoster). Fehlt die Einwilligung oder lässt sich der zugehörige Nutzer nicht zweifelsfrei bestimmen, wird die Anfrage sicherheitshalber abgelehnt statt lokal umgeleitet.

Jeder Glossar-Aufruf wird — wie beim KI-Assistenten — protokolliert, ohne dass Pflanzen- oder Kontodaten in der Anfrage an die Wissensbasis enthalten sind.

---

## Häufige Fragen

??? question "Muss ich angemeldet sein, um das Glossar zu nutzen?"
    Nein. Das Glossar funktioniert sowohl im Voll-Modus als auch im anonymen Light-Modus ohne Anmeldung — vorausgesetzt, der Betreiber hat KI-Funktionen instanzweit aktiviert.

??? question "Warum sehe ich manchmal „Kurzdefinition (kein Wissensbasis-Treffer)" statt einer ausführlichen Erklärung?"
    Das bedeutet, dass die Wissensbasis zu diesem Begriff keinen ausreichend relevanten Treffer gefunden hat. Statt eine unsichere KI-Antwort zu erfinden, zeigt dir das Glossar dann eine kurze, redaktionell geprüfte Definition.

??? question "Warum ändert sich die Erklärung, wenn ich meine Erfahrungsstufe wechsle?"
    Die Erklärung wird passend zu deiner eingestellten Erfahrungsstufe erzeugt — Anfänger bekommen Alltagssprache, Experten konkrete Wertebereiche. Nach einem Stufenwechsel gilt das für neu abgerufene Erklärungen.

??? question "Warum sehe ich das Fragezeichen-Symbol noch nicht neben Begriffen auf anderen Seiten?"
    Die Einbindung in bestehende Seiten (Pflanzen-Detailseite, Dashboard, Substrat-Editor und weitere) ist noch nicht abgeschlossen. Bis dahin findest du dieselben Erklärungen über die [Glossar-Übersicht](#das-glossar-durchsuchen).

## Siehe auch

- [KI-Assistent](ai-assistant.md)
- [Erfahrungsstufen im Onboarding-Wizard](onboarding.md)
- [Light-Modus](light-mode.md)
- [Datenschutz & DSGVO](privacy.md)
- [Statisches Fachbegriffe-Nachschlagewerk (Dokumentation)](../reference/glossary.md)
