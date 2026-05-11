# Build Guide — Sheet 02: PoE PD + Flyback Converter

This is the most critical sheet in the project. It handles the dangerous PoE voltage, the
isolation barrier, and power regulation. Take it slowly — one functional block at a time.

## Overview

```
  PAIR_A_HI ─┐
  PAIR_A_LO ─┤→ D1 (bridge) ─┐
  PAIR_B_HI ─┤               ├→ V_POE+ / V_POE-
  PAIR_B_LO ─┘→ D2 (bridge) ─┘    │
                                    │
                              Bulk caps + TVS
                                    │
                              FB1 (ferrite bead)
                                    │
                              Si3402-B (U1)
                              ┌─────┴──────┐
                              │  flyback   │───→ T1 primary
                              │  PWM/PD    │
                              └────────────┘
                                               T1 secondary
                                                    │
                                               D4 (rectifier)
                                                    │
                                  ╔═══════════════════╗
                              ═══ ║ ISOLATION BARRIER ║ ═══
                                  ╚═══════════════════╝
                                                    │
                                              C10–C13 (bulk)
                                                    │
                                              +5V → hier_label
                                                    │
                                    U7 (TL431) → U6 (PC817B)
                                    (voltage sense)  (optocoupler)
                                              │
                                        → Si3402-B FB pin
```

## Step 1 — Place the Schottky bridges (D1, D2)

Each DF06S is a 4-pin bridge rectifier handling one pair-set's PoE power.

1. Place `Diode:DF06S` (or `Diode:Bridge_Rectifier`) at approximately **(55, 52)** for D1 and **(55, 68)** for D2.
2. Connect inputs:
   - D1 AC pins → `PAIR_A_HI` and `PAIR_A_LO` hierarchical labels (left edge)
   - D2 AC pins → `PAIR_B_HI` and `PAIR_B_LO` hierarchical labels
3. Connect outputs:
   - D1 + D2 DC+ pins → tie together → net `V_POE+`
   - D1 + D2 DC- pins → tie together → net `GND_POE`
4. Set references: **D1**, **D2**.

## Step 2 — Primary bulk capacitors and TVS (C1, C2, D3)

Place as close as possible to the bridge outputs — this keeps the primary high-di/dt loop tight.

1. Place `Device:C` × 2 near the D1/D2 outputs:
   - **C1**: 10 µF / 100 V X7R 1210 — between `V_POE+` and `GND_POE`
   - **C2**: 47 µF / 100 V Al — between `V_POE+` and `GND_POE` (add a polarity marker)
2. Place `Device:D_TVS` for **D3** (SMAJ58A) between `V_POE+` and `GND_POE`, cathode to `V_POE+`.
3. Place `Device:Ferrite_Bead` for **FB1** in series on `V_POE+` between the bulk caps and the Si3402-B VDD pin. Value: 600 Ω @ 100 MHz, 3 A.

## Step 3 — Classification and detection resistors (R1, R2)

These tell the PSE what power class the PD is.

1. Place `Device:R` for **R1** (24.9 kΩ 1%): from Si3402-B RDET pin to `GND_POE`.
2. Place `Device:R` for **R2** (12.1 kΩ 1%): from Si3402-B RCLS pin to `GND_POE`.

**Class table** (for reference — R2 sets the class):

| Class | Max power at PD | RCLS (R2) value |
|---|---|---|
| 0 | 12.95 W (default, unclassified) | open (omit R2) |
| 1 | 3.84 W | 137 kΩ |
| 2 | 6.49 W | 75 kΩ |
| **3** | **12.95 W** | **12.1 kΩ ← we use this** |

> Note: Classes 0–3 are defined in IEEE 802.3af. Class 3 explicitly requests 12.95 W from the PSE; Class 0 also allows up to 12.95 W but is unclassified. Using Class 3 ensures managed switches reserve the full power budget for this port. Verify R2 against Si3402-B AN1004 Table 4 before ordering.

## Step 4 — Place Si3402-B (U1)

The Si3402-B is a single-chip 802.3af/at PoE PD controller with integrated 100 V MOSFET switch and flyback PWM controller.

