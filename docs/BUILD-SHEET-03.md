# Build Guide — Sheet 03: Bias Rails

This document walks through filling in `hardware/03_Bias_Rails.kicad_sch` in KiCad 8. The starter file has the four hierarchical labels positioned on the left and right edges. You'll place two LDOs, their decoupling caps, and PWR_FLAG symbols, then wire everything up.

## Before you start

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in KiCad 8.0 or newer.
2. In Eeschema, double-click the `03_Bias_Rails` sheet symbol on the root sheet.
3. You should see `+5V` and `GND` labels on the left edge and `+3V3` and `+1V0` labels on the right edge.

## Goal

```
         +5V (from Sheet 02)
          │
          ├──────────────────────────────────────────────────────────────────────────────────┐
          │                                                                                  │
          ▼                                                                                  ▼
    ┌──────────┐                                                                       ┌──────────┐
    │ U4       │ IN ← +5V      OUT ──────────────────► hier_label +3V3 → Sheet 04     │ U5       │
    │ AP2112K  │                                                                       │ RT9013   │
    │ 3.3 V    │ GND ──►GND    decoupling: C301 (IN), C302 (OUT)                      │ 1.0 V    │
    └──────────┘                                                                       └──────────┘
                                                                                              │
                                                        OUT ─────────────► hier_label +1V0 ◄─┘
                                                        decoupling: C303 (IN), C304 (OUT)

    PWR_FLAG → +3V3 net (one occurrence in this project)
    PWR_FLAG → +1V0 net (one occurrence in this project)
         GND → hier_label GND
```

## Step 1 — Place U4 (AP2112K-3.3, 3.3 V LDO)

1. Search the symbol library for `Regulator_Linear:AP2112K-3.3` (or `Regulator_Linear:XC6206xxx` as a placeholder if not available).
2. Place **U4** at approximately **(80, 70)** mm.
3. Wire pins:
   - IN → `+5V` power symbol
   - GND → `GND` power symbol
   - EN → `+5V` via a 100 kΩ pull-up resistor (tie EN high to enable the LDO unconditionally)
   - OUT → net `+3V3`
4. Set reference **U4**, value **AP2112K-3.3TRG1**.

## Step 2 — Add U4 decoupling caps (C301, C302)

1. Place `Device:C` for **C301** (1 µF / 10 V X5R 0402) between `+5V` and `GND`, within 2 mm of U4 IN pin.
2. Place `Device:C` for **C302** (1 µF / 10 V X5R 0402) between `+3V3` and `GND`, within 2 mm of U4 OUT pin.

These are the minimum stable-operation caps per AP2112 datasheet. Values below 1 µF risk instability.

## Step 3 — Place U5 (RT9013-10GB, 1.0 V LDO)

1. Search the symbol library for `Regulator_Linear:RT9013` (or use a generic `Regulator_Linear:LDO_SOT23-5` placeholder).
2. Place **U5** at approximately **(80, 110)** mm.
3. Wire pins:
   - IN → `+5V` power symbol
   - GND → `GND` power symbol
   - EN → `+5V` via a 100 kΩ pull-up resistor (tie EN high)
   - OUT → net `+1V0`
4. Set reference **U5**, value **RT9013-10GB**.

## Step 4 — Add U5 decoupling caps (C303, C304)

1. Place **C303** (1 µF / 10 V X5R 0402) on U5 IN, within 2 mm of pin.
2. Place **C304** (1 µF / 10 V X5R 0402) on U5 OUT, within 2 mm of pin.

## Step 5 — Add PWR_FLAG symbols

KiCad ERC requires at least one `PWR_FLAG` on every power net that has no explicit power source symbol. The `+3V3` and `+1V0` nets get their power from U4 and U5 respectively, but ERC doesn't know that without a flag.

1. From the symbol library, add `Power:PWR_FLAG` to the `+3V3` net — place it next to C302 or U4 OUT.
2. Add a second `Power:PWR_FLAG` to the `+1V0` net — place it next to C304 or U5 OUT.

**Do not** place PWR_FLAG on `+3V3` or `+1V0` anywhere else in the project; having more than one on the same net is harmless but confusing.

## Step 6 — Wire hierarchical labels

All four labels are pre-positioned in the starter file:

| Label | Location | Connect to |
|---|---|---|
| `+5V` | left edge | U4 IN rail, U5 IN rail |
| `GND` | left edge | GND power symbols throughout |
| `+3V3` | right edge | U4 OUT net |
| `+1V0` | right edge | U5 OUT net |

Draw short wires from each rail net to the corresponding label. Both IN rail connections (`+5V`) can share a single horizontal bus; tap each LDO IN pin from that bus.

## Step 7 — Run ERC

Expected result: **0 errors, 0 warnings**.

If you see:
- `"Pin unconnected"` on EN → confirm EN resistor is wired to `+5V`
- `"Missing power driver"` on `+3V3` or `+1V0` → PWR_FLAG is missing or misplaced
- `"Pin connected to some unconnected pins"` → a dangling wire end somewhere; chase it down

## ERC checklist before marking complete

- ✅ U4 and U5 placed, all pins connected or NC-flagged
- ✅ All 4 hierarchical labels have wires connected
- ✅ C301–C304 decoupling caps present on IN and OUT of each LDO
- ✅ EN pulled high on both LDOs
- ✅ PWR_FLAG on `+3V3` — exactly one in the project
- ✅ PWR_FLAG on `+1V0` — exactly one in the project
- ✅ Every component has Reference + Footprint assigned

## Annotate and check footprints

1. **Tools → Annotate Schematic** — assigns U4, U5, C301–C304.
2. **Tools → Assign Footprints**:
   - U4 → `Package_TO_SOT_SMD:SOT-23-5` (AP2112K comes in SOT-23-5)
   - U5 → `Package_TO_SOT_SMD:SOT-23-5` (RT9013 is also SOT-23-5)
   - C301–C304 → `Capacitor_SMD:C_0402_1005Metric`

## Gotchas

- **LDO stability**: the AP2112 and RT9013 are both capacitor-stable designs. Minimum output cap is 1 µF. Using less risks oscillation that can corrupt RTL8153B.
- **EN pull-up value**: 100 kΩ is fine. Do not short EN directly to VIN without a resistor — some LDOs draw significant current through EN on start-up.
- **PWR_FLAG location**: place it directly on the output net (e.g., the same wire as U4 OUT), not on the `+5V` input net. ERC needs to see the flag on `+3V3` and `+1V0`, not on `+5V` (Sheet 02 already flags `+5V`).
- **Footprint mismatch**: the RT9013-10GB is a fixed-output LDO (no feedback resistors). The generic `LDO_SOT23-5` symbol may have an extra ADJ/FB pin — mark it NC if so.

## When you're done

Sheet 03 is complete when:

- ✅ ERC passes with 0 errors
- ✅ All 4 hierarchical labels have wires
- ✅ `+3V3` and `+1V0` each have a PWR_FLAG
- ✅ Every component has a reference designator and footprint assigned
- ✅ Save, commit, push

Move on to `BUILD-SHEET-04.md` (RTL8153B Bridge).
