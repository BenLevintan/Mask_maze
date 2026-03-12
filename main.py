import pygame
import sys
import os
import asyncio
import ctypes
from glob import glob
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.audio import SoundManager
from src.loader import load_level

os.environ['SDL_VIDEO_CENTERED'] = '1'

TILE_SIZE = 32
WIDTH, HEIGHT = 1800, 960

# Level list - order matters
LEVELS = [
    '_tutorial_0.csv',
    '_tutorial_1.csv',
    '_tutorial_2.csv',    
    '_wall_level_1.csv',
    '_tutorial_spike_1.csv',     
    '_tutorial_spike_2.csv',
    '_level_1.csv',
    '_level_2.csv', 
    '_tutorial_ghost_0.csv',  
    '_tutorial_ghost.csv',
    'tutorial_box.csv',
    'maze_level_2.csv', 
    'maze_level_3.csv',
    'maze_level_4.csv',
    'maze_level_omri1.csv',
    'maze_level_omri2.csv',
    'ghost_boss.csv',
    'you_win.csv'
]

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()

# OpenGL Configuration - Use DOUBLEBUF and OPENGL flags
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
pygame.display.set_caption("Masks - Game Jam")

# We draw the game to this off-screen surface, then pass it to the shader
game_surface = pygame.Surface((WIDTH, HEIGHT))

assets_path = os.path.join(os.path.dirname(__file__), 'assets', 'game sound')
sound_manager = SoundManager(assets_path)

# Load sound effects
sound_manager.load_sound('key', 'sound effects/key/key1.wav')
sound_manager.load_sound('trap', 'sound effects/trap/trap1.wav', volume=0.5)
sound_manager.load_sound('button', 'sound effects/button/button1.wav')

# Load drag sound variants (for door opening)
drag_sounds = glob(os.path.join(assets_path, 'sound effects', 'drag', '*.wav'))
sound_manager.load_sound_variants('drag', drag_sounds)

# Load hurt sound variants (for taking damage)
hurt_sounds = glob(os.path.join(assets_path, 'sound effects', 'hurt', '*.wav'))
sound_manager.load_sound_variants('hurt', hurt_sounds)

# Start background music
sound_manager.play_music('music/MainMusic.wav')

# Load chase music
sound_manager.load_chase_music('music/ChaseMusic.wav', volume=0.3)

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
plate_presses = level_data['presses']
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
        x = target.rect.centerx - self.width // 2
        y = target.rect.centery - self.height // 2
        x = max(0, x)
        y = max(0, y)
        self.camera.x = x
        self.camera.y = y

camera = Camera(WIDTH, HEIGHT)

def update_mask_effects(player, mask_sprites):
    for sprite in mask_sprites:
        if hasattr(sprite, 'color'):
            if player.current_mask == sprite.color:
                if hasattr(sprite, 'toggle'):
                    sprite.toggle(False)
            else:
                if hasattr(sprite, 'toggle'):
                    sprite.toggle(True)

def check_aabb_collision(rect1, rect2):
    return rect1.colliderect(rect2)

def resolve_collision(player, solid_sprites):
    player.pos.x += player.velocity.x
    player.rect.x = player.pos.x
    
    for solid in solid_sprites:
        if hasattr(solid, 'on_off') and not solid.on_off:
            continue
        if hasattr(solid, 'is_open') and solid.is_open:
            continue
        if check_aabb_collision(player.rect, solid.rect):
            player.pos.x -= player.velocity.x
            player.rect.x = player.pos.x
            player.velocity.x = 0
            break
    
    player.pos.y += player.velocity.y
    player.rect.y = player.pos.y
    
    for solid in solid_sprites:
        if hasattr(solid, 'on_off') and not solid.on_off:
            continue
        if hasattr(solid, 'is_open') and solid.is_open:
            continue
        if check_aabb_collision(player.rect, solid.rect):
            player.pos.y -= player.velocity.y
            player.rect.y = player.pos.y
            player.velocity.y = 0
            break

def handle_mask_pickup(player, mask_sprites):
    for mask_obj in mask_sprites:
        if hasattr(mask_obj, 'color') and not hasattr(mask_obj, 'on_off'):
            if isinstance(mask_obj, type(player)) or mask_obj.__class__.__name__ == 'Mask':
                if check_aabb_collision(player.rect, mask_obj.rect):
                    player.equip_mask(mask_obj.color)
                    sound_manager.play_sound('button')
                    mask_obj.kill()

def handle_key_pickup(player, keys, doors):
    for key in keys:
        if check_aabb_collision(player.rect, key.rect):
            for door in doors:
                if door.door_id == key.key_id:
                    door.open_door()
                    sound_manager.play_sound('drag')
                    if door in solid_sprites:
                        solid_sprites.remove(door)
            key.kill()

