"""Streamlit UI:  streamlit run app.py"""
import json
import tempfile
from pathlib import Path

import streamlit as st

from agent.agent import ROOT, convert_file
from agent.llm import LLMClient

st.set_page_config(page_title="MATLAB to Python Agent", layout="wide")
st.title("MATLAB → Python agent")
st.caption("Converts a .m file to NumPy/SciPy/Matplotlib, tests it against saved MATLAB outputs, "
           "and retries with the test failures if it doesn't match.")

with st.sidebar:
    mock = st.toggle("Mock mode (no API calls)", value=True)
    provider = st.selectbox("Provider", ["gemini", "anthropic", "openai"], disabled=mock)
    max_attempts = st.slider("Max attempts", 1, 5, 3)

samples = sorted(p.stem for p in (ROOT / "samples").glob("*.m"))
source = st.radio("Input", ["Bundled sample", "Upload .m file"], horizontal=True)
ref_path = None
if source == "Bundled sample":
    m_path = ROOT / "samples" / f"{st.selectbox('Sample', samples)}.m"
else:
    up = st.file_uploader("MATLAB script", type=["m"])
    ref_up = st.file_uploader("Optional: reference outputs JSON (variable -> value, e.g. from jsonencode)",
                              type=["json"])
    if up is None:
        st.stop()
    tmp = Path(tempfile.mkdtemp())
    m_path = tmp / up.name
    m_path.write_bytes(up.getvalue())
    if ref_up is not None:
        ref_path = tmp / "reference.json"
        ref_path.write_bytes(ref_up.getvalue())
    elif not mock:
        st.info("No reference given: the result will only be checked to run without errors.")

matlab_src = m_path.read_text(encoding="utf-8")

if st.button("Convert", type="primary"):
    client = LLMClient(provider, mock=mock)
    logs = []
    with st.spinner("Converting and testing..."):
        report = convert_file(m_path, client, ROOT / "out" / "ui", ref_path,
                              max_attempts=max_attempts, log=logs.append)
    (st.success if report.passed else st.error)(
        f"{'PASSED' if report.passed else 'FAILED'} after {report.n_attempts} attempt(s) "
        f"({report.mode} mode, {client.api_calls} API call(s))")
    left, right = st.columns(2)
    left.subheader("MATLAB")
    left.code(matlab_src, language="matlab")
    right.subheader("Python")
    py = Path(report.python_path).read_text(encoding="utf-8")
    right.code(py, language="python")
    right.download_button("Download .py", py, file_name=f"{m_path.stem}.py")
    st.subheader("Attempts")
    for a in report.attempts:
        with st.expander(f"Attempt {a.number}: {'pass' if a.passed else 'fail'} "
                         f"({a.n_tests - a.n_failed}/{a.n_tests} checks)", expanded=not a.passed):
            st.code(Path(report.python_path).with_name(f"attempt_{a.number}.py").read_text(encoding="utf-8"),
                    language="python")
            for f in a.failures:
                st.write("- " + f)
    st.caption(f"MATLAB-function comment coverage: {report.comment_coverage:.0%}")
    img = Path(report.python_path).parent / "plotting_output.png"
    if img.exists() and m_path.stem == "plotting":
        st.image(str(img))
else:
    st.code(matlab_src, language="matlab")
