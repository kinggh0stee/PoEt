# Bring-Up Guide — PoEt Rev A

Work through these stages in order. Each stage verifies one functional block before the next is powered. **Do not skip ahead.** The PoE primary runs at up to 57 V; a wiring error found in Stage 1 costs nothing. The same error found in Stage 3 can destroy the RTL8153B.

> **Capacitor discharge:** After removing PoE or bench PSU power, wait at least 10 seconds before probing or reworking the primary side. C1 (10 µF / 100 V) and C2 (47 µF / 100 V) can hold charge above 50 V. Confirm V_POE+ < 5 V with a DMM before touching primary-side pads.

> **Ground coupling:** Y-cap C3 (1 nF / 2 kV) weakly couples `GND_POE` to secondary `GND`. The USB-C shell is therefore not fully floating from the PoE primary. If the PoE switch and the USB host have different protective-earth potentials, small common-mode currents flow through the host. This is normal EMC practice but means the board is not galvanically safe to touch on both sides simultaneously while powered.

---

## Before you touch a PSU

### Visual inspection checklist

- [ ] Board has no solder bridges (use a loupe or macro lens)
- [ ] All polarized parts placed correctly: C2 (Al electrolytic), D1/D2/D3/D4 (cathode stripe orientation), U6 PC817B (dot = Pin 1)
- [ ] T1 transformer installed in the correct orientation — dot (primary) to Pin 1, confirmed against Würth 750313638 datasheet pin map
- [ ] U1 Si3402-B seated flush; no lifted pins visible
- [ ] No components in the 4 mm isolation gap (check F.Cu and B.Cu under T1)
- [ ] J2 USB-C receptacle shell tabs soldered (mechanical strain relief)

### Cold resistance checks (board unpowered, DMM in resistance mode)

| Point | Expected | Action if wrong |
|---|---|---|
| V_POE+ to GND_POE | > 20 kΩ (RDET pulldown in circuit) | Short — find bridge on primary bulk caps or bridges |
| +5V to GND | > 1 kΩ | Short — find bridge on secondary bulk caps or RTL8153B pads |
| VBUS to GND | > 100 Ω (F1 in circuit + caps) | If < 10 Ω: short on VBUS node, check C11–C14 and F1 |
| CC1 to GND | ~22 kΩ ± 10 % | R10 value check |
| CC2 to GND | ~22 kΩ ± 10 % | R11 value check |
| GND_POE to GND | high-Z (MΩ) or open | Direct short = missing isolation — **do not power up** |

---

## Stage 1 — Primary side only (bench PSU, no PoE switch)

**Goal:** verify the Schottky bridges, bulk cap, TVS, and Si3402-B power-on sequence.

**Setup:**
- Bench PSU: 48 V DC, **current limit 150 mA**
- Connect PSU+ to both `PAIR_A_HI` and `PAIR_B_HI` test points (tied together — simulates DC PoE on both pair-sets simultaneously)
- Connect PSU− to both `PAIR_A_LO` and `PAIR_B_LO` test points

This drives DC through D1 and D2 bridges simultaneously, just as a PoE PSE would (the bridges are polarity-insensitive, so DC in = DC rectified on V_POE+). If your board has no test points on the PAIR lines yet, skip to Stage 2 and use a real PoE switch.

**Procedure:**
1. Set current limit, then apply 48 V.
2. Measure V_POE+ to GND_POE — expect **47–48 V** (one Schottky bridge diode drop from each pair-set).
3. Check current draw — expect **< 20 mA** at idle (Si3402-B detection resistor quiescent current only; flyback is not running).
4. Measure Si3402-B `PWOK` pin — if exposed on a test point, it should go high after ~80 ms as detection completes.
5. **Do not expect +5V yet** — Si3402-B's flyback won't run without a valid PoE PD detection sequence from a real PSE.

> If current draw is > 100 mA immediately: remove power, look for a short on V_POE+ rail.

---

## Stage 2 — PoE switch, primary + flyback

**Goal:** verify PoE PD negotiation (detect + classify) and flyback output.

**Setup:**
- PoE switch with 802.3af support (UniFi switch, Cisco 2960-P, Netgear GS308P, or similar)
- Short Ethernet cable, tested working
- Board connected — J1 RJ45 plugged into the PoE switch port

