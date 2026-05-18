from __future__ import annotations

import pygame
import pytmx

from config.paths import ASSETS_DIR
from config.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from core.interfaces import IStateManager
from states.base import BaseState

# ── Konfiguracja ──────────────────────────────────────────────────────────────

ZOOM = 4
TILE_SIZE = 16  # rozmiar kafla (1×)
PLAYER_SPEED = 50  # prędkość [px/s, 1×]

# Sprite gracza jest 32×32 w przestrzeni 1×
PLAYER_W = 32
PLAYER_H = 32

# Hitbox stóp (dolna środkowa część sprite'a, 1×)
FEET_W = PLAYER_W
FEET_H = 6

# Animacja chodzenia
WALK_FRAME_DURATION = 0.18  # sekund na klatkę chodu

# Widoczny obszar (1×)
VIEW_W = SCREEN_WIDTH // ZOOM  # 320
VIEW_H = SCREEN_HEIGHT // ZOOM  # 180

MAP_PATH = ASSETS_DIR / "map" / "mapa.tmx"
PLAYER_DIR = ASSETS_DIR / "images" / "entities" / "player"

# ─────────────────────────────────────────────────────────────────────────────


class Player:
    """Pozycja gracza w przestrzeni świata (1×)."""

    def __init__(self, x: float, y: float) -> None:
        self.x: float = x  # środek poziomy
        self.y: float = y  # dolna krawędź sprite'a

    def get_feet_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - FEET_W // 2,
            int(self.y) - FEET_H,
            FEET_W,
            FEET_H,
        )

    def get_sprite_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - PLAYER_W // 2,
            int(self.y) - PLAYER_H,
            PLAYER_W,
            PLAYER_H,
        )


# ─────────────────────────────────────────────────────────────────────────────


