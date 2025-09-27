import pygame
import numpy as np
import random
import math
import colorsys

# Initialize pygame
pygame.init()

# Get screen info for full screen
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Full-Screen Fireworks Display")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Create a surface for alpha blending
fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)


# Particle class for individual firework elements
class Particle:
    def __init__(self, x, y, color, velocity, decay=0.97, gravity=0.15, trail_length=15):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = np.array(velocity, dtype=float)
        self.decay = decay
        self.gravity = gravity
        self.trail = []
        self.trail_length = trail_length
        self.alive = True
        self.life = 1.0  # Full life
        self.fade_rate = random.uniform(0.002, 0.008)  # Slower fade rate

    def update(self):
        # Apply gravity
        self.velocity[1] += self.gravity

        # Apply decay to velocity
        self.velocity *= self.decay

        # Update position
        self.x += self.velocity[0]
        self.y += self.velocity[1]

        # Add current position to trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Decrease life
        self.life -= self.fade_rate
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        # Draw trail with fading
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * self.life)
            color = (*self.color[:3], alpha)
            radius = max(1, int(3 * (i / len(self.trail))))
            pygame.draw.circle(surface, color, (int(trail_x), int(trail_y)), radius)

        # Draw main particle
        alpha = int(255 * self.life)
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 4)


# Firework class
class Firework:
    def __init__(self, x, y, pattern_type="random"):
        self.x = x
        self.y = y
        self.particles = []
        self.pattern_type = pattern_type
        self.exploded = False
        self.color = self.generate_color()
        self.velocity = [0, -random.uniform(6, 10)]  # Slower ascent
        self.gravity = 0.15
        self.trail = []
        self.trail_color = (255, 255, 200, 255)  # Bright trail for the rocket

    def generate_color(self):
        # Generate a bright, vibrant color
        h = random.random()  # Hue
        s = 0.8 + random.random() * 0.2  # Saturation
        v = 1.0  # Value
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255), 255)

    def update(self):
        if not self.exploded:
            # Update position
            self.velocity[1] += self.gravity
            self.x += self.velocity[0]
            self.y += self.velocity[1]

            # Add to trail
            self.trail.append((self.x, self.y))
            if len(self.trail) > 10:
                self.trail.pop(0)

            # Check if it's time to explode
            if self.velocity[1] >= 0:
                self.explode()
        else:
            # Update all particles
            for particle in self.particles[:]:
                particle.update()
                if not particle.alive:
                    self.particles.remove(particle)

    def explode(self):
        self.exploded = True
        num_particles = random.randint(80, 250)  # More particles for fuller effect

        if self.pattern_type == "random":
            self.create_random_pattern(num_particles)
        elif self.pattern_type == "circle":
            self.create_circle_pattern(num_particles)
        elif self.pattern_type == "spiral":
            self.create_spiral_pattern(num_particles)
        elif self.pattern_type == "heart":
            self.create_heart_pattern(num_particles)
        elif self.pattern_type == "star":
            self.create_star_pattern(num_particles)
        elif self.pattern_type == "willow":
            self.create_willow_pattern(num_particles)
        else:
            self.create_random_pattern(num_particles)

    def create_random_pattern(self, num_particles):
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 5)  # Slower speed
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            decay = random.uniform(0.97, 0.99)  # Slower decay
            trail_length = random.randint(10, 20)
            self.particles.append(Particle(
                self.x, self.y, self.color,
                [vx, vy], decay, 0.12, trail_length  # Reduced gravity
            ))

    def create_circle_pattern(self, num_particles):
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2
            speed = random.uniform(2, 4)  # Slower speed
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # Vary color slightly for each particle
            color_var = random.randint(-20, 20)
            color = (
                max(0, min(255, self.color[0] + color_var)),
                max(0, min(255, self.color[1] + color_var)),
                max(0, min(255, self.color[2] + color_var)),
                255
            )
            self.particles.append(Particle(
                self.x, self.y, color, [vx, vy], 0.985, 0.08, 15  # Reduced gravity
            ))

    def create_spiral_pattern(self, num_particles):
        arms = random.randint(3, 6)
        for i in range(num_particles):
            arm = i % arms
            angle = (i / num_particles) * math.pi * 2 + (arm * math.pi * 2 / arms)
            speed = 3 + (i / num_particles) * 1.5  # Slower speed
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(
                self.x, self.y, self.color, [vx, vy], 0.99, 0.06, 20  # Reduced gravity
            ))

    def create_heart_pattern(self, num_particles):
        for i in range(num_particles):
            t = (i / num_particles) * math.pi * 2
            # Heart parametric equations
            x = 16 * (math.sin(t) ** 3)
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            # Scale and adjust direction
            scale = 0.2  # Smaller scale for slower spread
            vx = x * scale
            vy = -y * scale  # Negative to make it upright
            self.particles.append(Particle(
                self.x, self.y, self.color, [vx, vy], 0.988, 0.1, 15  # Reduced gravity
            ))

    def create_star_pattern(self, num_particles):
        points = random.randint(5, 8)  # Number of star points
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2
            # Create star shape with alternating inner and outer points
            point = i % (points * 2)
            if point % 2 == 0:
                # Outer point
                radius = 4.0  # Smaller radius for slower spread
            else:
                # Inner point
                radius = 2.0  # Smaller radius for slower spread
            vx = math.cos(angle) * radius
            vy = math.sin(angle) * radius
            self.particles.append(Particle(
                self.x, self.y, self.color, [vx, vy], 0.985, 0.08, 15  # Reduced gravity
            ))

    def create_willow_pattern(self, num_particles):
        for i in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)  # Slower speed for willow effect
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Create a secondary explosion effect after a delay
            if random.random() < 0.3:
                # These particles will fall slower and have longer trails
                self.particles.append(Particle(
                    self.x, self.y, self.color,
                    [vx, vy], 0.99, 0.25, 25  # Higher gravity for falling effect
                ))
            else:
                self.particles.append(Particle(
                    self.x, self.y, self.color,
                    [vx, vy], 0.98, 0.1, 20  # Reduced gravity
                ))

    def draw(self, surface):
        if not self.exploded:
            # Draw trail
            for i, (trail_x, trail_y) in enumerate(self.trail):
                alpha = int(200 * (i / len(self.trail)))
                color = (*self.trail_color[:3], alpha)
                radius = max(1, int(3 * (i / len(self.trail))))
                pygame.draw.circle(surface, color, (int(trail_x), int(trail_y)), radius)

            # Draw main rocket
            pygame.draw.circle(surface, self.trail_color, (int(self.x), int(self.y)), 4)
        else:
            # Draw all particles
            for particle in self.particles:
                particle.draw(surface)

    def is_done(self):
        return self.exploded and len(self.particles) == 0


