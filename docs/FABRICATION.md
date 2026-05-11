# Fabrication Guide — PoEt Rev A

How to generate production files from the KiCad project and order from JLCPCB.

---

## Board specification

| Parameter | Value |
|---|---|
| Dimensions | 60 × 30 mm |
| Layers | 4 (F.Cu / In1.Cu / In2.Cu / B.Cu) |
| Thickness | 1.6 mm |
| Stackup | **JLCPCB JLC04161H-7628** |
| Surface finish | ENIG (required for fine-pitch QFN pads) |
| Solder mask | Green (any colour works) |
| Min trace / space | 0.13 / 0.13 mm |
| Min drill | 0.2 mm |
| Impedance control | **Yes — 90 Ω diff and 100 Ω diff** (add note below) |

---

## Step 1 — Add the isolation slot to the PCB

Before generating gerbers, the physical isolation slot must be drawn in KiCad. The slot prevents creepage/clearance violations between the PoE primary side and the USB secondary side.

1. In PCB Editor, select the **Edge.Cuts** layer.
2. Draw a rectangle slot from approximately **(55, 0)** to **(57, 30)** mm — a 2 mm wide slot running the full board height at x ≈ 56 mm (between T1 primary pads and secondary pads).
3. Alternatively, draw two `Edge.Cuts` lines forming a narrow slot — JLCPCB will route this as a PCB slot.
4. Verify: with 4 mm clearance rule enabled in DRC, no primary-side copper should be closer than 4 mm to any secondary-side copper across the slot.

> The slot adds ~$5–10 to the fab order. Note it explicitly in the special instructions when ordering.

---

## Step 2 — Run DRC

1. **PCB Editor → Inspect → Design Rules Checker → Run DRC**
2. The custom rule file `hardware/PoE-USBC-Gigabit.kicad_dru` should be loaded automatically (KiCad looks for `.kicad_dru` in the project folder).
3. Expected result: 0 errors. Common legitimate warnings:
   - "Differential pair uncoupled length" — acceptable if short (< 2 mm) at via transitions
   - Courtyard overlap at T1 (transformer body overlaps the isolation slot annotation) — suppress if confirmed intentional

---

## Step 3 — Generate Gerbers

1. **PCB Editor → File → Plot**
2. Settings:
   - **Format:** Gerber
   - **Output directory:** `../fabrication/gerbers/`
   - **Layers to plot:**
     - F.Cu, In1.Cu, In2.Cu, B.Cu
     - F.Mask, B.Mask
     - F.Silkscreen, B.Silkscreen
     - F.Paste, B.Paste
     - Edge.Cuts
   - **Options:** check "Use Protel filename extensions", check "Generate Gerber job file"
   - Leave "Plot footprint values" and "Plot reference designators" on
3. Click **Plot**, then click **Generate Drill Files**:
   - Format: Excellon
   - Map file format: Gerber X2
   - Oval holes: Route
   - Separate files for PTH / NPTH: yes
4. Zip the `fabrication/gerbers/` folder contents (not the folder itself — JLCPCB expects files at the root of the ZIP).

---

## Step 4 — Generate BOM and CPL (for PCBA)

If ordering assembled boards (JLCPCB SMT assembly service):

### BOM (Bill of Materials)

1. **Schematic Editor → Tools → Generate BOM**
2. Use the default `bom_csv_grouped_by_value` plugin or any CSV plugin.
3. The exported CSV needs columns: **Designator, Quantity, Value, Footprint, LCSC part number**.
4. Cross-reference `docs/bom.md` for LCSC part numbers (U2 RTL8153B = C77999, U4 AP2112K = C51118, U5 RT9013 = C47773, U6 PC817B = C7440, U7 TL431 = C7831).

### CPL (Component Placement List)

1. **PCB Editor → File → Fabrication Outputs → Component Placement (.pos)**
2. Format: CSV, mm, front and back separately.
3. JLCPCB expects columns: Designator, Mid X, Mid Y, Layer, Rotation.
4. KiCad exports this directly; check that rotation angles match JLCPCB's convention (some footprints need a 90° or 180° offset — verify against JLCPCB's DFM preview).

---

## Step 5 — Order at JLCPCB

1. Go to jlcpcb.com → **Order Now**
2. Upload the gerber ZIP
3. Set parameters:
   - PCB Qty: your choice (5 is minimum for the price break)
   - Layers: **4**
   - PCB Thickness: **1.6 mm**
   - PCB Color: your choice
   - Surface Finish: **ENIG**
   - Copper Weight: **1 oz** (outer), **0.5 oz** (inner — JLCPCB default for JLC04161H-7628)
   - Min Solder Mask Dam: 0.1 mm
   - **Impedance Control: Yes**
     - Select stackup: **JLC04161H-7628**
     - Add note: "90 Ω differential on F.Cu (USB SS); 100 Ω differential on F.Cu (MDI). Reference net class comments in Gerber job file."
   - **Special Requests:** "Board contains a 2 mm slot from (55,0) to (57,30) mm — please route as a PCB slot, not a score line."
4. If using PCBA: enable **SMT Assembly** on the same order page. Upload the BOM CSV and CPL CSV.

---

## Impedance control reference

| Net class | Layers | Trace W | Gap | Target Ω | Notes |
|---|---|---|---|---|---|
| USB3_SS | F.Cu over In1.Cu GND | 0.15 mm | 0.13 mm | 90 Ω diff | USB 3.2 Gen1 SS pair |
| ETHERNET_MDI | F.Cu over In1.Cu GND | 0.25 mm | 0.20 mm | 100 Ω diff | 1000BASE-T MDI |
| USB 2.0 D+/D- | F.Cu over In1.Cu GND | 0.20 mm | — | 50 Ω SE | Short traces, less critical |

These values are calculated for the JLC04161H-7628 stackup (F.Cu to In1.Cu prepreg = 0.2 mm, εr = 4.5). If JLCPCB changes the stackup, recalculate using their online impedance calculator before ordering.

---

## File checklist

Before zipping and uploading, confirm:

- [ ] `*.GTL` — F.Cu
- [ ] `*.G2L` (or `*-In1_Cu.gbr`) — In1.Cu
- [ ] `*.G3L` (or `*-In2_Cu.gbr`) — In2.Cu
- [ ] `*.GBL` — B.Cu
- [ ] `*.GTS` / `*.GBS` — F.Mask, B.Mask
- [ ] `*.GTO` / `*.GBO` — F.Silkscreen, B.Silkscreen
- [ ] `*.GTP` / `*.GBP` — F.Paste, B.Paste (needed for stencil)
- [ ] `*.GKO` — Edge.Cuts (board outline + slot)
- [ ] `*.drl` — drill file (PTH + NPTH)
- [ ] No extra `.bak` or `.pro` files in the ZIP

---

## Post-order checks

Once JLCPCB's "DFM analysis" completes (usually < 1 hour):

1. **Check the slot** is shown correctly in their preview, not as a missing board section
2. **Check impedance note** was acknowledged in the engineering review
3. If they flag any DRC violations, compare against the KiCad DRC output — JLCPCB's minimum trace rules are slightly different from KiCad defaults
