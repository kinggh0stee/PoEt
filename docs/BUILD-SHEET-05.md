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

  USB_SSTX+ ──► C15 (100 nF) ──► U9 ESD ─────────────────────────► TX1+ (A2)
  USB_SSTX- ──► C16 (100 nF) ──► U9 ESD ─────────────────────────► TX1- (A3)
  USB_SSRX+ ──────────────────── U9 ESD ─────────────────────────► RX1+ (B10)
  USB_SSRX- ──────────────────── U9 ESD ─────────────────────────► RX1- (B11)

  USB_DP ─────────────────────── U9 ESD ─────────────────────────► D+ A6 + B6 (shorted)
  USB_DM ─────────────────────── U9 ESD ─────────────────────────► D- A7 + B7 (shorted)

                                              TX2+, TX2-, RX2+, RX2-  → NC
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
| TX1 | A2, A3 | SuperSpeed TX (single orientation) |
| RX1 | B10, B11 | SuperSpeed RX (single orientation) |
| TX2 | A10, A11 | NC (second orientation SS TX) |
| RX2 | B2, B3 | NC (second orientation SS RX) |
| D+ | A6, B6 | USB 2.0 D+ |
| D- | A7, B7 | USB 2.0 D- |
| CC1 | A5 | Configuration channel 1 |
| CC2 | B5 | Configuration channel 2 |
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

## Step 4 — CC pull-up resistors (R10, R11)

These resistors tell the host that this port is a USB-C power source advertising 1.5 A.

1. Place `Device:R` for **R10** (22 kΩ 1% 0402):
   - One end → `+5V`
   - Other end → J2 CC1 (A5)
2. Place `Device:R` for **R11** (22 kΩ 1% 0402):
   - One end → `+5V`
   - Other end → J2 CC2 (B5)

> A 22 kΩ Rp to 5 V = USB-C "Type-C Current" advertisement of 1.5 A (7.5 W). The actual supply can deliver 2 A / 10 W, but this conservative advertisement prevents a host from drawing more than 1.5 A under normal auto-negotiation. See design-spec.md §1.3.

## Step 5 — ESD protection (U9)

Place the ESD array before routing signals to J2 — ESD protection goes between the internal circuitry and the connector, as close to the connector as possible.

1. Place `Diode:NUP4202W1` (or `Diode:PRTR5V0U2X` as an alternate 2-line SOT-363 part) for **U9** at approximately **(115, 80)**.
2. Wire:
   - U9 line 1 pair → USB_SSTX+ / USB_SSTX- nets (TX SuperSpeed pair)
   - U9 line 2 pair → USB_SSRX+ / USB_SSRX- nets (RX SuperSpeed pair)
   - (If using NUP4202W1 in SOT-23-6: 4 lines in one package — use two chips for SS + D+/D- or one NUP4202W1 per differential pair)
   - A separate NUP4202W1 (or shared array) on USB_DP / USB_DM
   - All GND pins of U9 → `GND`

The SS pair ESD arrays must not add significant capacitance to the 5 Gbps lines. The NUP4202W1 and PRTR5V0U2X are both specified for USB 3.0 speeds.

## Step 6 — AC-coupling caps on TX pair (C15, C16)

USB 3.0 SuperSpeed TX lines require AC coupling to remove DC offset between transmitter and receiver.

1. Place `Device:C` for **C15** (100 nF / 16 V X7R 0402) in series on the `USB_SSTX+` line, between the U9 ESD array output and J2 TX1+ (A2).
2. Place `Device:C` for **C16** (100 nF / 16 V X7R 0402) in series on the `USB_SSTX-` line, between U9 and J2 TX1- (A3).

**RX pair (USB_SSRX±) has no AC-coupling caps here** — the RTL8153B has internal DC blocking on its RX inputs. Adding external caps on RX would create an unwanted RC filter.

## Step 7 — Wire SuperSpeed signals to J2

1. `USB_SSTX+` → C15 → J2 TX1+ (A2)
2. `USB_SSTX-` → C16 → J2 TX1- (A3)
3. `USB_SSRX+` → J2 RX1+ (B10)
4. `USB_SSRX-` → J2 RX1- (B11)

## Step 8 — Wire USB 2.0 D+/D- to J2

For USB 2.0 to work in both plug orientations, both the A-side and B-side D+/D- pins are connected together.

1. `USB_DP` → J2 A6 and J2 B6 (short A6 and B6 together at the connector pads — use a net junction or a short wire segment)
2. `USB_DM` → J2 A7 and J2 B7 (same, short A7 and B7 together)

This means that regardless of plug orientation, D+ always reaches the data lines. SuperSpeed only works in one orientation (TX1/RX1 path), but USB 2.0 enumeration works both ways — the device will always appear to the host even if SS doesn't train.

