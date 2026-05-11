# Build Guide — Sheet 01: PoE Frontend

This document walks through filling in `hardware/01_PoE_Frontend.kicad_sch` in KiCad 8. The starter file already has all hierarchical labels positioned on the right side. You'll add the actual components on the left and wire them up.

## Before you start

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in KiCad 8.0 or newer.
2. In Eeschema, double-click the `01_PoE_Frontend` sheet symbol on the root sheet to descend into it.
3. You should see the hierarchical labels (MDI0+, MDI0-, ..., CHASSIS_GND) along the right edge.

## Goal

Build this circuit on Sheet 01:

```
                    Cable                                                 To other sheets
                      │                                                        │
                  ┌───┴────┐                                                   │
                  │ RJ45   │ pins 1,2     ┌──┐                                 │
                  │ +      │═════════════╞XR╪═MDI0±  →→→  hier_label MDI0±  ───┤
                  │ Mag    │ pins 3,6     ╧──╧                                 │
                  │ Jack   │═════════════╞XR╪═MDI1±  →→→  hier_label MDI1±  ───┤
   PoE switch  ──→│ J1     │ pins 4,5     ╧──╧                                 │
                  │        │═════════════╞XR╪═MDI2±  →→→  hier_label MDI2±  ───┤
                  │        │ pins 7,8     ╧──╧                                 │
                  │        │═════════════╞XR╪═MDI3±  →→→  hier_label MDI3±  ───┤
                  │        │              ╧──╧                                 │
                  │        │ ─ centre tap pair A ────→  hier_label PAIR_A_HI ──┤
                  │        │ ─ centre tap pair A ────→  hier_label PAIR_A_LO ──┤
                  │        │ ─ centre tap pair B ────→  hier_label PAIR_B_HI ──┤
                  │        │ ─ centre tap pair B ────→  hier_label PAIR_B_LO ──┤
                  │        │ ── LED LINK   ←←  hier_label LED_LINK ────────────┤
                  │        │ ── LED ACT    ←←  hier_label LED_ACT  ────────────┤
                  │ shield │                                                   │
                  └───┬────┘                                                   │
                      │                                                        │
                      └─→ hier_label CHASSIS_GND ──────────────────────────────┘

 Where ╞XR╪ represents one ESD/TVS array per MDI pair (4 pairs total, 2× NUP4202W1 chips).
```

## Step 1 — Place J1, the RJ45 magjack

KiCad's stock libraries don't include the exact Bel Fuse 0826-1G1T-DV-F symbol. Two options:

### Option A — Use KiCad stock RJ45 + separate magnetics (recommended for first pass)

1. Place `Connector:RJ45_LED_Shielded` from the symbol library at approx **(60, 70)** mm.
2. Place 4× `Transformer:Transformer_1P_2S` next to it (one per pair) — these represent the 4 pair-wise transformers inside the integrated jack. Position them at **(85, 50)**, **(85, 65)**, **(85, 80)**, **(85, 95)**.
3. Wire the 8 RJ45 contact pins (1–8) to the primary side of the corresponding transformer:
   - Pair A (RJ45 pin 1, 2) → Transformer 1 primary
   - Pair B (RJ45 pin 3, 6) → Transformer 2 primary
   - Pair C (RJ45 pin 4, 5) → Transformer 3 primary
   - Pair D (RJ45 pin 7, 8) → Transformer 4 primary
4. Set J1 reference to **J1**, value to **RJ45_MAG**, footprint to a Bel-Fuse-compatible 8-pin RJ45 footprint.

### Option B — Use a community symbol (cleaner, takes more setup)

1. Download the Bel Fuse 0826-1G1T-DV-F symbol from SnapEDA, Ultra Librarian, or KiCad's UVL.
2. Add it as a symbol library in **Preferences → Manage Symbol Libraries**.
3. Place it at **(60, 70)** mm. All pins (8 RJ45 contacts, 8 PHY-side, 4 center taps, 2 LEDs, shield) are on one component.
4. Set reference to **J1**.

**Either way:** The "secondary" / PHY-side of the magnetics should net to MDI0+/-, MDI1+/-, MDI2+/-, MDI3+/-.

## Step 2 — Add ESD protection (U101, U102)

Each NUP4202W1 protects 4 single-ended signals. Use one chip per pair of MDI differential pairs:

1. Place `Diode:NUP4202W1` (if available) or use 8× `Diode:TVS_Bidirectional` symbols at approx **(115, 50)** to **(115, 90)**.
2. Reference them **U101** (covers MDI0±, MDI1±) and **U102** (covers MDI2±, MDI3±).
3. Connect each MDI line through one TVS pin to GND (the array shares a common GND pin).

**Note:** TVS arrays go on the secondary side of the magnetics, between the magjack and the labels. Don't put them on the cable side — the magnetics already isolate.

## Step 3 — Wire to hierarchical labels

Draw wires from each MDI signal at the secondary side of magnetics, through the ESD array, all the way to the corresponding hierarchical label. The labels are pre-positioned at:

