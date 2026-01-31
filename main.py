import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.loader import load_level
from src.entities import Player, Wall

TILE_SIZE = 32
WIDTH, HEIGHT = 1600, 960

# Level list - order matters
LEVELS = [
    'test_lvl.csv',
    #'maze_level_1.csv',
    'maze_level_3.csv',
    #'maze_level_5.csv',
]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Masks - Game Jam")

clock = pygame.time.Clock()
running = True
current_level_index = 0


def load_level_by_index(index):
    """Load a level by its index in the LEVELS list."""
    if index >= len(LEVELS):
        return None
    level_path = os.path.join(os.path.dirname(__file__), 'mazes', LEVELS[index])
    return load_level(level_path, TILE_SIZE)


# Load initial level
level_data = load_level_by_index(current_level_index)

if not level_data:
    print("Error: Could not load any levels!")
    pygame.quit()
    sys.exit()

player = level_data['player']
all_sprites = level_data['all_sprites']
solid_sprites = level_data['solid_sprites']
mask_sprites = level_data['mask_sprites']
endpoints = level_data['endpoints']
doors = level_data['doors']
keys = level_data['keys']
enemies = level_data['enemies']
traps = level_data['traps']
plate_presses=level_data['presses']
boxes = level_data['boxes']
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
    Handles X and Y collisions separately so player can slide along walls.
    """
    # Move on X axis and check collision
    player.pos.x += player.velocity.x
    player.rect.x = player.pos.x
    
    for solid in solid_sprites:
        if hasattr(solid, 'on_off') and not solid.on_off:
            continue
        if check_aabb_collision(player.rect, solid.rect):
            # Undo X movement
            player.pos.x -= player.velocity.x
            player.rect.x = player.pos.x
            player.velocity.x = 0
            break
    
    # Move on Y axis and check collision
    player.pos.y += player.velocity.y
    player.rect.y = player.pos.y
    
    for solid in solid_sprites:
        if hasattr(solid, 'on_off') and not solid.on_off:
            continue
        if check_aabb_collision(player.rect, solid.rect):
            # Undo Y movement
            player.pos.y -= player.velocity.y
            player.rect.y = player.pos.y
            player.velocity.y = 0
            break


def handle_mask_pickup(player, mask_sprites):
    """Check if player touches a mask and equip it."""
    for mask_obj in mask_sprites:
        if hasattr(mask_obj, 'color') and not hasattr(mask_obj, 'on_off'):
            # This is a mask (has color but no on_off toggle)
            if isinstance(mask_obj, type(player)) or mask_obj.__class__.__name__ == 'Mask':
                if check_aabb_collision(player.rect, mask_obj.rect):
                    player.equip_mask(mask_obj.color)
                    mask_obj.kill()


def handle_key_pickup(player, keys, doors):
    """Check if player collects a key and open corresponding door."""
    for key in keys:
        if check_aabb_collision(player.rect, key.rect):
            # Find and open the corresponding door
            for door in doors:
                if door.door_id == key.key_id:
                    door.open_door()
                    # Remove door from solid_sprites so it's not collidable
                    if door in solid_sprites:
                        solid_sprites.remove(door)
            key.kill()


def check_level_complete(player, endpoints):
    """Check if player reached the level endpoint."""
    for endpoint in endpoints:
        if check_aabb_collision(player.rect, endpoint.rect):
            return True
    return False


def check_spike_collision(player, traps):
    """Check if player hit an open spike. Returns True if hit an open spike."""
    for trap in traps:
        if trap.__class__.__name__ == 'Spike':
            if check_aabb_collision(player.rect, trap.rect):
                if trap.is_open:
                    return True
    return False


def next_level():
    """Load the next level."""

    global current_level_index, player, all_sprites, solid_sprites, mask_sprites, endpoints, camera, doors, keys, enemies, traps

    current_level_index += 1
    level_data = load_level_by_index(current_level_index)
    
    if not level_data:
        # No more levels
        print("You beat all levels! Congratulations!")
        return False
    enemies=level_data['enemies']
    player = level_data['player']
    all_sprites = level_data['all_sprites']
    solid_sprites = level_data['solid_sprites']
    mask_sprites = level_data['mask_sprites']
    endpoints = level_data['endpoints']
    doors = level_data['doors']
    keys = level_data['keys']
    traps = level_data['traps']
    camera = Camera(WIDTH, HEIGHT)
    enemies = level_data['enemies']
    plate_presses=level_data['plate_presses']
    boxes = level_data['boxes']
    print(f"Level {current_level_index + 1} loaded!")

    return True


def reload_level():
    """Reload the current level from scratch."""
    global player, all_sprites, solid_sprites, mask_sprites, endpoints, camera, doors, keys, enemies, traps
    
    level_data = load_level_by_index(current_level_index)
    
    if not level_data:
        print("Error: Could not reload level!")
        return False
    enemies=level_data['enemies']
    player = level_data['player']
    all_sprites = level_data['all_sprites']
    solid_sprites = level_data['solid_sprites']
    mask_sprites = level_data['mask_sprites']
    endpoints = level_data['endpoints']
    doors = level_data['doors']
    keys = level_data['keys']
    traps = level_data['traps']
    plate_presses = level_data['plate_presses']
    boxes = level_data['boxes']
    camera = Camera(WIDTH, HEIGHT)
    
    print(f"Level {current_level_index + 1} reloaded!")
    return True

#[print(d.open_door()) for d in doors]
#[print(d.door_id) for d in doors]
#[print(d.door_id) for d in plate_presses]
enemy_collisions=0
for press in plate_presses:
   press.set_door_list([door for door in doors if door.door_id == press.plate_id])

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
            elif event.key == pygame.K_2:
                player.equip_mask('green')
            elif event.key == pygame.K_3:
                player.equip_mask('blue')
            elif event.key == pygame.K_0:
                player.unequip_mask()
            # Reload level with R key
            elif event.key == pygame.K_r:
                reload_level()
    
    # Update player input and position
    if player:
        player.handle_input()
        
        # Move and check collision (handles both X and Y separately)
        resolve_collision(player, solid_sprites)

        # Update mask effects on sprites
        update_mask_effects(player, mask_sprites)
        
        # Check for mask pickup
        handle_mask_pickup(player, all_sprites)
        
        # Animate masks with bobbing motion
        for mask in mask_sprites:
            if mask.__class__.__name__ == 'Mask':
                mask.update(dt)
        
        # Animate keys with bobbing motion
        for key in keys:
            key.update(dt)

        #check press
        for press in plate_presses:
            press.update(boxes,player,dt)


        # Update enemies
        for enemy in enemies:
            enemy.update(player)
            resolve_collision(enemy, solid_sprites)
            if check_aabb_collision(player.rect,enemy.rect):
                enemy_collisions+=1
                if enemy_collisions>50:
                    enemy_collisions=0
                    reload_level()
        # Animate spikes
        for trap in traps:
            if trap.__class__.__name__ == 'Spike':
                trap.update(dt)
        # Check for key pickup and door opening
        handle_key_pickup(player, keys, doors)
        
        # Check for spike collision
        if check_spike_collision(player, traps):
            reload_level()
        
        # Check for level completion
        if check_level_complete(player, endpoints):
            if not next_level():
                running = False
        
        # Update camera to follow payer
        camera.update(player)
    
    # Render
    screen.fill((20, 20, 30))
    
    # Draw sprites with camera offset - sort by Y position for proper depth
    sorted_sprites = sorted(all_sprites, key=lambda sprite: sprite.rect.y)
    for sprite in sorted_sprites:
        screen.blit(sprite.image, camera.apply(sprite))
    
    # Draw HUD (fixed to screen, not affected by camera)
    font = pygame.font.Font(None, 24)
    lives_text = font.render(f"Lives: {player.lives}", True, (255, 255, 255))
    mask_text = font.render(f"Mask: {player.current_mask or 'None'}", True, (255, 255, 255))
    level_text = font.render(f"Level: {current_level_index + 1}/{len(LEVELS)}", True, (255, 255, 255))
    help_text = font.render("1=Red, 2=Green, 3=Blue, 0=No Mask | R=Reset | Arrow Keys=Move", True, (150, 150, 150))
    
    screen.blit(help_text, (10, HEIGHT - 110))
    screen.blit(level_text, (10, HEIGHT - 80))
    screen.blit(mask_text, (10, HEIGHT - 50))
    screen.blit(lives_text, (10, HEIGHT - 20))
    
    pygame.display.flip()

pygame.quit()
sys.exit()