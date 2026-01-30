import pygame
import os
from .entities import Wall, Player, Character


class Enemy(Character):
    """Base enemy class."""
    def __init__(self, x, y, sprite_img, color, lives=1):
        super().__init__(x, y, sprite_img, lives)
        self.color = color
        self.speed = 2
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self):
        self.pos += self.velocity
        self.rect.topleft = self.pos


class Mask(pygame.sprite.Sprite):
    """Mask object that player can pick up."""
    def __init__(self, x, y, sprite_img, color):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.color = color


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


class Key(pygame.sprite.Sprite):
    """Key that opens a door."""
    def __init__(self, x, y, sprite_img, key_id):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.key_id = key_id


class PressPlate(pygame.sprite.Sprite):
    """Pressure plate that triggers doors."""
    def __init__(self, x, y, sprite_img, plate_id):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.plate_id = plate_id
        self.is_pressed = False


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


class Decoration(pygame.sprite.Sprite):
    """Non-collidable decoration sprite."""
    def __init__(self, x, y, sprite_img):
        super().__init__()
        self.image = sprite_img
        self.rect = self.image.get_rect(topleft=(x, y))


def load_placeholder_image(width, height, color):
    """Create a placeholder surface with a specific color."""
    surf = pygame.Surface((width, height))
    surf.fill(color)
    try:
        surf = surf.convert_alpha()
    except pygame.error:
        # Fallback if no display mode set
        pass
    return surf


def load_texture(filename, width, height, fallback_color):
    """Load a texture from assets/images/ or create a placeholder."""
    asset_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', filename)
    
    try:
        if os.path.exists(asset_path):
            img = pygame.image.load(asset_path)
            # Scale to tile size if needed
            if img.get_size() != (width, height):
                img = pygame.transform.scale(img, (width, height))
            return img
    except pygame.error as e:
        print(f"Warning: Could not load {filename}: {e}")
    
    # Fallback to colored placeholder
    return load_placeholder_image(width, height, fallback_color)


def create_asset_dict(tile_size):
    """Create a dictionary of images for all assets."""
    colors = {
        'red': (200, 50, 50),
        'neutral': (100, 100, 100),
        'blue': (50, 50, 200),
        'green': (50, 200, 50),
        'yellow': (200, 200, 50),
        'purple': (200, 50, 200),
        'cyan': (50, 200, 200),
        'white': (200, 200, 200),
        'black': (30, 30, 30),
    }
    
    assets = {}
    # Walls - use your textures
    assets['wr'] = load_texture('red_wall.bmp', tile_size, tile_size, colors['red'])
    assets['w'] = load_texture('white_wall.bmp', tile_size, tile_size, colors['white'])
    
    # Player (smaller - 24x24)
    player_size = 24
    assets['p'] = load_texture('player.bmp', player_size, player_size, colors['blue'])
    
    # Enemies
    assets['er'] = load_texture('red_enemy.bmp', tile_size, tile_size, colors['red'])
    assets['ee'] = load_texture('yellow_enemy.bmp', tile_size, tile_size, colors['yellow'])
    
    # Masks - use your mask textures
    assets['mr'] = load_texture('red_bear_mask_32.bmp', tile_size, tile_size, (50, 200, 200))
    
    # Boxes
    assets['br'] = load_texture('red_box.bmp', tile_size, tile_size, (180, 50, 50))
    
    # Doors and keys
    assets['dk1'] = load_texture('door_1.bmp', tile_size, tile_size, colors['purple'])
    assets['k1'] = load_texture('key_1.bmp', tile_size, tile_size, colors['yellow'])
    assets['dp1'] = load_texture('pressure_door.bmp', tile_size, tile_size, colors['green'])
    assets['pr'] = load_texture('pressure_plate.bmp', tile_size, tile_size, colors['white'])
    
    # Traps
    for trap_type in ['tau', 'tad', 'tar', 'tal', 'tgu', 'tgd', 'tgr', 'tgl']:
        assets[trap_type] = load_texture(f'{trap_type}.bmp', tile_size, tile_size, colors['purple'])
    
    # Decoration
    assets['dec'] = load_texture('decoration.bmp', tile_size, tile_size, (150, 150, 150))
    
    return assets


