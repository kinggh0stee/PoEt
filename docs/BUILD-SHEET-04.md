# Build Guide — Sheet 04: RTL8153B Bridge

This is the most component-dense sheet in the project. The RTL8153B is a ~60-pin QFN with six power domains, multiple decoupling requirements, a crystal, an EEPROM, and two SuperSpeed differential pairs. Work one functional block at a time and run ERC after each block.

## Before you start

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in KiCad 8.0 or newer.
2. Descend into the `04_RTL8153B_Bridge` sheet.
3. You should see power labels (+5V, +3V3, +1V0, GND) and MDI labels on the left edge, and USB SS + LED labels on the right edge.
4. **Obtain the RTL8153B reference design** from Realtek (available via Realtek's website or distributors). The application note covers exact decoupling values, strap resistor tables, and crystal loading. This guide describes the structure; the reference design provides the specific values.

## Goal

```
  +5V ──────────────────────────────────────────────────────────────► VBUS (sense)
  +3V3 ─────────────────────────────────────────────────────────────► VDD33 pins (I/O ring)
  +1V0 ─────────────────────────────────────────────────────────────► VDD10 pins (core)
  GND ──────────────────────────────────────────────────────────────► GND pins

  MDI0± ─► ESD(U101) ───────────────────────────────────────────────► MDI_D+/- pins
  MDI1± ─► ESD(U101) ───────────────────────────────────────────────►    (U2 RTL8153B)
  MDI2± ─► ESD(U102) ───────────────────────────────────────────────►
  MDI3± ─► ESD(U102) ───────────────────────────────────────────────►
                                                                         │
                                         Y1 (25 MHz) ─────────────────► XTALIN / XTALOUT
                                         U3 (EEPROM) ─────────────────► EECS/EECLK/EEDI/EEDO
                                         SW1 (reset) ─────────────────► RST_N
                                         LED1 (green) ◄───────────────── LED0
                                         LED2 (yellow) ◄──────────────── LED1
                                                                         │
                                              USB_SSTX± ◄───────────────── SSTXP / SSTXN
                                              USB_SSRX± ◄───────────────── SSRXP / SSRXN
                                              USB_DP ◄─────────────────── DP
                                              USB_DM ◄─────────────────── DM
```

## Step 1 — Place U2 (RTL8153B)

The RTL8153B is available as a QFN-64 (8×8 mm, 0.5 mm pitch) or QFN-48 depending on the variant. Verify the exact package for your part number (RTL8153B-**VC**-CG = QFN-64).

1. Download the RTL8153B symbol from SnapEDA, Ultra Librarian, or build it from the datasheet pin list.
2. Place **U2** at approximately **(100, 80)** mm — center of the sheet.
3. Do not wire any pins yet. Just get the symbol positioned with room on all four sides for decoupling caps, the crystal, and the EEPROM.

## Step 2 — Add power domain decoupling (C22–C40)

The RTL8153B has approximately 15 power pins across three voltage domains. Each pin gets its own 100 nF bypass cap.

1. For every `VDD33` pin: place `Device:C` (100 nF / 10 V X7R 0402) between that pin and `GND`, within 2 mm of the pin.
2. For every `VDD10` pin: same as above.
3. For the `VBUS` pin: place one 100 nF cap and wire it to the `+5V` net (VBUS is a sense input on this chip; it sees the 5 V rail but does not source current through this pin).
4. Label all caps sequentially as **C22, C23, C24, …** up to roughly **C40** — the exact count depends on your symbol's pin grouping.

> The reference design shows which pins are paired internally and can share a single cap; follow it. As a safe default, one cap per pin is always correct.

## Step 3 — Add bulk decoupling (C41–C44)

In addition to the per-pin 100 nF caps, add four 10 µF X5R caps as bulk reservoir capacitors:

1. **C41**: 10 µF / 10 V X5R 0603 on the `+3V3` rail, within 5 mm of U2.
2. **C42**: 10 µF / 10 V X5R 0603 on the `+1V0` rail, within 5 mm of U2.
3. **C43**: 10 µF / 10 V X5R 0603 on the `+5V` (VBUS sense) rail, within 5 mm of U2.
4. **C44**: 10 µF / 10 V X5R 0603 on the `+3V3` rail (second bulk cap; RTL8153B VDD33 can benefit from extra bulk).

## Step 4 — Strap and bias resistors (R20–R25)

The RTL8153B has several strap pins that select operating modes at power-on. The values are specified in the Realtek reference design's strap resistor table.

1. Place `Device:R` for each strap resistor. Typical pins include:
   - USB speed straps (e.g., USB 3.0 vs 2.0 fallback behaviour)
   - LED polarity strap
   - EEPROM presence strap
2. Reference them **R20, R21, R22, R23, R24, R25** (adjust count to match actual strap pin count in your symbol).
3. Connect each as specified by the reference design — strap to GND or VDD33 via the prescribed resistor value.

**Important:** the strap values are sampled at RST_N de-assertion. Get them wrong and the chip may not enumerate, boot the wrong USB speed, or skip EEPROM loading.

## Step 5 — Crystal oscillator (Y1, C20, C21)

The RTL8153B requires a 25 MHz reference for its internal PLL.

1. Place `Device:Crystal` for **Y1** (25 MHz ±25 ppm, 5×3.2 mm or 3.2×2.5 mm) at approximately **(80, 85)** — between U2 and the left edge, near the XTALIN/XTALOUT pins.
2. Wire:
   - Y1 pin 1 (one terminal) → U2 XTALIN
   - Y1 pin 2 (other terminal) → U2 XTALOUT
3. Place `Device:C` for **C20** (18 pF NP0 0402) between XTALIN and GND.
4. Place `Device:C` for **C21** (18 pF NP0 0402) between XTALOUT and GND.

> **Load cap sizing:** the effective crystal load capacitance is `CL = (C1 × C2)/(C1 + C2) + C_stray`. With C1 = C2 = 18 pF and C_stray ≈ 3 pF (PCB), CL ≈ 12 pF. So 18 pF caps suit a crystal with CL = 12 pF. Adjust if your chosen crystal specifies a different CL (e.g., 9 pF crystal → use 12 pF load caps). The Realtek reference design's values are authoritative — use them over this approximation.

Schematic annotation notes for PCB layout:
- Place Y1 as close to XTALIN/XTALOUT as possible.
- Add a GND guard ring around Y1 in the PCB editor.
- No other traces are allowed to pass under Y1.

## Step 6 — EEPROM (U3)

The 93C46 stores VID, PID, MAC, and strap defaults. Without it, the RTL8153B uses silicon defaults (0x0BDA / 0x8153, random MAC). With it, you can set a unique MAC and descriptors.

1. Place `Memory_EEPROM:93LC46` (or `Memory_EEPROM:93C46` — 3-wire MicroWire variant) for **U3** at approximately **(130, 60)** — near U2's EEPROM interface pins.
2. Wire:
   - U3 CS  → U2 EECS
   - U3 CLK → U2 EECLK
   - U3 DI  → U2 EEDI
   - U3 DO  → U2 EEDO
   - U3 VCC → `+3V3`
   - U3 GND → `GND`
   - U3 ORG → `GND` (selects 16-bit word mode; RTL8153B reads EEPROM as 64×16-bit words)
3. Add 100 nF decoupling between U3 VCC and GND.
4. **Add 4 test points** (TP1–TP4) on CS, CLK, DI, DO — these allow in-circuit EEPROM programming after board assembly. Name them explicitly; they're how you write the MAC address per `firmware/eeprom-image.md`.

## Step 7 — Reset circuit (SW1)

1. Place `Switch:SW_Push` for **SW1** at approximately **(130, 100)**.
2. Wire:
   - One side → U2 RST_N pin
   - Other side → `GND`
3. Add a 10 kΩ pull-up resistor from RST_N to `+3V3` (keeps RST_N high normally; pressing SW1 pulls it low to reset).
4. Add a 100 nF cap from RST_N to GND for debouncing.

## Step 8 — LED drivers (LED1, LED2, R101, R102)

The RTL8153B drives LEDs with open-drain outputs (LED0 = link, LED1 = activity). Each output sinks current; the LED anode is pulled up to +3V3 through a current-limiting resistor.

1. Place `Device:R` for **R101** (330 Ω 0402) between `+3V3` and a new net `LED_LINK_ANODE`.
2. Place `Device:LED` for **LED1** (green 0603):
   - Anode → `LED_LINK_ANODE` net (from R101)
   - Cathode → U2 LED0 pin → `LED_LINK` hierarchical label (right edge)
3. Place `Device:R` for **R102** (330 Ω 0402) between `+3V3` and `LED_ACT_ANODE`.
4. Place `Device:LED` for **LED2** (yellow 0603):
   - Anode → `LED_ACT_ANODE` net (from R102)
   - Cathode → U2 LED1 pin → `LED_ACT` hierarchical label (right edge)

The circuit is: `+3V3 → R101 → LED1 → U2 LED0 (open-drain)`. When U2 LED0 pulls low, ~9 mA flows through LED1 (3.3 V − 2.0 V forward drop) / 330 Ω ≈ 4 mA — comfortably within the RTL8153B LED sink spec.

> The `LED_LINK` and `LED_ACT` labels carry the RTL8153B open-drain signals to Sheet 01, where they connect to J1's integrated LED holder pins (cathode side). On Sheet 01, J1's LED holder anodes require their own pull-up; mark J1 LED pins with NC flags if not using J1's LED holders.

## Step 9 — MDI connections

The MDI signals arrive from Sheet 01 already ESD-protected (U101/U102 on Sheet 01). On this sheet, connect them directly to U2.

1. Wire the left-side hierarchical labels to U2 MDI pins:
   - `MDI0+` → U2 MDI_DA+ (or equivalent pin name per symbol)
   - `MDI0-` → U2 MDI_DA-
   - `MDI1+` → U2 MDI_DB+
   - `MDI1-` → U2 MDI_DB-
   - `MDI2+` → U2 MDI_DC+
   - `MDI2-` → U2 MDI_DC-
   - `MDI3+` → U2 MDI_DD+
   - `MDI3-` → U2 MDI_DD-

The pair-to-pin mapping follows 1000BASE-T:
- MDI[0] = BI_DA (pins 1, 2 of RJ45)
- MDI[1] = BI_DB (pins 3, 6)
- MDI[2] = BI_DC (pins 4, 5)
- MDI[3] = BI_DD (pins 7, 8)

## Step 10 — USB SuperSpeed outputs

1. Wire U2 SSTXP → `USB_SSTX+` label (right edge).
2. Wire U2 SSTXN → `USB_SSTX-` label.
3. Wire U2 SSRXP → `USB_SSRX+` label.
4. Wire U2 SSRXN → `USB_SSRX-` label.
5. Wire U2 DP → `USB_DP` label.
6. Wire U2 DM → `USB_DM` label.

> The AC-coupling caps (C15, C16) for the SSTX pair are on Sheet 05. Do not add them here.

## Step 11 — Handle unused pins

The RTL8153B has additional pins that may not be needed in this design:
- Any unused GPIO/strap pins: tie to `GND` via 100 kΩ or add explicit NC flags, per reference design
- Internal test pins: NC flag
- Any RGMII/MII pins (if your symbol includes them for the Gig MII variant): NC flag

**Every pin must be either connected or explicitly NC-flagged.** ERC will fail on any floating pin.

## Step 12 — Wire remaining hierarchical labels

- Left: `+5V` → VBUS sense rail + decoupling
- Left: `+3V3` → VDD33 rail + decoupling
- Left: `+1V0` → VDD10 rail + decoupling
- Left: `GND` → GND power symbol throughout
- Right: all USB and LED labels should already be wired from Steps 8–10

## Step 13 — Run ERC

Expected results:
- 0 errors
- Possible warnings about undriven hierarchical labels if the project is only partially complete (normal at this stage — Sheets 01/03 haven't had all components placed yet)

## ERC checklist before marking complete

- ✅ All 20 hierarchical labels have wires connected
- ✅ U2 (RTL8153B): all pins connected or NC-flagged
- ✅ U3 (EEPROM): CS/CLK/DI/DO connected; ORG tied; 4 test points added
- ✅ Y1 crystal + C20/C21 load caps wired
- ✅ SW1 reset + pull-up + debounce cap wired
- ✅ LED1, LED2 anodes to +3V3; cathodes to LED0/LED1 pins; LED_LINK/LED_ACT labels connected
- ✅ MDI0–3 pairs all wired to correct U2 MDI pins
- ✅ USB SS and D+/D- labels wired to correct U2 pins
- ✅ Every component has Reference + Footprint assigned

## Annotate and check footprints

1. **Tools → Annotate Schematic**
2. **Tools → Assign Footprints**:
   - U2 → `Package_DFN_QFN:QFN-64-1EP_8x8mm_P0.5mm_EP5.4x5.4mm` (verify against RTL8153B package drawing)
   - U3 → `Package_TO_SOT_SMD:SOT-23-6` (93LC46 in SOT-23 is most common for this project)
   - Y1 → `Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm`
   - SW1 → `Button_Switch_SMD:SW_SPST_TL3342` (or equivalent 6×6 SMD tact)
   - C20, C21 → `Capacitor_SMD:C_0402_1005Metric`
   - C22–C40 → `Capacitor_SMD:C_0402_1005Metric`
   - C41–C44 → `Capacitor_SMD:C_0603_1608Metric`
   - LED1, LED2 → `LED_SMD:LED_0603_1608Metric`
   - R20–R25, pull-up and debounce → `Resistor_SMD:R_0402_1005Metric`

## Gotchas

- **QFN thermal pad**: the RTL8153B exposed pad must be connected to GND via via stitching. Most QFN footprints include this; verify.
- **Crystal guard ring**: failure to guard the crystal on the PCB results in noise coupling from USB switching. The crystal annotation in the schematic serves as a reminder — enforce it in the PCB editor with a courtyard keep-out under Y1 and a GND copper pour ring.
- **Strap resistors**: they must be placed before power-on. A missing strap can permanently misconfigure the chip until it is power-cycled.
- **EEPROM ORG pin**: if the 93LC46 symbol you use has an ORG pin, tie it to GND (selects 16-bit word mode, as required by RTL8153B). Tying ORG to VCC selects 8-bit byte mode, which the RTL8153B does not use for EEPROM access. Leaving ORG floating causes undefined behaviour.
- **LED polarity**: the RTL8153B LED outputs sink current (open-drain). Anode to +3V3, cathode to LED0/LED1 — not the other way around.
- **MDI differential pair names**: different RTL8153B symbols use different pin names (BI_DA+/BI_DA-, MDI0+/MDI0-, RXDP0/RXDM0…). Match them to the pinout table in the datasheet, not the label. MDI[0] = 1000BASE-T Pair A = RJ45 pins 1, 2.

## When you're done

Sheet 04 is complete when:

- ✅ ERC passes (or only has expected cross-sheet warnings)
- ✅ All 20 hierarchical labels have wires connected
- ✅ Every component has a reference designator and footprint assigned
- ✅ Save, commit, push

Move on to `BUILD-SHEET-05.md` (USB-C Connector) — the final sheet.
