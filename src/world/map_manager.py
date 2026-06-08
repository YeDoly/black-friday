from __future__ import annotations

import pygame
import pytmx

import config.settings as cfg
from systems.shopping_list import Product


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

        self.customer_zones: list[list[tuple[float, float]]] = []
        self.cashier_zones: list[tuple[float, float]] = []
        self.product_zones: list[tuple[Product | None, pygame.Rect]] = []
        self.buy_zones: list[pygame.Rect] = []

        self.pixel_w: int = 0
        self.pixel_h: int = 0

        self._tile_cache: dict[int, pygame.Surface] = {}

    def load_map(self, map_path: str) -> None:
        """Ładuje mapę z pliku i przygotowuje płaszczyzny renderowania."""
        self._tile_cache.clear()
        self.kolizja_tiles = []
        self.collision_rects = []
        self.customer_zones = []
        self.cashier_zones = []
        self.product_zones = []
        self.buy_zones = []

        tmap: pytmx.TiledMap = pytmx.load_pygame(map_path, pixelalpha=True)

        self.pixel_w = tmap.width * cfg.TILE_SIZE
        self.pixel_h = tmap.height * cfg.TILE_SIZE
        mw, mh = self.pixel_w, self.pixel_h

        self.floor_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)
        self.static_surface = pygame.Surface((mw, mh), pygame.SRCALPHA)

        for layer in tmap.layers:
            if isinstance(layer, pytmx.TiledObjectGroup):
                if layer.name == "Kolizje":
                    for obj in layer:
                        self.collision_rects.append(
                            pygame.Rect(
                                int(obj.x),
                                int(obj.y),
                                int(obj.width),
                                int(obj.height),
                            )
                        )
                elif layer.name == "Klienci":
                    for obj in layer:
                        pts: list[tuple[float, float]] | None = getattr(
                            obj, "polygon", getattr(obj, "points", None)
                        )

                        if pts:
                            poly: list[tuple[float, float]] = []
                            for p in pts:
                                px = float(p[0])
                                py = float(p[1])
                                poly.append((px, py))

                            self.customer_zones.append(poly)
                        else:
                            poly = [
                                (float(obj.x), float(obj.y)),
                                (float(obj.x + obj.width), float(obj.y)),
                                (float(obj.x + obj.width), float(obj.y + obj.height)),
                                (float(obj.x), float(obj.y + obj.height)),
                            ]
                            self.customer_zones.append(poly)
                elif layer.name == "Kasjerzy":
                    for obj in layer:
                        width = float(getattr(obj, "width", 0))
                        height = float(getattr(obj, "height", 0))

                        self.cashier_zones.append(
                            (float(obj.x + width), float(obj.y + height + 10))
                        )
                elif layer.name == "Produkty":
                    for obj in layer:
                        self.product_zones.append(
                            (
                                None,
                                pygame.Rect(
                                    int(obj.x),
                                    int(obj.y),
                                    int(obj.width),
                                    int(obj.height),
                                ),
                            )
                        )
                elif layer.name == "Zakup":
                    for obj in layer:
                        self.buy_zones.append(
                            pygame.Rect(
                                int(obj.x),
                                int(obj.y),
                                int(obj.width),
                                int(obj.height),
                            )
                        )

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
                    sort_y = self._find_sort_y(tile_rect, self.collision_rects)
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
        """
        candidates = [
            z for z in zones if z.left < tile_rect.right and z.right > tile_rect.left
        ]

        if candidates:
            best_zone = min(candidates, key=lambda z: abs(z.centery - tile_rect.bottom))

            if abs(best_zone.top - tile_rect.bottom) < cfg.TILE_SIZE * 4:
                return best_zone.y + best_zone.height // 2

        return tile_rect.bottom
