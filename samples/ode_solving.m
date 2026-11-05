% ode_solving.m
% Damped harmonic oscillator  x'' + 2*zeta*wn*x' + wn^2*x = 0
% solved with a hand-written fixed-step RK4 and with ode45.
% Written from scratch for the matlab-to-python-agent demo (public, no client data).

zeta = 0.1;
wn   = 2*pi;
f    = @(t, y) [y(2); -2*zeta*wn*y(2) - wn^2*y(1)];
y0   = [1; 0];

% --- fixed-step RK4 -----------------------------------------------------
h    = 0.01;
t_rk = 0:h:5;
n    = numel(t_rk);
Y    = zeros(2, n);
Y(:, 1) = y0;
for k = 1:n-1
    tk = t_rk(k);
    yk = Y(:, k);
    k1 = f(tk,       yk);
    k2 = f(tk + h/2, yk + h/2*k1);
    k3 = f(tk + h/2, yk + h/2*k2);
    k4 = f(tk + h,   yk + h*k3);
    Y(:, k+1) = yk + h/6*(k1 + 2*k2 + 2*k3 + k4);
end
x_rk4   = Y(1, :);
rk4_end = Y(:, end)';
energy  = 0.5*Y(2, :).^2 + 0.5*wn^2*Y(1, :).^2;

% --- adaptive ode45 with tight tolerances -------------------------------
opts = odeset('RelTol', 1e-10, 'AbsTol', 1e-12);
[t45, y45] = ode45(f, [0 5], y0, opts);
y45_end = y45(end, :);

% --- exact solution for comparison --------------------------------------
wd      = wn*sqrt(1 - zeta^2);
x_exact = exp(-zeta*wn*t_rk) .* (cos(wd*t_rk) + zeta*wn/wd*sin(wd*t_rk));
rk4_max_error = max(abs(x_rk4 - x_exact));
