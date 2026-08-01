# Auth-Bypass-Erkennung — Umsetzungsentscheidung

NFR-015 §4.2 verlangt eine Zwei-Pass-Prüfung: Jede Route, die die OpenAPI als
authentifizierungspflichtig deklariert, wird einmal mit gültigem Bearer-Token und
einmal ohne aufgerufen; aus dem Statuspaar folgt die Klassifikation. Die Spec
lässt zwei Umsetzungswege ausdrücklich offen und verlangt, dass die Wahl **hier**
festgehalten wird. Dieses Dokument ist diese Festlegung.

## Entscheidung

Umgesetzt als eigenständiger Prüfer `scripts/security/zap_auth_bypass.py`, der
vor dem ZAP-Full-Scan im Nightly läuft — nicht als zweiter `action-api-scan` mit
getrennten Context-Dateien und nicht als Active-Rule-Skript innerhalb von ZAP.

## Begründung

**Der Fehlerfall muss unterscheidbar sein.** Die vierte Zeile der Matrix in §4.2
— anonym `401`, authentifiziert `401` — bedeutet, dass das Token nicht
funktioniert. Ein Lauf in diesem Zustand hat *nichts* über Auth-Bypässe bewiesen,
darf also nicht als „keine Findings" durchgehen. Innerhalb von ZAP ist dieser
Zustand kaum von „alles korrekt geschützt" zu trennen: Beide erzeugen dieselbe
Abwesenheit von Alerts. Der eigenständige Prüfer erkennt ihn und **verwirft den
Lauf** mit einem eigenen Exit-Code. Das ist der Hauptgrund; alles andere ist
nachrangig.

**Determinismus.** Die Prüfung ist eine Schleife über deklarierte Routen mit zwei
HTTP-Aufrufen je Route. Als Skript ist sie lokal ausführbar, gegen Stub-Backends
testbar und ihr Ergebnis hängt nicht vom Spider-Verhalten oder der
Scan-Reihenfolge ab. Die drei relevanten Zustände — sauber, Bypass, kaputtes
Token — sind mit einem 25-zeiligen Stub-Server reproduzierbar und wurden vor der
Einführung so geprüft.

**Kosten.** Der Prüfer läuft in Sekunden und steht deshalb **vor** dem Full-Scan.
Ein kaputtes Token fällt damit auf, bevor Stunden in einen Scan fließen, der die
anonyme Oberfläche unter authentifiziertem Etikett vermisst.

## Grenzen — bewusst, nicht übersehen

- **Nur sichere Methoden.** Geprüft werden `GET` und `HEAD`. Ein Bypass auf einer
  Leseroute ist der Befund, auf den es ankommt; schreibende Requests mitten im
  Scan würden den Zustand verändern, den die anderen Profile vermessen. Die
  Statusklassen für `POST` aus der Matrik in §4.2 sind damit derzeit nicht
  abgedeckt.
- **Pfadparameter.** Routen mit einem Parameter, für den kein Fixture-Wert
  vorliegt, werden übersprungen. Die Anzahl wird **immer** ausgegeben und als
  Warnung markiert — eine Prüfung, die ihren eigenen Umfang still verkleinert,
  liest sich sonst wie breitere Abdeckung, als sie hatte.
- **Nur deklarierte Routen.** Was in der Implementierung existiert, aber nicht in
  der OpenAPI steht, ist per Definition unsichtbar. Das ist die eigene
  Finding-Klasse aus §4.4 und wird hier nicht mit abgedeckt.

## Verweise

- `spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md` §4.2 (Matrix), §3.4
  (Ausnahmen), §5.1 (Critical-Eskalation)
- `scripts/security/zap_auth_bypass.py`
- `.github/workflows/security-zap-nightly.yml`
