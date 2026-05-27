from __future__ import annotations

import heapq
import math
from typing import List, Tuple, Optional

import pygame

import config.settings as cfg

Tile = Tuple[int, int]
Grid = List[List[bool]]  # True = walkable


def build_grid(map_manager, polygon: List[Tuple[float, float]]) -> Tuple[Grid, int, int]:
    """
    Build a walkable grid for the whole map, but mark tiles outside polygon or inside collision rects as False.
    Returns (grid, width_tiles, height_tiles)
    """
    tile_w = map_manager.pixel_w // cfg.TILE_SIZE
    tile_h = map_manager.pixel_h // cfg.TILE_SIZE
    grid: Grid = [[False for _ in range(tile_h)] for _ in range(tile_w)]

    def world_center(t: Tile) -> Tuple[float, float]:
        tx, ty = t
        return (tx * cfg.TILE_SIZE + cfg.TILE_SIZE / 2, ty * cfg.TILE_SIZE + cfg.TILE_SIZE / 2)

    for tx in range(tile_w):
        for ty in range(tile_h):
            wx, wy = world_center((tx, ty))
            # inside polygon?
            if not _point_in_polygon(wx, wy, polygon):
                continue
            # not inside any collision rect
            blocked = False
            for rect in map_manager.collision_rects:
                if rect.collidepoint(wx, wy):
                    blocked = True
                    break
            if blocked:
                continue
            grid[tx][ty] = True

    return grid, tile_w, tile_h


def _point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def astar(grid: Grid, start: Tile, goal: Tile, allow_diagonal: bool = True) -> Optional[List[Tile]]:
    w = len(grid)
    h = len(grid[0]) if w else 0
    def neighbors(t: Tile):
        x, y = t
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if allow_diagonal:
            deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[nx][ny]:
                # prevent cutting corners: for diagonal ensure adjacent sides free
                if abs(dx) + abs(dy) == 2:
                    if not (grid[x+dx][y] and grid[x][y+dy]):
                        continue
                yield (nx, ny)

    def heuristic(a: Tile, b: Tile) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    open_set = []
    heapq.heappush(open_set, (0.0, start))
    came_from = {start: None}
    gscore = {start: 0.0}
    fscore = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            # reconstruct
            path = []
            cur = current
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path

        for nb in neighbors(current):
            tentative_g = gscore[current] + heuristic(current, nb)
            if tentative_g < gscore.get(nb, float('inf')):
                came_from[nb] = current
                gscore[nb] = tentative_g
                f = tentative_g + heuristic(nb, goal)
                if nb not in fscore or f < fscore[nb]:
                    fscore[nb] = f
                    heapq.heappush(open_set, (f, nb))

    return None


def tile_to_world(tile: Tile) -> Tuple[float, float]:
    tx, ty = tile
    return (tx * cfg.TILE_SIZE + cfg.TILE_SIZE / 2, ty * cfg.TILE_SIZE + cfg.TILE_SIZE / 2)