1. Use the Si3402-B symbol from your manufacturer library (SnapEDA / Ultra Librarian / DigiKey SchemGen).
2. Place **U1** at approximately **(80, 65)** — roughly centered on the primary side.
3. Wire pins per the AN1004 Figure 11 reference design:
   - `VDD` → `V_POE+` (via FB1)
   - `RTN` → `GND_POE`
   - `RDET` → R1 → `GND_POE`
   - `RCLS` → R2 → `GND_POE`
   - `SW` → `V_SW` net → primary winding Pin 1 of T1
   - `FB` → collector of U6 (optocoupler, transistor side)
   - `COMP` → RC network (1 nF cap + 10 kΩ resistor to `GND_POE`) — per AN1004 Table 2
   - `GATE`, `SD`, `SYNC` → follow AN1004 recommendations (typically tie SD high through 100 kΩ)
   - `PWOK` → NC (or route to a test point)
4. Add decoupling: 100 nF 0402 X7R from VDD to GND_POE, placed < 2 mm from pin.

## Step 5 — Flyback transformer T1

T1 is the isolation barrier. Its physical placement splits the board into primary and secondary sides.

1. Use the Würth 750313638 symbol or a generic `Transformer:Transformer_1P_2S` placeholder.
2. Place **T1** straddling the isolation barrier line at approximately **(107, 65)**.
3. Primary winding connections:
   - Pin 1 (dot) → `V_SW` net (Si3402-B SW pin)
   - Pin 2 → `V_POE+` (return path via internal bypass cap — follow AN1004)
4. Secondary winding connections:
   - Pin 3 (dot) → `V_SEC_RAW+` net → D4 anode
   - Pin 4 → `GND_SEC`
5. Mark the transformer dot (phasing dot) correctly — this sets the flyback polarity.
   - Primary dot = Pin 1 (connected to switch)
   - Secondary dot = Pin 3

⚠️ **Important**: the exact pinout and turns ratio of T1 must match the AN1004 reference design. The Würth 750313638 has a 5:1 primary-to-secondary turns ratio. A different transformer requires recalculating R1_COMP and the feedback network.

## Step 6 — Draw the isolation barrier marker

Before placing secondary-side components, visually mark the isolation barrier on the schematic:

1. Draw a thick yellow dashed vertical line at x ≈ 110 mm. Use `Place → Graphical Lines` in Eeschema, set line style to dashed, width 0.5 mm, color yellow.
2. Add a text label: **"ISOLATION BARRIER — ≥ 4 mm PCB CREEPAGE"**
3. Add another label: **"GND_POE ≠ GND — Y-cap only bridge"**

This is a schematic annotation only; the actual PCB slot is drawn in the PCB editor.

## Step 7 — Secondary rectifier and bulk (D4, C10–C13)

Now working on the right side of the isolation barrier:

