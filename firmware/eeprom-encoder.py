#!/usr/bin/env python3
"""
RTL8153B EEPROM encoder — PoEt project
Usage: python3 eeprom-encoder.py <config.yaml> [output.bin]
Output: 128-byte binary suitable for 93LC46 (PoEt U3)

Byte layout per eeprom-image.md. Fields not set by the YAML are left 0xFF
(93LC46 erased state). Consult RTL8153B datasheet for reserved/inferred fields.
"""

import sys
import struct
import yaml


EEPROM_SIZE = 128
SIGNATURE = bytes([0x29, 0x81])  # RTL8153B magic


def encode_mac(mac_str: str) -> bytes:
    parts = mac_str.strip().split(":")
    if len(parts) != 6:
        raise ValueError(f"MAC address must have 6 octets: {mac_str!r}")
    return bytes(int(p, 16) for p in parts)


def encode_usb_string(text: str) -> bytes:
    utf16 = text.encode("utf-16-le")
    length = 2 + len(utf16)  # bLength + bDescriptorType + string
    if length > 0xFF:
        raise ValueError(f"String too long ({length} bytes): {text!r}")
    return bytes([length, 0x03]) + utf16


def build_eeprom(cfg: dict) -> bytes:
    buf = bytearray([0xFF] * EEPROM_SIZE)

    # 0x00-0x01: signature
    buf[0x00:0x02] = SIGNATURE

    # 0x02-0x03: VID (little-endian)
    vid = int(cfg.get("vid", 0x0BDA))
    struct.pack_into("<H", buf, 0x02, vid)

    # 0x04-0x05: PID (little-endian)
    pid = int(cfg.get("pid", 0x8153))
    struct.pack_into("<H", buf, 0x04, pid)

    # 0x06-0x0B: MAC address
    mac = encode_mac(cfg.get("mac", "02:00:5E:00:00:01"))
    buf[0x06:0x0C] = mac

    # 0x0C-0x0D: bcdDevice (leave default 0x0300)
    buf[0x0C] = 0x00
    buf[0x0D] = 0x30

    # 0x0E: MaxPower
    self_powered = bool(cfg.get("self_powered", True))
    max_power_ma = int(cfg.get("max_power_ma", 0))
    buf[0x0E] = 0 if self_powered else max(1, max_power_ma // 2)

    # 0x0F: config flags — bit 5 = self-powered
    buf[0x0F] = 0x20 if self_powered else 0x00

    # 0x10: LED config
    buf[0x10] = int(cfg.get("led_config", 0x07))

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


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <config.yaml> [output.bin]", file=sys.stderr)
        sys.exit(1)

    yaml_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else yaml_path.replace(".yaml", ".bin")

    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)

    data = build_eeprom(cfg)
    assert len(data) == EEPROM_SIZE

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
    print(f"  Self-powered: {bool(data[0x0F] & 0x20)}")


if __name__ == "__main__":
    main()
