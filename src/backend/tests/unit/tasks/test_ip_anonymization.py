from app.tasks.auth_tasks import _anonymize_ip


class TestAnonymizeIpV4:
    def test_standard_ipv4(self):
        assert _anonymize_ip("192.168.1.42") == "192.168.1.0"

    def test_loopback(self):
        assert _anonymize_ip("127.0.0.1") == "127.0.0.0"

    def test_already_anonymized(self):
        assert _anonymize_ip("10.20.30.0") == "10.20.30.0"

    def test_all_zeros(self):
        assert _anonymize_ip("0.0.0.0") == "0.0.0.0"

    def test_max_values(self):
        assert _anonymize_ip("255.255.255.255") == "255.255.255.0"


class TestAnonymizeIpV6:
    def test_full_ipv6(self):
        result = _anonymize_ip("2001:0db8:85a3:1234:5678:8a2e:0370:7334")
        # Should zero out everything after /48 (first 3 groups kept)
        assert result == "2001:db8:85a3::"

    def test_loopback_ipv6(self):
        result = _anonymize_ip("::1")
        assert result == "::"

    def test_ipv6_short_form(self):
        result = _anonymize_ip("fe80::1")
        assert result == "fe80::"


class TestAnonymizeInvalid:
    def test_garbage_input(self):
        assert _anonymize_ip("not-an-ip") == "0.0.0.0"

    def test_empty_string(self):
        assert _anonymize_ip("") == "0.0.0.0"
