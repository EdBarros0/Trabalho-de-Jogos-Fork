"""Autotiling pelo padrão 47, com máscara de vizinhança e colisão por célula."""

import pygame

from assets import load_tileset


class Pattern47Terrain:
    TILE = 40
    SOURCE_TILE = 80
    ATLAS_ORIGIN = (112, 80)
    ATLAS_STEP = 84
    ART_SCALE = 1.10
    # No atlas, colunas 0 e 3 são pontas; 1 e 2 completam o trecho reto.
    TOP_TILES = tuple((column, 0) for column in range(4))
    BOTTOM_TILES = tuple((column, 2) for column in range(5))
    INTERIOR_TILES = tuple((column, 1) for column in range(5))

    def __init__(self, cells, columns, rows):
        self.cells = cells
        self.columns = columns
        self.rows = rows
        self.tileset = load_tileset()
        self._tile_cache = {}
        self._overlay_cache = {}

    def get(self, row, column):
        if row < 0 or column < 0 or row >= self.rows or column >= self.columns:
            return "open"
        return self.cells[row][column]

    def neighbor_mask_47(self, row, column):
        """Codifica cardinais e diagonais apenas quando a diagonal conecta."""
        solid = lambda dy, dx: self.get(row + dy, column + dx) == "solid"
        north, east, south, west = solid(-1, 0), solid(0, 1), solid(1, 0), solid(0, -1)
        mask = 0
        if north:
            mask |= 1
        if east:
            mask |= 4
        if south:
            mask |= 16
        if west:
            mask |= 64

        # Um vizinho diagonal só conta se estiver ligado pelos dois cardinais.
        if north and east and solid(-1, 1):
            mask |= 2
        if east and south and solid(1, 1):
            mask |= 8
        if south and west and solid(1, -1):
            mask |= 32
        if west and north and solid(-1, -1):
            mask |= 128
        return mask

    def draw(self, surface, origin=(0, 0), tile_size=None, show_collision=False):
        size = tile_size or self.TILE
        # A grade das células abertas vai atrás dos sprites. Como os sprites
        # ultrapassam um pouco a célula, desenhá-la depois criava frestas nas
        # junções ao cobrir as bordas ampliadas.
        for row in range(self.rows):
            for column in range(self.columns):
                current = self.get(row, column)
                x, y = origin[0] + column * size, origin[1] + row * size
                rect = pygame.Rect(x, y, size, size)
                if current != "solid":
                    # Células sem colisão deixam o fundo visível; no editor,
                    # uma malha sutil mostra onde é possível pintar.
                    if show_collision:
                        surface.blit(self._overlay(size, (35, 105, 142, 30)), rect)
                        pygame.draw.rect(surface, (91, 145, 160), rect, 1)

        for row in range(self.rows):
            for column in range(self.columns):
                if self.get(row, column) != "solid":
                    continue
                x, y = origin[0] + column * size, origin[1] + row * size
                rect = pygame.Rect(x, y, size, size)
                art_size = round(size * self.ART_SCALE)
                overdraw = (art_size - size) // 2
                art = self._sprite_for(row, column, art_size)
                surface.blit(art, (x - overdraw, y - overdraw))
                if show_collision:
                    surface.blit(self._overlay(size, (241, 72, 48, 48)), rect)

    def _overlay(self, size, color):
        key = (size, color)
        if key not in self._overlay_cache:
            overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            overlay.fill(color)
            self._overlay_cache[key] = overlay
        return self._overlay_cache[key]

    def _sprite_for(self, row, column, size):
        mask = self.neighbor_mask_47(row, column)
        north, east, south, west = (bool(mask & bit) for bit in (1, 4, 16, 64))
        diagonal_signature = sum(bool(mask & bit) << index
                                 for index, bit in enumerate((2, 8, 32, 128)))
        if not north:
            atlas_column, atlas_row = self._horizontal_piece(
                west, east, diagonal_signature, self.TOP_TILES
            )
        elif not west:
            atlas_column, atlas_row = (0, 1)
        elif not east:
            # A coluna 4 tem uma margem transparente larga à esquerda e abre
            # uma fresta contra o vizinho. A coluna 3 mantém essa junção cheia.
            atlas_column, atlas_row = (3, 1)
        elif not south:
            atlas_column, atlas_row = self._horizontal_piece(
                west, east, diagonal_signature, self.BOTTOM_TILES
            )
        else:
            atlas_column, atlas_row = self._horizontal_piece(
                west, east, diagonal_signature, self.INTERIOR_TILES
            )

        key = (atlas_column, atlas_row, size)
        if key not in self._tile_cache:
            source_x = self.ATLAS_ORIGIN[0] + atlas_column * self.ATLAS_STEP
            source_y = self.ATLAS_ORIGIN[1] + atlas_row * self.ATLAS_STEP
            source_rect = pygame.Rect(source_x, source_y,
                                      self.SOURCE_TILE, self.SOURCE_TILE)
            tile = self.tileset.subsurface(source_rect).copy()
            self._tile_cache[key] = pygame.transform.scale(tile, (size, size))
        return self._tile_cache[key]

    @staticmethod
    def _horizontal_piece(west, east, diagonal_signature, tiles):
        """Mantém pontas nas bordas e usa as diagonais para variar o miolo."""
        if not west and east:
            return tiles[0]
        if west and not east:
            return tiles[-1]

        middle = tiles[1:-1]
        if len(middle) == 1:
            return middle[0]
        return middle[diagonal_signature % len(middle)]

    def is_solid_at(self, x, y, origin=(0, 0), tile_size=None):
        size = tile_size or self.TILE
        column = int((x - origin[0]) // size)
        row = int((y - origin[1]) // size)
        return self.get(row, column) == "solid"