# Main function
def main():
    fireworks = []
    running = True

    # Pattern types to cycle through
    pattern_types = ["random", "circle", "spiral", "heart", "star", "willow"]
    pattern_index = 0

    # Font for instructions
    font = pygame.font.SysFont('Arial', 20)

    # Main loop
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Create firework at random position
                    x = random.randint(100, WIDTH - 100)
                    pattern = pattern_types[pattern_index]
                    fireworks.append(Firework(x, HEIGHT, pattern))
                    pattern_index = (pattern_index + 1) % len(pattern_types)

        # Randomly add fireworks (less frequently for slower pace)
        if random.random() < 0.02:
            x = random.randint(100, WIDTH - 100)
            pattern = pattern_types[pattern_index]
            fireworks.append(Firework(x, HEIGHT, pattern))
            pattern_index = (pattern_index + 1) % len(pattern_types)

        # Apply fade effect (lighter for longer trails)
        fade_surface.fill((0, 0, 0, 15))
        screen.blit(fade_surface, (0, 0))

        # Update and draw fireworks
        for firework in fireworks[:]:
            firework.update()
            firework.draw(screen)
            if firework.is_done():
                fireworks.remove(firework)

        # Display instructions
        instructions = font.render("Press SPACE to launch fireworks | ESC to exit", True, (200, 200, 200))
        screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 40))

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()