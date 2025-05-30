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

        self.top_left_x = self.x
        self.top_left_y = self.y

        self.top_right_x = self.x + self.width
        self.top_right_y = self.y

        self.bottom_left_x = self.x
        self.bottom_left_y = self.y + self.height

        self.bottom_right_x = self.x + self.width
        self.bottom_right_y = self.y + self.height
    
    def center_in_player_radius(self, player_x, player_y, radius=30) -> bool:
        return player_x - radius < self.center_x and self.center_x < player_x + radius and player_y - radius < self.center_y and self.center_y < player_y + radius
    
    def player_inside(self, player_x, player_y, player_radius=0) -> bool:
        inside_x = (self.top_left_x <= player_x) and (self.bottom_right_x >= player_x)
        inside_y = (self.top_left_y <= player_y) and (self.bottom_right_y >= player_y)
        return inside_x and inside_y
    
    def nearest_interior_pt(self, player_x, player_y, player_radius=30) -> tuple[int, int] :
        interior_x = player_x
        interior_y = player_y
        if (player_x < self.top_left_x):
            interior_x = self.top_left_x
        if (player_x > self.bottom_right_x):
            interior_x = self.bottom_right_x
        if (player_y < self.top_left_y):
            interior_y = self.top_left_y
        if (player_y > self.bottom_right_y):
            interior_y = self.bottom_right_y

        return interior_x, interior_y

    def in_player_radius(self, player_x, player_y, radius=30) -> bool:
        if self.player_inside(player_x, player_y):
            return True
        
        # if self.center_in_player_radius(player_x, player_y, radius):
        #     return True
        
        top_left_x = self.x
        top_left_y = self.y

        top_right_x = self.x + self.width
        top_right_y = self.y

        bottom_left_x = self.x
        bottom_left_y = self.y + self.height

        bottom_right_x = self.x + self.width
        bottom_right_y = self.y + self.height

        top_left_in = player_x - radius < top_left_x and top_left_x < player_x + radius and player_y - radius < top_left_y and top_left_y < player_y + radius
        if top_left_in:
            return True
        
        bottom_right_in = player_x - radius < bottom_right_x and bottom_right_x < player_x + radius and player_y - radius < bottom_right_y and bottom_right_y < player_y + radius
        if bottom_right_in:
            return True
        
        top_right_in = player_x - radius < top_right_x and top_right_x < player_x + radius and player_y - radius < top_right_y and top_right_y < player_y + radius
        if top_right_in:
            return True
        
        bottom_left_in = player_x - radius < bottom_left_x and bottom_left_x < player_x + radius and player_y - radius < bottom_left_y and bottom_left_y < player_y + radius
        if bottom_left_in:
            return True
        
        return False

        
            
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)    