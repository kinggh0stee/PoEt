# PoEt — PoE to USB-C Gigabit Adapter

A KiCad PCB project that converts an **802.3af PoE** Ethernet drop into a USB-C port carrying both **5 V / 2 A power** and **Gigabit Ethernet over USB 3.0**. Open-hardware clone of the Ubiquiti **UACC-Adapter-PoE-USBC** ($49 retail).

Design by [gh0stee.com](https://gh0stee.com)

## Features

- Single RJ45 input from a PoE switch; single USB-C output to the host device
- USB-C host sees a Gigabit Ethernet adapter — driver-less on Linux, Windows, macOS, ChromeOS, and iPadOS
- Up to **10 W (5 V × 2 A)** delivered over USB-C, sufficient for a Raspberry Pi Zero 2 W, Pi 4 (light load), USB-C cameras, and similar single-board computers
- Full Gigabit throughput with a USB 3.x cable; degrades gracefully to ~480 Mbps on a USB 2.0 cable

## Limitations

- No USB Power Delivery — output is fixed 5 V; laptops and fast-charge phones are not supported
- SuperSpeed (USB 3.0) lanes are single-orientation only. USB 2.0 fallback works in either orientation, so the device always enumerates; Gigabit throughput requires the cable to be inserted in the correct orientation

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
| PoE input | IEEE 802.3af Type 1 (Class 0 advertisement, ≤12.95 W at PD) |
| Ethernet | 10 / 100 / 1000 BASE-T full duplex, auto MDI/MDIX |
| USB output | USB 3.2 Gen 1 (5 Gbps), Type-C, single-orientation SS |
| USB-C power role | Source, 5 V / 2 A output; CC Rp = 22 kΩ → 1.5 A advertised (7.5 W) |
| Isolation | 1500 Vrms (PoE side to USB side) |
| Target dimensions | ~60 × 30 mm, 4-layer board |
| Operating temp | 0 – 50 °C |
| Target BOM (1k qty) | ~$10 |

## Repository Layout

```
PoE-USBC-Gigabit/
├── README.md
├── hardware/                       ← KiCad project
│   ├── PoE-USBC-Gigabit.kicad_pro
│   ├── PoE-USBC-Gigabit.kicad_sch
│   └── PoE-USBC-Gigabit.kicad_pcb
├── docs/
│   ├── design-spec.md              ← electrical spec, layout rules
│   ├── bom.md                      ← parts list
│   └── schematic-plan.md           ← 5 hierarchical sub-sheets
├── fabrication/                    ← gerbers + assembly drawings (generated)
└── firmware/
    └── eeprom-image.md             ← RTL8153B EEPROM (VID/PID/MAC)
```

## Getting Started

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in **KiCad 8.0+**
2. Read `docs/design-spec.md` — note the 4 mm creepage rule between the PoE primary and USB secondary
3. Order parts per `docs/bom.md`
4. The schematic is split into 5 hierarchical sheets — see `docs/schematic-plan.md`

## License

CERN-OHL-S v2 (hardware), MIT (any firmware/scripts).

## References

- Ubiquiti UACC-Adapter-PoE-USBC datasheet (the inspiration)
- Silicon Labs Si3402-B reference design AN1004
- Realtek RTL8153B datasheet & EEPROM tools (NDA)
