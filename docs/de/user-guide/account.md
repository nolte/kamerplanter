<!-- REQ-023 — Quelle: src/frontend/src/pages/auth/{LoginPage,RegisterPage,EmailVerificationPage,PasswordResetRequestPage,PasswordResetConfirmPage,OAuthCallbackPage,AccountSettingsPage,EmailChangeCard,EmailChangeConfirmPage,EmailChangeRevertPage}.tsx, src/backend/app/domain/services/auth_service.py, src/backend/app/domain/engines/login_throttle_engine.py, src/backend/app/config/settings.py — REQ-025 (Art. 16) für die E-Mail-Änderung selbst, siehe privacy.md -->

# Konto & Anmeldung

Hier erfährst du, wie du ein Kamerplanter-Konto anlegst, dich anmeldest und deine persönlichen Einstellungen wie Profil, Sprache und aktive Sitzungen verwaltest.

!!! info "Gilt für den Full-Modus"
    Diese Seite beschreibt den Mehrbenutzerbetrieb (Full-Modus) mit Registrierung und Login. Läuft deine Instanz im **Light-Modus**, gibt es keine Anmeldung — siehe [Light-Modus](light-mode.md).

---

## Voraussetzungen

- Deine Kamerplanter-Instanz läuft im Full-Modus
- Eine gültige E-Mail-Adresse, auf die du Zugriff hast

## Konto erstellen (Registrierung)

1. Öffne die Anmeldeseite und klicke auf **Noch kein Konto? Registrieren**
2. Fülle das Formular aus:

    | Feld | Beschreibung |
    |------|-------------|
    | **Anzeigename** | Dein Name, wie er in der App angezeigt wird |
    | **E-Mail** | Deine Anmelde-E-Mail-Adresse |
    | **Passwort** | Mindestens 10 Zeichen |
    | **Passwort bestätigen** | Muss mit dem Passwort übereinstimmen |

3. Klicke auf **Registrieren**

Bei der Registrierung legt das System automatisch deinen **persönlichen Tenant** an (siehe [Mandanten & Gärten](tenants.md)) — dein privater Bereich für Pflanzen, Standorte und Aufgaben.

### E-Mail-Adresse bestätigen

Nach der Registrierung erhältst du eine E-Mail mit einem Bestätigungslink.

1. Öffne die E-Mail und klicke auf den Bestätigungslink
2. Die Seite zeigt **E-Mail erfolgreich verifiziert** — du kannst dich jetzt anmelden
3. Klicke auf **Anmelden**, um direkt zur Anmeldeseite zu gelangen

!!! warning "Anmeldung erst nach Bestätigung möglich"
    Solange deine E-Mail-Adresse nicht bestätigt ist, lehnt das System die Anmeldung ab. Der Bestätigungslink ist **24 Stunden** gültig. Prüfe bei Ausbleiben der E-Mail auch deinen Spam-Ordner.

#### Wenn der Bestätigungslink nicht mehr funktioniert

Ist der Link älter als 24 Stunden oder unvollständig kopiert, zeigt die Seite statt der Erfolgsmeldung einen roten Hinweis — etwa **Ungültiger oder abgelaufener Token**. Darunter findest du ebenfalls den Button **Anmelden**, der dich zurück zur Anmeldeseite bringt. Von dort kannst du dich anmelden (sofern deine Adresse bereits über einen früheren Link bestätigt wurde) oder dir über **Passwort vergessen?** wieder eine E-Mail zusenden lassen.

!!! note "Geändertes Verhalten"
    Bis zu dieser Version war diese Fehlerseite eine Sackgasse: Sie zeigte nur die Fehlermeldung und keinen Weg zurück in die Anwendung — du musstest die Adresse der Anmeldeseite selbst eintippen. <!-- REQ-023 -->

---

## Anmelden

### Mit E-Mail und Passwort

1. Gib deine E-Mail-Adresse und dein Passwort ein
2. Aktiviere optional **Angemeldet bleiben**
3. Klicke auf **Anmelden**

