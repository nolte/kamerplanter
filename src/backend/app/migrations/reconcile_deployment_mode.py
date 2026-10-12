"""Reconcile the deployment mode on every start (REQ-027 §7a, #1855).

Runs as the seed job ``deployment_mode``, after the light-mode seed, under the migration
lock. In ``full`` mode it seals the light-mode system account (deactivated, keys revoked,
sessions ended) and opens the take-over of its data on the first full-mode start; in
``light`` mode it makes the system account usable again. The work lives in
:class:`~app.domain.services.mode_switch_service.ModeSwitchService`.
"""

import structlog

from app.common.dependencies import get_mode_switch_service
from app.config.settings import settings

logger = structlog.get_logger()


def run_reconcile_deployment_mode() -> None:
    outcome = get_mode_switch_service().reconcile(settings.kamerplanter_mode)
    logger.info(
        "deployment_mode_reconciled",
        current_mode=outcome.current_mode,
        previous_mode=outcome.previous_mode,
        previous_mode_inferred=outcome.previous_mode_inferred,
        system_account_deactivated=outcome.sealing.deactivated,
        api_keys_revoked=outcome.sealing.api_keys_revoked,
        pending_takeover_recorded=outcome.pending_takeover_recorded,
        system_account_restored=outcome.system_account_restored,
    )
