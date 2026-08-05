"""Pure logic for REQ-025 consent management."""

from app.domain.models.privacy import ConsentPurpose, ConsentRecord

#: REQ-050 §7.1 — purpose key for releasing single diary entries to the user's
#: own AI agent. Exported as a constant so the enforcement path and the
#: dependency wiring refer to the same string as the registry below.
DIARY_AI_ANALYSIS = "diary_ai_analysis"


class ConsentEngine:
    """Defines processing purposes and validates consent state changes.

    Pure-logic engine. No I/O. The ``PurposeNotFoundError`` style validation
    here keeps higher-level service code free of literal-string magic.
    """

    PURPOSES: list[ConsentPurpose] = [
        ConsentPurpose(
            key="core_functionality",
            label_de="Grundfunktionen",
            label_en="Core functionality",
            description_de=("Verarbeitung fuer den Betrieb des Systems (Pflanzenverwaltung, Phasensteuerung, etc.)."),
            description_en=("Processing required to operate the system (plant management, phase control, etc.)."),
            legal_basis="Art. 6(1)(b) GDPR — performance of contract",
            required=True,
        ),
        ConsentPurpose(
            key="error_tracking",
            label_de="Fehler-Tracking (Sentry)",
            label_en="Error tracking (Sentry)",
            description_de=("Automatische Erfassung von Fehlern zur Verbesserung der Software-Qualitaet."),
            description_en=("Automatic error capture to improve software quality."),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="hibp_check",
            label_de="Passwort-Sicherheitscheck (HaveIBeenPwned)",
            label_en="Password security check (HaveIBeenPwned)",
            description_de=("Pruefung ob Passwort in bekannten Datenlecks vorkommt (k-Anonymity, SHA-1-Praefix)."),
            description_en=("Check whether password appears in known breaches (k-anonymity, SHA-1 prefix)."),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="external_enrichment",
            label_de="Externe Stammdatenanreicherung",
            label_en="External master-data enrichment",
            description_de=("Abfrage botanischer Daten bei GBIF, Perenual und anderen externen Diensten."),
            description_en=("Querying botanical data from GBIF, Perenual and other external services."),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="plant_identification",
            label_de="KI-Pflanzenidentifikation (Bilderkennung)",
            label_en="AI plant identification (image recognition)",
            description_de=(
                "Senden hochgeladener Pflanzenfotos an Pl@ntNet zur Artbestimmung. "
                "Das Foto wird vor dem Versand von EXIF-Metadaten bereinigt und nicht dauerhaft gespeichert."
            ),
            description_en=(
                "Sending uploaded plant photos to Pl@ntNet for species identification. "
                "The photo is stripped of EXIF metadata before sending and is not persisted."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="pest_detection_cloud",
            label_de="Cloud-basierte Schädlingserkennung",
            label_en="Cloud-based pest detection",
            description_de=(
                "Senden hochgeladener Pflanzenfotos an einen Cloud-Dienst (Kindwise plant.health) "
                "zur Schädlingserkennung. Nur erforderlich, wenn der Cloud-Adapter aktiv ist — die "
                "Self-Hosted-Erkennung benötigt diese Einwilligung nicht. Das Foto wird vor dem "
                "Versand von EXIF-Metadaten bereinigt und nicht dauerhaft gespeichert."
            ),
            description_en=(
                "Sending uploaded plant photos to a cloud service (Kindwise plant.health) for pest "
                "detection. Only required when the cloud adapter is active — the self-hosted path "
                "needs no such consent. The photo is stripped of EXIF metadata before sending and "
                "is not persisted."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="ai_tenant_data_access",
            label_de="KI-Zugriff auf deine Pflanzendaten",
            label_en="AI access to your plant data",
            description_de=(
                "Erlaubt dem KI-Assistenten, Stammwerte deiner Pflanzen (Art, Phase, Substrat, "
                "EC/pH-Messwerte) als Kontext an die Wissensbasis zu senden, um personalisierte "
                "Tipps, Tipp-des-Tages, „Warum?“-Erklaerungen und Chat-Antworten zu erzeugen. "
                "Auf diesem serverseitigen Weg werden keine Namen, E-Mail-Adressen oder "
                "Freitext-Notizen uebermittelt (NFR-007). Wenn du einzelne Tagebuch-Eintraege samt "
                "Fotos ausdruecklich zur Analyse freigeben moechtest, ist das ein getrennter Weg mit "
                "eigener Einwilligung (siehe „diary_ai_analysis“, REQ-050). "
                "Jederzeit widerrufbar."
            ),
            description_en=(
                "Allows the AI assistant to send master values of your plants (species, phase, "
                "substrate, EC/pH readings) as context to the knowledge base to generate "
                "personalised tips, the tip of the day, “why?” explanations and chat answers. "
                "On this server-side path no names, e-mail addresses or free-text notes are "
                "transmitted (NFR-007). Releasing individual diary entries including photos for "
                "analysis is a separate path with its own consent (see “diary_ai_analysis”, "
                "REQ-050). Revocable at any time."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key=DIARY_AI_ANALYSIS,
            label_de="Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden",
            label_en="Individual diary entries may be analysed by my AI agent",
            description_de=(
                "Erlaubt dir, einzelne Tagebuch-Einträge samt Freitext und Fotos zur Analyse "
                "freizugeben (REQ-050). Die Analyse führt ein KI-Agent aus, den DU betreibst und der "
                "die Daten über deinen eigenen API-Schlüssel abruft — Kamerplanter selbst ruft dabei "
                "kein Sprachmodell auf. Es wird nie automatisch etwas analysiert: Jeden einzelnen "
                "Eintrag musst du selbst markieren. Übertragen werden verkleinerte Bildfassungen ohne "
                "Aufnahmeort und Gerätekennung. Ein Widerruf verhindert neue Markierungen und lässt "
                "vorhandene Ergebnisse unberührt."
            ),
            description_en=(
                "Allows you to release individual diary entries, including free text and photos, for "
                "analysis (REQ-050). The analysis is performed by an AI agent that YOU operate and "
                "that fetches the data via your own API key — Kamerplanter itself never calls a "
                "language model. Nothing is ever analysed automatically: you have to mark every "
                "single entry yourself. Only downscaled image renditions without capture location or "
                "device identifier are transmitted. Withdrawing consent prevents new markings and "
                "leaves existing results untouched."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="ai_cloud_processing",
            label_de="KI-Verarbeitung ueber Cloud-Provider",
            label_en="AI processing via cloud provider",
            description_de=(
                "Erlaubt die Verarbeitung deiner KI-Anfragen ueber einen externen Cloud-Provider "
                "(z. B. Anthropic, OpenAI) statt lokal (Ollama). Cloud-Provider koennen eine "
                "Drittland-Datenuebermittlung bedeuten. Nur erforderlich, wenn ein Cloud-Provider "
                "aktiv gewaehlt wird — der lokale Standard-Provider benoetigt diese Einwilligung "
                "nicht. Jederzeit widerrufbar."
            ),
            description_en=(
                "Allows your AI requests to be processed by an external cloud provider "
                "(e.g. Anthropic, OpenAI) instead of locally (Ollama). Cloud providers may involve "
                "a third-country data transfer. Only required when a cloud provider is actively "
                "selected — the local default provider needs no such consent. Revocable at "
                "any time."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="plant_diagnosis",
            label_de="KI-Krankheitsdiagnose (Bilderkennung)",
            label_en="AI disease diagnosis (image recognition)",
            description_de=(
                "Analyse hochgeladener Pflanzenfotos durch die self-hosted Bilderkennung zur "
                "Krankheits- und Mangel-Diagnose (REQ-038). Das Foto wird vor der Verarbeitung von "
                "EXIF-Metadaten bereinigt und nicht dauerhaft gespeichert. Das Ergebnis ist immer nur "
                "ein Verdacht — keine gesicherte Diagnose."
            ),
            description_en=(
                "Analysing uploaded plant photos with the self-hosted image recognition for disease "
                "and deficiency diagnosis (REQ-038). The photo is stripped of EXIF metadata before "
                "processing and is not persisted. The result is always a hypothesis — never a "
                "confirmed diagnosis."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
        ConsentPurpose(
            key="reference_contribution",
            label_de="Foto-Beitrag zur Pflanzenerkennung",
            label_en="Photo contribution to plant recognition",
            description_de=(
                "Optionaler Beitrag eigener Galerie-Fotos einer korrekt bestimmten Pflanze als "
                "zusaetzliche Referenz fuer die self-hosted Bilderkennung (REQ-034 §4). Es wird "
                "nur der Embedding-Vektor gespeichert — kein Bild verlaesst die Instanz; jederzeit "
                "widerrufbar."
            ),
            description_en=(
                "Optional contribution of your own gallery photos of a correctly identified plant "
                "as an additional reference for the self-hosted image recognition (REQ-034 §4). "
                "Only the embedding vector is stored — no image leaves the instance; revocable at "
                "any time."
            ),
            legal_basis="Art. 6(1)(a) GDPR — consent",
            required=False,
        ),
    ]

    def get_all_purposes(self) -> list[ConsentPurpose]:
        """Return all known processing purposes."""
        return list(self.PURPOSES)

    def find_purpose(self, key: str) -> ConsentPurpose | None:
        """Find a purpose by key, returning ``None`` if unknown."""
        for purpose in self.PURPOSES:
            if purpose.key == key:
                return purpose
        return None

    def is_known_purpose(self, key: str) -> bool:
        """Return True if the given purpose is registered."""
        return self.find_purpose(key) is not None

    def is_processing_allowed(
        self,
        purpose_key: str,
        consent: ConsentRecord | None,
    ) -> bool:
        """Decide whether processing for the given purpose is allowed."""
        purpose = self.find_purpose(purpose_key)
        if purpose is None:
            return False
        if purpose.required:
            return True
        if consent is None:
            return False
        return consent.granted

    def validate_consent_change(
        self,
        purpose_key: str,
        grant: bool,
    ) -> list[str]:
        """Validate a grant/revoke action. Returns list of human-readable errors."""
        errors: list[str] = []
        purpose = self.find_purpose(purpose_key)
        if purpose is None:
            errors.append(f"Unknown processing purpose: '{purpose_key}'.")
            return errors
        if purpose.required and not grant:
            errors.append(f"Consent for '{purpose.label_en}' is required and cannot be revoked.")
        return errors
