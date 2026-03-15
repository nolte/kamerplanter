# Growth Phases

Kamerplanter guides each plant through defined growth phases: Germination, Seedling, Vegetative, Flowering, Harvest. Each phase has distinct VPD (Vapor Pressure Deficit) targets, photoperiod settings, and NPK profiles.

!!! note "Placeholder"
    This content will be elaborated in a subsequent step.

## Phase Overview

```mermaid
stateDiagram-v2
    [*] --> Germination
    Germination --> Seedling : Cotyledon visible
    Seedling --> Vegetative : First true leaf
    Vegetative --> Flowering : Photoperiod change
    Flowering --> Harvest : Maturity reached
    Harvest --> [*]
```

## See Also

- [Master Data](plant-management.md)
- [Fertilization](fertilization.md)
