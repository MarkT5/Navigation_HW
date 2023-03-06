import time
import math
import threading as thr

import numpy as np

from Pygame_GUI.Screen import Screen
from Pygame_GUI.Sprites.KUKA_Sprite import KUKASprite
from Pygame_GUI.Space3D.Space3D import Space3D
from Pygame_GUI.Sprites.Objects import *
from Pygame_GUI.Sprites.map_editor import MapEditor
from Pygame_GUI.Sprites.Graph import GraphSprite
from pathfinding.time_rrt.time_tree import TimeTree
import random

from Pygame_GUI.Screen import Screen
from Pygame_GUI.Space3D.object_3d import *


class RRT_sim:
    def __init__(self, robot=None):

        self.discrete = 10
        self.robot_radius = int(0.3 * self.discrete + 1)

        self.rrt = None
        self.map_shape = (80, 45, 100)
        self.bool_map = np.zeros(self.map_shape)
        # self.bool_map[0, :, :] = 1
        # self.bool_map[:, 0, :] = 1
        # self.bool_map[-1, :, :] = 1
        # self.bool_map[:, -1, :] = 1

        self.bool_map[50:, 10:20, :] = 1
        self.bool_map[45:55, :15, :] = 1
        self.screen = Screen(2000, 1250)
        self.screen.init()
        self.enable_3d = True
        self.time_from_start = time.time()

        self.robot = self.screen.sprite(KUKASprite, "KUKA",
                                        ip='192.168.88.21', ros=False, offline=True, read_depth=False,
                                        camera_enable=False, advanced=False)

        if self.enable_3d:
            self.space_3d = self.screen.sprite(Space3D, "Space3D", x=0.5, y=0, width=0.5, height=0.8)
            self.cube = (self.space_3d, [*np.array([(-1, -1, -1, 2), (1, -1, -1, 2), (-1, 1, -1, 2), (-1, -1, 1, 2),
                                                    (1, 1, -1, 2), (1, -1, 1, 2),
                                                    (-1, 1, 1, 2), (1, 1, 1, 2)]) / 2],
                         [[0, 1, 4, 2][::-1], [3, 6, 7, 5][::-1], [0, 3, 5, 1][::-1], [2, 4, 7, 6][::-1],
                          [1, 5, 7, 4][::-1], [2, 6, 3, 0][::-1]])
            self.map3d = Solid3D(*self.cube)
            self.robot_3D_dot = Dot3D(self.space_3d, [[3.0, 3.0, 3.0, 1.0]], vertex_radius=[10],
                                      vertex_colors=[(0, 255, 0)],
                                      pos=(-40.5, -22.5, -51.5))
            self.robot_3D_dot.scale(1, 1, -1)

            self.axis_3d = Axis(self.space_3d)
            self.axis_3d.scale(-1, 1, 1)
            self.axis_3d.translate((0, 0, 10))
            self.axis_3d.post_projection_transform[3, :] = [0.7, 0.7, 0, 1]

            self.axis_3d.fix_to_camera = True
        self.map_editor = self.screen.sprite(MapEditor, "MapEditor", x=0.0, y=0, width=0.5, height=0.5,
                                             color=(255, 255, 255), map_shape=self.map_shape)
        self.map_editor.full_map = self.bool_map
        self.screen.sprite(Button, "input_TTL", x=0.51, y=0.82, width=0.06, height=0.08, color=(150, 255, 170),
                           func=self.map_editor.input_ttl, image="sprite_images/TTL2.png")
        self.screen.sprite(Button, "go_to", x=0.58, y=0.82, width=0.06, height=0.08, color=(0, 0, 0),
                           func=self.start_travelling_path)
        self.screen.sprite(Text, "go_to_label", x=0.58, y=0.82, width=0.06, height=0.08, color=(0, 255, 0),
                           inp_text=lambda: "GO", font='Verdana',
                           font_size=30, transparent_for_mouse=True)
        self.screen.sprite(Button, "set_origin", x=0.65, y=0.82, width=0.06, height=0.04, color=(0, 255, 0),
                           func=self.map_editor.set_mode_origin)
        self.screen.sprite(Button, "set_point", x=0.72, y=0.82, width=0.06, height=0.04, color=(0, 0, 255),
                           func=self.map_editor.set_mode_point)
        self.screen.sprite(Button, "set_wall", x=0.79, y=0.82, width=0.06, height=0.04, color=(132, 31, 39),
                           func=self.map_editor.set_mode_wall)
        self.screen.sprite(Button, "run_rrt", x=0.86, y=0.82, width=0.06, height=0.08, color=(255, 0, 255),
                           func=self.run_rrt, image="sprite_images/pathfinding.png")
        self.btn_3d = self.screen.sprite(Button, "disable_3d", x=0.93, y=0.82, width=0.06, height=0.08,
                                         color=(255, 0, 255),
                                         func=self.disable_3d, image=(
                "sprite_images/no_3d.png", "sprite_images/3d.png"))

        self.screen.sprite(Text, "set_origin_label", x=0.65, y=0.86, inp_text=lambda: "set_origin", font='serif',
                           font_size=10)
        self.screen.sprite(Text, "set_point_label", x=0.72, y=0.86, inp_text=lambda: "set_point", font='serif',
                           font_size=10)
        self.screen.sprite(Text, "set_wall_label", x=0.79, y=0.86, inp_text=lambda: "set_wall", font='serif',
                           font_size=10)
        self.screen.sprite(Slider, "curr_time", min=0, max=self.map_shape[-1] - 1, x=0.53, y=0.91,
                           width=0.2, height=0.05, color=(150, 160, 170),
                           func=self.screen["MapEditor"].change_curr_time)
        self.screen.sprite(Text, "out_time", x=0.75, y=0.91, inp_text=self.out_time, font='serif',
                           font_size=30)
        self.screen.sprite(Text, "out_vel", x=0.87, y=0.91, inp_text=self.out_vel, font='serif',
                           font_size=30)
        self.X_txt = self.screen.sprite(Text, "x", x=0.0, y=0.0, inp_text=lambda: "X", font='serif',
                                        font_size=10)
        self.Y_txt = self.screen.sprite(Text, "y", x=0.0, y=0.0, inp_text=lambda: "Y", font='serif',
                                        font_size=10)
        self.T_txt = self.screen.sprite(Text, "t", x=0.0, y=0.0, inp_text=lambda: "T", font='serif',
                                        font_size=10)

        self.graph_sprite = self.screen.sprite(GraphSprite, "RRT", x=0.0, y=0, graph=None, width=0.5, height=0.5,
                                               map_editor=self.map_editor)

        self.path_orig = [15, 26, 0]
        self.move_speed_val = 0.5
        self.last_checked_pressed_keys = []
        self.drive = False
        self.time_from_start = 0
        self.start_pos = [0, 0, 0]
        self.path_colors = [[255, 0, 0]]

        self.curr_point = 1
        self.goal = np.array(False)
        self.tree_running = False
        self.inv_dot_mat = np.array([[1, 1, 1, 1],
                                     [1, -1, -1, 1],
                                     [1, -1, -1, 1],
                                     [1, 1, 1, 1]])

    def out_time(self):
        return "T: " + str(round(self.curr_time(), 1))

    def out_vel(self):
        vx, vy, _ = self.robot.move_speed
        return "V: " + str(round(math.sqrt(vx ** 2 + vy ** 2) * 100))

    def disable_3d(self, *args, **kwargs):
        self.btn_3d.curr_img = not self.btn_3d.curr_img
        self.space_3d.enable = not self.space_3d.enable

    def export_3d(self, *arg, **kwargs):
        self.screen["MapEditor"].update_map()
        if self.tree_running:
            del self.rrt
        self.tree_running = False
        self.bin_map = self.screen["MapEditor"].bin_map
        exporter_bin_map = self.screen["MapEditor"].bin_map
        if not self.enable_3d:
            return
        for sl in range(3):
            shape = list(exporter_bin_map.shape)
            shape[sl] = 1

            zero_layer = np.zeros(shape)
            exporter_bin_map = np.append(zero_layer, exporter_bin_map, axis=sl)
            exporter_bin_map = np.append(exporter_bin_map, zero_layer, axis=sl)
        ebms = exporter_bin_map.shape
        vertices = np.array(False)
        edges = []
        curr_edge = 0
        for sl in range(3):
            for i in range(1, self.map_shape[sl] + 2):
                slicer = [slice(0, ebms[0]), slice(0, ebms[1]), slice(0, ebms[2])]
                slicer[sl] = i - 1
                prev_plane = exporter_bin_map[slicer[0], slicer[1], slicer[2]]
                slicer[sl] = i
                plane = exporter_bin_map[slicer[0], slicer[1], slicer[2]]
                vertices_x = []
                vertices_y = []
                for x in range(len(plane)):
                    for y in range(len(plane[x])):
                        if prev_plane[x, y] != plane[x, y]:
                            vertices_x += [x, x, x + 1, x + 1]
                            vertices_y += [y, y + 1, y + 1, y]
                            edges += [[curr_edge, curr_edge + 1, curr_edge + 2],
                                      [curr_edge, curr_edge + 2, curr_edge + 3]]
                            curr_edge += 4
                vertices_curr = np.zeros((len(vertices_x), 4)).astype(float_bit)
                vertices_curr[:, 3] = 1

                if len(vertices_x) == 0:
                    continue
                if sl == 0:
                    vertices_curr[:, 0] = i
                    vertices_curr[:, 1] = vertices_x
                    vertices_curr[:, 2] = vertices_y

                if sl == 1:
                    vertices_curr[:, 0] = vertices_x
                    vertices_curr[:, 1] = i
                    vertices_curr[:, 2] = vertices_y
                if sl == 2:
                    vertices_curr[:, 0] = vertices_x
                    vertices_curr[:, 1] = vertices_y
                    vertices_curr[:, 2] = i
                if vertices.any():
                    vertices = np.append(vertices, vertices_curr, axis=0)
                else:
                    vertices = vertices_curr
        map3d = Solid3D(self.space_3d, vertices, edges, pos=(-40.5, -22.5, -51.5))  # (16.5, 16.5,)
        map3d.scale(1, 1, -1)
        self.map3d.draw_faces = True

    def run_rrt(self, *args, **kwargs):
        if self.rrt:
            del self.rrt
        self.export_3d()
        if self.enable_3d:
            self.tree_3d_graphics = Hollow3D(self.space_3d, [[0.0, 0.0, 0.0, 1.0],
                                                             [0.0, 0.0, 0.0, 1.0]],
                                             [[0, 0]], edges_thickness=[1])
            self.tree_3d_graphics.translate((-40, -22, -51.0))
            self.tree_3d_graphics.scale(1, 1, -1)

            self.space_3d.add_object(self.tree_3d_graphics)

        points = [i[1] for i in sorted(self.map_editor.points.items(), key=lambda x: x[0])]
        orig, end = points[0], points[1]

        self.path_orig = orig[:2]
        orig_point = [[orig[0], orig[1], i] for i in range(orig[2].start, orig[2].stop)]
        end_point = [[end[0], end[1], i] for i in range(end[2].start, end[2].stop)]
        self.orig_len = orig[2].stop - orig[2].start
        self.end_len = end[2].stop - end[2].start
        self.map_editor.update_map()
        self.rrt = TimeTree(start_point=np.array(orig_point), end_point=np.array(end_point),
                            bin_map=self.map_editor.bin_map)
        self.graph_sprite.graph = self.rrt.graph
        self.rrt.start_thread()

    def main_thr(self):
        self.robot.go_to(0, 0, 0)
        # time.sleep(1)
        self.map_editor.draw_robot = True
        self.space_3d.camera.direction = rotate_x(math.pi)
        self.space_3d.camera.pos_serv = np.array([0, 0, -150, 1.0])
        while self.screen.running:
            self.axis_3d.transform[:3, :3] = self.space_3d.camera.direction.T[:3, :3]
            if self.axis_3d.vertices_on_screen.any():
                label_matrix = self.axis_3d.vertices_on_screen
                label_matrix[:, 0] = 0.5+(label_matrix[:, 0]+1)/2 * 0.5
                label_matrix[:, 1] = (-label_matrix[:, 1]+1)/2*0.8

                _, x_txt_pos, y_txt_pos, t_txt_pos = label_matrix
                self.X_txt.set_pos(x_txt_pos)
                self.Y_txt.set_pos(y_txt_pos)
                self.T_txt.set_pos(t_txt_pos)

            x, y, t = self.get_arr_rel_robot_pos()
            self.map_editor.set_robot_pos([-x, -y])
            self.robot_3D_dot.vertices = np.array([(-x + self.path_orig[0], -y + self.path_orig[1], t, 1)])
            if not self.drive:
                self.time_from_start = time.time()
            if self.rrt:
                if not self.rrt.dist_reached:
                    self.draw_tree()
                else:
                    last_node = sorted(self.rrt.path_ends, key=lambda x: self.rrt.graph[x].pos[-1])[0]
                    self.graph_sprite.path_end_node = last_node
                    self.draw_clear_path()
                    self.graph_sprite.draw_tree = False
            self.screen.step()
        self.screen.end()

    def curr_time(self):
        return time.time() - self.time_from_start

    def start_travelling_path(self, *args, **kwargs):
        if self.drive:
            return
        self.rrt.force_stop = True
        self.drive = True
        self.map_editor.draw_robot = True
        self.path_travaler = thr.Thread(target=self.travel_path)
        self.path_travaler.start()

    def get_rel_robot_pos(self):
        curr_x, curr_y, curr_a = self.robot.increment

        return curr_x - self.start_pos[0], curr_y - self.start_pos[1], curr_a - self.start_pos[2]

    def get_arr_rel_robot_pos(self):
        x, y, _ = self.get_rel_robot_pos()
        return x * self.discrete, y * self.discrete, self.curr_time()

    def get_rel_goal(self, point_ind):
        print("p i", point_ind)
        print(self.rrt.path)
        print(self.path_orig)
        x = (self.rrt.path[-point_ind][0] - self.path_orig[0]) / self.discrete
        y = (self.rrt.path[-point_ind][1] - self.path_orig[1]) / self.discrete
        t = self.rrt.path[-point_ind][2]
        return x, y, t

    def travel_path(self):
        prec = 0.2
        k = 3
        self.start_pos = self.robot.increment
        self.time_from_start = time.time()
        path = self.rrt.get_path()
        for goal in path[::-1]:
            print(goal, self.path_orig)
            robot_goal = (-goal[0] + self.path_orig[0]) / self.discrete, (-goal[1] + self.path_orig[1]) / self.discrete
            x, y = robot_goal

            while True:
                inc = self.get_rel_robot_pos()

                loc_x = x - inc[0]
                loc_y = y - inc[1]
                dist = math.sqrt(loc_x ** 2 + loc_y ** 2)
                initial_speed = dist / (goal[2] - self.curr_time())
                if (goal[2] - self.curr_time()) < 0:
                    break
                if dist < prec:
                    print("reached")
                    break
                fov_speed = loc_x * initial_speed * k
                side_speed = -loc_y * initial_speed * k
                self.robot.move_base(fov_speed, side_speed, 0)
                time.sleep(1 / 100)

        self.robot.move_base(0, 0, 0)
        time.sleep(0.1)
        self.robot.move_base(0, 0, 0)
        time.sleep(1)
        self.robot.move_base(0, 0, 0)
        print("end drive")
        # self.drive = False

    def draw_clear_path(self):
        nodes = []
        edges = []
        color_edges = []
        p = self.rrt.get_path()
        path, lens = p, [len(p)]
        if path:
            for i, pos in enumerate(path):
                nodes.append(np.array([*pos, 1]))
                edges.append([i, i + 1])
            edges = edges[:-1]
            vert_col = [[255, 255, 255] for _ in range(len(nodes))]
            vert_rad = [*[0] * len(nodes)]
            edges_thickness = [*[5] * len(edges)]
            for i in range(len(lens)):
                if i >= len(self.path_colors):
                    self.path_colors.append([random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])
                color_edges += [*[self.path_colors[i] for _ in range(lens[i])]]
            self.tree_3d_graphics.vertex_colors = np.array(vert_col).astype(np.int32)
            self.tree_3d_graphics.vertex_radius = np.array(vert_rad).astype(np.int16)
            self.tree_3d_graphics.vertices = np.array(nodes)
            self.tree_3d_graphics.edges_thickness = np.array(edges_thickness).astype(np.int16)
            self.tree_3d_graphics.color_edges = np.array(color_edges).astype(np.int32)
            self.tree_3d_graphics.edges = np.array(edges).astype(np.int32)

    def draw_tree(self):
        nodes = []
        edges = []
        self.rrt.step_lock.acquire()
        for j in range(len(self.rrt.graph)):
            nodes.append(np.array([*self.rrt.graph[j].pos, 1]).astype(float_bit))
            if not self.rrt.graph[j].parent:
                continue
            n = self.rrt.graph[j].parent.index
            if n != None:
                edges.append(np.array([j, n]).astype(np.int32))
        path_len = 1
        self.rrt.step_lock.release()
        path_len -= 1
        other_edges = len(edges) - path_len

        vert_col = [*[[0, 255, 0] for _ in range(self.orig_len)],
                    *[[0, 0, 255] for _ in range(self.end_len)],
                    *[[255, 255, 255] for _ in range(len(nodes) - self.orig_len - self.end_len)]
                    ]
        self.tree_3d_graphics.vertex_colors = np.array(vert_col).astype(np.int32)

        vert_rad = [*[5] * self.orig_len, *[5] * self.end_len, *[0] * (len(nodes) - self.orig_len - self.end_len), ]
        self.tree_3d_graphics.vertex_radius = np.array(vert_rad).astype(np.int16)
        self.tree_3d_graphics.vertices = np.array(nodes)

        self.tree_3d_graphics.edges_thickness = np.array([*[1] * other_edges, *[5] * path_len]).astype(np.int16)
        self.tree_3d_graphics.color_edges = np.array(
            [*[[255, 255, 255] for _ in range(other_edges)], *[[255, 0, 0] for _ in range(path_len)]]).astype(np.int32)
        self.tree_3d_graphics.edges = np.array(edges).astype(np.int32)


rrt_sim = RRT_sim()
rrt_sim.main_thr()
