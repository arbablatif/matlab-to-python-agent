"""The convert -> test -> retry loop.

    attempt 1: prompt = MATLAB source + mapping hints
    test     : generated pytest compares outputs with MATLAB reference values
    attempt n: prompt += previous code + exact test failures   (max_attempts total)
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .converter import SYSTEM_PROMPT, build_prompt, build_retry_prompt, extract_code
from .llm import LLMClient
from .mappings import find_matlab_functions, missing_mapping_comments
from .tester import run_smoke, run_test, write_test

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


@dataclass
class Attempt:
    number: int
    passed: bool
    n_tests: int
    n_failed: int
    failures: list[str]
    cached: bool  # True = no API cost (cache hit or mock)


@dataclass
class ConversionReport:
    name: str
    mode: str            # "reference" (numerical tests) or "smoke" (runs-only)
    provider: str
    model: str
    passed: bool
    attempts: list[Attempt] = field(default_factory=list)
    matlab_functions: list[str] = field(default_factory=list)
    missing_comments: list[str] = field(default_factory=list)
    python_path: str = ""
    test_path: str = ""
    seconds: float = 0.0

    @property
    def n_attempts(self) -> int:
        return len(self.attempts)

    @property
    def comment_coverage(self) -> float:
        if not self.matlab_functions:
            return 1.0
        return 1 - len(self.missing_comments) / len(self.matlab_functions)

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("python_path", "test_path"):  # repo-relative paths: no local paths in reports
            if d[k] and Path(d[k]).is_relative_to(ROOT):
                d[k] = Path(d[k]).relative_to(ROOT).as_posix()
        d.update(n_attempts=self.n_attempts, comment_coverage=round(self.comment_coverage, 3))
        return d


def load_spec(name: str) -> dict | None:
    """Spec (outputs to compare, tolerances) for a bundled sample, if any."""
    specs = json.loads((SAMPLES / "specs.json").read_text())
    return specs.get(name)


def convert_file(m_path: Path, client: LLMClient, out_root: Path = ROOT / "out",
                 reference_path: Path | None = None, spec: dict | None = None,
                 max_attempts: int = 3, log=print) -> ConversionReport:
    """Convert one .m file, test it, and retry on failure. Writes into out_root/<name>/."""
    t0 = time.time()
    name = m_path.stem
    matlab_src = m_path.read_text(encoding="utf-8")
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Locate reference outputs + spec (bundled samples have both).
    reference_path = reference_path or (SAMPLES / "references" / f"{name}.json")
    if spec is None and reference_path.exists():
        spec = load_spec(name) or {
            "outputs": [k for k in json.loads(reference_path.read_text()) if not k.startswith("x__")]}
    has_reference = reference_path.exists() and spec is not None

    py_path = out_dir / f"{name}.py"
    test_path = write_test(out_dir, name, spec, reference_path) if has_reference else None
    funcs = find_matlab_functions(matlab_src)
    report = ConversionReport(name, "reference" if has_reference else "smoke",
                              client.provider, client.model, False, matlab_functions=funcs,
                              python_path=str(py_path), test_path=str(test_path or ""))

    prompt = build_prompt(matlab_src, m_path.name)
    code = ""
    for attempt in range(1, max_attempts + 1):
        reply = client.complete(SYSTEM_PROMPT, prompt, mock_key=(name, attempt))
        code = extract_code(reply.text)
        py_path.write_text(code, encoding="utf-8")
        (out_dir / f"attempt_{attempt}.py").write_text(code, encoding="utf-8")

        result = run_test(test_path) if has_reference else run_smoke(py_path)
        report.attempts.append(Attempt(attempt, result.passed, result.n_tests, result.n_failed,
                                       result.failures, reply.cached))
        status = "PASS" if result.passed else f"FAIL ({result.n_failed}/{result.n_tests} checks)"
        log(f"[{name}] attempt {attempt}: {status}{' (mock)' if client.mock else (' (cached)' if reply.cached else '')}")
        for f in result.failures[:5]:
            log(f"    - {f[:160]}")
        if result.passed:
            report.passed = True
            break
        prompt = build_retry_prompt(matlab_src, m_path.name, code, result.report())

    report.missing_comments = missing_mapping_comments(code, funcs)
    report.seconds = round(time.time() - t0, 1)
    (out_dir / "report.json").write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
