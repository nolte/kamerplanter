---
name: deploy-ha
description: "Deployed die HA-Integration in den lokalen Kubernetes-Cluster (kubectl cp + Cache-Clear + Pod-Restart), prueft die HA-Logs auf erfolgreichen Start und meldet Fehler. Nutze diesen Skill nach Aenderungen an src/ha-integration/ um die Integration schnell zu testen."
disable-model-invocation: true
---

# HA-Integration deployen und verifizieren

## Schritt 1: Pre-Flight Check

Pruefe ob der HA-Pod laeuft:

```bash
kubectl get pod homeassistant-0 -n default -o jsonpath='{.status.phase}' 2>&1; echo ""
```

Falls der Pod nicht existiert oder nicht "Running" ist, melde den Fehler und brich ab.

## Schritt 2: Lint-Check

Fuehre Ruff auf dem HA-Code aus:

```bash
cd src/ha-integration && ruff check custom_components/ 2>&1; echo "EXIT:$?"
```

```bash
cd src/ha-integration && ruff format --check custom_components/ 2>&1; echo "EXIT:$?"
```

Falls Lint-Fehler: behebe sie automatisch, dann weiter.

## Schritt 3: Deploy (3-Schritt-Verfahren)

Fuehre die folgenden 3 Befehle **sequentiell** aus:

### 3a. Dateien kopieren

```bash
kubectl cp src/ha-integration/custom_components/kamerplanter/ default/homeassistant-0:/config/custom_components/kamerplanter/ 2>&1; echo "EXIT:$?"
```

### 3b. Bytecode-Cache loeschen (PFLICHT)

```bash
kubectl exec homeassistant-0 -n default -- rm -rf /config/custom_components/kamerplanter/__pycache__ 2>&1; echo "EXIT:$?"
```

### 3c. Pod neustarten

```bash
kubectl delete pod homeassistant-0 -n default 2>&1; echo "EXIT:$?"
```

## Schritt 4: Warten auf Pod-Ready

Warte bis der Pod wieder laeuft (max 120s):

```bash
kubectl wait --for=condition=ready pod/homeassistant-0 -n default --timeout=120s 2>&1; echo "EXIT:$?"
```

## Schritt 5: Log-Verifizierung

Pruefe die HA-Logs auf Kamerplanter-bezogene Eintraege:

```bash
kubectl logs homeassistant-0 -n default --since=90s 2>&1 | grep -iE "(kamerplanter|custom_components)" | tail -30
```

Zusaetzlich pruefe auf allgemeine Fehler beim Start:

```bash
kubectl logs homeassistant-0 -n default --since=90s 2>&1 | grep -iE "(error|exception|traceback)" | grep -v "template" | tail -20
```

## Schritt 6: Ergebnis melden

Stelle das Ergebnis in folgender Form dar:

```markdown
| Schritt            | Status     | Details                        |
|--------------------|------------|--------------------------------|
| Lint               | Pass/Fail  | {details}                      |
| Copy               | Pass/Fail  | kubectl cp                     |
| Cache Clear        | Pass/Fail  | __pycache__ entfernt           |
| Pod Restart        | Pass/Fail  | homeassistant-0 deleted        |
| Pod Ready          | Pass/Fail  | {time} bis Ready               |
| Integration Loaded | Pass/Fail  | Setup-Log-Eintraege            |
| Errors             | Pass/Fail  | {n} Fehler in Logs             |
```

### Bei Fehlern:

- Zeige die relevanten Log-Zeilen an
- Analysiere ob es ein Code-Fehler, Config-Problem oder Netzwerk-Issue ist
- Schlage einen konkreten Fix vor
- Frage ob der Fix angewendet und erneut deployed werden soll

### Bei Erfolg:

- Melde "HA-Integration erfolgreich deployed und gestartet"
- Zeige die geladenen Entities/Platforms falls in den Logs sichtbar
