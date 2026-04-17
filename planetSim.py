import pygame
import math
pygame.init()

WIDTH, HEIGHT = 800, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Planet Simulation")

class Body:
    AU = 149.6e6 * 1000 # all units are in KM for uniformity, will add imperial units later
    GRAVITY = 6.67428e-11
    SCALE = 250 / AU # scaled down so 1 AU = ~100px
    TIMESTEP = 3600 * 24 # represents 1 day


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

    def draw(self, window):
        x = self.x * self.SCALE + (WIDTH / 2)
        y = self.y * self.SCALE + (HEIGHT / 2)
        show_orbits = True

        if show_orbits:
            if len(self.orbit) > 2:
                updated_points = []
                for point in self.orbit:
                    x, y = point
                    x = x * self.SCALE + (WIDTH / 2)
                    y = y * self.SCALE + (HEIGHT / 2)
                    updated_points.append((x, y))

                pygame.draw.lines(window, self.color, False, updated_points, 2)

        pygame.draw.circle(window, self.color, (x,y), self.radius)

    def attraction(self, other):
        other_x, other_y = other.x, other.y
        distance_x = other_x - self.x
        distance_y = other_y - self.y
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        if other.sun:
            self.distance_to_sun = distance

        force = (self.GRAVITY* self.mass * other.mass / distance ** 2)
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

    sun = Body(0, 0, 30, (255, 255, 0), 1.98892 * 10**30)
    sun.sun = True
    earth = Body((-1 * Body.AU), 0, 16, (100, 216, 255), 5.9742 * 10**24)
    earth.y_vel = 29.783 * 1000
    mars = Body((-1.524*Body.AU), 0, 12, (188, 39, 50), 6.39 * 10**23)
    mars.y_vel = 24.077 * 1000


    planets = [sun, earth, mars]


    while run:
        clock.tick(60)
        WIN.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        for planet in planets:
            planet.update_position(planets)
            planet.draw(WIN)

        pygame.display.update()

    pygame.quit()

main()