| Label | Position (mm) |
|---|---|
| MDI0+ | (180.34, 40.64) |
| MDI0- | (180.34, 45.72) |
| MDI1+ | (180.34, 50.80) |
| MDI1- | (180.34, 55.88) |
| MDI2+ | (180.34, 60.96) |
| MDI2- | (180.34, 66.04) |
| MDI3+ | (180.34, 71.12) |
| MDI3- | (180.34, 76.20) |

Use `W` to start a wire in Eeschema, click the symbol pin, then click each grid point until the wire touches the hierarchical label.

## Step 4 — Center taps to PAIR labels

Each transformer's primary side has a center tap (the midpoint of the cable-side winding). For 802.3 PoE, both Mode A (data pairs) and Mode B (spare pairs) carry power.

1. Tie the center taps of pair-set A's transformers (pairs A and B / pins 1-2 and 3-6) to a single net `PAIR_A`. Connect to both `PAIR_A_HI` and `PAIR_A_LO` labels — actually, separately route the (+) and (–) center taps of one diode bridge's input to PAIR_A_HI / PAIR_A_LO.
2. Same for pair-set B (pairs C and D / pins 4-5 and 7-8) → `PAIR_B_HI`, `PAIR_B_LO`.

**Sanity check:** Each pair-set in 802.3 PoE provides one polarity-arbitrary DC path. The Schottky bridges on Sheet 02 will rectify each pair-set's DC into a fixed-polarity rail.

## Step 5 — LEDs (LED_LINK, LED_ACT)

Most integrated mag jacks have built-in LED holders driven by the PHY:

1. The RTL8153B drives `LED_LINK` and `LED_ACT` from Sheet 04. Those nets arrive on this sheet via the corresponding hierarchical labels (note: they're typed `input` on Sheet 01, since the signal flows in from another sheet).
2. Wire `LED_LINK` and `LED_ACT` directly to the LED pins of J1.
3. The LED anodes (+) typically pull up to a sheet-local +3V3. Add a power flag if needed, plus current-limiting resistors (R101, R102 = 330 Ω) in series with each LED.

If your magjack doesn't have integrated LEDs, instead place 2× standalone LEDs near the RJ45 cutout in the enclosure (you'd add LED1, LED2 here and wire them to LED_LINK/LED_ACT through resistors).

## Step 6 — Chassis ground

1. Drag a wire from J1's shield pin to the `CHASSIS_GND` hierarchical label.
2. On Sheet 02, you'll add a 1 MΩ resistor || 1 nF/2 kV cap between CHASSIS_GND and circuit GND for ESD bleed (the Bob Smith termination handles common-mode coupling).

## Step 7 — Bob Smith termination

For unused common-mode coupling on the cable side, add a 75 Ω resistor on each pair's center tap to a common node, and a 1 kV cap from that node to chassis ground.

**Before adding manually**: read the magjack's datasheet — most integrated magjacks already have Bob Smith termination internal to the part. If so, skip this step (verify by checking the data­sheet's internal schematic).

## Step 8 — Run ERC

Tools → Electrical Rules Check (or `F8`).

Expected result: 0 errors, possibly 1–2 warnings about hierarchical labels not yet driven (which is fine — Sheet 04 will drive LED_LINK and LED_ACT once it's built).

If you see "unconnected pin" errors, those are usually:
- LED pins on the magjack that don't have current-limiting resistors yet (add them)
- Unused RJ45 shield pins or extra magnetic taps (mark with explicit `~No Connection` flags from the toolbar)

## Step 9 — Annotate and check footprints

1. Tools → Annotate Schematic — gives every component a unique reference (J1, U101, U102, R101, etc.)
2. Tools → Assign Footprints — pick the right physical footprint for each component:
   - J1 → corresponding 0826 / JK0-0177 footprint (download from manufacturer)
   - U101, U102 → SOT-23-6 (NUP4202W1 package)
   - R101, R102 → 0402 or 0603 SMD
3. Save and move on to Sheet 02.

## Common gotchas

- **Polarity of magnetics:** the dot on the transformer symbol matters. Cable side is the dotted side conventionally; PHY side is undotted. Get this wrong and the link won't establish.
- **Pair numbering:** "Pair 1" in some datasheets = MDI[0] in others. Stick to MDI[0..3] convention internally and map to RJ45 pins per the IEEE 802.3 1000BASE-T table:
  - MDI[0] = RJ45 pins 1,2 (BI_DA in 1000BT)
  - MDI[1] = RJ45 pins 3,6 (BI_DB)
  - MDI[2] = RJ45 pins 4,5 (BI_DC)
  - MDI[3] = RJ45 pins 7,8 (BI_DD)
- **Center-tap polarity:** The "+" of pair set A vs "-" depends on which RJ45 pin you treat as positive. PoE is polarity-insensitive precisely because of the diode bridges on Sheet 02 — but be consistent in labeling so the bridge wiring on Sheet 02 makes sense.

## When you're done

Sheet 01 is complete when:

- ✅ ERC passes (or only has expected warnings)
- ✅ All 15 hierarchical labels have wires connected to them
- ✅ Every component has a reference designator and footprint assigned
- ✅ The MDI signals come out the secondary (PHY) side of magnetics, never directly from RJ45 contacts
- ✅ Save, commit, push.

Then move on to `BUILD-SHEET-02.md` (PoE PD + Flyback Converter).
