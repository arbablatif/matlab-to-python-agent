"""signal_filtering.py - converted from signal_filtering.m

Low-pass filtering of a noisy signal with a 4th-order Butterworth filter.
"""
import numpy as np
from scipy import signal

fs = 1000                                   # sampling rate (Hz)
t = np.arange(0, 1 - 1 / fs + 1e-12, 1 / fs)  # MATLAB: 0:1/fs:1-1/fs -> np.arange (end inclusive)

clean = np.sin(2 * np.pi * 5 * t)           # MATLAB: sin -> np.sin
noise = 0.5 * np.sin(2 * np.pi * 120 * t) + 0.2 * np.cos(2 * np.pi * 250 * t)  # MATLAB: sin, cos -> np.sin, np.cos
x = clean + noise

fc = 20                                     # cutoff frequency (Hz)
b, a = signal.butter(4, fc / (fs / 2))      # MATLAB: butter -> scipy.signal.butter

y_causal = signal.lfilter(b, a, x)          # MATLAB: filter -> scipy.signal.lfilter
# MATLAB pads 3*(max(len(a),len(b))-1) samples; SciPy's default is one sample longer.
y = signal.filtfilt(b, a, x, padlen=3 * (max(len(a), len(b)) - 1))  # MATLAB: filtfilt -> scipy.signal.filtfilt(padlen=...)

rms_error = np.sqrt(np.mean((y - clean) ** 2))  # MATLAB: sqrt, mean -> np.sqrt, np.mean
max_dev = np.max(np.abs(y - clean))             # MATLAB: max, abs -> np.max, np.abs

# MATLAB: finddelay -> scipy.signal.correlate + scipy.signal.correlation_lags
corr = signal.correlate(y_causal, clean, mode="full")
lags = signal.correlation_lags(len(y_causal), len(clean), mode="full")
lag_samples = int(lags[np.argmax(np.abs(corr))])
