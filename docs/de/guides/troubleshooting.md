# Fehlerbehebung

Lösungen zu häufigen Problemen bei Betrieb und Nutzung von Kamerplanter.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

??? question "Das Backend startet nicht"
    Prüfe, ob ArangoDB und Redis laufen. Logs: `kubectl logs deployment/kamerplanter-backend`

??? question "Ernte wird blockiert (422)"
    Eine aktive IPM-Behandlung mit offener Karenzzeit verhindert die Ernte. Prüfe aktive Behandlungen unter Pflanzenschutz.

??? question "iCal-Feed zeigt keine Ereignisse"
    Stelle sicher, dass der Feed-Token gültig ist und mindestens ein Kalender-Feed konfiguriert ist.
