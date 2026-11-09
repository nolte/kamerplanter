# SPEC-13 — Rechtsevidenzregister

```
Paket: spec/privacy · Version 1.1 · 2026-11-09
Zweck: Jede rechtliche Aussage des Pakets verweist auf einen Eintrag L-nn dieses Registers.
Ein Eintrag mit Status UNVERIFIED_AT_SOURCE darf keine MUSS-Anforderung tragen; er benennt,
wie er zu verifizieren ist.
Prüfdatum aller Einträge: 2026-11-09 (Abrufumgebung: Build-Umgebung ohne Browser).
```

## 0. Quellenhierarchie und Statuswerte

Hierarchie (absteigend): (1) EUR-Lex — DSGVO und EU-Verordnungen · (2) Gesetze im Internet —
deutsche Gesetze · (3) amtliche Veröffentlichungen der EU-Kommission · (4) EDSA/EDPB-Leitlinien
und Stellungnahmen (inkl. vom EDSA bestätigte Art.-29-Gruppe) · (5) deutsche Aufsichtsbehörden
(DSK, BfDI, LfDI) · (6) Gerichtsentscheidungen (EuGH, deutsche Gerichte). Sekundärquellen
werden nicht als Beleg verwendet.

| Status | Bedeutung |
|--------|-----------|
| `VERIFIED_LEGAL` | Wortlaut am Prüfdatum aus der Primärquelle gelesen (HTML der Primärseite oder Text aus dem amtlichen PDF). |
| `VERIFIED_META` | Nur Metadaten (Titel, Datum, Version, Status) aus der Primärseite gelesen; Wortlaut nicht. |
| `UNVERIFIED_AT_SOURCE` | Primärquelle am Prüfdatum aus der Umgebung nicht abrufbar (EUR-Lex antwortete HTTP 202/leer; Curia liefert nur eine JS-Weiterleitung). Inhalt wird **nicht** aus dem Gedächtnis ergänzt; der Eintrag nennt den Verifikationsauftrag (V-nn). |
| `UNVERIFIED` | Quelle nicht gesucht oder nicht gefunden. |

Quellentyp: `Gesetz` (bindend) · `Urteil` (bindend inter partes, Auslegungswirkung) ·
`Leitlinie` (Aufsichtsbehörde, nicht bindend) · `Verwaltungsliste` (DSK-Liste nach Art. 35
Abs. 4, veröffentlicht, Bindungswirkung umstritten → als Leitlinie behandelt).

---

## 1. Deutsche Gesetze (gesetze-im-internet.de, Primärquelle)

### L-01 · PflSchG § 11 Aufzeichnungs- und Informationspflichten — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/pflschg_2012/__11.html
- Fassung: Die Seite nennt in der extrahierten Fassung kein „Stand“-Datum; der Text verweist auf die
  „Durchführungsverordnung (EU) 2023/564“ und auf den 31. Dezember 2026, ist also eine Fassung nach 2023.
  Verifikationsauftrag **V-01**: Stand/Änderungsdatum aus der Kopfzeile der Seite ergänzen.
- Wortlaut (vollständig):
  > (1) Die Aufzeichnungen nach Artikel 67 Absatz 1 Satz 1 der Verordnung (EG) Nr. 1107/2009 können elektronisch oder schriftlich geführt werden.
  > (2) Die nach Artikel 67 Absatz 1 Satz 2 der Verordnung (EG) Nr. 1107/2009 in Verbindung mit Artikel 2 der Durchführungsverordnung (EU) 2023/564 grundsätzlich elektronisch zu führenden Aufzeichnungen der beruflichen Verwender können bis zum Ablauf des 31. Dezember 2026 auch schriftlich geführt werden. Der Leiter eines landwirtschaftlichen, forstwirtschaftlichen oder gärtnerischen Betriebes ist verpflichtet, die Aufzeichnungen für die bewirtschafteten Flächen seines Betriebes unter Angabe des jeweiligen Anwenders zusammen zu führen.
  > (3) Die Fristen des Artikels 67 Absatz 1 Satz 1 oder 2 der Verordnung (EG) Nr. 1107/2009 zur Aufbewahrung der Aufzeichnungen rechnen ab dem Beginn des Jahres, das auf das Jahr des Entstehens der jeweiligen Aufzeichnung folgt.
