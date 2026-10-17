import pygame
import json
import subprocess
import sys
from abc import ABC, abstractmethod

def singleton(class_):
    instances = { }
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)	
        return instances[class_]
    return getinstance

class editor_obj():
    def __init__(self, pos, sprite, dir = None):
        self.pos = pos
        self.sprite = sprite
        self.data = {"pos" : pos, "imagem" : {"dir": "", "dim" : [1,1]}}
        if dir:
            self.load(dir)
        self.following = False

    def update (self):
        if self.following:
            self.pos = pygame.mouse.get_pos()
            self.data["pos"]= self.pos

    def draw (self, screen):
         screen.blit(self.sprite, self.pos)

    def load (self, dir):
        s = pygame.image.load(dir).convert_alpha()
        self.sprite = s
        self.data["imagem"]["dir"] = dir
        self.data["imagem"]["dim"] = s.get_size()

class Background_layer (editor_obj):
    def __init__(self, imagem, profundidade):
        super().__init__((0,0), pygame.transform.scale(imagem, (600, 400)))
        self.profundidade = profundidade


    
        

@singleton
class Editor():
    
    def __init__(self):
        self.state = State_posicionando()
        self.highlighted_object = None
        self.lvl_objs = []
        self.background = []
        self.bg_dir = []
        self.grid = []


        for i in range (8):
            self.grid.append([])
            for j in range (8):
                self.grid[i].append(None)


    def change_states(self, state):
        if state == "Posicionando":
            self.set_state(State_posicionando())
        elif state == "Movendo":
            self.set_state(State_movendo())
        elif state == "Background":
            self.set_state(State_background())
        elif state == "Tileset":
            self.set_state(State_tiles())


    def add_background(self, bg, dir):
        self.background.append(bg)
        self.bg_dir.append(dir)
        self.background.sort(key = lambda bg : bg.profundidade, reverse = True)

    def set_state(self, state):
        self.state = state


class Editor_states(ABC):

    def check_buttons (self, pos):
        for b in buttons:
            if (b.handle_click(pos, 1)):
                return True
        return False


    @abstractmethod
    def click(self, pos):
        pass

class State_movendo(Editor_states):
    def click(self, pos):

            if not self.check_buttons(pos):
                for o in Editor().lvl_objs:
                    if  o.sprite.get_rect(topleft = o.pos).collidepoint(event.pos):
                        place_obj = False
                        o.following = True
                        Editor().highlighted_object = o
                        break

class State_posicionando(Editor_states):
    def click(self, pos):

        if not self.check_buttons(pos):
            sprite = pygame.transform.scale(
                pygame.image.load(r".\images\duck\step.png"), duck_size)
            o = editor_obj(event.pos, sprite, dir = r".\images\duck\step.png")
            Editor().lvl_objs.append(o)


class State_tiles(Editor_states):


    def __init__(self):
        super().__init__()
        self.tileset = pygame.image.load(r"./images/tileset/tileset.png")
        # precisamos cortar elementos

        TILE_SIZE = 80
        self.tiles= []
        for _ in range (16):
            self.tiles.append(pygame.Surface((TILE_SIZE,TILE_SIZE))) 

        coords = [[0,0], [0,1], [1,0], [2,2],
                  [3,1], [0,2], [3,2], [0,3],
                  [1,3], [2,3], [2,0], [3,0],
                  [3,3], [2,1], [1,2], [1,1]]

        for tile, pos in zip(self.tiles, coords):
            tile.blit(self.tileset, [-pos[0]* TILE_SIZE, -pos[1]*TILE_SIZE])
        
        #for tile, pos in zip(self.tiles, coords):
        #    Editor().lvl_objs.append(editor_obj([pos[0]* (TILE_SIZE) + 100, pos[1]*(TILE_SIZE) + 100], tile))


    def click(self, pos):
        
        if not self.check_buttons(pos):
            x = pos[0] // 80 # converte coords mundo 
            y = pos[1] // 80 # pra coords da grid

            if Editor().grid[x][y]:
                Editor().grid[x][y] = None
            else:
                Editor().grid[x][y] = Tile_cell((x,y), self.tiles)

            for line in Editor().grid:
                for element in line:
                    if element:
                        element.resolve()
        



class State_background(Editor_states):
    def click(self, pos):
            if not self.check_buttons(pos):
                dir = r"./images/backgrounds/hills.jpg"
                im = pygame.image.load(dir)
                BG = Background_layer(im, 3)
                Editor().add_background(BG, dir)



