#!/usr/bin/env python3
"""
RTL8153B EEPROM encoder — PoEt project
Usage: python3 eeprom_encoder.py <config.yaml> [output.bin]
Output: 128-byte binary suitable for 93LC46 (PoEt U3)

Requires: PyYAML  (pip install PyYAML  or  pip install -r requirements.txt)

Byte layout per eeprom-image.md. Fields not set by the YAML are left 0xFF
(93LC46 erased state). Consult RTL8153B datasheet for reserved/inferred fields.
"""

import sys
import struct
from pathlib import Path
from typing import Any
try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install PyYAML  (or: pip install -r requirements.txt)")


EEPROM_SIZE = 128
SIGNATURE = bytes([0x29, 0x81])  # RTL8153B magic


def encode_mac(mac_str: str) -> bytes:
    parts = mac_str.strip().split(":")
    if len(parts) != 6:
        raise ValueError(f"MAC address must have 6 octets: {mac_str!r}")
    result = []
    for i, p in enumerate(parts):
        try:
            value = int(p, 16)
        except ValueError:
            raise ValueError(f"MAC octet {i} is not valid hex: {p!r} in {mac_str!r}")
        if not 0 <= value <= 0xFF:
            raise ValueError(f"MAC octet {i} value 0x{value:X} out of range 0x00-0xFF in {mac_str!r}")
        result.append(value)
    return bytes(result)


def encode_usb_string(text: str) -> bytes:
    utf16 = text.encode("utf-16-le")
    length = 2 + len(utf16)  # bLength + bDescriptorType + string
    if length > 0xFF:
        raise ValueError(f"String too long ({length} bytes): {text!r}")
    return bytes([length, 0x03]) + utf16


def build_eeprom(cfg: dict[str, Any]) -> bytes:
    buf = bytearray([0xFF] * EEPROM_SIZE)

    # 0x00-0x01: signature
    buf[0x00:0x02] = SIGNATURE

    # 0x02-0x03: VID (little-endian)
    try:
        vid = int(cfg.get("vid", 0x0BDA))
    except (TypeError, ValueError):
        raise ValueError(f"'vid' must be an integer, got {cfg.get('vid')!r}")
    if not 0x0001 <= vid <= 0xFFFE:
        raise ValueError(f"VID 0x{vid:04X} out of valid USB range 0x0001–0xFFFE")
    struct.pack_into("<H", buf, 0x02, vid)

    # 0x04-0x05: PID (little-endian)
    try:
        pid = int(cfg.get("pid", 0x8153))
    except (TypeError, ValueError):
        raise ValueError(f"'pid' must be an integer, got {cfg.get('pid')!r}")
    if not 0x0000 <= pid <= 0xFFFF:
        raise ValueError(f"PID 0x{pid:04X} out of valid USB range 0x0000–0xFFFF")
    struct.pack_into("<H", buf, 0x04, pid)

    # 0x06-0x0B: MAC address
    mac = encode_mac(cfg.get("mac", "02:00:5E:00:00:01"))
    buf[0x06:0x0C] = mac

    # 0x0C-0x0D: bcdDevice (leave default 0x0300)
    buf[0x0C] = 0x00
    buf[0x0D] = 0x30

    # 0x0E: MaxPower
    self_powered = bool(cfg.get("self_powered", True))
    try:
        max_power_ma = int(cfg.get("max_power_ma", 0))
    except (TypeError, ValueError):
        raise ValueError(f"'max_power_ma' must be an integer, got {cfg.get('max_power_ma')!r}")
    if max_power_ma < 0:
        raise ValueError(f"'max_power_ma' must be non-negative, got {max_power_ma}")
    if not self_powered and max_power_ma > 510:
        raise ValueError(
            f"'max_power_ma' {max_power_ma} exceeds USB max 510 mA (encoded as a single byte × 2)"
        )
    buf[0x0E] = 0 if self_powered else max(1, max_power_ma // 2)

    # 0x0F: config flags — bit 5 = self-powered
    buf[0x0F] = 0x20 if self_powered else 0x00

    # 0x10: LED config
    try:
        led_config = int(cfg.get("led_config", 0x07))
    except (TypeError, ValueError):
        raise ValueError(f"'led_config' must be an integer, got {cfg.get('led_config')!r}")
    if not 0 <= led_config <= 0xFF:
        raise ValueError(f"'led_config' 0x{led_config:X} out of byte range 0x00-0xFF")
    buf[0x10] = led_config

    # 0x11-0x1F: reserved, leave 0xFF

    # 0x20+: optional string descriptors
    offset = 0x20
    for key in ("manufacturer", "product", "serial"):
        value = cfg.get(key, "")
        if value:
            encoded = encode_usb_string(value)
            end = offset + len(encoded)
            if end > EEPROM_SIZE:
                raise ValueError(
                    f"String descriptor '{key}' overflows EEPROM at offset 0x{offset:02X}"
                )
            buf[offset:end] = encoded
            offset = end

    return bytes(buf)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <config.yaml> [output.bin]", file=sys.stderr)
        sys.exit(1)

    yaml_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else str(Path(yaml_path).with_suffix(".bin"))

    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        sys.exit(f"YAML root must be a mapping, got {type(cfg).__name__}: {yaml_path}")

    data = build_eeprom(cfg)
    if len(data) != EEPROM_SIZE:
        raise RuntimeError(f"EEPROM buffer is {len(data)} bytes, expected {EEPROM_SIZE}")

    with open(out_path, "wb") as f:
        f.write(data)

    # Human-readable dump
    print(f"Written {EEPROM_SIZE} bytes → {out_path}")
    print()
    print("Hex dump (first 32 bytes):")
    for i in range(0, 32, 16):
        hex_part = " ".join(f"{b:02X}" for b in data[i : i + 16])
        print(f"  {i:04X}: {hex_part}")
    print()
    mac_str = ":".join(f"{b:02X}" for b in data[0x06:0x0C])
    print(f"  VID: 0x{struct.unpack_from('<H', data, 0x02)[0]:04X}")
    print(f"  PID: 0x{struct.unpack_from('<H', data, 0x04)[0]:04X}")
    print(f"  MAC: {mac_str}")
    if mac_str.upper() == "02:00:5E:00:00:01":
        print("  WARNING: MAC is the template default — update before deploying multiple boards")
    print(f"  Self-powered: {bool(data[0x0F] & 0x20)}")


if __name__ == "__main__":
    main()
