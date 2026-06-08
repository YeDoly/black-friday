from __future__ import annotations

import math
import random

import pygame

import config.paths as paths
import config.settings as cfg


class Customer:
    def __init__(self, customer_type: int, polygon: list[tuple[float, float]]) -> None:
        self.polygon: list[tuple[float, float]] = polygon
        self.customer_type: int = customer_type

        self.min_x: float = min(p[0] for p in polygon)
        self.max_x: float = max(p[0] for p in polygon)
        self.min_y: float = min(p[1] for p in polygon)
        self.max_y: float = max(p[1] for p in polygon)

        self.x: float = 0.0
        self.y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0

        self._pick_new_target(initial_spawn=True)

        self._sprites: list[list[pygame.Surface]] = []
        self._anim_timer: float = 0.0
        self._anim_frame: int = 0
        self._facing_right: bool = True
        self._is_moving: bool = False

        self.state: str = "IDLE"
        self.idle_timer: float = random.uniform(1.0, 3.0)
        self.speed: float = cfg.PLAYER_SPEED * random.uniform(0.6, 0.9)

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
            path = paths.ENTITIES_DIR / "customers" / name
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

    def update(self, dt: float, player_hitbox: pygame.Rect | None = None) -> None:
        if self.state == "IDLE":
            self._is_moving = False
            self.idle_timer -= dt
            if self.idle_timer <= 0:
                self._pick_new_target()
                self.state = "MOVING"

        elif self.state == "MOVING":
            if player_hitbox and self.get_hitbox_rect().colliderect(player_hitbox):
                self._is_moving = False
            else:
                self._is_moving = True
                self._move_towards_target(dt)

        # Animacja
        if self._is_moving:
            self._anim_timer += dt
            if self._anim_timer >= cfg.WALK_FRAME_DURATION:
                self._anim_timer -= cfg.WALK_FRAME_DURATION
                self._anim_frame = 1 - self._anim_frame
        else:
            self._anim_timer = 0.0
            self._anim_frame = 0

    def _pick_new_target(self, initial_spawn: bool = False) -> None:
        max_attempts = 150

        if initial_spawn:
            local_min_x, local_max_x = self.min_x, self.max_x
            local_min_y, local_max_y = self.min_y, self.max_y
        else:
            search_radius = 200.0
            local_min_x = max(self.min_x, self.x - search_radius)
            local_max_x = min(self.max_x, self.x + search_radius)
            local_min_y = max(self.min_y, self.y - search_radius)
            local_max_y = min(self.max_y, self.y + search_radius)

        for _ in range(max_attempts):
            tx = random.uniform(local_min_x, local_max_x)
            ty = random.uniform(local_min_y, local_max_y)

            if self._is_point_in_polygon(tx, ty):
                if initial_spawn or self._is_path_clear(tx, ty):
                    self.target_x = tx
                    self.target_y = ty
                    if initial_spawn:
                        self.x = tx
                        self.y = ty
                    return

        if not initial_spawn:
            self.target_x = self.x
            self.target_y = self.y

    def _move_towards_target(self, dt: float) -> None:
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < 5.0:
            self.state = "IDLE"
            self.idle_timer = random.uniform(1.5, 4.0)
            return

        dir_x = dx / distance
        dir_y = dy / distance

        self._facing_right = dir_x > 0

        self.x += dir_x * self.speed * dt
        self.y += dir_y * self.speed * dt

    def _is_point_in_polygon(self, x: float, y: float) -> bool:
        inside = False
        j = len(self.polygon) - 1
        for i in range(len(self.polygon)):
            xi, yi = self.polygon[i]
            xj, yj = self.polygon[j]

            intersect = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi) + xi
            )
            if intersect:
                inside = not inside
            j = i
        return inside

    def _ccw(
        self, A: tuple[float, float], B: tuple[float, float], C: tuple[float, float]
    ) -> bool:
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def _segments_intersect(
        self,
        A: tuple[float, float],
        B: tuple[float, float],
        C: tuple[float, float],
        D: tuple[float, float],
    ) -> bool:
        return self._ccw(A, C, D) != self._ccw(B, C, D) and self._ccw(
            A, B, C
        ) != self._ccw(A, B, D)

    def _is_path_clear(self, tx: float, ty: float) -> bool:
        A = (self.x, self.y)
        B = (tx, ty)

        j = len(self.polygon) - 1
        for i in range(len(self.polygon)):
            C = self.polygon[i]
            D = self.polygon[j]

            if self._segments_intersect(A, B, C, D):
                return False
            j = i

        return True
