"""
Photoelectric Effect Simulation — Pygame 

  - Animated photon beams toward the metal plate
  - Electrons fly out from plate (not random screen positions)
  - Plate glows green/red based on emission state
  - Wavelength colour shown on light beam and slider
  - Work function shown per metal; metal selector added
  - Threshold frequency indicator
  - Cleaner UI with coloured status text
"""

import pygame
import sys
import math
import random
pygame.init()

# ── Constants ──────────────────────────────────────────────
H, E_C, C = 6.626e-34, 1.602e-19, 3e8
H_EV = 4.136e-15

METALS = {
    "Sodium": 2.28,
    "Potassium": 2.30,
    "Zinc": 4.33,
    "Copper": 4.70,
    "Gold": 5.10,
}
METAL_NAMES = list(METALS.keys())

W, H_SCR = 900, 620
screen = pygame.display.set_mode((W, H_SCR))
pygame.display.set_caption("Photoelectric Effect")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
sfont = pygame.font.SysFont("consolas", 14)
bfont = pygame.font.SysFont("consolas", 22, bold=True)

# ── Colours ────────────────────────────────────────────────
BG = (12, 12, 26)
PANEL = (20, 20, 40)
WHITE = (255, 255, 255)
GREY = (120, 120, 140)
DKGREY = (50, 50, 70)
CYAN = (0, 255, 220)
GREEN = (0, 255, 120)
RED = (255, 60, 60)
YELLOW = (255, 220, 60)
ORANGE = (255, 150, 30)


def wl_to_rgb(nm):
    """Wavelength (nm) → (R,G,B) tuple, clamped to [0,255]."""
    w = nm
    if w < 380:
        r, g, b = 150,  0, 255
    elif w < 440:
        r, g, b = int((440-w)/60*200),  0, 255
    elif w < 490:
        r, g, b = 0, int((w-440)/50*255), 255
    elif w < 510:
        r, g, b = 0, 255, int((510-w)/20*255)
    elif w < 580:
        r, g, b = int((w-510)/70*255), 255, 0
    elif w < 645:
        r, g, b = 255, int((645-w)/65*255), 0
    elif w <= 780:
        r, g, b = 255, 0, 0
    else:
        r, g, b = 180, 0, 0
    return (min(r, 255), min(g, 255), min(b, 255))

# ── Slider ─────────────────────────────────────────────────


class Slider:
    def __init__(self, x, y, w, mn, mx, val, label, color=CYAN):
        self.rx, self.ry, self.rw = x, y, w
        self.mn, self.mx, self.val = mn, mx, val
        self.label, self.color = label, color
        self.dragging = False

    @property
    def knob_x(self):
        return int(self.rx + (self.val - self.mn)/(self.mx - self.mn)*self.rw)

    def draw(self, surf):
        # track
        pygame.draw.rect(surf, DKGREY, (self.rx, self.ry +
                         6, self.rw, 6), border_radius=3)
        # filled portion
        fill_w = self.knob_x - self.rx
        if fill_w > 0:
            pygame.draw.rect(surf, self.color,
                             (self.rx, self.ry+6, fill_w, 6), border_radius=3)
        # knob
        pygame.draw.circle(surf, WHITE, (self.knob_x, self.ry+9), 9)
        pygame.draw.circle(surf, self.color, (self.knob_x, self.ry+9), 6)
        # label
        surf.blit(sfont.render(self.label, True, GREY),
                  (self.rx, self.ry - 18))
        surf.blit(sfont.render(f"{self.val:.1f}", True, WHITE),
                  (self.rx + self.rw + 8, self.ry - 2))

    def handle(self, events):
        mx, my = pygame.mouse.get_pos()
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if abs(mx - self.knob_x) < 12 and abs(my - (self.ry+9)) < 12:
                    self.dragging = True
            if ev.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
        if self.dragging and pygame.mouse.get_pressed()[0]:
            raw = (mx - self.rx) / self.rw * (self.mx - self.mn) + self.mn
            self.val = max(self.mn, min(self.mx, raw))

# ── Particles ──────────────────────────────────────────────


class Photon:
    PLATE_X = 520

    def __init__(self, color):
        self.x = 160
        self.y = random.randint(160, 380)
        self.spd = random.uniform(4, 6)
        self.col = color
        self.dead = False
        self.hit = False

    def update(self, emitting):
        if not self.hit:
            self.x += self.spd
            if self.x >= self.PLATE_X:
                self.hit = True
                self.dead = True   # absorbed or bounced — handled outside
        return self.hit

    def draw(self, surf):
        pygame.draw.circle(surf, self.col, (int(self.x), self.y), 5)
        # small glow
        s = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, 60), (9, 9), 9)
        surf.blit(s, (int(self.x)-9, self.y-9))


