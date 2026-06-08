from __future__ import annotations

import random
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    icon: pygame.Surface


class ShoppingListManager:
    """Zarządza listą losowych produktów do znalezienia w sklepie i ich statusem."""

    def __init__(
        self, available_products: list[Product], items_to_choose: int = 3
    ) -> None:
        self.all_products: list[Product] = available_products
        self.target_products: list[Product] = random.sample(
            available_products, min(items_to_choose, len(available_products))
        )
        self.status: dict[str, bool] = {
            product.id: False for product in self.target_products
        }

    def collect_item(self, product: Product) -> bool:
        """
        Oznacza produkt jako znaleziony, jeśli znajduje się na liście.
        Zwraca True, jeśli produkt był potrzebny i został zebrany po raz pierwszy.
        """
        if product.id in self.status and not self.status[product.id]:
            self.status[product.id] = True
            return True
        return False

    def is_list_complete(self) -> bool:
        """Sprawdza, czy gracz znalazł już wszystkie produkty z listy."""
        return all(self.status.values())

    def draw_ui(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Rysuje przyciemniony panel z listą produktów w lewym górnym rogu."""
        margin_x, margin_y = 20, 20
        padding = 12
        item_height = 40

        box_w = 280
        box_h = padding * 2 + len(self.target_products) * item_height

        bg_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (margin_x, margin_y))

        for i, product in enumerate(self.target_products):
            is_found = self.status[product.id]

            row_y = margin_y + padding + (i * item_height)

            icon_x = margin_x + padding
            icon_y = row_y + (item_height - product.icon.get_height()) // 2
            screen.blit(product.icon, (icon_x, icon_y))

            text_x = icon_x + product.icon.get_width() + padding

            text_color = (100, 255, 100) if is_found else (255, 255, 255)
            display_name = f"[X] {product.name}" if is_found else product.name

            text_surf = font.render(display_name, True, text_color)
            text_y = row_y + (item_height - text_surf.get_height()) // 2
            screen.blit(text_surf, (text_x, text_y))
