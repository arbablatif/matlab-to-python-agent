"""Prompt construction and code extraction for MATLAB -> Python conversion."""
from __future__ import annotations

import re

from .mappings import find_matlab_functions, mapping_hints

SYSTEM_PROMPT = """You are an expert at porting MATLAB code to idiomatic Python
using NumPy, SciPy and Matplotlib. You produce a single runnable Python script.

Rules:
1. Keep every top-level MATLAB variable name identical in Python, so results can
   be compared numerically variable by variable.
2. After every line that uses a MATLAB built-in, add a comment of the form
   `# MATLAB: <matlab_function> -> <python_equivalent>`.
3. Translate 1-based to 0-based indexing carefully; `end` -> -1 or len().
   MATLAB is column-major: use order='F' for reshape / (:) flattening.
4. Preserve shapes as 1-D NumPy arrays for MATLAB row/column vectors unless a
   2-D shape is required for the maths.
5. Values returned as MATLAB indices (from max/find/...) used as *data* must stay
   meaningful: convert indices only where they index arrays.
6. Use `import matplotlib.pyplot as plt`; never call plt.show().
7. Reply with ONLY one ```python code block, no explanation outside it."""


def build_prompt(matlab_src: str, filename: str) -> str:
    """First-attempt prompt: source plus mapping hints for the functions it uses."""
    funcs = find_matlab_functions(matlab_src)
    hints = mapping_hints(funcs) or "(none detected)"
    return (f"Convert this MATLAB file ({filename}) to Python.\n\n"
            f"Relevant function mappings and gotchas:\n{hints}\n\n"
            f"MATLAB source:\n```matlab\n{matlab_src}\n```")


def build_retry_prompt(matlab_src: str, filename: str, previous_code: str, failure_report: str) -> str:
    """Retry prompt: original source, the failing Python, and the test failures."""
    return (build_prompt(matlab_src, filename)
            + "\n\nYour previous conversion FAILED the numerical tests against outputs "
              "saved from real MATLAB.\n\nPrevious Python:\n```python\n"
            + previous_code
            + "\n```\n\nTest failures:\n```\n"
            + failure_report
            + "\n```\n\nFix the root cause (indexing, column-major order, function defaults, "
              "padding conventions, ...) and return the full corrected script.")


def extract_code(reply: str) -> str:
    """Pull the Python code block out of an LLM reply (or use the whole reply)."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", reply, flags=re.DOTALL)
    code = max(blocks, key=len) if blocks else reply
    return code.strip() + "\n"
