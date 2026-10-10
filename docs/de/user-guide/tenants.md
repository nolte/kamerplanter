# Mandanten & Gärten

Kamerplanter ist eine Multi-Tenant-Plattform: Deine Daten sind in **Tenants** (Mandanten) organisiert — isolierten Behältern, die genau einer Organisationsform entsprechen. Du kannst gleichzeitig Mitglied in mehreren Tenants sein, zum Beispiel in deinem privaten Balkongarten und im Gemeinschaftsgarten des Vereins.

---

## Was ist ein Tenant?

Ein Tenant ist der zentrale Isolations-Container für alle Ressourcen: Pflanzen, Standorte, Aufgaben, Ernten und Pflegedaten gehören immer zu genau einem Tenant. Andere Tenants können diese Daten nicht sehen.

| Tenant-Typ | Anwendungsfall | Beispiel |
|------------|---------------|---------|
| **Persönlich** | Privater Garten, Balkongarten, Zimmerpflanzen | Dein eigener Garten |
| **Organisation** | Gemeinschaftsgarten, Verein, Betrieb | "Grüne Oase e.V.", Cannabis-Anbauvereinigung |

### Persönlicher Tenant

Bei der Registrierung erstellt das System automatisch deinen **persönlichen Tenant**. Du hast dort automatisch die Rolle **Leitung** und beide Zusatzberechtigungen (**Verwaltung** und **Technik**). Alle Ressourcen, die du in Kamerplanter anlegst, landen standardmäßig in deinem persönlichen Tenant.

!!! info "Persönliche Daten bleiben privat"
    Dein persönlicher Tenant ist vollständig von allen anderen Tenants isoliert. Kein Mitglied eines anderen Tenants kann deine privaten Zimmerpflanzen oder deinen Balkongarten sehen — auch wenn du demselben Gemeinschaftsgarten angehörst.

!!! warning "Dein persönlicher Tenant endet mit deinem Konto"
    Lädst du jemanden in deinen persönlichen Tenant ein, wird er mit deinem Konto gelöscht — auch mit allem, was die anderen Mitglieder darin angelegt haben. Sie bekommen eine E-Mail, sobald du die Löschung beantragst. Für einen Garten, den ihr gemeinsam und dauerhaft führen wollt, lege deshalb einen eigenen Gemeinschaftsgarten an. Details: [Datenaufbewahrung](../guides/data-retention.md#was-mit-deinem-personlichen-garten-passiert).

!!! info "Mitgliederlimit"
    Jeder Tenant hat ein Mitgliederlimit. Dein persönlicher Tenant startet mit **1** — dir selbst. Willst du jemanden in deinen persönlichen Tenant einladen, hebe das Limit vorher an; sonst bekommt die eingeladene Person beim Annehmen die Meldung, dass der Tenant voll ist. Ein Gemeinschaftsgarten startet mit dem Höchstwert, den der Betreiber der Plattform festlegt (Standard: 50); höher geht es nicht. <!-- Issue #2133 -->

---

## Zwischen Tenants wechseln

Wenn du Mitglied in mehreren Tenants bist, siehst du in der Navigationsleiste einen **Tenant-Selektor** oben links.

1. Klicke auf den Tenant-Namen in der Navigationsleiste
2. Es öffnet sich ein Dropdown mit all deinen Tenants
3. Klicke auf den gewünschten Tenant — die Ansicht wechselt sofort

Der aktuell aktive Tenant ist in der Navigationsleiste hervorgehoben. Die URL enthält den Tenant-Slug: `/t/gruene-oase/standorte/...`

---

## Aktiver Tenant: Katalog-Sicht und neue Einträge

Bist du Mitglied in einem Gemeinschaftsgarten, wirkt sich der aktiv gewählte Tenant auch auf den **Pflanzenkatalog** aus — also auf Pflanzenarten, Sorten und botanische Familien.

- **Die Katalog-Sicht folgt dem aktiven Tenant.** Ist ein Gemeinschaftsgarten aktiv, siehst du den globalen Basis-Katalog **plus** die Arten und Sorten, die genau dieser Garten selbst angelegt hat. Arten und Sorten eines *anderen* deiner Gärten bleiben ausgeblendet, solange dieser andere Garten nicht aktiv ist.
- **Neue Einträge gehören dem aktiven Tenant.** Legst du eine neue Pflanzenart oder Sorte an, während ein Gemeinschaftsgarten aktiv ist, gehört der neue Eintrag diesem Garten — nicht deinem persönlichen Garten. Wechsle deshalb erst bewusst den aktiven Tenant, bevor du eine Sorte für den Verein anlegst.

!!! warning "Häufiger Irrtum: Vereinigung statt Kontextwechsel"
    Der aktive Tenant zeigt **nicht** „alles, was ich in irgendeinem meiner Gärten je angelegt habe". Er zeigt genau die Sicht des gerade gewählten Gartens. Bist du in drei Gärten Mitglied, siehst du je nach aktivem Tenant drei verschiedene Ausschnitte des Katalogs — nie alle drei gleichzeitig kombiniert. Wechsle den Tenant-Selektor, um die Katalog-Einträge eines anderen Gartens zu sehen.

Zum Anlegen einer neuen Pflanzenart oder Sorte brauchst du mindestens die Rolle Gärtner im aktiven Tenant; als Beobachter kannst du den Katalog nur lesen. Details dazu stehen unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md).

