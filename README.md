# PoEt — PoE to USB-C Gigabit Adapter

A KiCad PCB project that converts an **802.3af PoE** Ethernet drop into a USB-C port carrying both **5 V / 2 A power** and **Gigabit Ethernet over USB 3.0**. Open-hardware clone of the Ubiquiti **UACC-Adapter-PoE-USBC** ($49 retail).

Design by [gh0stee.com](https://gh0stee.com)

## Features

- Single RJ45 input from a PoE switch; single USB-C output to the host device
- USB-C host sees a Gigabit Ethernet adapter — driver-less on Linux, Windows, macOS, ChromeOS, and iPadOS
- Up to **10 W (5 V × 2 A)** delivered over USB-C, sufficient for a Raspberry Pi Zero 2 W, Pi 4 (light load), USB-C cameras, and similar single-board computers
- Full Gigabit throughput with a USB 3.x cable in either orientation; degrades gracefully to ~480 Mbps on a USB 2.0 cable
- **Parametric OpenSCAD case** included — snap-fit standalone enclosure with LED windows and a reset pinhole, prints without supports

## Limitations

- No USB Power Delivery — output is fixed 5 V; laptops and fast-charge phones are not supported

## Block Diagram

```
   ┌─────────────────────┐
   │  RJ45 + Magnetics   │◄── Cat5e/6 from 802.3af PoE switch
   │  (PoE-rated jack)   │
   └──┬───────────────┬──┘
      │ MDI[0..3]±    │ center-tap power (modes A & B)
      │ (data pairs)  │
      ▼               ▼
  ┌─────────┐   ┌──────────────────┐
  │ ESD/TVS │   │ 2× Schottky      │ ← polarity-insensitive
  └────┬────┘   │ bridges + bulk   │
       │        └─────────┬────────┘
       │                  ▼   ~37–57 V DC
       │        ┌──────────────────┐
       │        │ Si3402-B PD +    │ Class 0/3 negotiation,
       │        │ integrated PWM   │ flyback control, 100 V switch
       │        └─────────┬────────┘
       │                  │
       │                  ▼   isolated 5 V / 2 A rail
       │                  │
       ▼                  │
  ┌─────────────────┐     │
  │ RTL8153B        │     │
  │ USB 3.0 ⇄ GbE   │◄────┤ powered from 5 V (with internal 3.3 V & 1 V LDOs)
  └────────┬────────┘     │
           │ SS+/SS-/D+/- │
           ▼              ▼
       ┌──────────────────────┐
       │  USB-C receptacle    │──► Host
       │  (Source 5 V / 2 A)  │
       └──────────────────────┘
```

Single-chip PoE PD (Si3402-B handles detect, classify, hot-swap, and flyback control) keeps the BOM tight.

## Specifications

| Parameter | Value |
|---|---|
| PoE input | IEEE 802.3af Type 1 (Class 0 advertisement, ≤ 12.95 W at PD) |
| Ethernet | 10 / 100 / 1000 BASE-T full duplex, auto MDI/MDIX |
| USB output | USB 3.2 Gen 1 (5 Gbps), Type-C, dual-orientation SS via mux (U11 + U12) |
| USB-C power role | Source, 5 V / 2 A; CC Rp = 22 kΩ → 1.5 A advertised (7.5 W) |
| Isolation | 1500 Vrms (PoE side to USB side) |
| Dimensions | ~60 × 30 mm, 4-layer board |
| Operating temp | 0 – 50 °C |
| BOM cost | ~$31 single unit / ~$13 at 1k qty |

## Repository Layout

```
PoEt/
├── hardware/                           ← KiCad project
│   ├── PoE-USBC-Gigabit.kicad_pro
│   ├── PoE-USBC-Gigabit.kicad_sch     ← root sheet (sheet symbols + title block)
│   ├── PoE-USBC-Gigabit.kicad_pcb     ← PCB layout (4-layer, 60×30 mm)
│   ├── 01_PoE_Frontend.kicad_sch      ← RJ45, magnetics, ESD, MDI breakout
│   ├── 02_PoE_PD_Converter.kicad_sch  ← bridges, Si3402-B, flyback, feedback
│   ├── 03_Bias_Rails.kicad_sch        ← 3.3 V and 1.0 V LDOs
│   ├── 04_RTL8153B_Bridge.kicad_sch   ← USB↔GbE controller, EEPROM, crystal
│   └── 05_USBC_Connector.kicad_sch    ← USB-C receptacle, CC Rp, ESD, AC-coupling
├── docs/
│   ├── design-spec.md                 ← electrical spec, layout rules
│   ├── bom.md                         ← full parts list with LCSC numbers
│   ├── schematic-plan.md              ← sheet I/O contracts and conventions
│   ├── BUILD-SHEET-0[1-5].md          ← step-by-step schematic build guides
│   ├── FABRICATION.md                 ← gerber export + JLCPCB order guide
│   └── BRING-UP.md                    ← staged power-on test procedure
├── case/
│   └── poet-case.scad                 ← parametric snap-fit enclosure (OpenSCAD)
├── fabrication/                        ← gerbers + assembly files (git-ignored)
└── firmware/
    ├── eeprom-image.md                ← RTL8153B EEPROM byte layout
    ├── eeprom-default.yaml            ← default EEPROM config (VID/PID/MAC)
    ├── eeprom_encoder.py              ← generates .bin from YAML config
    ├── test_eeprom_encoder.py         ← pytest suite
    └── requirements.txt               ← PyYAML, pytest
```

## Getting Started

### Viewing / editing the design

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in **KiCad 8.0+**
2. Read `docs/design-spec.md` before making any layout changes — the 4 mm creepage rule between the PoE primary and USB secondary is a hard constraint
3. The schematic is split across 5 hierarchical sheets; `docs/schematic-plan.md` documents the sheet I/O contracts and net class assignments

### Building the schematic from scratch

Follow the `docs/BUILD-SHEET-0[1-5].md` guides in order. Each guide walks through component placement, wiring, ERC expectations, and footprint assignment for one sheet. Run ERC (`F8`) after each sheet before moving to the next.

### Fabrication

See `docs/FABRICATION.md` for the full gerber export procedure and JLCPCB order settings (impedance control, isolation slot, ENIG finish).

### Programming the EEPROM

Each board needs a unique MAC address written to U3 (93LC46 EEPROM). Generate the binary from the YAML config:

```bash
pip install -r firmware/requirements.txt
cd firmware
python3 eeprom_encoder.py eeprom-default.yaml   # → eeprom-default.bin
```

Edit `mac:` in `eeprom-default.yaml` to a unique value before generating. Then program the binary using one of:

- **Option A (preferred):** Realtek's `r8153_fw_tool` (Linux) or `RTL8153B_EEPROM_Programmer.exe` (Windows) over USB once the board enumerates
- **Option B:** Bus Pirate / FT232H on test points TP1–TP4 (MicroWire, CS active-high, 16-bit words, ≤ 3 MHz)
- **Option C:** Pre-program the 93LC46 before assembly via a distributor programming service

See `firmware/eeprom-image.md` for the full byte map.

### Bring-up

Follow `docs/BRING-UP.md` — a 6-stage procedure from cold resistance checks through full-load thermal test. Do not skip stages; the primary side runs at up to 57 V.

### 3D-printed case

Open `case/poet-case.scad` in **OpenSCAD 2021.01+**. Both shells are in print-ready orientation — no rotation needed in your slicer.

Before printing:
1. Verify `clr_top` clears the tallest component on your board (default 12 mm; T1 transformer body ≈ 10 mm)
2. Adjust `led_xpos`, `led_ypos`, `sw_xpos`, `sw_ypos` to match the KiCad component positions
3. Verify `rj45_h` and `usbc_h` against the actual connector datasheets
4. Print a single-wall cross-section slice first to confirm the snap geometry fits your printer's tolerance

All dimensions are parametric — tunable at the top of the file.

## License

CERN-OHL-S v2 (hardware), MIT (firmware/scripts).

## References

- Ubiquiti UACC-Adapter-PoE-USBC (the inspiration)
- Silicon Labs Si3402-B reference design AN1004
- Realtek RTL8153B datasheet & EEPROM tools (NDA required from Realtek)
