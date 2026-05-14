# Hierarchical Schematic Plan

The schematic uses **5 hierarchical sub-sheets** off the root.

## Sheet tree

```
PoE-USBC-Gigabit.kicad_sch                      ← root, sheet symbols + title block
├── 01_PoE_Frontend.kicad_sch                   ← RJ45, magnetics, ESD, MDI breakout
├── 02_PoE_PD_Converter.kicad_sch               ← bridges, Si3402-B, T1, feedback → 5 V
├── 03_Bias_Rails.kicad_sch                     ← 3.3 V, 1.0 V LDOs from 5 V
├── 04_RTL8153B_Bridge.kicad_sch                ← USB-Eth controller, EEPROM, xtal, reset
├── 05_USBC_Connector.kicad_sch                 ← USB-C receptacle, CC pull-ups, ESD, AC-coupling
```

## Sheet I/O contracts

### Sheet 01 — PoE Frontend
- **In:** none (RJ45 cable is input)
- **Out:**
  - `PAIR_A_HI`, `PAIR_A_LO` (data pairs 1-2 / 3-6 center taps) → sheet 02
  - `PAIR_B_HI`, `PAIR_B_LO` (spare pairs 4-5 / 7-8 center taps) → sheet 02
  - `MDI0+/-`, `MDI1+/-`, `MDI2+/-`, `MDI3+/-` → sheet 04
  - `CHASSIS_GND` → board mounting holes
- **Bidir:** `LED_LINK`, `LED_ACT` ← sheet 04

### Sheet 02 — PoE PD + Converter
- **In:** `PAIR_A_HI/LO`, `PAIR_B_HI/LO`
- **Out:**
  - `+5V` (secondary, isolated) → sheet 03, sheet 05
  - `GND` (== secondary GND, isolated from primary `GND_POE`) → all secondary sheets
- **Components:** D1, D2 bridges; bulk caps; Si3402-B (U1); flyback xfmr T1; secondary rectifier D4; output bulk; opto U6 + TL431 U7; Y-cap C3 across barrier; LED3 power indicator + R3 (470 Ω) on secondary side.

⚠️ Place a **net tie** for the Y-cap between `GND_POE` and `GND` so ERC tolerates the deliberate connection.

### Sheet 03 — Bias Rails
- **In:** `+5V`, `GND`
- **Out:**
  - `+3V3` → sheet 04 (RTL8153B I/O ring)
  - `+1V0` → sheet 04 (RTL8153B core)
- **Components:** U4 (AP2112-3.3), U5 (RT9013-1.0), decoupling

⚠️ Place `PWR_FLAG` on each output rail at exactly one place here.

### Sheet 04 — RTL8153B Bridge
- **In:** `+5V`, `+3V3`, `+1V0`, `GND`, `MDI[0..3]+/-`
- **Out:**
  - `USB_SSTX+/-`, `USB_SSRX+/-` → sheet 05
  - `USB_DP`, `USB_DM` → sheet 05
  - `LED_LINK`, `LED_ACT` → sheet 01
- **Local:** Y1 (25 MHz xtal), U3 (93LC46 EEPROM), SW1 (reset), all decoupling, LED1/LED2, R401/R402

### Sheet 05 — USB-C Connector
- **In:** `+5V`, `GND`, `USB_SSTX+/-`, `USB_SSRX+/-`, `USB_DP`, `USB_DM`
  - `+3V3` is available as a global power net (no hierarchical label needed) for the comparator pull-up
- **Local components:**
  - J2 USB-C 24-pin receptacle
  - **R10, R11** = 22 kΩ 1 % from CC1, CC2 to `+5V` (Rp = advertise 1.5 A source)
  - **U11** PI3DBS12412A (or FSUSB43L10X) — 4-channel 2:1 SS mux; routes SSTX±/SSRX± to TX1/RX1 or TX2/RX2 depending on SEL
  - **U12** LMV321 single comparator (SOT-23-5) — IN+ = CC1, IN- = CC2; output drives U11 SEL; 10 kΩ pull-up (R12) from output to `+3V3`
  - **U10a, U10b** NUP4202W1 ESD arrays — one per SS pair set (TX1/RX1 and TX2/RX2), placed between mux outputs and J2
  - **U10c** NUP4202W1 on D+/D-
  - C15, C16 (100 nF) AC-coupling caps on USB_SSTX+/- **upstream of U11** (between hierarchical label and mux input)
  - C11–C14 VBUS bulk at the connector (3× 22 µF X5R + 100 nF)
- **Connector pin notes:**
  - TX1+, TX1-, RX1+, RX1- and **TX2+, TX2-, RX2+, RX2-** all connected through U11 mux
  - SBU1, SBU2 → NC
  - D+ wired to both A6 and B6 (shorted at connector pads, USB 2.0 reversibility)
  - D- wired to both A7 and B7 (same)
  - VBUS pins (A4, A9, B4, B9) all bussed to `+5V`
  - GND pins (A1, A12, B1, B12) all to `GND`
- **Orientation detection logic:**
  - When cable inserted orientation 1: CC1 pulled to ≈ 0.9 V by host Rd (5.1 kΩ); CC1 < CC2 → comparator output LOW → SEL = 0 → U11 routes SSTX to TX1, RX1 to SSRX
  - When cable inserted orientation 2: CC2 pulled low; CC1 > CC2 → comparator output HIGH → SEL = 1 → U11 routes SSTX to TX2, RX2 to SSRX
  - No cable: both CC at ~5 V; comparator output indeterminate — does not matter

## ERC expectations

- Zero unconnected pins (label TX2/RX2 / SBU as NC)
- Zero missing power flag errors
- Deliberate "different net names" warning for Y-cap → suppress with a net tie footprint (`Mechanical:SolderJumper_2_Open` from the KiCad standard library; place it on the `GND_POE`–`GND` connection at C3)
- About 50–60 nets total — small project, ERC should be quick

## Style conventions

- **Reference designators grouped by sheet:** U1xx for sheet 01, etc. (helps BOM grouping)
- **Net classes** (assigned in `kicad_pro`):
  - `Default` — general signals
  - `USB3_SS` — 90 Ω diff (RTL8153B → USB-C TX1/RX1)
  - `ETHERNET_MDI` — 100 Ω diff (RJ45 ↔ RTL8153B)
  - `POE_PRIMARY` — wide tracks for primary side (≥ 0.5 mm)
  - `POWER_5V` — 5 V rail (≥ 0.4 mm to handle 2 A)

## Drawing order (suggested)

1. **Sheet 01** — RJ45 + MDI breakout
2. **Sheet 02** — biggest sheet, all the analog magic
3. **Sheet 03** — quick LDO sheet
4. **Sheet 04** — busy chip (RTL8153B has ~60 pins)
5. **Sheet 05** — USB-C wiring

Run ERC after each sheet to catch issues early.
