import csv
import numpy as np

from matplotlib import pyplot as plt

t = []
accel = {"x": [], "y": [], "z": []}
gyro = []
with open('data\\Gyroscope.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        t.append(float(row["seconds_elapsed"]))
        accel["x"].append(float(row["x"]))
        accel["y"].append(float(row["y"]))
        accel["z"].append(float(row["z"]))



plt.plot(t, accel["x"], label="x")
plt.plot(t, accel["y"], label="y")
plt.plot(t, accel["z"], label="z")
print(t)
plt.xticks(np.arange(round(t[0]), round(t[-1])), np.arange(round(t[0]), round(t[-1])))
plt.xlabel("time, s")
plt.ylabel("acceleration, m/s^2")
plt.legend()
plt.show()
