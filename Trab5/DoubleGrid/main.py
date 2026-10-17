"""Jogo de plataforma mínimo que carrega um nível criado no editor."""

import json
import sys
from pathlib import Path

import pygame

from assets import load_background
from obj import Obj
from terrain import Pattern47Terrain


pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trab5 | Plataforma com padrão 47")
CLOCK = pygame.time.Clock()
FONT = pygame.font.Font(None, 24)
BACKGROUND = load_background((WIDTH, HEIGHT))
ROOT = Path(__file__).parent
GRID_ORIGIN = (40, 100)
TILE = 40


def load_level(path):
    with open(path, encoding="utf-8") as level_file:
        data = json.load(level_file)
    rows = data["grade"]
    terrain = Pattern47Terrain(rows, data["colunas"], len(rows))
    sprite_path = ROOT / data.get("jogador", "images/duck/step.png")
    player_image = pygame.image.load(sprite_path).convert_alpha()
    player_image = pygame.transform.scale(player_image, (32, 32))
    player = Obj(tuple(data.get("inicio", [70, 50])), player_image)
    return terrain, player


def find_level_arg():
    if "--lvl" in sys.argv:
        path = Path(sys.argv[sys.argv.index("--lvl") + 1])
        return path if path.is_absolute() else ROOT / path
    return ROOT / "level1.json"


terrain, player = load_level(find_level_arg())
velocity_y = 0.0
speed = 230
on_ground = False
running = True


def collides_with_terrain(rect):
    first_column = max(0, (rect.left - GRID_ORIGIN[0]) // TILE)
    last_column = min(terrain.columns - 1, (rect.right - 1 - GRID_ORIGIN[0]) // TILE)
    first_row = max(0, (rect.top - GRID_ORIGIN[1]) // TILE)
    last_row = min(terrain.rows - 1, (rect.bottom - 1 - GRID_ORIGIN[1]) // TILE)
    for row in range(first_row, last_row + 1):
        for column in range(first_column, last_column + 1):
            if terrain.get(row, column) == "solid":
                tile_rect = pygame.Rect(GRID_ORIGIN[0] + column * TILE,
                                        GRID_ORIGIN[1] + row * TILE, TILE, TILE)
                if rect.colliderect(tile_rect):
                    return tile_rect
    return None


while running:
    dt = min(CLOCK.tick(60) / 1000, 0.03)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    move_x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
    player_rect = player.sprite.get_rect(topleft=player.pos)
    player_rect.x = max(0, min(WIDTH - player_rect.width,
                               round(player_rect.x + move_x * speed * dt)))
    hit = collides_with_terrain(player_rect)
    if hit:
        player_rect.right = hit.left if move_x > 0 else hit.right
    player.pos = (player_rect.x, player_rect.y)
    if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
        velocity_y = -430
        on_ground = False

    velocity_y = min(650, velocity_y + 1050 * dt)
    player_rect.y = round(player_rect.y + velocity_y * dt)
    hit = collides_with_terrain(player_rect)
    if hit:
        if velocity_y > 0:
            player_rect.bottom = hit.top
            on_ground = True
        elif velocity_y < 0:
            player_rect.top = hit.bottom
        velocity_y = 0
    else:
        on_ground = False
    player_rect.y = max(0, min(HEIGHT - player_rect.height, player_rect.y))
    player.pos = (player_rect.x, player_rect.y)

    SCREEN.blit(BACKGROUND, (0, 0))
    terrain.draw(SCREEN, GRID_ORIGIN, TILE)
    player.draw(SCREEN)
    pygame.draw.rect(SCREEN, (17, 35, 48, 190), (0, 0, WIDTH, 68))
    SCREEN.blit(FONT.render("A/D ou setas: mover   Espaco/W/↑: pular", True, (238, 242, 229)), (40, 28))
    pygame.display.flip()

pygame.quit()