---

## Was für alle deine Gärten gleich bleibt

Einige Einstellungen gehören dir, nicht einem Garten. Sie gelten in jedem Tenant, in dem du Mitglied bist, und wechseln **nicht** mit dem Tenant-Selektor:

- dein **Dashboard-Layout** — welche Widgets wo stehen;
- deine **Benachrichtigungs-Einstellungen** — Kanäle, Ruhezeiten, Bündelung und Eskalation;
- welche **Module** du eingeblendet hast, dein Onboarding-Stand und deine **Favoriten**.

Was ein Widget anzeigt, kommt dagegen immer aus dem gerade aktiven Garten: Dasselbe Dashboard zeigt im Gemeinschaftsgarten dessen Pflanzen und Aufgaben, in deinem persönlichen Garten deine eigenen. Eine Benachrichtigung über Home Assistant geht nur an Ziele, die für den Garten der Benachrichtigung freigegeben sind.

---

## Gemeinschaftsgarten erstellen

### Neuen Tenant anlegen

1. Klicke auf den Tenant-Selektor in der Navigationsleiste
2. Wähle **Neuen Garten erstellen**
3. Fülle das Formular aus:

    | Feld | Beschreibung | Beispiel |
    |------|-------------|---------|
    | **Name** | Anzeigename des Gartens | Grüne Oase e.V. |
    | **Slug** | URL-freundlicher Kurzname (auto-generiert) | gruene-oase |
    | **Typ** | Art der Organisation | Organisation |
    | **Beschreibung** | Kurze Beschreibung (optional) | Gemeinschaftsgarten im Westpark |

4. Klicke auf **Erstellen**

Du bist automatisch **Leitung** des neuen Tenants und hast beide Zusatzberechtigungen (**Verwaltung** und **Technik**).

---

## Mitglieder einladen

Mit der Zusatzberechtigung **Verwaltung** kannst du Mitglieder auf drei Wegen einladen:

!!! note "Ist der Tenant voll, bleibt die Einladung offen"
    Hat dein Tenant sein Mitgliederlimit erreicht, kann niemand mehr beitreten — weder über eine E-Mail-Einladung noch über einen Einladungslink. Die Einladung verfällt dadurch nicht: Sobald ein Platz frei wird (jemand verlässt den Tenant) oder du das Limit anhebst, kann sie angenommen werden. Mitglieder, die schon dabei sind, bleiben es in jedem Fall — auch wenn du das Limit unter die aktuelle Mitgliederzahl senkst. <!-- Issue #2133 -->

### Methode 1: E-Mail-Einladung

