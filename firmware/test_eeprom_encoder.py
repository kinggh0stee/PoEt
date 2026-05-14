"""Tests for eeprom_encoder.py"""
import hashlib
import struct
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import eeprom_encoder
from eeprom_encoder import (
    EEPROM_SIZE,
    SIGNATURE,
    build_eeprom,
    encode_mac,
    encode_usb_string,
)


HERE = Path(__file__).parent
DEFAULT_YAML = HERE / "eeprom-default.yaml"
GOLDEN_BIN = HERE / "eeprom-default.golden.bin"
ENCODER = HERE / "eeprom_encoder.py"


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

    def test_bcd_device(self):
        # bcdDevice = 0x0300, little-endian → 00 30
        data = build_eeprom(default_cfg())
        assert data[0x0C] == 0x00
        assert data[0x0D] == 0x30

    def test_self_powered_flags(self):
        data = build_eeprom(default_cfg(self_powered=True))
        assert data[0x0E] == 0x00          # MaxPower = 0
        assert data[0x0F] & 0x20           # self-powered bit set

    def test_bus_powered_flags(self):
        data = build_eeprom(default_cfg(self_powered=False, max_power_ma=100))
        assert data[0x0E] == 50            # 100 mA / 2
        assert not (data[0x0F] & 0x20)     # self-powered bit clear

    def test_bus_powered_floor(self):
        # max(1, 0 // 2) → 1, never report 0 mA when bus-powered
        data = build_eeprom(default_cfg(self_powered=False, max_power_ma=0))
        assert data[0x0E] == 1

    def test_bus_powered_max(self):
        # 510 mA is the largest value that fits in a byte × 2 unit
        data = build_eeprom(default_cfg(self_powered=False, max_power_ma=510))
        assert data[0x0E] == 0xFF

    def test_led_config(self):
        data = build_eeprom(default_cfg(led_config=0x03))
        assert data[0x10] == 0x03

    def test_reserved_bytes_are_ff(self):
        data = build_eeprom(default_cfg())
        assert all(b == 0xFF for b in data[0x11:0x20])

    def test_string_descriptors_written(self):
        data = build_eeprom(default_cfg(manufacturer="Test"))
        # descriptor at 0x20: length byte, 0x03, then UTF-16LE
        assert data[0x20] == 2 + len("Test") * 2  # 10
        assert data[0x21] == 0x03
        assert data[0x22:0x2A] == "Test".encode("utf-16-le")

    def test_string_descriptors_stack_in_order(self):
        # manufacturer + product + serial laid out back-to-back from 0x20
        data = build_eeprom(default_cfg(manufacturer="A", product="BB", serial="CCC"))
        # manufacturer "A": header 2 + 2 = 4 bytes at 0x20
        assert data[0x20] == 4
        assert data[0x21] == 0x03
        assert data[0x22:0x24] == "A".encode("utf-16-le")
        # product "BB": 2 + 4 = 6 bytes at 0x24
        assert data[0x24] == 6
        assert data[0x25] == 0x03
        assert data[0x26:0x2A] == "BB".encode("utf-16-le")
        # serial "CCC": 2 + 6 = 8 bytes at 0x2A
        assert data[0x2A] == 8
        assert data[0x2B] == 0x03
        assert data[0x2C:0x32] == "CCC".encode("utf-16-le")
        # remainder still erased
        assert all(b == 0xFF for b in data[0x32:])

    def test_empty_string_skipped(self):
        # falsy values shouldn't emit a descriptor
        data = build_eeprom(default_cfg(manufacturer="", product="", serial=""))
        assert all(b == 0xFF for b in data[0x20:])

    def test_unicode_string(self):
        # Accented char: a single UTF-16 code unit
        data = build_eeprom(default_cfg(manufacturer="café"))
        encoded = "café".encode("utf-16-le")
        assert data[0x20] == 2 + len(encoded)  # 10
        assert data[0x22:0x22 + len(encoded)] == encoded

    def test_no_strings_leaves_region_ff(self):
        data = build_eeprom(default_cfg())
        assert all(b == 0xFF for b in data[0x20:])

    def test_vid_out_of_range(self):
        with pytest.raises(ValueError, match="VID"):
            build_eeprom(default_cfg(vid=0x00000))

    def test_vid_overflow(self):
        with pytest.raises(ValueError, match="VID"):
            build_eeprom(default_cfg(vid=0x1FFFF))

    def test_vid_non_integer(self):
        with pytest.raises(ValueError, match="'vid' must be an integer"):
            build_eeprom(default_cfg(vid="oops"))

    def test_pid_non_integer(self):
        with pytest.raises(ValueError, match="'pid' must be an integer"):
            build_eeprom(default_cfg(pid="oops"))

    def test_pid_overflow(self):
        with pytest.raises(ValueError, match="PID"):
            build_eeprom(default_cfg(pid=0x10000))

    def test_string_overflow(self):
        with pytest.raises(ValueError, match="overflows"):
            build_eeprom(default_cfg(manufacturer="A" * 60, product="B" * 60))

    def test_max_power_negative(self):
        with pytest.raises(ValueError, match="non-negative"):
            build_eeprom(default_cfg(self_powered=False, max_power_ma=-1))

    def test_max_power_overflow(self):
        with pytest.raises(ValueError, match="510"):
            build_eeprom(default_cfg(self_powered=False, max_power_ma=600))

    def test_max_power_non_integer(self):
        with pytest.raises(ValueError, match="'max_power_ma' must be an integer"):
            build_eeprom(default_cfg(max_power_ma="oops"))

    def test_led_config_overflow(self):
        with pytest.raises(ValueError, match="led_config"):
            build_eeprom(default_cfg(led_config=0x100))

    def test_led_config_non_integer(self):
        with pytest.raises(ValueError, match="'led_config' must be an integer"):
            build_eeprom(default_cfg(led_config="oops"))