**Procedure:**
1. Plug in the RJ45. The switch will begin PD detection.
2. Watch the switch's per-port PoE LED — it should go green within 2–3 seconds (detection + classification complete).
3. Measure V_POE+ — expect **36–57 V** depending on cable length and PSE output.
4. Measure +5V to GND — expect **4.9–5.1 V**.
5. Measure current on switch port — expect **30–150 mA at 48 V** (idle, no USB host connected). At full USB load this rises to ~270 mA (12.95 W / 48 V).

**If the switch doesn't grant power:**
- Measure RDET resistor (R1): should be 24.9 kΩ ± 1 %
- Measure RCLS resistor (R2): should be 12.1 kΩ ± 1 %
- Try a different switch — some budget switches have strict detection windows

---

## Stage 3 — LDO bias rails

**Goal:** verify AP2112K-3.3 and RT9013-10GB are running.

**With PoE power on from Stage 2:**

| Rail | Pin to measure | Expected |
|---|---|---|
| +3V3 | U4 output pin | 3.27–3.33 V |
| +1V0 | U5 output pin | 0.97–1.03 V |
| U4 EN pin | should be pulled high (100 kΩ to +5V) | ≥ 4.5 V |
| U5 EN pin | should be pulled high (100 kΩ to +5V) | ≥ 4.5 V |

If a rail is missing: check EN pull-up resistors (Sheet 03), check input bypass cap, verify LDO is not in thermal shutdown.

---

## Stage 4 — USB enumeration

**Goal:** RTL8153B enumerates as a USB Ethernet adapter.

**Setup:**
- Board still PoE-powered
- USB-C cable to a Linux host (USB 2.0 or 3.0 cable, correct orientation for SS if using USB 3.0)

**Procedure:**
1. Plug in USB-C cable.
2. On the Linux host: `dmesg | tail -20`
3. Expect to see:
   ```
   usb N-N: new SuperSpeed USB device number X using xhci_hcd
   usb N-N: New USB device found, idVendor=0bda, idProduct=8153
   r8152 N-N:1.0: v2.x.x
   r8152 N-N:1.0: eth0: RTL8153B
   ```
4. If USB 2.0 only (no SS): `dmesg` will say "high speed" and show 480 Mbps. Acceptable for bring-up; investigate AC-coupling caps (C15/C16) if SS never trains.
5. `ip link show eth0` — interface should appear.

