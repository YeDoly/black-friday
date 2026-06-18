from __future__ import annotations

from pathlib import Path

import pygame

from config.paths import ASSETS_DIR, FONTS_DIR, IMAGES_DIR, MUSIC_DIR
from utils.assets_loader import load_images_from_folder


class MusicContainer:
    """Sub-menedżer odpowiedzialny wyłącznie za zasoby muzyczne."""

    def __init__(self) -> None:
        self._storage: dict[str, Path] = {}

    def play(self, key: str, loops: int = -1) -> None:
        """Odtwarza muzykę z podanym kluczem."""
        if key in self._storage:
            try:
                pygame.mixer.music.load(str(self._storage[key]))
                pygame.mixer.music.play(loops=loops)
            except pygame.error:
                print(f"[BŁĄD] Nie udało się odtworzyć pliku muzyki: {key}")
        else:
            print(f"[OSTRZEŻENIE] Brak assetu muzycznego o kluczu: {key}")

    def pause(self) -> None:
        """Wstrzymuje odtwarzanie muzyki."""
        pygame.mixer.music.pause()

    def volume(self, level: float) -> None:
        """Ustawia głośność odtwarzania muzyki (0.0 - 1.0)."""
        if 0.0 <= level <= 1.0:
            pygame.mixer.music.set_volume(level)
        else:
            print(f"[OSTRZEŻENIE] Nieprawidłowy poziom głośności: {level}")

    def load(self, directory: Path) -> None:
        """Indeksuje ścieżki do plików muzycznych w folderze."""
        if directory.exists():
            for ext in ("*.mp3", "*.ogg", "*.wav"):
                for music_file in directory.rglob(ext):
                    print(music_file.stem)
                    self._storage[music_file.stem] = music_file
            print(
                f"[ASSET MANAGER] Znaleziono łącznie {len(self._storage)} wariantów muzyki."
            )
        else:
            print(f"[BŁĄD] Nie znaleziono folderu z muzyką: {directory}")

    def get(self, key: str) -> Path | None:
        """Zwraca ścieżkę do pliku muzycznego po kluczu."""
        if key in self._storage:
            return self._storage[key]

        print(f"[OSTRZEŻENIE] Brak assetu muzycznego o kluczu: {key}")
        return None


class ImageContainer:
    """Sub-menedżer odpowiedzialny wyłącznie za zasoby graficzne."""

    def __init__(self) -> None:
        self._storage: dict[str, pygame.Surface] = {}

    def load(self, directory: Path) -> None:
        """Wczytuje obrazy z podanego folderu."""
        if directory.exists():
            self._storage = load_images_from_folder(directory)
            print(f"[ASSET MANAGER] Załadowano łącznie {len(self._storage)} obrazów.")
        else:
            print(f"[BŁĄD] Nie znaleziono folderu z obrazami: {directory}")

    def get(self, key: str) -> pygame.Surface:
        """Zwraca obrazek po kluczu. W przypadku braku – zwraca magenta fallback."""
        if key in self._storage:
            return self._storage[key]

        print(f"[OSTRZEŻENIE] Brak assetu graficznego o kluczu: {key}")
        fallback = pygame.Surface((32, 32))
        fallback.fill((255, 0, 255))
        return fallback

    def get_keys_by_prefix(self, prefix: str) -> list[str]:
        """Zwraca listę wszystkich zarejestrowanych kluczy zaczynających się od podanego prefiksu."""
        return [key for key in self._storage if key.startswith(prefix)]


class FontContainer:
    """Sub-menedżer odpowiedzialny wyłącznie za czcionki i ich keszowanie."""

    def __init__(self) -> None:
        self._paths: dict[str, Path] = {}
        self._cache: dict[tuple[str, int], pygame.font.Font] = {}

    def load(self, directory: Path) -> None:
        """Indeksuje ścieżki do plików czcionek w folderze."""
        if directory.exists():
            for ext in ("*.ttf", "*.otf"):
                for font_file in directory.rglob(ext):
                    self._paths[font_file.stem] = font_file
            print(
                f"[ASSET MANAGER] Znaleziono łącznie {len(self._paths)} wariantów czcionek."
            )
        else:
            print(f"[BŁĄD] Nie znaleziono folderu z czcionkami: {directory}")

    def get(self, key: str, size: int) -> pygame.font.Font:
        """Zwraca czcionkę o wybranym rozmiarze, korzystając z cache."""
        cache_key = (key, size)

        if cache_key in self._cache:
            return self._cache[cache_key]

        if key in self._paths:
            try:
                font = pygame.font.Font(str(self._paths[key]), size)
                self._cache[cache_key] = font
                return font
            except pygame.error:
                print(f"[BŁĄD] Nie udało się zainicjalizować pliku czcionki: {key}")

        print(f"[OSTRZEŻENIE] Brak czcionki o kluczu: {key}. Zwracam systemową.")
        fallback_font = pygame.font.SysFont(None, size)
        self._cache[cache_key] = fallback_font
        return fallback_font


class AssetsManager:
    """Główny punkt zarządzania wszystkimi zasobami w grze."""

    def __init__(self, root_path: Path = ASSETS_DIR) -> None:
        self.root_path: Path = Path(root_path)

        self.images: ImageContainer = ImageContainer()
        self.fonts: FontContainer = FontContainer()
        self.music: MusicContainer = MusicContainer()

    def load_all(self) -> None:
        """Inicjalizuje ładowanie wszystkich sub-kontenerów."""
        self.images.load(IMAGES_DIR)
        self.fonts.load(FONTS_DIR)
        self.music.load(MUSIC_DIR)