class TestDefaults:
    """build_eeprom with missing keys must apply documented defaults."""

    def test_empty_cfg(self):
        data = build_eeprom({})
        assert len(data) == EEPROM_SIZE
        assert data[0x00:0x02] == SIGNATURE
        assert struct.unpack_from("<H", data, 0x02)[0] == 0x0BDA      # default VID
        assert struct.unpack_from("<H", data, 0x04)[0] == 0x8153      # default PID
        assert data[0x06:0x0C] == bytes([0x02, 0x00, 0x5E, 0x00, 0x00, 0x01])
        assert data[0x0E] == 0x00                                     # self-powered → 0
        assert data[0x0F] & 0x20                                      # self-powered bit set
        assert data[0x10] == 0x07                                     # default LED config
        assert all(b == 0xFF for b in data[0x20:])                    # no strings

    def test_only_mac_overridden(self):
        data = build_eeprom({"mac": "02:00:5E:DE:AD:BE"})
        assert data[0x06:0x0C] == bytes([0x02, 0x00, 0x5E, 0xDE, 0xAD, 0xBE])
        # everything else still default
        assert struct.unpack_from("<H", data, 0x02)[0] == 0x0BDA


class TestEncodeMac:
    def test_valid(self):
        assert encode_mac("02:00:5E:AA:BB:CC") == bytes([0x02, 0x00, 0x5E, 0xAA, 0xBB, 0xCC])

    def test_wrong_octet_count(self):
        with pytest.raises(ValueError, match="6 octets"):
            encode_mac("02:00:5E:AA:BB")

    def test_invalid_hex_octet(self):
        with pytest.raises(ValueError, match="octet 3"):
            encode_mac("02:00:5E:GG:BB:CC")

    def test_octet_overflow(self):
        # int("1FF", 16) == 511, must be rejected with a friendly error
        with pytest.raises(ValueError, match="out of range"):
            encode_mac("02:00:5E:1FF:00:01")

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

    def test_max_length_passes(self):
        # 126 BMP chars × 2 + 2 header = 254 = 0xFE → fits in length byte
        encoded = encode_usb_string("X" * 126)
        assert encoded[0] == 0xFE
        assert len(encoded) == 0xFE

    def test_just_over_max_fails(self):
        # 127 BMP chars × 2 + 2 header = 256 → overflows length byte
        with pytest.raises(ValueError, match="too long"):
            encode_usb_string("X" * 127)

    def test_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            encode_usb_string("X" * 128)


class TestGoldenImage:
    """Byte-for-byte regression check against a checked-in golden binary.

    If this fails after an intentional format change, regenerate with:
        python3 eeprom_encoder.py eeprom-default.yaml eeprom-default.golden.bin
    """

    def test_default_yaml_matches_golden(self):
        assert GOLDEN_BIN.exists(), (
            f"Missing fixture {GOLDEN_BIN}. Regenerate with: "
            f"python3 eeprom_encoder.py eeprom-default.yaml eeprom-default.golden.bin"
        )
        cfg = yaml.safe_load(DEFAULT_YAML.read_text())
        produced = build_eeprom(cfg)
        expected = GOLDEN_BIN.read_bytes()
        assert produced == expected, (
            f"EEPROM image drifted from golden.\n"
            f"  produced sha256: {hashlib.sha256(produced).hexdigest()}\n"
            f"  golden   sha256: {hashlib.sha256(expected).hexdigest()}"
        )

    def test_default_yaml_is_valid(self):
        # Smoke check: shipped YAML loads, builds, and is the right size.
        cfg = yaml.safe_load(DEFAULT_YAML.read_text())
        data = build_eeprom(cfg)
        assert len(data) == EEPROM_SIZE
        assert data[0x00:0x02] == SIGNATURE


