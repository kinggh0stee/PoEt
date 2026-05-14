# Bill of Materials — Rev A (v3)

Quantities are per board. Substitutes must match footprint **and** electrical rating.

## Critical / single-source ICs

| Ref | Qty | Part | Description | MPN | Source |
|---|---|---|---|---|---|
| U1 | 1 | PoE PD + flyback | 802.3af PD interface, integrated 100 V switch + flyback PWM controller | **Si3402-B-GM** (Skyworks) | Digi-Key 336-3293-1-ND |
| U2 | 1 | USB 3.0 to GbE | USB 3.0 device + Gigabit PHY+MAC | **RTL8153B-VC-CG** (Realtek) | LCSC C77999 |
| U3 | 1 | EEPROM | 93LC46 1 Kbit MicroWire (CMOS 3-wire, 2.0–5.5 V) | 93LC46BT-I/OT | Digi-Key |
| U4 | 1 | 3.3 V LDO (RTL8153B I/O) | 500 mA low-noise | AP2112K-3.3 | LCSC C51118 |
| U5 | 1 | 1.0 V LDO (RTL8153B core) | 500 mA fixed 1.0 V | RT9013-10GB | LCSC C47773 |
| U6 | 1 | Optocoupler | Si3402-B feedback isolation | PC817B | LCSC C7440 |
| U7 | 1 | Shunt regulator | TL431 reference | TL431ASN | LCSC C7831 |
| U101, U102 | 2 | ESD protection (MDI) | 4-line TVS array — Sheet 01, MDI0±–MDI3± | NUP4202W1T1G | Digi-Key |
| U10a, U10b, U10c | 3 | ESD protection (USB-C) | 4-line TVS array — Sheet 05: U10a on TX1/RX1, U10b on TX2/RX2, U10c on D+/D- | NUP4202W1T1G | Digi-Key |
| U11 | 1 | SS orientation mux | 4-channel 2:1 USB 3.0 SS mux/demux, ≤ 12 Gbps, SEL-controlled; **UFQFN-24** | **PI3DBS12412A** (Diodes Inc.) or FSUSB43L10X (ON Semi, SOT-23-6) | Digi-Key / Mouser (no LCSC listing confirmed — verify before ordering JLCPCB assembly) |
| U12 | 1 | CC orientation comparator | Single-supply comparator, **SOT-23-5** — IN+=CC1, IN-=CC2; output drives U11 SEL via R12 | **LMV321IDBVR** (TI) | LCSC C7950 / Digi-Key |

## Magnetics & connectors

| Ref | Qty | Part | Description | MPN |
|---|---|---|---|---|
| J1 | 1 | RJ45 jack with magnetics | PoE-rated, integrated mag, LEDs | **Bel Fuse 0826-1G1T-DV-F** or Pulse JK0-0177NL |
| T1 | 1 | Flyback transformer | 802.3af, primary 36–57 V → 5 V/2 A, isolation 1500 V, **matched to Si3402-B reference design AN1004** | Würth 750313638 or Coilcraft Y8862-AL |
| L1 | 1 | USB SS common-mode choke | 90 Ω @ 100 MHz, USB 3.0 rated | Murata DLP11SN900HL2L |
| L2 | 1 | USB 2.0 CMC | 90 Ω @ 100 MHz | Murata DLW21SN900SQ2L |
| FB1 | 1 | Ferrite bead | 600 Ω @ 100 MHz, 3 A | BLM21PG600SH1D |
| J2 | 1 | USB-C receptacle | 24-pin mid-mount SMT | GCT USB4105-GF-A or Amphenol 12401610E412A |

## Discretes — primary side (PoE)

| Ref | Qty | Value | Type | Notes |
|---|---|---|---|---|
| D1, D2 | 2 | DF06S | Bridge rectifier 600 V / 1 A | One per pair set |
| D3 | 1 | SMAJ58A | TVS unidir 58 V | Across V_POE rail |
| C1 | 1 | 10 µF / 100 V | X7R 1210 | PoE bulk |
| C2 | 1 | 47 µF / 100 V | Aluminum electrolytic, low ESR | PoE bulk |
| C3 | 1 | 1 nF / 2 kV | Y2 ceramic | Across iso barrier |
| R1 | 1 | 24.9 kΩ 1 % | RDET | Detection signature |
| R2 | 1 | 12.1 kΩ 1 % | RCLS | Class 3 (6.49–12.95 W) — verify per Si3402-B Table 4 |

## Discretes — secondary side (PoE → 5 V)

