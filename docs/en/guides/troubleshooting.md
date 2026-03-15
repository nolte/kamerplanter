# Troubleshooting

Solutions to common problems when operating and using Kamerplanter.

!!! note "Placeholder"
    This content will be elaborated in a subsequent step.

??? question "Backend does not start"
    Check that ArangoDB and Redis are running. Logs: `kubectl logs deployment/kamerplanter-backend`

??? question "Harvest is blocked (422)"
    An active IPM treatment with an open pre-harvest interval is preventing the harvest. Check active treatments under Pest Management.