- Im Paket verwendete Auslegung: (a) Adressat der Aufzeichnungspflicht sind die in Art. 67 VO 1107/2009
  Genannten („berufliche Verwender“, § 11 Abs. 2 S. 1); (b) der **Betriebsleiter** muss die Aufzeichnungen
  „unter Angabe des jeweiligen Anwenders“ zusammenführen → die **Identifizierbarkeit der anwendenden Person
  ist gesetzlicher Inhalt der Betriebsaufzeichnung** (Abs. 2 S. 2); (c) die Aufbewahrungsfrist beginnt **am
  1. Januar des Folgejahres** der Aufzeichnung (Abs. 3), nicht am Anwendungsdatum; (d) ab 1. Januar 2027
  grundsätzlich elektronische Führung (Abs. 2 S. 1, inhaltliche Vorgaben in DVO 2023/564 → L-04).
- Unsicherheit: Die Fristlänge selbst steht in Art. 67 VO 1107/2009 (L-03, hier nicht verifiziert); ob
  „Angabe des jeweiligen Anwenders“ den **Namen** oder eine betriebsinterne Kennung meint, ist Auslegungsfrage → LEG-04.

### L-02 · PflSchG § 2 Nr. 16 „beruflicher Anwender“ — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/pflschg_2012/__2.html
- Wortlaut: > 16. beruflicher Anwender: jede Person, die im Zuge ihrer beruflichen Tätigkeit Pflanzenschutzmittel anwendet;
  (Die Begriffsbestimmungen gelten „ergänzend zu den Begriffsbestimmungen der Artikel 2 und 3 der Verordnung (EG) Nr. 1107/2009“.)
- Auslegung: Hobby-/Privatgärten ohne berufliche Tätigkeit sind keine beruflichen Anwender; ein
  Gemeinschaftsgarten ohne Erwerbszweck in der Regel ebenfalls nicht (INFERRED; Einzelfall).

### L-05 · KCanG § 26 Dokumentations- und Berichtspflichten von Anbauvereinigungen — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/kcang/__26.html (Stand auf der Seite nicht extrahiert → **V-02**;
  § 43 KCanG sieht einen Zwischenbericht „spätestens bis zum 1. April 2026“ vor; Änderungsvorhaben werden hier nicht als geltendes Recht behandelt)
- Wortlaut Abs. 1 und Abs. 2 S. 1:
  > (1) Anbauvereinigungen haben zum Nachweis der Einhaltung der Vorgaben der §§ 18 bis 20 und 22 für die Rückverfolgbarkeit des weitergegebenen Cannabis und Vermehrungsmaterials fortlaufend folgende Angaben zu dokumentieren: 1. Name, Vorname und Anschrift jeder Person, Name und Sitz jeder Anbauvereinigung oder Name und Sitz jeder juristischen Person, von der sie Vermehrungsmaterial erhalten haben, 2. Mengen an Cannabis in Gramm und Stückzahl des Vermehrungsmaterials, die sich in oder auf ihrem befriedeten Besitztum befinden, 3. Mengen des angebauten Cannabis in Gramm, 4. Mengen des vernichteten Cannabis in Gramm und Stückzahl des vernichteten Vermehrungsmaterials, 5. Name, Vorname und Geburtsjahr jedes Mitglieds, an das Cannabis weitergegeben wurde, sowie die folgenden Angaben zu dem weitergegebenen Cannabis: a) Menge in Gramm, b) durchschnittlicher THC-Gehalt, c) Datum der Weitergabe, 6. Name, Vorname und Geburtsjahr jedes Mitglieds, an das Vermehrungsmaterial weitergegeben wurde, sowie folgende Angaben zu dem weitergegebenen Vermehrungsmaterial: a) Stückzahl des weitergegebenen Vermehrungsmaterials, b) Datum der Weitergabe und 7. Mengen in Gramm und Sorten des gemäß § 22 Absatz 3 transportierten Cannabis, Name und Vorname des jeweils den Transport durchführenden oder begleitenden Mitglieds sowie Datum, Start- und Zieladresse des jeweiligen Transports. […]
  > (2) Anbauvereinigungen haben die Aufzeichnungen der Angaben nach Absatz 1 fünf Jahre aufzubewahren und der zuständigen Behörde auf Verlangen elektronisch zu übermitteln. […]
