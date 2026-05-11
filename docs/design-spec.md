# Design Specification — PoEt

Rev A · 2026-05 · v3 (simplified to match Ubiquiti UACC-Adapter-PoE-USBC)

---

## 1. Electrical requirements

### 1.1 PoE input
- **Standard:** IEEE 802.3af Type 1
- **PSE voltage range:** 44 – 57 V at PSE; 36 – 57 V at PD (after cable drop)
- **Class:** Class 0 / 3 — advertises 12.95 W at PD
- **Polarity:** insensitive (Schottky bridge per pair set, both Mode A and Mode B handled)
- **Detection:** 25 kΩ signature resistor in Si3402-B
- **Classification:** programmable via Si3402-B class pin resistor (Class 3 = 6.49–12.95 W)
- **Maintain Power Signature:** automatic (Si3402-B keeps quiescent current above MPS threshold)

### 1.2 Ethernet
- **PHY:** integrated in RTL8153B
- **Speeds:** 10 / 100 / 1000 Mbps
- **MDI/MDIX:** auto
- **Magnetics:** integrated in RJ45 jack (must be PoE-rated; non-PoE jacks lack the center-tap traces and DC handling)

### 1.3 USB output
- **Connector:** USB-C receptacle, 24-pin
- **Role:** UFP (data device) + Source (power), **single-orientation SS**
- **Data:**
  - USB 3.2 Gen 1 (5 Gbps) on TX1+/-, RX1+/- pair only — wired to RTL8153B SuperSpeed pins
  - TX2/RX2 pair left unconnected
  - USB 2.0 D+/D- direct from RTL8153B; both A6/B6 (D+) and A7/B7 (D-) shorted at the connector pads, so USB 2.0 enumerates regardless of orientation
- **Power source:** 5 V / 2 A from secondary rail
- **CC configuration:**
  - CC1 and CC2 each pulled to **+5 V via 22 kΩ Rp** → advertises **5 V @ 1.5 A** (USB-C "Type-C 1.5 A" current)
  - Could use Rp = 10 kΩ to advertise 3 A, but supply is only 2 A — host might over-draw. **22 kΩ is the safe choice.**
- **VCONN:** not supplied. No e-marked cable required.

### 1.4 Isolation
- **Primary (PoE) ↔ Secondary (USB):** 1500 Vrms, 1 minute (per IEEE 802.3)
- **Isolation barrier crosses:** flyback transformer T1, optocoupler U6, RJ45 magnetics, Y-cap C3
- **Creepage primary↔secondary:** ≥ 4.0 mm
- **Clearance:** ≥ 4.0 mm

---

## 2. System architecture

### 2.1 Power chain

```
RJ45 (PoE-rated magnetics)
  → 2× Schottky bridge (Mode A pairs, Mode B pairs) — DF06S or 4× S2J discretes
  → bulk capacitor (10 µF / 100 V ceramic + 47 µF / 100 V Al)
  → TVS (SMAJ58A)
  → Si3402-B (single-chip PD interface + flyback PWM controller + 100 V hot-swap switch)
  → flyback transformer T1 (primary 36–57 V, secondary 5 V / 2 A, 1500 V isolation)
  → secondary rectifier (SS34 Schottky)
  → output bulk (220 µF polymer + 22 µF X5R + 100 nF)
  → optional output ferrite bead π-filter
  → 5 V / 2 A rail (~10 W) feeding both RTL8153B and USB-C VBUS
```

Feedback: TL431 + PC817B optocoupler across isolation barrier (standard pattern; Si3402-B datasheet Figure 11).

### 2.2 Power budget (worst case, full 2 A on USB-C)

| Stage | In | Out | Loss | η |
|---|---|---|---|---|
| Cable + RJ45 (Cat5e, 30 m) | 13 W @ PSE | 12.95 W @ PD | < 0.1 W | ~99 % (af cable budget allows up to 12.95 W loss tolerance) |
| Schottky bridges | 12.95 W | 12.45 W | 0.5 W | 96 % |
| Si3402-B + flyback (target 85 %) | 12.45 W | 10.6 W | 1.85 W | 85 % |
| 5 V rail to RTL8153B | — | ~1.5 W internal load | — | — |
| 5 V rail to USB-C VBUS | — | up to 10 W (5 V × 2 A) | — | — |

⚠️ Total available on the 5 V rail: ~10.6 W. RTL8153B draws ~1.5 W (varies with link rate), so USB-C VBUS gets ~9 W headroom — comfortably above the 7.5 W advertised (22 kΩ CC Rp → 5 V @ 1.5 A). F1 (PPTC) is the over-current protection; a host drawing > 2.2 A trips the fuse, preventing the brownout that would drop the Ethernet link.

### 2.3 Data chain

