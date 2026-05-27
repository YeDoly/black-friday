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
        collision_rects: list[pygame.Rect] | None = None,
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

        # Granice dla szybkiego losowania punktów wewnątrz poligonu
        self.min_x = min(p[0] for p in polygon)
        self.max_x = max(p[0] for p in polygon)
        self.min_y = min(p[1] for p in polygon)
        self.max_y = max(p[1] for p in polygon)

        # Lista prostokątów kolizji (z MapManagera) - może być None
        self.collision_rects: list[pygame.Rect] = collision_rects or []

        self._load_sprites()

        # Timer when klient jest 'utknięty' i próbuje wydostać się ze krawędzi
        self.stuck_timer: float = 0.0
        # Precompute centroid to allow cofanie się do wnętrza strefy
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        self._centroid = (cx, cy)

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
            # Musi być wewnątrz wieloboku i nie leżeć w obszarze kolizji
            if self._is_point_in_polygon(tx, ty):
                if not any(rect.collidepoint(tx, ty) for rect in self.collision_rects):
                    self.target_x = tx
                    self.target_y = ty
                    return

        # Jeśli nie uda się wylosować (np. strefa jest mała), klient stoi w miejscu
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

        step = self.speed * dt
        if step <= 0:
            return

        # Helper sprawdzający, czy punkt jest dopuszczalny (wewnątrz poligonu i bez kolizji)
        def point_blocked(nx: float, ny: float) -> bool:
            if not self._is_point_in_polygon(nx, ny):
                return True
            for rect in self.collision_rects:
                if rect.collidepoint(nx, ny):
                    return True
            return False

        # Jeśli jesteśmy w stanie 'utknięcia', najpierw spróbuj przemieścić się w stronę centroidu
        if self.stuck_timer > 0.0:
            self.stuck_timer -= dt
            cx, cy = self._centroid
            ddx = cx - self.x
            ddy = cy - self.y
            distc = math.hypot(ddx, ddy)
            if distc > 1.0:
                rx = ddx / distc
                ry = ddy / distc
                nx = self.x + rx * step
                ny = self.y + ry * step
                if not point_blocked(nx, ny):
                    self._facing_right = rx > 0
                    self.x = nx
                    self.y = ny
                    return
            # jeśli nie udało się cofnąć - kontynuuj do wyboru nowego celu dalej poniżej

        # Próba bezpośredniego kroku w stronę celu
        next_x = self.x + dir_x * step
        next_y = self.y + dir_y * step
        if not point_blocked(next_x, next_y):
            self._facing_right = dir_x > 0
            self.x = next_x
            self.y = next_y
            return

        # Jeśli bezpośrednia ścieżka jest zablokowana, spróbuj wykonać małe odchylenia
        # wokół kierunku ruchu (lokalne omijanie) — proste podejście do pathfindingu.
        offsets = [15, -15, 30, -30, 45, -45, 60, -60, 90, -90, 120, -120, 150, -150, 180]
        for deg in offsets:
            theta = math.radians(deg)
            rx = dir_x * math.cos(theta) - dir_y * math.sin(theta)
            ry = dir_x * math.sin(theta) + dir_y * math.cos(theta)
            nx = self.x + rx * step
            ny = self.y + ry * step
            if not point_blocked(nx, ny):
                self._facing_right = rx > 0
                self.x = nx
                self.y = ny
                return

        # Jeśli nic nie działa (np. klient utknął), ustaw timer 'utknięcia' i spróbuj cofnąć się do wnętrza
        self.stuck_timer = 0.6  # sekundy podczas których będzie próbował cofnąć się do centroidu
        # Dodatkowo wybierz cel dalej wewnątrz (przesunięcie centroidu bliżej środka)
        cx, cy = self._centroid
        # Nowy cel to punkt między obecnym centroidem a środkiem poligonu, bliżej środka
        nx_target = (self.x + cx) / 2.0
        ny_target = (self.y + cy) / 2.0
        if self._is_point_in_polygon(nx_target, ny_target) and not any(r.collidepoint(nx_target, ny_target) for r in self.collision_rects):
            self.target_x = nx_target
            self.target_y = ny_target
        else:
            # fallback - zwykły nowy cel
            self._pick_new_target()
        self.state = "MOVING"
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
