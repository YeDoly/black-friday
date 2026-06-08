from __future__ import annotations

import pygame

import config.settings as cfg
from systems.shopping_list import Product


class Player:
    """
    Klasa reprezentująca gracza, odpowiedzialna za jego ruch, animację
    oraz interakcję fizyczną ze środowiskiem gry.
    """

    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y

        self._sprites: list[list[pygame.Surface]] = []
        self._anim_timer: float = 0.0
        self._anim_frame: int = 0
        self._facing_right: bool = True
        self._is_moving: bool = False

        self._load_sprites()

    def _load_sprites(self) -> None:
        """Ładuje i przygotowuje klatki animacji we właściwych kierunkach."""
        target = (cfg.PLAYER_W * cfg.ZOOM, cfg.PLAYER_H * cfg.ZOOM)

        def load(name: str) -> pygame.Surface:
            raw = pygame.image.load(str(cfg.PLAYER_DIR / name)).convert_alpha()
            return pygame.transform.scale(raw, target)

        standing = load("standing.png")
        left_leg = load("left_leg_up.png")
        right_leg = load("right_leg_up.png")

        def flip(s: pygame.Surface) -> pygame.Surface:
            return pygame.transform.flip(s, True, False)

        self._sprites = [
            [standing, left_leg, right_leg],
            [flip(standing), flip(left_leg), flip(right_leg)],
        ]

    def get_hitbox_rect(self) -> pygame.Rect:
        """Zwraca aktualny kształt hitboxu (środek poziomo na p.x, dół na p.y)."""
        return pygame.Rect(
            int(self.x) - cfg.HITBOX_W // 2,
            int(self.y) - cfg.HITBOX_H,
            cfg.HITBOX_W,
            cfg.HITBOX_H,
        )

    def get_current_sprite(self) -> pygame.Surface:
        """Zwraca właściwą powierzchnię graficzną na podstawie obecnego stanu."""
        dir_idx = 1 if self._facing_right else 0
        if self._is_moving:
            walk_frame_idx = self._anim_frame + 1
            return self._sprites[dir_idx][walk_frame_idx]
        return self._sprites[dir_idx][0]

    def handle_input(
        self,
        dt: float,
        collision_rects: list[pygame.Rect],
        map_w: int,
        map_h: int,
    ) -> None:
        """Przetwarza klawisze, wyznacza wektor ruchu i aktualizuje klatki animacji."""
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        if dx != 0.0 and dy != 0.0:
            dx *= cfg.VECTOR_NORM
            dy *= cfg.VECTOR_NORM

        self._is_moving = dx != 0.0 or dy != 0.0

        if dx > 0.0:
            self._facing_right = True
        elif dx < 0.0:
            self._facing_right = False

        if self._is_moving:
            self._anim_timer += dt
            if self._anim_timer >= cfg.WALK_FRAME_DURATION:
                self._anim_timer -= cfg.WALK_FRAME_DURATION
                self._anim_frame = 1 - self._anim_frame
        else:
            self._anim_timer = 0.0
            self._anim_frame = 0

        self._move(
            dx * cfg.PLAYER_SPEED * dt,
            dy * cfg.PLAYER_SPEED * dt,
            collision_rects,
            map_w,
            map_h,
        )

    def _move(
        self,
        dx: float,
        dy: float,
        collision_rects: list[pygame.Rect],
        map_w: int,
        map_h: int,
    ) -> None:
        """Przesuwa gracza niezależnie na obu osiach, sprawdzając kolizje ścian."""
        half_fw = cfg.HITBOX_W // 2

        search_box = pygame.Rect(int(self.x) - 48, int(self.y) - 48, 96, 96)
        nearby = [r for r in collision_rects if search_box.colliderect(r)]

        self.x += dx
        self.x = max(float(half_fw), min(self.x, float(map_w - half_fw)))
        if dx != 0.0:
            hitbox = self.get_hitbox_rect()
            for rect in nearby:
                if hitbox.colliderect(rect):
                    self.x = (
                        float(rect.left - half_fw)
                        if dx > 0
                        else float(rect.right + half_fw)
                    )
                    hitbox = self.get_hitbox_rect()

        self.y += dy
        self.y = max(float(cfg.PLAYER_H), min(self.y, float(map_h)))
        if dy != 0.0:
            hitbox = self.get_hitbox_rect()
            for rect in nearby:
                if hitbox.colliderect(rect):
                    self.y = (
                        float(rect.top) if dy > 0 else float(rect.bottom + cfg.HITBOX_H)
                    )
                    hitbox = self.get_hitbox_rect()