1. Navigiere zu **Einstellungen** > **Mitglieder** > **Einladen**
2. Gib die E-Mail-Adresse des Mitglieds ein
3. Die Einladung vergibt die Rolle **Beobachter** — eine andere Rolle gibst du dem Mitglied nach dem Beitritt unter [Rollen ändern](#rollen-andern)
4. Klicke auf **Einladung senden**

Kamerplanter schickt der Adresse eine E-Mail mit einem Link zur Annahme-Seite; er ist 7 Tage gültig. Wer ihn öffnet, meldet sich an — oder registriert sich mit genau dieser Adresse —, bestätigt auf der Annahme-Seite mit **Einladung annehmen** und wird deinem Tenant mit der vorgewählten Rolle hinzugefügt. Wer beim Öffnen noch nicht angemeldet ist, landet nach der Anmeldung (auch über einen Anmeldeanbieter) wieder auf der Annahme-Seite. Die E-Mail nennt weder deinen Namen noch den Namen des Tenants — die eingeladene Person sieht erst nach der Anmeldung, worum es geht.

!!! note "Wenn die E-Mail nicht rausgeht"
    Nach dem Absenden sagt dir die Seite, ob die E-Mail verschickt wurde. Ist auf der Installation kein E-Mail-Versand eingerichtet oder schlägt er fehl, ist die Einladung trotzdem angelegt: Die Seite zeigt dir dann den Einladungslink mit einer Schaltfläche zum Kopieren — gib ihn selbst weiter, zum Beispiel per Messenger. Annehmen kann ihn auch dann nur, wer sich mit der eingeladenen Adresse anmeldet. Welche Installation E-Mails verschickt, legt dein Betreiber fest (`EMAIL_ADAPTER`). <!-- Issue #2162, REQ-024 AK-06 -->

!!! warning "Die Einladung gilt nur für die eingeladene Adresse"
    Eine E-Mail-Einladung kann nur das Konto annehmen, dessen E-Mail-Adresse die eingeladene ist **und** die bestätigt wurde. Wer den Link weiterleitet, verleiht damit niemandem die Mitgliedschaft: ein anderes Konto — oder dasselbe Konto mit noch unbestätigter Adresse — bekommt `403`, die Einladung bleibt offen und nichts wird angelegt. Bestätige die Adresse deines Kontos zuerst, wenn du eingeladen wirst, und melde dich mit dem Konto an, das diese Adresse trägt. Ein **Einladungslink** (Methode 2) ist dagegen zum Teilen gedacht und bleibt für jedes angemeldete Konto gültig. <!-- Issue #2115, REQ-024 AK-61 -->

### Methode 2: Einladungslink

1. Navigiere zu **Einstellungen** > **Mitglieder** > **Einladungslink generieren**
2. Stelle optional ein:
    - Maximale Anzahl Nutzungen (z.B. 20)
    - Ablaufdatum (z.B. in 30 Tagen)
    - Rolle, die neue Mitglieder erhalten
3. Kopiere den Link und teile ihn (WhatsApp, Aushang, E-Mail-Verteiler)

!!! tip "Ideal für große Gruppen"
    Der Einladungslink ist besonders praktisch für Gemeinschaftsgärten: Hänge ihn am Gartentor aus oder verschicke ihn im Vereins-Newsletter. Jeder mit dem Link kann beitreten, bis das Limit erreicht ist.

### Methode 3: OIDC (OpenID Connect) Auto-Join

Für Vereine und Organisationen mit eigenem Identity Provider (Keycloak, etc.) kann die OIDC-Integration so konfiguriert werden, dass neue Nutzer automatisch dem Tenant beitreten. Dies richtet der Plattform-Administrator ein.

---

## Rollen und Berechtigungen

Jedes Mitglied hat pro Tenant genau eine Rolle: **Leitung**, **Gärtner** oder **Beobachter**. Die Rolle bestimmt, was es an den Gartendaten tun darf. Unabhängig davon kann ein Mitglied Zusatzberechtigungen halten: **Verwaltung** (Mitglieder, Einladungen, Einstellungen) und **Technik** (Home Assistant, Sensoren, Import). Eine Rolle „Admin“ gibt es im Tenant nicht mehr.

### Rollenvergleich

| Aufgabe | Leitung | Gärtner | Beobachter |
|---------|:-------:|:--------:|:----------:|
| Alles lesen | Ja | Ja | Ja |
| Pflanzen anlegen/bearbeiten | Ja | Ja | Nein |
| Standorte anlegen/bearbeiten | Ja | Ja | Nein |
| Aufgaben erstellen | Ja | Ja | Nein |
| Ernten dokumentieren | Ja | Ja | Nein |
| Daten löschen | Ja | Nein | Nein |
| Wetterquellen eines Standorts auswählen | Ja | Nein | Nein |

| Aufgabe | Wer darf das? |
|---------|---------------|
| Mitglieder einladen | Zusatzberechtigung **Verwaltung**, unabhängig von der Rolle |
| Rollen ändern | Zusatzberechtigung **Verwaltung**, unabhängig von der Rolle |
| Tenant-Einstellungen ändern | Zusatzberechtigung **Verwaltung**, unabhängig von der Rolle |

Die vollständige Rechteübersicht — inklusive Plattform-Rollen, Dienstkonten und der Frage, wer welche Daten zu sehen bekommt — steht unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md).

