import pygame
import math

pygame.init()

# Fullscreen setup
WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = WIN.get_size()
pygame.display.set_caption("Solar System Simulation")

class Body:
    AU = 149.6e6 * 1000
    GRAVITY = 6.67428e-11
    SCALE = 15 / AU   # << adjusted so outer planets fit
    TIMESTEP = 3600 * 24


    def __init__(self, x, y, radius, color, mass):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.mass = mass

        self.sun = False
        self.distance_to_sun = 0
        self.orbit = []

        self.x_vel = 0
        self.y_vel = 0

    def draw(self, window, offset_x, offset_y):
        x = self.x * self.SCALE + offset_x
        y = self.y * self.SCALE + offset_y

        # Draw orbit
        if len(self.orbit) > 2:
            updated_points = []
            for point in self.orbit:
                px, py = point
                px = px * self.SCALE + offset_x
                py = py * self.SCALE + offset_y
                updated_points.append((px, py))

            pygame.draw.lines(window, self.color, False, updated_points, 1)

        # Draw planet (scaled radius)
        draw_radius = max(2, int(self.radius))
        pygame.draw.circle(window, self.color, (int(x), int(y)), draw_radius)

    def attraction(self, other):
        distance_x = other.x - self.x
        distance_y = other.y - self.y
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        if other.sun:
            self.distance_to_sun = distance

        force = self.GRAVITY * self.mass * other.mass / distance**2
        theta = math.atan2(distance_y, distance_x)

        force_x = math.cos(theta) * force
        force_y = math.sin(theta) * force

        return force_x, force_y

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
    run = True
    clock = pygame.time.Clock()

    # Split screen (left = simulation, right = UI panel)
    SIM_WIDTH = int(WIDTH * 0.7)
    offset_x = SIM_WIDTH // 2
    offset_y = HEIGHT // 2

    # Bodies
    sun = Body(0, 0, 30, (255, 255, 0), 1.98892 * 10**30)
    sun.sun = True

    mercury = Body((-0.387 * Body.AU), 0, 6, (169, 169, 169), 3.30 * 10**23)
    mercury.y_vel = 47.4 * 1000

    venus = Body((-0.723 * Body.AU), 0, 15, (218, 165, 32), 4.867 * 10**24)
    venus.y_vel = 35.02 * 1000

    earth = Body((-1 * Body.AU), 0, 16, (100, 216, 255), 5.9742 * 10**24)
    earth.y_vel = 29.783 * 1000

    mars = Body((-1.524 * Body.AU), 0, 12, (188, 39, 50), 6.39 * 10**23)
    mars.y_vel = 24.077 * 1000

    jupiter = Body((-5.203 * Body.AU), 0, 50, (222, 184, 135), 1.898 * 10**27)
    jupiter.y_vel = 13.07 * 1000

    saturn = Body((-9.537 * Body.AU), 0, 50, (210, 180, 140), 5.683 * 10**26)
    saturn.y_vel = 9.68 * 1000

    uranus = Body((-19.191 * Body.AU), 0, 40, (173, 216, 230), 8.681 * 10**25)
    uranus.y_vel = 6.80 * 1000

    neptune = Body((-30.07 * Body.AU), 0, 40, (72, 61, 139), 1.024 * 10**26)
    neptune.y_vel = 5.43 * 1000

    pluto = Body((-39.48 * Body.AU), 0, 3, (190, 190, 190), 1.309 * 10**22)
    pluto.y_vel = 4.74 * 1000

    planets = [sun, mercury, venus, earth, mars, jupiter, saturn, uranus, neptune, pluto]

    while run:
        clock.tick(120)
        WIN.fill((0, 0, 0))

        # Right-side UI panel (blank for now)
        pygame.draw.rect(WIN, (20, 20, 20), (SIM_WIDTH, 0, WIDTH - SIM_WIDTH, HEIGHT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

                # Zoom controls
                if event.key == pygame.K_UP:
                    Body.SCALE *= 1.1
                if event.key == pygame.K_DOWN:
                    Body.SCALE /= 1.1

        for planet in planets:
            planet.update_position(planets)
            planet.draw(WIN, offset_x, offset_y)

        pygame.display.update()

    pygame.quit()


main()