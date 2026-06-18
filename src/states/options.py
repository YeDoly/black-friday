from typing import override

import pygame
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from config.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from core.interfaces import IStateManager
from objects.button import Button

from .base import BaseState


class OptionsState(BaseState):
    def __init__(self, manager: IStateManager):
        super().__init__(manager)

        self.bg: pygame.Surface = self.manager.assets.images.get("gui/background")
        self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.font_title: Font = self.manager.assets.fonts.get("gui/font_main", size=48)
        self.font_text: Font = self.manager.assets.fonts.get("gui/font_main", size=24)

        self.title_text: str = "JAK GRAĆ"
        self.instructions: list[tuple[str, str, str]] = [
            ("RUCH", "WASD", "Używaj klawiszy WASD do poruszania się postacią."),
            (
                "ZBIERANIE",
                "Półka + [E]",
                "Podejdź do półki z towarem od dołu i naciśnij E, aby zabrać produkt.",
            ),
            ("PRZESZKODY", "NPC", "Inni klienci (NPC) mogą blokować Twoją drogę."),
            (
                "KASA",
                "ZAPŁAĆ + [E]",
                "Gdy lista jest pełna, podejdź do kasy od dołu i naciśnij E.",
            ),
            (
                "INTERFEJS",
                "Prawy i Lewy Górny Róg",
                "W prawym oraz lewym górnym rogu ekranu znajdują się:",
            ),
            ("• Czas & Najlepszy Czas", "", ""),
            ("• Lista zakupów & Koszyk", "", ""),
        ]

        self.panel_color: tuple[int, int, int, int] = (0, 0, 0, 180)
        self.panel_rect: Rect = pygame.Rect(
            int(SCREEN_WIDTH * 0.05),
            int(SCREEN_HEIGHT * 0.15),
            int(SCREEN_WIDTH * 0.9),
            int(SCREEN_HEIGHT * 0.7),
        )
        self.panel_surf: Surface = pygame.Surface(
            (self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA
        )
        self.panel_surf.fill(self.panel_color)

        self.title_surf: Surface = self.font_title.render(
            self.title_text, True, (255, 255, 255)
        )
        self.title_pos: tuple[int, int] = (
            (SCREEN_WIDTH - self.title_surf.get_width()) // 2,
            int(SCREEN_HEIGHT * 0.05),
        )

        self.instruction_surfaces: list[tuple[Surface, Surface | None]] = []
        for header, sub, text in self.instructions:
            h_surf = self.font_text.render(header, True, (255, 215, 0))
            if sub:
                h_surf.blit(
                    self.font_text.render(f" ({sub})", True, (200, 200, 200)),
                    (h_surf.get_width() + 5, 0),
                )

            t_surf = None
            if text:
                t_surf = self.font_text.render(text, True, (255, 255, 255))

            self.instruction_surfaces.append((h_surf, t_surf))

            exit_img = self.manager.assets.images.get("gui/buttons/exit")
            exit_img = pygame.transform.scale(exit_img, (200, 80))
            self.start_btn: Button = Button(0, 0, exit_img)

            btn_x = (SCREEN_WIDTH - exit_img.get_width()) // 2
            btn_y = SCREEN_HEIGHT - exit_img.get_height() - int(SCREEN_HEIGHT * 0.05)
            self.back_btn: Button = Button(btn_x, btn_y, exit_img)

    @override
    def handle_events(self, events: list[pygame.event.Event]):
        for event in events:
            if self.back_btn and self.back_btn.is_clicked(event):
                self.manager.change_state("MENU")

    @override
    def update(self, dt: float):
        pass

    @override
    def draw(self, screen: pygame.Surface):
        screen.blit(self.bg, (0, 0))

        screen.blit(self.title_surf, self.title_pos)
        screen.blit(self.panel_surf, (self.panel_rect.x, self.panel_rect.y))

        current_y = self.panel_rect.y + 20
        margin_x = self.panel_rect.x + 30

        for h_surf, t_surf in self.instruction_surfaces:
            screen.blit(h_surf, (margin_x, current_y))
            current_y += h_surf.get_height() + 5

            if t_surf:
                screen.blit(t_surf, (margin_x + 20, current_y))
                current_y += t_surf.get_height() + 15
            else:
                current_y += 10

        if self.back_btn:
            self.back_btn.draw(screen)

    @override
    def enter(self):
        print("Instrukcje wejście")

    @override
    def exit(self):
        print("Instrukcje wyjście")