| Ref | Qty | Value | Type | Notes |
|---|---|---|---|---|
| D4 | 1 | SS34 (or PMEG6020) | Schottky 60 V / 3 A | Secondary rectifier |
| R3 | 1 | 470 Ω 1/16 W 0402 | Current-limiting | LED3 power indicator (Sheet 02, +5V → R3 → LED3 → GND) |
| C10 | 1 | 220 µF / 16 V | Polymer low-ESR | Secondary bulk |
| C11–C13 | 3 | 22 µF / 10 V | X5R 1210 | VBUS bulk at USB-C connector |
| C14 | 1 | 100 nF / 16 V | X7R 0402 | High-freq bypass at VBUS |
| C15, C16 | 2 | 100 nF / 16 V | X7R 0402 | USB SS AC-coupling on TX pair |
| **R10, R11** | 2 | **22 kΩ 1 %** | 0402 | Rp on CC1, CC2 → 5 V (advertise 1.5 A) |
| R12 | 1 | 10 kΩ | 0402 | Pull-up from U12 comparator output to +3V3 (open-drain output to SEL logic level) |
| F1 | 1 | 2 A / 6 V PPTC | Resettable fuse | VBUS over-current protection; Bourns MF-MSMF200/33X-2 or TE MICROSMD200F-2 |

## RTL8153B support

| Ref | Qty | Value | Notes |
|---|---|---|---|
| Y1 | 1 | 25 MHz ±25 ppm crystal, **CL = 12 pF** | 5×3.2 mm or 3.2×2.5 mm SMD — e.g. EPSON FA-128 25.0000MF12X, ABM8-25.000MHZ-B2-T (verify CL against RTL8153B ref design) |
| C20, C21 | 2 | 18 pF NP0 0402 | Crystal load (verify per crystal CL) |
| C22–C40 | ~15 | 100 nF 0402 X7R | Decoupling per RTL8153B power pin |
| C41–C44 | 4 | 10 µF 0603 X5R | Bulk decoupling |
| R20–R25 | 6 | bias/strap resistors | per RTL8153B reference design |
| R401, R402 | 2 | 330 Ω 1/16 W 0402 | LED1/LED2 current-limiting (Sheet 04, in series with RTL8153B LED0/LED1 open-drain outputs) |

## LEDs / user interface

| Ref | Qty | Part | Color | Function |
|---|---|---|---|---|
| LED1 | 1 | green 0603 | GREEN | LINK — Sheet 04, driven by RTL8153B LED0 via R401 |
| LED2 | 1 | yellow 0603 | YELLOW | ACT — Sheet 04, driven by RTL8153B LED1 via R402 |
| LED3 | 1 | blue 0603 | BLUE | PWR (5 V rail present) — Sheet 02, driven by +5V rail via R3 |
| SW1 | 1 | tact switch SMD | — | Reset (pulls RTL8153B RST_N low) |

---

## Cost estimate

| Category | Single qty | 1k qty |
|---|---|---|
| Critical ICs (U1–U7, U10a–U10c, U11, U12, U101, U102) | $11.50 | $6.85 |
| Magnetics (J1, T1, L1, L2) | $5.20 | $2.80 |
| USB-C receptacle | $0.80 | $0.35 |
| Passives (~80 parts) | $4.00 | $1.20 |
| PCB (4-layer, 60×30 mm) | $4.50 | $0.70 |
| Assembly (JLCPCB) | $7.50 | $2.20 |
| **Total** | **~$31** | **~$13** |

---

## Procurement notes

- **Si3402-B** — single-chip 802.3af PD with integrated 100 V switch and flyback PWM controller. Skyworks announced PoE PD line wind-down in 2025; verify availability before committing. Drop-in alternates: TPS23753APWR (TI, requires external N-FET like SiR882ADP) or LTC4267 (ADI).
- **RTL8153B** — had supply issues 2023–2024. Drop-ins: ASIX AX88179B (different footprint, recompile EEPROM), Microchip LAN7800 (different driver).
- **Flyback transformer** — must be matched to the chosen PD controller's reference design (turns ratio, leakage L, isolation rating). Don't sub blindly.
- **RJ45 magnetics** — must be PoE-rated. Non-PoE jacks fail at the center-tap current.
- **F1 (PPTC fuse)** — protects against host over-draw on VBUS (>2.2 A causes a clean shutoff instead of a brownout). Any 2 A / 6 V PPTC in a 1206 footprint works. If substituting a TPS25940 eFuse for active limiting, update R2 and connect PG/EN per TPS25940 datasheet.
