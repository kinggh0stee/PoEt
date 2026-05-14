# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

PoEt is an open-hardware KiCad PCB project that converts an 802.3af PoE Ethernet drop into a USB-C port delivering 5 V / 2 A power and Gigabit Ethernet over USB 3.0. It is a clone of the Ubiquiti UACC-Adapter-PoE-USBC. Licensed CERN-OHL-S v2 (hardware) and MIT (firmware/scripts).

The only software in this repo is the EEPROM encoder script (`firmware/eeprom-encoder.py`). Everything else is hardware design files and documentation.

## Firmware (the only runnable code)

### Setup

```bash
pip install -r firmware/requirements.txt   # installs PyYAML
```

### Generate EEPROM binary

```bash
cd firmware
python3 eeprom-encoder.py eeprom-default.yaml          # → eeprom-default.bin
python3 eeprom-encoder.py eeprom-default.yaml out.bin  # explicit output path
```

The script reads a YAML config and writes a 128-byte binary for the 93LC46 EEPROM (U3). The generated `.bin` is git-ignored; always regenerate from the YAML source.

### EEPROM programming

- **Option A (preferred):** Board enumerated over USB → use Realtek's `r8153_fw_tool` (Linux) or `RTL8153B_EEPROM_Programmer.exe` (Windows) to write through the RTL8153B's own USB interface.
- **Option B:** Bus Pirate / FT232H on test points TP1=CS, TP2=CLK, TP3=DI, TP4=DO — MicroWire 3-wire, CS active-high, 16-bit word size, ≤ 3 MHz.
- **Option C:** Pre-program the 93LC46 before assembly via distributor programming service.

See `firmware/eeprom-image.md` for the full byte map and MAC allocation strategy.

## Architecture

### System signal flow

```
RJ45 (PoE input)
  → Sheet 01: Magnetics, ESD (NUP4202W1), MDI breakout
  → Sheet 02: Schottky bridges → Si3402-B PD → flyback T1 → 5 V / 2 A rail
  → Sheet 03: AP2112K → 3.3 V, RT9013 → 1.0 V (bias for RTL8153B)
  → Sheet 04: RTL8153B (GbE PHY + USB 3.0), 93LC46 EEPROM, 25 MHz crystal
  → Sheet 05: USB-C receptacle, CC Rp (22 kΩ → 1.5 A), ESD, AC-coupling caps
```

### Critical isolation boundary

The PoE primary side (`GND_POE`) and USB secondary side (`GND`) are **galvanically isolated at 1500 Vrms**. The boundary crosses:
- Flyback transformer T1 (power)
- Optocoupler U6 + TL431 U7 (feedback)
- RJ45 integrated magnetics (data)
- Y-cap C3, 1 nF / 2 kV (EMC)
- A net tie (for ERC) between `GND_POE` and `GND` at the Y-cap

Any edit touching components on both sides of the barrier requires checking the ≥ 4 mm creepage/clearance rule across all four copper layers.

### Schematic sheet conventions

Reference designators are grouped by sheet (e.g., U1xx for Sheet 01, U2 for Sheet 02, U101/U102 for ESD arrays in Sheet 01). Net classes in `PoE-USBC-Gigabit.kicad_pro`:

| Net class | Impedance | Trace / gap |
|---|---|---|
| `USB3_SS` | 90 Ω diff | 0.15 mm / 0.13 mm |
| `ETHERNET_MDI` | 100 Ω diff | 0.25 mm / 0.20 mm |
| `POE_PRIMARY` | — | ≥ 0.5 mm |
| `POWER_5V` | — | ≥ 0.4 mm |

### EEPROM config (`eeprom-default.yaml`)

Default ships Realtek VID `0x0BDA` / PID `0x8153` so the in-tree Linux `r8152` driver auto-binds. Change the MAC field — `02:00:5E:xx:xx:xx` — to a unique value per board. The `self_powered: true` flag is important: the board draws from PoE, not from the USB host.

## Hardware design workflow

### Schematic editing order

Build sheets in order: 01 → 02 → 03 → 04 → 05. Run ERC (`F8` in Eeschema) after each sheet. The goal is 0 errors before proceeding; expected non-errors are documented in `docs/schematic-plan.md` under "ERC expectations."

### PCB validation

```
PCB Editor → Inspect → Design Rules Checker → Run DRC
```

The `.kicad_dru` file in `hardware/` loads automatically. Target: 0 errors. Acceptable warnings are listed in `docs/FABRICATION.md`.

### Generating fabrication outputs

All fabrication outputs go to `fabrication/` (git-ignored). Steps in `docs/FABRICATION.md`:
1. Add the isolation slot to Edge.Cuts (2 mm slot at x ≈ 56 mm, full board height)
2. Run DRC → 0 errors
3. Plot gerbers (File → Plot) + drill files
4. Export BOM CSV and CPL CSV for JLCPCB SMT assembly
5. Order with impedance control on JLC04161H-7628 stackup; note the PCB slot in special instructions

## Key design constraints (never violate)

- **4 mm creepage/clearance** between PoE primary and USB secondary — in all four copper layers
- **PoE-rated RJ45** (J1) required — non-PoE jacks lack center-tap traces and can't handle DC current
- **Single-orientation SS:** TX1/RX1 only are wired; TX2/RX2 are NC. USB 2.0 (D+/D-) is reversible by shorting A6+B6 and A7+B7 at the connector pads
- **22 kΩ Rp on CC1/CC2** (not 10 kΩ): advertises 1.5 A source; using 10 kΩ would advertise 3 A which the 2 A supply cannot sustain
- **Flyback transformer T1** must be matched to Si3402-B reference design AN1004 — do not substitute blindly
- **Crystal Y1:** 25 MHz, CL = 12 pF, load capacitors C20/C21 = 18 pF NP0; verify against chosen crystal datasheet

## Bring-up sequence

Hardware bring-up follows a staged procedure (`docs/BRING-UP.md`):
1. Visual inspection + cold resistance checks before any power
2. Bench PSU (48 V, 150 mA limit) on PAIR test points — verify V_POE, Si3402-B quiescent
3. Live PoE switch — verify PD negotiation and 5 V rail
4. Measure 3.3 V and 1.0 V bias rails
5. USB-C to Linux host — verify `dmesg` shows `idVendor=0bda idProduct=8153` and `r8152` binds
6. Ethernet link — verify 1000 Mbps with `ethtool eth0`, throughput with `iperf3`
7. Full-load thermal test (15 min at 1.5 A USB + iperf3); Si3402-B < 70 °C, RTL8153B < 60 °C

## Procurement notes

- **Si3402-B:** Skyworks announced PoE PD line wind-down 2025 — verify availability. Drop-ins: TPS23753APWR (TI, needs external N-FET) or LTC4267 (ADI).
- **RTL8153B:** had supply issues 2023–2024. Drop-ins: ASIX AX88179B (different footprint) or Microchip LAN7800 (different driver).
- LCSC part numbers for JLCPCB assembly: RTL8153B = C77999, AP2112K-3.3 = C51118, RT9013-10GB = C47773, PC817B = C7440, TL431 = C7831.
