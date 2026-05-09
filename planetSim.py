import pygame
import math
import random

# ─── Init ────────────────────────────────────────────────────────────────────
pygame.init()

WIN = pygame.display.set_mode((0, 0), pygame.WINDOWMAXIMIZED)
WIDTH, HEIGHT = WIN.get_size()
pygame.display.set_caption("Solar System Simulation")

SIM_WIDTH   = int(WIDTH * 0.70)
PANEL_X     = SIM_WIDTH
PANEL_W     = WIDTH - SIM_WIDTH
PANEL_COLOR = (25, 28, 38)
DIVIDER_CLR = (60, 65, 85)
TEXT_CLR    = (220, 225, 240)
DIM_CLR     = (130, 140, 165)
ACCENT_CLR  = (100, 180, 255)

FPS         = 120
ORBIT_TAIL  = 900           # max orbit points kept per body
STAR_COUNT  = 350

# ─── Star field ──────────────────────────────────────────────────────────────
random.seed(42)
stars = [
    (
        random.randint(0, SIM_WIDTH),
        random.randint(0, HEIGHT),
        random.uniform(0.4, 2.0),           # radius
        random.randint(160, 255),            # base brightness
        random.uniform(0, math.tau),         # twinkle phase offset
        random.uniform(0.4, 1.2),            # twinkle speed
    )
    for _ in range(STAR_COUNT)
]

def draw_stars(surface, t):
    for sx, sy, r, base_b, phase, speed in stars:
        brightness = int(base_b * (0.75 + 0.25 * math.sin(t * speed + phase)))
        col = (brightness, brightness, brightness)
        if r < 1.0:
            surface.set_at((sx, sy), col)
        else:
            pygame.draw.circle(surface, col, (sx, sy), int(r))

# ─── Glow helper ─────────────────────────────────────────────────────────────
def draw_glow(surface, color, pos, radius, layers=6):
    for i in range(layers, 0, -1):
        alpha = int(18 * (i / layers))
        r_off = int(radius * i * 0.55)
        glow_surf = pygame.Surface((r_off * 2, r_off * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, alpha), (r_off, r_off), r_off)
        surface.blit(glow_surf, (pos[0] - r_off, pos[1] - r_off))

