# Rollen, Mandanten & Sichtbarkeit

Diese Seite ist der zentrale Ort für alle Fragen rund um Rollen: welche es gibt, wie sie mit dem Mandanten-Konzept zusammenspielen, warum du mehrere Rollen gleichzeitig haben kannst, und wer am Ende welche Daten zu sehen bekommt.

Sie beantwortet drei Fragen:

1. **Welche Rollen gibt es** — und auf welcher Ebene wirken sie?
2. **Wie hängen Rolle und Mandant zusammen** — und was passiert, wenn du in mehreren Gärten mitmachst?
3. **Wer sieht was** — insbesondere: bleiben deine Zimmerpflanzen privat, wenn du gleichzeitig im Kleingartenverein aktiv bist?

---

## Die drei Ebenen im Überblick

Berechtigungen entstehen in Kamerplanter aus drei voneinander unabhängigen Ebenen. Sie werden häufig verwechselt, sind aber getrennt zu betrachten:

| Ebene | Was sie steuert | Wo sie gilt | Werte |
|-------|-----------------|-------------|-------|
| **Mandanten-Rolle** | Was du innerhalb *eines* Gartens darfst | Pro Mandant getrennt | Admin, Gärtner, Beobachter |
| **Plattform-Rolle** | Ob du die Instanz verwalten darfst (globale Stammdaten, Mandantenübersicht) | Einmal für die gesamte Installation | Plattform-Administrator |
| **Kontoart** | Ob hinter dem Konto ein Mensch oder eine Maschine steckt | Pro Konto | Nutzerkonto, Dienstkonto |

Die entscheidende Eigenschaft: Die **Mandanten-Rolle hängt am Mandanten, nicht an dir**. Du hast keine „Kamerplanter-Rolle" — du hast pro Garten eine Rolle. Genau daraus ergibt sich alles Weitere auf dieser Seite.

