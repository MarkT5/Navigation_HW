from Pygame_GUI.Sprites.Objects import Sprite
import pygame as pg


class GraphSprite(Sprite):
    def __init__(self, par_surf, /, graph=None, map_editor=None, **kwargs):
        assert map_editor
        super().__init__(par_surf, **kwargs)
        self.graph = graph
        self.map_editor = map_editor
        self.map_shape = map_editor.map_shape
        self.path_end_node = None
        self.draw_tree = True
        self.discrete_wh = self.width / self.map_shape[0], self.height / self.map_shape[1]
        self.transparent_for_mouse = True
        self.style = {0: {"color": (0, 255, 0), "radius": 20},
                      1: {"color": (0, 255, 0), "radius": 20},
                      2: {"color": (130, 255, 0), "radius": 5},
                      3: {"color": (0, 0, 255), "radius": 20},
                      4: {"color": (0, 0, 255), "radius": 20}}
        '''
        ORIGIN = 0
        ORIGIN_BLOCKED = 1
        SLAVE = 2
        ENDPOINT = 3
        ENDPOINT_BLOCKED = 4'''

    def convert_coords(self, pos):
        return (pos[0] + 0.5) * self.discrete_wh[0], (pos[1] + 0.5) * self.discrete_wh[1]

    def draw(self):
        if self.graph:
            if self.draw_tree:
                for i in range(len(self.graph)):
                    node = self.graph[i]
                    color = self.style[node.rank]["color"]
                    rad = self.style[node.rank]["radius"]
                    pg.draw.circle(self.surface, color, self.convert_coords(node.pos[:2]), rad)
                    if node.parent:
                        pg.draw.aaline(self.surface, (0, 0, 0),
                                       self.convert_coords(node.pos[:2]),
                                       self.convert_coords(node.parent.pos[:2]))
            if self.path_end_node:
                node = self.graph[self.path_end_node]
                for _ in range(len(self.graph)):
                    color = (255, 0, 0)
                    if node.parent:
                        pg.draw.line(self.surface, color,
                                     self.convert_coords(node.pos[:2]),
                                     self.convert_coords(node.parent.pos[:2]), 17)
                    else:
                        break
                    node = node.parent