**If nothing appears in dmesg:**
- Check +3V3 and +1V0 (Stage 3 must be clean)
- Check crystal Y1 — 25 MHz should be visible on an oscilloscope at the XTAL pins
- Check U3 EEPROM: if blank or misconfigured, RTL8153B may enumerate with wrong VID/PID (won't bind to `r8152`). Re-program EEPROM per `firmware/eeprom-image.md`.
- Check USB-C connector orientation; try flipping the cable — U11 mux should route to TX1/RX1 or TX2/RX2 depending on which CC pin is active. If SS trains in one orientation but not the other, check U12 comparator output (SS_SEL should toggle with cable flip) and U11 SEL pin.

---

## Stage 5 — Ethernet link

**Goal:** Gigabit Ethernet link established.

**Procedure:**
1. The same PoE switch port that is powering the board also carries Ethernet data — this is normal 802.3af operation. Plug J1 into the same switch port that is already granting PoE power.

2. `ip link show eth0` — should show `state UP` after a few seconds.
3. `ethtool eth0` — confirm `Speed: 1000Mb/s, Duplex: Full`.
4. Ping the switch IP — expect < 1 ms latency.
5. Run a quick throughput test: `iperf3 -c <switch_ip> -t 10` — expect > 900 Mbps for Gigabit.

**If link stays at 100 Mbps or won't establish Gigabit:**
- Verify Cat5e or better cable (Cat3 won't do 1000BASE-T)
- Check MDI trace length matching (all 4 pairs within 5 mm per design-spec §3.2 rule 4)
- Check Bob Smith termination — if the magjack doesn't have it integrated, it needs to be added externally

---

## Stage 6 — Full-load thermal test

**Goal:** confirm thermal performance at rated output.

**Setup:**
- USB-C cable to a host capable of drawing 1.5 A (Raspberry Pi 4 under load, or a USB load tester)
- Ethernet active (iperf3 running simultaneously)

**Procedure:**
1. Run combined load for 15 minutes.
2. Measure temperatures with an IR thermometer or thermocouple:

   | Component | Expected (ambient 25 °C) | Concern threshold |
   |---|---|---|
   | U1 Si3402-B | < 70 °C | > 85 °C: improve thermal pour |
   | T1 transformer | < 65 °C | > 80 °C: check winding resistance |
   | D1, D2 bridges | < 55 °C | > 70 °C: check trace width on V_POE+ |
   | U2 RTL8153B | < 60 °C | > 75 °C: improve GND pour under chip |

3. Measure actual output voltage at J2 VBUS under load — should be ≥ 4.75 V at 1.5 A (TL431 regulation).
4. Measure F1 fuse voltage drop — should be < 100 mV at 1.5 A for a fresh PPTC.

---

## Stage 7 — Pre-compliance safety screening (CSA / 62368-1 readiness)

**Goal:** catch insulation and thermal failures in-house before sending samples
to an NRTL. None of these tests certify the product, but failures here are
near-certain failures at the lab. See `docs/CSA-COMPLIANCE.md` for the standards
mapping and the open items list.

> **Safety.** Stage 7 applies 3 kV between exposed conductors. Use a dedicated
> hi-pot tester with a ground-fault interlock and a high-voltage probe.
> Do **not** use a regular bench DMM. Wear insulated gloves; clear the bench;
> never leave the tester unattended while energized.

### 7.1 Dielectric strength (hi-pot), routine production test

**Equipment:** AC hi-pot tester capable of 3 kV rms with adjustable trip
current (e.g. Slaughter 2700, GW Instek GPT-9904A, Vitrek 944i)

**Setup:**
- Board unpowered, no PoE input, no USB cable
- Short all primary-side test points together (PAIR_A_HI, PAIR_A_LO,
  PAIR_B_HI, PAIR_B_LO, V_POE+, GND_POE) — this is the "primary" terminal
- Short all secondary-side exposed conductors (+5 V test point, GND test
  point, USB-C shell via the receptacle case) — this is the "secondary"
  terminal
- Connect hi-pot HV lead to primary; return to secondary

**Procedure:**
1. Ramp at ≤ 500 V/s to **3000 V rms, 50/60 Hz**.
2. Hold for **60 seconds**.
3. Trip current set to **5 mA**.

**Pass:** no breakdown, no flashover, no arc, leakage current stays ≤ 5 mA
for the full hold time.

**Common failures:**
- Trip on ramp → check for solder bridge or contamination across the slot
- Trip at 1.5–2 kV → Y-cap C3 is Y2-rated (Y2 typical breakdown ~3 kV vs Y1
  ~8 kV — confirm the part is Y1 per BOM)
- Optocoupler U6 breakdown → wrong grade; needs PC817B-X1 or TLP785

### 7.2 Insulation resistance

**Equipment:** Megohmmeter at 500 V DC (e.g. Fluke 1507, Megger MIT415)

**Procedure:**
1. Same primary / secondary terminals as §7.1.
2. Apply **500 V DC for 60 seconds**.
3. Read insulation resistance after the 60 s soak.

**Pass:** ≥ **100 MΩ**. 62368-1 §5.4.9.2 sets 2 MΩ as the bare minimum after a
humidity preconditioning step; 100 MΩ on a clean board is realistic.

### 7.3 Touch current (leakage)

**Equipment:** Touch-current meter implementing the IEC 60990 networks A & B
(e.g. Megger PAT420, Chroma 19032)

**Setup:**
- Board powered from a calibrated 802.3af PoE injector at **1.06× nominal
  voltage** (60 V rather than 57 V) per §5.7.4
- USB-C plugged into an isolated USB host
- Touch-current meter clipped between the USB-C shell and protective earth

**Pass:** ≤ **0.25 mA** (Class II equipment limit, §5.7.4 Table 5).

> Expect leakage roughly equal to the charging current through C3. With C3 =
> 1 nF and 60 Hz mains-equivalent disturbance, capacitive leakage is far
> below 0.25 mA — but verify on an actual sample.

### 7.4 Temperature rise at 25 °C ambient (extended)

Stage 6 covers a 15-minute thermal check. For 62368-1 §B.2.6 you need a full
**thermal-equilibrium** measurement (typically 1–2 h until ΔT < 1 °C / 30 min).

**Procedure:**
1. Repeat the Stage 6 setup (1.5 A USB load + iperf3 saturating Gigabit).
2. Log temperature every 5 min on:
   - U1 Si3402-B package top
   - T1 transformer core
   - U2 RTL8153B package top
   - PCB surface midway between primary and secondary (FR-4 max 105 °C)
   - Bulk caps C1 (X7R 1210) and C2 (Al electrolytic)
3. Wait until two consecutive readings ≤ 1 °C apart on every channel.
4. Record ambient at each reading and compute rise: ΔT = T_part − T_ambient.

**Pass criteria (62368-1 Table B.10, abbreviated):**

| Material | T_max | Typical headroom needed |
|---|---|---|
| FR-4 PCB | 105 °C | ΔT ≤ 80 °C at 25 °C ambient |
| X7R ceramic | 125 °C | ΔT ≤ 100 °C |
| Al electrolytic (C2) | per datasheet, typically 105 °C | ΔT ≤ 80 °C |
| Transformer winding (Class B insulation) | 130 °C | ΔT ≤ 105 °C |
| Optocoupler PC817 | per datasheet, typically 110 °C | ΔT ≤ 85 °C |

### 7.5 Temperature rise at 40 °C ambient

Same as §7.4 but in a 40 °C environmental chamber. 62368-1 expects 25 °C
ambient with allowance for a max operating ambient marked on the product;
if you market for 40 °C operation, this test is required.

### 7.6 Abnormal operation — output short

**Procedure:**
1. PoE-power the board normally.
2. Short USB-C VBUS to GND with a low-resistance shunt (< 100 mΩ).
3. Hold for **7 hours** (§B.4.5 single-fault test duration).
4. Monitor: thermal IR camera or thermocouples on U1, T1, F1, PCB hot spots.

**Pass:**
- No fire, no breach of the enclosure, no expulsion of molten material
- F1 (PPTC) latches into high-impedance state quickly (< 5 s) and stays there
- No damage to the PoE PSE (port should reach its OCP threshold and remove
  power, then re-attempt detection per 802.3 — this is normal)
- After removing the short and cycling PoE, the board recovers and re-enumerates

### 7.7 Abnormal operation — RJ45 cable short to mains

Not feasible to test in-house; this is one for the NRTL. Documented here for
the technical file: a 230 V AC application to the RJ45 pins shall not breach
the isolation barrier or cause an unsafe state on the USB-C side. The Y1
C3 + transformer reinforced insulation are the protective elements.

### 7.8 Sign-off checklist before NRTL submission

- [ ] §7.1 hi-pot 3 kV / 60 s passed on **all** sample units (production
      sample size = NRTL's choice, usually 5–10)
- [ ] §7.2 IR ≥ 100 MΩ on all samples
- [ ] §7.3 touch current ≤ 0.25 mA on all samples
- [ ] §7.4 thermal margins documented; no material exceeds Table B.10
- [ ] §7.5 40 °C ambient repeat passes (only if claiming 40 °C operation)
- [ ] §7.6 7 h output short held; no fire, recovery confirmed
- [ ] All BOM **§ CSA** lines have certificate numbers recorded
- [ ] `docs/CSA-COMPLIANCE.md` §8 open items all closed

---

## Fault reference

| Symptom | Likely cause | Check |
|---|---|---|
| Switch never grants PoE | Wrong RDET / RCLS values | R1 = 24.9 kΩ, R2 = 12.1 kΩ — see Stage 2 |
| +5V absent, switch granted power | Flyback not oscillating | U1 COMP network, T1 dot polarity, R_OPT value — see Si3402-B AN1004 Figure 11 |
| +5V present but > 5.1 V | TL431 feedback resistor ratio | R_UPPER / R_LOWER divider — see Si3402-B AN1004 Table 3 |
| USB not detected at all | +3V3 or +1V0 missing | See Stage 3 checklist |
| USB enumerates, wrong VID/PID | EEPROM blank or wrong | Re-program per `firmware/eeprom-image.md` §Programming |
| SS doesn't train in either orientation | C15/C16 AC-coupling caps or U11 mux wiring | See Stage 4; verify C15/C16 are on SSTX upstream of U11; check U11 VCC = +3V3 (not 5V); check U11 SEL receives a valid logic level |
| SS trains in one orientation only | U12 comparator not detecting CC or U11 SEL stuck | Probe SS_SEL with DMM while flipping cable — should toggle between ~0 V and ~3.3 V; if stuck, check R12 pull-up (10 kΩ to +3V3) and U12 IN+/IN- wiring to CC1/CC2 |
| Ethernet link won't reach 1G | MDI impedance / length mismatch | See Stage 5; layout review against `docs/design-spec.md` §3.2 rule 4 |
| F1 trips under light load | PPTC fuse in wrong footprint (high resistance part) | Verify MPN: Bourns MF-MSMF200/33X-2 or TE MICROSMD200F-2 |
| Si3402-B very hot at low load | Compensation network oscillating | Replace COMP RC per Si3402-B AN1004 Table 2 |