def _run_main(monkeypatch, *args):
    """Invoke main() in-process so coverage tracks it. Returns nothing; raises SystemExit on error."""
    monkeypatch.setattr(sys, "argv", ["eeprom_encoder.py", *args])
    eeprom_encoder.main()


class TestMain:
    """In-process tests of main(). Keep one subprocess test below for true E2E coverage."""

    def test_no_args_exits_nonzero(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["eeprom_encoder.py"])
        with pytest.raises(SystemExit) as exc:
            eeprom_encoder.main()
        assert exc.value.code == 1
        assert "Usage" in capsys.readouterr().err

    def test_writes_binary_to_explicit_path(self, monkeypatch, tmp_path, capsys):
        out = tmp_path / "out.bin"
        _run_main(monkeypatch, str(DEFAULT_YAML), str(out))
        assert out.read_bytes() == GOLDEN_BIN.read_bytes()
        assert f"Written {EEPROM_SIZE} bytes" in capsys.readouterr().out

    def test_default_output_path_derived_from_input(self, monkeypatch, tmp_path):
        src = tmp_path / "myconf.yaml"
        src.write_text(DEFAULT_YAML.read_text())
        _run_main(monkeypatch, str(src))
        derived = tmp_path / "myconf.bin"
        assert derived.exists()
        assert derived.read_bytes() == GOLDEN_BIN.read_bytes()

    def test_default_mac_warning_printed(self, monkeypatch, tmp_path, capsys):
        out = tmp_path / "out.bin"
        _run_main(monkeypatch, str(DEFAULT_YAML), str(out))
        captured = capsys.readouterr().out
        assert "WARNING" in captured
        assert "MAC is the template default" in captured

    def test_no_warning_for_custom_mac(self, monkeypatch, tmp_path, capsys):
        cfg = yaml.safe_load(DEFAULT_YAML.read_text())
        cfg["mac"] = "02:00:5E:DE:AD:BE"
        src = tmp_path / "custom.yaml"
        src.write_text(yaml.safe_dump(cfg))
        out = tmp_path / "out.bin"
        _run_main(monkeypatch, str(src), str(out))
        assert "WARNING" not in capsys.readouterr().out

    def test_empty_yaml_uses_defaults(self, monkeypatch, tmp_path):
        src = tmp_path / "empty.yaml"
        src.write_text("")
        out = tmp_path / "out.bin"
        _run_main(monkeypatch, str(src), str(out))
        # Defaults match the golden image (the shipped YAML uses the same defaults)
        assert out.read_bytes() == GOLDEN_BIN.read_bytes()

    def test_non_mapping_yaml_fails_cleanly(self, monkeypatch, tmp_path, capsys):
        src = tmp_path / "list.yaml"
        src.write_text("- one\n- two\n")
        out = tmp_path / "out.bin"
        with pytest.raises(SystemExit) as exc:
            _run_main(monkeypatch, str(src), str(out))
        assert exc.value.code != 0
        assert "mapping" in str(exc.value.code) or "mapping" in capsys.readouterr().err
        assert not out.exists()

    def test_missing_yaml_fails(self, monkeypatch, tmp_path):
        out = tmp_path / "out.bin"
        with pytest.raises(FileNotFoundError):
            _run_main(monkeypatch, str(tmp_path / "nope.yaml"), str(out))

    def test_invalid_config_propagates_error(self, monkeypatch, tmp_path):
        src = tmp_path / "bad.yaml"
        src.write_text("vid: 0x1FFFF\n")  # out of range
        out = tmp_path / "out.bin"
        with pytest.raises(ValueError, match="VID"):
            _run_main(monkeypatch, str(src), str(out))
        assert not out.exists()


class TestCliBlackBox:
    """One real subprocess invocation as a smoke test that the script is executable end-to-end."""

    def test_subprocess_invocation(self, tmp_path):
        out = tmp_path / "out.bin"
        result = subprocess.run(
            [sys.executable, str(ENCODER), str(DEFAULT_YAML), str(out)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert out.read_bytes() == GOLDEN_BIN.read_bytes()
