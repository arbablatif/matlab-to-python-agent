"""fft_analysis.py - converted from fft_analysis.m

Single-sided amplitude spectrum and peak detection with the FFT.
"""
import numpy as np
from scipy import signal

fs = 500                                    # sampling rate (Hz)
N = 1000                                    # number of samples
t = np.arange(N) / fs                       # MATLAB: (0:N-1)/fs -> np.arange(N)/fs

x = 1.0 * np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t) + 0.25 * np.cos(2 * np.pi * 200 * t)  # MATLAB: sin, cos -> np.sin, np.cos

X = np.fft.fft(x)                           # MATLAB: fft -> np.fft.fft
P2 = np.abs(X / N)                          # MATLAB: abs -> np.abs (two-sided spectrum)
P1 = P2[: N // 2 + 1].copy()                # MATLAB: P2(1:N/2+1) -> P2[:N//2+1]
P1[1:-1] = 2 * P1[1:-1]                     # MATLAB: P1(2:end-1) -> P1[1:-1]
f = fs * np.arange(N // 2 + 1) / N          # MATLAB: fs*(0:(N/2))/N

idx = int(np.argmax(P1))                    # MATLAB: [~, idx] = max(P1) -> np.argmax (0-based)
peak_freq = f[idx]

locs, props = signal.find_peaks(P1, height=0.1)  # MATLAB: findpeaks(...,'MinPeakHeight',0.1) -> scipy.signal.find_peaks(height=0.1)
pk = props["peak_heights"]
peak_freqs = f[locs]

total_power = np.sum(x ** 2) / N                  # MATLAB: sum -> np.sum
spectral_power = np.sum(np.abs(X) ** 2) / N ** 2  # MATLAB: sum, abs -> np.sum, np.abs (Parseval)
