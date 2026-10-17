class Obj ():
    def __init__(self, pos, sprite):
          self.pos = pos
          self.sprite = sprite

    def draw (self, screen):
         screen.blit(self.sprite, self.pos)