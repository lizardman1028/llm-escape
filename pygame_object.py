import pygame
from our_enums import Unlock_Type, Agent_Type, Item_Type
class PygameObject:
    def __init__(self, 
                color: tuple, 
                x: int, 
                y: int, 
                width: int = 40, 
                height: int = 40,
                shape_type: str = "rect"):
        
        self.shape_type = shape_type    # "rect", "circle", "triangle", etc.
        self.color = color              # (R, G, B)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.item_type : Item_Type = Item_Type.ITEM 
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.center_x = self.x + self.width/2
        self.center_y = self.y + self.height/2
    
    def in_player_radius(self, player_x, player_y, radius):
        return player_x - radius < self.center_x and self.center_x < player_x + radius and player_y - radius < self.center_y and self.center_y < player_y + radius
            
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)    