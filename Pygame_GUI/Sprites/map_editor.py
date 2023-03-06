from Pygame_GUI.Sprites.Objects import *


class MapEditor(Sprite):
    def __init__(self, par_surf, /, map_shape=None, **kwargs):
        super().__init__(par_surf, **kwargs)
        self.map_shape = map_shape
        self.discrete_per_pixel_width = self.map_shape[0] / self.width
        self.discrete_per_pixel_height = self.map_shape[1] / self.height
        self.discrete_wh = self.width / self.map_shape[0], self.height / self.map_shape[1]
        self.bin_map = np.zeros(self.map_shape).astype(np.uint8)
        self.time_range = slice(0, self.map_shape[-1]-1)
        self.curr_time = 0
        self.set_mode = 1
        self.origin = [15, 26, slice(0, map_shape[2]-1)]
        self.end_point = [map_shape[0]-1, map_shape[1]-1, slice(0, map_shape[2]-1)]
        self.full_map = np.zeros(self.map_shape).astype(np.uint16)
        self.full_map[15, 26, :] = 2
        self.point_ind = 3
        self.points = dict()
        self.points[0] = [15, 26, slice(0, map_shape[2]-1)]
        self.brush = 1
        self.robot_init_pos = [15, 26]
        self.robot_pos = self.robot_init_pos
        self.draw_robot = False


    def set_mode_wall(self, *args, **kwargs):
        self.set_mode = 1

    def set_mode_origin(self, *args, **kwargs):
        self.set_mode = 2

    def set_mode_point(self, *args, **kwargs):
        self.set_mode = 3

    def change_curr_time(self, val):
        self.curr_time = int(val)

    def change_brush_size(self, val):
        self.brush = int(val)

    def fill_map(self, x, y, setter=1):
        bs = self.brush
        if bs == 1:
            self.full_map[x, y, self.time_range] = setter
            return
        for di in range(-bs, bs):
            for dj in range(-bs, bs):
                i, j = x + di, y + dj
                if di ** 2 + dj ** 2 < bs ** 2 and self.map_shape[0] > i >= 0 and self.map_shape[1] > j >= 0:
                    self.full_map[i, j, self.time_range] = setter

    def release(self, *args, **kwargs):
        #self.update_map()
        pass

    def update_map(self):
        self.bin_map = self.full_map == 1

    def input_ttl(self, *args, **kwargs):
        try:
            print("begin: ", end='')
            from_time = int(input())
            print("end: ", end='')
            to_time = int(input())
            if to_time < from_time:
                assert Exception
            else:
                self.time_range = slice(from_time, to_time)
        except:
            print("wrong format")

    def pressed(self, *args, **kwargs):
        pos = kwargs["mouse_pos"]
        x = int(pos[0] * self.discrete_per_pixel_width)
        y = int(pos[1] * self.discrete_per_pixel_height)
        if x >= self.full_map.shape[0] or y >= self.full_map.shape[1]:
            return
        if kwargs["btn_id"] == 1:
            if not self.full_map[x, y, self.time_range].any():

                if self.set_mode == 2:
                    self.full_map[self.origin[0], self.origin[1], self.origin[2]] = 0
                    self.origin = [x, y, self.time_range]
                    self.points[0] = [x, y, self.time_range]
                    self.full_map[x, y, self.time_range] = self.set_mode
                elif self.set_mode == 3:
                    self.full_map[x, y, self.time_range] = self.point_ind
                    self.points[self.point_ind] = [x, y, self.time_range]
                    self.point_ind += 1
                    self.end_point = [x, y, self.time_range]
                else:
                    self.full_map[x, y, self.time_range] = 1
            else:
                print("no")
        else:
            to_del_ind = self.full_map[x, y, self.curr_time]
            if to_del_ind == 1:
                self.full_map[x, y, self.time_range] = 0
            elif to_del_ind and to_del_ind != 2:
                to_del_param = self.points[to_del_ind]
                del self.points[to_del_ind]
                self.full_map[to_del_param[0], to_del_param[1], to_del_param[2].start:to_del_param[2].stop] = 0


    def dragged(self, *args, **kwargs):
        setter = 1
        if kwargs["btn_id"] == 3:
            setter = 0
        elif self.set_mode != 1:
            return
        pos = kwargs["mouse_pos"]
        x = int(pos[0] * self.discrete_per_pixel_width)
        y = int(pos[1] * self.discrete_per_pixel_height)
        if x >= self.full_map.shape[0] or y >= self.full_map.shape[1]:
            return
        self.full_map[x, y, self.time_range] = setter

    def discrete_rect(self, i, j):
        x = i * self.discrete_wh[0]
        y = j * self.discrete_wh[1]
        return (x, y, *self.discrete_wh)

    def draw(self):
        out = self.full_map[:, :, self.curr_time] == 1
        self.surface.blit(
            pg.transform.scale(pg.surfarray.make_surface((out-1) * -255), (self.width, self.height)), (0, 0))
        for i in range(self.map_shape[0]):
            for j in range(self.map_shape[1]):
                if self.full_map[i, j, self.curr_time] == 2:
                    pg.draw.rect(self.surface, (0, 255, 0), self.discrete_rect(i, j))
                elif self.full_map[i, j, self.curr_time] != 0 and out[i, j] != 1:
                    pg.draw.rect(self.surface, (0, 0, 255), self.discrete_rect(i, j))

        if self.draw_robot:
            pg.draw.circle(self.surface, (0, 255, 0), self.robot_pos, 30)

    def set_robot_pos(self, pos):
        x = (pos[0] + self.robot_init_pos[0])*self.discrete_wh[0]
        y = (pos[1] + self.robot_init_pos[1])*self.discrete_wh[1]
        self.robot_pos = [x, y]