!!! info "Was ist ein Mandant?"
    Ein **Mandant** (englisch „Tenant") ist ein abgeschlossener Behälter für Daten — dein privater Garten, ein Gemeinschaftsgarten, ein Betrieb. Jede Pflanze, jeder Standort, jede Aufgabe und jede Ernte gehört zu genau einem Mandanten. Eine ausführliche Einführung findest du unter [Mandanten & Gärten](../user-guide/tenants.md).

---

## Mandanten-Rollen: wer im Garten was darf

Innerhalb eines Mandanten hat jedes Mitglied **genau eine** von drei Rollen. Sie bilden eine Rangfolge: Admin schließt alles ein, was ein Gärtner darf; Gärtner schließt alles ein, was ein Beobachter darf.

| Rolle | Kurzbeschreibung | Typischer Einsatz |
|-------|------------------|-------------------|
| **Admin** | Vollzugriff innerhalb des Gartens, inklusive Mitglieder- und Einstellungsverwaltung | Vereinsvorstand, Eigentümer des privaten Gartens |
| **Gärtner** | Darf pflanzen, dokumentieren, Aufgaben abarbeiten — aber den Garten nicht verwalten | Aktives Vereinsmitglied mit eigener Parzelle |
| **Beobachter** | Darf alles lesen, nichts ändern | Interessierte Angehörige, Vereinsarchiv, Anzeige-Bildschirm |

### Das überarbeitete Rollenmodell

!!! note "Teilweise verfügbar: Rollenmodell"
    Für die Rollen ist eine Überarbeitung beschlossen, die die Tabelle oben ersetzen wird. Verfügbar sind heute die drei Rollen Admin, Gärtner und Beobachter. Was noch fehlt: die dritte fachliche Stufe **Leitung** und die Trennung der administrativen Rechte in **Verwaltung** und **Technik**. Bis dahin bündelt die heutige Admin-Rolle alles, was künftig auf Leitung, Verwaltung und Technik verteilt wird. <!-- REQ-049 §2.3, §2.4 -->

Das künftige Modell trennt zwei Fragen, die heute in einer einzigen Rangfolge stecken: was du **im Garten** tun darfst, und was du **am Garten** verwalten darfst.

**Fachliche Rollen — im Garten unterwegs.** Jedes Mitglied wird genau eine davon haben:

| Künftige Rolle | Wird dürfen | Gedacht für |
|----------------|-------------|-------------|
| **Beobachter** | Lesen, drucken, exportieren | Buchhaltung, Prüfung, Angehörige, Anzeige-Bildschirm |
| **Gärtner** | Zusätzlich anlegen, ändern, dokumentieren — aber **nicht löschen** | Vereinsmitglied, Schüler, Saisonkraft, angelernte Hilfe |
| **Leitung** | Zusätzlich löschen, Aufgaben an andere zuweisen, die Standortstruktur anlegen und umbauen, Vorlagen pflegen | Parzellenwart, Meister, Betriebsleitung |

Die Grenze zwischen Gärtner und Leitung verläuft entlang der Umkehrbarkeit: Ein Gärtner wird Fehler korrigieren können, indem er einen Wert überschreibt — Historie vernichten wird er nicht können.

**Administrative Zusatzberechtigungen — am Garten.** Diese wirst du zusätzlich zur fachlichen Rolle erhalten, unabhängig davon, welche du hast:

| Künftige Zusatzberechtigung | Wird umfassen | Gedacht für |
|-----------------------------|---------------|-------------|
| **Verwaltung** | Mitglieder einladen und entfernen, Rollen ändern, Garteneinstellungen, Parzellen zuordnen, Dienstkonten | Vorstand, Lehrkraft, Inhaber |
| **Technik** | Home Assistant und andere Integrationen anbinden, Sensoren konfigurieren, Import ausführen | Technikwart, betreuender Dienstleister |

Der praktische Gewinn: Rechte lassen sich künftig einzeln vergeben statt nur im Paket. Der Vorstand verwaltet Mitglieder, ohne die Sensorik anfassen zu müssen; das technikaffine Mitglied bindet Home Assistant an, ohne Zugriff auf die Mitgliederliste zu bekommen; und ein Schüler dokumentiert Messwerte, ohne versehentlich ein Beet löschen zu können.

### Rollenvergleich — was heute gilt

<!-- Quelle: src/backend/app/core/permissions.py, src/backend/app/common/auth.py -->

| Aufgabe | Admin | Gärtner | Beobachter |
|---------|:-----:|:-------:|:----------:|
| Alle Daten des Gartens lesen | Ja | Ja | Ja |
| Pflanzen anlegen, bearbeiten, entfernen | Ja | Ja† | Nein |
| Standorte, Bereiche und Stellplätze anlegen und bearbeiten | Ja | Ja‡ | Nein |
| Pflanzdurchläufe anlegen und weiterschalten | Ja | Ja | Nein |
| Aufgaben erstellen und erledigen | Ja | Ja | Nein |
| Ernten und Nacherntedaten dokumentieren | Ja | Ja | Nein |
| Gießen, Düngen und Behandlungen protokollieren | Ja | Ja | Nein |
| Tanks und Nährlösungen verwalten | Ja | Ja | Nein |
| Eigene Düngemittel und Nährstoffpläne anlegen | Ja | Ja | Nein |
| Pflegeerinnerungen bestätigen | Ja | Ja | Nein |
| Mitglieder einladen, Rollen ändern, Mitglieder entfernen | Ja | Nein | Nein |
| Garteneinstellungen ändern (Name, Kurzname, Stammdaten-Zuweisung) | Ja | Nein | Nein |
| Standort-Zuweisungen verwalten | Ja | Nein | Nein |
| Garten löschen | Ja | Nein | Nein |
| Mitgliederliste einsehen (Name und Rolle) | Ja | Ja | Ja |
| Den Garten selbst verlassen | Ja* | Ja | Ja |

*Als einziger Admin kannst du den Garten nicht verlassen, ohne vorher ein anderes Mitglied zum Admin zu machen — sonst bliebe der Garten ohne Verwaltung zurück.

†Mit dem überarbeiteten Modell wandert bei Pflanzen nur das **Entfernen** zur Leitung; Anlegen und Bearbeiten bleiben beim Gärtner. <!-- REQ-049 §2.3 -->

‡Diese Zeile wandert vollständig zur Leitung: Anlegen und Umbau der Standortstruktur werden dort gebündelt. <!-- REQ-049 §2.3, §4.1 -->

### Wer darf Mitglieder verwalten?

Mitgliederverwaltung ist bewusst allein dem Admin vorbehalten. Ein Admin kann außerdem nur Rollen vergeben, die seine eigene Rangstufe nicht überschreiten — es gibt also keinen Weg, sich über die Mitgliederverwaltung mehr Rechte zu verschaffen, als man selbst besitzt.

!!! note "Teilweise verfügbar: Gemeinschaftsfunktionen"
    Pinnwand, Gießrotation und gemeinsame Einkaufsliste sind für Gemeinschaftsgärten geplant, aber noch nicht umgesetzt. Sobald sie verfügbar sind, werden sie eigene Rechte in dieser Tabelle erhalten — bis dahin tauchen sie hier absichtlich nicht auf. <!-- REQ-024 §1a.3 -->

---

## Ein Mensch, mehrere Rollen gleichzeitig

Ein echter Nutzer hat in der Regel **mehrere Rollen gleichzeitig** — eine pro Garten, in dem er Mitglied ist. Das ist kein Sonderfall, sondern der Normalfall: Schon nach der Registrierung hast du deinen persönlichen Garten, in dem du automatisch Admin bist. Jede weitere Mitgliedschaft kommt mit ihrer eigenen, unabhängigen Rolle hinzu.

Wichtig dabei:

- **Eine Rolle pro Garten, aber beliebig viele Gärten.** Es gibt keine technische Obergrenze für die Zahl deiner Mitgliedschaften.
- **Die Rollen sind voneinander unabhängig.** Admin in einem Garten zu sein verschafft dir in einem anderen Garten kein einziges zusätzliches Recht.
- **Es zählt immer nur der Garten, in dem du gerade arbeitest.** Kamerplanter prüft bei jeder Aktion die Rolle in genau diesem Garten — nicht deine „höchste" Rolle irgendwo.
- **Deine Rolle kann sich jederzeit ändern.** Ein Vereinsadmin kann dich vom Gärtner zum Beobachter machen; das wirkt sofort und ausschließlich in diesem Garten.

### Beispiel: Wohnung und Kleingartenverein

Der typische Fall, für den dieses Modell gebaut ist:

| Garten | Art | Deine Rolle | Was darin liegt |
|--------|-----|-------------|-----------------|
| „Mein Zuhause" | Persönlich | **Admin** | Monstera im Wohnzimmer, Basilikum auf der Fensterbank, Balkonkästen |
| „Kleingartenverein Grüne Aue" | Organisation | **Gärtner** | Deine Parzelle 14, plus Gemeinschaftsflächen wie Gewächshaus und Kompost |
| „Schulgarten AG" | Organisation | **Beobachter** | Du schaust nur zu, dokumentierst nichts |

Ein und dieselbe Person ist hier gleichzeitig Admin, Gärtner und Beobachter — und das ohne jeden Konflikt, weil jede Rolle nur in ihrem eigenen Garten wirkt. Im Verein kannst du keine Mitglieder einladen (dafür bräuchtest du dort die Admin-Rolle), im Schulgarten kannst du nichts dokumentieren — in deinem Zuhause darfst du alles.

### Wie du zwischen deinen Gärten wechselst

Sobald du Mitglied in mehr als einem Garten bist, erscheint in der Navigationsleiste ein Auswahlfeld mit dem Namen des aktuellen Gartens. Ein Klick darauf zeigt alle deine Gärten; die Auswahl schaltet die gesamte Anwendung um — Dashboard, Pflanzenliste, Aufgaben, Kalender, Ernten. Du siehst also immer genau einen Garten auf einmal, nie eine Mischung aus mehreren.

Die schrittweise Anleitung dazu steht unter [Mandanten & Gärten](../user-guide/tenants.md#zwischen-tenants-wechseln).

---

## Wer bekommt welche Elemente zu sehen?

Für die Sichtbarkeit gibt es vier Kategorien. Jedes Element in Kamerplanter fällt in genau eine davon.

### Was zu genau einem Garten gehört

Diese Daten sind an einen Garten gebunden. Wer im Garten Mitglied ist, sieht sie **vollständig** — unabhängig von der Rolle, denn alle drei Rollen dürfen lesen. Wer nicht Mitglied ist, sieht sie überhaupt nicht.

<!-- Quelle: tenant_key-Filter in src/backend/app/data_access/arango/ -->

- Pflanzen und Pflanzenfotos
- Standorte, Bereiche und Stellplätze
- Pflanzdurchläufe und Nachsaat-Pläne
- Aufgaben und Arbeitsplanung
- Ernten und Nacherntedaten
- Gießprotokoll, Düngungen, Pflanzenschutz-Behandlungen und Kontrollgänge
- Tanks und tankbezogene Messwerte
- Sensoren und Aktoren des Gartens
- Eigene Düngemittel und Nährstoffpläne des Gartens
- Pflegeprofile und Überwinterungsprofile
- Dashboard-Kennzahlen und Kalender

Das heißt konkret: In einem Gemeinschaftsgarten sehen **alle Mitglieder alle Parzellen** — auch die, die ihnen nicht zugewiesen sind. Die Zuweisung von Standorten regelt das Bearbeiten, nicht das Lesen. Ein Gemeinschaftsgarten ist bewusst transparent aufgebaut: Wer den Kompost umsetzt oder wann in Parzelle 7 zuletzt gegossen wurde, soll für alle nachvollziehbar sein.

### Was dir persönlich gehört — über alle Gärten hinweg

Diese Daten hängen an deinem Konto, nicht an einem Garten. Sie folgen dir in jeden Garten, und kein Admin eines Gartens kann sie einsehen oder ändern:

<!-- Quelle: src/backend/app/domain/models/user_preference.py, notification_repository.py -->

- Dein Konto: E-Mail-Adresse, Anzeigename, Passwort, verknüpfte Anmeldeanbieter
- Deine Sitzungen und angemeldeten Geräte
- Sprache und Zeitzone
- Deine Erfahrungsstufe und die Auswahl sichtbarer Module
- Deine persönliche Dashboard-Anordnung
- Deine Benachrichtigungen und Benachrichtigungskanäle
- Deine Datenschutzanfragen (Datenauskunft, Löschung)

Deine Erfahrungsstufe gilt also für dich als Person — sie ist keine Einstellung „pro Garten". Benachrichtigungen sind ebenfalls persönlich: Andere Mitglieder sehen nicht, was dir zugestellt wurde.

### Was alle Gärten gemeinsam sehen

Der Stammdaten-Katalog ist bewusst nicht in Gärten aufgeteilt, sondern global. Er ist für jeden Garten **lesbar**, aber nur vom Plattform-Administrator veränderbar:

<!-- Quelle: tenant_key == "" Sentinel, src/backend/app/data_access/arango/collections.py -->

- Pflanzenarten, Sorten und botanische Familien
- Schädlinge, Krankheiten und Behandlungsmittel
- Globale Düngemittel und Nährstoffplan-Vorlagen
- Substrattypen und Arbeitsablauf-Vorlagen
- Klimazonen und agroklimatische Referenzdaten

Legst du in deinem Garten eine eigene Sorte oder ein eigenes Düngemittel an, bleibt das zunächst dein Garten-Datensatz. Nur der Plattform-Administrator kann so etwas in den globalen Katalog übernehmen, wo es dann für alle sichtbar wird.

### Was niemals über Gartengrenzen hinweg sichtbar ist

Es gibt in Kamerplanter **keinen** Weg, Daten zwischen Gärten zu teilen oder in einen anderen Garten hineinzusehen. Das ist eine Architekturentscheidung, keine Einstellung:

- Kein Admin eines Gemeinschaftsgartens sieht Daten aus deinem persönlichen Garten.
- Kein Mitglied eines Gartens sieht, in welchen anderen Gärten du Mitglied bist.
- Es gibt keine Freigabe-Funktion, mit der du eine einzelne Pflanze in einen anderen Garten „teilen" könntest.

Der Plattform-Administrator ist die einzige Ausnahme — siehe [Plattform-Rollen](#plattform-rollen-die-betreiber-ebene).

---

## Trennung von privater Pflege und Vereinsarbeit

Weil die Trennung von privaten Pflanzen und Vereinsarbeit der häufigste Grund für Rückfragen ist, hier noch einmal ausführlich am konkreten Fall.

### Deine Zimmerpflanzen bleiben privat

Bei der Registrierung entsteht automatisch dein **persönlicher Garten**, in dem du Admin bist. Alles, was du anlegst, ohne vorher bewusst in einen anderen Garten zu wechseln, landet dort: die Monstera, das Basilikum, die Balkonkästen. Dieser Garten ist von allen anderen vollständig abgeschottet — auch von Gärten, in denen du selbst Admin bist.

Ein Vereinsadmin sieht davon **nichts**: nicht die Pflanzen, nicht die Gießhistorie, nicht die Fotos, nicht die Aufgaben. Er sieht in der Mitgliederliste des Vereins lediglich deinen Anzeigenamen und deine Rolle im Verein.

### Die Vereinsparzelle bleibt beim Verein

Umgekehrt gilt dasselbe: Deine Parzelle 14 gehört dem Vereins-Garten, nicht dir. Wenn du den Verein verlässt, verlierst du den Zugriff auf diese Daten — sie bleiben beim Verein. Deine privaten Zimmerpflanzen sind davon nicht betroffen. Und wenn der Verein seinen Garten löscht, bleiben dein persönlicher Garten und alle anderen Mitgliedschaften unverändert bestehen.

### Was das für Aufgaben und Erinnerungen bedeutet

| Element | Wo es entsteht | Wer es sieht |
|---------|----------------|--------------|
| Gieß-Aufgabe für die Monstera | Persönlicher Garten | Nur du |
| Gieß-Aufgabe für Parzelle 14 | Vereins-Garten | Alle Vereinsmitglieder |
| Pflegeerinnerung „Basilikum gießen" | Persönlicher Garten | Nur du |
| Benachrichtigung über eine fällige Vereinsaufgabe | Vereins-Garten, zugestellt an dich | Nur du (die Aufgabe selbst sehen alle) |
| Deine Erfahrungsstufe „Fortgeschritten" | Dein Konto | Nur du, gilt in allen Gärten |

Die Konsequenz für den Alltag: Dein Dashboard und deine Aufgabenliste zeigen immer nur den **aktuell gewählten** Garten. Es gibt keine zusammengeführte Ansicht über alle Gärten hinweg — wenn du morgens sowohl deine Zimmerpflanzen als auch die Vereinsparzelle prüfen willst, wechselst du einmal den Garten. Benachrichtigungen erreichen dich dagegen unabhängig davon, welcher Garten gerade geöffnet ist.

---

## Standort-Zuweisungen innerhalb eines Gemeinschaftsgartens

Ein Garten ist eine **gemeinsame Arbeitsmenge**: Alle Gärtner pflegen alle Pflanzen und Aufgaben dieses Gartens. Es gibt innerhalb eines Gartens keine Aufteilung der Daten auf einzelne Mitglieder — wer im Garten Gärtner ist, darf jede Parzelle bearbeiten.

Eine Zuweisung ist deshalb eine **Absprache, keine Schranke**:

- **Standort-Zuweisung** — hält fest, wer sich um eine Parzelle kümmert. Sie steuert Sortierung, Filter und die Ansicht „meine Parzelle", schränkt das Bearbeiten aber nicht ein.
- **Aufgabenzuweisung** — hält fest, wer eine Aufgabe übernimmt. Die Aufgabe wird dieser Person hervorgehoben angezeigt; erledigen darf sie jeder Gärtner — etwa, wenn die zugewiesene Person kurzfristig ausfällt.
- **Beobachter** — lesen alles, ändern nichts, unabhängig von Zuweisungen.

!!! tip "Wenn du etwas wirklich für dich behalten willst"
    Dann gehört es in einen eigenen Garten. Die Trennung verläuft immer an der Gartengrenze, nie innerhalb eines Gartens. Genau dafür gibt es deinen persönlichen Garten — und du kannst jederzeit weitere Gärten anlegen, etwa einen nur für dich und deine Partnerin.

!!! example "Typischer Gemeinschaftsgarten"
    20 Parzellen, jede einem Mitglied zugeordnet, dazu Kompostbereich und Gewächshaus. Jedes Mitglied sieht auf einen Blick seine eigene Parzelle — kann aber einspringen, wenn jemand im Urlaub ist, ohne dass ein Admin etwas umstellen muss.

---

## Plattform-Rollen: die Betreiber-Ebene

Neben den Rollen innerhalb der Gärten gibt es eine Ebene darüber: die Verwaltung der Installation selbst. Sie ist an eine Admin-Mitgliedschaft in einem besonderen, technischen Mandanten gebunden, den man nicht wie einen Garten betreten kann.

<!-- Quelle: src/backend/app/common/auth.py -->

| Rolle | Was sie darf |
|-------|--------------|
| **Plattform-Administrator** | Globalen Stammdaten-Katalog pflegen; festlegen, welche globalen Arten ein Garten sieht; Übersicht über alle Gärten und Nutzerkonten; Anmeldeanbieter konfigurieren; Bilderkennung aktivieren; Garten-eigene Arten und Sorten in den globalen Katalog übernehmen; Gärten und Konten sperren oder wieder freischalten |

Ein Plattform-Administrator ist damit die einzige Rolle, die über Gartengrenzen hinweg blicken kann — allerdings nur auf **Verwaltungsdaten**: Er sieht, dass ein Garten existiert, wie er heißt und wer Mitglied ist. Er erhält dadurch nicht automatisch Lesezugriff auf die Pflanzen und Ernten eines fremden Gartens; dafür müsste ihn ein Admin dieses Gartens regulär als Mitglied aufnehmen.

Die Rolle ist unabhängig von den Garten-Rollen: Ein Plattform-Administrator ist in deinem privaten Garten trotzdem kein Mitglied. Umgekehrt macht Admin-Sein in einem Gemeinschaftsgarten niemanden zum Plattform-Administrator.

Was der Plattform-Bereich im Detail bietet, steht unter [Plattform-Admin](../user-guide/admin.md).

!!! warning "Noch nicht implementiert"
    Eine reine Lese-Rolle für den Plattform-Bereich ist geplant — gedacht für Monitoring und Prüfungen, ohne Schreibrechte auf globale Daten. Sie wird es ermöglichen, den Verwaltungsbereich einzusehen, ohne etwas ändern zu können. Derzeit gibt es nur den vollen Plattform-Administrator. <!-- REQ-024 §1a.4 Platform-Viewer -->

---

## Konten für Maschinen

Neben Konten für Menschen gibt es **Dienstkonten** für die Anbindung anderer Systeme — etwa Home Assistant, ein Auswertungs-Dashboard oder einen KI-Assistenten.

<!-- Quelle: src/backend/app/domain/models/user.py, src/backend/app/mcp_server/auth.py -->

Ein Dienstkonto ist technisch ein normales Konto mit zwei Besonderheiten: Es hat kein Passwort und kann sich nicht über die Oberfläche anmelden — es authentifiziert sich ausschließlich über einen Schlüssel. Und es erhält **dieselben Rollen wie ein Mensch**: Ein Dienstkonto mit der Gärtner-Rolle in deinem Garten darf genau das, was ein menschlicher Gärtner dort darf, und nicht mehr.

Daraus folgt die praktische Regel für die Einrichtung: Gib einem Dienstkonto die niedrigste Rolle, die für seine Aufgabe reicht. Ein Anzeige-Dashboard braucht **Beobachter**. Ein Automatisierungsdienst, der Gießvorgänge protokolliert, braucht **Gärtner**. **Admin** braucht ein Dienstkonto nur, wenn es Standorte anlegen oder Mitglieder verwalten soll — was selten der Fall ist.

Bei KI-Assistenten, die über die Werkzeug-Schnittstelle angebunden sind, wirkt dieselbe Rangfolge: Ein Beobachter-Konto darf ausschließlich abfragen, ein Gärtner-Konto darf zusätzlich dokumentieren, und einrichtende Eingriffe wie das Anlegen von Standorten bleiben Admin-Konten vorbehalten.

Die Einrichtung ist unter [Service Accounts](../api/service-accounts.md) beschrieben.

---

## Rollen im Light-Modus

Kamerplanter kann ohne Anmeldung betrieben werden — als lokale Einzelinstallation für eine Person. In diesem Betriebsmodus vereinfacht sich das ganze Rollenmodell zu einem einzigen Fall:

<!-- Quelle: src/backend/app/common/auth.py is_platform_admin -->

- Es gibt genau ein Konto, und es ist automatisch angemeldet.
- Dieses Konto ist Admin in seinem Garten **und** Plattform-Administrator.
- Es gibt keine Mitgliederverwaltung, keine Einladungen und keine Rollenwahl — es ist niemand da, dem man eine Rolle geben könnte.

Alles auf dieser Seite Beschriebene wird erst relevant, wenn die Installation mit Anmeldung betrieben wird. Der Wechsel ist möglich: Beim Umstieg wird das erste registrierte Konto zum Admin des bestehenden Gartens und zum Plattform-Administrator. Details unter [Light-Modus](../user-guide/light-mode.md).

---

## Für technische Nutzer / Self-Hoster

### Wo die Rollen technisch geprüft werden

Die Rolle wird bei jedem Zugriff auf einen mandantenbezogenen Pfad aus der Mitgliedschaft aufgelöst: Der Kurzname des Gartens steht im Pfad, daraus wird die Mitgliedschaft des angemeldeten Kontos gesucht. Fehlt sie oder ist sie inaktiv, endet die Anfrage mit `403`. Anschließend prüfen Endpunkte über eine Mindestrollen-Abhängigkeit, ob die aufgelöste Rolle ausreicht.

Die Isolation zwischen Gärten geschieht eine Ebene tiefer, in den Datenbankabfragen: Jede mandantenbezogene Abfrage filtert auf den Schlüssel des Gartens. Globale Katalogdaten werden über einen leeren Mandanten-Schlüssel markiert und in Abfragen zusätzlich zugelassen — daher sind sie überall lesbar.

Die Oberfläche blendet Schreibaktionen für die Beobachter-Rolle aus; sie liest die Rolle aus dem aktiven Garten und leitet daraus ab, ob Bearbeiten-Schaltflächen erscheinen.

### Grenzen der aktuellen Durchsetzung

Drei Einschränkungen sind für den Betrieb wichtig, weil die Spezifikation hier weiter ist als die Umsetzung:

- **Die Beobachter-Rolle ist noch keine belastbare Schranke.** Ein erheblicher Teil der schreibenden Endpunkte prüft derzeit nur die Mitgliedschaft im Garten, nicht die Mindestrolle. Wer die Schnittstelle direkt anspricht, kann als Beobachter deshalb Daten anlegen und ändern, obwohl die Oberfläche das nicht anbietet. Vergib die Beobachter-Rolle daher als organisatorische Festlegung, nicht als Sicherheitsgrenze gegenüber einem Mitglied, dem du nicht vertraust. Vollständig durchgesetzt ist die Rangfolge unter anderem bei Aktorik, Vermehrung, Aquaponik, Nachernte, Inventar und Mitgliederverwaltung.
- **Benachrichtigungen erreichen bisher nur eine Person.** Nach dem Zielbild wird jede fällige Aufgabe allen Gärtnern des Gartens zugestellt. Umgesetzt ist derzeit ein einzelner Empfänger — wer die Aufgabe angelegt oder zuletzt bearbeitet hat, ersatzweise die zugewiesene Person. Entsteht eine Pflegeaufgabe automatisch und ist niemand zugewiesen, wird derzeit **niemand** benachrichtigt.
- **Einige Nebenpfade rund um die Pflanze liegen außerhalb der Gartenprüfung.** Die eigentlichen Pflanzen-Endpunkte prüfen die Zugehörigkeit zum Garten bei jedem Zugriff sauber. Drei ältere Pfade sind jedoch nicht garten-, sondern nur anmeldegebunden: die Wachstumsphasen einer Pflanze, ihre Pflegeerinnerungen und eine ältere Dashboard-Zusammenfassung. Wer den Schlüssel einer fremden Pflanze kennt, kann darüber Phasen- und Pflegedaten lesen und ändern. Ebenso sind die schreibenden Zugriffe auf den globalen Stammdaten-Katalog (Arten, Lebenszyklen, Phasenprofile) noch nicht auf die Plattform-Rolle beschränkt.

Die ersten beiden Punkte betreffen nur die Abstufung **innerhalb** eines Gartens. Der dritte betrifft die Trennung **zwischen** Gärten: Für die Kernressourcen — Pflanzenliste, Standorte, Aufgaben, Ernten, Fotos — ist sie in allen Abfragen durchgesetzt; für die genannten Nebenpfade ist sie es noch nicht. Betreibe eine Instanz mit mehreren, einander unbekannten Parteien daher vorerst nur mit vertrauenswürdigen Konten.

### Standort-Zuweisungen über die API

Zuweisungen werden unter dem Pfad `/api/v1/t/{garten-kurzname}/assignments` verwaltet; sämtliche schreibenden Aufrufe dort sind der Admin-Rolle vorbehalten. Eine Zuweisung verbindet eine Mitgliedschaft mit einem Standort und trägt ein Kennzeichen für den Bearbeitungswunsch sowie ein freies Notizfeld. Die zugehörigen Aufrufe stehen im Frontend bereits als Schnittstellenfunktionen bereit, sind aber noch an keine Seite angebunden.

---

## Häufige Fragen

??? question "Kann ich in einem Garten Admin und in einem anderen nur Beobachter sein?"
    Ja, und das ist der Normalfall. Rollen gelten immer nur für einen Garten. Deine Rolle in einem Garten hat keinerlei Auswirkung auf einen anderen.

??? question "Sehen die Vereinsmitglieder meine Zimmerpflanzen?"
    Nein. Deine Zimmerpflanzen liegen in deinem persönlichen Garten, der von allen anderen Gärten vollständig getrennt ist. Vereinsmitglieder sehen in der Mitgliederliste nur deinen Anzeigenamen und deine Rolle im Verein.

??? question "Sehen andere Vereinsmitglieder meine Parzelle im Verein?"
    Ja. Innerhalb eines Gartens dürfen alle Mitglieder alles lesen — auch fremde Parzellen. Die Zuweisung von Standorten ist dafür gedacht, das *Bearbeiten* zu regeln, nicht das Lesen. Wenn du etwas wirklich privat halten willst, gehört es in deinen persönlichen Garten.

??? question "Kann ein Vereinsadmin meine Rolle ändern, ohne mich zu fragen?"
    Ja, innerhalb seines Gartens. Er kann dich dort zum Beobachter machen oder ganz entfernen. Auf deinen persönlichen Garten und deine anderen Mitgliedschaften hat er keinen Zugriff.

??? question "Was passiert mit meinen Daten, wenn ich den Verein verlasse?"
    Was du im Vereins-Garten dokumentiert hast, bleibt dort — die Daten gehören dem Garten, nicht dir. Du verlierst lediglich den Zugriff. Dein persönlicher Garten ist davon nicht betroffen.

??? question "Gibt es eine Ansicht über alle meine Gärten hinweg?"
    Nein. Du siehst immer genau einen Garten. Benachrichtigungen sind die Ausnahme: Sie erreichen dich unabhängig davon, welcher Garten gerade geöffnet ist.

??? question "Wie bekomme ich Rechte für den Plattform-Bereich?"
    Über eine Admin-Mitgliedschaft im technischen Plattform-Mandanten — die vergibt ein bestehender Plattform-Administrator. Bei einer eigenen Installation erhält das erste registrierte Konto diese Rolle automatisch.

??? question "Braucht Home Assistant ein Admin-Konto?"
    Nein. Ein Dienstkonto mit der Gärtner-Rolle genügt zum Lesen und Dokumentieren; nur zum Anlegen von Standorten wäre Admin nötig.

---

## Siehe auch

- [Mandanten & Gärten](../user-guide/tenants.md) — Gärten anlegen, Mitglieder einladen, Garten wechseln
- [Konto & Anmeldung](../user-guide/account.md) — Registrierung, Anmeldeanbieter, Sitzungen
- [Plattform-Admin](../user-guide/admin.md) — der Verwaltungsbereich im Detail
- [Light-Modus](../user-guide/light-mode.md) — Betrieb ohne Anmeldung
- [Service Accounts](../api/service-accounts.md) — Konten für Maschinen einrichten
- [Datenschutz (DSGVO)](../user-guide/privacy.md) — deine Rechte an deinen Daten
- [Datenbankschema](database-schema.md) — Collections und Kanten hinter Mandanten und Mitgliedschaften
