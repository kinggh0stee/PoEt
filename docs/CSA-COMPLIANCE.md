# CSA / IEC 62368-1 Compliance Readiness — PoEt Rev A

> **Scope of this document.** This is a design-side readiness review against
> **CSA C22.2 No. 62368-1** (harmonized with UL 62368-1 and IEC 62368-1, the
> standard for "Audio/video, information and communication technology
> equipment — safety requirements"). It does **not** confer certification.
> Listing, marking, and continued surveillance must be obtained from an NRTL
> (CSA Group, UL, Intertek, TÜV, etc.) on samples built from the production
> BOM and stackup documented in this repo.

Use this document as the gating checklist before submitting samples to an
NRTL. Each row links a clause of 62368-1 to the file in this repo where the
design decision lives.

---

## 1. Product classification

| Item | Value | Clause |
|---|---|---|
| Equipment category | ICT equipment, externally powered | 62368-1 §3.3 |
| Permanent / pluggable | Pluggable Type B (RJ45 input) | §3.3.4 |
| Enclosure type | Plastic, PD2 pollution degree | §4.4, §G.14 |
| User category | Ordinary person (both ports) | §0.5.4 |
| Overvoltage category | OVC I (downstream of PoE PSE, isolated network) | §4.3, Table 9 |

## 2. Energy source classification

| Net / interface | Voltage | Current | Class | Clause |
|---|---|---|---|---|
| PoE input (V_POE+, V_POE−, V_SW) | 57 V DC max | 350 mA | **ES2 / PS2** | §5.2.2.2, §6.2.2 |
| Flyback transformer primary | 57 V DC + transient ringing (~200 V peak on switch node) | — | **ES2** (peak design ≤ 200 V) | §5.2.2.2 |
| 5 V secondary rail / VBUS | 5 V DC | 2 A | **ES1 / PS1** | §5.2.2.1, §6.2.1 |
| MDI pairs (RJ45) | < 5 V signal, isolated through magnetics | — | ES1 | §5.4.4 (telecom isolated) |
| USB 2.0 / USB 3.2 SS | < 1 V differential | — | ES1 | §5.2.2.1 |

**Operator-accessible parts:** USB-C shell, enclosure, RJ45 latch. All must
be ES1/PS1 or separated from higher classes by reinforced insulation.

## 3. Insulation requirements across the PoE↔USB barrier

For an **ES2 → ES1** boundary with operator access, 62368-1 requires
**reinforced insulation** (Table 13). The barrier crosses T1, U6, J1
magnetics, and C3.

### 3.1 Clearance (air gap)

Working voltage 57 V DC, OVC I, mains transient voltage 330 V (Table 14):

| Parameter | Required (§5.4.2, Table 16) | This design | File |
|---|---|---|---|
| Clearance (reinforced) | ≥ 0.5 mm (transient) | **4.0 mm** | `hardware/PoE-USBC-Gigabit.kicad_dru` |

Headroom: ~8× over the standard. Adequate even if the design is later
re-rated for OVC II (which raises transient to 1500 V → 1.5 mm required).

### 3.2 Creepage (along surface)

Working voltage 57 V DC, PD2, material group IIIa (FR-4 typical CTI):

| Parameter | Required (§5.4.3, Table 17) | This design | File |
|---|---|---|---|
| Creepage (reinforced, basic × 2) | ~1.7 mm | **4.0 mm** | `hardware/PoE-USBC-Gigabit.kicad_dru` |

The 2 mm physical slot in Edge.Cuts (`docs/FABRICATION.md` §1) reduces the
surface path requirement further by removing surface material entirely.

### 3.3 Solid insulation

Distance through insulation (DTI) for reinforced: ≥ 0.4 mm of material with
known dielectric strength (§5.4.4.6). Inside T1 winding, optocoupler U6
package, and Y-cap C3 dielectric — verified by the component manufacturer's
safety listing, not by this design. See §4.

### 3.4 Routine test (dielectric strength)

§5.4.9.1: every unit shall pass a routine production hi-pot test of
**3000 V rms / 1 min** primary↔secondary. Procedure: `docs/BRING-UP.md`
Stage 7.

## 4. Safety-critical component certification

Each component crossing or supporting the isolation barrier must hold an
applicable component certification. Submission to the NRTL requires the
certificate number for each.

| Ref | Part | Required listing | Current BOM | Action |
|---|---|---|---|---|
| T1 | Flyback transformer | **IEC 61558** or **IEC 60601-1** dielectric-tested; ≥ 3000 V rms primary↔secondary; reinforced insulation construction | Würth 750313638 / Coilcraft Y8862-AL | Confirm IEC 62368-1 / 61558 listing on datasheet; obtain certificate from supplier |
| C3 | Y-cap, 1 nF / 2 kV | **Y1 class** (8 kV impulse, reinforced insulation) — per IEC 60384-14 | **Listed as "Y2 ceramic"** ⚠ | **Replace with Y1-rated part.** Y2 is basic/supplementary only |
| U6 | Optocoupler | **VDE 0884-11** or **UL 1577** with reinforced-insulation rating; ≥ 5000 V rms isolation; pollution-protected coupler | "PC817B" generic | Specify **PC817B-X1** (Sharp) or **TLP785(GR)** — both have VDE 0884 with reinforced grade. Generic PC817B is basic-insulation only |
| J1 | RJ45 with magnetics | UL 60950/62368 listed for ≥ 1500 V rms (Ethernet IEEE 802.3 standard) | Bel Fuse 0826-1G1T-DV-F / Pulse JK0-0177NL | Confirm UL recognition (typically pre-certified for this part class) |
| F_in | **PoE-input fuse** | UL 248 listed slow-blow, ≥ 250 V rated | **Not present** ⚠ | **Add F_in (1 A T 250 V) in series with V_POE+** — required by §5.5.6 for fault current limiting on primary side |
| F1 | VBUS PPTC | UL 248-14 listed | Bourns MF-MSMF200/33X-2 / TE MICROSMD200F-2 | Both are UL recognized — OK |
| D3 | TVS, primary | Required only as part of EMC strategy; no safety listing needed unless used as a primary protective device | SMAJ58A | OK as-is |

## 5. Marking and labelling (Annex F)

Required permanent markings on the product / packaging:

- Manufacturer name and address (or registered trademark)
- Model designation: **PoEt Rev A**
- Input rating: **48 V DC, PoE 802.3af, max 350 mA**
- Output rating: **5 V DC, 2 A**
- Safety symbols: **CSA / cULus** mark (after listing), **CE**, **FCC ID**
  (after Part 15 cert), **RoHS** mark, **WEEE** crossed-wheelie bin
- "For indoor use only" if not IP-rated
- Cautions per §F.3.6 if applicable

These markings must be **permanent** (rub-test §F.3.10 — 15 s with water,
15 s with petroleum spirit, no fade or smear). Silkscreen on PCB is not
sufficient if the PCB is fully enclosed; the case label must carry them.

## 6. Construction (§6 — fire enclosure, mechanical)

| Requirement | Status |
|---|---|
| Fire enclosure for PS2 source | Enclosure must be V-1 rated or thicker than 3 mm wall PC. Current 3D-printed case is **PLA, not flame-rated** — production case must move to V-0 ABS, polycarbonate, or steel/aluminium |
| Drop test (§T.7) | Not yet performed |
| Stress relief on cordage | RJ45 latch + USB-C friction is borderline; consider strain relief on PCB for both connectors |
| Ball impact test (§T.6) | 500 g steel ball from 1.3 m, on enclosure top — not yet performed |

## 7. Mandatory pre-compliance evaluations (before NRTL submission)

Run all of these in-house before submitting samples. Failures here are
cheap to fix; failures at the NRTL cost weeks per round.

| Test | Method | Pass criterion | Where |
|---|---|---|---|
| Hi-pot, primary↔secondary | 3000 V rms / 60 s, ≤ 5 mA leakage | No breakdown, no flashover | `docs/BRING-UP.md` Stage 7 |
| Insulation resistance | 500 V DC, primary↔secondary | ≥ 100 MΩ | `docs/BRING-UP.md` Stage 7 |
| Touch current | Per §5.7.4, IEC 60990 networks A/B | ≤ 0.25 mA at 1.06× rated voltage | `docs/BRING-UP.md` Stage 7 |
| Temperature rise (normal) | Full load, 25 °C ambient, 1 h thermal equilibrium | All material temps below Table B.10 limits | `docs/BRING-UP.md` Stage 6 (expand to 1 h) |
| Temperature rise (40 °C ambient) | Full load in 40 °C chamber | All material temps below Table B.10 | `docs/BRING-UP.md` Stage 7 |
| Abnormal operation, output short | Short VBUS to GND for 7 h | No fire, no breach of fire enclosure, no PoE PSE fault propagation | `docs/BRING-UP.md` Stage 7 |
| Abnormal operation, fan/cap short | Force fault on individual components per §B.4 | No fire | NRTL only (destructive) |
| Solder joint reliability | Thermal cycle −40 ↔ +85 °C, 100 cycles | No open joints | Third-party lab (optional pre-compliance) |

## 8. Open items before NRTL submission

In priority order:

1. **Re-spec C3** from Y2 to Y1 (1 nF / 250 V AC Y1, e.g. Murata
   DE2B3KY102KA3B — verify availability)
2. **Add F_in** primary-side fuse to schematic Sheet 02 (1 A T 250 V)
3. **Specify U6 reinforced-insulation grade** in BOM (PC817B-X1 or TLP785)
4. **Confirm T1 IEC 61558 listing** with Würth / Coilcraft; record
   certificate number in BOM
5. **Production enclosure material** — switch from PLA print to V-0
   thermoplastic injection or sheet metal
6. **Run pre-compliance hi-pot, IR, touch current** per `BRING-UP.md` Stage 7
7. **Compile technical file** — schematic, layout, BOM with cert numbers,
   construction drawing, test reports — for NRTL engineer review

## 9. References

- CSA C22.2 No. 62368-1:19 — *Audio/video, information and communication
  technology equipment — Part 1: Safety requirements*
- IEC 62368-1:2018 — international equivalent
- UL 62368-1:2019 — US equivalent
- IEC 60384-14 — Y-class capacitor safety standard
- IEC 61558-1, -2-16 — transformer safety
- VDE 0884-11 — optocoupler reinforced insulation
- UL 248-14 — PPTC fuse safety
- IEEE 802.3-2022 §33 — PoE PD requirements
