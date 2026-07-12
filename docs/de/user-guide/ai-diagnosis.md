# KI-Diagnose

Mit der KI-Diagnose beschreibst du Symptome deiner Pflanze über einen kurzen, geführten Assistenten — statt eine freie Chat-Frage zu formulieren, wählst du aus einem kuratierten Katalog aus. Du erhältst die **drei wahrscheinlichsten Ursachen** mit Konfidenz, Begründung und empfohlenen Maßnahmen, jeweils verknüpft mit dem passenden Eintrag im [Pflanzenschutz (IPM)](pest-management.md)-System.

!!! note "Teilweise verfügbar"
    Die KI-Diagnose ist als eigenständige Seite **KI-Diagnose** (`/diagnose`) nutzbar: Du wählst Symptome aus einem kuratierten Katalog, ergänzst optional eine Anmerkung und erhältst eine KI-gestützte Top-3-Einschätzung mit Verknüpfung zum Pflanzenschutz-System. Aktuell **nicht** umgesetzt sind eine Verknüpfung mit einer konkreten Pflanze oder Pflanzdurchlauf, ein Foto-Upload direkt im Assistenten sowie eine gespeicherte Diagnose-Historie — jede Sitzung ist zustandslos und wird nach der Antwort nicht aufbewahrt. Auch einen eigenen Menüpunkt im Seitenmenü gibt es noch nicht. Die folgenden Abschnitte beschreiben den heutigen Stand im Präsens. <!-- REQ-036 -->

!!! warning "Einschätzung — keine sichere Diagnose"
    Jede Antwort ist eine KI-gestützte Einschätzung auf Basis der von dir ausgewählten Symptome, keine gesicherte Diagnose. Bitte prüfe den Befund selbst, bevor du eine Behandlung startest. Die KI-Diagnose löst **niemals** automatisch eine Behandlung aus, und ein bestehendes Karenz-Gate (gesetzliche Wartefrist zwischen Behandlung und Ernte) bleibt in jedem Fall aktiv.

