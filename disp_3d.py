import csv

from Pygame_GUI.Screen import Screen
from Pygame_GUI.Space3D.Space3D import Space3D
from Pygame_GUI.Space3D.object_3d import *
from Pygame_GUI.Sprites.Objects import *

screen = Screen(1100, 900)
screen.init()
space_3d = screen.sprite(Space3D, "Space3D", x=0, y=0, width=1, height=1)
cube_vert = np.array([(-1, -1, -1, 2), (1, -1, -1, 2), (-1, 1, -1, 2), (-1, -1, 1, 2),
                      (1, 1, -1, 2), (1, -1, 1, 2),
                      (-1, 1, 1, 2), (1, 1, 1, 2)]) / 2
cube_vert[:, 0] *= 20
cube_vert[:, 1] *= 10
cube_dummy = (space_3d, [*cube_vert],
              [[0, 1, 4, 2][::-1], [3, 6, 7, 5][::-1], [0, 3, 5, 1][::-1], [2, 4, 7, 6][::-1],
               [1, 5, 7, 4][::-1], [2, 6, 3, 0][::-1]])

cube = Solid3D(*cube_dummy)
space_3d.add_object(cube)

t_a = []
t_g = []
accel = {"x": [], "y": [], "z": []}
gyro = {"x": [], "y": [], "z": []}
with open('data\\Gyroscope.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        t_g.append(float(row["seconds_elapsed"]))
        gyro["x"].append(float(row["x"]))
        gyro["y"].append(float(row["y"]))
        gyro["z"].append(float(row["z"]))
with open('data\\Accelerometer.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        t_a.append(float(row["seconds_elapsed"]))
        accel["x"].append(float(row["x"]))
        accel["y"].append(float(row["y"]))
        accel["z"].append(float(row["z"]))

counter = 1
k = 20/15*100
while screen.running:
    if counter >= len(gyro["x"]):
        counter = 1
    screen.step()
    dt = t_g[counter]-t_g[counter-1]
    cube.rotate_x(gyro["x"][counter]*dt)
    cube.rotate_y(gyro["y"][counter]*dt)
    cube.rotate_z(gyro["z"][counter]*dt)
    cube.translate((accel["x"][counter]*dt*dt*k, accel["y"][counter]*dt*dt*k, accel["z"][counter]*dt*dt*k))
    counter += 1
