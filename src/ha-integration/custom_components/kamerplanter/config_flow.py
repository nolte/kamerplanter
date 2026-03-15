"""Config flow for the Kamerplanter integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    KamerplanterApi,
    KamerplanterAuthError,
    KamerplanterConnectionError,
)
from .const import (
    CONF_API_KEY,
    CONF_LIGHT_MODE,
    CONF_POLL_ALERTS,
    CONF_POLL_LOCATIONS,
    CONF_POLL_PLANTS,
    CONF_POLL_TASKS,
    CONF_TENANT_SLUG,
    DEFAULT_POLL_ALERTS,
    DEFAULT_POLL_LOCATIONS,
    DEFAULT_POLL_PLANTS,
    DEFAULT_POLL_TASKS,
    DOMAIN,
    MIN_POLL_ALERTS,
    MIN_POLL_LOCATIONS,
    MIN_POLL_PLANTS,
    MIN_POLL_TASKS,
)

_LOGGER = logging.getLogger(__name__)

STEP_URL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="http://localhost:8000"): str,
    }
)

STEP_AUTH_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_API_KEY): str,
    }
)


class KamerplanterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kamerplanter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._base_url: str = ""
        self._api_key: str | None = None
        self._light_mode: bool = False
        self._server_version: str = ""
        self._tenants: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Enter Kamerplanter URL."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._base_url = user_input[CONF_URL].rstrip("/")
            session = async_get_clientsession(self.hass)
            api = KamerplanterApi(base_url=self._base_url, session=session)

            try:
                health = await api.async_get_health()
                self._server_version = health.get("version", "unknown")
                server_mode = health.get("mode", "full")
                self._light_mode = server_mode == "light"
            except KamerplanterConnectionError:
                errors["base"] = "cannot_connect"
            else:
                if self._light_mode:
                    # Light mode: no auth needed, skip to creating entry
                    return self._create_entry()
                return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_URL_SCHEMA,
            errors=errors,
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Configure authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._api_key = user_input.get(CONF_API_KEY)
            session = async_get_clientsession(self.hass)
            api = KamerplanterApi(
                base_url=self._base_url,
                session=session,
                api_key=self._api_key,
            )

            try:
                await api.async_get_current_user()
            except KamerplanterAuthError:
                errors["base"] = "invalid_auth"
            except KamerplanterConnectionError:
                errors["base"] = "cannot_connect"
            else:
                # Fetch tenants for next step
                try:
                    self._tenants = await api.async_get_tenants()
                except KamerplanterConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    if len(self._tenants) <= 1:
                        # Single tenant or no tenants, skip tenant selection
                        return self._create_entry(
                            tenant_slug=self._tenants[0]["slug"] if self._tenants else None
                        )
                    return await self.async_step_tenant()

        return self.async_show_form(
            step_id="auth",
            data_schema=STEP_AUTH_SCHEMA,
            errors=errors,
        )

    async def async_step_tenant(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3: Select tenant."""
        if user_input is not None:
            return self._create_entry(tenant_slug=user_input[CONF_TENANT_SLUG])

        tenant_options = {t["slug"]: t["name"] for t in self._tenants}
        schema = vol.Schema(
            {
                vol.Required(CONF_TENANT_SLUG): vol.In(tenant_options),
            }
        )
        return self.async_show_form(step_id="tenant", data_schema=schema)

    def _create_entry(self, tenant_slug: str | None = None) -> ConfigFlowResult:
        title = "Kamerplanter"
        if tenant_slug:
            title = f"Kamerplanter ({tenant_slug})"

        data: dict[str, Any] = {
            CONF_URL: self._base_url,
            CONF_LIGHT_MODE: self._light_mode,
        }
        if self._api_key:
            data[CONF_API_KEY] = self._api_key
        if tenant_slug:
            data[CONF_TENANT_SLUG] = tenant_slug

        return self.async_create_entry(title=title, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigFlow) -> KamerplanterOptionsFlow:
        """Get the options flow handler."""
        return KamerplanterOptionsFlow()


class KamerplanterOptionsFlow(OptionsFlow):
    """Handle Kamerplanter options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage polling interval options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POLL_PLANTS,
                    default=options.get(CONF_POLL_PLANTS, DEFAULT_POLL_PLANTS),
                ): vol.All(int, vol.Range(min=MIN_POLL_PLANTS)),
                vol.Optional(
                    CONF_POLL_LOCATIONS,
                    default=options.get(CONF_POLL_LOCATIONS, DEFAULT_POLL_LOCATIONS),
                ): vol.All(int, vol.Range(min=MIN_POLL_LOCATIONS)),
                vol.Optional(
                    CONF_POLL_ALERTS,
                    default=options.get(CONF_POLL_ALERTS, DEFAULT_POLL_ALERTS),
                ): vol.All(int, vol.Range(min=MIN_POLL_ALERTS)),
                vol.Optional(
                    CONF_POLL_TASKS,
                    default=options.get(CONF_POLL_TASKS, DEFAULT_POLL_TASKS),
                ): vol.All(int, vol.Range(min=MIN_POLL_TASKS)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