- Auslegung: Adressat sind **ausschließlich Anbauvereinigungen**. Personenbezogene Pflichtangaben sind: Herkunft
  von Vermehrungsmaterial (Nr. 1), **Empfänger** von Cannabis/Vermehrungsmaterial (Nr. 5, 6: Name, Vorname,
  Geburtsjahr) und **Transportbegleitende** (Nr. 7). **Die Person, die geerntet oder gepflegt hat, ist keine
  Pflichtangabe.** Mengenangaben (Nr. 2–4) sind sachbezogen. Fristbeginn ist in § 26 nicht geregelt (INFERRED:
  Entstehung der Aufzeichnung; → LEG-17).

### L-06 · KCanG § 16 Abs. 3 (Selbstauskunft) — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/kcang/__16.html
- Wortlaut: > Die Selbstauskunft nach Satz 1 ist von der Anbauvereinigung drei Jahre aufzubewahren.
- Relevanz: Mitgliedschaftsnachweise der Anbauvereinigung — nicht Gegenstand von Kamerplanter (keine entsprechende Entität).

### L-07 · KCanG § 9, § 10 (privater Eigenanbau) — `VERIFIED_LEGAL`, Gesetz

- URLs: https://www.gesetze-im-internet.de/kcang/__9.html, https://www.gesetze-im-internet.de/kcang/__10.html
- Wortlaut § 9: > (1) Personen, die das 18. Lebensjahr vollendet haben, ist […] der private Eigenanbau von insgesamt nicht mehr als drei Cannabispflanzen gleichzeitig erlaubt. (2) Cannabis aus dem privaten Eigenanbau darf nicht an Dritte weitergegeben werden.
  § 10: > Cannabis und Vermehrungsmaterial sind am Wohnsitz und am gewöhnlichen Aufenthalt durch geeignete Maßnahmen und Sicherheitsvorkehrungen vor dem Zugriff durch Dritte, insbesondere Kinder und Jugendliche, zu schützen.
- Auslegung: **Keine Dokumentations- oder Aufbewahrungspflicht für den privaten Eigenanbau.** Ein persönlicher
  Mandant hat damit aus dem KCanG keine Rechtsgrundlage nach Art. 6 Abs. 1 lit. c für die Aufbewahrung von Ernteaufzeichnungen.

### L-09 · BDSG § 26 Abs. 1 S. 1 und Abs. 8 — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/bdsg_2018/__26.html
- Wortlaut Abs. 1 S. 1: > Personenbezogene Daten von Beschäftigten dürfen für Zwecke des Beschäftigungsverhältnisses verarbeitet werden, wenn dies für die Entscheidung über die Begründung eines Beschäftigungsverhältnisses oder nach Begründung des Beschäftigungsverhältnisses für dessen Durchführung oder Beendigung oder zur Ausübung oder Erfüllung der sich aus einem Gesetz oder einem Tarifvertrag, einer Betriebs- oder Dienstvereinbarung (Kollektivvereinbarung) ergebenden Rechte und Pflichten der Interessenvertretung der Beschäftigten erforderlich ist.
- Wortlaut Abs. 8: > Beschäftigte im Sinne dieses Gesetzes sind: 1. Arbeitnehmerinnen und Arbeitnehmer, einschließlich der Leiharbeitnehmerinnen und Leiharbeitnehmer im Verhältnis zum Entleiher, 2. zu ihrer Berufsbildung Beschäftigte, 3. Teilnehmerinnen und Teilnehmer an Leistungen zur Teilhabe am Arbeitsleben sowie an Abklärungen der beruflichen Eignung oder Arbeitserprobung (Rehabilitandinnen und Rehabilitanden), 4. in anerkannten Werkstätten für behinderte Menschen Beschäftigte, 5. Freiwillige, die einen Dienst nach dem Jugendfreiwilligendienstegesetz oder dem Bundesfreiwilligendienstgesetz leisten, 6. Personen, die wegen ihrer wirtschaftlichen Unselbständigkeit als arbeitnehmerähnliche Personen anzusehen sind; zu diesen gehören auch die in Heimarbeit Beschäftigten und die ihnen Gleichgestellten, 7. Beamtinnen und Beamte des Bundes, Richterinnen und Richter des Bundes, Soldatinnen und Soldaten sowie Zivildienstleistende. Bewerberinnen und Bewerber für ein Beschäftigungsverhältnis sowie Personen, deren Beschäftigungsverhältnis beendet ist, gelten als Beschäftigte.
- Auslegung: Ehrenamtliche (außer JFDG/BFDG) und Vereinsmitglieder sind **nicht** Beschäftigte i. S. d. § 26 Abs. 8
  (VERIFIED_LEGAL für den Katalog; die Einordnung „arbeitnehmerähnlich“ nach Nr. 6 ist Einzelfall → INFERRED).
  Die Anwendbarkeit des § 26 Abs. 1 nach dem EuGH-Urteil C-34/21 ist offen → L-13, LEG-05.

