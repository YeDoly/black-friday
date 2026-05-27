from __future__ import annotations

import math
import random

import pygame

import config.settings as cfg


class Customer:
    """
    Klasa reprezentująca klienta poruszającego się w wyznaczonej strefie (poligonie).
    """

    def __init__(
        self,
        start_x: float,
        start_y: float,
        customer_type: int,
        polygon: list[tuple[float, float]],
    ) -> None:
        self.x: float = start_x
        self.y: float = start_y
        self.polygon: list[tuple[float, float]] = polygon
        self.customer_type: int = customer_type

        # Logika animacji
        self._sprites: list[list[pygame.Surface]] = []
        self._anim_timer: float = 0.0
        self._anim_frame: int = 0
        self._facing_right: bool = True
        self._is_moving: bool = False

        # Logika AI
        self.target_x: float = start_x
        self.target_y: float = start_y
        self.state: str = "IDLE"
        self.idle_timer: float = random.uniform(1.0, 3.0)
        self.speed: float = cfg.PLAYER_SPEED * random.uniform(0.6, 0.9)

        # Wyliczenie granic do optymalizacji losowania punktów
        self.min_x = min(p[0] for p in polygon)
        self.max_x = max(p[0] for p in polygon)
        self.min_y = min(p[1] for p in polygon)
        self.max_y = max(p[1] for p in polygon)

        self._load_sprites()

    def _load_sprites(self) -> None:
        target = (cfg.PLAYER_W * cfg.ZOOM, cfg.PLAYER_H * cfg.ZOOM)

        def load(name: str) -> pygame.Surface:
            path = cfg.ENTITIES_DIR / "customers" / name
            raw = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.scale(raw, target)

        prefix = f"klient_{self.customer_type}_"
        standing = load(f"{prefix}standing.png")
        left_leg = load(f"{prefix}left_leg_up.png")
        right_leg = load(f"{prefix}right_leg_up.png")

        def flip(s: pygame.Surface) -> pygame.Surface:
            return pygame.transform.flip(s, True, False)

        self._sprites = [
            [standing, left_leg, right_leg],
            [flip(standing), flip(left_leg), flip(right_leg)],
        ]

    def get_current_sprite(self) -> pygame.Surface:
        dir_idx = 1 if self._facing_right else 0
        if self._is_moving:
            walk_frame_idx = self._anim_frame + 1
            return self._sprites[dir_idx][walk_frame_idx]
        return self._sprites[dir_idx][0]

    def update(self, dt: float) -> None:
        if self.state == "IDLE":
            self._is_moving = False
            self.idle_timer -= dt
            if self.idle_timer <= 0:
                self._pick_new_target()
                self.state = "MOVING"

        elif self.state == "MOVING":
            self._is_moving = True
            self._move_towards_target(dt)

        if self._is_moving:
            self._anim_timer += dt
            if self._anim_timer >= cfg.WALK_FRAME_DURATION:
                self._anim_timer -= cfg.WALK_FRAME_DURATION
                self._anim_frame = 1 - self._anim_frame
        else:
            self._anim_timer = 0.0
            self._anim_frame = 0

    def _pick_new_target(self) -> None:
        max_attempts = 100
        for _ in range(max_attempts):
            tx = random.uniform(self.min_x, self.max_x)
            ty = random.uniform(self.min_y, self.max_y)
            if self._is_point_in_polygon(tx, ty):
                self.target_x = tx
                self.target_y = ty
                return

        # Jeśli nie uda się wylosować (nie powinno się zdarzyć), klient stoi w miejscu
        self.target_x = self.x
        self.target_y = self.y

    def _move_towards_target(self, dt: float) -> None:
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)

        # Margines błędu przy dotarciu do celu
        if distance < 5.0:
            self.state = "IDLE"
            self.idle_timer = random.uniform(1.5, 4.0)
            return

        dir_x = dx / distance
        dir_y = dy / distance

        self._facing_right = dir_x > 0

        # Proponowana następna pozycja po wykonaniu kroku ruchu
        next_x = self.x + dir_x * self.speed * dt
        next_y = self.y + dir_y * self.speed * dt

        # Jeśli kolejny krok wychodzi poza wielobok, nie poruszamy się poza niego.
        # Zamiast tego wybieramy nowy cel wewnątrz strefy.
        if self._is_point_in_polygon(next_x, next_y):
            self.x = next_x
            self.y = next_y
        else:
            # Unikamy wychodzenia poza obszar - wyznacz inny cel i przejdź w tryb IDLE
            self._pick_new_target()
            self.state = "IDLE"
            self.idle_timer = random.uniform(0.5, 1.5)
            return

    def _is_point_in_polygon(self, x: float, y: float) -> bool:
        """Standardowy, niezawodny algorytm Even-Odd do ray-castingu na wielobokach."""
        inside = False
        j = len(self.polygon) - 1

        for i in range(len(self.polygon)):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]

            # Sprawdzenie czy promień przecina krawędź
            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi) + xi
            )
            if intersect:
                inside = not inside

            j = i

        return inside
