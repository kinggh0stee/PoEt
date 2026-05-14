# Build Guide — Sheet 05: USB-C Connector

This is the last sheet. It terminates all the signals from the rest of the project at the physical USB-C receptacle. The connector wiring requires careful attention to which pins get which signals, which are shorted together, and which are left NC.

## Before you start

1. Open `hardware/PoE-USBC-Gigabit.kicad_pro` in KiCad 8.0 or newer.
2. Descend into the `05_USBC_Connector` sheet.
3. You should see `+5V`, `GND`, `USB_SSTX+`, `USB_SSTX-`, `USB_SSRX+`, `USB_SSRX-`, `USB_DP`, and `USB_DM` labels on the left edge. There are no right-side outputs — J2 is the signal terminus.

## Goal

```
  +5V ──► F1 (2 A PPTC) ──────────────────────────────────────────► VBUS (A4, A9, B4, B9)
                                  C11 ─┐                                     │
                                  C12 ─┤ ← bulk at VBUS pads             22Ω (PCB trace only)
                                  C13 ─┤
                                  C14 ─┘

  GND ────────────────────────────────────────────────────────────► GND (A1, A12, B1, B12)

                                  R10 (22 kΩ) ────────────────────► CC1 (A5)
                                  R11 (22 kΩ) ────────────────────► CC2 (B5)
                                              (pull to +5V → advertise 1.5 A source)

  USB_SSTX+ ──► C15 (100 nF) ──┐
  USB_SSTX- ──► C16 (100 nF) ──┤
                                 ├──► U11 (PI3DBS12412A SS mux) ──► SEL=0: TX1+ (A2), TX1- (A3)
                                 │                                  SEL=1: TX2+ (A10), TX2- (A11)
  USB_SSRX+ ◄──────────────────┐│
  USB_SSRX- ◄──────────────────┼┤ U11 ◄── SEL=0: RX1+ (B10), RX1- (B11)
                                 │         SEL=1: RX2+ (B2),  RX2- (B3)

                 CC1 ──► R10 (22 kΩ) ──► +5V
                 CC2 ──► R11 (22 kΩ) ──► +5V
                 CC1 ──► U12 IN+  ┐
                 CC2 ──► U12 IN-  ├──► U12 OUT ──► R12 (10 kΩ to +3V3) ──► U11 SEL
                                   └  (LMV321 comparator)

  ESD at connector (between U11 and J2):
    U10a: TX1+, TX1-, RX1+, RX1-
    U10b: TX2+, TX2-, RX2+, RX2-

  USB_DP ─────────────────────── U10c ESD ────────────────────────► D+ A6 + B6 (shorted)
  USB_DM ─────────────────────── U10c ESD ────────────────────────► D- A7 + B7 (shorted)

                                              SBU1, SBU2               → NC
                                              SHIELD / shell            → GND (or CHASSIS_GND)
```

## Step 1 — Place J2 (USB-C receptacle)

The connector is the anchor of this sheet. Place it first.

1. Download the footprint and symbol for **GCT USB4105-GF-A** (mid-mount, through-hole pins on the shell, SMT signal pads) from SnapEDA or GCT's website. Alternatively use **Amphenol 12401610E412A**.
2. Place **J2** at approximately **(150, 80)** mm — right side of the sheet, leaving room on the left for the signal chain.
3. At this stage, just identify each pin group. The 24-signal pins in the USB-C spec are:

| Group | Pins | Signal |
|---|---|---|
| VBUS | A4, A9, B4, B9 | +5 V power |
| GND | A1, A12, B1, B12 | Ground |
| TX1 | A2, A3 | SuperSpeed TX — orientation 1 (via U11 mux) |
| RX1 | B10, B11 | SuperSpeed RX — orientation 1 (via U11 mux) |
| TX2 | A10, A11 | SuperSpeed TX — orientation 2 (via U11 mux) |
| RX2 | B2, B3 | SuperSpeed RX — orientation 2 (via U11 mux) |
| D+ | A6, B6 | USB 2.0 D+ |
| D- | A7, B7 | USB 2.0 D- |
| CC1 | A5 | Configuration channel 1 — Rp pull-up + comparator tap |
| CC2 | B5 | Configuration channel 2 — Rp pull-up + comparator tap |
| SBU1 | A8 | Sideband use (NC) |
| SBU2 | B8 | Sideband use (NC) |

4. Set reference **J2**, value **USB4105-GF-A** (or whichever part you chose).

## Step 2 — VBUS rail and PPTC fuse (F1, C11–C14)

