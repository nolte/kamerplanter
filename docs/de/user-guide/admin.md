# Plattform-Admin-Bereich

Der Plattform-Admin-Bereich ist ausschließlich für Nutzer mit der Plattform-Rolle **admin** zugänglich. Er ermöglicht die plattformweite Verwaltung aller Mandanten und Nutzer — unabhängig von der mandantengebundenen Tenant-Admin-Rolle.

---

## Voraussetzungen

- Plattform-Rolle **admin** (unterscheidet sich von der Tenant-Admin-Rolle)
- Zugang über `/admin/platform` (im Full-Modus)

!!! warning "Nicht mit Tenant-Admin verwechseln"
    Die Plattform-Admin-Rolle ist eine **plattformweite** Sonderrolle, die zum Zugriff auf Daten aller Mandanten berechtigt. Die Tenant-Admin-Rolle dagegen ist auf einen einzelnen Mandanten beschränkt und wird über **Einstellungen > Mandanten > Mitglieder** vergeben.

---

## Abgrenzung: Plattform-Admin vs. Tenant-Admin

| Funktion | Plattform-Admin | Tenant-Admin |
|---------|----------------|-------------|
| Alle Mandanten verwalten | Ja | Nein |
| Nutzerverwaltung plattformweit | Ja | Nein |
| Mandantenstatistiken einsehen | Ja | Nein |
| OIDC-Provider konfigurieren | Ja | Nein |
| Mitglieder des eigenen Mandanten verwalten | Ja | Ja |
| Standorte und Pflanzdaten des Mandanten | Ja | Ja |

---

## Mandantenverwaltung

Im Bereich **Admin > Mandanten** kannst du:

- Alle Mandanten der Plattform einsehen (Name, Slug, Mitgliederzahl, Erstellungsdatum)
- Einzelne Mandanten deaktivieren oder löschen
- Mandanten-Kontingente und Limits einsehen
- Mitglieder eines Mandanten stellvertretend verwalten

!!! info "Ein deaktivierter Mandant sperrt alle Mitglieder aus"
    Deaktivierst du einen Mandanten, erreicht ihn kein Mitglied mehr — weder in der App noch über einen API-Schlüssel oder einen MCP-Client. Für die Mitglieder sieht er dann aus wie ein Mandant, den es nicht gibt. War es ihr persönlicher Garten, sehen sie nur noch den gemeinsamen Pflanzenkatalog. Die Mitgliedschaften und alle Daten bleiben erhalten: Reaktivierst du den Mandanten, haben alle Mitglieder sofort wieder ihren bisherigen Zugriff mit derselben Rolle. Du selbst verwaltest einen deaktivierten Mandanten weiterhin hier im Admin-Bereich. <!-- Issue #2105 -->

!!! warning "Mandanten löschen: erst nach einer Frist, bis dahin abbrechbar"
    Löschst du einen Mandanten, wird die Löschung zunächst nur **geplant**: Der Mandant zeigt den Zustand **Löschung geplant** mit dem Löschdatum, ist ab sofort für alle Mitglieder gesperrt, und alle Mitglieder bekommen eine E-Mail mit dem Datum — bis dahin können sie ihre eigenen Daten über den Datenexport sichern. Die Frist beträgt `RETENTION_TENANT_ERASURE_GRACE_DAYS` Tage (Standard 90). Bis zum Löschdatum kannst du hier mit **Löschung abbrechen** und deinem Passwort alles rückgängig machen: Der Mandant ist danach wieder aktiv, alle Mitgliedschaften sind unverändert. Der Aktiv-Schalter und das erneute Löschen sind währenddessen gesperrt. Erst nach Ablauf der Frist wechselt der Zustand auf **Wird gelöscht**, und die eigentliche Löschung beginnt — ab dann ist nichts mehr rückgängig zu machen. Mit `RETENTION_TENANT_ERASURE_GRACE_DAYS=0` löscht die Instanz wie früher sofort. <!-- Issue #2123 -->

    Eine Organisation im Zustand **Verwaist** hat nach einer Kontolöschung niemanden mehr, der sie verwalten kann (die letzte Person mit Verwaltungsrecht hat ihr Konto gelöscht und es gab keine Leitung, die übernehmen konnte). Sie läuft in dieselbe Frist und wird danach gelöscht; abbrechen lässt sich das nicht. Du wirst per E-Mail informiert, wenn eine Organisation verwaist. <!-- Issue #2134 -->

!!! danger "Nach Ablauf der Frist ist die Löschung irreversibel"
    Nach Ablauf der Frist deaktiviert die Löschung zuerst alle Mitgliedschaften und entfernt dann die dazu beigetragenen Erkennungsvektoren, den Dateispeicher (Fotos, Anhänge) und sämtliche fachlichen Daten des Mandanten — Standorte, Pflanzen, Pflanzdurchläufe, Tagebucheinträge, Aufgaben, Tanks, Sensoren und alle weiteren Standort-gebundenen Daten — sowie zuletzt den Mandanten-Datensatz selbst. Ausgenommen ist Ernte- und Behandlungsdokumentation, die aus gesetzlichen Gründen (CanG, Pflanzenschutzgesetz) einige Jahre aufbewahrt werden muss: Diese Datensätze bleiben erhalten, werden aber pseudonymisiert. Diese Aktion kann nicht rückgängig gemacht werden. Einen Export des ganzen Mandanten gibt es nicht; jedes Mitglied sichert seine eigenen Daten über den persönlichen Datenexport. <!-- Issue #1769, #2123 -->

    Ein Bestätigungsdialog verlangt zusätzlich eine erneute Bestätigung, bevor die Löschung ausgeführt wird: Trage den Kurznamen (Slug) des Mandanten ein und, sofern dein Konto ein lokales Passwort hat, dein aktuelles Passwort — hast du keines und meldest dich über Google oder einen generischen OIDC-Anbieter an, klickst du stattdessen auf **Erneut anmelden**; nur bei ausschließlich GitHub/Apple klickst du auf **Code per E-Mail senden** und gibst den zugeschickten Bestätigungscode ein. Stimmt der eingegebene Kurzname nicht, meldet die Aktion `422`; fehlt das Passwort, die erneute Anmeldung oder der Code oder ist er falsch, meldet sie `401` — in allen Fällen bleibt der Mandant unverändert. Ein Dienstkonto kann diese Aktion nicht ausführen, ebenso wenig eine Anmeldung mit einem persönlichen API-Schlüssel statt einer angemeldeten Sitzung. Nach fünf falschen Bestätigungen sperrt das System die Bestätigung für 15 Minuten — bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis zu 4 Stunden (`429`, Meldung nennt die Wartezeit); dasselbe Budget gilt kontoweit auch für die Bestätigung einer Konto-Löschung, einer E-Mail-Änderung und einer Passwortänderung. <!-- Issue #1791, #1813, #1814, #1816, #1815, #1841 -->

    Die Aktion antwortet mit `202 Accepted` (zuvor `200` bzw. `204`): Sie nimmt die Löschung nur an und legt den Löschungs-Datensatz an; die Oberfläche meldet „Löschung geplant für den …“. Nach Ablauf der Frist deaktiviert der tägliche Lauf alle Mitgliedschaften — die eigentliche Löschung läuft danach im Hintergrund in einem Worker, in kleinen Stapeln mit fortlaufendem Lebenszeichen. Beim Antworten ist also noch nichts gelöscht; die Oberfläche meldet „Löschung angenommen“. Scheitert ein Schritt oder bleibt etwas übrig, siehst du das nicht mehr als Fehler (`500`/`502`) an der Aktion: Der Löschvorgang bleibt vorgemerkt, der tägliche Wiederholungs-Lauf setzt ihn automatisch fort, und nach dem dritten erfolglosen Versuch löst das System einen Betreiber-Alarm aus (Log-Ereignis `tenant_erasure.escalated`). Läuft für den Mandanten bereits eine Löschung, meldet ein zweiter Versuch einen Konflikt (`409`). <!-- Issue #1792 --> Ist die Instanz für Mandanten-Löschungen nicht korrekt konfiguriert, meldet sie das mit `503` — in diesem Fall wurde noch nichts geändert.