class Tile_cell (editor_obj):
    def __init__(self, grid_pos, sprites):
        self.grid_pos = grid_pos
        self.sprites   = sprites
        super().__init__((grid_pos[0]*80, grid_pos[1]*80), self.sprites[self.pick_sprite()])
        
    def pick_sprite (self): #retornar qual sprite deve ser usada
        offset_vizinhos = [[-1, 0, 4], [0, -1, 8], [1, 0, 1], [0, 1, 2]]

        result_tile = 0

        for v in offset_vizinhos:
            vizinhox = self.grid_pos[0] + v[0]
            if vizinhox < 0 or vizinhox > 8:
                pass
            vizinhoy = self.grid_pos[1] + v[1]
            if vizinhoy < 0 or vizinhoy > 8:
                pass

            if Editor().grid[vizinhox][vizinhoy]: # None não passa
                result_tile += v[2] # valor para chegar na pos certa

        
        return result_tile

    def resolve (self):
        n = self.pick_sprite()
        self.sprite = self.sprites [n]


duck_size = [32, 32]

def save_level (lvl_dicionario):
    with open("level1.json", "w") as f:
        json.dump(lvl_dicionario, f)
    return "level1.json"

def play_level():
    lvl_dict = { "objetos" : [o.data for o in Editor().lvl_objs]}#,
                 #"background" : {image =  }}



    fdir = save_level( lvl_dict ) # salva 
   # chama o jogo já no nível
    subprocess.Popen([
        sys.executable,
        "main.py",
        "--lvl", #flag de passar nível
        fdir #passa o nível certo 
    ]) 


class Button:
    def __init__(self, rect, sprite=None):
        self.rect = pygame.Rect(rect)
        self.sprite = sprite

        if sprite is not None:
            max_w = self.rect.width * 0.8
            max_h = self.rect.height * 0.8

            scale = min(
                max_w / sprite.get_width(),
                max_h / sprite.get_height())
            size = (
                int(sprite.get_width() * scale),
                int(sprite.get_height() * scale))

            self.sprite = pygame.transform.scale(sprite, size)
    
        self.left_callback = None
        self.right_callback = None

# ---------------------
    def bind_left(self, callback):
        self.left_callback = callback

    def bind_right(self, callback):
        self.right_callback = callback

    def draw(self, surface):
        pygame.draw.rect(surface, (80, 80, 80), self.rect)
# ---------------------
        if self.sprite is not None:
            pos = self.sprite.get_rect(center=self.rect.center)
            surface.blit(self.sprite, pos)
    
    def handle_click(self, mouse_pos, mouse_button):
        if not self.rect.collidepoint(mouse_pos):
            return

        if mouse_button == 1 and self.left_callback:
            self.left_callback()
            return True

        elif mouse_button == 3 and self.right_callback:
            self.right_callback()
            return True



screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Pygame Sample")
clock = pygame.time.Clock()

running = True

def create_buttons():
    buttons = []
    icons = [
        r".\images\duck\duck.png",
        r".\images\icons\hand.png",
        r".\images\backgrounds\hills.jpg",
        r".\images\tileset\tileset.png"
    ]
    callbacks = [
        lambda  : Editor().change_states("Posicionando"),
        lambda  : Editor().change_states("Movendo"),
        lambda  : Editor().change_states("Background"),
        lambda  : Editor().change_states("Tileset")
    ]
    for i in range (len(list(zip(icons, callbacks)))):
        b = Button([0+60*i, 0, 60, 60], pygame.image.load(icons[i]))
        b.bind_left(callbacks[i])
        buttons.append(b)

    return buttons

buttons = create_buttons()

while running:

    # processa entrada
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            Editor().state.click(event.pos)
            
            
        if event.type == pygame.MOUSEBUTTONUP:
            if Editor().highlighted_object:
                Editor().highlighted_object.following = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                play_level()



    #atualiza objetos
    for o in Editor().lvl_objs:
        o.update()


    #desenha 
    screen.fill((30,30,30))

    for b in Editor().background:
        b.draw(screen)

    for linha in Editor().grid:
        for tile in linha:
            if tile:
                tile.draw(screen)

    for o in Editor().lvl_objs:
         o.draw(screen)

    for b in buttons:
        b.draw(screen)

    pygame.display.flip()
    clock.tick(15)

pygame.quit()