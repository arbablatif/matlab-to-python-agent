"""Run the agent on every bundled sample and write a pass-rate table.

    python evaluate.py --mock          # zero API calls
    python evaluate.py                 # real LLM (<= 5 samples x max_attempts calls, all cached)

Writes results/eval_<provider>.json and results/eval_<provider>.md.
"""
import argparse
import json
from pathlib import Path

from agent.agent import ROOT, convert_file
from agent.llm import LLMClient

SAMPLES = ["signal_filtering", "fft_analysis", "matrix_ops", "ode_solving", "plotting"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true")
    p.add_argument("--provider")
    p.add_argument("--model")
    p.add_argument("--max-attempts", type=int, default=3)
    a = p.parse_args()

    client = LLMClient(a.provider, a.model, mock=a.mock)
    reports = [convert_file(ROOT / "samples" / f"{s}.m", client, ROOT / "out" / client.provider,
                            max_attempts=a.max_attempts) for s in SAMPLES]

    n = len(reports)
    first = sum(r.attempts[0].passed for r in reports)
    final = sum(r.passed for r in reports)
    lines = [f"**Provider/model:** `{client.provider}/{client.model}` | max attempts: {a.max_attempts} | "
             f"API calls this run: {client.api_calls}", "",
             "| Sample | Checks | Attempt 1 | Final | Attempts | Comment coverage |",
             "|---|---|---|---|---|---|"]
    for r in reports:
        a1 = r.attempts[0]
        last = r.attempts[-1]
        lines.append(f"| {r.name} | {last.n_tests - last.n_failed}/{last.n_tests} | "
                     f"{'pass' if a1.passed else f'fail ({a1.n_failed})'} | "
                     f"{'**pass**' if r.passed else '**fail**'} | {r.n_attempts} | {r.comment_coverage:.0%} |")
    lines += ["", f"**Pass rate on first attempt: {first}/{n} ({first / n:.0%}) | "
                  f"after retries: {final}/{n} ({final / n:.0%})**"]
    md = "\n".join(lines)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"eval_{client.provider}.md").write_text(md + "\n", encoding="utf-8")
    (out / f"eval_{client.provider}.json").write_text(
        json.dumps([r.to_dict() for r in reports], indent=2), encoding="utf-8")
    print("\n" + md)


if __name__ == "__main__":
    main()