def load_level(csv_path, tile_size=32):
    """
    Load a level from a CSV file and create sprite groups.
    The CSV uses space-separated values with spaces as empty cells.
    
    Returns:
        dict with keys: 'player', 'enemies', 'all_sprites', 'solid_sprites', 
                       'mask_sprites', 'entities' (dict mapping color to sprite lists)
    """
    all_sprites = pygame.sprite.Group()
    solid_sprites = pygame.sprite.Group()
    mask_sprites = pygame.sprite.Group()  # Colored sprites affected by masks
    enemies = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    plates = pygame.sprite.Group()
    boxes = pygame.sprite.Group()
    traps = pygame.sprite.Group()
    decorations = pygame.sprite.Group()
    
    # Create asset placeholders
    assets = create_asset_dict(tile_size)
    
    player = None
    
    try:
        with open(csv_path, 'r') as f:
            for row_idx, line in enumerate(f):
                x_counter = 0
                line = line.strip('\n')  # Remove newline
                tiles = line.split(' ')  # Split by spaces
                
                for cell in tiles:
                    cell = cell.strip()
                    
                    x = x_counter * tile_size
                    y = row_idx * tile_size
                    
                    # Empty space
                    if not cell or cell == 'o':
                        x_counter += 1
                        continue
                    
                    # Player
                    if cell == 'p':
                        player = Player(x + (tile_size - 24) // 2, y + (tile_size - 24) // 2, assets['p'], lives=3)
                        all_sprites.add(player)
                    
                    # Neutral wall
                    elif cell == 'w':
                        wall = Wall(x, y, assets['w'], tile_size)
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                    
                    # Red wall
                    elif cell == 'wr':
                        wall = Wall(x, y, assets['wr'], tile_size, color='red')
                        wall.color = 'red'  # Add color attribute for mask logic
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                        mask_sprites.add(wall)
                    
                    # Red mask
                    elif cell == 'mr':
                        mask_obj = Mask(x, y, assets['mr'], 'red')
                        all_sprites.add(mask_obj)
                    
                    # Red enemy
                    elif cell == 'er':
                        enemy = Enemy(x, y, assets['er'], 'red', lives=1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                        mask_sprites.add(enemy)
                    
                    # Neutral enemy
                    elif cell == 'ee':
                        enemy = Enemy(x, y, assets['ee'], 'neutral', lives=1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                    
                    # Red box
                    elif cell == 'br':
                        box = Box(x, y, assets['br'], 'red')
                        all_sprites.add(box)
                        solid_sprites.add(box)
                        boxes.add(box)
                        mask_sprites.add(box)
                    
                    # Door 1
                    elif cell == 'dk1':
                        door = Door(x, y, assets['dk1'], 1)
                        all_sprites.add(door)
                        solid_sprites.add(door)
                        doors.add(door)
                    
                    # Key 1
                    elif cell == 'k1':
                        key = Key(x, y, assets['k1'], 1)
                        all_sprites.add(key)
                        keys.add(key)
                    
                    # Door/Pressure plate 1
                    elif cell == 'dp1':
                        door = Door(x, y, assets['dp1'], 1)
                        all_sprites.add(door)
                        solid_sprites.add(door)
                        doors.add(door)
                    
                    # Pressure plate 1
                    elif cell == 'pr':
                        plate = PressPlate(x, y, assets['pr'], 1)
                        all_sprites.add(plate)
                        plates.add(plate)
                    
                    # Arrow traps
                    elif cell in ['tau', 'tad', 'tar', 'tal']:
                        direction_map = {'tau': 'up', 'tad': 'down', 'tar': 'right', 'tal': 'left'}
                        trap = ArrowTrap(x, y, assets[cell], direction_map[cell])
                        all_sprites.add(trap)
                        traps.add(trap)
                    
                    # Guillotine traps
                    elif cell in ['tgu', 'tgd', 'tgr', 'tgl']:
                        direction_map = {'tgu': 'up', 'tgd': 'down', 'tgr': 'right', 'tgl': 'left'}
                        trap = GuillotineTrap(x, y, assets[cell], direction_map[cell])
                        all_sprites.add(trap)
                        traps.add(trap)
                    
                    # Decoration
                    elif cell == 'dec':
                        deco = Decoration(x, y, assets['dec'])
                        all_sprites.add(deco)
                    
                    x_counter += 1
    
    except FileNotFoundError:
        print(f"Error: Could not find level file at {csv_path}")
    
    return {
        'player': player,
        'enemies': enemies,
        'all_sprites': all_sprites,
        'solid_sprites': solid_sprites,
        'mask_sprites': mask_sprites,
        'doors': doors,
        'keys': keys,
        'plates': plates,
        'boxes': boxes,
        'traps': traps,
        'decorations': decorations,
    }
