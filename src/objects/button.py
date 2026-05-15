import pygame


class Button:
    def __init__(self, x: int, y: int, image: pygame.Surface):
        self.image: pygame.Surface = image
        self.rect: pygame.Rect = self.image.get_bounding_rect()
        self.rect.topleft = (x, y)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Sprawdza, czy ten konkretny przycisk został kliknięty."""

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # pyright: ignore[reportAny]
                return self.rect.collidepoint(event.pos)  # pyright: ignore[reportAny]
        return False

    def is_hovered(self, event: pygame.event.Event) -> bool:
        """Sprawdza, czy ten konkretny przycisk został najechany przez myszkę."""

        if not self.is_clicked(event) and event.type == pygame.MOUSEMOTION:
            return self.rect.collidepoint(event.pos)  # pyright: ignore[reportAny]
        return False
