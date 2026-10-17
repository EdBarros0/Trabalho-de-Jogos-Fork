import pygame
import json
from obj import Obj
import sys

pygame.init()

screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Pygame Sample")
clock = pygame.time.Clock()

running = True


def load_level(dir):
    with open (dir, 'r') as file:
            l = json.load(file) # é um dicionário

    if "objetos" not in l:
        return None
    
    objs = []
    for o in l["objetos"]:
         if "imagem" not in o:
              pass
         sprite = pygame.image.load(o["imagem"]["dir"]).convert_alpha()
         sprite = pygame.transform.scale(sprite, o["imagem"]["dim"])
         if "pos" not in o:
              pass
          
         objs.append(Obj(o["pos"], sprite))
    return objs
        


# nosso json digamos que é uma lista de objetos
#{
#    objetos = [ 
#        {   
        #   imagem = quack.png,
        #    pos   = [20, 40 ]
#         }, 
#   ]     
#}



if "--lvl" in sys.argv:
#pega o índice depois de lvl
    pos = sys.argv.index("--lvl") + 1
    level_file = sys.argv[pos]
else:
    level_file = "main_level.json"
lvl_objs = load_level (level_file)



while running:


    # processa entrada
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    #atualiza objetos
    #pato.update(1) #passando o dt como 1


    #desenha 
    screen.fill((30,30,30))
    print(len(lvl_objs))
    for o in lvl_objs:
         o.draw(screen)
    pygame.display.flip()
    clock.tick(15)

pygame.quit()