from abc import ABC, abstractmethod

import pygame

from core.interfaces import IStateManager


class BaseState(ABC):
    def __init__(self, manager: IStateManager):
        self.manager: IStateManager = manager

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]):
        """Musi zostać nadpisane. Obsługa klawiszy/myszki."""
        pass

    @abstractmethod
    def update(self, dt: float):
        """Musi zostać nadpisane. Logika gry."""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """Musi zostać nadpisane. Rysowanie na ekranie."""
        pass

    def enter(self):
        """Wywoływana przy wejściu w stan."""
        pass

    def exit(self):
        """Wywoływana przy wyjściu ze stanu."""
        pass