!!! note "Voll-Modus und Einwilligung erforderlich"
    Die KI-Diagnose steht nur angemeldeten Nutzerinnen und Nutzern zur Verfügung. Im **[Light-Modus](light-mode.md)** (anonymer Zugang) ist die Funktion nicht verfügbar. Zusätzlich braucht die Analyse — wie beim [KI-Assistenten](ai-assistant.md) — alle drei Freischaltungsstufen (Betreiber, dein Garten/Mandant, deine Einwilligung „KI-Zugriff auf deine Pflanzendaten"). Fehlt eine davon, lässt sich der Assistent zwar bis zum letzten Schritt ausfüllen, die Analyse selbst schlägt dann aber mit einer allgemeinen Fehlermeldung fehl (siehe [Wenn die Analyse fehlschlägt](#wenn-die-analyse-fehlschlaegt)).

---

## Voraussetzungen

- Angemeldetes Benutzerkonto (kein Light-Modus)
- KI-Funktionen müssen instanzweit und für deinen Garten (Mandanten) freigeschaltet sein
- Deine Einwilligung „KI-Zugriff auf deine Pflanzendaten" (`ai_tenant_data_access`) muss erteilt sein — Details unter [KI-Assistent: Einwilligung erteilen](ai-assistant.md#einwilligung-erteilen)

---

## Was die KI-Diagnose leistet

Die KI-Diagnose ist ein **strukturierter, symptombasierter** Weg zu einer Einschätzung — du beschreibst, was du an deiner Pflanze siehst, statt eine offene Frage zu formulieren. Das reduziert Fachbegriff-Hürden und liefert der KI ein klar umrissenes Eingabeformat.

!!! info "Abgrenzung zur Foto-basierten Erkennung"
    Die KI-Diagnose arbeitet **textbasiert**: Du wählst Symptome aus, keine Bilder. Sie ist damit etwas anderes als die bildbasierten Funktionen in Kamerplanter:

    - [Pflanze per Foto identifizieren](plant-identification.md) bestimmt die **Art** einer unbekannten Pflanze aus einem Foto.
    - [Schädlingserkennung per Foto](pest-detection.md) erkennt Schädlinge und typische Schadbilder aus einem Foto einer bereits bekannten Pflanze.

    Im Kontext-Schritt der KI-Diagnose (siehe unten) weist ein Hinweis auf die bestehende Foto-Erkennung hin, falls ein Bild zusätzlichen Anhaltspunkt liefern könnte — die KI-Diagnose selbst nimmt aber kein Foto entgegen und wertet keines aus.

---

## So startest du

Du erreichst die KI-Diagnose aktuell direkt über die Adresse `/diagnose` in deinem Browser — im Seitenmenü gibt es dafür noch keinen eigenen Eintrag.

Der Assistent führt dich in drei Schritten durch die Diagnose: **Symptome**, **Kontext** und **Ergebnis**. Eine Fortschrittsanzeige oben zeigt, in welchem Schritt du dich befindest.

### Schritt 1: Symptome auswählen

Der Katalog enthält über 30 kuratierte Symptome, gruppiert nach Kategorie (zum Beispiel „Verfärbung der Blätter", „Sichtbare Schädlinge" oder „Wachstumsstörung"). Setze ein Häkchen bei allen Symptomen, die auf deine Pflanze zutreffen — mehrere Auswahlen sind möglich.

!!! tip "Mögliche Ursachen vorab ansehen"
    Neben vielen Symptomen zeigt ein kleines Info-Symbol beim Antippen oder Hovern einen kurzen Hinweis auf typische Ursachen — das hilft dir schon bei der Auswahl, die richtigen Symptome zu erkennen.

Sobald du mindestens ein Symptom ausgewählt hast, wird die Schaltfläche **Weiter** aktiv.

### Schritt 2: Kontext ergänzen (optional)

In diesem Schritt kannst du optional eine Anmerkung im Freitextfeld hinterlassen (bis zu 2000 Zeichen), zum Beispiel zu Standort, Gießverhalten oder wann das Symptom erstmals aufgetreten ist.

!!! note "Deine Anmerkung wird nicht im Wortlaut übermittelt"
    Aus Datenschutzgründen wird dein Freitext **nicht** an das Sprachmodell weitergegeben. Die KI erhält lediglich den neutralen Hinweis, dass du eine Anmerkung gemacht hast — dein Text selbst bleibt bei dir.

Darunter findest du einen Hinweis mit einem Link zur bestehenden Foto-Erkennung, falls ein Foto zusätzlichen Anhaltspunkt liefern könnte (siehe [Abgrenzung zur Foto-basierten Erkennung](#was-die-ki-diagnose-leistet) oben).

Klicke auf **Diagnose starten**, um die Analyse auszulösen — oder auf **Zurück**, um deine Symptomauswahl zu ändern.

### Schritt 3: Ergebnis lesen

Nach wenigen Sekunden erscheinen die **drei wahrscheinlichsten Ursachen**, absteigend nach Konfidenz sortiert.

---

## Ergebnis verstehen

Jede der drei Diagnose-Karten zeigt:

- **Rang und Name** der vermuteten Ursache, bei botanisch benennbaren Ursachen ergänzt um den wissenschaftlichen Namen
- **Konfidenz** in Prozent, farblich abgestuft (grün = hoch, blau = mittel, orange = niedrig)
- **Begründung**, warum die KI zu dieser Einschätzung kommt
- **Empfohlene Maßnahmen** als Aufzählung

Erkennt das System einen Treffer in den Schädlings-Stammdaten, verlinkt die Karte zusätzlich direkt zur passenden [Schädlings-Detailseite](pest-detail.md) sowie zu vorgeschlagenen Behandlungen. Trägt eine vorgeschlagene Behandlung eine Karenzzeit (gesetzliche Wartefrist zwischen Behandlung und Ernte, siehe [Glossar](../reference/glossary.md#karenzzeit-pre-harvest-interval-phi)), ist das an der Behandlungs-Chip deutlich mit einem Warnsymbol und der Anzahl Tage gekennzeichnet.

Die Antwort ist zusätzlich in die für alle KI-Antworten übliche Hülle eingebettet — KI-Kennzeichnung, aufklappbare Quellenangaben aus der Wissensbasis sowie Hinweise, ob deine Pflanzendaten oder ein Cloud-Provider verwendet wurden. Details dazu stehen unter [KI-Assistent: Transparenz](ai-assistant.md#transparenz-woran-du-eine-ki-antwort-erkennst).

Über die Schaltfläche **Neue Diagnose** startest du den Assistenten mit leerer Symptomauswahl neu.

### Wenn die Analyse fehlschlägt {#wenn-die-analyse-fehlschlaegt}

Schlägt die Analyse fehl, zeigt der Assistent eine allgemeine Fehlermeldung, unabhängig von der genauen Ursache — etwa wenn KI-Funktionen nicht freigeschaltet sind, deine Einwilligung fehlt, die Wissensbasis nicht erreichbar ist oder die KI kein auswertbares Ergebnis liefert. Prüfe in diesem Fall zunächst die drei Freischaltungsstufen unter [KI-Assistent](ai-assistant.md#so-ist-der-ki-assistent-aufgebaut-drei-stufen-freischaltung) und versuche es anschließend erneut.

---

## Von der Diagnose zur Behandlung

Verweist eine Diagnose auf einen bekannten Schädling, kannst du direkt über den Link **Schädling im Detail ansehen** zur [Schädlings-Detailseite](pest-detail.md) wechseln und von dort eine Befallskontrolle im [Pflanzenschutz-System (IPM)](pest-management.md) anlegen. Trägt eine vorgeschlagene Behandlung eine Karenzzeit, wird diese auf der [Behandlungs-Detailseite](treatment-detail.md) berücksichtigt — das System löst nie automatisch eine Behandlung aus, die Entscheidung triffst immer du selbst.

---

## Häufige Fragen

??? question "Warum finde ich die KI-Diagnose nicht im Seitenmenü?"
    Die Funktion hat aktuell noch keinen eigenen Eintrag im Seitenmenü. Du erreichst sie direkt über die Adresse `/diagnose`.

??? question "Kann ich der Diagnose ein Foto beifügen?"
    Nicht direkt im Assistenten. Im Kontext-Schritt findest du einen Link zur bestehenden Foto-Erkennung — für eine Schädlingserkennung nutzt du die [Schädlingserkennung per Foto](pest-detection.md), für eine reine Artbestimmung die [Pflanzenbestimmung per Foto](plant-identification.md).

??? question "Ist das dasselbe wie die geplante Foto-Diagnose für Krankheiten und Nährstoffmängel?"
    Nein. Die KI-Diagnose ist symptom- und textbasiert und heute nutzbar. Eine ergänzende, bildbasierte Zustandsdiagnose speziell für Krankheiten und Nährstoffmängel ist als eigenes Feature geplant beziehungsweise als API bereits vorhanden, aber noch nicht in eine Oberfläche eingebunden — siehe [Meiner Pflanze geht es schlecht — was tun?](plant-health-troubleshooting.md#geplante-erweiterung-foto-diagnose-fur-krankheiten-und-mangel).

??? question "Warum bekomme ich immer eine allgemeine Fehlermeldung, wenn etwas nicht funktioniert?"
    Der Assistent unterscheidet aktuell noch nicht zwischen den möglichen Fehlerursachen (fehlende Freischaltung, fehlende Einwilligung, nicht erreichbare Wissensbasis oder ein unauswertbares KI-Ergebnis) — in allen Fällen erscheint dieselbe allgemeine Meldung. Prüfe im Zweifel die [Freischaltungsstufen des KI-Assistenten](ai-assistant.md#so-ist-der-ki-assistent-aufgebaut-drei-stufen-freischaltung).

??? question "Wird meine Diagnose gespeichert, damit ich sie später wiederfinde?"
    Nein. Jede Sitzung ist zustandslos: Es wird nur ein anonymisierter, gehashter Eintrag im internen KI-Audit-Log geschrieben (ohne Klartext deiner Symptome oder Anmerkungen), aber keine Diagnose-Historie, die du dir später ansehen könntest.

---

## Siehe auch

- [Pflanzenschutz (IPM)](pest-management.md) — Inspektionen, Behandlungen, Karenzzeiten
- [Schädlings-Detailseite](pest-detail.md) — Steckbrief, Referenzbilder, Gegenmaßnahmen
- [Behandlungs-Detailseite](treatment-detail.md) — Details zu vorgeschlagenen Behandlungen
- [Meiner Pflanze geht es schlecht — was tun?](plant-health-troubleshooting.md) — Symptom-Nachschlagetabelle als erste Einschätzung
- [Schädlingserkennung per Foto](pest-detection.md) — bildbasierte Erkennung von Schädlingen
- [Pflanze per Foto identifizieren](plant-identification.md) — Artbestimmung unbekannter Pflanzen
- [KI-Assistent](ai-assistant.md) — Freischaltungsstufen, Einwilligungen und Transparenz-Kennzeichnung
- [Datenschutz & DSGVO](privacy.md) — Einwilligungen und Betroffenenrechte
