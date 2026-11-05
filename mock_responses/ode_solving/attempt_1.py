"""ode_solving.py - converted from ode_solving.m

Damped harmonic oscillator x'' + 2*zeta*wn*x' + wn^2*x = 0, solved with a
fixed-step RK4 and with an adaptive RK45 (MATLAB ode45 equivalent).
"""
import numpy as np
from scipy.integrate import solve_ivp

zeta = 0.1
wn = 2 * np.pi


def f(t, y):
    """MATLAB: f = @(t, y) [...] -> Python function returning a 1-D array."""
    return np.array([y[1], -2 * zeta * wn * y[1] - wn ** 2 * y[0]])


y0 = np.array([1.0, 0.0])

# --- fixed-step RK4 ---------------------------------------------------------
h = 0.01
t_rk = np.linspace(0, 5, int(round(5 / h)) + 1)  # MATLAB: 0:h:5 -> np.linspace (avoids float drift of arange)
n = t_rk.size                              # MATLAB: numel -> .size
Y = np.zeros((2, n))                       # MATLAB: zeros -> np.zeros
Y[:, 0] = y0
for k in range(n - 1):                     # MATLAB: for k = 1:n-1 -> range(n-1), 0-based
    tk = t_rk[k]
    yk = Y[:, k]
    k1 = f(tk, yk)
    k2 = f(tk + h / 2, yk + h / 2 * k1)
    k3 = f(tk + h / 2, yk + h / 2 * k2)
    k4 = f(tk + h, yk + h * k3)
    Y[:, k + 1] = yk + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
x_rk4 = Y[0, :]
rk4_end = Y[:, -1]                          # MATLAB: Y(:, end)' -> Y[:, -1]
energy = 0.5 * Y[1, :] ** 2 + 0.5 * wn ** 2 * Y[0, :] ** 2

# --- adaptive RK45 with tight tolerances -----------------------------------
# MATLAB: odeset('RelTol',1e-10,'AbsTol',1e-12) -> solve_ivp(rtol=, atol=)
# MATLAB: ode45 -> scipy.integrate.solve_ivp(method='RK45')
sol = solve_ivp(f, (0, 5), y0, method="RK45", rtol=1e-10, atol=1e-12)
t45, y45 = sol.t, sol.y.T                  # SciPy returns (states, times); MATLAB (times, states)
y45_end = y45[-1, :]

# --- exact solution ---------------------------------------------------------
wd = wn * np.sqrt(1 - zeta ** 2)           # MATLAB: sqrt -> np.sqrt
x_exact = np.exp(-zeta * wn * t_rk) * (np.cos(wd * t_rk) + zeta * wn / wd * np.sin(wd * t_rk))  # MATLAB: exp, cos, sin -> np.exp, np.cos, np.sin
rk4_max_error = np.max(np.abs(x_rk4 - x_exact))  # MATLAB: max, abs -> np.max, np.abs
