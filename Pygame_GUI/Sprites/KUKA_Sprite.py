from Pygame_GUI.Sprites.Objects import Sprite
from KUKA.KUKA import KUKA
import pygame as pg


class KUKASprite(Sprite, KUKA):
    def __init__(self, par_surf, **kwargs):
        KUKA.__init__(self, kwargs["ip"], **kwargs)
        Sprite.__init__(self, par_surf, **kwargs)
        self.move_speed_val = 0.4
        self.old_move_speed = [0, 0, 0]
        self.last_checked_pressed_keys = []
        self.wasd_enabled = True

    def update(self):
        pressed_keys = self.par_surf.pressed_keys[:]
        move_speed = [0, 0, 0]
        fov = 0
        if self.wasd_enabled:
            if pg.K_w in pressed_keys:
                fov += 1
            if pg.K_s in pressed_keys:
                fov -= 1
            move_speed[0] = fov * self.move_speed_val

            rot = 0
            if pg.K_a in pressed_keys:
                rot += 1
            if pg.K_d in pressed_keys:
                rot -= 1
            move_speed[2] = rot * self.move_speed_val

            side = 0
            if pg.K_q in pressed_keys:
                side += 1
            if pg.K_e in pressed_keys:
                side -= 1
            move_speed[1] = side * self.move_speed_val

            if self.last_checked_pressed_keys != pressed_keys and self.old_move_speed != move_speed:
                self.move_base(*move_speed)
                self.going_to_target_pos = False
                self.last_checked_pressed_keys = pressed_keys[:]
                self.old_move_speed = move_speed[:]

    def draw(self):
        pass