---

## Home-Assistant-Entitäten freigeben {#home-assistant-entitaeten-freigeben}

Kamerplanter ist mit genau **einer** Home-Assistant-Instanz verbunden — deiner, mit deinem Token — und nutzt sie für alle Mandanten. Damit ein Mandant nicht auf Türkontakte, Anwesenheitssensoren oder Schalter deines Haushalts zugreifen kann, gibst du jedem Mandanten nur die Entitäten frei, die er nutzen soll: als Sensor, Aktor, Wetterquelle oder Benachrichtigungsziel. <!-- Issue #2112 -->

1. Öffne **Admin > Mandanten** und wähle den Mandanten.
2. Im Abschnitt **Home-Assistant-Entitäten** siehst du alle Entitäten deiner Instanz mit ihrem Freigabestand. Über die Suche und den Schalter **Nur freigegebene** grenzt du die Liste ein.
3. Mit dem Schalter neben einer Entität gibst du sie frei oder ziehst die Freigabe zurück.
4. Benachrichtigungsdienste (zum Beispiel `notify.mobile_app_handy`) stehen nicht in der Liste. Trag sie unten unter **Entität per ID freigeben** ein.

Was die Freigabe bewirkt:

- Mitglieder sehen in den Auswahllisten nur freigegebene Entitäten — und nur, wenn sie im Mandanten das Recht **Technik** haben.
- Wer eine nicht freigegebene Entität eintragen will, bekommt eine Fehlermeldung; gespeichert wird nichts.
- Ziehst du eine Freigabe zurück, bleiben Sensoren und Aktoren bestehen, Kamerplanter liest und schaltet die Entität für diesen Mandanten aber nicht mehr. Ein Aktor fällt dann auf die manuelle Aufgabe zurück, wie bei einem Home-Assistant-Ausfall.
- Eine Entität, die Home Assistant nicht mehr meldet, bleibt mit dem Hinweis „nicht mehr in Home Assistant" in der Liste, bis du die Freigabe zurückziehst.

!!! info "Bestehende Zuordnungen bleiben nach dem Update gültig"
    Beim Update auf diese Version gibt Kamerplanter jede Entität, die ein Mandant schon nutzt, diesem Mandanten automatisch frei. Diese Freigaben siehst und änderst du hier wie jede andere. Ein Benachrichtigungsziel, das ein Nutzer in seinen Einstellungen eingetragen hat, gilt dabei für alle Mandanten, in denen er Mitglied ist — prüfe diese Freigaben, wenn du mehrere Mandanten betreibst.

!!! warning "Eine Instanz für alle Mandanten"
    Diese Freigaben begrenzen, was ein Mandant nutzen kann. Sie machen aus einer Instanz keine getrennten Instanzen: Ereignisse und Hinweise, die Kamerplanter an Home Assistant schickt, landen weiterhin alle in deiner Instanz. Für einen Betrieb mit fremden Mandanten ist eine eigene Home-Assistant-Verbindung je Mandant nötig; die gibt es noch nicht.

---

## Nutzerverwaltung

Im Bereich **Admin > Nutzer** kannst du:

- Alle Nutzerkonten der Plattform einsehen
- Nutzerkonten sperren oder deaktivieren
- Plattform-Rollen zuweisen (`admin`, `viewer`)
- Passwort-Reset für Nutzer auslösen
- DSGVO-Anfragen (Datenlöschung, Datenauskunft) bearbeiten

!!! note "DSGVO-Anfragen"
    Betroffenenrechte nach Art. 15–21 DSGVO stehen Nutzern über die Self-Service-API unter `/api/v1/privacy/` zur Verfügung. Als Platform-Admin kannst du Anfragen im Admin-Bereich einsehen und bearbeiten. Weitere Informationen: [Datenschutz (DSGVO)](privacy.md).

