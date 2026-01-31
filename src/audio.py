import pygame
import os
import random

class SoundManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        
    def load_sound(self, name, filepath):
        """Load a sound effect."""
        full_path = os.path.join(self.base_path, filepath)
        self.sounds[name] = pygame.mixer.Sound(full_path)
        self.sounds[name].set_volume(self.sfx_volume)
    
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
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.set_volume(self.music_volume)
        pygame.mixer.music.play(loop)
    
    def stop_music(self):
        pygame.mixer.music.stop()
    
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