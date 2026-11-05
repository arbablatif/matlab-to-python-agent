% plotting.m
% Two-panel figure saved to PNG, plus a few numeric summaries.
% Written from scratch for the matlab-to-python-agent demo (public, no client data).

x  = linspace(0, 2*pi, 200);
y1 = sin(x);
y2 = cos(x);
y3 = sin(x) .* exp(-x/3);

fig = figure('Visible', 'off');
subplot(2, 1, 1);
plot(x, y1, 'b-', x, y2, 'r--');
legend('sin', 'cos');
title('Trigonometric functions');
grid on;

subplot(2, 1, 2);
plot(x, y3, 'k', 'LineWidth', 1.5);
xlabel('x'); ylabel('y');
title('Damped sine');

saveas(fig, 'plotting_output.png');

area_y3      = trapz(x, y3);
[ymax, imax] = max(y3);
x_at_max     = x(imax);
zero_cross   = sum(abs(diff(sign(y2))) > 0);
