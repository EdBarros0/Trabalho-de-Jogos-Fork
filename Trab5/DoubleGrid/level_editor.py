"""Editor simples de nível em grade, no estilo do exemplo de aula."""

import json
import random
import subprocess
import sys
from pathlib import Path

import pygame

from assets import load_background
from terrain import Pattern47Terrain


pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trab5 | Editor de nivel - padrao 47")
CLOCK = pygame.time.Clock()
FONT = pygame.font.Font(None, 25)
SMALL = pygame.font.Font(None, 20)
BACKGROUND = load_background((WIDTH, HEIGHT))
ROOT = Path(__file__).parent
LEVEL_PATH = ROOT / "level1.json"
PLAYER_SPRITE = "images/duck/step.png"
COLS, ROWS, TILE = 18, 11, 40
ORIGIN = (40, 120)
cells = [["open" for _ in range(COLS)] for _ in range(ROWS)]
selected = "solid"


def load_level():
    """Continua a editar o último nível salvo, se existir."""
    if not LEVEL_PATH.exists():
        return
    try:
        data = json.loads(LEVEL_PATH.read_text(encoding="utf-8"))
        saved_cells = data["grade"]
        for row in range(min(ROWS, len(saved_cells))):
            for column in range(min(COLS, len(saved_cells[row]))):
                if saved_cells[row][column] in ("solid", "open"):
                    cells[row][column] = saved_cells[row][column]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        pass


def save_level():
    data = {"colunas": COLS, "grade": cells, "inicio": [70, 55], "jogador": PLAYER_SPRITE}
    LEVEL_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def random_level():
    for row in range(ROWS):
        for column in range(COLS):
            cells[row][column] = "solid" if random.random() < 0.20 else "open"
    # Piso e plataformas para que o nível recém-gerado seja jogável.
    cells[-1] = ["solid"] * COLS
    for left, right, row in ((2, 6, 8), (8, 12, 6), (13, 16, 8), (5, 9, 4)):
        for column in range(left, right):
            cells[row][column] = "solid"


def run_game():
    save_level()
    subprocess.Popen([sys.executable, str(ROOT / "main.py"), "--lvl", str(LEVEL_PATH)], cwd=ROOT)


load_level()
terrain = Pattern47Terrain(cells, COLS, ROWS)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                selected = "solid"
            elif event.key == pygame.K_2:
                selected = "open"
            elif event.key == pygame.K_g:
                random_level()
            elif event.key == pygame.K_s:
                save_level()
            elif event.key == pygame.K_p:
                run_game()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and pygame.Rect(ORIGIN, (COLS * TILE, ROWS * TILE)).collidepoint(event.pos):
                column = (event.pos[0] - ORIGIN[0]) // TILE
                row = (event.pos[1] - ORIGIN[1]) // TILE
                cells[row][column] = selected
            elif event.button == 3 and pygame.Rect(ORIGIN, (COLS * TILE, ROWS * TILE)).collidepoint(event.pos):
                column = (event.pos[0] - ORIGIN[0]) // TILE
                row = (event.pos[1] - ORIGIN[1]) // TILE
                cells[row][column] = "open" if cells[row][column] == "solid" else "solid"

    SCREEN.blit(BACKGROUND, (0, 0))
    pygame.draw.rect(SCREEN, (17, 35, 48, 205), (0, 0, WIDTH, 110))
    pygame.draw.rect(SCREEN, (17, 35, 48, 185), (0, 558, WIDTH, 42))
    SCREEN.blit(FONT.render("Editor de nivel | Padrao 47", True, (238, 242, 229)), (40, 25))
    instructions = "1: solido  2: sem colisao  Clique: pintar  Botao direito: alternar"
    SCREEN.blit(SMALL.render(instructions, True, (178, 205, 201)), (40, 57))
    SCREEN.blit(SMALL.render("G: gerar mapa  S: salvar  P: jogar nivel", True, (178, 205, 201)), (40, 82))
    terrain.draw(SCREEN, ORIGIN, TILE, show_collision=True)
    pygame.draw.rect(SCREEN, (188, 214, 203), (40, 568, 22, 18), border_radius=3)
    pygame.draw.rect(SCREEN, (221, 104, 76), (40, 568, 22, 18), 1, border_radius=3)
    selected_text = "solido (1)" if selected == "solid" else "sem colisao (2)"
    SCREEN.blit(SMALL.render(f"Pincel: {selected_text} | camada vermelha indica colisao", True,
                             (237, 205, 173)), (72, 568))
    pygame.display.flip()
    CLOCK.tick(60)

pygame.quit()
