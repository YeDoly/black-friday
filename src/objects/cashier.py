from __future__ import annotations

import pygame

import config.paths as paths
import config.settings as cfg


class Cashier:
    def __init__(self, cashier_type: int, x: float, y: float) -> None:
        self.cashier_type: int = cashier_type

        self.x: float = x
        self.y: float = y

        self._sprites: list[list[pygame.Surface]] = []
        self._load_sprites()

    def get_hitbox_rect(self) -> pygame.Rect:
        """Zwraca kształt hitboxu klienta (identyczny jak u gracza)."""
        return pygame.Rect(
            int(self.x) - cfg.HITBOX_W // 2,
            int(self.y) - cfg.HITBOX_H,
            cfg.HITBOX_W,
            cfg.HITBOX_H,
        )

    def _load_sprites(self) -> None:
        target = (cfg.PLAYER_W * cfg.ZOOM, cfg.PLAYER_H * cfg.ZOOM)

        def load(name: str) -> pygame.Surface:
            path = paths.ENTITIES_DIR / "cashiers" / name
            raw = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.scale(raw, target)

        entity = load(f"kasjer_{self.cashier_type}.png")

        self._sprites = [[entity]]

    def get_current_sprite(self) -> pygame.Surface:
        return self._sprites[0][0]
