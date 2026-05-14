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
- Check USB-C connector orientation (TX1/RX1 single-orientation SS)

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

## Fault reference

| Symptom | Likely cause | Check |
|---|---|---|
| Switch never grants PoE | Wrong RDET / RCLS values | R1 = 24.9 kΩ, R2 = 12.1 kΩ — see Stage 2 |
| +5V absent, switch granted power | Flyback not oscillating | U1 COMP network, T1 dot polarity, R_OPT value — see Si3402-B AN1004 Figure 11 |
| +5V present but > 5.1 V | TL431 feedback resistor ratio | R_UPPER / R_LOWER divider — see Si3402-B AN1004 Table 3 |
| USB not detected at all | +3V3 or +1V0 missing | See Stage 3 checklist |
| USB enumerates, wrong VID/PID | EEPROM blank or wrong | Re-program per `firmware/eeprom-image.md` §Programming |
| SS doesn't train, USB 2.0 only | C15/C16 AC-coupling or wrong SS pair routed | See Stage 4; check C15/C16 (100 nF on TX pair) and USB-C orientation |
| Ethernet link won't reach 1G | MDI impedance / length mismatch | See Stage 5; layout review against `docs/design-spec.md` §3.2 rule 4 |
| F1 trips under light load | PPTC fuse in wrong footprint (high resistance part) | Verify MPN: Bourns MF-MSMF200/33X-2 or TE MICROSMD200F-2 |
| Si3402-B very hot at low load | Compensation network oscillating | Replace COMP RC per Si3402-B AN1004 Table 2 |