### L-10 · BetrVG § 87 Abs. 1 Nr. 6 — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/betrvg/__87.html
- Wortlaut: > (1) Der Betriebsrat hat, soweit eine gesetzliche oder tarifliche Regelung nicht besteht, in folgenden Angelegenheiten mitzubestimmen: […] 6. Einführung und Anwendung von technischen Einrichtungen, die dazu bestimmt sind, das Verhalten oder die Leistung der Arbeitnehmer zu überwachen;
- Auslegung: Nach ständiger Rechtsprechung des BAG genügt die objektive **Eignung** zur Überwachung
  („dazu bestimmt“ wird weit ausgelegt) — diese Rechtsprechung ist hier **nicht** aus einer Primärquelle
  verifiziert (UNVERIFIED; → **V-05**: BAG-Entscheidung zitieren, z. B. zu § 87 Abs. 1 Nr. 6). Die Pflicht trifft
  den Arbeitgeber (Mandanten), nicht den Anbieter.

### L-11 · TDDDG § 25 Abs. 1 und 2 — `VERIFIED_LEGAL`, Gesetz

- URL: https://www.gesetze-im-internet.de/ttdsg/__25.html (Verzeichnispfad weiterhin `ttdsg`; amtlicher Titel auf der Seite:
  „Gesetz über den Datenschutz und den Schutz der Privatsphäre in der Telekommunikation und bei digitalen Diensten (Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz – TDDDG)“)
- Wortlaut:
  > (1) Die Speicherung von Informationen in der Endeinrichtung des Endnutzers oder der Zugriff auf Informationen, die bereits in der Endeinrichtung gespeichert sind, sind nur zulässig, wenn der Endnutzer auf der Grundlage von klaren und umfassenden Informationen eingewilligt hat. Die Information des Endnutzers und die Einwilligung haben gemäß der Verordnung (EU) 2016/679 zu erfolgen.
  > (2) Die Einwilligung nach Absatz 1 ist nicht erforderlich, 1. wenn der alleinige Zweck der Speicherung von Informationen in der Endeinrichtung des Endnutzers oder der alleinige Zweck des Zugriffs auf bereits in der Endeinrichtung des Endnutzers gespeicherte Informationen die Durchführung der Übertragung einer Nachricht über ein öffentliches Telekommunikationsnetz ist oder 2. wenn die Speicherung von Informationen in der Endeinrichtung des Endnutzers oder der Zugriff auf bereits in der Endeinrichtung des Endnutzers gespeicherte Informationen unbedingt erforderlich ist, damit der Anbieter eines digitalen Dienstes einen vom Nutzer ausdrücklich gewünschten digitalen Dienst zur Verfügung stellen kann.
- Datum der Umbenennung TTDSG → TDDDG: auf der Seite nicht ausgewiesen (**V-03**).
- Auslegung: Zwei kumulative Voraussetzungen für die Ausnahme Nr. 2: (i) **ausdrücklich gewünschter** Dienst,
  (ii) Speicherung **unbedingt erforderlich**. Beide sind je Speicherkategorie zu prüfen (`07` §2); „ausdrücklich
  gewünscht“ spricht für ein aktives Einschalten der Offline-Funktion (DEC-29).

---

## 2. EU-Recht und EuGH — aus der Umgebung nicht abrufbar

### L-03 · VO (EG) Nr. 1107/2009 Art. 3 Nr. 25, Art. 67 Abs. 1 — `UNVERIFIED_AT_SOURCE`, Gesetz

- Versuchte URLs: EUR-Lex konsolidiert `CELEX:02009R1107-20221121` (HTTP 202, leer), ELI `eli/reg/2009/1107/2022-11-21` (HTTP 202, leer).
- Was aus verifizierten Quellen folgt: § 11 PflSchG (L-01) verweist auf „Artikel 67 Absatz 1 Satz 1“
  (Aufzeichnungen) und „Satz 2“ (elektronische Führung) sowie auf „die Fristen des Artikels 67 Absatz 1 Satz 1 oder 2“.
  Die **Fristlänge (3 Jahre) und der Inhaltskatalog (Mittel, Zeitpunkt, Dosis, Fläche, Kultur)** werden im Paket als
  `VERIFIED_SPEC` (NFR-011 R-17) geführt, **nicht** als `VERIFIED_LEGAL`.