class Electron:
    def __init__(self, y, ke):
        spd = 2.5 + ke * 0.8
        angle = math.radians(random.uniform(-55, 55))
        self.x, self.y = Photon.PLATE_X + 10, y
        self.vx = spd * math.cos(angle)
        self.vy = spd * math.sin(angle)
        self.life = 255
        self.trail = []

    def update(self):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 12:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 4
        return self.life > 0 and self.x < W - 50

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            a = int(80 * i / len(self.trail))
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s, (80, 255, 160, a), (4, 4), 4)
            surf.blit(s, (tx-4, ty-4))
        pygame.draw.circle(surf, (80, 255, 160), (int(self.x), int(self.y)), 5)
        surf.blit(sfont.render("e⁻", True, GREEN),
                  (int(self.x)+6, int(self.y)-8))


class BouncePhoton:
    """Red photon that bounces back when no emission."""

    def __init__(self, y, col):
        self.x, self.y = Photon.PLATE_X, y
        self.spd = random.uniform(3, 5)
        self.life = 200
        self.col = col

    def update(self):
        self.x -= self.spd
        self.life -= 8
        return self.life > 0 and self.x > 50

    def draw(self, surf):
        a = max(0, self.life)
        s = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 60, 60, a), (6, 6), 5)
        surf.blit(s, (int(self.x)-6, int(self.y)-6))


# ── Metal selector button ───────────────────────────────────
metal_idx = 0
photons = []
electrons = []
bounces = []
spawn_timer = 0

# Sliders
sl_wl = Slider(50,  540, 200, 200, 800, 300,  "Wavelength (nm)")
sl_int = Slider(300, 540, 180,   0, 100,  50,  "Intensity (%)")
sl_volt = Slider(520, 540, 180,   0,   5,   0,  "Stopping Voltage (V)", YELLOW)


def draw_panel(surf, x, y, w, h, title):
    pygame.draw.rect(surf, PANEL, (x, y, w, h), border_radius=8)
    pygame.draw.rect(surf, DKGREY, (x, y, w, h), 1, border_radius=8)
    surf.blit(sfont.render(title, True, GREY), (x+10, y+8))


def draw_text(surf, text, x, y, col=WHITE, f=font):
    surf.blit(f.render(text, True, col), (x, y))


