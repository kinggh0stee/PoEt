# RTL8153B EEPROM Configuration

The RTL8153B reads a 93C46 (1 Kbit MicroWire) EEPROM at boot to configure:

- USB Vendor ID (VID) and Product ID (PID)
- USB string descriptors (Manufacturer, Product, Serial Number)
- 48-bit Ethernet MAC address (must be unique per board)
- USB power consumption advertised in descriptors
- LED behavior

## Byte layout

The RTL8153B EEPROM is 128 bytes (1 Kbit, word-addressed as 64 × 16-bit words). Bytes are stored little-endian. Fields not listed here are reserved — leave at `0xFF` (erased state of the 93LC46).

Source: `drivers/net/usb/r8152.c` (Linux kernel, open-source), cross-referenced against community teardowns of RTL8153B-based adapters. Consult the RTL8153B datasheet (Realtek NDA) for any field marked *inferred*.

| Offset | Bytes | Field | Value | Notes |
|---|---|---|---|---|
| 0x00 | 2 | Signature | `0x29 0x81` | RTL8153B magic; RTL8152 uses `0x28 0x81` |
| 0x02 | 2 | USB VID | `0xDA 0x0B` | 0x0BDA = Realtek (LE) |
| 0x04 | 2 | USB PID | `0x53 0x81` | 0x8153 (LE); `r8152` driver binds to this |
| 0x06 | 6 | MAC address | `02 00 5E xx xx xx` | See MAC allocation section |
| 0x0C | 1 | USB bcdDevice lo | `0x00` | Device release number, lo byte *(inferred)* |
| 0x0D | 1 | USB bcdDevice hi | `0x30` | Device release number, hi byte → 0x3000 (BCD 30.00) *(inferred)* |
| 0x0E | 1 | MaxPower | `0x00` | In 2 mA units. `0x00` = self-powered (we draw from PoE) |
| 0x0F | 1 | Config flags | `0x20` | Bit 5 = self-powered; bit 0 = remote wakeup *(inferred)* |
| 0x10 | 1 | LED config | `0x07` | Default: LED0 = LINK, LED1 = ACT, LED2 = off *(inferred)* |
| 0x11–0x1F | 15 | Reserved | `0xFF` | Leave erased |
| 0x20–0x7F | 96 | String descriptors | see below | Optional; omit to use RTL8153B internal defaults |

### String descriptors (optional, 0x20–0x7F)

If omitted, the chip uses its internal ROM strings ("Realtek", "USB 10/100/1000 LAN"). To override:

- Each string is a USB string descriptor: length byte + descriptor type byte (`0x03`) + UTF-16LE characters
- Manufacturer string at 0x20, Product string follows, Serial Number string follows
- Example manufacturer "gh0stee" in UTF-16LE: `0E 03 67 00 68 00 30 00 73 00 74 00 65 00 65 00` (14 bytes)

For a first-run board, leave 0x20–0x7F as `0xFF` and let the chip use its ROM strings. The `r8152` driver binds purely on VID/PID regardless of string descriptors.

## MAC address allocation

Use a locally-administered MAC range until/unless an OUI is purchased:
- First octet bit 1 set, bit 0 clear → e.g. `02:xx:xx:xx:xx:xx`
- Recommended: `02:00:5E:` followed by 24 bits of board serial number
- For production: register an IEEE OUI ($2,995 for 24-bit MA-L, $755 for 24-bit MA-S, $580 for MA-M as of 2025) and program from a per-board secret.

## Programming

Three options, in order of preference:

### Option A — Realtek USB programmer (easiest, preferred)

Once the board enumerates over USB (even with wrong VID/PID), Realtek's `r8153_fw_tool` or `RTL8153B_EEPROM_Programmer.exe` (Windows) can write the EEPROM through the RTL8153B's own interface — no soldering, no Bus Pirate needed.

```sh
# Linux (open-source rtl8153-fw-tool if available):
sudo ./r8153_fw_tool --write eeprom-default.bin

# Windows: run RTL8153B_EEPROM_Programmer.exe, select device, load .bin, click Write
```

If the chip doesn't enumerate at all (e.g., bad EEPROM content causing boot failure), fall back to Option B.

### Option B — In-circuit via test points TP1–TP4 (Bus Pirate / FT232H)

Connect to TP1=CS, TP2=CLK, TP3=DI, TP4=DO. Power the board normally (PoE or bench PSU). The 93LC46 runs at 3.3 V (U3 VCC tied to +3V3 rail).

**Key parameters:**
- Interface: MicroWire (SPI mode 0, CPOL=0, CPHA=0), MSB first
- Word size: **16-bit** (ORG tied to GND → 64 words × 16 bits)
- Clock speed: ≤ 3 MHz (conservative; 1 MHz is fine)
- CS is active-**high** (unlike most SPI devices which are active-low)

**Bus Pirate setup (RAWWIRE mode):**
```
HiZ> m
...select 5 (RAWWIRE)...
Raw wire mode: CLK idle low, data sampled on rising edge, MSB first
Speed: 1MHz
CS: active high
```

**Programming sequence per word (address 0 to 63):**

1. **Enable erase/write** (EWEN, send once before any write):
   - CS high → clock out: `1 1 00 000000` (9 bits: start=1, op=11, addr=00xxxxxx) → CS low
2. **Write word at address N** (repeat for all 64 words):
   - CS high → clock out: `1 01 AAAAAA DDDDDDDDDDDDDDDD` (1 start + 2 op + 6 addr + 16 data bits) → CS low
   - Poll DO: wait for DO to go high (write complete, typically < 10 ms)
3. **Disable erase/write** (EWDS) when done:
   - CS high → clock out: `1 0 00 000000` (9 bits) → CS low

**Practical note:** Most Bus Pirate users script this in Python using `pyserial` to send the raw bit sequences. A sample script is straightforward but board-specific — write one based on the `eeprom-default.bin` output from `eeprom-encoder.py`, reading 2 bytes at a time (little-endian) as each 16-bit word to program.

### Option C — Pre-program before assembly

Order the 93LC46 from a distributor that offers custom-programmed EEPROMs (e.g., Digi-Key or Arrow programming services), supply the `.bin` file. Simplest for larger quantities where programming every board individually is impractical.

## Reference

- RTL8153B datasheet: NDA required from Realtek, but reference designs and EEPROM templates circulate widely
- Linux driver: `r8152` (in-tree since kernel 4.x), or out-of-tree from Realtek for newest features

## Files

- `eeprom-default.bin` — 128-byte template (generate with `python3 eeprom-encoder.py eeprom-default.yaml`)
- `eeprom-encoder.py` — script to produce a .bin from a YAML config (see below)
- `eeprom-default.yaml` — default config (Realtek VID/PID, locally-administered MAC)