```
RJ45 magnetics MDI[0..3]+/- (4 pairs in 1000BASE-T)
  → ESD protection (NUP4202W1 ×2)
  → RTL8153B MDI inputs
  → internal Gigabit PHY + MAC + USB 3.0 device
  → SuperSpeed differential (SSTX±, SSRX±)
  → AC-coupling caps (100 nF) on TX pair only
  → USB-C TX1±, RX1± pins (single orientation)
  → USB 2.0 D+/D- routed direct, both orientations shorted at pad
```

### 2.4 EEPROM

- 93C46 1 Kbit MicroWire EEPROM at U3
- Stores: VID 0x0BDA, PID 0x8153 (Realtek defaults so the in-tree `r8152` driver auto-binds), 48-bit MAC, USB string descriptors
- See `firmware/eeprom-image.md` for byte layout

---

## 3. PCB layout

### 3.1 Stackup (4-layer, 1.6 mm)

| Layer | Use |
|---|---|
| F.Cu | signals, components, USB SS pair |
| In1.Cu | **solid GND plane** (reference for SS + MDI) |
| In2.Cu | power plane (5 V on secondary; V_POE on primary; isolated regions) |
| B.Cu | signals, low-speed routing |

Manufacturer: JLCPCB JLC04161H-7628 stackup, controlled impedance:
- 90 Ω diff: USB 3.0 SS (0.15 mm trace, 0.13 mm gap)
- 100 Ω diff: Ethernet MDI (0.25 mm trace, 0.2 mm gap)
- 50 Ω SE: USB 2.0 D+/D-

### 3.2 Critical layout rules

1. **Isolation gap:** ≥ 4 mm slot in **all four copper layers** between PoE primary and USB secondary. Cut under T1. Mark on silkscreen.
2. **PoE primary loop:** Vin → bridge → bulk cap → Si3402-B → xfmr primary → return; keep the loop area as small as possible — high di/dt.
3. **USB 3.0 SS pair:** 90 Ω diff, length-match within 0.1 mm intra-pair, max 2 vias, no stubs, reference to solid GND. AC-couple caps (100 nF GRM188) on TX side only, close to USB-C connector.
4. **Ethernet MDI:** 100 Ω diff, length-match within 0.5 mm, all 4 pairs same length within 5 mm. RJ45 within 25 mm of RTL8153B.
5. **Bob Smith termination:** verify integrated jack already includes 75 Ω + kV cap to chassis ground; if not, add externally.
6. **Crystal Y1 (25 MHz):** under RTL8153B XTAL pins, GND guard ring, no traces underneath, GND vias around guard.
7. **Decoupling:** 100 nF + 10 µF per RTL8153B power pin (~6 power pins), < 2 mm from pin.
8. **Output bulk:** 47 µF + 22 µF + 100 nF at USB-C VBUS pin pads.
9. **Thermal:** Si3402-B package dissipates ~1.5 W at full load. Thermal pour ≥ 200 mm² with via stitching to internal GND.

### 3.3 EMC

- Common-mode choke on USB SS pair (Murata DLP11SN900HL2L)
- Common-mode choke on USB 2.0 D+/D-
- Y-cap (1 nF, 2 kV) across primary/secondary GND
- Ferrite bead between bulk filter and Si3402-B VIN

---

## 4. Compliance targets

| Standard | Notes |
|---|---|
| IEEE 802.3af | self-cert via interop with managed PoE switches (UniFi, Cisco, Aruba) |
| USB 3.2 | aim for TX eye-diagram pass; full USB-IF cert optional |
| FCC Part 15 Class B | requires pre-compliance scan |
| CE (EN 55032/55035) | as above |
| RoHS / REACH | choose RoHS BOM lines |

---

## 5. Decisions log

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | PoE class | **802.3af** (12.95 W) | Matches Ubiquiti reference product spec exactly |
| 2 | Output | **5 V / 2 A fixed**, no PD | Same as reference |
| 3 | USB-C orientation | **Single-orientation SS** | Reference product almost certainly does this; saves $1.50 BOM |
| 4 | PD controller | **Si3402-B** | Single-chip integrated PD + flyback PWM, simplest possible |
| 5 | Bridges | **Schottky** (DF06S ×2) | Only 0.5 W loss at 12 W; active rectifiers (LT4321) overkill |
| 6 | USB-Eth bridge | **RTL8153B** | Mature, in-tree Linux driver, ~$3 single qty |
| 7 | Form factor | **~60 × 30 mm, 4-layer** | Comfortable layout, fits standard project enclosures |

## 6. Future work

- Reversible USB-C (add PI3DBS12412A SS mux) → +$1.50, full orientation reversibility
- Active rectifiers (LT4321 ×2) → fewer thermal concerns at 802.3at upgrade
- Upgrade to 802.3at + USB-PD 9 V
