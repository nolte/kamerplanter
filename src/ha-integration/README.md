# Kamerplanter Home Assistant Integration

Custom Integration für Home Assistant zur Anbindung an das Kamerplanter-Backend.

## Entwicklung: Integration in den HA-Container kopieren

```bash
kubectl exec homeassistant-0 -- mkdir -p /config/custom_components
kubectl cp src/ha-integration/custom_components/kamerplanter homeassistant-0:/config/custom_components/kamerplanter
```

Danach HA neu starten (Einstellungen > System > Neustart).
