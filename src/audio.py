import pygame
import os
import random

class SoundManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        # Chase music system
        self.main_music_path = None
        self.chase_music = None  # pygame.mixer.Sound for chase music
        self.chase_channel = None  # Dedicated channel for chase music
        self.is_chasing = False
        
    def load_sound(self, name, filepath, volume=None):
        """Load a sound effect. Optional volume override (0.0 to 1.0)."""
        full_path = os.path.join(self.base_path, filepath)
        self.sounds[name] = pygame.mixer.Sound(full_path)
        self.sounds[name].set_volume(volume if volume is not None else self.sfx_volume)
    
    def load_sound_variants(self, name, filepaths):
        """Load multiple variants of a sound for random playback."""
        self.sounds[name] = []
        for filepath in filepaths:
            full_path = os.path.join(self.base_path, filepath)
            sound = pygame.mixer.Sound(full_path)
            sound.set_volume(self.sfx_volume)
            self.sounds[name].append(sound)
    
    def play_sound(self, name):
        """Play a sound effect. If multiple variants exist, plays a random one."""
        if name in self.sounds:
            sound = self.sounds[name]
            if isinstance(sound, list):
                random.choice(sound).play()
            else:
                sound.play()
    
    def play_music(self, filepath, loop=-1):
        """Play background music. loop=-1 means infinite loop."""
        full_path = os.path.join(self.base_path, filepath)
        self.main_music_path = full_path
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(loop)
    
    def load_chase_music(self, filepath):
        """Load chase music as a Sound object for independent playback."""
        full_path = os.path.join(self.base_path, filepath)
        self.chase_music = pygame.mixer.Sound(full_path)
        self.chase_music.set_volume(self.music_volume)
        # Reserve a channel for chase music
        self.chase_channel = pygame.mixer.Channel(7)  # Use channel 7 for chase music
    
    def start_chase(self):
        """Start chase music - pause main music, play chase from beginning."""
        if self.is_chasing:
            return  # Already chasing
        self.is_chasing = True
        pygame.mixer.music.pause()
        if self.chase_music and self.chase_channel:
            self.chase_channel.play(self.chase_music, loops=-1)
    
    def stop_chase(self):
        """Stop chase music - resume main music from where it paused."""
        if not self.is_chasing:
            return  # Not currently chasing
        self.is_chasing = False
        if self.chase_channel:
            self.chase_channel.stop()
        pygame.mixer.music.unpause()
    
    def stop_music(self):
        pygame.mixer.music.stop()
        if self.chase_channel:
            self.chase_channel.stop()
        self.is_chasing = False
    
    def pause_music(self):
        pygame.mixer.music.pause()
    
    def unpause_music(self):
        pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume):
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)
    
    def set_sfx_volume(self, volume):
        self.sfx_volume = volume
        for sound in self.sounds.values():
            if isinstance(sound, list):
                for s in sound:
                    s.set_volume(volume)
            else:
                sound.set_volume(volume)