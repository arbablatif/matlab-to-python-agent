"""Fast tests: no API calls (mock mode + pure functions)."""
import json
from pathlib import Path

import pytest

from agent.agent import ROOT, convert_file
from agent.converter import extract_code
from agent.llm import LLMClient
from agent.mappings import find_matlab_functions, missing_mapping_comments

SAMPLES = ["signal_filtering", "fft_analysis", "matrix_ops", "ode_solving", "plotting"]


def test_find_functions_ignores_comments_and_strings():
    src = "% fft(x) in a comment\ny = filtfilt(b, a, x); legend('max(')\nz = A \\ b;"
    assert find_matlab_functions(src) == ["filtfilt", "legend", "mldivide"]


def test_missing_comments_detected():
    code = "y = np.fft.fft(x)  # MATLAB: fft -> np.fft.fft\n"
    assert missing_mapping_comments(code, ["fft", "abs"]) == ["abs"]


def test_extract_code_from_fenced_reply():
    assert extract_code("Here:\n```python\nx = 1\n```\nbye") == "x = 1\n"


def test_cache_is_used(tmp_path, monkeypatch):
    client = LLMClient("gemini", "test-model", cache_dir=tmp_path)
    monkeypatch.setattr(client, "_call_api", lambda s, p: "reply")
    assert client.complete("sys", "hi").cached is False
    monkeypatch.setattr(client, "_call_api", lambda s, p: pytest.fail("API called despite cache"))
    assert client.complete("sys", "hi").text == "reply"
    assert client.api_calls == 1


@pytest.mark.parametrize("name", SAMPLES)
def test_mock_pipeline_passes_against_matlab_reference(name, tmp_path):
    report = convert_file(ROOT / "samples" / f"{name}.m", LLMClient(mock=True), tmp_path, log=lambda *_: None)
    assert report.passed and report.mode == "reference"
    assert report.missing_comments == []


def test_retry_recovers_from_column_major_bug(tmp_path):
    r = convert_file(ROOT / "samples" / "matrix_ops.m", LLMClient(mock=True), tmp_path, log=lambda *_: None)
    assert [a.passed for a in r.attempts] == [False, True]
    assert any("B:" in f for f in r.attempts[0].failures)
