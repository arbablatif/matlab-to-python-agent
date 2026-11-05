"""Static MATLAB -> Python function mapping table.

Used in two places:
  1. Prompting: only the rows for functions that actually appear in the input
     .m file are added to the LLM prompt (keeps prompts short and cheap).
  2. Verification: after conversion we check that every MATLAB function found
     in the source has a "# MATLAB: <name> -> ..." comment in the Python.
"""
from __future__ import annotations

import re

# name -> (python equivalent, gotcha note shown to the LLM)
MAPPINGS: dict[str, tuple[str, str]] = {
    # --- array construction -------------------------------------------------
    "zeros": ("np.zeros", "pass shape as a tuple: np.zeros((m, n))"),
    "ones": ("np.ones", "pass shape as a tuple"),
    "eye": ("np.eye", ""),
    "linspace": ("np.linspace", "MATLAB default is 100 points, NumPy default 50"),
    "reshape": ("np.reshape", "MATLAB is column-major: use order='F'"),
    "numel": ("np.size / .size", ""),
    "size": ("np.shape", ""),
    "length": ("max(np.shape(a))", ""),
    "repmat": ("np.tile", ""),
    "kron": ("np.kron", ""),
    "diag": ("np.diag", ""),
    # --- math / reductions --------------------------------------------------
    "sum": ("np.sum", "MATLAB sums along dim 1 (columns) for matrices -> axis=0"),
    "cumsum": ("np.cumsum", "cumsum(A, 2) -> np.cumsum(A, axis=1)"),
    "mean": ("np.mean", "default dim 1 -> axis=0 for matrices"),
    "max": ("np.max / np.argmax", "[m, i] = max(v) -> m = v.max(); i = v.argmax() (0-based!)"),
    "min": ("np.min / np.argmin", "index is 0-based in Python"),
    "abs": ("np.abs", ""),
    "sqrt": ("np.sqrt", ""),
    "exp": ("np.exp", ""),
    "sin": ("np.sin", ""),
    "cos": ("np.cos", ""),
    "sign": ("np.sign", ""),
    "diff": ("np.diff", ""),
    "sort": ("np.sort", "returns ascending; [s, i] = sort -> np.sort + np.argsort"),
    "trapz": ("np.trapezoid (NumPy>=2) / scipy.integrate.trapezoid", "argument order is (y, x)"),
    "norm": ("np.linalg.norm", ""),
    # --- linear algebra -----------------------------------------------------
    "inv": ("np.linalg.inv", ""),
    "det": ("np.linalg.det", ""),
    "eig": ("np.linalg.eig / np.linalg.eigh", "eigh for symmetric matrices; ordering may differ"),
    "trace": ("np.trace", ""),
    "mldivide": ("np.linalg.solve", "A \\ b -> np.linalg.solve(A, b)"),
    # --- signal processing --------------------------------------------------
    "fft": ("np.fft.fft", ""),
    "ifft": ("np.fft.ifft", ""),
    "butter": ("scipy.signal.butter", "Wn is normalised to Nyquist, same as MATLAB"),
    "filter": ("scipy.signal.lfilter", "filter(b, a, x) -> lfilter(b, a, x)"),
    "filtfilt": ("scipy.signal.filtfilt",
                 "MATLAB pads 3*(max(len(a),len(b))-1) samples; SciPy default pads "
                 "3*max(len(a),len(b)). Pass padlen=3*(max(len(a),len(b))-1) to match MATLAB"),
    "findpeaks": ("scipy.signal.find_peaks", "returns (indices, props); heights in props['peak_heights']"),
    "finddelay": ("scipy.signal.correlate + scipy.signal.correlation_lags",
                  "finddelay(x, y) is the lag of y relative to x: argmax of correlate(y, x, mode='full')"),
    # --- ODEs ----------------------------------------------------------------
    "ode45": ("scipy.integrate.solve_ivp(method='RK45')", "y is returned as sol.y with shape (n_states, n_times)"),
    "odeset": ("solve_ivp keyword args rtol=, atol=", ""),
    # --- plotting -----------------------------------------------------------
    "figure": ("plt.figure", "'Visible','off' -> just don't call plt.show()"),
    "subplot": ("plt.subplot", "same 1-based panel index as MATLAB"),
    "plot": ("plt.plot / ax.plot", "style strings like 'r--' work unchanged"),
    "legend": ("plt.legend", "pass labels as a list"),
    "title": ("plt.title", ""),
    "xlabel": ("plt.xlabel", ""),
    "ylabel": ("plt.ylabel", ""),
    "grid": ("plt.grid(True)", ""),
    "saveas": ("fig.savefig", ""),
    "disp": ("print", ""),
    "fprintf": ("print with f-string", ""),
}

# Words that look like calls but are language keywords / not worth mapping.
_IGNORE = {"if", "for", "while", "end", "function", "return", "else", "elseif"}


def _strip_comments_and_strings(src: str) -> str:
    """Remove MATLAB % comments and quoted strings so we only scan real code."""
    out = []
    for line in src.splitlines():
        line = re.sub(r"'[^'\n]*'", "''", line)  # 'strings' (crude, fine for scanning)
        line = line.split("%", 1)[0]
        out.append(line)
    return "\n".join(out)


def find_matlab_functions(src: str) -> list[str]:
    """Return the known MATLAB functions used in *src*, in order of first use."""
    code = _strip_comments_and_strings(src)
    found: list[str] = []
    for name in re.findall(r"\b([A-Za-z]\w*)\s*\(", code):
        if name in MAPPINGS and name not in _IGNORE and name not in found:
            found.append(name)
    if "\\" in code and "mldivide" not in found:  # backslash solve operator
        found.append("mldivide")
    return found


def mapping_hints(functions: list[str]) -> str:
    """Format the mapping rows for the given functions as prompt text."""
    rows = []
    for name in functions:
        py, note = MAPPINGS[name]
        rows.append(f"- {name} -> {py}" + (f"  (note: {note})" if note else ""))
    return "\n".join(rows)


def missing_mapping_comments(py_code: str, functions: list[str]) -> list[str]:
    """MATLAB functions that have no '# MATLAB: <name>' comment in the Python."""
    comments = " ".join(re.findall(r"#\s*MATLAB:([^\n]*)", py_code))
    missing = []
    for name in functions:
        if name == "mldivide":  # the "\" operator may be written either way
            ok = "mldivide" in comments or "\\" in comments
        else:
            ok = re.search(rf"\b{re.escape(name)}\b", comments) is not None
        if not ok:
            missing.append(name)
    return missing
