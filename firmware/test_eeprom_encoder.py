"""Tests for eeprom-encoder.py"""
import struct
import pytest
from eeprom_encoder import build_eeprom, encode_mac, encode_usb_string, EEPROM_SIZE, SIGNATURE


def default_cfg(**overrides):
    cfg = {
        "vid": 0x0BDA,
        "pid": 0x8153,
        "mac": "02:00:5E:00:00:01",
        "self_powered": True,
        "max_power_ma": 0,
        "led_config": 0x07,
    }
    cfg.update(overrides)
    return cfg


class TestBuildEeprom:
    def test_length(self):
        data = build_eeprom(default_cfg())
        assert len(data) == EEPROM_SIZE

    def test_signature(self):
        data = build_eeprom(default_cfg())
        assert data[0x00:0x02] == SIGNATURE

    def test_vid_pid(self):
        data = build_eeprom(default_cfg(vid=0x0BDA, pid=0x8153))
        assert struct.unpack_from("<H", data, 0x02)[0] == 0x0BDA
        assert struct.unpack_from("<H", data, 0x04)[0] == 0x8153

    def test_mac(self):
        data = build_eeprom(default_cfg(mac="02:00:5E:AA:BB:CC"))
        assert data[0x06:0x0C] == bytes([0x02, 0x00, 0x5E, 0xAA, 0xBB, 0xCC])

    def test_self_powered_flags(self):
        data = build_eeprom(default_cfg(self_powered=True))
        assert data[0x0E] == 0x00          # MaxPower = 0
        assert data[0x0F] & 0x20           # self-powered bit set

    def test_bus_powered_flags(self):
        data = build_eeprom(default_cfg(self_powered=False, max_power_ma=100))
        assert data[0x0E] == 50            # 100 mA / 2
        assert not (data[0x0F] & 0x20)    # self-powered bit clear

    def test_led_config(self):
        data = build_eeprom(default_cfg(led_config=0x03))
        assert data[0x10] == 0x03

    def test_reserved_bytes_are_ff(self):
        data = build_eeprom(default_cfg())
        assert all(b == 0xFF for b in data[0x11:0x20])

    def test_string_descriptors_written(self):
        data = build_eeprom(default_cfg(manufacturer="Test"))
        # descriptor at 0x20: length byte, 0x03, then UTF-16LE
        assert data[0x21] == 0x03
        assert data[0x22:0x2A] == "Test".encode("utf-16-le")

    def test_no_strings_leaves_region_ff(self):
        data = build_eeprom(default_cfg())
        assert all(b == 0xFF for b in data[0x20:])

    def test_vid_out_of_range(self):
        with pytest.raises(ValueError, match="VID"):
            build_eeprom(default_cfg(vid=0x00000))

    def test_vid_overflow(self):
        with pytest.raises(ValueError, match="VID"):
            build_eeprom(default_cfg(vid=0x1FFFF))

    def test_string_overflow(self):
        with pytest.raises(ValueError, match="overflows"):
            build_eeprom(default_cfg(manufacturer="A" * 60, product="B" * 60))


class TestEncodeMac:
    def test_valid(self):
        assert encode_mac("02:00:5E:AA:BB:CC") == bytes([0x02, 0x00, 0x5E, 0xAA, 0xBB, 0xCC])

    def test_wrong_octet_count(self):
        with pytest.raises(ValueError, match="6 octets"):
            encode_mac("02:00:5E:AA:BB")

    def test_invalid_hex_octet(self):
        with pytest.raises(ValueError, match="octet 3"):
            encode_mac("02:00:5E:GG:BB:CC")

    def test_uppercase_and_lowercase(self):
        assert encode_mac("ff:FF:00:aa:AA:0b") == bytes([0xFF, 0xFF, 0x00, 0xAA, 0xAA, 0x0B])


class TestEncodeUsbString:
    def test_length_byte(self):
        encoded = encode_usb_string("Hi")
        # 2 header bytes + 2 chars × 2 bytes each = 6 total
        assert encoded[0] == 6
        assert encoded[1] == 0x03

    def test_utf16le_content(self):
        encoded = encode_usb_string("AB")
        assert encoded[2:] == b"A\x00B\x00"

    def test_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            encode_usb_string("X" * 128)
