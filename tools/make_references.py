"""Regenerate samples/references/*.json by running every sample in real MATLAB.

Requires a local MATLAB (with Signal Processing Toolbox) on PATH. Run once;
the resulting JSON files are committed so nobody else needs MATLAB.

    python tools/make_references.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


def main() -> None:
    specs = json.loads((SAMPLES / "specs.json").read_text())
    calls = []
    for name, spec in specs.items():
        if name.startswith("_"):
            continue
        script = (SAMPLES / f"{name}.m").as_posix()
        out = (SAMPLES / "references" / f"{name}.json").as_posix()
        names = ",".join(f"'{v}'" for v in spec["outputs"])
        calls.append(f"export_reference('{script}', '{out}', {{{names}}});")
    cmd = f"addpath('{(ROOT / 'tools').as_posix()}'); " + " ".join(calls)
    # One MATLAB start-up for all samples (start-up is the slow part).
    subprocess.run(["matlab", "-batch", cmd], check=True)
    print("References written to", SAMPLES / "references")


if __name__ == "__main__":
    main()