The VBUS rail delivers 5 V from the PoE secondary rail to the host.

1. Place `Device:Polyfuse` (or `Device:Fuse`) for **F1** (2 A / 6 V PPTC, 1206 footprint) at approximately **(60, 70)**.
   - One side → `+5V` hierarchical label
   - Other side → net `VBUS` (internal to this sheet)
2. Bus all four J2 VBUS pins (A4, A9, B4, B9) together → `VBUS` net.
3. Add bulk capacitors at the VBUS node, as close to J2 pads as possible:
   - **C11**: 22 µF / 10 V X5R 1210
   - **C12**: 22 µF / 10 V X5R 1210
   - **C13**: 22 µF / 10 V X5R 1210
   - **C14**: 100 nF / 16 V X7R 0402 (high-frequency bypass)
   All connected between `VBUS` and `GND`.

## Step 3 — GND

Bus all four J2 GND pins (A1, A12, B1, B12) together and connect to the `GND` hierarchical label. Wire the connector shell / shield pins to GND as well (or to `CHASSIS_GND` from Sheet 01 if your connector symbol exposes them separately — the distinction matters for EMC, but GND is acceptable for a first pass).

## Step 4 — CC pull-up resistors and orientation comparator (R10, R11, U12, R12)

### CC Rp resistors
These tell the host that this port is a USB-C power source advertising 1.5 A.

1. Place `Device:R` for **R10** (22 kΩ 1% 0402):
   - One end → `+5V`
   - Other end → J2 CC1 (A5) and U12 IN+
2. Place `Device:R` for **R11** (22 kΩ 1% 0402):
   - One end → `+5V`
   - Other end → J2 CC2 (B5) and U12 IN-

> A 22 kΩ Rp to 5 V = USB-C "Type-C Current" advertisement of 1.5 A (7.5 W). See design-spec.md §1.3.

### Orientation comparator
When a cable is plugged in, the active CC pin is pulled to ≈ 0.9 V by the host's Rd (5.1 kΩ to GND); the idle CC stays at ≈ 5 V through its Rp. The comparator detects which CC is active.

3. Place `Comparator:LMV321` for **U12** (SOT-23-5):
   - IN+ (pin 3) → CC1 net
   - IN- (pin 2) → CC2 net
   - V+ (pin 5) → `+5V`
   - GND (pin 1) → `GND`
   - OUT (pin 4) → net `SS_SEL`
4. Place `Device:R` for **R12** (10 kΩ 0402):
   - One end → `+3V3` (global power net)
   - Other end → `SS_SEL` net
   This pull-up converts the open-drain comparator output to a clean logic level for U11 SEL.

**Comparator logic:**
- CC1 < CC2 (orientation 1 cable plugged in): OUT → LOW → SEL = 0
- CC1 > CC2 (orientation 2): OUT → HIGH → SEL = 1
- No cable (both CC at ~5 V): output indeterminate — U11 can be in either state; no cable means no SS link regardless

## Step 5 — SS mux (U11)

The mux sits between the AC-coupled SSTX pair and the connector, routing SS signals to the correct J2 pins based on cable orientation.

1. Place **U11** (PI3DBS12412A, UFQFN-24, or FSUSB43L10X as an alternative) at approximately **(100, 80)**.
2. Wire inputs (from the RTL8153B side, after C15/C16):
   - SSTX+ → U11 TX_A input
   - SSTX- → U11 TX_B input
   - U11 RX_A output → SSRX+
   - U11 RX_B output → SSRX-
3. Wire outputs toward J2 (through ESD arrays added in Step 6):
   - U11 port 1 TX+/TX- → toward J2 TX1 (A2, A3)
   - U11 port 1 RX+/RX- → from J2 RX1 (B10, B11)
   - U11 port 2 TX+/TX- → toward J2 TX2 (A10, A11)
   - U11 port 2 RX+/RX- → from J2 RX2 (B2, B3)
4. Wire `SS_SEL` → U11 SEL pin.
5. Add 100 nF bypass cap between U11 VCC and GND, and connect U11 VCC to `+3V3`.
6. Connect U11 GND pins to `GND`.

> The PI3DBS12412A is a 4-channel 2:1 mux; one IC handles all four SS lines (SSTX+, SSTX-, SSRX+, SSRX−) with the same SEL. Verify the exact pinout from the Diodes Inc. datasheet — the port numbering and enable pins vary by package variant.

## Step 6 — ESD protection (U10a, U10b, U10c)

