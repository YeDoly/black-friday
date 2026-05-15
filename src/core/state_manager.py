import pygame

from config.literals import iSTATES
from config.settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from states.base import BaseState
from states.menu import MenuState
from states.options import OptionsState

from .assets_manager import AssetsManager


class StateManager:
    def __init__(self, assets: AssetsManager):
        self.screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.__running: bool = True
        pygame.display.set_caption("Czarny piątek - Kradnij jak czarnuch")

        self.assets: AssetsManager = assets
        self.assets.load_all()

        self.states: dict[iSTATES, BaseState] = {
            "MENU": MenuState(self),
            # "GAME": GameState(self),
            "OPTIONS": OptionsState(self),
        }

        self.current_state: BaseState = self.states["MENU"]

    def change_state(self, state_name: iSTATES):
        """Zmienia aktywny widok na inny."""
        self.current_state = self.states[state_name]

    def run(self):
        """Główna pętla gry."""
        while self.__running:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.__running = False

            self.current_state.handle_events(events)
            self.current_state.update(dt)
            self.current_state.draw(self.screen)

            pygame.display.flip()

    def quit(self):
        """Zatrzymuje główną pętlę gry."""
        self.__running = False