- Verifikationsauftrag **V-04**: Wortlaut Art. 67 Abs. 1 S. 1–2 und Art. 3 Nr. 25 aus EUR-Lex (konsolidierte Fassung) ins Register übernehmen.

### L-04 · DVO (EU) 2023/564 (Inhalt und Format der Aufzeichnungen beruflicher Verwender) — `UNVERIFIED_AT_SOURCE`, Gesetz

- Existenz und Gegenstand sind über § 11 Abs. 2 PflSchG (L-01) belegt: „Artikel 2 der Durchführungsverordnung (EU) 2023/564“, „grundsätzlich elektronisch zu führende Aufzeichnungen“, Übergangsfrist für schriftliche Führung bis 31.12.2026.
- Nicht verifiziert: der Datenkatalog des Art. 2 (insbesondere, ob die **anwendende Person** als Datenelement
  vorgeschrieben ist) und der Anwendungsbeginn.
- Verifikationsauftrag **V-06**: Art. 1–2 und Geltungsbeginn aus EUR-Lex übernehmen; danach die Feldzuordnung
  in `06` §3.2 für `treatment_applications` vervollständigen. Bis dahin gilt `treatment_applications` als
  **Hilfsdokumentation**, nicht als nachgewiesen vollständige Pflichtaufzeichnung (DA-03).

### L-12 · DSGVO (VO (EU) 2016/679) — `UNVERIFIED_AT_SOURCE`, Gesetz

- Versuchte URLs: EUR-Lex HTML `CELEX:02016R0679-20160504` EN/DE (HTTP 202, 0 Zeichen), ELI `eli/reg/2016/679/oj/eng`
  (HTTP 202), OP-Portal `publication-detail/-/publication/3e485e15-11bd-11e6-ba9a-01aa75ed71a1` (nur Metadaten:
  CELEX 32016R0679, ELI reg/2016/679/oj, OJ L 119; PDF-Download nur per JavaScript).
- Betroffene Artikel im Paket: Art. 4 Nr. 5, 7, 8; Art. 5 Abs. 1 lit. b, c, e, Abs. 2; Art. 6 Abs. 1 lit. a, b, c, f,
  Abs. 4; Art. 11; Art. 12 Abs. 3; Art. 13, 14; Art. 15; Art. 17 Abs. 1, 3; Art. 19; Art. 21; Art. 25; Art. 26; Art. 28;
  Art. 30; Art. 32; Art. 35; Art. 36; Art. 88; Erwägungsgründe 26, 47, 50, 75, 91.
- Umgang im Paket: Artikel werden **als Bezug genannt**, nicht wörtlich zitiert; Auslegungen tragen den Status
  `INFERRED` oder stützen sich auf verifizierte Leitlinien (L-14…L-19). Verifikationsauftrag **V-07**: Wortlaute aus
  EUR-Lex (DE) ergänzen, sobald ein Browserzugang besteht; die Metadaten (OJ L 119, CELEX) sind `VERIFIED_META`.

### L-13 · EuGH, Urteil vom 30.03.2023, C-34/21 (ECLI:EU:C:2023:270) — `UNVERIFIED_AT_SOURCE`, Urteil

- Versuchte URLs: EUR-Lex `CELEX:62021CJ0034` (HTTP 202), curia.europa.eu `document.jsf?docid=271961` (301 → JS-Weiterleitung, 5 Zeichen).
- Im Paket getroffene Aussage: „Die fortgesetzte Berufung auf § 26 BDSG ist rechtlich unsicher“ — Status
  `INFERRED`, nicht `VERIFIED_LEGAL`. Verifikationsauftrag **V-08**: Tenor und Rn. zur Vereinbarkeit nationaler
  Vorschriften mit Art. 88 DSGVO aus Curia übernehmen; DSK-Stellungnahme (falls vorhanden) als Leitlinie ergänzen.

---

## 3. Leitlinien (amtliche PDFs, Text lokal extrahiert)

### L-14 · Art.-29-Gruppe, WP216, Stellungnahme 5/2014 zu Anonymisierungstechniken (angenommen 10.04.2014) — `VERIFIED_LEGAL` (Text), Leitlinie