Place ESD arrays on the connector side of U11 (between mux outputs and J2 pins). Three NUP4202W1 ICs cover all eight SS lines plus D+/D-.

1. Place **U10a** (NUP4202W1, SOT-23-6) at approximately **(125, 65)**:
   - Lines → TX1+ (A2), TX1- (A3), RX1+ (B10), RX1- (B11)
   - GND → `GND`
2. Place **U10b** (NUP4202W1) at approximately **(125, 95)**:
   - Lines → TX2+ (A10), TX2- (A11), RX2+ (B2), RX2- (B3)
   - GND → `GND`
3. Place **U10c** (NUP4202W1) at approximately **(125, 110)**:
   - Lines → USB_DP, USB_DM (and two spare lines → NC)
   - GND → `GND`

## Step 7 — AC-coupling caps on SSTX (C15, C16)

AC-coupling caps sit upstream of U11 (between the hierarchical labels and the mux input). One set of caps handles both orientations.

1. Place `Device:C` for **C15** (100 nF / 16 V X7R 0402) in series on the `USB_SSTX+` line, between the hierarchical label and U11 TX input.
2. Place `Device:C` for **C16** (100 nF / 16 V X7R 0402) in series on the `USB_SSTX-` line, same placement.

**RX pair (USB_SSRX±) has no AC-coupling caps** — the RTL8153B has internal DC blocking on its RX inputs.

## Step 8 — Wire SuperSpeed signals to J2

1. U11 port 1 TX+ → U10a → J2 TX1+ (A2)
2. U11 port 1 TX- → U10a → J2 TX1- (A3)
3. J2 RX1+ (B10) → U10a → U11 port 1 RX+
4. J2 RX1- (B11) → U10a → U11 port 1 RX-
5. U11 port 2 TX+ → U10b → J2 TX2+ (A10)
6. U11 port 2 TX- → U10b → J2 TX2- (A11)
7. J2 RX2+ (B2) → U10b → U11 port 2 RX+
8. J2 RX2- (B3) → U10b → U11 port 2 RX-

## Step 9 — Wire USB 2.0 D+/D- to J2

For USB 2.0 to work in both plug orientations, both the A-side and B-side D+/D- pins are connected together.

1. `USB_DP` → J2 A6 and J2 B6 (short A6 and B6 together at the connector pads — use a net junction or a short wire segment)
2. `USB_DM` → J2 A7 and J2 B7 (same, short A7 and B7 together)

This means that regardless of plug orientation, D+ always reaches the data lines. SuperSpeed only works in one orientation (TX1/RX1 path), but USB 2.0 enumeration works both ways — the device will always appear to the host even if SS doesn't train.

## Step 10 — Mark unused pins NC

KiCad ERC will flag any unconnected pins as errors. Only SBU pins are NC in this design:

- J2 SBU1 (A8), SBU2 (B8) — NC

TX2/RX2 are now wired through U11 — do not add NC flags to them.

## Step 11 — Wire hierarchical labels

All eight input labels are on the left edge of the sheet:

| Label | Connect to |
|---|---|
| `+5V` | F1 input; R10/R11 pull-ups |
| `GND` | GND bus (J2 GND pins, capacitor negatives, U11/U12 GND) |
| `USB_SSTX+` | C15 input (then to U11 TX input) |
| `USB_SSTX-` | C16 input (then to U11 TX input) |
| `USB_SSRX+` | U11 RX output (no cap) |
| `USB_SSRX-` | U11 RX output (no cap) |
| `USB_DP` | U10c → J2 A6 + B6 (shorted) |
| `USB_DM` | U10c → J2 A7 + B7 (shorted) |

## Step 12 — Run ERC

Expected results:
- 0 errors
- 0 warnings (if all NC flags are placed correctly)

If you see:
- `"Pin unconnected"` on SBU pins → add No-Connect flags
- `"Pin unconnected"` on TX2/RX2 → these should be wired through U11, not NC
- `"Wire not connected"` → chase down dangling wire ends at D+ / D- junction (the short between A and B pads can look like an unconnected wire end)

## ERC checklist before marking complete

