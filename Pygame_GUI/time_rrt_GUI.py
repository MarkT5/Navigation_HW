from Pygame_GUI.Screen import Screen
from Pygame_GUI.Space3D.Space3D import Space3D
from Pygame_GUI.Space3D.object_3d import *
from Pygame_GUI.Sprites.Objects import *
from pathfinding.multiple_tree_control import MultiTree
import time
from Pygame_GUI.Sprites.map_editor import MapEditor
import random


class TimeRrtGui:
    def __init__(self, width, height):
        self.map_shape = (30, 30, 100)
        self.width, self.height = width, height
        self.screen = Screen(2000, 1250)
        self.screen.init()
        self.enable_3d = True
        if self.enable_3d:
            self.space_3d = self.screen.sprite(Space3D, "Space3D", x=0.5, y=0, width=0.5, height=0.8)
            self.cube = (self.space_3d, [*np.array([(-1, -1, -1, 2), (1, -1, -1, 2), (-1, 1, -1, 2), (-1, -1, 1, 2),
                                                    (1, 1, -1, 2), (1, -1, 1, 2),
                                                    (-1, 1, 1, 2), (1, 1, 1, 2)]) / 2],
                         [[0, 1, 4, 2][::-1], [3, 6, 7, 5][::-1], [0, 3, 5, 1][::-1], [2, 4, 7, 6][::-1],
                          [1, 5, 7, 4][::-1], [2, 6, 3, 0][::-1]])
            self.map3d = Solid3D(*self.cube)
            self.space_3d.add_object(self.map3d)

        self.map_editor = self.screen.sprite(MapEditor, "MapEditor", x=0.0, y=0, width=0.5, height=0.8,
                                             color=(255, 255, 255), map_shape=self.map_shape)
        # self.map_editor.update_map = self.export_3d
        self.screen.sprite(Button, "change_cam_mode", x=0.93, y=0.01, width=0.06, height=0.12, color=(150, 255, 170),
                           func=self.change_cam_mode)
        self.screen.sprite(Button, "input_TTL", x=0.03, y=0.82, width=0.06, height=0.08, color=(150, 255, 170),
                           func=self.map_editor.input_ttl, image="Pygame_GUI/sprite_images/TTL2.png")
        self.screen.sprite(Button, "export_3d", x=0.1, y=0.82, width=0.06, height=0.08, color=(150, 255, 170),
                           func=self.export_3d, image="Pygame_GUI/sprite_images/refresh_3d.png")
        self.screen.sprite(Button, "set_origin", x=0.17, y=0.82, width=0.06, height=0.04, color=(0, 255, 0),
                           func=self.map_editor.set_mode_origin)
        self.screen.sprite(Button, "set_point", x=0.24, y=0.82, width=0.06, height=0.04, color=(0, 0, 255),
                           func=self.map_editor.set_mode_point)
        self.screen.sprite(Button, "set_wall", x=0.31, y=0.82, width=0.06, height=0.04, color=(132, 31, 39),
                           func=self.map_editor.set_mode_wall)
        self.screen.sprite(Button, "run_rrt", x=0.38, y=0.82, width=0.06, height=0.08, color=(255, 0, 255),
                           func=self.run_rrt, image="Pygame_GUI/sprite_images/pathfinding.png")
        self.btn_3d = self.screen.sprite(Button, "disable_3d", x=0.45, y=0.82, width=0.06, height=0.08,
                                         color=(255, 0, 255),
                                         func=self.disable_3d, image=(
            "Pygame_GUI/sprite_images/no_3d.png", "Pygame_GUI/sprite_images/3d.png"))

        # self.screen.sprite(Text, "input_TTL_label", x=0.03, y=0.86, inp_text=lambda: "input_TTL", font='serif',
        #                   font_size=10)
        # self.screen.sprite(Text, "export_3d_label", x=0.1, y=0.86, inp_text=lambda: "export_3d", font='serif',
        #                   font_size=10)
        self.screen.sprite(Text, "set_origin_label", x=0.17, y=0.86, inp_text=lambda: "set_origin", font='serif',
                           font_size=10)
        self.screen.sprite(Text, "set_point_label", x=0.24, y=0.86, inp_text=lambda: "set_point", font='serif',
                           font_size=10)
        self.screen.sprite(Text, "set_wall_label", x=0.31, y=0.86, inp_text=lambda: "set_wall", font='serif',
                           font_size=10)
        # self.screen.sprite(Text, "run_rrt_label", x=0.38, y=0.86, inp_text=lambda: "run_rrt", font='serif',
        #                   font_size=10)
        # self.screen.sprite(Text, "disable_3d_label", x=0.45, y=0.86, inp_text=lambda: "disable_3d", font='serif',
        #                   font_size=10)
        self.screen.sprite(Slider, "curr_time", min=0, max=self.map_shape[-1] - 1, x=0.03, y=0.91,
                           width=0.47, height=0.05, color=(150, 160, 170),
                           func=self.screen["MapEditor"].change_curr_time)

        self.old_pressed_keys = []
        self.old_mouse_pos = [0, 0]
        self.screen.add_fps_indicator()
        self.path_colors = []

        self.multi_tree_running = False

        self.bin_map = np.zeros(self.map_shape).astype(np.uint8)

    def export_3d(self, *arg, **kwargs):
        self.screen["MapEditor"].update_map()
        if self.multi_tree_running:
            del self.multi_tree
        self.multi_tree_running = False
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
        self.space_3d.all_obj = []
        map3d = Solid3D(self.space_3d, vertices, edges, pos=(-16.5, -16.5, -51.5))
        self.space_3d.add_object(map3d)
        self.map3d.draw_faces = True

    def disable_3d(self, *args, **kwargs):
        self.btn_3d.curr_img = not self.btn_3d.curr_img
        self.space_3d.enable = not self.space_3d.enable

    def run_rrt(self, *args, **kwargs):
        if self.multi_tree_running:
            del self.multi_tree
            self.multi_tree_running = False
        self.export_3d()
        points = [i[1] for i in sorted(self.map_editor.points.items(), key=lambda x:x[0])]
        self.multi_tree = MultiTree(points, self.bin_map)
        if self.enable_3d:
            self.multi_tree_3d_graphics = Hollow3D(self.space_3d, [[0.0, 0.0, 0.0, 1.0],
                                                                   [0.0, 0.0, 0.0, 1.0]],
                                                   [[0, 0]], edges_thickness=[1])
            self.multi_tree_3d_graphics.translate((-15, -15, -50))
            self.space_3d.add_object(self.multi_tree_3d_graphics)
        t = time.time()
        self.multi_tree.start_thread()
        # print(time.time() - t)
        self.multi_tree_running = True

    def run(self):
        i = 0
        t = time.time()
        while self.screen.running:
            self.screen.step()
            if self.multi_tree_running and self.enable_3d and self.space_3d.enable:
                self.draw_clear_path()
        self.multi_tree.print_report()

    def draw_clear_path(self):
        nodes = []
        edges = []
        vert_col = []
        vert_rad = []
        edges_thickness = []
        color_edges = []
        path, lens = self.multi_tree.get_path()
        if path:
            for i, pos in enumerate(path):
                nodes.append(np.array([*pos, 1]))
                edges.append([i, i+1])
            edges = edges[:-1]
            vert_col = [[255, 255, 255] for _ in range(len(nodes))]
            vert_rad = [*[0] * len(nodes)]
            edges_thickness = [*[5] * len(edges)]
            for i in range(len(lens)):
                if i >= len(self.path_colors):
                    self.path_colors.append([random.randint(0,255),random.randint(0,255),random.randint(0,255)])
                color_edges += [*[self.path_colors[i] for _ in range(lens[i])]]
            self.multi_tree_3d_graphics.vertex_colors = np.array(vert_col).astype(np.int32)
            self.multi_tree_3d_graphics.vertex_radius = np.array(vert_rad).astype(np.int16)
            self.multi_tree_3d_graphics.vertices = np.array(nodes)
            self.multi_tree_3d_graphics.edges_thickness = np.array(edges_thickness).astype(np.int16)
            self.multi_tree_3d_graphics.color_edges = np.array(color_edges).astype(np.int32)
            self.multi_tree_3d_graphics.edges = np.array(edges).astype(np.int32)


    def draw_tree(self):
        nodes = []
        for j in range(self.multi_tree.graph.nodes.shape[0]):
            nodes.append(np.array([*self.multi_tree.graph.nodes[j], 1]).astype(float_bit))
        edges = []
        path_len = 1
        for i in range(1, self.multi_tree.graph.node_num - 1):
            if not self.multi_tree.graph[i].parent:
                continue
            n = self.multi_tree.graph[i].parent.index
            if n != None:
                edges.append(np.array([i, n]).astype(np.int32))
        if self.multi_tree.dist_reached:
            self.multi_tree.get_path()
            path_len = len(self.multi_tree.path_ind)
            edges += [np.array([self.multi_tree.path_ind[p], self.multi_tree.path_ind[p + 1]]).astype(np.int32) for p in
                      range(path_len - 1)]

        path_len -= 1
        other_edges = len(edges) - path_len

        vert_col = [*[[0, 255, 0] for _ in range(self.orig_len)],
                    *[[0, 0, 255] for _ in range(self.end_len)],
                    *[[255, 255, 255] for _ in range(len(nodes) - self.orig_len - self.end_len)]
                    ]
        self.multi_tree_3d_graphics.vertex_colors = np.array(vert_col).astype(np.int32)

        vert_rad = [*[5] * self.orig_len, *[5] * self.end_len, *[0] * (len(nodes) - self.orig_len - self.end_len), ]
        self.multi_tree_3d_graphics.vertex_radius = np.array(vert_rad).astype(np.int16)
        self.multi_tree_3d_graphics.vertices = np.array(nodes)

        self.multi_tree_3d_graphics.edges_thickness = np.array([*[1] * other_edges, *[5] * path_len]).astype(np.int16)
        self.multi_tree_3d_graphics.color_edges = np.array(
            [*[[255, 255, 255] for _ in range(other_edges)], *[[255, 0, 0] for _ in range(path_len)]]).astype(np.int32)
        self.multi_tree_3d_graphics.edges = np.array(edges).astype(np.int32)

    def change_cam_mode(self, *args, **kwargs):
        self.space_3d.camera.mode = not self.space_3d.camera.mode
        self.space_3d.camera.reset()


trgui = TimeRrtGui(WIDTH, HEIGHT)
trgui.run()
