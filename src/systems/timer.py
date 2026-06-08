import os

import pygame


class Timer:
    """Zarządza czasem gry i najlepszym wynikiem."""

    def __init__(self) -> None:
        self.start_ticks: int = pygame.time.get_ticks()
        self.current_time_sec: int = 0

        self.save_dir: str = "score"
        self.filepath: str = os.path.join(self.save_dir, "time.txt")
        self.best_time_sec: float | int = self._load_best_time()

    def _load_best_time(self) -> float | int:
        """Wczytuje najlepszy czas z pliku. Zwraca nieskończoność, jeśli brak pliku."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return int(f.read().strip())
            except ValueError:
                pass  # W przypadku błędu, traktujemy go jak brak wyniku

        return float("inf")

    def save_best_time(self) -> None:
        """Zapisuje obecny czas jako najlepszy, jeśli gra została ukończona szybciej."""
        if self.current_time_sec < self.best_time_sec:
            self.best_time_sec = self.current_time_sec
            os.makedirs(self.save_dir, exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write(str(self.current_time_sec))

    def update(self) -> None:
        """Aktualizuje obecny czas. Powinno być wywoływane w głównej pętli gry."""
        self.current_time_sec = (pygame.time.get_ticks() - self.start_ticks) // 1000

    def _format_time(self, seconds: int | float) -> str:
        """Formatuje czas z sekund na format MM:SS."""
        if seconds == float("inf"):
            return "--:--"
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"

    def draw_ui(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Rysuje licznik i najlepszy czas na ciemnym tle w prawym górnym rogu ekranu."""

        if self.best_time_sec == float("inf"):
            color = (100, 255, 100)
        else:
            time_diff = self.best_time_sec - self.current_time_sec
            if self.current_time_sec > self.best_time_sec:
                color = (255, 100, 100)
            elif time_diff <= 30:
                color = (255, 165, 0)
            else:
                color = (100, 255, 100)

        current_time_str = self._format_time(self.current_time_sec)
        best_time_str = f"Najlepszy: {self._format_time(self.best_time_sec)}"

        current_surf = font.render(current_time_str, True, color)
        best_surf = font.render(best_time_str, True, (150, 150, 150))

        margin_x, margin_y = 20, 20
        padding = 12
        screen_w = screen.get_width()

        max_text_w = max(current_surf.get_width(), best_surf.get_width())
        box_w = max_text_w + padding * 2
        box_h = current_surf.get_height() + best_surf.get_height() + 5 + padding * 2

        box_x = screen_w - margin_x - box_w
        box_y = margin_y

        bg_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, (box_x, box_y))

        current_x = box_x + box_w - padding - current_surf.get_width()
        best_x = box_x + box_w - padding - best_surf.get_width()

        current_y = box_y + padding
        best_y = current_y + current_surf.get_height() + 5

        screen.blit(current_surf, (current_x, current_y))
        screen.blit(best_surf, (best_x, best_y))
