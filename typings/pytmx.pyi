from collections.abc import Iterator

import pygame

class TiledElement:
    name: str
    properties: dict[str, object]

class TiledLayer(TiledElement):
    visible: bool
    opacity: float
    id: int

class TiledTileLayer(TiledLayer):
    data: list[list[int]]
    def iter_data(self) -> Iterator[tuple[int, int, int]]: ...
    def __iter__(self) -> Iterator[tuple[int, int, int]]: ...

class TiledObject(TiledElement):
    type: str | None
    x: float
    y: float
    width: float
    height: float
    rotation: float
    gid: int
    visible: bool

class TiledObjectGroup(TiledLayer):
    def __iter__(self) -> Iterator[TiledObject]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> TiledObject: ...

class TiledImageLayer(TiledLayer):
    source: str | None

class TiledMap:
    width: int
    height: int
    tilewidth: int
    tileheight: int
    layers: list[TiledTileLayer | TiledObjectGroup | TiledImageLayer | TiledLayer]
    properties: dict[str, object]
    images: list[pygame.Surface | None]

    def __init__(self, filename: str | None = ...) -> None: ...
    def get_tile_image(self, x: int, y: int, layer: int) -> pygame.Surface: ...
    def get_tile_properties(
        self, x: int, y: int, layer: int
    ) -> dict[str, object] | None: ...
    def get_tile_image_by_gid(self, gid: int) -> pygame.Surface: ...

def load_pygame(
    filename: str, pixelalpha: bool = ..., *args: object, **kwargs: object
) -> TiledMap: ...
