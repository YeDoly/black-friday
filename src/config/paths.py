from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ASSETS_DIR = BASE_DIR / "assets"

IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"

MAP_DIR = ASSETS_DIR / "map"

ENTITIES_DIR = IMAGES_DIR / "entities"
SPRITES_DIR = IMAGES_DIR / "sprites"
TILES_DIR = IMAGES_DIR / "tiles"
UI_DIR = ASSETS_DIR / "ui"
VFX_DIR = ASSETS_DIR / "vfx"

MUSIC_DIR = SOUNDS_DIR / "music"
SFX_DIR = SOUNDS_DIR / "sfx"