# ── Main loop ──────────────────────────────────────────────
running = True
while running:
    dt = clock.tick(60)
    events = pygame.event.get()

    for ev in events:
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Metal selector
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RIGHT:
                metal_idx = (metal_idx + 1) % len(METAL_NAMES)
            if ev.key == pygame.K_LEFT:
                metal_idx = (metal_idx - 1) % len(METAL_NAMES)

    sl_wl.handle(events)
    sl_int.handle(events)
    sl_volt.handle(events)

    # ── Physics ─────────────────────────────────────────
    metal = METAL_NAMES[metal_idx]
    phi_eV = METALS[metal]
    wl_nm = sl_wl.val
    intens = sl_int.val / 100
    vstop = sl_volt.val

    freq = C / (wl_nm * 1e-9)
    E_eV = H_EV * freq
    KE_max = max(0.0, E_eV - phi_eV)
    f0 = phi_eV / H_EV
    emitting = (E_eV > phi_eV) and (KE_max > vstop)
    current = intens * KE_max * 2.0 if emitting else 0.0
    wl_col = wl_to_rgb(wl_nm)

    # ── Spawn photons ────────────────────────────────────
    spawn_timer += 1
    rate = max(2, int(10 - intens * 8))
    if spawn_timer % rate == 0 and intens > 0:
        photons.append(Photon(wl_col))

    # ── Update photons ───────────────────────────────────
    next_photons = []
    for p in photons:
        hit = p.update(emitting)
        if hit:
            if emitting:
                electrons.append(Electron(p.y, KE_max))
            else:
                bounces.append(BouncePhoton(p.y, wl_col))
        else:
            next_photons.append(p)
    photons = next_photons[-25:]

    electrons = [e for e in electrons if e.update()][-20:]
    bounces = [b for b in bounces if b.update()][-15:]

    # ── Draw ─────────────────────────────────────────────
    screen.fill(BG)

    # Light beam glow from source to plate
    beam_surf = pygame.Surface((W, H_SCR), pygame.SRCALPHA)
    for i in range(8):
        alpha = max(0, int(intens * 25 - i*3))
        pygame.draw.line(beam_surf, (*wl_col, alpha),
                         (130, 100 + i*4), (Photon.PLATE_X, 100 + i*4), 2)
    screen.blit(beam_surf, (0, 0))

    # Light source bulb
    pygame.draw.circle(screen, YELLOW, (110, 270), 30)
    pygame.draw.circle(screen, (255, 255, 200), (110, 270), 20)
    draw_text(screen, "Light", 80, 305, GREY, sfont)
    draw_text(screen, "Source", 77, 320, GREY, sfont)

    # Beam rays
    for dy in [-80, -40, 0, 40, 80]:
        col_a = (*wl_col, int(intens * 120))
        s = pygame.Surface((W, H_SCR), pygame.SRCALPHA)
        pygame.draw.line(s, col_a, (130, 270+dy), (Photon.PLATE_X, 270+dy), 2)
        screen.blit(s, (0, 0))

    # Metal plate
    plate_col = (0, 200, 80) if emitting else (200, 40, 40)
    glow_col = (0, 255, 100, 40) if emitting else (255, 40, 40, 40)
    gs = pygame.Surface((40, 300), pygame.SRCALPHA)
    gs.fill((*glow_col[:3], 30))
    screen.blit(gs, (Photon.PLATE_X - 10, 110))
    pygame.draw.rect(screen, plate_col, (Photon.PLATE_X,
                     120, 18, 280), border_radius=4)
    draw_text(screen, "Cathode", Photon.PLATE_X - 10, 408, GREY, sfont)

    # Collector
    pygame.draw.rect(screen, DKGREY, (730, 120, 14, 280), border_radius=4)
    draw_text(screen, "Anode", 722, 408, GREY, sfont)

    # Circuit wire
    pygame.draw.lines(screen, DKGREY, False,
                      [(529, 400), (529, 450), (738, 450), (738, 400)], 2)
    pygame.draw.circle(screen, DKGREY, (634, 450), 18, 2)
    draw_text(screen, "A", 628, 443, CYAN, sfont)

    # Particles
    for p in photons:
        p.draw(screen)
    for b in bounces:
        b.draw(screen)
    for e in electrons:
        e.draw(screen)

    # ── Info panel (top right) ────────────────────────────
    draw_panel(screen, 580, 10, 305, 200, "")

    # Metal name + selector hint
    draw_text(screen, f"Metal: {metal}", 590, 18, CYAN, font)
    draw_text(screen, "← → to change", 590, 38, GREY, sfont)

    phi_col = GREEN if E_eV >= phi_eV else RED
    draw_text(
        screen, f"Work function φ  = {phi_eV:.2f} eV", 590,  62, WHITE, sfont)
    draw_text(
        screen, f"Photon energy E  = {E_eV:.2f} eV",   590,  80, YELLOW, sfont)
    draw_text(
        screen, f"Threshold freq   = {f0:.2e} Hz",     590,  98, GREY, sfont)
    draw_text(
        screen, f"Max KE           = {KE_max:.2f} eV", 590, 116, phi_col, sfont)
    draw_text(
        screen, f"Current          = {current:.2f} μA", 590, 134, phi_col, sfont)

    # Status badge
    if emitting:
        status, scol, sbg = "● EMITTING", GREEN, (0, 40, 20)
    else:
        reason = "E < φ" if E_eV < phi_eV else "stopped by V"
        status, scol, sbg = f"✖ NO EMISSION  ({reason})", RED, (40, 0, 0)
    pygame.draw.rect(screen, sbg,  (590, 158, 288, 42), border_radius=6)
    pygame.draw.rect(screen, scol, (590, 158, 288, 42), 1, border_radius=6)
    draw_text(screen, status, 598, 168, scol, sfont)

    # Wavelength colour swatch
    pygame.draw.rect(screen, wl_col, (590, 208, 40, 16), border_radius=3)
    draw_text(screen, f"{wl_nm:.0f} nm", 636, 207, GREY, sfont)

    # Sliders
    sl_wl.color = wl_col
    for sl in [sl_wl, sl_int, sl_volt]:
        sl.draw(screen)

    # Slider labels at bottom
    draw_text(screen, "Wavelength (nm)", 50,  518, GREY, sfont)
    draw_text(screen, "Intensity (%)",  300, 518, GREY, sfont)
    draw_text(screen, "Stopping V",     520, 518, GREY, sfont)

    pygame.display.flip()

pygame.quit()
sys.exit()
