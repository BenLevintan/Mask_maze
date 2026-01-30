import pygame

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, color, tile_size):
        super().__init__()
        self.color = color
        self.on_off = True  # Default to solid
        self.image = pygame.Surface((tile_size, tile_size)).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.update_appearance()

    def update_appearance(self):
        """Updates the opacity based on the on_off state."""
        self.image.fill(self.color)
        if not self.on_off:
            self.image.set_alpha(100) # Ghostly/Transparent
        else:
            self.image.set_alpha(255) # Fully Opaque

    def toggle(self, state):
        """Method to change wall state based on player's current mask."""
        self.on_off = state
        self.update_appearance()
        

class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, sprite_img, lives):
        super().__init__()
        self.image = sprite_img # Pass a loaded surface here
        self.rect = self.image.get_rect(topleft=(x, y))
        self.lives = lives
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)

    def take_damage(self):
        self.lives -= 1
        if self.lives <= 0:
            self.kill() # Remove from sprite groups


class Player(Character):
    def __init__(self, x, y, sprite_img, lives=3):
        super().__init__(x, y, sprite_img, lives)
        self.current_mask = None # Holds the color of the current mask
        self.speed = 4

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        self.velocity.y = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed

    def update(self):
        self.handle_input()
        self.pos += self.velocity
        self.rect.topleft = self.pos