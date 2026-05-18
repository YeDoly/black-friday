from typing import override

import pygame

from config.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from core.interfaces import IStateManager
from objects.button import Button

from .base import BaseState


class MenuState(BaseState):
    def __init__(self, manager: IStateManager):
        super().__init__(manager)

        self.bg: pygame.Surface = self.manager.assets.get_image("gui/background")
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        play_img = self.manager.assets.get_image("gui/buttons/play")
        play_img = pygame.transform.scale(play_img, (200, 80))
        self.start_btn: Button = Button(0, 0, play_img)

        options_img = self.manager.assets.get_image("gui/buttons/options")
        options_img = pygame.transform.scale(options_img, (200, 80))
        self.options_btn: Button = Button(200, 0, options_img)

        exit_img = self.manager.assets.get_image("gui/buttons/exit")
        exit_img = pygame.transform.scale(exit_img, (200, 80))
        self.exit_btn: Button = Button(400, 0, exit_img)

    @override
    def handle_events(self, events: list[pygame.event.Event]):
        for event in events:
            if self.start_btn.is_clicked(event):
                self.manager.change_state("GAME")
            if self.options_btn.is_clicked(event):
                self.manager.change_state("OPTIONS")
            if self.exit_btn.is_clicked(event):
                self.manager.quit()

    @override
    def update(self, dt: float):
        pass

    @override
    def draw(self, screen: pygame.Surface):
        screen.blit(self.bg, (0, 0))
        self.start_btn.draw(screen)
        self.options_btn.draw(screen)
        self.exit_btn.draw(screen)

    @override
    def enter(self):
        print("Menu wejście")

    @override
    def exit(self):
        print("Menu wyjście")
