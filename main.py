import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.loader import load_level
from src.entities import Player, Wall

TILE_SIZE = 32
WIDTH, HEIGHT = 1600, 960

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Masks - Game Jam")

clock = pygame.time.Clock()
running = True

# Load level
level_path = os.path.join(os.path.dirname(__file__), 'mazes', 'test_lvl.csv')
level_data = load_level(level_path, TILE_SIZE)

player = level_data['player']
all_sprites = level_data['all_sprites']
solid_sprites = level_data['solid_sprites']
mask_sprites = level_data['mask_sprites']

if not player:
    print("Error: No player spawn point found in level!")
    pygame.quit()
    sys.exit()


class Camera:
    """Camera that follows the player."""
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
    
    def apply(self, entity):
        """Apply camera offset to an entity's rect."""
        return entity.rect.move(-self.camera.x, -self.camera.y)
    
    def update(self, target):
        """Update camera to follow target (player)."""
        # Center camera on target
        x = target.rect.centerx - self.width // 2
        y = target.rect.centery - self.height // 2
        
        # Clamp camera to level bounds (prevent black borders)
        x = max(0, x)
        y = max(0, y)
        
        self.camera.x = x
        self.camera.y = y


camera = Camera(WIDTH, HEIGHT)


def update_mask_effects(player, mask_sprites):
    """Update which sprites are solid/ghostly based on player's mask."""
    for sprite in mask_sprites:
        if hasattr(sprite, 'color'):
            if player.current_mask == sprite.color:
                # Make sprite ghostly and non-collidable
                if hasattr(sprite, 'toggle'):
                    sprite.toggle(False)
            else:
                # Make sprite solid and collidable
                if hasattr(sprite, 'toggle'):
                    sprite.toggle(True)


def check_aabb_collision(rect1, rect2):
    """Check if two rects overlap (AABB collision)."""
    return rect1.colliderect(rect2)


def resolve_collision(player, solid_sprites):
    """
    Resolve player collision with solid sprites.
    Player stops when hitting a solid sprite.
    """
    for solid in solid_sprites:
        if hasattr(solid, 'on_off') and not solid.on_off:
            # Skip ghostly sprites
            continue
        
        if check_aabb_collision(player.rect, solid.rect):
            # Reverse velocity to stop collision
            player.pos -= player.velocity
            player.rect.topleft = player.pos
            player.velocity.x = 0
            player.velocity.y = 0


def handle_mask_pickup(player, mask_sprites):
    """Check if player touches a mask and equip it."""
    for mask_obj in mask_sprites:
        if hasattr(mask_obj, 'color') and not hasattr(mask_obj, 'on_off'):
            # This is a mask (has color but no on_off toggle)
            if isinstance(mask_obj, type(player)) or mask_obj.__class__.__name__ == 'Mask':
                if check_aabb_collision(player.rect, mask_obj.rect):
                    player.equip_mask(mask_obj.color)
                    mask_obj.kill()


# Game loop
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Switch masks with number keys
            if event.key == pygame.K_1:
                player.equip_mask('red')
            elif event.key == pygame.K_0:
                player.unequip_mask()
    
    # Update player input and position
    if player:
        player.handle_input()
        
        # Move and check collision
        player.update()
        resolve_collision(player, solid_sprites)
        
        # Update mask effects on sprites
        update_mask_effects(player, mask_sprites)
        
        # Check for mask pickup
        handle_mask_pickup(player, all_sprites)
        
        # Update camera to follow player
        camera.update(player)
    
    # Render
    screen.fill((20, 20, 30))
    
    # Draw sprites with camera offset
    for sprite in all_sprites:
        screen.blit(sprite.image, camera.apply(sprite))
    
    # Draw HUD (fixed to screen, not affected by camera)
    font = pygame.font.Font(None, 24)
    lives_text = font.render(f"Lives: {player.lives}", True, (255, 255, 255))
    mask_text = font.render(f"Mask: {player.current_mask or 'None'}", True, (255, 255, 255))
    help_text = font.render("1=Red Mask, 0=No Mask, Arrow Keys=Move", True, (150, 150, 150))
    
    screen.blit(lives_text, (10, 10))
    screen.blit(mask_text, (10, 40))
    screen.blit(help_text, (10, 70))
    
    pygame.display.flip()

pygame.quit()
sys.exit()