def check_level_complete(player, endpoints):
    for endpoint in endpoints:
        if check_aabb_collision(player.rect, endpoint.rect):
            return True
    return False

def check_spike_collision(player, traps):
    for trap in traps:
        if trap.__class__.__name__ == 'Spike':
            if check_aabb_collision(player.rect, trap.rect):
                if trap.is_open:
                    return True
    return False

def next_level():
    global current_level_index, player, all_sprites, solid_sprites, mask_sprites, endpoints, camera, doors, keys, enemies, traps, plate_presses, boxes
    current_level_index += 1
    level_data = load_level_by_index(current_level_index)
    
    if not level_data:
        print("You beat all levels! Congratulations!")
        return False
        
    enemies = level_data['enemies']
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
    plate_presses = level_data['presses']
    boxes = level_data['boxes']
    print(f"Level {current_level_index + 1} loaded!")
    return True

def reload_level():
    global player, all_sprites, solid_sprites, mask_sprites, endpoints, camera, doors, keys, enemies, traps, plate_presses, boxes
    level_data = load_level_by_index(current_level_index)
    
    if not level_data:
        print("Error: Could not reload level!")
        return False
    
    player = level_data['player']
    all_sprites = level_data['all_sprites']
    solid_sprites = level_data['solid_sprites']
    mask_sprites = level_data['mask_sprites']
    endpoints = level_data['endpoints']
    doors = level_data['doors']
    keys = level_data['keys']
    enemies = level_data['enemies']
    traps = level_data['traps']
    plate_presses = level_data['presses']
    boxes = level_data['boxes']
    camera = Camera(WIDTH, HEIGHT)
    
    for press in plate_presses:
        press.set_door_list([door for door in doors if door.door_id == press.plate_id])
    
    print(f"Level {current_level_index + 1} reloaded!")
    return True

for press in plate_presses:
    press.set_door_list([door for door in doors if door.door_id == press.plate_id])

enemy_collisions = 0

VERTEX_SHADER = """
#version 100
attribute vec2 position;
attribute vec2 texcoord;
varying vec2 v_texcoord;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    v_texcoord = texcoord; 
}
"""

FRAGMENT_SHADER = """
#version 100
precision mediump float;
varying vec2 v_texcoord;
uniform sampler2D texture;

void main() {
    vec2 crt_coords = v_texcoord - 0.5;
    float rsq = crt_coords.x * crt_coords.x + crt_coords.y * crt_coords.y;
    crt_coords += crt_coords * (rsq * 0.08); 
    crt_coords += 0.5;

    // Use a small epsilon for bounds checking to avoid artifacts
    if (crt_coords.x < 0.0 || crt_coords.x > 1.0 || crt_coords.y < 0.0 || crt_coords.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    float r = texture2D(texture, crt_coords + vec2(0.0008, 0.0)).r;
    float g = texture2D(texture, crt_coords).g;
    float b = texture2D(texture, crt_coords - vec2(0.0008, 0.0)).b;
    vec4 color = vec4(r, g, b, 1.0);

    float scanline = sin(crt_coords.y * 800.0) * 0.02;
    color.rgb -= scanline;

    float vignette = distance(v_texcoord, vec2(0.5));
    color.rgb *= smoothstep(1.0, 0.3, vignette * vignette * 1.5);

    gl_FragColor = color;
}
"""

shader = compileProgram(
    compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
    compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
)

# Create full-screen quad (x, y, u, v)
quad_vertices = (ctypes.c_float * 16)(
    -1.0, -1.0,  0.0, 0.0,
     1.0, -1.0,  1.0, 0.0,
    -1.0,  1.0,  0.0, 1.0,
     1.0,  1.0,  1.0, 1.0,
)

# VBO setup
vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(quad_vertices), quad_vertices, GL_STATIC_DRAW)

position_loc = glGetAttribLocation(shader, "position")
texcoord_loc = glGetAttribLocation(shader, "texcoord")

# Texture setup
texture_id = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture_id)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

# --- ASYNC MAIN LOOP ---

