from pathlib import Path

import pygame

from config.paths import IMAGES_DIR


def get_fixed_key(file_path: Path) -> str:
    folder_path = IMAGES_DIR
    rel_path = file_path.relative_to(folder_path).with_suffix("")
    fixed_key = str(rel_path).replace("\\", "/")

    return fixed_key


def load_image(file_path: Path) -> pygame.Surface | None:
    """
    Wczytuje pojedynczy obraz i zwraca pygame Surface.
    """

    try:
        image_surface = pygame.image.load(file_path).convert_alpha()

        print(f"[ZAŁADOWANO] {get_fixed_key(file_path)}")
        return image_surface

    except pygame.error as e:
        print(f"[BŁĄD] Nie udało się wczytać {file_path.name}: {e}")
        return None


def load_images_from_folder(folder_path: Path) -> dict[str, pygame.Surface]:
    """
    Skanuje folder rekurencyjnie.
    Wczytuje znalezione obrazy i zwraca dict[str, pygame.Surface].
    """
    loaded_images: dict[str, pygame.Surface] = {}

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"[UWAGA] Folder nie istnieje: {folder_path}")
        return loaded_images

    for file_path in folder_path.rglob("*.png"):
        image_surface = load_image(file_path)

        if image_surface:
            loaded_images[get_fixed_key(file_path)] = image_surface

    return loaded_images
