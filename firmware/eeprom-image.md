# RTL8153B EEPROM Configuration

The RTL8153B reads a 93C46 (1 Kbit MicroWire) EEPROM at boot to configure:

- USB Vendor ID (VID) and Product ID (PID)
- USB string descriptors (Manufacturer, Product, Serial Number)
- 48-bit Ethernet MAC address (must be unique per board)
- USB power consumption advertised in descriptors
- LED behavior

## Default values (use Realtek's IDs to get auto-driver-binding)

| Field | Address | Value |
|---|---|---|
| Magic | 0x00–0x01 | `0x29 0x81` (RTL8153B signature) |
| VID | 0x02–0x03 | `0xDA 0x0B` (0x0BDA = Realtek) |
| PID | 0x04–0x05 | `0x53 0x81` (0x8153) |
| MAC[0..5] | 0x06–0x0B | unique per board, see allocation below |
| Power (mA) | 0x0E | `0x32` (100 mA — bus-powered nominal; we are self-powered so this is informational) |
| Bus-powered flag | 0x0F | `0x00` (self-powered) |

## MAC address allocation

Use a locally-administered MAC range until/unless an OUI is purchased:
- First octet bit 1 set, bit 0 clear → e.g. `02:xx:xx:xx:xx:xx`
- Recommended: `02:00:5E:` followed by 24 bits of board serial number
- For production: register an IEEE OUI ($2,995 for 24-bit MA-L, $755 for 24-bit MA-S, $580 for MA-M as of 2025) and program from a per-board secret.

## Programming

Two options:

### Option A — preprogram before assembly
Order the EEPROM with a serial number range from the distributor (most carry programmable EEPROMs on demand). Simplest for low volumes.

### Option B — in-circuit program after assembly
Add 4 test points on the EEPROM lines (CS, CLK, DI, DO) and program through them with a Bus Pirate, FT232H, or a Pi Pico running a MicroWire master.

Realtek provides `RTL8153B_EEPROM_Programmer.exe` (Windows) that talks to the chip via USB and writes the EEPROM through the RTL8153B's own SMI-style interface — this is the easiest way at production. Run on a Windows test fixture as part of board test.

## Reference

- RTL8153B datasheet: NDA required from Realtek, but reference designs and EEPROM templates circulate widely
- Linux driver: `r8152` (in-tree since kernel 4.x), or out-of-tree from Realtek for newest features

## Files

- `eeprom-default.bin` — 128 byte template (TODO: generate)
- `eeprom-encoder.py` — script to produce a .bin from a YAML config (TODO)
