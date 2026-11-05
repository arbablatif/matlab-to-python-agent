% fft_analysis.m
% Single-sided amplitude spectrum and peak detection with the FFT.
% Written from scratch for the matlab-to-python-agent demo (public, no client data).

fs = 500;                          % sampling rate (Hz)
N  = 1000;                         % number of samples
t  = (0:N-1)/fs;

x = 1.0*sin(2*pi*50*t) + 0.5*sin(2*pi*120*t) + 0.25*cos(2*pi*200*t);

X  = fft(x);
P2 = abs(X/N);                     % two-sided spectrum
P1 = P2(1:N/2+1);                  % keep DC .. Nyquist
P1(2:end-1) = 2*P1(2:end-1);       % fold negative frequencies in
f  = fs*(0:(N/2))/N;               % frequency axis (Hz)

[~, idx]  = max(P1);
peak_freq = f(idx);                % strongest component

[pk, locs] = findpeaks(P1, 'MinPeakHeight', 0.1);
peak_freqs = f(locs);

total_power    = sum(x.^2)/N;      % time-domain power
spectral_power = sum(abs(X).^2)/N^2;   % Parseval check
