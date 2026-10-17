"""Carregamento e ajuste dos recursos visuais do projeto."""

from pathlib import Path
from functools import lru_cache

import pygame


ROOT = Path(__file__).parent
IMAGES = ROOT / "images"
TILESET_PATH = IMAGES / "grass_tileset.png"
BACKGROUND_PATH = IMAGES / "background.png"


@lru_cache(maxsize=1)
def load_tileset():
    return pygame.image.load(TILESET_PATH).convert_alpha()


@lru_cache(maxsize=4)
def load_background(size):
    """Escala o fundo para cobrir a janela e centraliza o recorte."""
    image = pygame.image.load(BACKGROUND_PATH).convert()
    scale = max(size[0] / image.get_width(), size[1] / image.get_height())
    scaled_size = (round(image.get_width() * scale), round(image.get_height() * scale))
    image = pygame.transform.smoothscale(image, scaled_size)
    left = (image.get_width() - size[0]) // 2
    top = (image.get_height() - size[1]) // 2
    return image.subsurface((left, top, size[0], size[1])).copy()