- ✅ All 8 hierarchical labels have wires connected
- ✅ J2 all 24 signal pins: connected or NC-flagged
- ✅ J2 shell / shield pin: connected to GND
- ✅ F1 (PPTC) in series between `+5V` and VBUS node
- ✅ C11–C14 all at VBUS node (3× 22 µF + 100 nF)
- ✅ R10, R11 (22 kΩ) on CC1 and CC2 to `+5V`; CC1/CC2 also tapped to U12 IN+/IN-
- ✅ U12 comparator: IN+ = CC1, IN- = CC2, output → R12 pull-up → SS_SEL
- ✅ U11 SS mux: SSTX±/SSRX± on one side, all four J2 SS pairs on the other, SEL driven
- ✅ U10a, U10b ESD arrays on TX1/RX1 and TX2/RX2 respectively; U10c on D+/D-
- ✅ C15, C16 (100 nF) on SSTX pair only, upstream of U11; no caps on RX pair
- ✅ D+ shorted A6+B6; D- shorted A7+B7
- ✅ SBU1, SBU2 have No-Connect flags; TX2/RX2 do NOT
- ✅ Every component has Reference + Footprint assigned

## Annotate and check footprints

1. **Tools → Annotate Schematic** — assigns J2, F1, R10–R12, U10a–U10c, U11, U12, C11–C16.
2. **Tools → Assign Footprints**:
   - J2 → footprint from GCT (download from GCT website for USB4105-GF-A)
   - F1 → `Resistor_SMD:R_1206_3216Metric` (PPTC fuses use resistor-style 1206 footprint)
   - R10, R11, R12 → `Resistor_SMD:R_0402_1005Metric`
   - U10a, U10b, U10c → `Package_TO_SOT_SMD:SOT-23-6` (NUP4202W1 is SOT-23-6)
   - U11 → per PI3DBS12412A datasheet (UFQFN-24 or similar — download from Diodes Inc.)
   - U12 → `Package_TO_SOT_SMD:SOT-23-5` (LMV321)
   - C11–C13 → `Capacitor_SMD:C_1210_3225Metric`
   - C14–C16 → `Capacitor_SMD:C_0402_1005Metric`

## Gotchas

- **AC-coupling caps upstream of mux**: C15/C16 go between the SSTX hierarchical labels and U11 — not between U11 and J2. Putting them downstream means one set of caps AC-couples only one orientation path; the other orientation gets no coupling and may fail to train.
- **AC-coupling on TX only**: never add AC caps on the SSRX path. The RTL8153B receiver has internal DC blocking; external caps on RX create insertion loss and prevent SS link training.
- **Comparator IN+ / IN- polarity**: IN+ = CC1, IN- = CC2. With this polarity, SEL=0 when CC1 is active (orientation 1) and SEL=1 when CC2 is active (orientation 2). Swapping IN+ and IN- reverses the SEL mapping — ensure U11 routing matches whichever polarity you use.
- **SS mux VCC**: PI3DBS12412A operates from 3.3 V. Do not connect to 5 V. The SEL pull-up (R12) must also be to 3.3 V to match the mux's logic level.
- **ESD placement**: U10a/U10b/U10c must be between U11 and J2 (connector side), not between U11 and the RTL8153B. ESD arrays protect the connector pins from external discharge events.
- **D+ / D- shorting**: the schematic junction of A6 and B6 to the same net is correct. On the PCB, short them at the connector pad (a copper track between A6 and B6 pads on the same copper layer). Keep the short local to J2.
- **PPTC fuse reset time**: PPTC fuses trip and then self-reset when cooled. A host that draws > 2 A will see the port go away and come back when the fuse resets — expected behaviour. If you need faster response or a latch, substitute TPS25940 (see bom.md procurement notes).
- **USB-C receptacle footprint**: mid-mount receptacles have very precise pad geometry. Use the manufacturer's recommended footprint, not a generic one. Shell mounting pads must be large enough to solder reliably for mechanical strain relief.
- **VCONN**: VCONN is not implemented (no e-marked cable support). Do not connect VCONN. The CC1/CC2 Rp pull-ups are for source-role power advertisement and orientation detection only.

## When you're done

Sheet 05 is complete when:

- ✅ ERC passes with 0 errors
- ✅ All 8 hierarchical labels have wires connected
- ✅ Only SBU1/SBU2 have No-Connect flags; TX2/RX2 are wired through U11
- ✅ U11, U12, R12 placed and wired; SS_SEL net connects comparator output to mux SEL
- ✅ U10a, U10b, U10c each placed with correct signal assignments
- ✅ Every component has a reference designator and footprint assigned
- ✅ Save, commit, push

**All five sheets are now complete.** Next steps are:
1. Run a full-project ERC from the root sheet and clear any remaining cross-sheet issues
2. Generate the netlist and import it into the PCB editor
3. Follow `docs/design-spec.md §3` for layout rules before placing any components
