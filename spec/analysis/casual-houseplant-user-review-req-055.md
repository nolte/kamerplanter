# Review REQ-055 (v1.1) aus Sicht des lustlosen Zimmerpflanzen-Besitzers

**Dokument:** `spec/req/REQ-055_Plant-Identity-Plant-Social.md` v1.1
**Datum:** 2026-10-04
**Reviewer:** `casual-houseplant-user-reviewer` (Agent, Bericht vom Hauptagenten abgelegt)
**Persona:** UZG-001 Lena (26, kein Vorwissen, Link an Freunde schicken), ergänzend ZG-003 Julia (hat schon Mastodon, will 2–3 Pflanzen „sprechen" lassen).
**Gelesen:** §1–§12, §13.3/13.5/13.6, §15–§17, §25–§27 vollständig oder gezielt. Die Stellen §18–§24, §28–§37 und die Anhänge wurden nur überflogen; Aussagen dazu unter Vorbehalt.

---

## 1. Zusammenfassung

**Gesamturteil: für Lena nur mit Änderungen brauchbar. Für Julia gut gedacht, aber zu schwer.**

Das Dokument schützt Lena vor Fehlern (Privacy, Spam, Cannabis, Freigabe-Pflicht). Es gibt ihr aber keinen Anlass anzufangen. Der Weg „nur Link teilen" existiert technisch, ist aber nicht als eigener Weg beschrieben. Er steckt zwischen Begriffen wie Identität, Sichtbarkeit, Policy und Provider. Die Wörter „Mastodon", „Account", „Bot-Flag", „Instanz", „OAuth" und „Handle" tauchen im Nutzerfluss auf, ohne dass irgendwo steht, was das ist.

Die drei größten Probleme:
1. **Vokabular.** Lena sieht in der Oberfläche „Identität", „Sichtbarkeit", „Policy", „Provider" und „Zusammenfassen" (der Digest hat im Spec keinen Alltagsnamen). Kein Wort davon steht im Alltag einer Person mit drei Pflanzen.
2. **Der Link-Pfad ist kein eigener Pfad.** PS-UX-002 sagt „Name, Sichtbarkeit (Default nur intern), Speichern". Danach ist die Pflanze weiterhin unsichtbar. Lena muss die Sichtbarkeit anschließend noch einmal umstellen. Einen Button „Link zum Teilen erstellen" gibt es nicht.
3. **Das Nutzenversprechen fehlt.** §2 beschreibt eine Mastodon-Vision. Die UX-Anforderungen enthalten keinen Satz, der Lena sagt, warum sie das tun soll. Der Onboarding-Hinweis (PS-UX-014) ist SHOULD und nicht im MVP.

**Würde Lena das nach 2 Tagen aufgeben? Ja.** Sie würde den Tab „Identität" öffnen, ein leeres Formular sehen, „Profil" nicht verstehen und wegklicken. Wer es doch anlegt, lässt es auf „Nur intern" stehen und hat nichts davon.

**Positiv (Auswahl):**
- Default „keine Identität" (PS-PI-002).
- Standardmäßig nichts öffentlich (PS-PRI-002).
- Standort nur grob und nur getippt (PS-PRI-010).
- Die ersten 10 Posts werden geprüft (PS-SOC-003).
- Der Default `friendly` verlangt keine Konfiguration (PS-AI-001).
- Anti-Spam ist eingebaut.
- Das Profil läuft ohne Mastodon (§27 „Ohne Social Features").
- „Veröffentlichen ohne Provider heißt: auf dem Profil zeigen" (§27) ist genau Lenas Fall. Der Satz steht aber nur im Betriebsmodi-Kapitel.

---

## 2. Bewertung je Bereich

| Bereich | Note | Kommentar |
|---|---|---|
| Einstieg und Nutzenversprechen | ⭐⭐ | Leerer Zustand ist nur angekündigt („Erklärtext und Beispiel", §25.1). Es gibt keinen Wortlaut und keinen Nutzensatz. Der Hinweis PS-UX-014 ist nicht im MVP. |
| „Profil in 3 Schritten" | ⭐⭐⭐ | Schritte sind kurz, aber der Weg endet bei „Nur intern" und führt nicht zu einem teilbaren Link. |
| Link-Pfad für Lena (`unlisted`) | ⭐⭐ | Technisch vorhanden (§17.1), UX nicht ausgeführt. Der Begriff „unlisted" ist Mastodon-Jargon. |
| Sprache und Verständlichkeit | ⭐⭐ | PS-UX-005 benennt Ereignistypen in Alltagssprache (gut). Die Hauptbegriffe sind es nicht. |
| Mastodon-Assistent | ⭐⭐ | Für Julia machbar. Für Lena nicht, weil „Was ist Mastodon / wie komme ich zu einem Account" fehlt. |
| Freigabe-Liste | ⭐⭐⭐ | Gutes Sicherheitsnetz, aber mit Lastpotenzial (siehe F-08). |
| Fehlertexte | ⭐⭐⭐ | Zustände sind sauber, aber an Technik und Mastodon statt an Handlung ausgerichtet. |
| Privacy-Erklärung | ⭐⭐⭐⭐ | Konzept stark (PS-UX-003). Wortwahl und Angstvermeidung noch nicht spezifiziert. |
| Personality/KI | ⭐⭐⭐⭐ | Sinnvoll als Nicht-MVP. Vorlage hat aber ein inhaltliches Problem (F-12). |
| Mobile | ⭐⭐⭐ | Vorbildlich für Freigabe, aber „Foto vom Sofa posten" ist nicht als Ein-Hand-Ablauf beschrieben. |
| Spaß statt Pflicht | ⭐⭐ | Kein Belohnungsmoment, keine Reaktion, keine Vorschau mit Lenas eigener Pflanze. |

---

## 3. Antworten auf die zehn Prüffragen

**1. Begriffe (§25, §9).** Nein, nicht ohne Vorwissen.

| Spec-Begriff | Verstehe ich? | Alltagswort-Vorschlag |
|---|---|---|
| Identität / Plant Identity | ❌ klingt nach Personalausweis | **„Pflanzenprofil"** (Tab: „Profil") |
| Sichtbarkeit | ⚠️ | „Wer darf das sehen?" |
| `internal` / „Nur intern" | ⚠️ | „Nur ich und mein Haushalt" |
| `unlisted` | ❌ | „Jeder mit dem Link" |
| `public` | ✅ aber Angst | „Für alle im Netz auffindbar" (siehe F-10) |
| Policy | ❌ | „Was soll {Name} erzählen?" |
| Prüfen / Automatisch / Zusammenfassen / Nie | ⚠️ („Zusammenfassen" ist missverständlich) | „Erst fragen" / „Gleich posten" / „Einmal pro Woche" / „Nicht erzählen" |
| Digest | ❌ | „Wochenrückblick" |
| Verbindung / Provider | ❌ | „Mit Mastodon verknüpfen" bzw. „Konto verknüpfen" |
| Freigabe-Liste | ⚠️ | „Wartet auf dein OK" |
| Slug / Handle | ❌ | „Adresse deiner Pflanze" bzw. „Mastodon-Name" |
| Timeline | ⚠️ | „Verlauf" oder „Geschichte von {Name}" |
| Ereignis | ⚠️ | „Was passiert ist" |
| Allowlist, Disclosure, Bot-Flag, Instanz, Scope | ❌ | siehe F-06, F-07 |

Konkret: §25.1 nennt Tabs „Identität", „Timeline" und „Beiträge". Für Lena heißt das: „Profil", „Verlauf", „Veröffentlicht".

**2. „Profil in 3 Schritten" (PS-UX-002).** Zeitlich realistisch, motivational nicht. Was fehlt:
- Wortlaut des leeren Zustands und ein Nutzensatz.
- Ein Beispielprofil.
- Eine Vorschau mit Lenas eigener Pflanze und Foto, noch vor dem Speichern.
- Ein Ergebnis am Ende („Fertig, hier ist dein Link: Kopieren").

PS-UX-004 verlangt die Vorschau erst vor dem ersten Veröffentlichen. Lena sieht also erst nach Speichern und Umstellen, wie das aussieht, wenn sie überhaupt so weit kommt.

**3. Link-Pfad (`unlisted`).** Nicht klar genug. Beides ist inhaltlich vorhanden (Persona-Tabelle §6, Use Case UC-02, §17.1), aber nicht als zusammenhängender Ablauf. Das Wort „unlisted" stammt aus Mastodon und ist für Lena falsch besetzt. Siehe Vorschlag V-01.

**4. Mastodon-Assistent (PS-UX-008, §13.3).** Für Lena nicht gangbar, für Julia ja.
- Es fehlt eine Erklärung „Was ist Mastodon?".
- Es fehlt „Du brauchst zuerst ein Konto für deine Pflanze" mit Anleitung, bevor der Assistent nach der Instanz-Domain fragt.
- Das Bot-Flag wird als Blocker mit drei Optionen angezeigt (PS-MAS-022). Der Begriff ist ohne Erklärung unverständlich.
- Option (b) „mit `write:accounts` durch Kamerplanter setzen lassen" würde Lena am ehesten wählen, ist aber technisch und im Wortlaut unverständlich.
- Dieser Schritt bleibt auch bei guter Erklärung für Lena ein Abbruchpunkt (siehe V-06).

**5. Freigabe-Liste (PS-UX-006, `review`, erste 10 Posts).**
- Als Sicherheitsnetz gut. Standardmäßig steht fast alles auf `review` (planted, phase_changed, repotted, new_leaf, flower, harvested, photo_added, removed). Das erzeugt Posts, die Lena zwingend jedes Mal bestätigen muss, sobald ein Konto verbunden ist.
- Die Liste ist Last, sobald mehr als etwa 1 Karte pro Woche wartet. Bei drei Pflanzen mit Profil und Verbindung können es leicht 3 bis 5 pro Woche werden.
- Entwürfe laufen nach 14 Tagen ab (`review_ttl_days`). Wer zwei Wochen nichts tut, verliert sie stillschweigend. Das ist für Lena ein „Hausaufgaben"-Gefühl.
- **Aufgabe-Moment:** nach der zweiten wartenden Karte, die sie nicht sofort bearbeitet. Mit PS-UX-032 (Push „1 Beitrag wartet") nur als SHOULD.
- Regelung nach 10 Posts: Der Spec sagt, `auto` wirkt dann wirklich. Es fehlt aber ein Moment, in dem die App Lena das anbietet („Das lief 10-mal gut. Soll {Name} künftig ohne Rückfrage posten?"). Ohne diesen Moment bleibt Prüfen für immer an, oder Lena stellt es unbedacht auf 0 (F-09).

**6. Fehlertexte (§13.6, PS-UX-007).** Die Zustandstabelle ist gut. Als Nutzertext fehlt der Satz, was Lena tun soll:
- „temporary_exhausted", „connection_revoked", „account_suspended", „instance_blocked", „media_rejected", „moderation_hold", „text.too_long" sind Entwicklersprache. PS-UX-007 verweist nur auf „beschreibende Texte", nennt aber keine.
- Mastodon-Meldungen wie „revoked_remote" oder „suspended" erreichen sie ohne Handlungsanweisung.
- Der Zustand `draft(moderation_hold)` ist für Lena der schlimmste: ein Beitrag, der einfach nicht rausgeht. Hier braucht sie einen klaren Satz, warum.

**7. Privacy-Erklärung (PS-UX-003, §17).** Die Idee (kurze Liste „öffentlich: …, nie: …") ist richtig. Offen sind:
- Wortlaut für Lena. „Allowlist" darf nirgends erscheinen.
- Das Gefühl: Die Liste „Nie: Standort, Sensorwerte, Dünger, Notizen" ist beruhigend. Die Checkliste PS-PRI-013 („Fenster, Hausnummern, Personen, Nachbargebäude auf Fotos") ist wichtig, aber SHOULD. Fotos sind der reale Risikopunkt, nicht die Textfelder. Sie sollte MUST sein, mindestens beim ersten Veröffentlichen.
- Die Warnung bei `ambience_text` (PS-PRI-011) ist nur ein Hinweis. Für Lena („Ostfenster, Musterstraße 12") reicht ein freundlicher Hinweis; der Spec ist hier richtig.
- Gefahr zu locker: Die Stufe „Jeder mit dem Link" klingt harmlos. Ein weitergeleiteter Link ist aber nicht mehr kontrollierbar. Das fehlt im Erklärtext.
- Gefahr zu ängstlich: „Öffentlich" ohne Beispiel schreckt ab.

**8. Personality/KI (§15/§16, nicht MVP).** Lena erwartet das **nicht**. Der Ich-Ton („Ein neues Blatt! Ich wachse weiter.") kommt dagegen schon im MVP über Vorlagen.
- Problem: Die Vorlage in §12.4 („Mein Platz ({ambience_text}) tut mir offenbar gut.") klingt wie ein Textbaustein. Wer 10 Mal denselben Satz liest, ist genervt.
- Der Ich-Ton ist nicht für jeden: `minimalist` (PS-AI-004) existiert, wird aber erst „sobald Personality existiert" geliefert. Im MVP gibt es nur `friendly`. Wer die Vermenschlichung nicht mag (Lena könnte das cringe finden), hat keinen Ausweg außer dem manuellen Post.
- Die Ich-Form bedeutet, dass die Pflanze im Namen von Lena sprechen darf. Das ist ein Vertrauensthema und sollte in der Vorschau sichtbar sein („So klingt {Name}").

**9. Mobile (§26).** Konzept gut (Kartenstapel, 48 px, Alt-Text als eigener Schritt). Lücken für „Foto vom Sofa":
- Es fehlt ein Ein-Tap-Weg: Foto machen → „Auf dem Profil zeigen" (ohne Mastodon, ohne Alt-Text-Pflicht).
- Der Alt-Text als eigener Schritt (PS-SOC-012: leer nur nach bewusstem „ohne Beschreibung") ist für den reinen Profil-Fall zu viel. Er bremst Lena aus. Vorschlag: Beim reinen Profil automatisch aus Bildunterschrift/Vorlage vorbefüllen, ohne Pflicht-Dialog.
- PS-UX-031 verweist auf den REQ-052-Erfassungsweg („Teilen" aus Galerie/Tagebuch). Das ist ein Umweg: Foto aufnehmen, speichern, teilen. Es fehlt ein direkter Button „Foto → Profil".

**10. Was für den Spaß fehlt:** siehe Abschnitt 6.

---

## 4. Findings

### Dealbreaker (Lena steigt aus)

**F-01 Kein eigener Pfad „Link teilen" (PS-UX-002, §17.1, UC-02).**
Anlegen endet im Default `internal`. Teilen verlangt einen zweiten Durchgang durch Sichtbarkeit. Es gibt keinen Button, der einen Link erzeugt und kopiert. → V-01.

**F-02 Leerer Zustand und Nutzenversprechen fehlen (§25.1, PS-UX-014).**
Der Tab „Identität" soll „Erklärtext und Beispiel" zeigen, aber ohne Wortlaut. Der Anstoß in der App (PS-UX-014) ist SHOULD und nicht im MVP. Ohne diese beiden Dinge findet Lena die Funktion nicht und weiß nicht, wozu sie dient. → V-02, V-03.

**F-03 Hauptbegriffe sind Fachsprache (§25.1, PS-UX-005, PS-UX-007, PS-UX-013).**
„Identität", „Sichtbarkeit", „Policy", „Verbindung", „Digest", „Freigabe" sind in den Tabs, i18n-Schlüsseln und Enums gesetzt. i18n-Namespaces wie `pages.plantIdentity.*` sind interne Namen und dürfen so bleiben, aber die sichtbaren DE-Texte sind nicht festgelegt. Es fehlt eine verbindliche Begriffsliste. → V-04.

**F-04 Mastodon-Assistent setzt Vorwissen voraus (PS-UX-008, §13.3, PS-MAS-022).**
Kein „Was ist Mastodon", keine Anleitung zum Konto, Bot-Flag unerklärt. → V-05, V-06.

### Frustrierend

**F-05 Viele Typen standardmäßig `review`, danach fehlt ein sanfter Übergang zu `auto` (§11.2, PS-SOC-003).** Kein „Das lief gut, soll es automatisch laufen?"-Moment; das Abschalten (min 0) erfolgt nur „nach explizitem Hinweis", dessen Wortlaut offen ist. → V-07.

**F-06 Fehlertexte sind Zustände, keine Handlungsanweisungen (§13.6, PS-UX-007).** → V-08.

**F-07 Drei Optionen beim Bot-Flag, keine Empfehlung (PS-MAS-022).** Lena wählt blind. Eine Option muss als „Empfohlen" markiert sein, mit einem Satz Warum („Damit andere sehen, dass hier eine App für die Pflanze postet — das wird auf Mastodon erwartet"). → V-06.

**F-08 Freigabe-Verfall nach 14 Tagen ist stumm (§12.2 `review_ttl_days`).** Entwürfe verschwinden, ohne dass Lena es merkt. Zumindest ein Hinweis kurz vor Ablauf nötig. → V-07.

**F-09 „Erste 10 Posts prüfen" lässt sich auf 0 setzen (PS-SOC-003).** Zu locker für eine Person, die das Konzept nicht versteht. Mindestens: Zwischenschritt mit Konsequenz („Dann geht alles ohne Rückfrage raus, auch ein ungünstiges Foto"). → V-07.

**F-10 Stufe „public" ohne Gegengewicht (PS-UX-003, `allow_indexing`).** Der Default ist gut gewählt (`noindex` bis aktiviert). Für Lena fehlt die Übersetzung: „public" klingt wie „ins Internet gestellt", der Unterschied zu „Jeder mit dem Link" ist unklar. Zwei Stufen reichen für den Start; `public` sollte erst mit Hinweis erscheinen (V-01).

**F-11 Alt-Text-Pflicht im reinen Profil-Fall (PS-SOC-012, PS-SOC-031).** Der Dialog „ohne Beschreibung" bremst. → V-09.

**F-12 Vorlage in §12.4 klingt nach Baustein.** Zwei Varianten pro Ereignis reichen nicht; der angehängte Satz „Mein Platz (…) tut mir offenbar gut." wiederholt sich bei jedem Blatt. Wirkung: Lena findet es peinlich, bevor sie die Freigabe drückt, und verwirft Posts. → V-10.

### Überfordernd

**F-13 Policy-Tabelle mit 25 Ereignistypen (PS-UX-005, §11.2).** Für Lena sind Typen wie `care_done`, `moved`, `pest_detected`, `disease_detected`, `treatment_applied`, `sensor_threshold`, `propagated` nicht relevant, stehen aber als Zeilen da. Hinzu kommen Limits, Hashtags, Content-Warnung, Mentions, Quiet Hours. Sichtbar dürfen sie nur nach „Erweitert" sein. → V-11.

**F-14 Unterseite `/social` mit vier Bereichen (§25.1).** Freigaben, Verbindungen, Identitäten, Protokoll. Für Lena eine zentrale Seite zu viel; das Protokoll gehört nicht in ihre Navigation. → V-11.

**F-15 Hashtags und Begriffe wie „Content Warning", „Mentions" (§12.3).** Gehören in den Expertenbereich.

### Gut gelöst

- PS-PI-002: keine automatische Identität.
- PS-PRI-002/010: Allowlist, Standort nur grob und getippt.
- PS-UX-003: Wer-sieht-was in einem Satz.
- PS-SOC-003: Schutzschalter für die ersten Posts.
- PS-SOC-006: Keine Kamerplanter-Werbung in Posts.
- PS-SOC-040: Kein In-App-Mastodon-Client (weniger Oberfläche).
- §27: Profil ohne Mastodon voll nutzbar.
- PS-UX-005: Alltagsnamen für Ereignistypen („Neues Blatt", „Gegossen").
- PS-UX-009: Herkunftskennzeichen konsistent.
- PS-UX-001: Timeline unabhängig vom Social-Modul.
- Cannabis-Sperre mit Erklärung (für Lena irrelevant, aber ohne Risiko).

---

## 5. Priorisierte Änderungsvorschläge

### Muss vor Umsetzung (P1)

**V-01 Eigener Pfad „Profil teilen" (zu PS-UX-002, PS-UX-004, UC-02, §17.1).**
- Zwei Sichtbarkeitsstufen vorne: **„Nur für mich und meinen Haushalt"** (Default) und **„Jeder mit dem Link"**. Die dritte Stufe („Für alle im Netz auffindbar") erst unter „Mehr Optionen" mit Hinweis.
- Schritt 3 von PS-UX-002 anders: statt „Speichern" → **„Profil ansehen und Link kopieren"**. Ablauf: (1) Name bestätigen, (2) Wer darf es sehen, (3) Vorschau mit eigenem Foto und Button **Link kopieren / Teilen**. Beim reinen Haushalts-Default heißt der Button „Speichern", und der Link bleibt aus.
- Vor dem Erzeugen des Links der Satz: „Wer den Link hat, kann das Profil sehen — auch wenn er ihn weitergibt. Dein Name und dein Wohnort stehen nicht drin."
- Den Slug vorbefüllen und standardmäßig verbergen (Feld „Adresse ändern" unter „Mehr"). Lena sieht nur den fertigen Link.
- Auf diesem Pfad dürfen die Wörter „Mastodon", „Provider", „Policy", „Timeline", „Handle" nicht vorkommen. Als Abnahmekriterium in §33 aufnehmen (Textsuche in den DE-Strings des Pfads).

**V-02 Wortlaut des leeren Zustands festlegen (zu §25.1, PS-UX-002).**
Normative Textbausteine in den Spec, z. B.:
- Titel: „Gib {Name} ein Profil"
- Nutzensatz: „Zeig Freunden, wie {Name} wächst — mit einer Seite, die du per Link teilen kannst. Du entscheidest, was drauf steht."
- Beispiel: eine Beispielkarte mit Foto, Name, „Seit März 2024" und zwei Verlaufseinträgen, klar als Beispiel gekennzeichnet.
- Ein Button, ein Nebenlink „Was sehen andere?".

**V-03 Anstoß in den MVP ziehen (PS-UX-014 von SHOULD/„nein" auf MUST/MVP) und Auslöser ändern.**
- Der Auslöser „nach dem fünften Tagebucheintrag" trifft Lena nie, weil sie kaum Tagebuch schreibt. Besser: nach dem ersten Foto an einer Pflanze oder nach dem ersten Gießen-Tap, einmalig, abweisbar, mit Vorschaubild der eigenen Pflanze.
- **Frage an die Spec:** Der Modulkatalog setzt `social` auf Default-Level `intermediate` (PS-UX-001). Wer auf Anfänger-Stufe ist, sieht Tab und Hinweis dann überhaupt? Empfehlung: Der Tab „Profil" sollte auch für Anfänger sichtbar sein, nur der Social-Teil nicht.

**V-04 Verbindliche Begriffsliste in den Spec (neuer Absatz in §25 oder Anhang).**

| Intern | Sichtbar für Anwender |
|---|---|
| Plant Identity | Pflanzenprofil |
| Timeline | Verlauf |
| Beiträge (Tab `social`) | Veröffentlicht |
| visibility internal | Nur ich und mein Haushalt |
| visibility unlisted | Jeder mit dem Link |
| visibility public | Für alle im Netz auffindbar |
| Policy | Was soll {Name} erzählen? |
| never / review / auto / digest | Nicht erzählen / Erst fragen / Gleich erzählen / Einmal pro Woche |
| Digest | Wochenrückblick |
| Freigabe-Liste | Wartet auf dein OK |
| SocialConnection | Verknüpftes Mastodon-Konto |
| Slug | Adresse |

„Admin", „Mitglied", „Nutzer" bleiben laut PS-UX-015 ausgeschlossen. Zusätzlich im Glossar die Begriffe Mastodon, Fediverse, Bot-Kennzeichnung erklären.

### Wichtig (P2)

**V-05 Vor dem Assistenten: „Was ist Mastodon?" (zu PS-UX-008, §13.3).**
- Erster Bildschirm des Assistenten: zwei Sätze Erklärung und eine ehrliche Voraussetzung: „Dafür brauchst du ein Mastodon-Konto für {Name} (nicht dein eigenes). Das legst du dort an, es dauert ein paar Minuten. Hast du schon eins?" Buttons: „Ja, verknüpfen" / „Nein, wie geht das?" / „Lieber nicht, nur den Link nutzen".
- „Nein, wie geht das?" öffnet eine Kurzanleitung (3 Schritte, Link zu einer empfohlenen Instanz-Liste, Hinweis auf E-Mail-Bestätigung und mögliche Freischaltung).
- „Lieber nicht" führt zurück in den Link-Pfad (V-01). Das ist der wichtigste Ausstieg für Lena.
- Instanz-Auswahl: Eine Liste mit 3–5 bekannten Instanzen zum Anklicken, statt nur ein freies Domain-Feld. Das Betreiber-Allowlist-Konzept (§27) passt dazu.

**V-06 Bot-Flag in Alltagssprache und mit Empfehlung (zu PS-MAS-022, PS-UX-008).**
- Titel: „Dein Konto ist noch nicht als ‚automatisch' gekennzeichnet."
- Erklärung: „Auf Mastodon erwarten die Leute, dass Konten, die automatisch posten, als solche markiert sind. Sonst werden sie schnell gesperrt."
- Optionen, Reihenfolge so: **Empfohlen:** „Kamerplanter soll das für mich einstellen" · „Ich mache das selbst in Mastodon (Anleitung)" · „Ich poste nur selbst, ohne Automatik".
- Option (b) verlangt den Zusatz-Scope `write:accounts` und damit einen zweiten Zustimmungsschritt. Der Text dazu muss erklären, was Kamerplanter dann zusätzlich darf („Name, Beschreibung und Kennzeichnung ändern — nicht lesen, nicht folgen").

**V-07 Freigabe-Liste entlasten (zu PS-SOC-002/003, §12.2, PS-UX-006, PS-UX-032).**
- Sammel-Aktionen: „Alle freigeben" und „Alle verwerfen" bei mehr als einer Karte.
- Nach dem 10. freigegebenen Post einmalig fragen: „Das lief 10-mal gut. Soll {Name} künftig ohne Rückfrage posten?" mit den Buttons „Ja, automatisch" · „Weiter erst fragen". Das ersetzt das stille Auslaufen.
- Push „Beitrag wartet auf dein OK" (PS-UX-032) von SHOULD auf MUST, aber gebündelt: höchstens eine Nachricht pro Tag, nicht pro Karte.
- Hinweis vor Verfall: Karte zeigt „Noch 3 Tage" und ist 2 Tage vorher in der Push-Nachricht enthalten. Verfall nicht als „verworfen" darstellen, sondern als „abgelaufen" (siehe V-08).
- Beim Absenken von `review_required_until_posts` auf 0 ein Bestätigungstext mit Konsequenz (siehe F-09).
- Default für Lena: Wenn keine Verbindung existiert, entfällt die Freigabe-Liste vollständig. Offen: Der Spec (§27) sagt „`review`/`auto` steuern, ob ein Ereignis auf `/p/{slug}` erscheint". Dadurch müsste Lena auch für ihr Link-Profil Einträge freigeben. Das sollte im reinen Profil-Fall **nicht** der Default sein: Vorschlag **Standard „Gleich zeigen" nur für Fotos und Meilensteine, die Lena selbst angelegt hat** (Handlung = Zustimmung).

**V-08 Fehlertexte: pro Zustand ein Satz „Was ist passiert / Was kannst du tun" (zu §13.6, PS-UX-007).**

| Zustand (intern) | Text für Lena |
|---|---|
| `temporary_exhausted` | „Mastodon war gerade nicht erreichbar. Wir haben es mehrfach versucht. [Nochmal senden]" |
| `rate_limited` | „Zu viele Beiträge in kurzer Zeit. Wir senden später automatisch." (kein Fehlerzustand) |
| `connection_revoked` / `revoked_remote` | „Die Verknüpfung wurde in Mastodon aufgehoben. Verknüpfe das Konto neu, dann geht es weiter. [Neu verknüpfen]" |
| `account_suspended` | „Mastodon hat das Konto gesperrt. Wir senden nichts mehr. Das musst du direkt bei deiner Instanz klären. [Wie geht das?]" |
| `instance_blocked` | „Diese Mastodon-Instanz ist bei dieser Kamerplanter-Installation nicht freigegeben." |
| `media_rejected` | „Das Foto wurde abgelehnt (zu groß oder falsches Format). Wähle ein anderes oder poste ohne Foto." |
| `moderation_hold` | „Wir haben diesen Beitrag angehalten, weil er {Grund: z. B. einen Namen / einen Link} enthält. Bitte prüfe ihn." |
| `text.too_long` | „Der Text ist für diese Instanz zu lang. Kürze ihn oder nutze die kurze Fassung." |
| verfallen (`review_ttl`) | „Abgelaufen — du hast diesen Vorschlag zwei Wochen nicht bearbeitet." (nicht „verworfen") |

Alle mit Handlungs-Button. Statuschips (PS-UX-007) bleiben, aber die Beschriftung sollte „Wartet auf dein OK / Wird gesendet / Veröffentlicht / Hat nicht geklappt / Abgelaufen" lauten.

**V-09 Mobil: Ein-Tap-Pfad „Foto → Profil" (zu PS-UX-030/031, PS-SOC-012, PS-SOC-031).**
- Auf der Pflanzenseite ein Button „Foto zum Profil" → Kamera → Vorschau → „Zeigen". Kein Alt-Text-Dialog im reinen Profil-Fall: Der Alt-Text wird aus Bildunterschrift/Vorlage vorbefüllt und ist nachträglich editierbar. Die Alt-Text-Pflicht-Bestätigung bleibt für Posts an Mastodon.
- PS-UX-031 klarstellen: „Teilen" aus dem Tagebuch ist ein zusätzlicher Weg, nicht der einzige.
- Offline und schlechtes Netz: Foto bleibt lokal, Upload später (REQ-052 deckt das, im Spec erwähnen).

**V-10 Vorlagen (zu §12.4, PS-SOC-010).**
- Mindestens 3 Varianten pro Ereignistyp im Seed, nach Zufall, mit Sperre gegen direkte Wiederholung (derselbe Satz nie zweimal hintereinander).
- Kein Pflichtsatz zum Standort. Ein Ambiente-Satz höchstens bei jedem fünften Post.
- Neutraler Ton als zweites Preset schon im MVP (`minimalist`, „Neues Blatt, 34 cm."). Das ist nur ein Datensatz, kein KI-Aufwand, und deckt alle ab, die den Ich-Ton nicht wollen.
- In der Vorschau (Profil und Freigabe) steht oben: „So klingt {Name}" mit einem Beispiel und Umschalter Ich-Ton / sachlich.

### Nützlich (P3)

**V-11 Policy-Editor mit zwei Ebenen (zu PS-UX-005, §25.1).**
- Ebene 1 (Standard): drei Fragen statt 25 Zeilen: „Neues Blatt und Blüte → [Erst fragen]", „Gießen → [Wochenrückblick / Nicht erzählen]", „Alles andere → Nicht erzählen." Mit Button „Mehr einstellen".
- Ebene 2 („Erweitert"): die jetzige Tabelle, Limits, Hashtags, Content Warning, Mentions, Quiet Hours.
- Navigation: `/social` für Anfänger auf „Wartet auf dein OK" und „Mastodon-Konto" verkürzen; Identitäten-Liste und Protokoll hinter „Mehr".
- Ereignistypen ohne Zimmerpflanzen-Bezug (`harvested`, `fruit`, `sensor_threshold`, `treatment_applied`, `pest_detected`, `disease_detected`, `care_done`, `moved`) in der Anfängeransicht ausblenden.

**V-12 Privacy-Texte (zu PS-UX-003, PS-PRI-011/013).**
- PS-PRI-013 (Checkliste für Fotos) von SHOULD auf MUST, beim ersten Link/Veröffentlichen, als einmaliger Dialog, nicht als Pflicht-Checkbox-Wand: „Auf deinen Fotos können Fenster, Straßenschilder oder Personen zu sehen sein. Schau kurz drüber."
- Wortlaut ohne „Allowlist": „Das sehen andere: Name, Art, Sorte, ‚Seit 2024', deine Beschreibung, Fotos, die du zeigst. Das sehen sie nie: Wohnort, Sensorwerte, Dünger, Notizen, dein Name."
- Eigener Satz zu `unlisted`: „Den Link finden Suchmaschinen nicht. Wer ihn hat, kann ihn aber weitergeben."
- Erklärtext zu „Nur für Folgende" (O-18, `followers`-Stufe) im Alltagswort: „Nur für Leute, die {Name} auf Mastodon folgen. Auf deinem Profil-Link sieht man das nicht." Diese Stufe sollte im Anfängermodus gar nicht angeboten werden.
- Zeitpunkt der Datenschutz-Zustimmung: Der Consent `social_publishing` (PS-PRI-050) wird beim ersten Verbinden abgefragt, in Alltagssprache („Deine Beiträge werden an {Instanz} gesendet, die eigene Datenschutzregeln hat. Löschen dort klappt nur teilweise.").

**V-13 Cannabis-Sperre freundlich (zu PS-PRI-040).**
Falls eine Pflanze fälschlich als Cannabis erkannt wird (Gattungsabgleich, kein Feld), gibt es keinen Ausweg. Fehlermeldung mit Erklärung und Kontakt („Wenn das ein Irrtum ist, melde es") ergänzen.

---

## 6. Was komplett fehlt, damit es Spaß macht

1. **Ein Ergebnis mit Wiedererkennung:** Am Ende von Schritt 3 die Vorschau mit Lenas eigenem Foto und ein Teilen-Button.
2. **Ein erstes Profil ohne Eigenleistung:** Beim Anlegen wird der Verlauf rückwirkend aus Bestand gefüllt (UC-01-Backfill). Lena sollte sofort etwas sehen („Seit März 2024 · 12 Mal gegossen · 3 Fotos"), nicht eine leere Seite. Im leeren Zustand darauf hinweisen.
3. **Eine sichtbare Rückmeldung:** Ein anonymer Zähler „Dein Profil wurde 12-mal angesehen" ohne Tracking (aggregiert). Ohne Mastodon gibt es sonst nie ein Echo. Datenschutzkonformität gegen §29 prüfen.
4. **Ein Jahresrückblick light:** Ein einfacher Rückblick („{Name} wurde 2026 52-mal gegossen und hat 4 neue Blätter") wäre für Casual-Nutzer der stärkste Grund, die Funktion zu behalten, und braucht kein Mastodon.
5. **Ein Teilen-Format für Messenger:** OpenGraph-Vorschaubild für den Link. Wer einen Link in WhatsApp schickt und nur eine graue Kachel sieht, klickt ihn nicht an. Für den Link-Pfad ist das Vorschaubild kein Nice-to-have. Vorschlag: Vorschaubild für `unlisted` zulassen, wenn Lena es beim Teilen sieht und bestätigt.
6. **Nebeneinander-Vergleich:** Vorher/Nachher-Foto (UZG-001 §3.7). Mit der Timeline machbar: „Vor einem Jahr / Heute".
7. **Aufräumhilfe:** Ein Weg zurück ohne Verlust: „Profil verbergen" (reversibel) gut sichtbar. Löschen verlangt die Slug-Eingabe (PS-PI-015) und ist für Lena die falsche Hürde, wenn sie nur „nicht mehr teilen" will. Sichtbarkeit zurück auf „Nur ich" ist der einfache Weg und sollte so beschriftet sein.

---

## 7. Aufwand (Minuten) für Lena

| Tätigkeit | Aktuell geschätzt | Schmerzgrenze | Bewertung |
|---|---|---|---|
| Profil anlegen (3 Schritte, ohne Link) | 1–2 Min | 1 Min | ⚠️ |
| Link erzeugen und teilen | unklar (zweiter Durchgang, 2–3 Min) | 30 Sek | ❌ (V-01) |
| Mastodon verknüpfen inkl. Konto anlegen | 15–30 Min (extern) | nicht bereit | ❌ |
| Freigabe-Liste, 1–3 Karten/Woche | 1–2 Min | 1 Min | ⚠️ |
| Foto → Profil | 1–2 Min mit Alt-Text-Schritt | 15 Sek | ❌ (V-09) |

---

## 8. Offene Fragen an die Spec

1. Sieht Lena als Anfängerin überhaupt den Tab „Profil"? Modulkatalog sagt Default-Level `intermediate` (PS-UX-001).
2. Muss Lena im reinen Profil-Fall Einträge freigeben (§27)? Empfehlung: nein, eigene Handlungen werden direkt gezeigt (V-07).
3. Ab wann darf ein Link-Profil ohne Foto-Hinweis (PS-PRI-013) entstehen? Empfehlung: nie.
4. Wo steht der Wortlaut der Texte? Der Spec sollte wenigstens die Kernbegriffe festschreiben (V-04).

## 9. Fazit

**FAIL aus Casual-Sicht für v1.1 in der jetzigen Form.** Würde ich die Funktion nach 2 Tagen aufgeben? Ich hätte sie nie gefunden oder nie zu Ende genutzt.
**Dringendster Dealbreaker:** F-01/F-02, also fehlender „Link teilen"-Pfad und fehlender Grund, anzufangen. Mit V-01 bis V-04 wäre es ein PASS für den Link-Fall. Für den Mastodon-Fall braucht Lena zusätzlich V-05 und V-06, sonst bleibt er Julia vorbehalten.

Konkurrenz-Kontext (kurz): Planta und Greg bieten kein öffentliches Pflanzenprofil mit Fediverse-Anbindung. Der Mehrwert liegt also bei Julia. Für Lena gewinnt die Funktion nur, wenn „Link teilen" so einfach ist wie ein Foto in WhatsApp.