- URL: https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf (PDF, Text extrahiert)
- Wortlaut (EN): > pseudonymisation is not a method of anonymisation. It merely reduces the linkability of a dataset with the original identity of a data subject, and is accordingly a useful security measure.
  > Singling out, which corresponds to the possibility to isolate some or all records which identify an individual in the dataset; Linkability, which is the ability to link, at least, two records concerning the same data subject or a group of data subjects (either in the same database or in two different databases). […]
  Tabelle 5 nennt Hashing als Pseudonymisierungsbeispiel, das „can be easily reversed“ (bei kleinem Eingaberaum).
- Status der EDSA-Bestätigung (Endorsement 1/2018): `UNVERIFIED` (edpb.europa.eu antwortete 503) → **V-09**.
- Verwendung: Begründung, dass `anon_<hash>` Pseudonymisierung ist (`04` §1) und dass Verknüpfbarkeit ein
  eigenständiges Risiko ist (DA-06).

### L-15 · EDSA, Leitlinien 01/2025 zur Pseudonymisierung, v1 (angenommen 16.01.2025, Konsultationsfassung) — `VERIFIED_LEGAL` (Text), Leitlinie (Entwurf)

- URL: https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf; Dokumentseite:
  „Public consultation closed“, nur „Guidelines 01/2025 v1“ gelistet (keine Endfassung am Prüfdatum sichtbar).
- Wortlaut (EN): > Pseudonymised data, which could be attributed to a natural person by the use of additional information, is to be considered information on an identifiable natural person, and is therefore personal. This statement also holds true if pseudonymised data and additional information are not in the hands of the same person. Even if all additional information retained by the pseudonymising controller has been erased, the pseudonymised data can be considered anonymous only if the conditions for anonymity are met.
- Verwendung: Tombstones bleiben personenbezogen, auch nach Löschung der Nutzerzeile (`04` §1, DA-06).
  Hinweis: Konsultationsfassung, keine Endfassung → nicht als abschließende Auslegung zitieren.

### L-16 · Art.-29-Gruppe, WP248 rev.01, Leitlinien zur DSFA (angenommen 04.04.2017, revidiert 04.10.2017) — `VERIFIED_LEGAL` (Text), Leitlinie

- URL: https://ec.europa.eu/newsroom/just/document.cfm?doc_id=47711 (PDF, Text extrahiert); EDSA-Endorsement 1/2018: `UNVERIFIED` (503) → V-09.
- Wortlaut (EN), neun Kriterien (Nummerierung des Dokuments): 1. Evaluation or scoring · 2. Automated-decision making with legal or similar significant effect · 3. Systematic monitoring · 4. Sensitive data or data of a highly personal nature · 5. Data processed on a large scale · 6. Matching or combining datasets · 7. Data concerning vulnerable data subjects (recital 75) · 8. Innovative use or applying new technological or organisational solutions · 9. When the processing in itself “prevents data subjects from exercising a right or using a service or a contract”.
  > Vulnerable data subjects may include children […], employees, more vulnerable segments of the population […], and in any case where an imbalance in the relationship between the position of the data subject and the controller can be identified.
  > In most cases, a data controller can consider that a processing meeting two criteria would require a DPIA to be carried out. In general, the WP29 considers that the more criteria are met by the processing, the more likely it is to present a high risk to the rights and freedoms of data subjects, and therefore to require a DPIA, regardless of the measures which the controller envisages to adopt. However, in some cases, a data controller can consider that a processing meeting only one of these criteria requires a DPIA.
  Beispiel der Leitlinie: > A company systematically monitoring its employees’ activities, including the monitoring of the employees’ work station, internet activity, etc. — Kriterien: Systematic monitoring; Data concerning vulnerable data subjects.
- Verwendung: `11` §4 — die „Zwei-Kriterien“-Aussage ist **Leitlinie** („in most cases … can consider“), kein
  Schwellenwert; die Bewertung erfolgt begründet je Kriterium.

### L-17 · DSK, „Liste der Verarbeitungstätigkeiten, für die eine DSFA durchzuführen ist“ (nicht-öffentlicher Bereich), Version 1.1 vom 17.10.2018 — `VERIFIED_LEGAL` (Text), Verwaltungsliste

