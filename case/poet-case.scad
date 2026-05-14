// PoEt Rev A — parametric snap-fit enclosure
// Board: 60 × 30 mm, 4-layer, 1.6 mm thick
//
// Print orientation (both parts are already in print-ready orientation)
//   Bottom shell : open face UP  — no rotation needed
//   Top shell    : ceiling face DOWN (Z=0) — no rotation needed; skirt prints upward
//                  Flip physically to assemble: press skirt into bottom shell until beads click
//
// VERIFY clr_top and all connector dimensions against real parts before printing.
// Print a single-wall cross-section first.

/* ═══ Board dimensions ═══════════════════════════════════════════════════ */
pcb_l = 60.0;   // board length (X)
pcb_w = 30.0;   // board width  (Y)
pcb_t =  1.6;   // board thickness

/* ═══ Interior clearances ════════════════════════════════════════════════ */
clr_bot  = 2.0;  // floor to PCB bottom  (standoff height)
clr_top  = 12.0; // PCB top to ceiling inner face
                  // T1 transformer (Würth 750313638) ≈ 10 mm → 12 mm = 2 mm headroom
clr_side = 0.5;  // per-side gap between PCB edge and inner wall

/* ═══ Wall & snap geometry ═══════════════════════════════════════════════ */
wall    = 2.0;   // shell wall thickness
skirt_t = 1.5;   // top-shell inner skirt thickness
overlap = 5.0;   // skirt insertion depth into bottom shell
fit_gap = 0.2;   // radial clearance: skirt OD vs cavity ID (each side)

bead_h  = 1.5;   // snap bead height (Z)
bead_d  = 0.9;   // snap bead radial depth (into wall groove)
grove_tol = 0.2; // extra groove width per side for tolerance

/* ═══ Connector cutouts ══════════════════════════════════════════════════ */
// RJ45 — Bel Fuse 0826-1G1T-DV-F, back face (X-min end, "PAIR" end of board)
rj45_w = 16.5;  // opening width  (Y)  — verify against datasheet
rj45_h = 14.5;  // opening height (Z)  — includes LED indicators above body

// USB-C — GCT USB4105-GF-A mid-mount, front face (X-max end of board)
usbc_w =  9.5;  // opening width  (Y)
usbc_h =  4.5;  // opening height (Z): mid-mount body ≈ 3.3 mm + plug clearance

/* ═══ LED windows — top face ══════════════════════════════════════════════ */
// LED1=LINK (green), LED2=ACT (yellow), LED3=PWR (blue); see docs/bom.md.
// Positions measured from X=0 (RJ45 end) of PCB. Adjust to match KiCad layout.
led_dia  = 3.2;          // window bore (slightly over 3 mm LED lens)
led_xpos = [8, 20, 32];  // X from RJ45 end (PCB coords)
led_ypos = 15.0;         // Y from Y=0 edge (PCB coord, = board centre)

/* ═══ Reset-button pinhole ════════════════════════════════════════════════ */
// SW1 tact switch (Sheet 04). Adjust to match KiCad placement.
sw_dia  = 2.5;   // bore for a 2 mm tool
sw_xpos = 48.0;  // X from RJ45 end (PCB coord)
sw_ypos = 15.0;  // Y from Y=0 edge (PCB coord)

/* ═══ PCB standoffs ══════════════════════════════════════════════════════ */
so_od = 4.0;  // standoff outer diameter
so_id = 1.8;  // screw bore (M2 self-tap); set to 0 for solid boss
// Standoff XY centres in PCB coordinates (from PCB corner at X=0, Y=0)
so_pos = [[3.5, 3.5], [56.5, 3.5], [3.5, 26.5], [56.5, 26.5]];

/* ═══ Derived dimensions ══════════════════════════════════════════════════ */
out_l = pcb_l + 2*clr_side + 2*wall;
out_w = pcb_w + 2*clr_side + 2*wall;

// Bottom shell height: tall enough so groove doesn't punch through floor
// floor=wall, clr_bot=2, pcb_t=1.6 → floor-to-PCB-top = 5.6; add 2 mm above PCB
bot_h = max(8.0, wall + clr_bot + pcb_t + 2.0);

// Top shell height (ceiling plate + headroom above PCB)
top_h = wall + clr_top;

// Inner cavity XY (the hollow inside the shell walls)
cav_l = out_l - 2*wall;
cav_w = out_w - 2*wall;

// Snap groove in bottom-shell inner wall, measured from shell floor
groove_w   = bead_h + 2*grove_tol;
groove_z   = bot_h - 2.5 - bead_h;   // 2.5 mm below top rim
groove_dep = fit_gap + bead_d + 0.15; // depth cut into inner wall face

// Snap bead on skirt (Z from skirt bottom) aligned with groove when assembled
bead_z_sk = groove_z - bot_h + overlap;

// Skirt outer and inner dimensions (centred in XY)
sk_ol = cav_l - 2*fit_gap;  // skirt outer length
sk_ow = cav_w - 2*fit_gap;  // skirt outer width
sk_il = sk_ol - 2*skirt_t;  // skirt inner length
sk_iw = sk_ow - 2*skirt_t;  // skirt inner width

// Origin used throughout: shell body centred in XY, floor at Z=0
// PCB origin (X=0,Y=0 corner of board) maps to shell coords:
//   pcb_x0 = -out_l/2 + wall + clr_side
//   pcb_y0 = -out_w/2 + wall + clr_side

