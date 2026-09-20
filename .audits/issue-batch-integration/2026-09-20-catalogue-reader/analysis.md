# Gruppe 2026-09-20-catalogue-reader

**Transientes Artefakt.** Vor dem Bündel-PR mit `git rm -r` entfernen.

## Frage dieser Research-Phase
Warum erreicht ein Katalogleser seinen Katalog nicht vollständig, warum trägt er keinen Fehler- und Ladezustand, und warum sieht der Seed-Wächter beides nicht?

## Die eine logische Änderung
Jeder Katalogleser der Anwendung bezieht seinen Katalog vollständig über den gemeinsamen Loader und meldet ausstehend, fehlgeschlagen und leer getrennt, und der Seed-Seitengrößen-Wächter wird von „der Listenansicht" auf „jedes Modul, das diesen Katalog liest" erweitert.

## Aufnahmeprädikat
| Issue | Prädikat | Beleg |
|---|---|---|
| #1568 | geteilte Berührungsfläche | `WorkflowDetailPage.tsx` und `SpeciesCreateDialog.tsx` sind zugleich die Reparaturvorlage von #1560 und die Fundstellen 1+2 von #1568; #1568 nennt die Store-Konsolidierung selbst und verweist auf #1560 |
| #1560 | geteilte Fläche + Abhängigkeitskette | `scripts/check_seed_catalogue_page_size.py` bindet je Katalog EIN `owner`-Modul (die Store-Slice); die Picker bauen deren Ladelogik lokal nach — dieselbe Duplikation, die #1568 als Zustandslücke sichtbar macht |

## Clusterart
**Symptom-Cluster**, eine Grundursache: der Picker baut die Ladelogik der Slice lokal nach. Deshalb erreicht er den Katalog nicht vollständig (#1560), deshalb trägt er keinen Status (#1568), und deshalb ist der Ein-Owner-Wächter blind. **Der Plan adressiert die Ursache** — Picker an Slice oder gemeinsamen Hook — nicht 19 Aufrufstellen einzeln.

## Modus und Reihenfolge
**Modus B**: #1568 ändert sichtbares Verhalten und braucht einen UI-Review, der es ablehnen kann; #1560 braucht das nicht und muss ohne #1568 mergen können.
Reihenfolge: **#1568** (legt den Drei-Zustands-Vertrag und die Konsolidierung an zwei Seiten fest) → **#1560** (rollt dieselbe Form auf die übrigen Aufrufstellen aus und erweitert ERST DANN den Wächter — sonst prüft er eine Form, die noch nicht existiert).
**Stufe 2**: kein veröffentlichter Vertrag, keine Datenänderung. Neue i18n-Schlüssel in DE und EN sind keiner.

## Vollständigkeitsmatrix
| Posten | Produktionscode | Test rot zuerst | Guard | i18n | UI-Review |
|---|---|---|---|---|---|
| #1568 Fehler- und Ladezustand | beide Seiten bekommen ausstehend/fehlgeschlagen/leer getrennt; verschluckter Fehler weg; Ignore-Guard im Effekt | Fehlerfall zeigt NICHT dieselbe Meldung wie ein leerer Katalog | not applicable — der Vertrag ist der Test | neue Schlüssel DE+EN | **erforderlich**, sichtbares Verhalten |
| #1560 vollständige Reichweite | die Aufrufstellen mit explizitem Deckel auf den vollständigen Loader | ein Katalog über dem Deckel liefert die letzte Zeile | Wächter sieht jedes lesende Modul, nicht nur den Store | not applicable | nicht erforderlich |
| Klassen-Sweep | — | — | Prädikat im Guard-Docstring | — | — |

## Risiken
- **Der Wächter ist heute GRÜN, während der Defekt live ist**: 207 Arten gegen Deckel 200, acht abschneidende Aufrufstellen, Rückgabewert 0. Die Gruppe darf nicht schließen, bevor der erweiterte Wächter gegen genau diesen Zustand **rot** wird. Das ist die Abnahmebedingung, nicht eine Formalie.
- Jede umgestellte Stelle zahlt eine zusätzliche sequentielle Anfrage je Seite; der Ladezustand muss die ganze Sequenz abdecken, nicht nur die erste Anfrage.
- Der Aktivitätendialog rendert unvirtualisiert; der frühere Deckel war eine versehentliche Renderschranke.

## Außerhalb des Scopes
Virtualisierung der Listen (#1568 Punkt 3) — eigener Posten, falls die Zeilenzahl es verlangt. Die vier Aufrufstellen mit großzügigerem Deckel, die heute korrekt sind.

## Offene Fragen
Keine.
