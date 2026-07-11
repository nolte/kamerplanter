"""Pure logic for REQ-025 consent management."""

from app.domain.models.privacy import ConsentPurpose, ConsentRecord


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
