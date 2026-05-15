from pathlib import Path

import pygame

from config.paths import ASSETS_DIR, IMAGES_DIR
from utils.assets_loader import load_images_from_folder


class AssetsManager:
    def __init__(self, root_path: Path = ASSETS_DIR):
        self.root_path: Path = Path(root_path)
        self.images: dict[str, pygame.Surface] = {}

    def load_all(self):
        """Wczytuje całą strukturę folderu assets/images."""
        images_dir = IMAGES_DIR

        if images_dir.exists():
            self.images = load_images_from_folder(images_dir)
            print(f"[ASSET MANAGER] Załadowano łącznie {len(self.images)} obrazów.")
        else:
            print(f"[BŁĄD] Nie znaleziono folderu: {images_dir}")

    def get_image(self, key: str) -> pygame.Surface:
        """
        Zwraca obrazek po kluczu. Jeśli nie istnieje, rzuca błędem
        lub zwraca pusty Surface.
        """
        if key in self.images:
            return self.images[key]

        print(f"[OSTRZEŻENIE] Brak assetu o kluczu: {key}")
        fallback = pygame.Surface((32, 32))
        fallback.fill((255, 0, 255))

        return fallback