- URL: https://www.datenschutzkonferenz-online.de/media/ah/20181017_ah_DSK_DSFA_Muss-Liste_Version_1.1_Deutsch.pdf (PDF, Text extrahiert; „Version 1.1 vom 17.10.2018, ersetzt die Liste vom 18.07.2018“)
- Wortlaut Nr. 8: > Umfangreiche Verarbeitung von personenbezogenen Daten über das Verhalten von Beschäftigten, die zur Bewertung ihrer Arbeitstätigkeit derart eingesetzt werden können, dass sich Rechtsfolgen für die Betroffenen ergeben oder diese Betroffenen in anderer Weise erheblich beeinträchtigt werden — Typische Einsatzfelder: Einsatz von Data-Loss-Prevention Systemen, die systematische Profile der Mitarbeiter erzeugen; Geolokalisierung von Beschäftigten.
  > 1. Diese Liste ist nicht abschließend, sondern ergänzt die in den Absätzen 1 und 3 des Artikels 35 DSGVO enthaltenen allgemeinen Regelungen.
  Nr. 1 der Liste verweist für Zusatzkriterien ausdrücklich auf „WP 248 Rev. 01“.
- Verwendung: `11` §4 — Prüfung, ob das Pflegeprotokoll mit Personenfilter/-export eine „umfangreiche“ Verarbeitung über
  das Verhalten Beschäftigter ist, die zur Bewertung eingesetzt werden **kann**.

### L-18 · EDSA, Leitlinien 07/2020 zu den Begriffen Verantwortlicher und Auftragsverarbeiter, Version 2.1 (angenommen 07.07.2021) — `VERIFIED_LEGAL` (Text), Leitlinie

- URL: https://www.edpb.europa.eu/system/files/2023-10/EDPB_guidelines_202007_controllerprocessor_final_en.pdf (PDF, Text extrahiert)
- Wortlaut (EN), Rn. 40: > “Essential means” are traditionally and inherently reserved to the controller. While non-essential means can also be determined by the processor, essential means are to be determined by the controller. “Essential means” are means that are closely linked to the purpose and the scope of the processing […]
  Rn. 54–55: > Joint participation in the determination of purposes and means implies that more than one entity have a decisive influence over whether and how the processing takes place. […] joint participation can take the form of a common decision taken by two or more entities or result from converging decisions by two or more entities regarding the purposes and essential means. […] Decisions can be considered as converging on purposes and means if they complement each other and are necessary for the processing to take place in such manner that they have a tangible impact on the determination of the purposes and means of the processing.
  Rn. 81: > As provided in Article 28(10), a processor infringes the GDPR by going beyond the controller’s instructions and starting to determine its own purposes and means of processing. The processor will be considered a controller in respect of that processing […]
- Verwendung: DA-01 (Rollenmatrix): Wer bestimmt die **wesentlichen Mittel** (welche Daten, wie lange, wer Zugriff)?
  Vom Anbieter fest vorgegebene Aufbewahrungsfristen und Sichtbarkeitsregeln sind wesentliche Mittel → Indiz für
  eigene oder gemeinsame Verantwortlichkeit des Anbieters, soweit der Mandant sie nicht konfigurieren kann.

### L-19 · EDSA, Leitlinien 01/2022 zu den Rechten der betroffenen Person — Auskunftsrecht, Version 2.1 (angenommen 28.03.2023) — `VERIFIED_LEGAL` (Text), Leitlinie

- URL: https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_202201_data_subject_rights_access_v2_en.pdf (PDF, Text extrahiert)
- Wortlaut (EN), Rn. 110: > Archived personal data needs to be distinguished from back-up data that is personal data stored solely for the purpose of restoring the data in the case of a data loss event. […] A decrease in data in the live system (e.g. erasure after the retention period of some data came to an end or following an erasure request) will in some cases only be overwritten in the back-up data at the time of the subsequent back-up. […]
  Zur Frist: > The request must be fulfilled as soon as possible and in any event within one month of receipt of the request […]
- Verwendung: DA-? Backups (`09` §6): Der EDSA erkennt an, dass Backup-Daten eine Löschung erst mit dem nächsten
  Backup-Zyklus nachvollziehen; das Paket leitet daraus **keine** Erlaubnis ab, Löschungen in Backups dauerhaft zu
  unterlassen, sondern die Pflicht, den Zyklus kurz zu halten und Löschungen nach einem Restore erneut anzuwenden (LEG-11).

### L-20 · DSK, Kurzpapier Nr. 14 Beschäftigtendatenschutz (Stand 24.09.2020) — `VERIFIED_META`, Leitlinie

