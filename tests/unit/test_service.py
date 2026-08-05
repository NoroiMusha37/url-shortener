from app.service import truncate_ip


def test_truncate_ipv4() -> None:
    assert truncate_ip("192.168.1.123") == "192.168.1.0"
    assert truncate_ip("8.8.8.8") == "8.8.8.0"


def test_truncate_ipv6() -> None:
    assert truncate_ip("2001:db8:85a3::8a2e:370:7334") == "2001:db8:85a3::"


def test_truncate_ip_empty() -> None:
    assert truncate_ip("") == ""
    assert truncate_ip(None) == ""


def test_truncate_ip_invalid() -> None:
    assert truncate_ip("not-an-ip") == ""
    assert truncate_ip("192.168.1.999") == ""
