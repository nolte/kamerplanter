"""Tests for mDNS/Zeroconf service announcement."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from zeroconf import ServiceInfo

from app.common.mdns import (
    MDNS_SERVICE_TYPE,
    MdnsAnnouncer,
    create_service_info,
    generate_instance_id,
)


class TestGenerateInstanceId:
    def test_format(self) -> None:
        iid = generate_instance_id()
        assert iid.startswith("kp-")
        assert len(iid) == 11  # "kp-" + 8 hex chars

    def test_uniqueness(self) -> None:
        ids = {generate_instance_id() for _ in range(100)}
        assert len(ids) == 100


class TestCreateServiceInfo:
    def test_required_txt_records(self) -> None:
        info = create_service_info(
            port=8000,
            version="1.0.0",
            mode="full",
            instance_id="kp-abc123",
        )
        assert isinstance(info, ServiceInfo)
        assert info.type == MDNS_SERVICE_TYPE
        assert info.port == 8000

        props = info.properties
        assert props[b"version"] == b"1.0.0"
        assert props[b"mode"] == b"full"
        assert props[b"api_path"] == b"/api"
        assert props[b"instance_id"] == b"kp-abc123"

    def test_optional_tenant(self) -> None:
        info = create_service_info(
            port=8000,
            version="1.0.0",
            mode="full",
            instance_id="kp-abc123",
            tenant="my-garden",
        )
        assert info.properties[b"tenant"] == b"my-garden"

    def test_no_tenant_when_omitted(self) -> None:
        info = create_service_info(
            port=8000,
            version="1.0.0",
            mode="light",
            instance_id="kp-abc123",
        )
        assert b"tenant" not in info.properties

    def test_custom_api_path(self) -> None:
        info = create_service_info(
            port=8000,
            version="1.0.0",
            mode="full",
            api_path="/custom/api",
            instance_id="kp-abc123",
        )
        assert info.properties[b"api_path"] == b"/custom/api"

    def test_light_mode(self) -> None:
        info = create_service_info(
            port=8000,
            version="1.0.0",
            mode="light",
            instance_id="kp-abc123",
        )
        assert info.properties[b"mode"] == b"light"


class TestMdnsAnnouncer:
    @patch("app.common.mdns.Zeroconf")
    def test_start_registers_service(self, mock_zc_cls: MagicMock) -> None:
        mock_zc = mock_zc_cls.return_value
        info = create_service_info(port=8000, version="1.0.0", mode="full", instance_id="kp-test")
        announcer = MdnsAnnouncer(info)
        announcer.start()

        mock_zc_cls.assert_called_once()
        mock_zc.register_service.assert_called_once_with(info)

    @patch("app.common.mdns.Zeroconf")
    def test_stop_unregisters_and_closes(self, mock_zc_cls: MagicMock) -> None:
        mock_zc = mock_zc_cls.return_value
        info = create_service_info(port=8000, version="1.0.0", mode="full", instance_id="kp-test")
        announcer = MdnsAnnouncer(info)
        announcer.start()
        announcer.stop()

        mock_zc.unregister_service.assert_called_once_with(info)
        mock_zc.close.assert_called_once()

    @patch("app.common.mdns.Zeroconf")
    def test_stop_without_start_is_noop(self, mock_zc_cls: MagicMock) -> None:
        info = create_service_info(port=8000, version="1.0.0", mode="full", instance_id="kp-test")
        announcer = MdnsAnnouncer(info)
        announcer.stop()  # Should not raise

        mock_zc_cls.assert_not_called()

    @patch("app.common.mdns.Zeroconf")
    def test_stop_clears_zeroconf_reference(self, mock_zc_cls: MagicMock) -> None:
        info = create_service_info(port=8000, version="1.0.0", mode="full", instance_id="kp-test")
        announcer = MdnsAnnouncer(info)
        announcer.start()
        announcer.stop()

        assert announcer._zeroconf is None
