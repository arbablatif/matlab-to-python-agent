"""Command-line entry point.

    python cli.py samples/fft_analysis.m --mock
    python cli.py my_script.m --reference my_outputs.json --max-attempts 3
"""
import argparse
import sys
from pathlib import Path

from agent.agent import convert_file
from agent.llm import LLMClient


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Convert a MATLAB .m file to tested Python.")
    p.add_argument("matlab_file", type=Path)
    p.add_argument("--reference", type=Path, help="JSON of MATLAB outputs (default: samples/references/<name>.json)")
    p.add_argument("--out", type=Path, default=Path("out"), help="output folder (default: out/)")
    p.add_argument("--max-attempts", type=int, default=3, help="conversion attempts incl. retries (default 3)")
    p.add_argument("--provider", choices=["gemini", "anthropic", "openai"], help="override LLM_PROVIDER")
    p.add_argument("--model", help="override LLM_MODEL")
    p.add_argument("--mock", action="store_true", help="use canned responses: no API calls")
    a = p.parse_args(argv)

    client = LLMClient(a.provider, a.model, mock=a.mock)
    r = convert_file(a.matlab_file, client, a.out.resolve(), a.reference, max_attempts=a.max_attempts)
    print(f"\n{'PASSED' if r.passed else 'FAILED'} after {r.n_attempts} attempt(s) "
          f"[{r.mode} mode, {client.provider}/{client.model}, {client.api_calls} API call(s)]")
    print(f"MATLAB-function comment coverage: {r.comment_coverage:.0%}"
          + (f" (missing: {', '.join(r.missing_comments)})" if r.missing_comments else ""))
    print(f"Python: {r.python_path}\nTest:   {r.test_path or '(smoke run only, no reference)'}")
    return 0 if r.passed else 1


if __name__ == "__main__":
    sys.exit(main())
