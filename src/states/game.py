from __future__ import annotations

import math
import random
from typing import cast, override

import pygame

import config.settings as cfg
from core.camera import Camera
from core.interfaces import IStateManager
from objects.cashier import Cashier
from objects.customer import Customer
from objects.player import Player
from states.base import BaseState
from systems.shopping_list import Product, ShoppingListManager
from systems.timer import Timer


class GameState(BaseState):
    def __init__(self, manager: IStateManager) -> None:
        super().__init__(manager)
        self.camera: Camera = Camera()
        self.player: Player | None = None
        self.customers: list[Customer] = []
        self.cashiers: list[Cashier] = []
        self.timer: Timer | None = None
        self.shopping_list: ShoppingListManager | None = None

        self.is_won: bool = False
        self.win_time_start: int = 0

    @override
    def enter(self) -> None:
        self.is_won = False
        self.manager.map.load_map(str(cfg.MAP_PATH))

        self.player = Player(
            self.manager.map.pixel_w / 2,
            self.manager.map.pixel_h - cfg.TILE_SIZE * 2,
        )
        self._sync_camera()

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

        self.shopping_list = ShoppingListManager(pula_produktow, items_to_choose=6)

        self._spawn_customers(count=50)
        self._spawn_cashiers()
        self._spawn_products()

        self.timer = Timer()

    def _spawn_cashiers(self) -> None:
        points = self.manager.map.cashier_zones

        if not points:
            print(
                "Ostrzeżenie: Nie znaleziono punktów dla kasjerów na mapie (warstwa 'Kasjerzy')!"
            )
            return

        for index, (px, py) in enumerate(points):
            c_type = index + 1
            cashier = Cashier(cashier_type=c_type, x=px, y=py)
            self.cashiers.append(cashier)

    def _spawn_customers(self, count: int) -> None:
        zones = self.manager.map.customer_zones

        if not zones:
            print(
                "Ostrzeżenie: Nie znaleziono stref dla klientów na mapie (warstwa 'Klienci')!"
            )
            return

        available_types = [1, 2, 3, 4, 5]

        for _ in range(count):
            polygon = random.choice(zones)
            c_type = random.choice(available_types)

            customer = Customer(c_type, polygon)
            self.customers.append(customer)

    def _spawn_products(self) -> None:
        zones = self.manager.map.product_zones
        targets = self.shopping_list.target_products
        all_prods = self.shopping_list.all_products

        if len(targets) > len(zones):
            raise ValueError(
                "Za mało stref, aby pomieścić wszystkie docelowe produkty!"
            )

        garbage_products = [p for p in all_prods if p not in targets]
        empty_zones_count = len(zones) - len(targets)

        available_garbage_count = min(empty_zones_count, len(garbage_products))
        chosen_garbage = random.sample(garbage_products, available_garbage_count)

        products_to_spawn = targets + chosen_garbage
        random.shuffle(products_to_spawn)

        new_product_zones: list[tuple[Product | None, pygame.Rect]] = []

        for zone, product in zip(zones, products_to_spawn):
            _, rect = zone
            new_product_zones.append((product, rect))

        if len(products_to_spawn) < len(zones):
            leftover_zones = zones[len(products_to_spawn) :]
            new_product_zones.extend(leftover_zones)

        self.manager.map.product_zones = new_product_zones

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
        if self.is_won:
            return

        for event in events:
            if event.type == pygame.KEYDOWN and cast(int, event.key) == pygame.K_ESCAPE:
                self.manager.change_state("MENU")
            if (
                self.shopping_list
                and event.type == pygame.KEYDOWN
                and cast(int, event.key) == pygame.K_e
            ):
                for product, zone in self.manager.map.product_zones:
                    if self.player and self.player.get_hitbox_rect().colliderect(zone):
                        if product:
                            self.shopping_list.collect_item(product)

                for zone in self.manager.map.buy_zones:
                    if self.player and self.player.get_hitbox_rect().colliderect(zone):
                        if self.shopping_list.is_list_complete() and not self.is_won:
                            if self.timer:
                                self.timer.save_best_time()
                            self.is_won = True
                            self.win_time_start = pygame.time.get_ticks()

    @override
    def update(self, dt: float) -> None:
        if self.is_won:
            time_elapsed = pygame.time.get_ticks() - self.win_time_start
            if time_elapsed >= 5000:
                self.manager.change_state("MENU")
            return

        if not self.player:
            return

        cashier_hitboxes = [c.get_hitbox_rect() for c in self.cashiers]
        customer_hitboxes = [c.get_hitbox_rect() for c in self.customers]

        all_collisions = (
            self.manager.map.collision_rects + customer_hitboxes + cashier_hitboxes
        )

        self.player.handle_input(
            dt,
            all_collisions,
            self.manager.map.pixel_w,
            self.manager.map.pixel_h,
        )

        player_hitbox = self.player.get_hitbox_rect()

        for customer in self.customers:
            customer.update(dt, player_hitbox)

        self._sync_camera()

        if self.timer:
            self.timer.update()

    def _draw_win_screen(self, screen: pygame.Surface) -> None:
        """Rysuje nakładkę ekranu końcowego nad resztą gry."""
        time_elapsed = pygame.time.get_ticks() - self.win_time_start
        time_left_sec = math.ceil((5000 - time_elapsed) / 1000)

        overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        font_title = self.manager.assets.fonts.get("Poppins-Bold", 60)
        font_sub = self.manager.assets.fonts.get("Poppins-Regular", 30)

        win_text = font_title.render("Wygrałeś!", True, (100, 255, 100))
        win_rect = win_text.get_rect(
            center=(cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2 - 40)
        )
        screen.blit(win_text, win_rect)

        sub_text = font_sub.render(
            f"Powrót do menu za: {time_left_sec}s", True, (200, 200, 200)
        )
        sub_rect = sub_text.get_rect(
            center=(cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2 + 40)
        )
        screen.blit(sub_text, sub_rect)

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

        drawables: list[
            tuple[int, int, int, int, pygame.Surface | Player | Customer | Cashier]
        ] = []

        for img, wpx, wpy, sort_y in self.manager.map.kolizja_tiles:
            if view_rect.colliderect(
                pygame.Rect(wpx, wpy, cfg.TILE_SIZE, cfg.TILE_SIZE)
            ):
                drawables.append((sort_y, 0, wpx, wpy, img))

        drawables.append(
            (int(self.player.y), 1, int(self.player.x), int(self.player.y), self.player)
        )

        for customer in self.customers:
            if view_rect.collidepoint(customer.x, customer.y):
                drawables.append(
                    (int(customer.y), 1, int(customer.x), int(customer.y), customer)
                )

        for cashier in self.cashiers:
            if view_rect.collidepoint(cashier.x, cashier.y):
                drawables.append(
                    (int(cashier.y), 1, int(cashier.x), int(cashier.y), cashier)
                )

        drawables.sort(key=lambda d: (d[0], d[1]))

        for _, _, wx, wy, obj in drawables:
            if isinstance(obj, (Player, Customer, Cashier)):
                sx = (wx - cfg.PLAYER_W // 2 - cam_x) * cfg.ZOOM
                sy = (wy - cfg.PLAYER_H - cam_y) * cfg.ZOOM
                screen.blit(obj.get_current_sprite(), (sx, sy))
            else:
                sx = (wx - cam_x) * cfg.ZOOM
                sy = (wy - cam_y) * cfg.ZOOM
                screen.blit(self.manager.map.get_scaled_tile(obj), (sx, sy))

        static_portion = self.manager.map.static_surface.subsurface(src_rect)
        screen.blit(
            pygame.transform.scale(
                static_portion, (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
            ),
            (0, 0),
        )

        if self.shopping_list:
            self.shopping_list.draw_ui(
                screen, self.manager.assets.fonts.get("Poppins-Regular", 20)
            )

        if self.timer:
            self.timer.draw_ui(
                screen, self.manager.assets.fonts.get("Poppins-Bold", 20)
            )

        if self.is_won:
            self._draw_win_screen(screen)
