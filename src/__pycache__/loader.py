import pygame
import os

from .entities import Wall, Player,Enemy,Door,Mask,Box,Endpoint,PressPlate

import random



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
            # Convert to alpha and set black as transparent
            img = img.convert_alpha()
            img.set_colorkey((0, 0, 0))  # Make black pixels transparent
            return img
    except pygame.error as e:
        print(f"Warning: Could not load {filename}: {e}")
    
    # Fallback to colored placeholder
    return load_placeholder_image(width, height, fallback_color)


def create_asset_dict(tile_size):
    """Create a dictionary of images for all assets."""
    colors = {
        'red': (200, 50, 50),
        'green': (50, 200, 50),
        'blue': (50, 50, 200),
        'neutral': (100, 100, 100),
        'yellow': (200, 200, 50),
        'purple': (200, 50, 200),
        'cyan': (50, 200, 200),
        'white': (200, 200, 200),
        'black': (30, 30, 30),
    }
    
    assets = {}
    # Walls
    assets['wr'] = load_texture('red_wall.bmp', tile_size, tile_size, colors['red'])
    assets['wg'] = load_texture('green_wall.bmp', tile_size, tile_size, colors['green'])
    assets['wb'] = load_texture('blue_wall.bmp', tile_size, tile_size, colors['blue'])
    assets['w_normal'] = load_texture('Wall_normal.bmp', tile_size, tile_size, colors['white'])
    assets['w_cobweb'] = load_texture('Wall_cobwebs.bmp', tile_size, tile_size, colors['white'])
    assets['wy'] = load_texture('yellow_wall.bmp', tile_size, tile_size, colors['yellow'])
    
    # Player (24x24) with sprite variants for each mask
    player_size = 24
    assets['p'] = load_texture('protagonist_base_right.bmp', player_size, player_size, colors['blue'])
    assets['p_red'] = load_texture('protagonist_bear_right.bmp', player_size, player_size, colors['red'])
    assets['p_green'] = load_texture('protagonist_turtle_right.bmp', player_size, player_size, colors['green'])
    assets['p_blue'] = load_texture('protagonist_wolf_right.bmp', player_size, player_size, colors['blue'])
    
    # Enemies - use mask textures as enemy sprites
    assets['er'] = load_texture('Ghost_enemy.bmp', tile_size, tile_size, colors['red'])
    assets['eg'] = load_texture('Ghost_enemy.bmp', tile_size, tile_size, colors['green'])
    assets['eb'] = load_texture('Ghost_enemy.bmp', tile_size, tile_size, colors['blue'])
    assets['ee'] = load_texture('Ghost_enemy.bmp', tile_size, tile_size, colors['yellow'])
    
    # Masks
    assets['mr'] = load_texture('red_bear_mask_32.bmp', tile_size, tile_size, colors['red'])
    assets['mg'] = load_texture('green_turtle_mask_32.bmp', tile_size, tile_size, colors['green'])
    assets['mb'] = load_texture('blue_wolf_mask_32.bmp', tile_size, tile_size, colors['blue'])
    
    # Boxes
    assets['br'] = load_texture('red_box.bmp', tile_size, tile_size, (180, 50, 50))
    
    # Doors and keys
    assets['dk1'] = load_texture('door.bmp', tile_size, tile_size, colors['purple'])
    assets['dk2'] = load_texture('door.bmp', tile_size, tile_size, colors['purple'])
    assets['dk3'] = load_texture('door.bmp', tile_size, tile_size, colors['purple'])
    assets['k1'] = load_texture('image.bmp', tile_size, tile_size, colors['yellow'])
    assets['k2'] = load_texture('image.bmp', tile_size, tile_size, colors['yellow'])
    assets['k3'] = load_texture('image.bmp', tile_size, tile_size, colors['yellow'])
    assets['dp1'] = load_texture('door.bmp', tile_size, tile_size, colors['green'])
    assets['pr'] = load_texture('press.bmp', tile_size, tile_size, colors['white'])



    # Traps
    for trap_type in ['tau', 'tad', 'tar', 'tal', 'tgu', 'tgd', 'tgr', 'tgl']:
        assets[trap_type] = load_texture(f'{trap_type}.bmp', tile_size, tile_size, colors['purple'])
    
    # Spike traps - store both closed and open variants
    assets['tgr_closed'] = load_texture('spikes_closed.bmp', tile_size, tile_size, (100, 100, 100))
    assets['tgr_open'] = load_texture('spikes_open.bmp', tile_size, tile_size, (100, 100, 100))
    
    # Decoration
    assets['dec'] = load_texture('decoration.bmp', tile_size, tile_size, (150, 150, 150))
    
    # Endpoint (flag)
    assets['end'] = load_texture('level_end.bmp', tile_size, tile_size, colors['green'])
    
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
    doors = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    plates = pygame.sprite.Group()
    boxes = pygame.sprite.Group()
    traps = pygame.sprite.Group()
    decorations = pygame.sprite.Group()
    endpoints = pygame.sprite.Group()
    enemies=pygame.sprite.Group()

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
                        sprite_variants = {
                            'red': assets['p_red'],
                            'green': assets['p_green'],
                            'blue': assets['p_blue']
                        }
                        player = Player(x + (tile_size - 24) // 2, y + (tile_size - 24) // 2, assets['p'], lives=3, sprite_variants=sprite_variants)
                        all_sprites.add(player)
                    
                    # Neutral wall
                    elif cell == 'w':
                        # 5% chance for cobweb wall
                        if random.random() < 0.05:
                            wall_img = assets['w_cobweb']
                        else:
                            wall_img = assets['w_normal']
                            
                        wall = Wall(x, y, wall_img, tile_size)
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                    
                    # Red wall
                    elif cell == 'wr':
                        wall = Wall(x, y, assets['wr'], tile_size, color='red')
                        wall.color = 'red'
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                        mask_sprites.add(wall)
                    
                    # Green wall
                    elif cell == 'wg':
                        wall = Wall(x, y, assets['wg'], tile_size, color='green')
                        wall.color = 'green'
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                        mask_sprites.add(wall)
                    
                    # Blue wall
                    elif cell == 'wb':
                        wall = Wall(x, y, assets['wb'], tile_size, color='blue')
                        wall.color = 'blue'
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                        mask_sprites.add(wall)
                    
                    # Yellow wall
                    elif cell == 'wy':
                        wall = Wall(x, y, assets['wy'], tile_size, color='yellow')
                        wall.color = 'yellow'
                        all_sprites.add(wall)
                        solid_sprites.add(wall)
                    
                    # Red mask
                    elif cell == 'mr':
                        mask_obj = Mask(x, y, assets['mr'], 'red')
                        all_sprites.add(mask_obj)
                    
                    # Green mask
                    elif cell == 'mg':
                        mask_obj = Mask(x, y, assets['mg'], 'green')
                        all_sprites.add(mask_obj)
                    
                    # Blue mask
                    elif cell == 'mb':
                        mask_obj = Mask(x, y, assets['mb'], 'blue')
                        all_sprites.add(mask_obj)
                    
                    # Red enemy
                    elif cell == 'er':
                        enemy = Enemy(x, y, assets['er'], 'red', lives=1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                        mask_sprites.add(enemy)
                    
                    # Green enemy
                    elif cell == 'eg':
                        enemy = Enemy(x, y, assets['eg'], 'green', lives=1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                        mask_sprites.add(enemy)
                    
                    # Blue enemy
                    elif cell == 'eb':
                        enemy = Enemy(x, y, assets['eb'], 'blue', lives=1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                        mask_sprites.add(enemy)
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
                    
                    # Key 1, 2, 3
                    elif cell in ['k1', 'k2', 'k3']:
                        key_id = int(cell[1])
                        key = Key(x, y, assets[cell], key_id)
                        all_sprites.add(key)
                        keys.add(key)
                    
                    # Door/Pressure plate 1
                    elif cell == 'dp1':
                        door = Door(x, y, assets['dp1'], 1)
                        all_sprites.add(door)
                        solid_sprites.add(door)
                        doors.add(door)
                    
                    # Pressure plate 1
                    elif cell in ['p1','p2','p3']:
                        print('making plate')
                        plate = PressPlate(x, y, assets['pr'], 1)
                        all_sprites.add(plate)
                        plates.add(plate)
                    
                    # Arrow traps
                    elif cell in ['tau', 'tad', 'tar', 'tal']:
                        direction_map = {'tau': 'up', 'tad': 'down', 'tar': 'right', 'tal': 'left'}
                        trap = ArrowTrap(x, y, assets[cell], direction_map[cell])
                        all_sprites.add(trap)
                        traps.add(trap)
                    
                    # Spike traps (guillotine right with alternating animation)
                    elif cell == 'tgr':
                        spike = Spike(x, y, assets['tgr_closed'], assets['tgr_open'])
                        all_sprites.add(spike)
                        traps.add(spike)
                    
                    # Guillotine traps
                    elif cell in ['tgu', 'tgd', 'tgl']:
                        direction_map = {'tgu': 'up', 'tgd': 'down', 'tgl': 'left'}
                        trap = GuillotineTrap(x, y, assets[cell], direction_map[cell])
                        all_sprites.add(trap)
                        traps.add(trap)
                    
                    # Decoration
                    elif cell == 'dec':
                        deco = Decoration(x, y, assets['dec'])
                        all_sprites.add(deco)
                    
                    # Endpoint
                    elif cell == 'end':
                        endpoint = Endpoint(x, y, assets['end'])
                        all_sprites.add(endpoint)
                        endpoints.add(endpoint)
                    
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
        'boxes': boxes,
        'traps': traps,
        'decorations': decorations,
        'endpoints': endpoints,
        'presses': plates,
    }