!!! note "Geplante Gemeinschaftsfunktionen fehlen in dieser Tabelle"
    Pinnwand, Gießrotation und gemeinsame Einkaufsliste sind noch nicht implementiert (siehe [Gemeinschaftsfunktionen](#gemeinschaftsfunktionen) unten) und tauchen deshalb hier nicht als Berechtigung auf.

### Rollen ändern

1. Navigiere zu **Einstellungen** > **Mitglieder**
2. Klicke beim gewünschten Mitglied auf das Bearbeitungs-Symbol
3. Wähle die neue Rolle
4. Bestätige mit **deinem eigenen** Zugang — die Änderung gilt sofort

!!! note "Rollenwechsel und Entfernen verlangen deine eigene Bestätigung"
    Wer die Rolle eines Mitglieds ändert oder ein Mitglied entfernt, gibt dazu **sein eigenes** aktuelles Passwort ein — ohne lokales Passwort meldet er sich stattdessen frisch bei seinem Anmeldeanbieter an, oder lässt sich, nur bei einer Anmeldung ausschließlich über GitHub oder Apple, einen Code per E-Mail schicken. Grund: Die Rolle bestimmt, was jemand im Mandanten ändern und löschen darf, und das Entfernen sperrt die Person aus — auch die letzte Leitung. Eine Rolle, die du unverändert erneut sendest, braucht keine Bestätigung. Das Löschen einer Parzellen-Zuordnung braucht sie nicht: Es sperrt niemanden aus dem Mandanten aus.

!!! warning "Du kannst deine eigene Rolle nicht erhöhen"
    Auch mit Verwaltung erhöhst du die Rolle deiner **eigenen** Mitgliedschaft nicht — das Herabstufen bleibt möglich. Im technischen Mandanten `platform` ist die Rolle Leitung die Plattform-Rolle; sie vergibt dort, per Rollenwechsel wie per Einladung, nur, wer sie selbst hat. Das wird auch beim Annehmen geprüft: Eine Leitungs-Einladung in `platform`, deren Absender dort inzwischen keine Leitung mehr ist, lässt sich nicht annehmen. In jedem anderen Mandanten darf die Verwaltung weiterhin eine Leitung ernennen. <!-- Issue #2078, #2180, REQ-024 AK-58 -->

---

## Parzellen zuordnen

Ein Garten ist eine gemeinsame Arbeitsmenge: Alle Gärtner pflegen alle Pflanzen und Aufgaben. Eine Parzellen-Zuordnung hält deshalb fest, **wer sich kümmert** — sie sperrt niemanden aus.

- **Zugeordnete Parzellen**: Das Mitglied findet „seine" Parzelle schneller wieder; bearbeiten dürfen sie alle Gärtner.
- **Gemeinschaftsflächen** wie Kompost oder Gewächshaus brauchen gar keine Zuordnung.
- **Beobachter** lesen alles und ändern nichts — unabhängig von Zuordnungen.

Der praktische Vorteil: Fällt jemand kurzfristig aus, springt ein anderes Mitglied ein, ohne dass jemand mit der Zusatzberechtigung Verwaltung erst etwas umstellen muss.

!!! tip "Etwas wirklich privat halten"
    Trennung verläuft immer an der Gartengrenze, nie innerhalb eines Gartens. Was nur dich etwas angeht, gehört in deinen persönlichen Garten — oder in einen weiteren Garten, den du jederzeit anlegen kannst.

!!! note "Teilweise verfügbar: Parzellen-Zuordnung"
    Zuordnungen lassen sich bislang nur über die Programmierschnittstelle anlegen — eine Bedienoberfläche dafür gibt es noch nicht. Einzelheiten unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md#standort-zuweisungen-innerhalb-eines-gemeinschaftsgartens). <!-- REQ-049 §3.5 -->

---

## Gemeinschaftsfunktionen

!!! warning "Noch nicht implementiert"
    Pinnwand, Gießrotation und gemeinsame Einkaufsliste sind für Gemeinschaftsgärten geplant, aber aktuell weder im Backend noch in der Oberfläche vorhanden. Die folgenden Abschnitte beschreiben den vorgesehenen Funktionsumfang.

### Pinnwand

Die Pinnwand wird ein gemeinsamer Nachrichtenbereich für alle Tenant-Mitglieder sein: Mitglieder werden Beiträge veröffentlichen können, die Leitung wird Beiträge anpinnen und löschen können.

!!! example "Typische Pinnwand-Posts (Konzept)"
    - "Schneckenalarm! Bitte Bierfallen aufstellen."
    - "Samstag 10 Uhr: Gemeinsames Kompost-Umsetzen."
    - "Zu viele Zucchini — wer will welche?"

### Gießrotation

Für die Verteilung von Gießpflichten unter Mitgliedern ist eine Rotationsfunktion geplant: Ein Intervall (z. B. wöchentlich) und die beteiligten Mitglieder werden hinterlegbar sein, und das System wird das jeweils zuständige Mitglied erinnern. Mitglieder sollen Dienste untereinander tauschen können, ohne die Leitung einzubeziehen.

### Gemeinsame Einkaufsliste

Eine gemeinsame Einkaufsliste ist geplant: Alle Gärtner sollen Einträge hinzufügen und abhaken können, die Leitung soll Listen archivieren können.

---

## Tenant-Einstellungen

Mit der Zusatzberechtigung **Verwaltung** erreichst du alle Einstellungen unter **Einstellungen** (Zahnrad-Icon).

### Wichtige Einstellungen

| Einstellung | Beschreibung |
|-------------|-------------|
| **Name & Slug** | Anzeigename und URL-Kurzname |
| **Stammdaten-Zuweisung** | Welche globalen Pflanzenarten sind sichtbar |
| **Einladungseinstellungen** | Standard-Rolle für neue Mitglieder |
| **OIDC-Konfiguration** | Auto-Join über externen Identity Provider |

!!! warning "Slug ändern bricht URLs"
    Wenn du den Slug änderst, ändern sich alle URLs innerhalb des Tenants. Lesezeichen und geteilte Links werden ungültig. Ändere den Slug nur, wenn nötig.

---

## Tenant verlassen

Du kannst einen Tenant verlassen, solange du nicht das einzige Mitglied mit der Zusatzberechtigung **Verwaltung** bist:

1. Navigiere zu **Einstellungen** > **Mitgliedschaft** > **Tenant verlassen**
2. Bestätigen

!!! note "Aufgaben und Erinnerungen"
    Verlässt du einen Tenant — oder entfernt dich jemand mit der Zusatzberechtigung Verwaltung —, bist du dort bei keiner Aufgabe mehr zugewiesen: Die Aufgaben bleiben im Tenant, aber ohne Zuständigen. Die täglichen Pflege-Erinnerungen und die Tageszusammenfassung gehen nur noch an aktive Mitglieder; eine Zusammenfassung enthält immer nur die Aufgaben **eines** Tenants (hast du mehrere, bekommst du je Tenant eine). <!-- Issue #2114, REQ-024 AK-62 -->

!!! warning "Als einziges Mitglied mit Verwaltung"
    Bist du das einzige Mitglied mit der Zusatzberechtigung Verwaltung, musst du sie vorher entweder an ein anderes Mitglied weitergeben oder den Tenant löschen — Letzteres setzt zusätzlich voraus, dass du dort sowohl die Rolle Leitung als auch die Zusatzberechtigung Verwaltung hast. Details dazu unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md). <!-- Issue #1791 -->

---

## Häufige Fragen

??? question "Kann ich Daten zwischen Tenants teilen?"
    Nein — Ressourcen gehören immer zu genau einem Tenant. Cross-Tenant-Sharing ist bewusst nicht möglich, um Datenisolation zu gewährleisten. Globale Stammdaten (Pflanzenarten, Schädlinge) sind hingegen für alle Tenants sichtbar.

??? question "Wie viele Tenants kann ich erstellen?"
    Es gibt keine technische Begrenzung. Du kannst beliebig viele Tenants erstellen und beitreten.

??? question "Was passiert mit meinen Daten, wenn ich einen Tenant lösche?"
    Löschen darf nur ein Mitglied, das im betroffenen Tenant sowohl die Rolle Leitung als auch die Zusatzberechtigung Verwaltung hat — nicht bereits die Verwaltung allein (Details unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md)) —, und zwar nur aus einer angemeldeten Sitzung heraus; ein persönlicher API-Schlüssel genügt dafür nicht. Zur Sicherheit fragt das System dabei zusätzlich den Kurznamen (Slug) des Tenants sowie, sofern das Konto ein lokales Passwort hat, dieses Passwort erneut ab (zusätzlich zum Kurznamen); ein Konto ohne lokales Passwort, das sich über Google oder einen generischen OIDC-Anbieter anmeldet, bestätigt stattdessen mit einer frischen Anmeldung bei diesem Anbieter, ein Konto ausschließlich über GitHub und/oder Apple mit einem per E-Mail zugeschickten Bestätigungscode. Nach fünf falschen Bestätigungen sperrt das System die Bestätigung für 15 Minuten — bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis zu 4 Stunden, die Fehlermeldung nennt die verbleibende Zeit; die Anmeldung selbst bleibt davon unberührt. <!-- Issue #1791, #1813, #1814, #1816, #1815 -->

    Die Löschung wird zuerst nur **geplant**: Der Tenant ist ab sofort für alle Mitglieder gesperrt, und alle Mitglieder erhalten eine E-Mail mit dem Löschdatum — bis dahin können sie ihre eigenen Daten über den Datenexport sichern. Bis zu diesem Datum (standardmäßig 90 Tage) kann ein Mitglied mit Leitung und Verwaltung die Löschung mit seinem Passwort abbrechen (`POST /api/v1/tenants/{slug}/erasure/cancel`), ebenso ein Platform-Admin im Admin-Bereich; danach ist der Tenant wieder aktiv, alle Mitgliedschaften sind unverändert. <!-- Issue #2123 --> Erst nach Ablauf der Frist werden alle Mitgliedschaften deaktiviert. Anschließend werden die dazu beigetragenen Erkennungsvektoren, der Dateispeicher (Fotos, Anhänge) und sämtliche fachlichen Daten des Tenants gelöscht: Standorte, Pflanzen, Pflanzdurchläufe, Tagebucheinträge, Aufgaben, Tanks, Sensoren, Dünge- und Gießprotokolle und alle weiteren Standort-gebundenen Daten, danach der Tenant-Datensatz selbst. <!-- Issue #1769 -->

    Eine Ausnahme gilt für Ernte- und Behandlungsdokumentation (Erntechargen, Qualitätsbewertungen, Behandlungen, Inspektionen): Diese muss aus gesetzlichen Gründen (CanG, Pflanzenschutzgesetz) einige Jahre aufbewahrt werden. Diese Datensätze bleiben deshalb erhalten, werden aber pseudonymisiert — Namensangaben von Mitgliedern werden entfernt und ihre Kontenreferenzen durch ein Pseudonym ersetzt.

    Konnte beim Löschen nicht sofort alles vollständig entfernt werden, bleibt der Vorgang vorgemerkt und wird automatisch täglich wiederholt, bis er abgeschlossen ist. Dein persönlicher Tenant und deine Mitgliedschaften in anderen Tenants sind von einer solchen Löschung nicht betroffen.

??? question "Sieht die Leitung eines Gemeinschaftsgartens meine persönlichen Zimmerpflanzen?"
    Nein. Dein persönlicher Tenant ist vollständig von allen anderen Tenants isoliert. Selbst wenn jemand im Gemeinschaftsgarten Leitung ist oder Zusatzberechtigungen hat, kann er niemals Daten in deinem persönlichen Tenant sehen.

---

## Siehe auch

- [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md)
- [Erste Schritte — Onboarding](onboarding.md)
- [Konto & Anmeldung](account.md)
- [Standorte & Substrate](locations-substrates.md)