1. Place `Diode:D_Schottky` for **D4** (SS34) at approximately **(130, 60)`:
   - Anode → T1 secondary winding Pin 3 (via `V_SEC_RAW+`)
   - Cathode → `+5V` net
2. Place output bulk capacitors between `+5V` and `GND_SEC`:
   - **C10**: 220 µF / 16 V polymer at **(150, 60)**
   - **C11–C13**: 22 µF / 10 V X5R 1210 clustered around C10
3. Connect `GND_SEC` to T1 secondary Pin 4 and to negative terminals of all secondary caps.

> At this point `+5V` should be a well-defined net tied to the cathode of D4 and the positive terminal of all secondary caps.

## Step 8 — Y-cap (C3)

The Y-cap provides a high-frequency return path for common-mode noise across the isolation barrier.

1. Place `Device:C` for **C3** (1 nF / 2 kV rated):
   - One terminal → `GND_POE` (primary ground)
   - Other terminal → `GND_SEC` (secondary ground)
2. In the schematic, this creates a deliberate connection between two otherwise-isolated nets. Add a **Net Tie** symbol (KiCad: `Device:Net_Tie_2`) in series or add a note suppressing the ERC "different net" warning for this junction.
3. On the PCB, C3 must physically straddle the isolation cut slot and be rated for the full isolation voltage (the 2 kV cap handles PoE surge voltages with margin).

## Step 9 — Feedback network (U6, U7 + resistors)

This closes the regulation loop, keeping `+5V` stable as load current changes.

### TL431 voltage setting (U7)

Vout = 2.495 × (1 + R_UPPER / R_LOWER)

For 5.0 V output:
- 5.0 = 2.495 × (1 + R_UPPER / R_LOWER)
- R_UPPER / R_LOWER = 1.004 ≈ 1.0
- Use **R_UPPER = R_LOWER = 10 kΩ 1%** → Vout = 4.99 V ✓

1. Place `Device:Q_NMOS` or `Amplifier_DAC:TL431` for **U7** at **(155, 80)**:
   - REF pin → midpoint of R_UPPER / R_LOWER divider
   - R_UPPER (10 kΩ): from `+5V` to REF pin
   - R_LOWER (10 kΩ): from REF pin to `GND_SEC`
   - CATHODE → optocoupler U6 LED cathode
   - ANODE → `GND_SEC`

### Optocoupler (U6)

2. Place `Isolation:PC817x` for **U6** at **(145, 80)** — it straddles the isolation barrier:
   - Primary (LED) side:
     - Anode (Pin 1) → R_OPT (560 Ω) → `+5V`
     - Cathode (Pin 2) → U7 (TL431) cathode
   - Secondary (transistor) side:
     - Collector (Pin 4) → Si3402-B FB pin (crosses to primary side)
     - Emitter (Pin 3) → `GND_POE`

> The optocoupler physically straddles the isolation barrier on the PCB. Its LED pins are on the secondary side; its transistor pins are on the primary side.

3. Add 100 nF decoupling across the LED supply (Pin 1 to GND_SEC).
4. Add R_OPT = **560 Ω** 0402 in series with the LED anode.

## Step 10 — Snubber (across T1 primary)

Flyback converters produce a large voltage spike when the primary switch turns off (leakage inductance ringing). The snubber damps this.

1. Place a series RC: **220 Ω + 470 pF** (1 kV rated) in series between `V_POE+` and `V_SW`. Name this net `V_SW`.
2. Place between Pin 2 of T1 primary and the drain of the integrated switch (Si3402-B SW pin) — in parallel with the primary winding from VDD side to SW side.

## Step 11 — Wire the hierarchical labels

Connect the 6 hierarchical labels:
- Left: `PAIR_A_HI`, `PAIR_A_LO` → D1 AC inputs
- Left: `PAIR_B_HI`, `PAIR_B_LO` → D2 AC inputs
- Right: `+5V` → cathode of D4 / positive rail
- Right: `GND` → `GND_SEC` (secondary ground)

## Step 12 — Run ERC

Expected results:
- 0 errors ideally
- 1 "different net names connected" warning → the Y-cap C3 joining GND_POE and GND_SEC — suppress with a Net Tie footprint
- Possible "unconnected pin" warnings on Si3402-B if PWOK / SYNC / SD are not wired → add explicit NC flags

## ERC checklist before marking complete

- ✅ All 6 hierarchical labels have wires connected
- ✅ Both bridges (D1, D2) are fully wired
- ✅ V_POE+ and GND_POE are clearly separate nets from +5V and GND_SEC
- ✅ Isolation barrier marked with graphical line
- ✅ C3 Y-cap has a net tie symbol (no bare ERC error)
- ✅ All Si3402-B pins are either connected or explicitly NC
- ✅ Transformer dot notation is correct
- ✅ TL431 REF pin voltage divider calculates to ≈ 5.0 V
- ✅ Every component has Reference + Footprint assigned

## Gotchas

- **Transformer polarity**: getting the dots wrong makes the flyback not regulate. Primary dot to SW, secondary dot to D4 anode.
- **Optocoupler primary/secondary**: it's easy to place U6 with both sides on the same GND. Confirm the collector/emitter side is on `GND_POE` and the LED side is on `GND_SEC`.
- **RCLS vs RDET**: these are different pins. RDET sets the 25 kΩ detection signature (always 24.9 kΩ). RCLS is class-specific.
- **Compensation network**: wrong COMP values cause oscillation or sluggish regulation. Use AN1004 Table 2 values verbatim for the 750313638 transformer. Recalculate only if substituting a different transformer.
- **Two separate GND symbols**: use `GND_POE` power symbol on the primary side and `GND` (or `GND_SEC`) on the secondary side. Never connect them directly — only via C3 net tie.
