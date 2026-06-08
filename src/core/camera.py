import config.settings as cfg


class Camera:
    def __init__(self) -> None:
        self.x: float = 0.0
        self.y: float = 0.0

    def update(self, target_x: float, target_y: float, map_w: int, map_h: int) -> None:
        self.x = max(0.0, min(target_x - cfg.VIEW_W / 2.0, float(map_w - cfg.VIEW_W)))
        self.y = max(0.0, min(target_y - cfg.VIEW_H / 2.0, float(map_h - cfg.VIEW_H)))
