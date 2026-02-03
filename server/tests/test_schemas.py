"""Unit tests for Pydantic schemas validation"""

import pytest
from pydantic import ValidationError

from server.schemas import (
    PlugCreate,
    PlugRemove,
    PlugUpdate,
    ServerCreate,
    ServerUpdate,
    ServerRemove,
    PowerAction,
    ElectricityPrice,
)


class TestPlugCreate:
    """Tests for PlugCreate schema"""

    def test_valid_plug(self):
        plug = PlugCreate(name="myplug", ip="192.168.1.100")
        assert plug.name == "myplug"
        assert plug.ip == "192.168.1.100"

    def test_strips_whitespace(self):
        plug = PlugCreate(name="  myplug  ", ip="  192.168.1.100  ")
        assert plug.name == "myplug"
        assert plug.ip == "192.168.1.100"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="", ip="192.168.1.100")
        assert "Plug name cannot be empty" in str(exc.value)

    def test_empty_ip_raises(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="myplug", ip="")
        assert "IP address cannot be empty" in str(exc.value)

    def test_invalid_ip_raises(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="myplug", ip="999.999.999.999")
        assert "Invalid IP address" in str(exc.value)

    def test_name_too_long(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="a" * 100, ip="192.168.1.100")
        assert "too long" in str(exc.value)

    def test_name_with_special_chars(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="plug@name", ip="192.168.1.100")
        assert "must start with alphanumeric" in str(exc.value)

    def test_name_starting_with_hyphen(self):
        with pytest.raises(ValidationError) as exc:
            PlugCreate(name="-myplug", ip="192.168.1.100")
        assert "must start with alphanumeric" in str(exc.value)

    def test_valid_name_with_hyphen_underscore(self):
        plug = PlugCreate(name="my-plug_1", ip="192.168.1.100")
        assert plug.name == "my-plug_1"


class TestPlugRemove:
    """Tests for PlugRemove schema"""

    def test_valid_removal(self):
        plug = PlugRemove(name="myplug")
        assert plug.name == "myplug"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            PlugRemove(name="")
        assert "cannot be empty" in str(exc.value)


class TestPlugUpdate:
    """Tests for PlugUpdate schema"""

    def test_valid_update(self):
        plug = PlugUpdate(name="myplug", ip="192.168.1.200")
        assert plug.name == "myplug"
        assert plug.ip == "192.168.1.200"

    def test_invalid_ip_raises(self):
        with pytest.raises(ValidationError) as exc:
            PlugUpdate(name="myplug", ip="not-an-ip")
        assert "Invalid IP address" in str(exc.value)


class TestServerCreate:
    """Tests for ServerCreate schema"""

    def test_valid_server(self):
        server = ServerCreate(
            name="myserver",
            hostname="server.local",
            mac="AA:BB:CC:DD:EE:FF",
            plug="myplug",
        )
        assert server.name == "myserver"
        assert server.hostname == "server.local"
        assert server.mac == "AA:BB:CC:DD:EE:FF"
        assert server.plug == "myplug"

    def test_minimal_server(self):
        server = ServerCreate(name="myserver", hostname="server.local")
        assert server.name == "myserver"
        assert server.hostname == "server.local"
        assert server.mac is None
        assert server.plug is None

    def test_hostname_normalized_lowercase(self):
        server = ServerCreate(name="myserver", hostname="SERVER.LOCAL")
        assert server.hostname == "server.local"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="", hostname="server.local")
        assert "Server name cannot be empty" in str(exc.value)

    def test_empty_hostname_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="myserver", hostname="")
        assert "Hostname cannot be empty" in str(exc.value)

    def test_invalid_hostname_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="myserver", hostname="-invalid")
        assert "Invalid hostname format" in str(exc.value)

    def test_hostname_too_long(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="myserver", hostname="a" * 300)
        assert "too long" in str(exc.value)

    def test_valid_mac_formats(self):
        # Colon-separated uppercase
        server1 = ServerCreate(name="s1", hostname="h1", mac="AA:BB:CC:DD:EE:FF")
        assert server1.mac == "AA:BB:CC:DD:EE:FF"

        # Hyphen-separated lowercase (normalized to colon-separated uppercase)
        server2 = ServerCreate(name="s2", hostname="h2", mac="aa-bb-cc-dd-ee-ff")
        assert server2.mac == "AA:BB:CC:DD:EE:FF"

    def test_invalid_mac_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="myserver", hostname="server.local", mac="invalid")
        assert "Invalid MAC address" in str(exc.value)

    def test_name_too_long(self):
        with pytest.raises(ValidationError) as exc:
            ServerCreate(name="a" * 100, hostname="server.local")
        assert "too long" in str(exc.value)


class TestServerUpdate:
    """Tests for ServerUpdate schema"""

    def test_valid_update(self):
        server = ServerUpdate(name="myserver", hostname="new.local")
        assert server.name == "myserver"
        assert server.hostname == "new.local"

    def test_partial_update(self):
        server = ServerUpdate(name="myserver", mac="11:22:33:44:55:66")
        assert server.name == "myserver"
        assert server.hostname is None
        assert server.mac == "11:22:33:44:55:66"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerUpdate(name="")
        assert "cannot be empty" in str(exc.value)


class TestServerRemove:
    """Tests for ServerRemove schema"""

    def test_valid_removal(self):
        server = ServerRemove(name="myserver")
        assert server.name == "myserver"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ServerRemove(name="")
        assert "cannot be empty" in str(exc.value)


class TestPowerAction:
    """Tests for PowerAction schema"""

    def test_valid_action(self):
        action = PowerAction(name="myserver")
        assert action.name == "myserver"

    def test_strips_whitespace(self):
        action = PowerAction(name="  myserver  ")
        assert action.name == "myserver"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            PowerAction(name="")
        assert "cannot be empty" in str(exc.value)


class TestElectricityPrice:
    """Tests for ElectricityPrice schema"""

    def test_valid_price(self):
        price = ElectricityPrice(price=0.25)
        assert price.price == 0.25

    def test_zero_price(self):
        price = ElectricityPrice(price=0)
        assert price.price == 0

    def test_max_price(self):
        price = ElectricityPrice(price=10)
        assert price.price == 10

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError) as exc:
            ElectricityPrice(price=-0.1)
        assert "cannot be negative" in str(exc.value)

    def test_too_high_price_raises(self):
        with pytest.raises(ValidationError) as exc:
            ElectricityPrice(price=100)
        assert "unreasonably high" in str(exc.value)

    def test_decimal_precision(self):
        price = ElectricityPrice(price=0.123456)
        assert price.price == 0.123456
