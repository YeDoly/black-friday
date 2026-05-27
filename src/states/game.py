from __future__ import annotations

import random
from typing import cast, override

import pygame

import config.settings as cfg
from core.camera import Camera
from core.interfaces import IStateManager
from objects.customer import Customer
from objects.player import Player
from states.base import BaseState
from systems.shopping_list import Product, ShoppingListManager


class GameState(BaseState):
    def __init__(self, manager: IStateManager) -> None:
        super().__init__(manager)
        self.camera: Camera = Camera()
        self.player: Player | None = None
        self.customers: list[Customer] = []

    @override
    def enter(self) -> None:
        self.manager.map.load_map(str(cfg.MAP_PATH))

        self.player = Player(
            self.manager.map.pixel_w / 2,
            self.manager.map.pixel_h - cfg.TILE_SIZE * 2,
        )
        self._sync_camera()

        # Generowanie Klientów
        self._spawn_customers(count=20)

        food_keys = self.manager.assets.images.get_keys_by_prefix("sprites/food/")
        pula_produktow: list[Product] = []

        for key in food_keys:
            product_id = key.split("/")[-1]
            name = product_id.replace("_", " ").capitalize()

            pula_produktow.append(
                Product(
                    id=product_id, name=name, icon=self.manager.assets.images.get(key)
                )
            )

        self.shopping_list: ShoppingListManager = ShoppingListManager(
            pula_produktow, items_to_choose=6
        )

    def _spawn_customers(self, count: int) -> None:
        """Pobiera gotowe strefy nawigacyjne (wieloboki) z MapManagera i generuje klientów."""
        zones = self.manager.map.customer_zones

        if not zones:
            print(
                "Ostrzeżenie: Nie znaleziono stref dla klientów na mapie (warstwa 'Klienci')!"
            )
            return

        available_types = [1, 2]

        for _ in range(count):
            polygon = random.choice(zones)
            c_type = random.choice(available_types)

            # Używamy tymczasowej instancji aby wylosować poprawny pierwszy cel
            # (zapewnia to, że klient od razu respi się w granicach wieloboku)
            temp_customer = Customer(0, 0, c_type, polygon, self.manager.map.collision_rects)
            temp_customer._pick_new_target()

            customer = Customer(
                temp_customer.target_x,
                temp_customer.target_y,
                c_type,
                polygon,
                self.manager.map.collision_rects,
            )
            self.customers.append(customer)

    def _sync_camera(self) -> None:
        if self.player:
            self.camera.update(
                self.player.x,
                self.player.y,
                self.manager.map.pixel_w,
                self.manager.map.pixel_h,
            )

    @override
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and cast(int, event.key) == pygame.K_ESCAPE:
                self.manager.change_state("MENU")

    @override
    def update(self, dt: float) -> None:
        if not self.player:
            return

        self.player.handle_input(
            dt,
            self.manager.map.collision_rects,
            self.manager.map.pixel_w,
            self.manager.map.pixel_h,
        )

        # Aktualizacja logiki poruszania się dla każdego klienta
        for customer in self.customers:
            customer.update(dt)

        self._sync_camera()

    @override
    def draw(self, screen: pygame.Surface) -> None:
        if (
            not self.player
            or not self.manager.map.floor_surface
            or not self.manager.map.static_surface
        ):
            return

        cam_x, cam_y = int(self.camera.x), int(self.camera.y)
        src_rect = pygame.Rect(cam_x, cam_y, cfg.VIEW_W, cfg.VIEW_H)

        # Rysowanie tła / podłogi
        floor_portion = self.manager.map.floor_surface.subsurface(src_rect)
        screen.blit(
            pygame.transform.scale(
                floor_portion, (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
            ),
            (0, 0),
        )

        view_rect = pygame.Rect(
            cam_x, cam_y, cfg.VIEW_W + cfg.TILE_SIZE, cfg.VIEW_H + cfg.TILE_SIZE
        )

        # Lista elementów do narysowania: (sort_y, priorytet, wx, wy, obiekt)
        drawables: list[
            tuple[int, int, int, int, pygame.Surface | Player | Customer]
        ] = []

        # Płytki (np. regały)
        for img, wpx, wpy, sort_y in self.manager.map.kolizja_tiles:
            if view_rect.colliderect(
                pygame.Rect(wpx, wpy, cfg.TILE_SIZE, cfg.TILE_SIZE)
            ):
                drawables.append((sort_y, 0, wpx, wpy, img))

        # Gracz
        drawables.append(
            (int(self.player.y), 1, int(self.player.x), int(self.player.y), self.player)
        )

        # Klienci (optymalizacja - rysujemy tylko tych, co są w kamerze)
        for customer in self.customers:
            if view_rect.collidepoint(customer.x, customer.y):
                drawables.append(
                    (int(customer.y), 1, int(customer.x), int(customer.y), customer)
                )

        # Główne sortowanie Y
        drawables.sort(key=lambda d: (d[0], d[1]))

        # Renderowanie
        for _, _, wx, wy, obj in drawables:
            # Duck typing: rozpoznaje gracza i klienta dzięki wspólnej metodzie
            if hasattr(obj, "get_current_sprite"):
                sx = (wx - cfg.PLAYER_W // 2 - cam_x) * cfg.ZOOM
                sy = (wy - cfg.PLAYER_H - cam_y) * cfg.ZOOM
                screen.blit(obj.get_current_sprite(), (sx, sy))
            else:
                sx = (wx - cam_x) * cfg.ZOOM
                sy = (wy - cam_y) * cfg.ZOOM
                screen.blit(self.manager.map.get_scaled_tile(obj), (sx, sy))

        # Obiekty nad głowami
        static_portion = self.manager.map.static_surface.subsurface(src_rect)
        screen.blit(
            pygame.transform.scale(
                static_portion, (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
            ),
            (0, 0),
        )

        # UI
        self.shopping_list.draw_ui(
            screen, self.manager.assets.fonts.get("Poppins-Regular", 20)
        )
