import pygame
import math

pygame.init()

# Fullscreen
WIN = pygame.display.set_mode((0, 0), pygame.WINDOWMAXIMIZED)
WIDTH, HEIGHT = WIN.get_size()
pygame.display.set_caption("Solar System Simulation")

class Body:
    AU = 149.6e6 * 1000
    GRAVITY = 6.67428e-11

    SCALE = 80 / AU   # START ZOOMED INTO INNER PLANETS
    MIN_SCALE = 15 / AU
    MAX_SCALE = 200 / AU

    TIMESTEP = 3600 * 24

    def __init__(self, name, x, y, radius, color, mass):
        self.name = name
        self.x = x
        self.y = y
        self.base_radius = radius  # store original size
        self.color = color
        self.mass = mass

        self.sun = False
        self.orbit = []

        self.x_vel = 0
        self.y_vel = 0

    def draw(self, window, offset_x, offset_y):
        x = self.x * self.SCALE + offset_x
        y = self.y * self.SCALE + offset_y

        # Draw orbit (limit points for performance)
        if len(self.orbit) > 2:
            points = self.orbit[-800:]  # prevents lag
            updated = []
            for px, py in points:
                px = px * self.SCALE + offset_x
                py = py * self.SCALE + offset_y
                updated.append((px, py))

            pygame.draw.lines(window, self.color, False, updated, 1)

        # SCALE RADIUS WITH ZOOM
        scale_factor = self.SCALE / (80 / self.AU)
        draw_radius = max(2, int(self.base_radius * scale_factor))

        pygame.draw.circle(window, self.color, (int(x), int(y)), draw_radius)

    def attraction(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        force = self.GRAVITY * self.mass * other.mass / distance**2
        theta = math.atan2(dy, dx)

        return math.cos(theta) * force, math.sin(theta) * force

    def update_position(self, planets):
        total_fx = total_fy = 0

        for planet in planets:
            if self == planet:
                continue
            fx, fy = self.attraction(planet)
            total_fx += fx
            total_fy += fy

        self.x_vel += total_fx / self.mass * self.TIMESTEP
        self.y_vel += total_fy / self.mass * self.TIMESTEP

        self.x += self.x_vel * self.TIMESTEP
        self.y += self.y_vel * self.TIMESTEP

        self.orbit.append((self.x, self.y))


def main():
    clock = pygame.time.Clock()
    run = True

    SIM_WIDTH = int(WIDTH * 0.7)
    offset_x = SIM_WIDTH // 2
    offset_y = HEIGHT // 2

    # Bodies
    sun = Body("Sun", 0, 0, 20, (255, 255, 0), 1.98892 * 10**30)
    sun.sun = True

    mercury = Body("Mercury", (-0.387 * Body.AU), 0, 6, (169, 169, 169), 3.30 * 10**23)
    mercury.y_vel = 47.4 * 1000

    venus = Body("Venus", (-0.723 * Body.AU), 0, 13, (218, 165, 32), 4.867 * 10**24)
    venus.y_vel = 35.02 * 1000

    earth = Body("Earth", (-1 * Body.AU), 0, 12, (100, 216, 255), 5.9742 * 10**24)
    earth.y_vel = 29.783 * 1000

    mars = Body("Mars", (-1.524 * Body.AU), 0, 12, (188, 39, 50), 6.39 * 10**23)
    mars.y_vel = 24.077 * 1000

    jupiter = Body("Jupiter", (-5.203 * Body.AU), 0, 50, (222, 184, 135), 1.898 * 10**27)
    jupiter.y_vel = 13.07 * 1000

    saturn = Body("Saturn", (-9.537 * Body.AU), 0, 50, (210, 180, 140), 5.683 * 10**26)
    saturn.y_vel = 9.68 * 1000

    uranus = Body("Uranus", (-19.191 * Body.AU), 0, 40, (173, 216, 230), 8.681 * 10**25)
    uranus.y_vel = 6.80 * 1000

    neptune = Body("Neptune", (-30.07 * Body.AU), 0, 40, (72, 61, 139), 1.024 * 10**26)
    neptune.y_vel = 5.43 * 1000

    pluto = Body("Pluto", (-39.48 * Body.AU), 0, 3, (190, 190, 190), 1.309 * 10**22)
    pluto.y_vel = 4.74 * 1000

    planets = [sun, mercury, venus, earth, mars, jupiter, saturn, uranus, neptune, pluto]

    while run:
        clock.tick(120)
        WIN.fill((0, 0, 0))
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    Body.SCALE *= 1.15
                elif event.y < 0:
                    Body.SCALE /= 1.15

        if keys[pygame.K_UP]:
            Body.SCALE *= 1.02
        if keys[pygame.K_DOWN]:
            Body.SCALE /= 1.02




        # Clamp zoom
        Body.SCALE = max(Body.MIN_SCALE, min(Body.MAX_SCALE, Body.SCALE))

        for planet in planets:
            planet.update_position(planets)
            planet.draw(WIN, offset_x, offset_y)

        # Create transparent panel
        panel_surface = pygame.Surface((WIDTH - SIM_WIDTH, HEIGHT), pygame.SRCALPHA)
        panel_surface.fill((40, 40, 40, 180))

        # Draw panel
        WIN.blit(panel_surface, (SIM_WIDTH, 0))

        # Text setup
        font = pygame.font.SysFont("Times New Roman", 30)
        text_surface = font.render("Solar System Simulator", True, (255, 255, 255))

        # Center text in panel
        panel_center_x = SIM_WIDTH + (WIDTH - SIM_WIDTH) // 2
        text_x = panel_center_x - text_surface.get_width() // 2
        pygame.draw.line(WIN, (80, 80, 80), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

        # Draw text
        WIN.blit(text_surface, (text_x, 20))

        # List of planet names
        y = 80
        for planet in planets:
            text_surface = font.render(planet.name, True, (255, 255, 255))
            WIN.blit(text_surface, (text_x, y))
            y += 40

        pygame.display.update()

    pygame.quit()


main()