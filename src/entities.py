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
    def __init__(self, x, y, sprite_img, color, lives=3,sprite_variants=None):
        super().__init__(x, y, sprite_img, lives)
        self.current_mask = None  # Holds the color of the current mask
        self.speed = 4
        self.facing_right = True  # Track sprite direction
        self.base_image = sprite_img.copy()  # Store original sprite
        self.sprite_variants = sprite_variants or {}  # Dict of mask color -> sprite image
        self.chase_distance=250
    def set_speed(self,player):
        #self.velocity=(((self.pos[0] - player.pos[0])**2+(self.pos[1] - player.pos[1])**2)*0.5)*(self.pos[0] - player.pos[0]) ,(((self.pos[0] - player.pos[0])**2+(self.pos[1] - player.pos[1])**2)*0.5)*(self.pos[1] - player.pos[1])
        if ((player.pos[0]-self.pos[0])**2 + (player.pos[1]-self.pos[1])**2)**0.5<self.chase_distance:
            speed_factor=5
        else:
            speed_factor=1


        if player.pos[0]-self.pos[0]<0:
            self.velocity[0]=-speed_factor
        if player.pos[0] - self.pos[0] > 0:
            self.velocity[0] = speed_factor
        if player.pos[1]-self.pos[1]<0:
            self.velocity[1]=-speed_factor
        if player.pos[1] - self.pos[1] > 0:
            self.velocity[1] = speed_factor
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

    def update(self,player):
        """Update player position."""


        self.pos += self.velocity
        self.rect.topleft = self.pos
        self.set_speed(player)

    def equip_mask(self, color):
        """Equip a mask and change sprite."""
        self.current_mask = color
        self._update_sprite_display()

    def unequip_mask(self):
        """Remove the current mask and change sprite."""
        self.current_mask = None
        self._update_sprite_display()


class Mask(pygame.sprite.Sprite):
    """Mask object that player can pick up - has subtle bobbing animation."""

    def __init__(self, x, y, sprite_img, color):
        super().__init__()
        self.image = sprite_img
        self.base_y = y  # Store the base Y position
        self.rect = self.image.get_rect(topleft=(x, y))
        self.color = color
        self.time = 0  # For animation timing

    def update(self, time_delta=0.016):
        """Update animation - subtle bobbing motion."""
        import math
        self.time += time_delta
        # Sine wave animation - amplitude of 8 pixels, same speed as keys
        bob_amount = math.sin(self.time * 3) * 8
        self.rect.y = self.base_y + bob_amount


class Box(pygame.sprite.Sprite):
    """Pushable box with color coding."""

    def __init__(self, x, y, sprite_img, color):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.color = color
        self.pos = pygame.math.Vector2(x, y)
        self.on_off = True  # Collision state toggle


class Door(pygame.sprite.Sprite):
    """Door that requires a key."""

    def __init__(self, x, y, sprite_img, door_id):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.door_id = door_id
        self.is_open = False
        self.base_image = sprite_img.copy()

    def open_door(self):
        """Open the door - make it non-collidable."""
        self.is_open = True
        # Make door semi-transparent
        transparent_image = self.base_image.copy()
        transparent_image.set_alpha(100)
        self.image = transparent_image

    def close_door(self):
        """Close the door - make it solid again."""
        self.is_open = False
        self.image = self.base_image.copy()
        self.image.set_alpha(255)


class Key(pygame.sprite.Sprite):
    """Key that opens a door - has subtle bobbing animation."""

    def __init__(self, x, y, sprite_img, key_id):
        super().__init__()
        self.image = sprite_img
        self.base_y = y  # Store the base Y position
        self.rect = self.image.get_rect(topleft=(x, y))
        self.key_id = key_id
        self.time = 0  # For animation timing
        self.x = x  # Store x position

    def update(self, time_delta=0.016):
        """Update animation - slight bobbing motion."""
        import math
        self.time += time_delta
        # Sine wave animation - amplitude of 8 pixels, slower movement
        bob_amount = math.sin(self.time * 3) * 8
        self.rect.y = self.base_y + bob_amount


class PressPlate(pygame.sprite.Sprite):
    """Pressure plate that triggers doors."""
    is_pressed = False
    debouncing = False
    door_list = []
    def __init__(self, x, y, sprite_img, plate_id,debounce=False):
        super().__init__()
        self.pos=[x,y]
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.plate_id = plate_id
        self.is_pressed = False
        self.debouncing = debounce
        self.counter=0
    def press(self):
        self.is_pressed=True
    def depress(self):
        self.is_pressed=False
    def change_doors(self):
        for door in self.door_list:
            if door.is_open:
                door.close_door()
            else:
                door.open_door()
    def set_door_list(self,doors):
        self.door_list=doors
    
    def update(self, boxes, player, time_delta=0.016):
        """Check if box or player is on the plate using collision detection."""
        currently_pressed = False
        
        # Check if any box is colliding with the plate
        for box in boxes:
            if self.rect.colliderect(box.rect):
                currently_pressed = True
                break
        
        # Check if player is colliding with the plate
        if not currently_pressed and self.rect.colliderect(player.rect):
            currently_pressed = True
        
        # Update pressed state
        if currently_pressed and not self.is_pressed:
            self.press()
        elif not currently_pressed and self.is_pressed:
            self.depress()







class ArrowTrap(pygame.sprite.Sprite):
    """Arrow trap that shoots in a direction."""

    def __init__(self, x, y, sprite_img, direction):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = direction  # 'up', 'down', 'left', 'right'


class GuillotineTrap(pygame.sprite.Sprite):
    """Guillotine trap that falls in a direction."""

    def __init__(self, x, y, sprite_img, direction):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = direction  # 'up', 'down', 'left', 'right'


class Spike(pygame.sprite.Sprite):
    """Spike trap that alternates between open and closed."""

    def __init__(self, x, y, closed_img, open_img):
        super().__init__()
        self.closed_image = closed_img
        self.open_image = open_img
        self.image = self.closed_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_open = False
        self.time = 0
        self.toggle_interval = 2.0  # Toggle every 2 seconds

    def update(self, time_delta=0.016):
        """Update spike state - alternate between open and closed."""
        self.time += time_delta

        # Toggle state every 2 seconds
        state = int(self.time / self.toggle_interval) % 2
        self.is_open = (state == 1)

        # Update image based on state
        if self.is_open:
            self.image = self.open_image.copy()
        else:
            self.image = self.closed_image.copy()


class Decoration(pygame.sprite.Sprite):
    """Non-collidable decoration sprite."""

    def __init__(self, x, y, sprite_img):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))


class Endpoint(pygame.sprite.Sprite):
    """Level endpoint - player reaches here to complete level."""

    def __init__(self, x, y, sprite_img):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))

