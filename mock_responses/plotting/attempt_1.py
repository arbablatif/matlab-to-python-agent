"""plotting.py - converted from plotting.m

Two-panel figure saved to PNG, plus a few numeric summaries.
"""
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 200)         # MATLAB: linspace -> np.linspace
y1 = np.sin(x)                             # MATLAB: sin -> np.sin
y2 = np.cos(x)                             # MATLAB: cos -> np.cos
y3 = np.sin(x) * np.exp(-x / 3)            # MATLAB: .* and exp -> * and np.exp

fig = plt.figure()                         # MATLAB: figure('Visible','off') -> plt.figure (no plt.show)
plt.subplot(2, 1, 1)                       # MATLAB: subplot -> plt.subplot
plt.plot(x, y1, "b-", x, y2, "r--")        # MATLAB: plot -> plt.plot
plt.legend(["sin", "cos"])                 # MATLAB: legend -> plt.legend
plt.title("Trigonometric functions")       # MATLAB: title -> plt.title
plt.grid(True)                             # MATLAB: grid on -> plt.grid(True)

plt.subplot(2, 1, 2)                       # MATLAB: subplot -> plt.subplot
plt.plot(x, y3, "k", linewidth=1.5)        # MATLAB: plot(...,'LineWidth',1.5) -> plt.plot(linewidth=1.5)
plt.xlabel("x")                            # MATLAB: xlabel -> plt.xlabel
plt.ylabel("y")                            # MATLAB: ylabel -> plt.ylabel
plt.title("Damped sine")                   # MATLAB: title -> plt.title

fig.savefig("plotting_output.png")         # MATLAB: saveas -> fig.savefig

area_y3 = np.trapezoid(y3, x)              # MATLAB: trapz(x, y3) -> np.trapezoid(y3, x) (note argument order)
imax = int(np.argmax(y3))                  # MATLAB: [ymax, imax] = max(y3) -> np.argmax (0-based)
ymax = y3[imax]
x_at_max = x[imax]
zero_cross = int(np.sum(np.abs(np.diff(np.sign(y2))) > 0))  # MATLAB: sum, abs, diff, sign -> np.sum, np.abs, np.diff, np.sign
