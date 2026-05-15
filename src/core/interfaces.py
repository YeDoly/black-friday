from typing import Protocol

import pygame

from config.literals import iSTATES
from core.assets_manager import AssetsManager


class IStateManager(Protocol):
    screen: pygame.Surface
    clock: pygame.time.Clock
    assets: AssetsManager

    def change_state(self, state_name: iSTATES) -> None: ...
    def run(self) -> None: ...
    def quit(self) -> None: ...