# ─── Body class ──────────────────────────────────────────────────────────────
class Body:
    AU      = 149.6e6 * 1000
    GRAVITY = 6.67428e-11

    SCALE     = 80 / AU
    MIN_SCALE = 15  / AU
    MAX_SCALE = 200 / AU
    TIMESTEP  = 3600 * 24          # one simulation day per frame step

    def __init__(self, name, x, y, radius, color, mass,
                 orbital_period_days=None, description=""):
        self.name                = name
        self.x                   = x
        self.y                   = y
        self.base_radius         = radius
        self.color               = color
        self.mass                = mass
        self.orbital_period_days = orbital_period_days
        self.description         = description

        self.sun    = False
        self.orbit  = []          # list of (x, y) in simulation coords
        self.x_vel  = 0.0
        self.y_vel  = 0.0
        self.days_elapsed = 0

    # ── screen position ───────────────────────────────────────────────────────
    def screen_pos(self, offset_x, offset_y):
        return (
            self.x * self.SCALE + offset_x,
            self.y * self.SCALE + offset_y,
        )

    # ── drawing ───────────────────────────────────────────────────────────────
    def draw(self, window, offset_x, offset_y, selected):
        sx, sy = self.screen_pos(offset_x, offset_y)

        # orbit trail
        if len(self.orbit) > 2:
            tail   = self.orbit[-ORBIT_TAIL:]
            n      = len(tail)
            points = []
            for i, (px, py) in enumerate(tail):
                points.append((
                    px * self.SCALE + offset_x,
                    py * self.SCALE + offset_y,
                ))
            # draw trail in segments so it fades toward the oldest end
            seg = max(1, n // 4)
            for seg_i in range(4):
                start = seg_i * seg
                end   = min(n, start + seg + 1)
                if end - start < 2:
                    continue
                alpha_factor = (seg_i + 1) / 4
                r = int(self.color[0] * alpha_factor)
                g = int(self.color[1] * alpha_factor)
                b = int(self.color[2] * alpha_factor)
                pygame.draw.lines(window, (r, g, b), False, points[start:end], 1)

        scale_factor = self.SCALE / (80 / self.AU)
        draw_radius  = max(2, int(self.base_radius * scale_factor))

        # sun glow
        if self.sun:
            draw_glow(window, self.color, (int(sx), int(sy)), draw_radius + 10)

        # highlight ring when selected
        if selected:
            pygame.draw.circle(window, ACCENT_CLR,
                               (int(sx), int(sy)), draw_radius + 4, 1)

        pygame.draw.circle(window, self.color, (int(sx), int(sy)), draw_radius)

    # ── physics ───────────────────────────────────────────────────────────────
    def attraction(self, other):
        dx  = other.x - self.x
        dy  = other.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return 0.0, 0.0
        force = self.GRAVITY * self.mass * other.mass / dist ** 2
        theta = math.atan2(dy, dx)
        return math.cos(theta) * force, math.sin(theta) * force

    def update_position(self, bodies):
        total_fx = total_fy = 0.0
        for body in bodies:
            if body is self:
                continue
            fx, fy   = self.attraction(body)
            total_fx += fx
            total_fy += fy

        self.x_vel += total_fx / self.mass * self.TIMESTEP
        self.y_vel += total_fy / self.mass * self.TIMESTEP
        self.x     += self.x_vel * self.TIMESTEP
        self.y     += self.y_vel * self.TIMESTEP

        self.orbit.append((self.x, self.y))
        if len(self.orbit) > ORBIT_TAIL * 2:
            self.orbit = self.orbit[-ORBIT_TAIL:]

        self.days_elapsed += 1

    # ── derived info ──────────────────────────────────────────────────────────
    def distance_from_sun_au(self):
        return math.hypot(self.x, self.y) / self.AU

    def speed_km_s(self):
        return math.hypot(self.x_vel, self.y_vel) / 1000.0

# ─── UI controls ─────────────────────────────────────────────────────────────
class Slider:
    """Horizontal slider that returns a float in [min_val, max_val]."""

    def __init__(self, x, y, w, h, min_val, max_val, initial, label=""):
        self.rect    = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value   = initial
        self.label   = label
        self.dragging = False

    @property
    def handle_x(self):
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.x + t * self.rect.w)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            hx = self.handle_x
            hy = self.rect.centery
            if math.hypot(event.pos[0] - hx, event.pos[1] - hy) <= 10:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel = (event.pos[0] - self.rect.x) / self.rect.w
            rel = max(0.0, min(1.0, rel))
            self.value = self.min_val + rel * (self.max_val - self.min_val)

    def draw(self, surface, fonts):
        # track
        track_y = self.rect.centery
        pygame.draw.line(surface, DIVIDER_CLR,
                         (self.rect.x, track_y), (self.rect.right, track_y), 3)
        # filled portion
        pygame.draw.line(surface, ACCENT_CLR,
                         (self.rect.x, track_y), (self.handle_x, track_y), 3)
        # handle
        pygame.draw.circle(surface, ACCENT_CLR, (self.handle_x, track_y), 8)
        pygame.draw.circle(surface, TEXT_CLR,   (self.handle_x, track_y), 5)
        # value label
        val_txt = fonts["small"].render(f"{self.value:.1f}×", True, TEXT_CLR)
        surface.blit(val_txt, (self.rect.right + 8, track_y - val_txt.get_height() // 2))


class PauseButton:
    def __init__(self, x, y, w, h):
        self.rect   = pygame.Rect(x, y, w, h)
        self.paused = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.paused = not self.paused
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.paused = not self.paused

    def draw(self, surface, fonts):
        col_bg  = (50, 60, 90) if self.paused else (35, 42, 62)
        col_bdr = ACCENT_CLR  if self.paused else DIVIDER_CLR
        pygame.draw.rect(surface, col_bg,  self.rect, border_radius=7)
        pygame.draw.rect(surface, col_bdr, self.rect, width=1, border_radius=7)

        label = "▶  Resume" if self.paused else "⏸  Pause"
        txt   = fonts["body"].render(label, True, TEXT_CLR)
        surface.blit(txt, (
            self.rect.centerx - txt.get_width()  // 2,
            self.rect.centery - txt.get_height() // 2,
        ))


# ─── Panel drawing ───────────────────────────────────────────────────────────
def draw_panel(window, fonts, planets, buttons, selected_planet, sim_days,
               slider, pause_btn):
    # background
    panel_surf = pygame.Surface((PANEL_W, HEIGHT))
    panel_surf.fill(PANEL_COLOR)
    window.blit(panel_surf, (PANEL_X, 0))

    # divider
    pygame.draw.line(window, DIVIDER_CLR, (PANEL_X, 0), (PANEL_X, HEIGHT), 2)

    cx = PANEL_X + PANEL_W // 2
    y  = 18

    # title
    title = fonts["title"].render("Solar System", True, TEXT_CLR)
    window.blit(title, (cx - title.get_width() // 2, y))
    y += title.get_height() + 2

    sub = fonts["small"].render("Simulator", True, DIM_CLR)
    window.blit(sub, (cx - sub.get_width() // 2, y))
    y += sub.get_height() + 10

    # sim time
    years  = sim_days / 365.25
    t_text = fonts["small"].render(
        f"Sim time: {years:.2f} yr  ({sim_days} d)", True, DIM_CLR)
    window.blit(t_text, (cx - t_text.get_width() // 2, y))
    y += t_text.get_height() + 14

    pygame.draw.line(window, DIVIDER_CLR,
                     (PANEL_X + 12, y), (PANEL_X + PANEL_W - 12, y))
    y += 14

    # ── playback controls ─────────────────────────────────────────────────────
    ctrl_hdr = fonts["small"].render("PLAYBACK", True, DIM_CLR)
    window.blit(ctrl_hdr, (PANEL_X + 20, y))
    y += ctrl_hdr.get_height() + 8

    # pause button — reposition its rect to current y
    pause_btn.rect.x = PANEL_X + 10
    pause_btn.rect.y = y
    pause_btn.rect.w = PANEL_W - 20
    pause_btn.rect.h = 32
    pause_btn.draw(window, fonts)
    y += pause_btn.rect.h + 12

    # speed slider label
    spd_lbl = fonts["small"].render("Sim Speed", True, DIM_CLR)
    window.blit(spd_lbl, (PANEL_X + 16, y))
    y += spd_lbl.get_height() + 6

    # reposition slider to current y
    slider.rect.x = PANEL_X + 16
    slider.rect.y = y
    slider.rect.w = PANEL_W - 70   # leave room for the "×" label
    slider.rect.h = 20
    slider.draw(window, fonts)
    y += slider.rect.h + 16

    pygame.draw.line(window, DIVIDER_CLR,
                     (PANEL_X + 12, y), (PANEL_X + PANEL_W - 12, y))
    y += 10

    # planet buttons
    header = fonts["small"].render("SELECT A BODY", True, DIM_CLR)
    window.blit(header, (PANEL_X + 20, y))
    y += header.get_height() + 6

    for btn in buttons:
        planet = btn["planet"]
        rect   = btn["rect"]
        rect.y = y

        is_sel = planet is selected_planet
        if is_sel:
            pygame.draw.rect(window, (40, 50, 75), rect, border_radius=6)
            pygame.draw.rect(window, ACCENT_CLR, rect, width=1, border_radius=6)
        else:
            pygame.draw.rect(window, (35, 38, 52), rect, border_radius=6)

        # dot
        dot_col = planet.color
        pygame.draw.circle(window, dot_col,
                           (rect.x + 14, rect.y + rect.height // 2), 5)

        label = fonts["body"].render(planet.name, True,
                                     TEXT_CLR if is_sel else DIM_CLR)
        window.blit(label, (rect.x + 26, rect.y + (rect.height - label.get_height()) // 2))

        y += rect.height + 5

    y += 8
    pygame.draw.line(window, DIVIDER_CLR,
                     (PANEL_X + 12, y), (PANEL_X + PANEL_W - 12, y))
    y += 14

    # ── info panel for selected planet ────────────────────────────────────────
    if selected_planet:
        sp = selected_planet

        name_lbl = fonts["planet_name"].render(sp.name, True, TEXT_CLR)
        window.blit(name_lbl, (cx - name_lbl.get_width() // 2, y))
        y += name_lbl.get_height() + 6

        if sp.description:
            # word-wrap description
            words  = sp.description.split()
            line   = ""
            max_w  = PANEL_W - 32
            for word in words:
                test = line + (" " if line else "") + word
                if fonts["small"].size(test)[0] <= max_w:
                    line = test
                else:
                    rendered = fonts["small"].render(line, True, DIM_CLR)
                    window.blit(rendered, (PANEL_X + 16, y))
                    y   += rendered.get_height() + 2
                    line = word
            if line:
                rendered = fonts["small"].render(line, True, DIM_CLR)
                window.blit(rendered, (PANEL_X + 16, y))
                y += rendered.get_height() + 8

        def stat_row(label, value):
            nonlocal y
            lbl_s = fonts["small"].render(label, True, DIM_CLR)
            val_s = fonts["small"].render(value, True, TEXT_CLR)
            window.blit(lbl_s, (PANEL_X + 16, y))
            window.blit(val_s, (PANEL_X + PANEL_W - val_s.get_width() - 16, y))
            y += lbl_s.get_height() + 5

        stat_row("Mass",
                 f"{sp.mass:.3e} kg")
        stat_row("Distance from Sun",
                 f"{sp.distance_from_sun_au():.3f} AU")
        stat_row("Orbital speed",
                 f"{sp.speed_km_s():.2f} km/s")
        if sp.orbital_period_days:
            stat_row("Orbital period",
                     f"{sp.orbital_period_days:.1f} d")
        stat_row("Sim days elapsed",
                 f"{sp.days_elapsed}")

    else:
        hint = fonts["small"].render("Click a body to see details", True, DIM_CLR)
        window.blit(hint, (cx - hint.get_width() // 2, y))

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    clock  = pygame.time.Clock()
    run    = True

    offset_x       = SIM_WIDTH // 2
    offset_y       = HEIGHT    // 2
    selected_planet = None
    sim_days        = 0
    time_elapsed    = 0.0      # seconds, for star twinkle

    # ── font set ──────────────────────────────────────────────────────────────
    fonts = {
        "title":       pygame.font.SysFont("Georgia", 26, bold=True),
        "planet_name": pygame.font.SysFont("Georgia", 22, bold=True),
        "body":        pygame.font.SysFont("Georgia", 18),
        "small":       pygame.font.SysFont("Georgia", 15),
        "label":       pygame.font.SysFont("Arial",   16),
    }

    # ── planet definitions ────────────────────────────────────────────────────
    AU = Body.AU

    sun = Body("Sun", 0, 0, 20, (255, 220, 80), 1.98892e30,
               description="The star at the centre of our solar system. "
                           "It accounts for 99.86% of the total mass.")
    sun.sun = True

    mercury = Body("Mercury", -0.387 * AU, 0, 6, (169, 169, 169), 3.30e23,
                   orbital_period_days=87.97,
                   description="Smallest planet; closest to the Sun. "
                               "Surface temperature swings from -180 °C to 430 °C.")
    mercury.y_vel = 47.4e3

    venus = Body("Venus", -0.723 * AU, 0, 13, (218, 165, 32), 4.867e24,
                 orbital_period_days=224.7,
                 description="Hottest planet due to a runaway greenhouse effect. "
                             "Rotates retrograde — the Sun rises in the west.")
    venus.y_vel = 35.02e3

    earth = Body("Earth", -1.0 * AU, 0, 12, (100, 216, 255), 5.9742e24,
                 orbital_period_days=365.25,
                 description="Our home. Only known planet to harbour life. "
                             "Liquid water covers ~71% of its surface.")
    earth.y_vel = 29.783e3

    mars = Body("Mars", -1.524 * AU, 0, 9, (188, 80, 60), 6.39e23,
                orbital_period_days=686.97,
                description="The Red Planet. Home to Olympus Mons, "
                            "the tallest volcano in the solar system.")
    mars.y_vel = 24.077e3

    jupiter = Body("Jupiter", -5.203 * AU, 0, 45, (200, 160, 110), 1.898e27,
                   orbital_period_days=4332.59,
                   description="Largest planet; a gas giant. Its Great Red Spot "
                               "is a storm larger than Earth, ongoing for centuries.")
    jupiter.y_vel = 13.07e3

    saturn = Body("Saturn", -9.537 * AU, 0, 40, (210, 185, 130), 5.683e26,
                  orbital_period_days=10759.22,
                  description="Famous for its stunning ring system, made mostly "
                              "of ice and rocky debris. Less dense than water.")
    saturn.y_vel = 9.68e3

    uranus = Body("Uranus", -19.191 * AU, 0, 30, (173, 216, 230), 8.681e25,
                  orbital_period_days=30688.5,
                  description="An ice giant that rotates on its side — "
                              "its axial tilt is 97.77°.")
    uranus.y_vel = 6.80e3

    neptune = Body("Neptune", -30.07 * AU, 0, 28, (72, 100, 200), 1.024e26,
                   orbital_period_days=60182.0,
                   description="Windiest planet — gusts reach 2 100 km/h. "
                               "Has not yet completed one orbit since its 1846 discovery.")
    neptune.y_vel = 5.43e3

    pluto = Body("Pluto", -39.48 * AU, 0, 4, (200, 190, 180), 1.309e22,
                 orbital_period_days=90560.0,
                 description="Dwarf planet in the Kuiper Belt. "
                             "Its moon Charon is half its own size.")
    pluto.y_vel = 4.74e3

    bodies = [sun, mercury, venus, earth, mars,
              jupiter, saturn, uranus, neptune, pluto]

    # ── sidebar buttons (y updated each frame in draw_panel) ─────────────────
    btn_h = 30
    buttons = [
        {"planet": p, "rect": pygame.Rect(PANEL_X + 10, 0, PANEL_W - 20, btn_h)}
        for p in bodies
    ]

    # ── playback controls (positions are overwritten each frame in draw_panel) ─
    speed_slider = Slider(PANEL_X + 16, 0, PANEL_W - 70, 20,
                          min_val=0.01, max_val=10.0, initial=1.0,
                          label="Sim Speed")
    pause_btn    = PauseButton(PANEL_X + 10, 0, PANEL_W - 20, 32)

    # ── main loop ─────────────────────────────────────────────────────────────
    while run:
        dt = clock.tick(FPS) / 1000.0        # seconds since last frame
        dt = min(dt, 0.05)                   # clamp to avoid spiral on lag
        time_elapsed += dt

        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

            elif event.type == pygame.MOUSEWHEEL:
                # only zoom when mouse is over the simulation area
                if pygame.mouse.get_pos()[0] < SIM_WIDTH:
                    factor = 1.15 if event.y > 0 else 1 / 1.15
                    Body.SCALE = max(Body.MIN_SCALE,
                                     min(Body.MAX_SCALE, Body.SCALE * factor))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # planet buttons are only in the panel
                if mx >= PANEL_X:
                    for btn in buttons:
                        if btn["rect"].collidepoint(mx, my):
                            if selected_planet is btn["planet"]:
                                selected_planet = None
                            else:
                                selected_planet = btn["planet"]
                            break

            # delegate to controls
            speed_slider.handle_event(event)
            pause_btn.handle_event(event)

        # held keys for continuous zoom
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            Body.SCALE = min(Body.MAX_SCALE, Body.SCALE * 1.02)
        if keys[pygame.K_DOWN]:
            Body.SCALE = max(Body.MIN_SCALE, Body.SCALE / 1.02)

        # smooth camera follow
        if selected_planet:
            target_x = SIM_WIDTH // 2 - selected_planet.x * Body.SCALE
            target_y = HEIGHT    // 2 - selected_planet.y * Body.SCALE
            smooth   = min(1.0, 8.0 * dt)          # frame-rate independent
            offset_x += (target_x - offset_x) * smooth
            offset_y += (target_y - offset_y) * smooth

        # ── render ────────────────────────────────────────────────────────────
        WIN.fill((5, 6, 14))

        # star field
        draw_stars(WIN, time_elapsed)

        # physics — skip when paused; run multiple steps for higher speeds
        if not pause_btn.paused:
            steps = max(1, round(speed_slider.value))
            for _ in range(steps):
                for body in bodies:
                    body.update_position(bodies)
                sim_days += 1

        # draw bodies
        for body in bodies:
            body.draw(WIN, offset_x, offset_y, body is selected_planet)

        # floating name label above selected planet
        if selected_planet:
            sx, sy = selected_planet.screen_pos(offset_x, offset_y)
            lbl    = fonts["label"].render(selected_planet.name, True, (255, 255, 255))
            lx     = sx - lbl.get_width()  // 2
            ly     = sy - 28
            pad    = 4
            bg     = pygame.Rect(lx - pad, ly - pad,
                                 lbl.get_width()  + pad * 2,
                                 lbl.get_height() + pad * 2)
            pygame.draw.rect(WIN, (15, 18, 30), bg, border_radius=5)
            WIN.blit(lbl, (lx, ly))

        # paused overlay banner
        if pause_btn.paused:
            pause_surf = pygame.Surface((SIM_WIDTH, 32), pygame.SRCALPHA)
            pause_surf.fill((10, 12, 24, 180))
            WIN.blit(pause_surf, (0, 0))
            p_txt = fonts["body"].render("⏸  PAUSED  —  press Space or Resume to continue",
                                         True, ACCENT_CLR)
            WIN.blit(p_txt, (SIM_WIDTH // 2 - p_txt.get_width() // 2, 7))

        # side panel (drawn on top)
        draw_panel(WIN, fonts, bodies, buttons, selected_planet, sim_days,
                   speed_slider, pause_btn)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()