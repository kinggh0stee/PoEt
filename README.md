# PoEt — PoE → USB-C Gigabit Adapter

A KiCad PCB project that converts an **802.3af PoE** Ethernet drop into a USB-C port carrying both **5 V / 2 A power** and **Gigabit Ethernet over USB 3.0**. Open-hardware clone of the Ubiquiti **UACC-Adapter-PoE-USBC** ($49 retail).

## What it does

✅ Plug RJ45 from a PoE switch in one end, plug any USB-C device in the other.
✅ The USB-C device sees a Gigabit Ethernet adapter (auto-driver-binds on Linux, Windows, macOS, ChromeOS, iPadOS).
✅ Up to **10 W (5 V × 2 A)** delivered to the host over USB-C — enough to power a Pi Zero 2 W, Pi 4 (light load), USB-C cameras, microcontroller dev boards, USB-powered SBCs.
✅ Bus speed depends on USB-C cable: a USB 3.x cable enables full Gigabit; a USB 2.0 cable caps at ~480 Mbps.

## What it doesn't do

❌ No USB-PD (5 V fixed only) — cannot charge laptops or phones at fast-charge speeds.
❌ Single-orientation USB 3.0 SuperSpeed. USB 2.0 fallback works in either orientation, so the device always enumerates; SuperSpeed (and therefore full Gigabit throughput) requires plugging the cable in the right way up.

## Top-level block diagram

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

## Quick spec

| Parameter | Value |
|---|---|
| PoE input | IEEE 802.3af Type 1 (Class 0 advertisement, ≤12.95 W at PD) |
| Ethernet | 10 / 100 / 1000 BASE-T full duplex, auto MDI/MDIX |
| USB output | USB 3.2 Gen 1 (5 Gbps), Type-C, single-orientation SS |
| USB-C power role | Source, 5 V / 2 A (10 W advertised via 22 kΩ Rp on CC) |
| Isolation | 1500 Vrms (PoE side ↔ USB side) |
| Target dimensions | ~60 × 30 mm, 4-layer board |
| Operating temp | 0 – 50 °C |
| Target BOM (1k qty) | ~$10 |

## Folder layout

```
PoE-USBC-Gigabit/
├── README.md                       ← you are here
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

## Getting started

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in **KiCad 8.0+**
2. Read `docs/design-spec.md` first — note the 4 mm creepage rule between PoE primary and USB secondary
3. Order parts per `docs/bom.md`
4. Schematic is split into 5 hierarchical sheets — see `docs/schematic-plan.md`

## License

CERN-OHL-S v2 (hardware), MIT (any firmware/scripts).

## References

- Ubiquiti UACC-Adapter-PoE-USBC datasheet (the inspiration)
- Silicon Labs Si3402-B reference design AN1004
- Realtek RTL8153B datasheet & EEPROM tools (NDA)