- URL: https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_14.pdf (PDF, Text extrahiert; Stand 24.09.2020)
- Inhalt: behandelt § 26 BDSG; **vor** dem Urteil C-34/21 verfasst, enthält daher keine Aussage zu dessen Folgen.
  Nicht wörtlich verwendet.

### L-21 · DSK, Kurzpapier Nr. 11 Recht auf Löschung / „Recht auf Vergessenwerden“ — `VERIFIED_META`, Leitlinie

- URL: https://www.datenschutzkonferenz-online.de/media/kp/dsk_kpnr_11.pdf; Index markiert das Papier als „in Überarbeitung“.
- Befund: Der extrahierte Text enthält keine Aussage zu Backups/Sicherungskopien. **Es wurde keine autoritative
  Aussage einer deutschen Aufsichtsbehörde zur Löschung in Backups gefunden** → LEG-11 bleibt ohne Primärbeleg.

### L-22 · EDSA, Leitlinien 1/2024 zur Verarbeitung auf Grundlage von Art. 6 Abs. 1 lit. f, Version 1.0 (angenommen 09.10.2024, Konsultation geschlossen) — `VERIFIED_META`, Leitlinie (Entwurf)

- URL: https://www.edpb.europa.eu/documents/guideline/guidelines-12024-on-processing-of-personal-data-based-on-article-61f-gdpr_en (Metadaten); PDF nicht abgerufen.
- Verwendung: Die dreistufige Prüfung (berechtigtes Interesse, Erforderlichkeit, Abwägung) in `06` §4 folgt dem
  Prüfschema der Leitlinie, ohne sie wörtlich zu zitieren (`INFERRED`). Verifikationsauftrag **V-10**: Rn. zu den
  „reasonable expectations“ und zu „mitigating measures“ ergänzen.

---

## 4. Offene Verifikationsaufträge (V-nn) — Teil der Roadmap (E17)

| V | Was | Quelle | Wirkung bis zur Erledigung |
|---|-----|--------|-----------------------------|
| V-01 | Stand/Fassung PflSchG § 11 | gesetze-im-internet.de Kopfzeile | keine (Wortlaut verifiziert) |
| V-02 | Stand/Fassung KCanG, angekündigte Änderungen | gesetze-im-internet.de, BGBl. | keine; geplante Änderungen werden nicht angewendet |
| V-03 | Umbenennung TTDSG → TDDDG (Datum, Gesetz) | BGBl. 2024 | redaktionell |
| V-04 | VO 1107/2009 Art. 67 Abs. 1, Art. 3 Nr. 25 | EUR-Lex | R-17-Frist bleibt `VERIFIED_SPEC`; PRIV-412 (Fristbeginn) stützt sich allein auf § 11 Abs. 3 PflSchG |
| V-05 | BAG-Rechtsprechung zu § 87 Abs. 1 Nr. 6 („Eignung“) | bundesarbeitsgericht.de | Aussage „objektiv geeignet“ bleibt `INFERRED` |
| V-06 | DVO 2023/564 Art. 1–2, Geltungsbeginn | EUR-Lex | `treatment_applications` gilt als Hilfsdokumentation (DA-03) |
| V-07 | DSGVO-Wortlaute (DE) | EUR-Lex | Artikel nur als Bezug; keine MUSS-Anforderung stützt sich allein auf einen nicht verifizierten Wortlaut |
| V-08 | EuGH C-34/21 Tenor und Gründe | curia.europa.eu | § 26-BDSG-Aussagen bleiben `INFERRED` (LEG-05) |
| V-09 | EDSA Endorsement 1/2018 (WP216, WP248) | edpb.europa.eu | Leitlinienstatus der WP-Dokumente als „vom EDSA bestätigt“ bleibt unbelegt |
| V-10 | EDSA 1/2024 Rn. zu Erwartungen/Maßnahmen | edpb.europa.eu PDF | LIA-Schema bleibt `INFERRED` |
| V-11 | Discovery (Code, nicht Recht): trägt `quality_assessments` oder `harvests` ein Feld für den THC-Gehalt der **weitergegebenen** Charge (KCanG § 26 Abs. 1 Nr. 5 lit. b)? Existiert eine Weitergabe-Entität? | `src/backend/app/domain/models/` (grep `thc`), REQ-010/REQ-012 | `06` §3.2 Zeile Nr. 5 lit. b bleibt `[?]`; R-16 deckt das Feld nur, wenn es den Nachweis trägt; sonst fällt es aus der Pflichtmenge (DA-03) |