!!! tip "Angemeldet bleiben nur auf privaten Geräten"
    Ohne **Angemeldet bleiben** läuft deine Sitzung nach 24 Stunden ab. Mit aktivierter Option bleibt sie bis zu 30 Tage aktiv. Verwende diese Option nur auf Geräten, auf die niemand sonst Zugriff hat.

### Mit Google, GitHub oder einem anderen Anbieter anmelden

Wenn dein Administrator externe Anmeldeanbieter eingerichtet hat, erscheinen unterhalb des Anmeldeformulars zusätzliche Buttons wie **Anmelden mit Google**. Technisch nutzt Kamerplanter dafür **OpenID Connect (OIDC)**, einen offenen Standard, mit dem sich Anbieter wie Google, GitHub oder Apple anbinden lassen.

1. Klicke auf den Button des gewünschten Anbieters
2. Melde dich beim Anbieter an und bestätige den Zugriff
3. Du wirst automatisch zurück zu Kamerplanter geleitet und bist angemeldet

Kamerplanter verknüpft den Anbieter mit einem bestehenden lokalen Konto nur dann, wenn **beide Seiten** die E-Mail-Adresse bestätigt haben: dein lokales Konto und der Anbieter. Schlägt die Anmeldung fehl, landest du mit einer Fehlermeldung zurück auf der Anmeldeseite. Versuche es erneut oder melde dich stattdessen mit E-Mail und Passwort an.

!!! info "Wenn der Anbieter nichts über die Adresse sagt"
    Manche Anbieter geben gar nicht an, ob eine E-Mail-Adresse bestätigt ist. Kamerplanter wertet dieses Schweigen als „nicht bestätigt" und verknüpft nicht automatisch. Melde dich stattdessen mit E-Mail und Passwort an — die Anmeldeseite sagt dir in diesem Fall auch, warum.

!!! note "Alternative Anmeldeoptionen nicht sichtbar?"
    Falls die Liste der externen Anbieter nicht geladen werden kann, zeigt die Anmeldeseite einen Hinweis. Du kannst dich in diesem Fall weiterhin mit E-Mail und Passwort anmelden.

### Konto vorübergehend gesperrt

Nach mehreren fehlgeschlagenen Anmeldeversuchen in Folge sperrt das System dein Konto vorübergehend, um es vor automatisierten Angriffen zu schützen. Die Sperrdauer beginnt bei wenigen Minuten und verlängert sich bei weiteren Fehlversuchen — die Anmeldemaske zeigt dir an, wie lange die Sperre noch andauert. Warte die angezeigte Zeit ab oder setze dein Passwort zurück (siehe unten).

---

## Passwort vergessen und zurücksetzen

1. Klicke auf der Anmeldeseite auf **Passwort vergessen?**
2. Gib deine E-Mail-Adresse ein und klicke auf **Reset-Link senden**
3. Du siehst die Bestätigung **Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link gesendet**

!!! note "Warum die Meldung immer erscheint"
    Diese Meldung wird unabhängig davon angezeigt, ob ein Konto mit der eingegebenen Adresse existiert. Das verhindert, dass Außenstehende über die Reset-Funktion herausfinden können, welche E-Mail-Adressen bei Kamerplanter registriert sind.

4. Öffne den Reset-Link aus der E-Mail (gültig für **1 Stunde**)
5. Vergib ein neues Passwort (mindestens 10 Zeichen) und bestätige es
6. Klicke auf **Passwort speichern** — du wirst zur Anmeldeseite weitergeleitet

---

## Profil, Sprache und Zeitzone verwalten

Öffne deine Kontoeinstellungen über dein Profilbild bzw. deine Initialen oben rechts in der Navigationsleiste.

Im Tab **Profil** kannst du folgende Angaben ändern:

| Einstellung | Beschreibung |
|-------------|-------------|
| **Anzeigename** | Wird in der gesamten App angezeigt |
| **E-Mail** | Nur zur Anzeige an dieser Stelle — deine Anmeldeadresse änderst du im Abschnitt **E-Mail-Adresse ändern** direkt darunter (siehe nächster Abschnitt) |
| **Sprache** | Deutsch oder Englisch — wechselt die Oberflächensprache sofort |
| **Zeitzone** | Wird für alle Datums- und Zeitanzeigen verwendet, z. B. `Europe/Berlin` |

Klicke nach Änderungen auf **Speichern**.

---

## E-Mail-Adresse ändern

Im Tab **Profil** der Kontoeinstellungen findest du unterhalb deiner Profildaten den Abschnitt **E-Mail-Adresse ändern**. Das ist der Berichtigungsweg nach DSGVO Art. 16 — die ausführliche Aufschlüsselung, was dabei mit deinen Daten passiert, findest du unter [E-Mail-Adresse ändern (Art. 16 DSGVO)](privacy.md#e-mail-adresse-andern-art-16-dsgvo).

1. Trage die **neue E-Mail-Adresse** ein und klicke auf **Änderung anfordern**
2. Bestätige dich im aufklappenden Dialog — mit deinem **aktuellen Passwort**, sofern dein Konto eines hat, sonst über **Erneut anmelden** (Google, generischer OIDC-Anbieter) oder, nur bei ausschließlich GitHub/Apple, über **Code per E-Mail senden**
3. Die Oberfläche bestätigt: An die neue Adresse wurde ein Bestätigungslink geschickt; deine **aktuelle** Adresse erhält sofort eine Information über die angestoßene Änderung

Bis zur Bestätigung meldest du dich weiterhin mit deiner bisherigen Adresse an.

!!! tip "Bestätigung über die neue Adresse"
    Öffne die E-Mail an der **neuen** Adresse und klicke auf **Neue Adresse bestätigen**. Erst mit diesem Klick wird die neue Adresse zu deiner Anmeldeadresse — das bloße Öffnen der Mail reicht nicht. Danach werden alle deine Sitzungen abgemeldet; du meldest dich anschließend mit der neuen Adresse erneut an.

!!! warning "Falscher Empfänger? Rückgängig machen"
    Deine **bisherige** Adresse erhält nach der Bestätigung ebenfalls eine Mail — mit einem Link, über den sich die Änderung innerhalb von 7 Tagen einmalig rückgängig machen lässt. Das trennt dabei auch seit der Änderung neu verknüpfte Anmeldeanbieter und widerruft seitdem angelegte API-Schlüssel. Details dazu, was die Wiederherstellung im Einzelnen tut, unter [E-Mail-Adresse ändern (Art. 16 DSGVO)](privacy.md#e-mail-adresse-andern-art-16-dsgvo).

---

## Passwort ändern und Anmeldeanbieter verwalten

Im Tab **Sicherheit** der Kontoeinstellungen verwaltest du, wie du dich anmeldest.

### Passwort ändern oder festlegen

- Hast du bereits ein lokales Passwort, gibst du dein aktuelles Passwort ein und vergibst ein neues
- Hast du dich bisher nur über einen externen Anbieter angemeldet, kannst du hier zusätzlich ein lokales Passwort **festlegen** — statt eines aktuellen Passworts (das noch nicht existiert) klickst du bei Google oder einem generischen OIDC-Anbieter auf **Erneut anmelden** und bestätigst dich frisch beim Anbieter; nur wenn du dich ausschließlich über GitHub oder Apple anmeldest, klickst du stattdessen auf **Code per E-Mail senden** und gibst den Code aus der Mail ein. Danach kannst du dich wahlweise mit E-Mail/Passwort oder über den Anbieter anmelden.

!!! warning "Passwortänderung beendet alle Sitzungen"
    Sobald du dein Passwort änderst, werden alle aktiven Sitzungen beendet — auch auf anderen Geräten. Du musst dich dort erneut anmelden.

!!! note "Nach zu vielen Fehlversuchen gesperrt"
    Dein aktuelles Passwort korrekt einzugeben ist bei einer Passwortänderung eine erneute Bestätigung (genau wie bei der Konto- oder Mandantenlöschung, siehe unten). Tippst du es mehrfach falsch ein, sperrt das System die Bestätigung für 15 Minuten — bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis zu 4 Stunden; die Fehlermeldung zeigt die verbleibende Zeit. Diese Sperre betrifft nur die Bestätigung, nicht die Anmeldung selbst.

### Verknüpfte Anmeldeanbieter

Die Liste zeigt alle mit deinem Konto verknüpften Anmeldewege (lokales Passwort, Google, GitHub, …). Du kannst einen Anbieter trennen, solange danach mindestens ein weiterer Anmeldeweg bestehen bleibt. Dein letzter Anmeldeweg lässt sich nicht entfernen, damit du nicht aus deinem Konto ausgesperrt wirst.

!!! note "Liste konnte nicht geladen werden?"
    Lässt sich die Liste nicht laden, zeigt die Karte einen Warnhinweis. Solange unklar ist, ob dein Konto ein lokales Passwort hat, zeigt dir das Passwort-Formular oben sicherheitshalber weiterhin das Feld für das aktuelle Passwort an — lade die Seite neu, um es erneut zu versuchen.

---

## Aktive Sitzungen einsehen und beenden

Im Tab **Sitzungen** siehst du alle Geräte und Browser, auf denen du aktuell angemeldet bist:

| Spalte | Bedeutung |
|--------|-----------|
| **Gerät** | Browser-/Geräteinformation; deine aktuelle Sitzung ist markiert |
| **Sitzungstyp** | **Persistent** (mit „Angemeldet bleiben" erzeugt, bis zu 30 Tage) oder **Sitzung** (ohne, bis zu 24 Stunden) |
| **IP** | IP-Adresse, von der aus die Sitzung erstellt wurde |
| **Läuft ab** | Ablaufdatum der Sitzung |

Um eine fremde oder nicht mehr benötigte Sitzung zu beenden, klicke auf das Papierkorb-Symbol in der jeweiligen Zeile. Deine aktuelle Sitzung kannst du hier nicht beenden — dafür meldest du dich über **Abmelden** im Konto-Menü ab.

!!! tip "Verdächtige Sitzung entdeckt?"
    Beende die Sitzung sofort und ändere anschließend dein Passwort — das beendet automatisch alle verbleibenden Sitzungen (siehe oben).

---

## Erfahrungsstufe und weitere Einstellungen

Im Tab **Erfahrungsstufe** der Kontoeinstellungen kannst du außerdem:

- deine Erfahrungsstufe (Einsteiger, Mittelstufe, Experte) anpassen — siehe [Erste Schritte — Onboarding](onboarding.md) für die Details zu den drei Stufen
- deine **Gießkannengröße** hinterlegen, die als Vorbelegung in Dosierungsrechnern verwendet wird
- den **Einrichtungsassistenten** erneut starten, etwa um ein weiteres Szenario einzurichten

Welche Funktionsbereiche du unabhängig von deiner Erfahrungsstufe ein- oder ausblendest, regelst du im Tab **Module & Funktionen** — siehe [Module & Funktionen](module-visibility.md).

Im Tab **API-Schlüssel** (Zugangsschlüssel für automatisierte Zugriffe, z. B. eigene Skripte) erstellst und widerrufst du persönliche API-Schlüssel. Details dazu findest du in der [API-Dokumentation](../api/authentication.md).

---

## Konto löschen

Im Tab **Konto** der Kontoeinstellungen findest du im rot markierten Bereich die Schaltfläche **Konto löschen**. Das ist derselbe Löschweg wie im Datenschutz-Bereich (siehe [Konto löschen (Art. 17 DSGVO)](privacy.md#account-loschen-art-17-dsgvo)): Dein Konto wird sofort geschlossen — du kannst dich danach nicht mehr anmelden —, und deine personenbezogenen Daten werden nach Ablauf der Karenzzeit (standardmäßig 90 Tage) endgültig gelöscht. Gesetzlich geschützte Daten (Ernte- und Behandlungsdokumentation) werden stattdessen anonymisiert, nicht gelöscht.

Der Bestätigungsdialog verlangt, dass du deine **eigene E-Mail-Adresse** erneut eintippst. Hat dein Konto ein lokales Passwort, gibst du zusätzlich dein **aktuelles Passwort** ein. Meldest du dich stattdessen über Google oder einen generischen OIDC-Anbieter an, klickst du im Dialog auf **Erneut anmelden** und bestätigst dich frisch beim Anbieter; nur wenn du dich ausschließlich über GitHub oder Apple anmeldest — die das nicht unterstützen —, klickst du auf **Code per E-Mail senden** und gibst den zugeschickten Bestätigungscode ein.

!!! danger "Konto-Löschung ist endgültig"
    Sobald du bestätigst, ist die Löschung nicht mehr rückgängig zu machen. Lade vorher deinen Datenexport herunter, wenn du deine Daten sichern möchtest (siehe [Datenschutz & DSGVO](privacy.md)). Die vollständige Aufschlüsselung, welche Daten sofort bzw. nach 90 Tagen gelöscht und welche nur anonymisiert werden, findest du unter [Konto löschen (Art. 17 DSGVO)](privacy.md#account-loschen-art-17-dsgvo).

!!! note "Nach zu vielen Fehlversuchen gesperrt"
    Tippst du das Passwort mehrfach falsch ein, sperrt das System die Bestätigung für 15 Minuten — bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis zu 4 Stunden; der Dialog zeigt dir die verbleibende Wartezeit an. Diese Sperre betrifft nur die Bestätigung der Löschung, nicht die Anmeldung: Du kannst dich weiterhin normal anmelden, im Tab **Sitzungen** einzelne Sitzungen beenden oder dein Passwort über **Passwort vergessen?** zurücksetzen.

---

## Häufige Fragen

??? question "Ich habe keine Bestätigungs-E-Mail erhalten. Was kann ich tun?"
    Prüfe zuerst deinen Spam-Ordner. Der Bestätigungslink ist 24 Stunden gültig; danach musst du dich erneut registrieren, um eine neue E-Mail zu erhalten.

??? question "Kann ich meine E-Mail-Adresse ändern?"
    Ja, im Tab **Profil** der Kontoeinstellungen im Abschnitt **E-Mail-Adresse ändern** (siehe oben). Die neue Adresse muss über einen Bestätigungslink freigeschaltet werden; deine bisherige Adresse kann die Änderung anschließend 7 Tage lang rückgängig machen. Details: [E-Mail-Adresse ändern (Art. 16 DSGVO)](privacy.md#e-mail-adresse-andern-art-16-dsgvo).

??? question "Was passiert, wenn ich einen Anmeldeanbieter wie Google trenne?"
    Du kannst dich danach nicht mehr über diesen Anbieter anmelden. Solange mindestens ein weiterer Anmeldeweg (Passwort oder anderer Anbieter) übrig bleibt, funktioniert die Anmeldung über diesen Weg weiter.

??? question "Warum wurden alle meine Sitzungen beendet, obwohl ich nur mein Passwort geändert habe?"
    Das ist ein Sicherheitsmechanismus: Nach einer Passwortänderung werden vorsorglich alle Sitzungen beendet, damit ein möglicherweise kompromittiertes Gerät keinen Zugriff mehr hat. Du meldest dich danach überall neu an.

---

## Siehe auch

- [Erste Schritte — Onboarding](onboarding.md)
- [Mandanten & Gärten](tenants.md)
- [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md)
- [Module & Funktionen](module-visibility.md)
- [Datenschutz & DSGVO](privacy.md)
- [API-Dokumentation: Authentifizierung](../api/authentication.md)