!!! note "E-Mail bestätigen oder Konto reaktivieren verlangt deine eigene Bestätigung"
    Änderst du im Bearbeitungsdialog eines Nutzers, ob dessen E-Mail-Adresse als bestätigt gilt oder ob das Konto aktiv ist (bestätigen, die Bestätigung zurücknehmen, wieder aktivieren oder deaktivieren), bestätigst du das zusätzlich mit deinem **eigenen** aktuellen Passwort — hast du keines, meldest du dich stattdessen frisch bei deinem Anmeldeanbieter an, oder lässt dir, nur wenn du dich ausschließlich über GitHub oder Apple anmeldest, einen Code per E-Mail schicken. Grund: Eine bestätigte E-Mail-Adresse erlaubt es, Anmeldedienste automatisch mit diesem Konto zu verknüpfen (siehe [Konto & Anmeldung](account.md#mit-google-github-oder-einem-anderen-anbieter-anmelden)) — eine gekaperte Admin-Sitzung könnte sonst ein fremdes Konto unter der Adresse einer anderen Person als verifiziert markieren. Auch die Rücknahme der Bestätigung ist heikel: Ein unbestätigtes Konto räumt der tägliche Aufräumlauf ab, und ein deaktiviertes kann sich nicht anmelden — deshalb sind diese Änderungen ebenfalls Step-up-Handlungen, und ein API-Schlüssel wird abgewiesen (`403`). Ein Konto, dessen Bestätigung ein Administrator zurückgenommen hat, entfernt der Aufräumlauf für unbestätigte Konten **nie**. Umbenennen und das erneute Speichern unveränderter Werte verlangen keine zusätzliche Bestätigung. Nach zu vielen Fehlversuchen gilt dieselbe Sperre wie unten bei der Kontolöschung beschrieben (15 Minuten, verdoppelnd bis 4 Stunden, `429`). <!-- Issue #1857, #1992 -->

!!! note "Mandant deaktivieren, Rolle ändern und Mitglied entfernen verlangen deine eigene Bestätigung"
    Deaktivierst oder reaktivierst du einen Mandanten, änderst du die Rolle eines Mitglieds (auch beim Mandanten-Admin-Bereich eines Nutzers) oder entfernst du ein Mitglied, bestätigst du das mit deinem **eigenen** aktuellen Passwort — hast du keines, meldest du dich stattdessen frisch bei deinem Anmeldeanbieter an, oder lässt dir, nur wenn du dich ausschließlich über GitHub oder Apple anmeldest, einen Code per E-Mail schicken. Grund: Jede dieser Aktionen kann Mitglieder aus einem Mandanten aussperren oder ihnen die Leitung nehmen. Das Umbenennen und ein unverändert erneut gesendeter Wert brauchen keine Bestätigung.

!!! note "Einen Nutzer einem Mandanten hinzufügen verlangt deine eigene Bestätigung"
    Fügst du einen Nutzer einem Mandanten hinzu — in der Mandanten- wie in der Nutzeransicht —, bestätigst du das mit deinem **eigenen** aktuellen Passwort (ohne lokales Passwort: frische Anmeldung bei deinem Anbieter, oder nur bei GitHub/Apple ein Code per E-Mail). Grund: Wer im Mandanten `platform` die Rolle Leitung erhält, ist Plattform-Admin; auch in jedem anderen Mandanten verleiht die Mitgliedschaft Zugriff auf dessen Fachdaten. Dich selbst kannst du dem Mandanten `platform` nicht hinzufügen. Jedes Hinzufügen steht im Sicherheits-Audit (`GET /api/v1/admin/platform/security-audit`; Aufbewahrung zwei Jahre) — dort auch jede Rollen-, Scope- und Entfernen-Änderung. <!-- Issue #2106, #2111 -->

!!! note "Wer sich registrieren darf"
    Ob sich jeder registrieren kann, nur mit Einladung oder niemand, legst du als Betreiber mit `REGISTRATION_MODE` fest (`open` ist der Standard; siehe [Umgebungsvariablen](../reference/environment-variables.md)); `REGISTRATION_ALLOWED_DOMAINS` beschränkt die Registrierung zusätzlich auf bestimmte E-Mail-Domains. Eine offene E-Mail-Einladung für genau die Adresse öffnet die Registrierung bei `invite_only` und trotz Domain-Liste — bei `closed` nicht. Bestehende Konten melden sich in jedem Modus an. <!-- Issue #2132 -->

!!! note "Mitgliederlimit und Plattform-Obergrenze"
    Jeder Mandant hat ein Mitgliederlimit (`max_members`). Es kann höchstens so hoch sein wie die Plattform-Obergrenze `TENANT_MAX_MEMBERS_CEILING` (Standard 50, siehe [Umgebungsvariablen](../reference/environment-variables.md)) — auch für dich als Plattform-Admin. Ist ein Mandant voll, wird das Hinzufügen abgelehnt, bevor du nach deiner Bestätigung gefragt wirst. Senkst du die Obergrenze, behalten Mandanten mit mehr Mitgliedern alle; nur neue Beitritte werden verweigert. Der Plattform-Mandant ist davon nicht ausgenommen. <!-- Issue #2133 -->

!!! warning "Plattform-Leitungen aus ungeprüften Einladungen sichten"
    Bis #2084 prüfte niemand, wer eine Leitungs-Einladung in den Mandanten `platform` ausstellte; bis #2180 prüfte auch die Annahme das nicht. Die Migration `v0089` widerruft nur **offene** Einladungen — wer eine solche Einladung schon **angenommen** hat, ist weiterhin Plattform-Admin. So findest du diese Konten: (1) Rufe `GET /api/v1/admin/platform/security-audit?tenant_key=platform&limit=500` auf (zusätzlich mit dem Schlüssel der Plattform-Zeile, falls sie einen anderen hat) und suche Zeilen mit `action: membership_added`, `via: invitation` und `new_role: lead`; `target_user_key` ist das beigetretene Konto. Das Audit gibt es erst seit #2111 (Migration `v0082`). (2) Für ältere Beitritte lies die angenommenen Einladungen direkt aus der Datenbank: `FOR t IN tenants FILTER t._key == "platform" OR t.is_platform == true FOR i IN invitations FILTER i.tenant_key IN [t._key, "platform"] AND i.role == "lead" AND i.status == "accepted" RETURN DISTINCT {account: i.accepted_by_user_key, issuer: i.invited_by_user_key, accepted_at: i.accepted_at}`. (3) Prüfe für jedes Konto, ob der Aussteller damals selbst Plattform-Leitung war; wenn nicht, stufe die Mitgliedschaft im Admin-Bereich herab oder entferne sie (mit deiner Bestätigung, steht im Audit). Kamerplanter ändert solche Mitgliedschaften nicht automatisch. <!-- Issue #2180 -->

!!! danger "Nutzerkonto löschen ist sofort und vollständig"
    Ein Bestätigungsdialog verlangt vor der Löschung eine erneute Bestätigung: Trage die **E-Mail-Adresse des Zielkontos** ein und gib **dein eigenes** aktuelles Passwort ein, sofern dein Admin-Konto ein lokales Passwort hat — hat es keines und meldest du dich über Google oder einen generischen OIDC-Anbieter an, klickst du stattdessen auf **Erneut anmelden**; nur bei ausschließlich GitHub/Apple klickst du auf **Code per E-Mail senden** und gibst deinen eigenen Bestätigungscode ein; in keinem Fall das Passwort des zu löschenden Kontos. Stimmt die eingegebene E-Mail-Adresse nicht, meldet die Aktion `422`; fehlt dein Passwort, deine erneute Anmeldung oder dein Code oder ist er falsch, meldet sie `401`. Dein eigenes Konto kannst du auf diesem Weg nicht löschen (`403`). Nach fünf falschen Bestätigungen sperrt das System die Bestätigung für 15 Minuten — bei wiederholten Fehlversuchen verdoppelt sich die Wartezeit bis zu 4 Stunden (`429`, Meldung nennt die Wartezeit); dasselbe Budget gilt kontoweit auch für Mandantenlöschung, E-Mail-Änderung und Passwortänderung. <!-- Issue #1813, #1814, #1816, #1815, #1841 -->

    Bestätigst du erfolgreich, antwortet die Aktion mit `202 Accepted` (zuvor `204`): Die Löschung ist angenommen, das Nutzerkonto wird sofort deaktiviert, alle Sitzungen werden beendet, die anderen Mitglieder seiner persönlichen Gärten werden sofort benachrichtigt (ohne Karenzzeit), und die vollständige Konto-Löschung läuft danach im Hintergrund in einem Worker (siehe [Datenaufbewahrung & Anonymisierung](../guides/data-retention.md)). Wenn die Antwort eintrifft, ist noch nichts gelöscht; der Body nennt den Löschantrag (`erasure_key`), dessen Status du über `GET /api/v1/admin/platform/erasures/{erasure_key}` liest (`completed`, sobald alles erledigt ist). <!-- Issue #1949 --> Ein Löschantrag wird dabei als Nachweis gespeichert — genau wie bei einer Löschung, die ein Nutzer selbst über sein Konto anstößt; er hält zusätzlich eine gesalzene Referenz auf dich als bestätigenden Admin, nie deinen Kontoschlüssel im Klartext.

    Konnte die Löschung nicht vollständig abgeschlossen werden — oder ein einzelner externer Dienst nicht erreicht werden —, zeigt der Löschantrag `partially_completed` und wird vom täglichen Wiederholungs-Lauf automatisch fortgesetzt; du musst nichts manuell nachholen (die Aktion antwortet dafür nicht mehr mit `500` oder `502`). Ein zweiter Löschversuch für dasselbe Konto stößt die Fortsetzung des offenen Antrags sofort an, statt auf den nächsten Lauf zu warten, und antwortet wieder mit `202`; solange noch ein Lauf daran arbeitet, antwortet die Aktion mit `409`.

    Läuft für das Konto bereits eine Löschung (z. B. durch den täglichen Aufräumlauf für nie bestätigte Konten), meldet die Aktion einen Konflikt (`409`). Ist die Instanz für Konto-Löschungen nicht korrekt konfiguriert, meldet sie das mit `503` — in diesem Fall wurde noch nichts geändert.

---

## Statistiken

Der Bereich **Admin > Statistiken** bietet eine Übersicht über:

- Anzahl aktiver Mandanten und Nutzer
- Aktive Pflanzdurchläufe plattformweit
- Celery-Task-Queue-Status
- Speicherverbrauch (ArangoDB, TimescaleDB, Redis)

---

## OIDC-Provider

Hier konfigurierst du föderierte Authentifizierungs-Provider (z.B. Google, GitHub, firmeneigene OIDC-Instanzen). Diese Einstellungen gelten plattformweit für alle Mandanten.

Du verwaltest sie auf einer eigenen Seite: Öffne **Einstellungen > Plattform-Modus** und klicke in der Karte „Anmelde-Provider (OIDC)“ auf **OIDC-Provider verwalten** (Adresse `/admin/oidc-providers`). Die Karte erscheint nur für Plattform-Admins. Auf der Seite kannst du:

- jeden Provider mit Typ, Aussteller-URL, Client-ID, Scopes, Status (aktiv oder abgeschaltet) und dem Zeitpunkt des letzten Discovery-Abrufs sehen
- einen Provider **hinzufügen** (**Provider hinzufügen**)
- einen Provider **bearbeiten** (Stift-Symbol)
- einen Provider **testen** (**Testen**): Der Test ruft das Discovery-Dokument ab und meldet vier Befunde — Scopes, Provider-Typ, Signaturschlüssel und Aussteller — je als „In Ordnung“, „Fehlgeschlagen“ oder „Nicht anwendbar“, mit der Begründung des Servers. Der Test braucht keine Bestätigung.
- einen Provider **löschen** (Papierkorb-Symbol)

Ein neuer Provider startet **abgeschaltet**. Er erscheint erst auf der Anmeldeseite, wenn du ihn aktivierst.

!!! warning "Alles, was beeinflusst, wer sich anmelden darf, verlangt deine erneute Bestätigung"
    Ein Provider entscheidet, wem eine Anmeldung zugeordnet wird: Wer einen Provider auf einen eigenen Server umstellen kann, kann sich als jedes Konto anmelden, dessen Adresse dieser Server behauptet. Deshalb verlangen Hinzufügen, Löschen und jede Änderung außer Anzeigename und Icon eine Bestätigung mit deinem eigenen Zugang: dein aktuelles Passwort — oder, ohne lokales Passwort, eine frische Anmeldung bei deinem Provider bzw. den Bestätigungscode, der per E-Mail kommt. Beim Löschen tippst du zusätzlich den Kurznamen des Providers ein. Auch das Ein- **und** Abschalten eines Providers verlangt die Bestätigung: Ein abgeschalteter Provider kann niemanden mehr frisch anmelden, und die Konten, die nur über ihn verknüpft sind, würden dann auf den schwächeren E-Mail-Code ausweichen. Das Formular sagt dir vor dem Absenden, ob deine Änderung die Bestätigung braucht. Eine Sitzung mit einem persönlichen API-Key kann Provider gar nicht ändern.

    Bekannter Randfall: Meldest du dich **nur** über genau den Provider an, den du reparieren willst, und funktioniert der gerade nicht, kannst du dich dort nicht erneut anmelden. Setze dir vorher ein lokales Passwort. <!-- #1883, #1906 -->

!!! info "Das Client-Secret ist nur beschreibbar"
    Das Client-Secret wird verschlüsselt gespeichert und nie wieder angezeigt — weder in der Liste noch im Bearbeiten-Formular. Beim Bearbeiten lässt du **Neues Client-Secret** leer, um das gespeicherte zu behalten; ein neues Secret verlangt deine Bestätigung. <!-- #1906 -->

!!! info "Feste Endpunkte und Standard-Mandant setzt du beim Hinzufügen"
    Unter **Erweitert** im Formular zum Hinzufügen gibst du feste Adressen für Autorisierung, Token, Userinfo und Schlüsselverzeichnis an, dazu den Standard-Mandanten, dem neue föderierte Konten beitreten. Die Oberfläche zeigt sie danach nicht an, weil die Schnittstelle zum Server sie nicht zurückgibt; zum späteren Ändern nutzt du die REST-Schnittstelle unter `/api/v1/admin/oidc-providers` (`PUT`). Auch den Kurznamen (Slug) kannst du nach dem Hinzufügen nicht mehr ändern: Er steckt in der Rückruf-URL. <!-- #1906 -->

!!! info "Rückruf-URL beim Provider hinterlegen"
    Trage beim Provider als Rückruf-URL (Redirect URI) genau `{APP_BASE_URL}/api/v1/auth/oauth/{slug}/callback` ein — mit der öffentlichen Adresse aus `APP_BASE_URL` und dem Kurznamen (Slug) des Providers, z.B. `https://garten.example/api/v1/auth/oauth/google/callback`. Anmeldung und erneute Anmeldung zur Bestätigung nutzen dieselbe URL. Steht `APP_BASE_URL` noch auf der Voreinstellung `http://localhost:5173`, lehnt der Provider die Anmeldung ab. <!-- #1865 -->

!!! info "Zwei Provider, dieselbe Kennung"
    Eine Verknüpfung gehört zu genau dem Provider, über den sie entstand. Meldet ein anderer Provider dieselbe Nutzerkennung (`sub`), ist das eine andere Person — sie wird nie in das verknüpfte Konto angemeldet. Ältere Verknüpfungen hat das Update dem Provider zugeordnet, wenn es genau einen ihres Typs gab. Waren zu dem Zeitpunkt schon zwei generische OIDC-Provider eingerichtet, ist die Zuordnung offen: Die Betroffenen melden sich einmal über ihre bestätigte E-Mail-Adresse neu an (oder mit ihrem Passwort). <!-- #1869 -->

!!! info "Provider löschen, neu anlegen, auf einen anderen Aussteller umstellen"
    Beim **Löschen** eines Providers werden auch alle Verknüpfungen gelöscht, die über ihn entstanden sind (samt der verschlüsselten Provider-Token) — sonst würde ein später unter demselben Kurznamen (Slug) angelegter Provider, womöglich bei einem anderen Identity-Provider, sie erben. Die betroffenen Konten behalten ihre übrigen Anmeldewege; wer nur über diesen Provider angemeldet war, meldet sich nach dem Neuanlegen einmal über die bestätigte E-Mail-Adresse neu an (oder mit dem Passwort). Das Log-Ereignis `oidc_provider.deleted` nennt die Anzahl (`links_deleted`), keine Konten. Auch das **Anlegen** räumt Verknüpfungen weg, die ein früheres Löschen unter diesem Slug zurückgelassen hat. Beim **Umstellen** von `issuer_url` oder `provider_type` wird das gespeicherte Discovery-Dokument im selben Schritt gelöscht: Es gehörte dem alten Aussteller. Bis zum nächsten Abruf (alle 6 Stunden oder `POST /api/v1/admin/oidc-providers/{key}/test`) sind die Endpunkte des neuen Ausstellers unbekannt — hinterlegst du sie nicht selbst, rufe den Test gleich nach dem Umstellen auf. Ein abgerufenes Discovery-Dokument wird nur angenommen, wenn sein `issuer` der konfigurierte Aussteller ist und `authorization_endpoint`, `token_endpoint` und `jwks_uri` enthält. <!-- #1935, #1969 -->

!!! info "Anmeldung prüft das ID-Token"
    Die Anmeldung über einen Provider mit ID-Token prüft Signatur (Schlüssel aus `jwks_url` bzw. dem Discovery-Dokument), Aussteller, Zielgruppe (`aud`), `nonce` und Gültigkeit, und das `sub` darf nicht leer sein und muss zum Userinfo-Ergebnis passen. Scheitert die Anmeldung eines bisher funktionierenden Providers danach mit `provider_error`, suche im Log nach dem Ereignis `oauth_login_refused` — das Feld `reason` sagt, welche Prüfung scheiterte (`signature` oder `jwks_unavailable`: Schlüssel nicht erreichbar bzw. falsch; `iss`: `issuer_url` stimmt nicht mit dem `iss` des Providers überein; `sub_mismatch`: Userinfo und ID-Token nennen verschiedene Personen). Das Schlüsselverzeichnis muss über `https` erreichbar sein. <!-- #1936 -->

!!! info "Nur `https`-Adressen; Schlüsselabruf mit Zwischenspeicher und Grenzen"
    `issuer_url`, `authorization_url`, `token_url`, `userinfo_url` und `jwks_url` (optional: pinnt den Schlüsselendpunkt des Providers) nehmen das Formular und die API nur als `https`-Adresse an — sonst antwortet sie mit `422`. Nur mit `DEBUG=true` ist `http` zu `localhost`, `127.0.0.1` oder `::1` erlaubt (lokale Entwicklung gegen einen Provider auf demselben Rechner). Eine Konfiguration, die du vor dieser Regel mit `http` gespeichert hast, bleibt gespeichert, wird aber bei der Anmeldung nicht mehr angesprochen: Die Anmeldung endet mit `provider_error`, bis du die Adresse auf `https` änderst — der Test (`POST /api/v1/admin/oidc-providers/{key}/test`) nennt den Grund. Schickt eine Änderung das alte `http`-Feld unverändert mit, antwortet sie ebenfalls mit `422`.

    Die Schlüssel des Providers ruft der Server nicht bei jeder Anmeldung ab: Er behält sie je Provider zehn Minuten im Arbeitsspeicher des jeweiligen Workers und holt sie neu, wenn ein ID-Token einen unbekannten Schlüssel (`kid`) nennt — höchstens einmal alle zehn Sekunden je Provider. Ein Abruffehler gilt nur 30 Sekunden; danach versucht der Server es wieder. Antworten über 256 KiB werden verworfen, ein einzelner unbrauchbarer Schlüssel im Verzeichnis wird übersprungen. Nennt das Discovery-Dokument des Providers ein `jwks_uri` auf eine interne Adresse (Metadaten-Dienst, privates Netz), ruft der Server es nicht ab; ein Provider im eigenen Netz darf sein Schlüsselverzeichnis nur auf seinem eigenen Host veröffentlichen — andernfalls trage es selbst als `jwks_url` ein. Zusätzlich verweigert die Anmeldung ein ID-Token, das noch nicht gültig ist (`nbf`, 30 Sekunden Toleranz, Grund `nbf`) oder vor mehr als zehn Minuten ausgestellt wurde (`iat`). <!-- #1987 -->

    Dieselbe Regel gilt für den Token- und den Userinfo-Endpunkt, die das Client-Secret, den Autorisierungscode bzw. das Access-Token erhalten: Stammen sie aus dem Discovery-Dokument, ruft der Server sie nie auf einer Metadaten- oder Link-Local-Adresse und auf einer privaten Adresse nur auf dem Host des Ausstellers selbst auf; trägst du `token_url` oder `userinfo_url` selbst ein, ist eine private Adresse deine Wahl, die Metadaten-Adresse nie. Auch die Adresse von `issuer_url` wird vor dem Abruf des Discovery-Dokuments so geprüft. Ihre Antworten sind wie das Schlüsselverzeichnis auf 256 KiB begrenzt. Eine verweigerte Anmeldung erscheint im Log als `oauth_endpoint_refused` (Grund etwa `The token endpoint resolves to a blocked address.`), der Browser sieht `provider_error`. <!-- #2007 -->

!!! info "Test meldet Schlüssel und Aussteller"
    `POST /api/v1/admin/oidc-providers/{key}/test` liefert neben `scope_check` und `provider_type_check` zwei weitere Befunde, damit du eine scheiternde Anmeldeprüfung siehst, bevor Nutzer sie treffen: `jwks_check` (`ok`, `jwks_url`, `key_count`, `skipped_key_count`, `key_ids`, `detail`) ruft das Schlüsselverzeichnis wie die Anmeldung ab und sagt, ob das gelang; `issuer_check` (`ok`, `configured_issuer`, `accepted_issuers`, `discovery_issuer`, `detail`) sagt, ob der `iss`, den der Provider ankündigt, der ist, den die Anmeldung akzeptiert. Weicht er ab, nennt `detail` den angekündigten Wert, den du als `issuer_url` setzen musst. Beide Befunde haben `applicable: false`, wenn der Provider kein ID-Token ausstellt (GitHub oder ein Provider ohne `openid`-Scope). Der Test füllt den Zwischenspeicher der Anmeldung nicht. Beim **Umstellen** von `issuer_url` löscht die API außerdem die gespeicherten Adressen `authorization_url`, `token_url`, `userinfo_url` und `jwks_url`, die die Anfrage nicht neu nennt — sie gehörten dem alten Aussteller. <!-- #1987 -->

!!! info "Gleichzeitiges Löschen und Neuanlegen"
    Eine Anmeldung, die läuft, während du einen Provider löschst und unter demselben Slug neu anlegst, schreibt keine Verknüpfung und kein Konto mehr in den neuen Provider: Die Anmeldung endet mit `provider_error` (`reason=configuration_changed`). Verknüpfungen tragen jetzt zusätzlich den Schlüssel ihrer Konfiguration; ältere ohne Schlüssel gelten wie bisher über den Slug. Das Anlegen erzeugt die Konfiguration zuerst deaktiviert, entfernt die Waisen des Slugs und schaltet sie dann ein; legen zwei Admins gleichzeitig denselben Slug an, scheitert der zweite mit `409`, ohne Verknüpfungen des ersten zu löschen. <!-- #1987 -->


!!! warning "Der Provider-Typ ist auf vier Werte festgelegt"
    Gültig sind ausschließlich `google`, `github`, `apple` und `oidc` — kleingeschrieben. Alles andere, auch `GitHub` oder `GITHUB`, wird beim Anlegen und beim Ändern mit `422` abgelehnt.

    Grund: Die Anmeldung wertet den Typ zeichengenau aus. Ein als `GitHub` eingetragener Provider wurde bisher gespeichert und danach vom **generischen OIDC-Zweig** bedient — die bekannten Endpunkte von GitHub wurden nicht eingesetzt, der GitHub-Adressabruf unterblieb, und nichts hat sich beschwert.

    `oidc` ist der richtige Wert für jeden Provider ohne eigene Sonderbehandlung (Keycloak, Authentik, Azure AD, Okta); die Endpunkte kommen dann aus dem Discovery-Dokument.

    Für Provider, die vor dieser Prüfung gespeichert wurden, meldet `POST /api/v1/admin/oidc-providers/{key}/test` den Befund im Feld `provider_type_check` (`ok`, `provider_type`, `known_provider_types`, `detail`). Bestehende Einträge werden **nicht** automatisch umgeschrieben — korrigiere sie im Bearbeiten-Formular (oder per `PUT`).

!!! warning "GitHub braucht den Scope `user:email`"
    Ein Provider vom Typ `github`, dessen Scope-Liste weder `user:email` noch den übergeordneten Scope `user` enthält, wird beim Anlegen und beim Ändern mit `422` abgelehnt.

    Grund: GitHub liefert das Merkmal, ob eine Adresse bestätigt ist, ausschließlich über `GET /user/emails`, und dieser Endpunkt antwortet ohne den Scope mit `403`. Ohne ihn gilt bei **jeder** Anmeldung über diesen Provider die Adresse als unbestätigt, und ein bereits vorhandenes Konto wird nie automatisch verknüpft — bisher war das nur an einer Logzeile pro Anmeldung zu erkennen.

    Auf die Schreibweise kommt es an: GitHub kennt nur Kleinbuchstaben, `USER:EMAIL` wird abgelehnt. Mehrere Scopes dürfen in einem Eintrag stehen (`"read:user user:email"`).

    Für Provider, die vor dieser Prüfung gespeichert wurden, meldet `POST /api/v1/admin/oidc-providers/{key}/test` denselben Befund im Feld `scope_check` (`ok`, `missing_scopes`, `detail`). Der Test verlangt kein gültiges Discovery-Dokument — GitHub veröffentlicht keins, der Scope-Befund kommt trotzdem.

Mehr dazu: [Authentifizierung](../api/authentication.md).

---

## Pflanzenerkennung per Foto aktivieren

Die [Foto-Identifikation](plant-identification.md) ist ein optionales Feature, das API-Zugangsdaten eines Drittanbieters erfordert. Solange kein Key konfiguriert ist, meldet das Backend `available: false` und die gesamte Kamera-/Upload-UI bleibt für alle Nutzer ausgeblendet.

Der Pl@ntNet-API-Key ist eine **instanzweite Einstellung** — ein einziger Key gilt für alle Nutzer der Instanz. Der Free-Tier erlaubt 500 Identifikationen pro Tag für die gesamte Instanz.

!!! note "Plattform-Admin erforderlich"
    Nur Nutzer mit der Plattform-Rolle **admin** können den API-Key verwalten. Die Einstellung gilt plattformweit.

### Schritt 1: Kostenlosen Pl@ntNet-Key besorgen

1. Öffne [my.plantnet.org](https://my.plantnet.org) in einem Browser
2. Erstelle ein Konto oder melde dich an
3. Navigiere zu **Account** > **API key**
4. Kopiere den angezeigten API-Key

!!! warning "Nur für nicht-kommerzielle Nutzung"
    Der Pl@ntNet Free-Tier ist ausdrücklich für nicht-kommerzielle Nutzung lizenziert. Für kommerzielle Instanzen die Nutzungsbedingungen auf [my.plantnet.org](https://my.plantnet.org) prüfen.

### Schritt 2: Key über die Admin-UI eintragen (empfohlen)

Dies ist der **bevorzugte Weg** — kein Pod-Neustart, keine Datei-Änderung, wirkt sofort.

1. Melde dich als Plattform-Admin an
2. Öffne **Konto-Einstellungen** (oben rechts auf dein Profilbild klicken)
3. Wähle den Tab **Integrationen**
4. Scrolle zum Abschnitt **Pflanzenerkennung**
5. Gib den kopierten API-Key in das Feld **Pl@ntNet API-Key** ein
6. Klicke auf **Speichern**

Der Key wird maskiert gespeichert (nie im Klartext in Antworten oder Logs sichtbar). Das Feld zeigt an, ob der Key aus der Datenbank (UI-Eintrag), aus einer Umgebungsvariable oder gar nicht gesetzt ist.

**Optional: Key sofort prüfen**

Nach dem Speichern kannst du auf **Verbindung prüfen** klicken. Das Backend sendet eine Testanfrage an Pl@ntNet und meldet, ob der Key gültig ist und wie viele Anfragen heute noch verfügbar sind.

!!! info "Verschlüsselt gespeichert"
    Den Pl@ntNet-Key und den Home-Assistant-Token speichert Kamerplanter verschlüsselt mit dem `FERNET_KEY` der Instanz; die Oberfläche zeigt nur die letzten vier Zeichen. Ohne `FERNET_KEY` — das geht nur mit `DEBUG=true` — bleiben sie im Klartext, und das Log meldet `encryption_disabled`. <!-- #2113 -->

**Optional: Key entfernen**

Klicke auf **Entfernen**, um den in der Datenbank gespeicherten Key zu löschen. Ist keine Umgebungsvariable gesetzt, wird die Foto-Identifikation damit deaktiviert.

---

### Alternative: Key als Umgebungsvariable setzen

Die Umgebungsvariable `PLANTNET_API_KEY` bleibt weiterhin gültig — sie eignet sich für automatisierte Deployments, GitOps-Workflows oder wenn kein UI-Zugang genutzt werden soll.

!!! warning "Priorität: UI-Wert hat Vorrang"
    Ist in der Datenbank ein Key über die Admin-UI gespeichert, **überschreibt dieser den Wert der Umgebungsvariable** `PLANTNET_API_KEY`. Ein per UI gesetzter Key wirkt sofort ohne Pod-Neustart. Die Umgebungsvariable greift nur, wenn kein DB-Eintrag vorhanden ist.

=== "Produktion / Kubernetes"

    Lege einen Kubernetes-Secret an und lade ihn per `envFrom` ins Backend. **Niemals** den Key im Klartext in `values.yaml` committen.

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PLANTNET_API_KEY="dein-api-key" \
      --namespace kamerplanter
    ```

    Im Helm-Values referenzieren:

    ```yaml
    # helm/kamerplanter/values.yaml (Auszug)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

    Nach dem nächsten Rollout liest das Backend den Key automatisch aus der Secret-Umgebungsvariable.

=== "Lokales Dev (kind / Skaffold)"

    Für schnelle Tests ohne Kubernetes-Secret: die Variable direkt in den `env:`-Block des Backend-Containers in `helm/kamerplanter/values.yaml` eintragen. **Nicht committen.**

    ```yaml
    # helm/kamerplanter/values.yaml (lokal, nicht committen)
    backend:
      env:
        PLANTNET_API_KEY: "dein-api-key"
    ```

    Skaffold deployt die Änderung automatisch neu.

=== "Docker Compose"

    Trage den Key in die `.env`-Datei im Repository-Wurzelverzeichnis ein:

    ```bash
    # .env (nicht committen)
    PLANTNET_API_KEY=dein-api-key
    ```

    Starte den Stack neu:

    ```bash
    docker compose up -d
    ```

### Schritt 3: Aktivierung per API prüfen

Rufe den Status-Endpunkt auf:

```bash
curl -s http://localhost:8000/api/v1/recognition/status | python3 -m json.tool
```

Erwartete Antwort, wenn der Key korrekt gesetzt ist:

```json
{
  "available": true,
  "adapter": "plantnet",
  "daily_limit": 500,
  "remaining_today": 498
}
```

Nach erfolgreicher Konfiguration erscheinen in der UI automatisch die Kamera-/Upload-Funktion und die Schaltfläche **Per Foto hinzufügen** in der Artenübersicht. Nutzer sehen beim ersten Aufruf den Einwilligungs-Dialog — die Funktion ist ab diesem Moment vollständig nutzbar.

### Optionale Feineinstellung

Die folgenden Variablen müssen in der Regel nicht geändert werden. Sie sind mit sinnvollen Standardwerten vorbelegt. Eine vollständige Beschreibung findet sich in der [Umgebungsvariablen-Referenz](../reference/environment-variables.md#foto-identifikation-req-029):

| Variable | Standard | Zweck |
|----------|---------|-------|
| `IDENTIFICATION_PRIMARY_ADAPTER` | `plantnet` | Bevorzugter Adapter (erweiterbar) |
| `IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT` | `0.85` | Schwelle für „sehr sicher"-Hervorhebung |
| `IDENTIFICATION_CONFIDENCE_MIN_SHOW` | `0.10` | Mindest-Übereinstimmung für Anzeige |
| `IDENTIFICATION_MAX_IMAGE_SIZE_MB` | `10` | Maximale Bildgröße in Megabyte |
| `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` | `0` | Max. Anfragen pro Nutzer/Tag (`0` = Adapter-Limit) |

### Datenschutz-Hinweis

Fotos werden **nicht** auf dem Kamerplanter-Server gespeichert — sie werden ausschließlich zur Analyse an Pl@ntNet (CIRAD/INRIA, Frankreich/EU) übertragen und danach verworfen. EXIF-Metadaten (GPS, Kameramodell) werden vor der Übertragung entfernt. Jeder Nutzer muss einmalig der Bildübertragung zustimmen. Weitere Details: [Datenschutz (DSGVO) — Foto-Identifikation](privacy.md#foto-identifikation-plant_identification).

---

## Schädlingserkennung aktivieren {#schaedlingserkennung-aktivieren}

Die [Schädlingserkennung](pest-detection.md) ist standardmäßig deaktiviert (`PEST_DETECTION_ENABLED=false`). Solange kein Adapter konfiguriert ist, meldet das Backend `adapter: null` und der Button „Auf Schädlinge prüfen" bleibt für alle Nutzer ausgeblendet.

!!! note "Plattform-Admin erforderlich"
    Nur Nutzer mit der Plattform-Rolle **admin** können die Schädlingserkennung konfigurieren. Die Einstellungen gelten plattformweit.

!!! note "Phase 1 — Self-Hosted-First"
    In der aktuellen Phase (Phase 1) stehen zwei Adapter zur Verfügung: der lokale **Schadbild-Adapter** (`local_pest_symptom`, erfordert keine externen Dienste oder Einwilligung) und der optionale **Cloud-Adapter** (Kindwise, einwilligungspflichtig). Ein Self-Hosted-Direkt-Detektor mit ONNX ist für Phase 2 in Vorbereitung.

### Adapter 1: Lokaler Schadbild-Adapter (Self-Hosted, empfohlen)

Der lokale Adapter erkennt Schadbilder und Symptome (Gespinste, Honigtau, Saugschäden) direkt auf der Instanz — kein Drittanbieter, kein Datenschutz-Consent für Nutzer erforderlich.

**Aktivieren via Umgebungsvariable:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_SYMPTOM_ENABLED=true
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
```

=== "Kubernetes / Helm"

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PEST_DETECTION_ENABLED="true" \
      --from-literal=PEST_DETECTION_SYMPTOM_ENABLED="true" \
      --from-literal=PEST_DETECTION_PRIMARY_ADAPTER="local_pest_symptom" \
      --namespace kamerplanter
    ```

    Im Helm-Values referenzieren:

    ```yaml
    # helm/kamerplanter/values.yaml (Auszug)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

=== "Docker Compose"

    ```bash
    # .env (nicht committen)
    PEST_DETECTION_ENABLED=true
    PEST_DETECTION_SYMPTOM_ENABLED=true
    PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
    ```

    Starte den Stack neu:

    ```bash
    docker compose up -d
    ```

=== "Lokales Dev (kind / Skaffold)"

    ```yaml
    # helm/kamerplanter/values.yaml (lokal, nicht committen)
    backend:
      env:
        PEST_DETECTION_ENABLED: "true"
        PEST_DETECTION_SYMPTOM_ENABLED: "true"
        PEST_DETECTION_PRIMARY_ADAPTER: "local_pest_symptom"
    ```

!!! warning "Voraussetzung: Inferenz-Service + Few-Shot-Index"
    Der lokale Schadbild-Adapter erkennt über **Few-Shot-Klassifikation mit einem frozen DINOv2-Modell** (kein separates, lizenzkritisches Modell). Damit der Button erscheint und echte Befunde liefert, sind **zwei** Schritte nötig:

    1. **Inferenz-Service bereitstellen** (derselbe Dienst wie für die Pflanzenerkennung). Sobald er erreichbar ist, beantwortet er `GET /pest/ready`. <!-- REQ-029-A -->
    2. **Few-Shot-Index aufbauen** — einmalig pro Klasse ~30 CC0/CC-BY-Bilder von GBIF beschaffen und als Prototypen indizieren. **Keine GBIF-Zugangsdaten nötig** (öffentliche Occurrence-Suche):

        ```bash
        # im Backend-Container/-Umfeld, Inferenz-Service muss erreichbar sein
        python -m app.migrations.acquire_pest_dataset --manifest pest_reference_manifest.json
        ```

        Das Skript beschafft Bilder, filtert pro Bild auf CC0/CC-BY, indiziert die DINOv2-Prototypen im Inferenz-Service und schreibt ein **Attributions-Manifest** (CC-BY-Pflicht). Es werden **keine Bilder dauerhaft gespeichert**. Alternativ als Celery-Task `acquire_pest_dataset_task`.

    Solange der Index leer ist, meldet `/pest/detect` „keine Befunde" (kein Fehler). Der **Direkt-Detektor mit Bounding-Boxes** (Modus 1) bleibt für Phase 2 in Vorbereitung (extern blockiert: Modell-Lizenzfreigabe + Benchmark).

!!! tip "Nur Vorschau ohne Inferenz-Service"
    Zum reinen Ausprobieren der Oberfläche ohne Inferenz-Service den Demo-Adapter aktivieren: `PEST_DETECTION_ENABLED=true` + `PEST_DETECTION_DEMO_ENABLED=true`. Er liefert klar gekennzeichnete Platzhalter-Befunde — niemals für echte Entscheidungen.

### Adapter 2: Cloud-Erkennung (Kindwise — optional, einwilligungspflichtig)

Der Kindwise-Cloud-Adapter sendet Fotos zur Analyse an den Kindwise-Dienst (Brno, Tschechien — EU). Er ist standardmäßig deaktiviert und erfordert eine explizite Nutzereinwilligung (Consent-Zweck `pest_detection_cloud`).

!!! warning "Vertragsvoraussetzungen vor der Aktivierung prüfen"
    Vor der Aktivierung des Cloud-Adapters sind folgende Punkte zu klären:
    - Auftragsverarbeitungsvertrag (AVV nach Art. 28 DSGVO) mit Kindwise abschließen
    - EU-Hosting-Garantie und Datenaufbewahrungsdauer vertraglich bestätigen
    - Indoor-Eignung des `plant.health`-Produkts für die eigenen Schädlingsziel-Klassen empirisch testen
    Detaillierte Prüfpunkte: `spec/analysis/pest-detection-implementation-prep.md` §5.

**Aktivieren via Umgebungsvariablen:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_CLOUD_ENABLED=true
PEST_DETECTION_CLOUD_API_KEY=dein-kindwise-api-key
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom   # lokal bleibt Default; Cloud als Fallback oder primär wählbar
```

Die Schaltfläche erscheint nach dem nächsten Backend-Neustart automatisch in der UI. Nutzer, die den Cloud-Adapter nutzen möchten, werden beim ersten Aufruf zur Einwilligung aufgefordert.

### Status prüfen

Rufe den Status-Endpunkt auf (tenant-scoped, JWT erforderlich):

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/t/{tenant_slug}/pests/status | python3 -m json.tool
```

Erwartete Antwort, wenn ein Adapter aktiv ist:

```json
{
  "adapter": "local_pest_symptom",
  "pest_detection_enabled": true,
  "symptom_enabled": true,
  "detector_enabled": false,
  "cloud_enabled": false
}
```

Ist `pest_detection_enabled: false` oder `adapter: null`, bleibt der Button in der UI ausgeblendet.

### Optionale Feineinstellungen

Die folgenden Variablen müssen in der Regel nicht geändert werden. Eine vollständige Beschreibung findet sich in der [Umgebungsvariablen-Referenz](../reference/environment-variables.md#schaedlingserkennung-req-044):

| Variable | Standard | Zweck |
|----------|---------|-------|
| `PEST_DETECTION_ENABLED` | `false` | Gesamtschalter — Feature ein/aus |
| `PEST_DETECTION_SYMPTOM_ENABLED` | `true` | Schadbild-Erkennung (Modus 2) ein/aus |
| `PEST_DETECTION_DETECTOR_ENABLED` | `false` | Direkt-Detektor (Modus 1, Phase 2) ein/aus |
| `PEST_DETECTION_CLOUD_ENABLED` | `false` | Cloud-Adapter ein/aus |
| `PEST_DETECTION_CLOUD_API_KEY` | — | API-Key für den Cloud-Adapter (Kindwise) |
| `PEST_DETECTION_PRIMARY_ADAPTER` | `local_pest_symptom` | Bevorzugter Adapter |
| `PEST_DETECTION_MAX_IMAGE_SIZE_MB` | `8` | Maximale Bildgröße in Megabyte |

### Datenschutz-Hinweis

- **Lokaler Adapter:** Fotos verlassen die Instanz nicht; kein Consent erforderlich; EXIF wird vor jeder Verarbeitung entfernt.
- **Cloud-Adapter:** Fotos gehen an Kindwise (EU); Nutzer müssen einmalig für den Zweck `pest_detection_cloud` einwilligen; AVV vertraglich erforderlich; EXIF zweifach gestrippt (Frontend + Backend).
- Fotos werden nie dauerhaft gespeichert — nur Erkennungsergebnis und anonymer Bild-Hash bleiben.

Weitere Details: [Datenschutz (DSGVO)](privacy.md).

---

## Referenzbilder für die Bilderkennung kuratieren

Die Self-Hosted-Bilderkennung (DINOv2) vergleicht Nutzer-Fotos mit einem gespeicherten **Referenz-Index**. Enthält dieser Index unscharfe, falsch bestimmte oder anderweitig ungeeignete Bilder, verschlechtert sich die Erkennungsgenauigkeit für die betroffene Art.

Als Platform-Admin kannst du einzelne Referenzbilder nach einem **Sichttest abwählen** — sie werden dann aus der Erkennung ausgeschlossen, bleiben aber im System erhalten (Soft-Delete, reaktivierbar). Die vollständige Anleitung einschließlich Coverage-Schwellenwert (< 5 aktive Bilder), API-Endpunkten und FAQ findest du auf der Seite:

**[Referenzbilder kuratieren](reference-image-curation.md)**

---

## Nutzer-Schädlingsbilder freigeben (Moderation)

Nutzer können in der [Schädlings-Detailseite](pest-detail.md) eigene Fotos zu einem Schädling beitragen. Diese Bilder sind zunächst **privat** (nur für den jeweiligen Garten/Mandanten sichtbar). Als Platform-Admin kannst du besonders gute Aufnahmen **global freigeben**.

Die Moderation findest du im Admin-Bereich in der Karte **„Beigesteuerte Schädlingsbilder"**:

1. Wähle den betreffenden Schädling aus.
2. Du siehst alle beigesteuerten Bilder **aller Mandanten** mit Vorschau, Herkunft (Nutzer/Mandant/Datum) und Status (privat/global).
3. Mit **Freigeben** wird ein Bild auf `global` gesetzt — es ist dann für alle Nutzer in der Galerie sichtbar (über einen globalen, schreibgeschützten Auslieferungspfad, der ausschließlich freigegebene Bilder bereitstellt). **Zurücknehmen** macht die Freigabe rückgängig (mit Bestätigung).

!!! tip "Abwählen direkt auf der Detailseite"
    Als Platform-Admin kannst du Bilder auch **direkt auf der [Schädlings-Detailseite](pest-detail.md)** kuratieren: Mit dem Schalter **„Abgewählte einblenden"** werden auch deaktivierte Bilder sichtbar, und je Bild kannst du es **abwählen** (deaktivieren statt löschen) bzw. **wieder aufnehmen**. Das gilt für Erkennungs-Referenzbilder und für beigesteuerte Bilder. Normale Nutzer sehen ausschließlich aktive Bilder. Abwählen ist reversibel; der Erkennungs-Index bleibt von einer reinen Galerie-Abwahl unberührt.

!!! note "Wirkung auf die KI-Erkennung"
    Wenn die [Schädlingserkennung](#schaedlingserkennung-aktivieren) aktiv ist (`PEST_DETECTION_ENABLED=true`), wird ein freigegebenes Bild zusätzlich als Few-Shot-Referenz (`source=user_contributed`) in den Erkennungs-Index aufgenommen — sofern der Schädling eine Erkennungsklasse (`detection_slug`) hat. Es wird nur das Embedding samt Herkunft gespeichert, **kein Originalbild**. Das Zurücknehmen deaktiviert die Referenz wieder.

!!! warning "Datenschutz"
    Beigesteuerte Bilder werden beim Löschen eines Nutzers oder Mandanten vollständig entfernt (Dokument, Bilddatei samt Vorschaubildern). Standortdaten (EXIF) werden bereits beim Hochladen entfernt. Wurde ein Bild jemals freigegeben, entfernt dieselbe Löschung auch den daraus berechneten Erkennungsvektor aus der Erkennungsbasis — unabhängig davon, ob die Freigabe zum Zeitpunkt der Löschung noch aktiv oder bereits zurückgenommen war. Ist der Inferenz-Service dabei nicht erreichbar oder auf dem Celery-Worker nicht konfiguriert, bleibt die Löschung offen bzw. eine Mandantenlöschung wird abgelehnt, statt Vektoren zurückzulassen — siehe [Bilderkennung in Betrieb nehmen](../deployment/inference-service.md).

---

## Häufige Fragen

??? question "Wer kann die Plattform-Admin-Rolle vergeben?"
    Die Plattform-Admin-Rolle kann nur von einem bestehenden Platform-Admin vergeben werden — direkt über die API oder im Admin-Bereich, jeweils mit seinem Passwort bestätigt. Beim ersten Setup richtest du das erste Plattform-Admin-Konto auf dem Server ein (`python -m app.migrations.add_platform_admin <e-mail>`); der erste registrierte Nutzer wird **nicht** automatisch Platform-Admin.

??? question "Kann ein Platform-Admin auch Tenant-Daten einsehen?"
    Nein, nicht die Fachdaten. Ein Platform-Admin sieht Verwaltungsdaten über alle Mandanten hinweg — dass ein Mandant existiert, wie er heißt, wer Mitglied ist — aber keine Pflanzen, Ernten oder Tagebücher eines fremden Mandanten. Dafür müsste er dort regulär als Mitglied aufgenommen werden. <!-- REQ-049 §2.5 -->

??? question "Gibt es eine Viewer-Rolle für den Admin-Bereich?"
    Ja. Die Plattform-Rolle `viewer` bietet Lesezugriff auf alle Admin-Statistiken und Mandanten-Übersichten, jedoch keine Schreibberechtigungen.

??? question "Wo genau in der UI finde ich die Einstellung für den Pl@ntNet-Key?"
    Öffne **Konto-Einstellungen** (Klick auf dein Profilbild oben rechts) → Tab **Integrationen** → Abschnitt **Pflanzenerkennung**. Dort kannst du den Key eintragen, prüfen und entfernen. Die Einstellung ist nur für Nutzer mit der Plattform-Rolle **admin** sichtbar.

??? question "Kann ich den Key auch ohne UI als Umgebungsvariable setzen?"
    Ja. Die Umgebungsvariable `PLANTNET_API_KEY` ist weiterhin gültig und eignet sich für GitOps-Workflows oder automatisierte Deployments. Wichtig: Ein über die UI in der Datenbank gespeicherter Key hat **Vorrang** vor der Umgebungsvariable und wirkt sofort ohne Pod-Neustart.

??? question "Was passiert, wenn das Tages-Limit erschöpft ist?"
    Das Backend meldet `remaining_today: 0`. In der UI erscheint die Meldung „Tages-Limit für Bilderkennung erreicht. Morgen wieder verfügbar." Das Limit erneuert sich täglich um Mitternacht UTC. Alle anderen Funktionen bleiben uneingeschränkt verfügbar.

??? question "Kann ich einen anderen Erkennungsdienst als Pl@ntNet verwenden?"
    Aktuell ist Pl@ntNet der einzige implementierte Adapter (`IDENTIFICATION_PRIMARY_ADAPTER=plantnet`). Eine Phase-2-Erweiterung für lokale Offline-Erkennung (ohne Drittanbieter) ist geplant.

---

## Siehe auch

- [Mandanten & Gärten](tenants.md) — Mandantenverwaltung als Tenant-Admin <!-- REQ-024 -->
- [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md) — Abgrenzung Plattform-Rolle gegen Garten-Rolle
- [Datenschutz (DSGVO)](privacy.md) — Betroffenenrechte und DSGVO-Compliance
- [Authentifizierung](../api/authentication.md) — JWT, OAuth2/OIDC, Service Accounts
- [Pflanze per Foto identifizieren](plant-identification.md) — Endnutzer-Anleitung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablen-Referenz
