import pygame

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, image, tile_size, color=(100, 100, 100)):
        super().__init__()
        self.color = color
        self.on_off = True  # Default to solid
        self.image = image.copy() if isinstance(image, pygame.Surface) else pygame.Surface((tile_size, tile_size))
        try:
            self.image = self.image.convert_alpha()
        except pygame.error:
            # Fallback if no display mode set
            pass
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_image = self.image.copy()  # Store original for toggling
        self.update_appearance()

    def update_appearance(self):
        """Updates the opacity based on the on_off state."""
        self.image = self.base_image.copy()
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
    def __init__(self, x, y, sprite_img, lives=3, sprite_variants=None):
        super().__init__(x, y, sprite_img, lives)
        self.current_mask = None # Holds the color of the current mask
        self.speed = 4
        self.facing_right = True  # Track sprite direction
        self.base_image = sprite_img.copy()  # Store original sprite
        self.sprite_variants = sprite_variants or {}  # Dict of mask color -> sprite image

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        self.velocity.y = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        
        # Update sprite direction based on movement
        if self.velocity.x > 0:  # Moving right
            if not self.facing_right:
                self.facing_right = True
                self._update_sprite_display()
        elif self.velocity.x < 0:  # Moving left
            if self.facing_right:
                self.facing_right = False
                self._update_sprite_display()

    def _update_sprite_display(self):
        """Update the displayed sprite based on current mask and facing direction."""
        # Get the current sprite (base or masked variant)
        current_sprite = self.base_image
        if self.current_mask and self.current_mask in self.sprite_variants:
            current_sprite = self.sprite_variants[self.current_mask]
        
        # Apply facing direction
        if not self.facing_right:
            self.image = pygame.transform.flip(current_sprite, True, False)
        else:
            self.image = current_sprite.copy()

    def update(self):
        """Update player position."""
        self.pos += self.velocity
        self.rect.topleft = self.pos
    
    def equip_mask(self, color):
        """Equip a mask and change sprite."""
        self.current_mask = color
        self._update_sprite_display()
    
    def unequip_mask(self):
        """Remove the current mask and change sprite."""
        self.current_mask = None
        self._update_sprite_display()


class Enemy(Character):
    def __init__(self, x, y, sprite_img, lives=3, sprite_variants=None):
        super().__init__(x, y, sprite_img, lives)
        self.current_mask = None  # Holds the color of the current mask
        self.speed = 4
        self.facing_right = True  # Track sprite direction
        self.base_image = sprite_img.copy()  # Store original sprite
        self.sprite_variants = sprite_variants or {}  # Dict of mask color -> sprite image

    def set_speed(self,player):
        self.velocity=(5/((self.pos - player.pos)**2))*(self.pos - player.pos)
        if (self.pos-player.pos)**2 <150:
            self.velocity=self.velocity*5
        # Update sprite direction based on movement
        if self.velocity.x > 0:  # Moving right
            if not self.facing_right:
                self.facing_right = True
                self._update_sprite_display()
        elif self.velocity.x < 0:  # Moving left
            if self.facing_right:
                self.facing_right = False
                self._update_sprite_display()

    def _update_sprite_display(self):
        """Update the displayed sprite based on current mask and facing direction."""
        # Get the current sprite (base or masked variant)
        current_sprite = self.base_image
        if self.current_mask and self.current_mask in self.sprite_variants:
            current_sprite = self.sprite_variants[self.current_mask]

        # Apply facing direction
        if not self.facing_right:
            self.image = pygame.transform.flip(current_sprite, True, False)
        else:
            self.image = current_sprite.copy()

    def update(self):
        """Update player position."""
        self.pos += self.velocity
        self.rect.topleft = self.pos
        self.set_speed()

    def equip_mask(self, color):
        """Equip a mask and change sprite."""
        self.current_mask = color
        self._update_sprite_display()

    def unequip_mask(self):
        """Remove the current mask and change sprite."""
        self.current_mask = None
        self._update_sprite_display()