class GameState(BaseState):
    """
    Stan rozgrywki.

    Renderowanie:
      1. Podłoga                   – pre-renderowana, zawsze pierwsza
      2. Kafle kolizyjne + gracz   – Y-sortowane razem:
             sort_y kafla  = zone.y + zone.height // 2  (środek strefy „Kolizje")
             sort_y gracza = player.y (stopy)
      3. Ściany / drzwi            – pre-renderowane, zawsze ostatnie

    Kolizje:
      • statyczne  : pełny prostokąt kafla
      • kolizja    : cienki pasek COLLISION_THICKNESS na górnej krawędzi
                     każdego obiektu z warstwy „Kolizje"

    Animacja gracza:
      • stój  : klatka "standing"
      • chód  : naprzemiennie "left_leg_up" / "right_leg_up" co WALK_FRAME_DURATION
      • lewa  : sprite odbity poziomo
    """

    def __init__(self, manager: IStateManager) -> None:
        super().__init__(manager)
        self.player: Player | None = None
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0

        # Pre-renderowane powierzchnie (nie wymagają sortowania)
        self.floor_surface: pygame.Surface | None = None
        self.static_surface: pygame.Surface | None = None

        # Kafle kolizyjne do Y-sortowania: (image, world_x, world_y, sort_y)
        self.kolizja_tiles: list[tuple[pygame.Surface, int, int, int]] = []

        self.collision_rects: list[pygame.Rect] = []

        # Cache przeskalowanych kafli
        self._tile_cache: dict[int, pygame.Surface] = {}

        self.map_pixel_w: int = 0
        self.map_pixel_h: int = 0

        # ── Animacja gracza ───────────────────────────────────────────────────
        # _sprites[facing_right (0=lewo, 1=prawo)][frame_idx]
        # frame_idx: 0 = stój, 1 = lewa noga, 2 = prawa noga
        self._sprites: list[list[pygame.Surface]] = []
        self._anim_timer: float = 0.0
        self._anim_frame: int = 0  # 0 lub 1 – indeks w cyklu chodu [left, right]
        self._facing_right: bool = True
        self._is_moving: bool = False

    # ── Wejście / wyjście ─────────────────────────────────────────────────────

    def enter(self) -> None:
        self._tile_cache.clear()
        self._load_sprites()
        self._load_map()
        self.player = Player(480.0, 300.0)
        self._update_camera()

    def exit(self) -> None:
        pass

    # ── Ładowanie sprite'ów gracza ────────────────────────────────────────────

    def _load_sprites(self) -> None:
        """
        Ładuje 3 klatki (standing, left_leg_up, right_leg_up) i pre-skaluje ×ZOOM.
        Przechowuje też wersje odbite dla ruchu w lewo.

        self._sprites[dir][frame]:
            dir   0 = lewo, 1 = prawo
            frame 0 = stój, 1 = left_leg_up, 2 = right_leg_up
        """
        target = (PLAYER_W * ZOOM, PLAYER_H * ZOOM)  # 128 × 128 px na ekranie

        def load(name: str) -> pygame.Surface:
            raw = pygame.image.load(str(PLAYER_DIR / name)).convert_alpha()
            return pygame.transform.scale(raw, target)

        standing = load("standing.png")
        left_leg = load("left_leg_up.png")
        right_leg = load("right_leg_up.png")

        def flip(s: pygame.Surface) -> pygame.Surface:
            return pygame.transform.flip(s, True, False)

        # [lewo, prawo]  ×  [stój, left_leg, right_leg]
        # Oryginał patrzy w lewo (wózek idzie w lewo) → flip = prawo
        self._sprites = [
            [standing, left_leg, right_leg],  # dir=0 (lewo)
            [flip(standing), flip(left_leg), flip(right_leg)],  # dir=1 (prawo)
        ]

    # ── Cache przeskalowanych kafli mapy ──────────────────────────────────────

    def _scaled(self, img: pygame.Surface) -> pygame.Surface:
        key = id(img)
        if key not in self._tile_cache:
            self._tile_cache[key] = pygame.transform.scale(
                img, (TILE_SIZE * ZOOM, TILE_SIZE * ZOOM)
            )
        return self._tile_cache[key]

    # ── Ładowanie mapy ────────────────────────────────────────────────────────

    def _load_map(self) -> None:
        tmap: pytmx.TiledMap = pytmx.load_pygame(str(MAP_PATH), pixelalpha=True)

        self.map_pixel_w = tmap.width * TILE_SIZE
        self.map_pixel_h = tmap.height * TILE_SIZE
        mw, mh = self.map_pixel_w, self.map_pixel_h

        self.floor_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)
        self.static_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)
        self.kolizja_tiles = []
        self.collision_rects = []

        # ── Strefy z warstwy „Kolizje" ────────────────────────────────────────
        kolizje_zones: list[pygame.Rect] = []
        for layer in tmap.layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name == "Kolizje":
                for obj in layer:
                    kolizje_zones.append(
                        pygame.Rect(
                            int(obj.x),
                            int(obj.y),
                            int(obj.width),
                            int(obj.height),
                        )
                    )

        # Cienki pasek kolizji = górna krawędź każdej strefy
        for zone in kolizje_zones:
            self.collision_rects.append(
                pygame.Rect(zone.x, zone.y, zone.width, zone.height)
            )

        # ── Warstwy kaflowe ───────────────────────────────────────────────────
        for layer in tmap.layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue

            props = layer.properties
            is_static = bool(props.get("statyczne", False))
            has_col = bool(props.get("kolizja", False))

            for x, y, gid in layer:
                if gid == 0:
                    continue
                img = tmap.get_tile_image_by_gid(gid)
                if img is None:
                    continue

                px = x * TILE_SIZE
                py = y * TILE_SIZE
                tile_rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)

                if not has_col and not is_static:
                    self.floor_surface.blit(img, (px, py))

                elif is_static:
                    self.collision_rects.append(tile_rect.copy())
                    self.static_surface.blit(img, (px, py))

                else:
                    sort_y = self._find_sort_y(tile_rect, kolizje_zones)
                    self.kolizja_tiles.append((img, px, py, sort_y))

    def _find_sort_y(
        self,
        tile_rect: pygame.Rect,
        zones: list[pygame.Rect],
    ) -> int:
        """
        Wyznacza klucz Y-sortowania dla kafla.

        Używa środka strefy kolizji (zone.y + zone.height // 2) zamiast samego
        zone.y – dzięki temu strefa, w której gracz jest wizualnie „przed" szafką,
        jest o połowę mniejsza.
        """
        candidates = [
            z for z in zones if z.left < tile_rect.right and z.right > tile_rect.left
        ]
        if candidates:
            cy = tile_rect.centery
            zone = min(candidates, key=lambda z: abs(z.y - cy))
            # Środek strefy – kompromis między górą a dołem kolizji
            return zone.y + zone.height // 2
        return tile_rect.bottom

    # ── Kamera ───────────────────────────────────────────────────────────────

    def _update_camera(self) -> None:
        if self.player is None:
            return
        self.camera_x = max(
            0.0,
            min(self.player.x - VIEW_W / 2.0, float(self.map_pixel_w - VIEW_W)),
        )
        self.camera_y = max(
            0.0,
            min(self.player.y - VIEW_H / 2.0, float(self.map_pixel_h - VIEW_H)),
        )

    # ── Obsługa zdarzeń ───────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.change_state("MENU")

    # ── Aktualizacja ─────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self.player is None:
            return

        keys = pygame.key.get_pressed()
        dx = dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        # Normalizacja ukośna
        if dx != 0.0 and dy != 0.0:
            dx *= 0.7071067811865476
            dy *= 0.7071067811865476

        # ── Kierunek i animacja ───────────────────────────────────────────────
        self._is_moving = dx != 0.0 or dy != 0.0

        if dx > 0.0:
            self._facing_right = True
        elif dx < 0.0:
            self._facing_right = False

        if self._is_moving:
            self._anim_timer += dt
            if self._anim_timer >= WALK_FRAME_DURATION:
                self._anim_timer -= WALK_FRAME_DURATION
                self._anim_frame = 1 - self._anim_frame  # przełącz 0 ↔ 1
        else:
            self._anim_timer = 0.0
            self._anim_frame = 0

        self._move_player(dx * PLAYER_SPEED * dt, dy * PLAYER_SPEED * dt)
        self._update_camera()

    # ── Ruch i kolizje ────────────────────────────────────────────────────────

    def _move_player(self, dx: float, dy: float) -> None:
        if self.player is None:
            return
        p: Player = self.player
        half_fw = FEET_W // 2  # = 8 px

        search = pygame.Rect(int(p.x) - 48, int(p.y) - 48, 96, 96)
        nearby = [r for r in self.collision_rects if search.colliderect(r)]

        # X
        p.x += dx
        p.x = max(float(half_fw), min(p.x, float(self.map_pixel_w - half_fw)))
        if dx != 0.0:
            feet = p.get_feet_rect()
            for rect in nearby:
                if not feet.colliderect(rect):
                    continue
                p.x = (
                    float(rect.left - half_fw)
                    if dx > 0
                    else float(rect.right + half_fw)
                )
                feet = p.get_feet_rect()

        # Y
        p.y += dy
        p.y = max(float(PLAYER_H), min(p.y, float(self.map_pixel_h)))
        if dy != 0.0:
            feet = p.get_feet_rect()
            for rect in nearby:
                if not feet.colliderect(rect):
                    continue
                p.y = float(rect.top) if dy > 0 else float(rect.bottom + FEET_H)
                feet = p.get_feet_rect()

    # ── Rysowanie ─────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((15, 15, 15))

        if (
            self.player is None
            or self.floor_surface is None
            or self.static_surface is None
            or not self._sprites
        ):
            return

        src_x = max(0, min(int(self.camera_x), self.map_pixel_w - VIEW_W))
        src_y = max(0, min(int(self.camera_y), self.map_pixel_h - VIEW_H))
        src_rect = pygame.Rect(src_x, src_y, VIEW_W, VIEW_H)

        # ── 1. Podłoga ───────────────────────────────────────────────────────
        portion = self.floor_surface.subsurface(src_rect)
        screen.blit(
            pygame.transform.scale(portion, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0)
        )

        # ── 2. Y-sortowanie: kafle kolizyjne + gracz ──────────────────────────
        # (sort_y, secondary, world_x, world_y, image_or_None)
        # secondary: 0=kafel, 1=gracz → przy remisie kafel pierwszy, gracz na wierzchu
        view_rect = pygame.Rect(src_x, src_y, VIEW_W + TILE_SIZE, VIEW_H + TILE_SIZE)

        drawables: list[tuple[int, int, int, int, pygame.Surface | None]] = []

        for img, wpx, wpy, sort_y in self.kolizja_tiles:
            if view_rect.colliderect(pygame.Rect(wpx, wpy, TILE_SIZE, TILE_SIZE)):
                drawables.append((sort_y, 0, wpx, wpy, img))

        p = self.player
        drawables.append((int(p.y), 1, int(p.x), int(p.y), None))

        drawables.sort(key=lambda d: (d[0], d[1]))

        # Wyznacz klatkę gracza raz przed pętlą
        dir_idx = 1 if self._facing_right else 0
        if self._is_moving:
            # klatki chodu: frame_idx 1 i 2
            walk_frame_idx = self._anim_frame + 1  # 1 = left_leg, 2 = right_leg
            player_surf = self._sprites[dir_idx][walk_frame_idx]
        else:
            player_surf = self._sprites[dir_idx][0]  # 0 = stój

        for _sort_y, secondary, wx, wy, img in drawables:
            if img is None:
                # ── Gracz ────────────────────────────────────────────────────
                sx = (wx - PLAYER_W // 2 - src_x) * ZOOM
                sy = (wy - PLAYER_H - src_y) * ZOOM
                screen.blit(player_surf, (sx, sy))
            else:
                # ── Kafel ────────────────────────────────────────────────────
                sx = (wx - src_x) * ZOOM
                sy = (wy - src_y) * ZOOM
                screen.blit(self._scaled(img), (sx, sy))

        # ── 3. Ściany i drzwi (zawsze na wierzchu) ───────────────────────────
        portion = self.static_surface.subsurface(src_rect)
        screen.blit(
            pygame.transform.scale(portion, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0)
        )
