% signal_filtering.m
% Low-pass filtering of a noisy signal with a 4th-order Butterworth filter.
% Written from scratch for the matlab-to-python-agent demo (public, no client data).

fs = 1000;                         % sampling rate (Hz)
t  = 0:1/fs:1-1/fs;                % 1 second of samples (row vector)

clean = sin(2*pi*5*t);             % 5 Hz signal we want to keep
noise = 0.5*sin(2*pi*120*t) + 0.2*cos(2*pi*250*t);   % deterministic "noise"
x = clean + noise;

fc = 20;                           % cutoff frequency (Hz)
[b, a] = butter(4, fc/(fs/2));     % normalised cutoff in (0, 1)

y_causal = filter(b, a, x);        % one-pass (causal) filter -> phase lag
y        = filtfilt(b, a, x);      % zero-phase forward-backward filter

rms_error   = sqrt(mean((y - clean).^2));
max_dev     = max(abs(y - clean));
lag_samples = finddelay(clean, y_causal);