## Step 9 — Mark unused pins NC

KiCad ERC will flag any unconnected pins as errors. Mark all of these with explicit `Place → No Connect` flags (`X` key in Eeschema):

- J2 TX2+ (A10), TX2- (A11) — NC
- J2 RX2+ (B2), RX2- (B3) — NC
- J2 SBU1 (A8), SBU2 (B8) — NC

## Step 10 — Wire hierarchical labels

All eight input labels are on the left edge of the sheet:

| Label | Connect to |
|---|---|
| `+5V` | F1 input |
| `GND` | GND bus (J2 GND pins, capacitor negatives) |
| `USB_SSTX+` | C15 input (then through to J2 A2) |
| `USB_SSTX-` | C16 input (then through to J2 A3) |
| `USB_SSRX+` | J2 B10 (direct, no cap) |
| `USB_SSRX-` | J2 B11 (direct, no cap) |
| `USB_DP` | J2 A6 + B6 (shorted) |
| `USB_DM` | J2 A7 + B7 (shorted) |

## Step 11 — Run ERC

Expected results:
- 0 errors
- 0 warnings (if all NC flags are placed correctly)

If you see:
- `"Pin unconnected"` on TX2 / RX2 / SBU pins → add No-Connect flags
- `"Wire not connected"` → chase down dangling wire ends at D+ / D- junction (the short between A and B pads can look like an unconnected wire end)

## ERC checklist before marking complete

- ✅ All 8 hierarchical labels have wires connected
- ✅ J2 all 24 signal pins: connected or NC-flagged
- ✅ J2 shell / shield pin: connected to GND
- ✅ F1 (PPTC) in series between `+5V` and VBUS node
- ✅ C11–C14 all at VBUS node (3× 22 µF + 100 nF)
- ✅ R10, R11 (22 kΩ) on CC1 and CC2 to `+5V`
- ✅ U9 ESD array on SS pairs and D+/D-
- ✅ C15, C16 (100 nF) on TX pair only; no caps on RX pair
- ✅ D+ shorted A6+B6; D- shorted A7+B7
- ✅ TX2/RX2/SBU pins have No-Connect flags
- ✅ Every component has Reference + Footprint assigned

## Annotate and check footprints

1. **Tools → Annotate Schematic** — assigns J2, F1, R10, R11, U9, C11–C16.
2. **Tools → Assign Footprints**:
   - J2 → footprint from GCT (download from GCT website for USB4105-GF-A)
   - F1 → `Resistor_SMD:R_1206_3216Metric` (PPTC fuses use resistor-style 1206 footprint)
   - R10, R11 → `Resistor_SMD:R_0402_1005Metric`
   - U9 → `Package_TO_SOT_SMD:SOT-23-6` (NUP4202W1 is SOT-23-6)
   - C11–C13 → `Capacitor_SMD:C_1210_3225Metric`
   - C14–C16 → `Capacitor_SMD:C_0402_1005Metric`

## Gotchas

- **AC-coupling caps on TX only**: a very common mistake is to put AC-coupling caps on the RX pair too. The RTL8153B receiver already has internal DC blocking; external caps on RX create a 6 dB insertion loss and can prevent SS link training. C15/C16 go on TX1+/TX1- only.
- **D+ / D- shorting**: the schematic junction of A6 and B6 to the same net is correct. On the PCB, short them at the connector pad (a copper track between A6 and B6 pads on the same copper layer). Do not route the net back upstream to Sheet 04 and then return — keep the short local to J2.
- **PPTC fuse reset time**: PPTC fuses trip and then self-reset when cooled. A host that draws > 2 A will see the port go away and come back when the fuse resets — this is expected behaviour. If you need faster response or a latch, substitute TPS25940 (see bom.md procurement notes).
- **USB-C receptacle footprint**: mid-mount receptacles have very precise pad geometry. Use the manufacturer's recommended footprint, not a generic one. Shell mounting pads must be large enough to solder reliably for mechanical strain relief.
- **VCONN**: VCONN is not implemented in this design (no e-marked cable support). Do not connect VCONN. The CC1/CC2 Rp pull-ups are for the source-role power advertisement only.

## When you're done

Sheet 05 is complete when:

- ✅ ERC passes with 0 errors
- ✅ All 8 hierarchical labels have wires connected
- ✅ All unused J2 pins have No-Connect flags
- ✅ Every component has a reference designator and footprint assigned
- ✅ Save, commit, push

**All five sheets are now complete.** Next steps are:
1. Run a full-project ERC from the root sheet and clear any remaining cross-sheet issues
2. Generate the netlist and import it into the PCB editor
3. Follow `docs/design-spec.md §3` for layout rules before placing any components
