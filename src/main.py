import sys

import pygame

from core.assets_manager import AssetsManager
from core.state_manager import StateManager

if __name__ == "__main__":
    pygame.init()

    assets = AssetsManager()
    app = StateManager(assets)

    assets.music.volume(0.1)
    assets.music.play("1")
    app.run()

    pygame.quit()
    sys.exit()