function pcb2x(x) = -out_l/2 + wall + clr_side + x;
function pcb2y(y) = -out_w/2 + wall + clr_side + y;

/* ═══ Utility ════════════════════════════════════════════════════════════ */
module rbox(l, w, h, r=1.0) {
    // Rounded-corner box, centred in XY, bottom at Z=0
    hull()
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*(l/2-r), sy*(w/2-r), 0])
                cylinder(r=r, h=h, $fn=32);
}

module ccube(lx, ly, lz) {
    // Cube centred in XY, bottom at Z=0
    translate([-lx/2, -ly/2, 0]) cube([lx, ly, lz]);
}

/* ═══ Bottom shell ═══════════════════════════════════════════════════════ */
module bottom_shell() {
    difference() {
        rbox(out_l, out_w, bot_h);

        // ── Interior cavity (open top) ───────────────────────────────── //
        translate([0, 0, wall])
            ccube(cav_l, cav_w, bot_h);  // extra height is fine — just removes air

        // ── Snap grooves in the two long inner walls (+Y and -Y) ─────── //
        // Cut a channel outward from the inner face into the wall material
        for (sy = [-1, 1]) {
            // inner face at y = sy*cav_w/2; groove goes further out by groove_dep
            gy = sy * (cav_w/2 + groove_dep/2);
            translate([0, gy, groove_z + groove_w/2])
                cube([cav_l + 0.02, groove_dep, groove_w], center=true);
        }

        // ── RJ45 cutout — back face (X = -out_l/2) ──────────────────── //
        // Board sits so the RJ45 end is at the -X wall
        translate([-out_l/2 - 0.01,
                   -rj45_w/2,
                   wall + clr_bot])
            cube([wall + 0.02, rj45_w, rj45_h]);

        // ── USB-C cutout — front face (X = +out_l/2) ────────────────── //
        // Mid-mount: opening from just above floor to usbc_h
        translate([out_l/2 - wall - 0.01,
                   -usbc_w/2,
                   wall + clr_bot - 0.5])   // 0.5 mm below PCB-bottom floor
            cube([wall + 0.02, usbc_w, usbc_h + 1.0]);
    }

    // ── PCB standoffs ────────────────────────────────────────────────── //
    for (p = so_pos) {
        translate([pcb2x(p[0]), pcb2y(p[1]), wall])
            difference() {
                cylinder(d=so_od, h=clr_bot, $fn=24);
                if (so_id > 0)
                    cylinder(d=so_id, h=clr_bot + 0.01, $fn=18);
            }
    }
}

/* ═══ Top shell ══════════════════════════════════════════════════════════ */
// Print orientation: Z=0 = ceiling outer face (on bed); everything else
// extends upward in positive Z (rim, skirt, beads all point toward sky while
// printing). In the assembled case, the top shell is flipped so the ceiling
// faces upward and the skirt drops into the bottom shell.
//
// Z landmarks (in print orientation, Z=0 on bed):
//   0               ceiling outer face (bed)
//   wall            ceiling inner face
//   wall+rim_h      top of cosmetic rim
//   wall+rim_h+overlap  top of skirt (= shell interior side)
module top_shell() {
    rim_h   = 1.5;  // cosmetic outer rim height
    skirt_z = wall + rim_h;  // Z where skirt starts

    // Snap bead Z centre in print coords:
    // In assembly the bead is bead_z_sk from the skirt tip (the end that
    // enters the bottom shell). In print orientation, that tip is at the
    // FAR end from the bed (Z = skirt_z + overlap). Count inward by
    // bead_z_sk + bead_h/2 to find the bead centre.
    bead_zc = skirt_z + overlap - bead_z_sk - bead_h/2;

    difference() {
        union() {
            // ── Ceiling plate ─────────────────────────────────────────── //
            rbox(out_l, out_w, wall);

            // ── Cosmetic outer rim above ceiling ──────────────────────── //
            translate([0, 0, wall])
                difference() {
                    rbox(out_l, out_w, rim_h);
                    ccube(cav_l, cav_w, rim_h + 0.01);
                }

            // ── Inner snap skirt ──────────────────────────────────────── //
            translate([0, 0, skirt_z])
                difference() {
                    ccube(sk_ol, sk_ow, overlap);
                    ccube(sk_il, sk_iw, overlap + 0.01);
                }

            // ── Snap beads on long skirt faces (+Y and -Y) ────────────── //
            for (sy = [-1, 1]) {
                translate([0,
                           sy * (sk_ow/2 + bead_d/2),
                           bead_zc])
                    cube([sk_ol - 6, bead_d, bead_h], center=true);
            }
        }

        // ── LED windows through ceiling (bore from outer face inward) ── //
        for (i = [0 : len(led_xpos)-1]) {
            translate([pcb2x(led_xpos[i]), pcb2y(led_ypos), -0.01])
                cylinder(d=led_dia, h=wall + 0.02, $fn=24);
        }

        // ── Reset-button pinhole ──────────────────────────────────────── //
        translate([pcb2x(sw_xpos), pcb2y(sw_ypos), -0.01])
            cylinder(d=sw_dia, h=wall + 0.02, $fn=20);
    }
}

/* ═══ Print layout ═══════════════════════════════════════════════════════ */
spacing = out_l + 8;

// Bottom shell: open face up — no rotation needed
translate([-spacing/2, 0, 0])
    bottom_shell();

// Top shell: already in print orientation (ceiling outer face at Z=0)
translate([spacing/2, 0, 0])
    top_shell();