async def main():
    global running, current_level_index, player, enemy_collisions
    global all_sprites, solid_sprites, mask_sprites, endpoints, camera 
    global doors, keys, enemies, traps, plate_presses, boxes

    font = pygame.font.Font(None, 24)

    while running:
        dt = clock.tick(60) / 1000.0 

        for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        # Add these two lines right here
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        # The rest stays the same
                        elif event.key == pygame.K_1:
                            player.equip_mask('red')
                        elif event.key == pygame.K_2:
                            player.equip_mask('green')
                        elif event.key == pygame.K_3:
                            player.equip_mask('blue')
                        elif event.key == pygame.K_0:
                            player.unequip_mask()
                        elif event.key == pygame.K_r:
                            reload_level()
        
        if player:
            player.handle_input()
            
            predicted_rect = player.rect.copy()
            predicted_rect.x += player.velocity.x
            predicted_rect.y += player.velocity.y
            
            for box in boxes:
                if predicted_rect.colliderect(box.rect):
                    if player.current_mask == box.color:
                        push_x, push_y = 0, 0
                        if player.velocity.x > 0: push_x = player.speed
                        elif player.velocity.x < 0: push_x = -player.speed
                        if player.velocity.y > 0: push_y = player.speed
                        elif player.velocity.y < 0: push_y = -player.speed
                        
                        new_box_rect = box.rect.copy()
                        new_box_rect.x += push_x
                        new_box_rect.y += push_y
                        
                        can_push = True
                        for solid in solid_sprites:
                            if solid != box and new_box_rect.colliderect(solid.rect):
                                if hasattr(solid, 'on_off') and not solid.on_off: continue
                                if hasattr(solid, 'is_open') and solid.is_open: continue
                                can_push = False
                                break
                        
                        for other_box in boxes:
                            if other_box != box and new_box_rect.colliderect(other_box.rect):
                                can_push = False
                                break
                        
                        if can_push:
                            box.pos.x += push_x
                            box.pos.y += push_y
                            box.rect.topleft = (box.pos.x, box.pos.y)
            
            resolve_collision(player, solid_sprites)
            update_mask_effects(player, mask_sprites)
            handle_mask_pickup(player, all_sprites)
            
            for mask in mask_sprites:
                if mask.__class__.__name__ == 'Mask':
                    mask.update(dt)
            
            for key in keys:
                key.update(dt)

            for press in plate_presses:
                was_pressed = press.is_pressed
                press.update(boxes, player, dt)
                if press.is_pressed != was_pressed:
                    press.change_doors()
                    sound_manager.play_sound('drag')

            any_enemy_chasing = False
            for enemy in enemies:
                enemy.update(player)
                resolve_collision(enemy, solid_sprites)
                
                distance = ((player.pos[0] - enemy.pos[0])**2 + (player.pos[1] - enemy.pos[1])**2)**0.5
                if distance < enemy.chase_distance:
                    any_enemy_chasing = True
                
                if check_aabb_collision(player.rect, enemy.rect):
                    enemy_collisions += 1
                    if enemy_collisions > 50:
                        enemy_collisions = 0
                        sound_manager.play_sound('hurt')
                        reload_level()
            
            if any_enemy_chasing:
                sound_manager.start_chase()
            else:
                sound_manager.stop_chase()

            for trap in traps:
                if trap.__class__.__name__ == 'Spike':
                    was_open = trap.is_open
                    trap.update(dt)
                    if trap.is_open and not was_open:
                        sound_manager.play_sound('trap')
            
            handle_key_pickup(player, keys, doors)
            
            if check_spike_collision(player, traps):
                sound_manager.play_sound('hurt')
                reload_level()
            
            if check_level_complete(player, endpoints):
                if not next_level():
                    running = False
            
            camera.update(player)
        
        # 1. RENDER GAME TO OFF-SCREEN SURFACE
        game_surface.fill((20, 20, 30))
        
        def get_sprite_layer(sprite):
            class_name = sprite.__class__.__name__
            if class_name in ('Spike', 'PressPlate'): return 0 
            elif class_name == 'Player': return 2 
            return 1 
        
        sorted_sprites = sorted(all_sprites, key=lambda s: (get_sprite_layer(s), s.rect.y))
        for sprite in sorted_sprites:
            game_surface.blit(sprite.image, camera.apply(sprite))
        
        lives_text = font.render(f"Lives: {player.lives}", True, (255, 255, 255))
        mask_text = font.render(f"Mask: {player.current_mask or 'None'}", True, (255, 255, 255))
        level_text = font.render(f"Level: {current_level_index + 1}/{len(LEVELS)}", True, (255, 255, 255))
        help_text = font.render("R=Reset | ESC=Exit | Arrow Keys=Move", True, (150, 150, 150))
        
        game_surface.blit(help_text, (10, HEIGHT - 110))
        game_surface.blit(level_text, (10, HEIGHT - 80))
        game_surface.blit(mask_text, (10, HEIGHT - 50))
        game_surface.blit(lives_text, (10, HEIGHT - 20))
        
        # 2. OPENGL SHADER PIPELINE (Draws the surface onto the screen)
        texture_data = pygame.image.tostring(game_surface, "RGBA", True)
        
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(shader)

        # Update texture data
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glUniform1i(glGetUniformLocation(shader, "texture"), 0)

        # Draw the Quad
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glEnableVertexAttribArray(position_loc)
        glVertexAttribPointer(position_loc, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(texcoord_loc)
        glVertexAttribPointer(texcoord_loc, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        
        pygame.display.flip()
        
        # CRITICAL: Let the browser breathe 
        await asyncio.sleep(0)

# Start the async execution
if __name__ == "__main__":
    asyncio.run(main())