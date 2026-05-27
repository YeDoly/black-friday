from __future__ import annotations

import pygame
import pytmx

import config.settings as cfg


class MapManager:
    """
    Klasa odpowiedzialna za ładowanie mapy z Tiled, pre-renderowanie warstw
    oraz zarządzanie danymi kolizji, stref klientów i kafli do Y-sortowania.
    """

    def __init__(self) -> None:
        self.floor_surface: pygame.Surface | None = None
        self.static_surface: pygame.Surface | None = None

        self.kolizja_tiles: list[tuple[pygame.Surface, int, int, int]] = []
        self.collision_rects: list[pygame.Rect] = []

        # Nowa zmienna przechowująca wieloboki stref dla klientów
        self.customer_zones: list[list[tuple[float, float]]] = []

        self.pixel_w: int = 0
        self.pixel_h: int = 0

        # Cache przeskalowanych kafelków (id(img) -> scaled_img)
        self._tile_cache: dict[int, pygame.Surface] = {}

    def load_map(self, map_path: str) -> None:
        """Ładuje mapę z pliku i przygotowuje płaszczyzny renderowania."""
        self._tile_cache.clear()
        self.kolizja_tiles = []
        self.collision_rects = []
        self.customer_zones = []
        # Cache na siatki nawigacyjne per strefa (index -> grid)
        self._nav_grids: list[tuple] = []  # (grid, w, h)

        tmap: pytmx.TiledMap = pytmx.load_pygame(map_path, pixelalpha=True)

        self.pixel_w = tmap.width * cfg.TILE_SIZE
        self.pixel_h = tmap.height * cfg.TILE_SIZE
        mw, mh = self.pixel_w, self.pixel_h

        self.floor_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)
        self.static_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)

        kolizje_zones: list[pygame.Rect] = []

        # Parsowanie warstw obiektowych
        for layer in tmap.layers:
            if isinstance(layer, pytmx.TiledObjectGroup):
                if layer.name == "Kolizje":
                    for obj in layer:
                        kolizje_zones.append(
                            pygame.Rect(
                                int(obj.x),
                                int(obj.y),
                                int(obj.width),
                                int(obj.height),
                            )
                        )
                elif layer.name == "Klienci":
                    for obj in layer:
                        # Jeśli narysowałeś wielobok (Polygon) w Tiled
                        if hasattr(obj, "points"):
                            poly = [
                                (float(obj.x + p.x), float(obj.y + p.y))
                                for p in obj.points
                            ]
                            self.customer_zones.append(poly)
                        # Fallback jeśli narysujesz zwykły prostokąt
                        else:
                            poly = [
                                (float(obj.x), float(obj.y)),
                                (float(obj.x + obj.width), float(obj.y)),
                                (float(obj.x + obj.width), float(obj.y + obj.height)),
                                (float(obj.x), float(obj.y + obj.height)),
                            ]
                            self.customer_zones.append(poly)

        for zone in kolizje_zones:
            self.collision_rects.append(
                pygame.Rect(zone.x, zone.y, zone.width, zone.height)
            )

        # Zbuduj siatki nawigacyjne dla każdej strefy klientów jeśli istnieją
        try:
            from systems.navigation import build_grid

            self._nav_grids = []
            for poly in self.customer_zones:
                grid_info = build_grid(self, poly)
                self._nav_grids.append(grid_info)
        except Exception:
            # W przypadku błędu - zostaw pustą listę, klienci użyją fallbacku
            self._nav_grids = []

        # Parsowanie warstw kafelkowych
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

                px = x * cfg.TILE_SIZE
                py = y * cfg.TILE_SIZE
                tile_rect = pygame.Rect(px, py, cfg.TILE_SIZE, cfg.TILE_SIZE)

                if not has_col and not is_static:
                    self.floor_surface.blit(img, (px, py))

                elif is_static:
                    self.collision_rects.append(tile_rect.copy())
                    self.static_surface.blit(img, (px, py))

                else:
                    sort_y = self._find_sort_y(tile_rect, kolizje_zones)
                    self.kolizja_tiles.append((img, px, py, sort_y))

    def get_scaled_tile(self, img: pygame.Surface) -> pygame.Surface:
        """Zwraca przeskalowany kafel pobrany z pamięci podręcznej."""
        key = id(img)
        if key not in self._tile_cache:
            self._tile_cache[key] = pygame.transform.scale(
                img, (cfg.TILE_SIZE * cfg.ZOOM, cfg.TILE_SIZE * cfg.ZOOM)
            )
        return self._tile_cache[key]

    def _find_sort_y(self, tile_rect: pygame.Rect, zones: list[pygame.Rect]) -> int:
        """
        Wyznacza klucz Y-sortowania dla kafla.
        Szuka najbliższej strefy kolizji w tej samej kolumnie X i synchronizuje
        wszystkie kafelki danego obiektu do wspólnego punktu Y.
        """
        candidates = [
            z for z in zones if z.left < tile_rect.right and z.right > tile_rect.left
        ]

        if candidates:
            best_zone = min(candidates, key=lambda z: abs(z.centery - tile_rect.bottom))

            if abs(best_zone.top - tile_rect.bottom) < cfg.TILE_SIZE * 4:
                return best_zone.y + best_zone.height // 2

        return tile_rect.bottom
