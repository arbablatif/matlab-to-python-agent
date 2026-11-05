# LEARNING: How this project works, in plain language

## 1. Why "looks right" is not enough
When code is translated between languages, the dangerous bugs don't crash anything. The program runs and prints numbers that are slightly wrong. Two real examples from this repo:

- **Column-major order.** MATLAB fills matrices column by column, and NumPy fills them row by row. `reshape(1:12, 3, 4)` therefore gives a different matrix in each language unless you pass `order='F'` to NumPy. Nothing errors. The values are just in the wrong places.
- **Edge padding in `filtfilt`.** MATLAB and SciPy both pad the signal before filtering it forwards and backwards, but SciPy pads one sample more. The middle of the signal is identical, while the edges differ by about 5%. A reviewer reading the code would never notice.

**Client talking point:** "We don't trust a translation until it reproduces the original MATLAB numbers."

## 2. Reference outputs, or "golden files"
We run each MATLAB script once and save the variables we care about to a JSON file. That file is the answer key. The Python translation passes only if it reproduces every value within a tolerance. Software testers call these *golden files*, or *characterization tests*: they pin down what the existing system actually does, without arguing about what it should do.

## 3. Tolerances
Computers round floating-point numbers slightly differently depending on the order of operations, so we never test for exact equality. `np.allclose(got, expected, rtol=1e-6, atol=1e-9)` means "equal to about 6 significant digits, with tiny values treated as zero". Some variables get looser tolerances on purpose. For example, two adaptive ODE solvers that take different internal steps will agree to about 7 digits, not 15.

## 4. The agent loop: generate → test → repair
An "agent" here is simply an LLM inside a loop that has a way to check its own work:

1. Ask the LLM for a translation.
2. Run the automatic test.
3. If the test fails, show the LLM *exactly* what failed, for example "B: expected [1 4 7 10], got [1 2 3 4]", and ask it to fix the code.
4. Stop when the test passes or after 3 attempts.

The key design choice is that the feedback is **specific and numerical**. "It's wrong" gives the model nothing to work with. "These values came out transposed" points it straight at the column-major bug.

## 5. Targeted hints (a lightweight form of retrieval)
`mappings.py` is a hand-written table of MATLAB functions, their Python equivalents and their known pitfalls. Before calling the LLM, we scan the script for functions that appear in the table and add only those rows to the prompt. That keeps prompts short and cheap, and it works. In the live run, Gemini got the `filtfilt` padding right on its first try because the hint warned about it. For a table this small, sending the matching rows is enough, so this project uses no embeddings or vector search.

## 6. Mapping comments
Every translated line is tagged with a comment such as `# MATLAB: filtfilt -> scipy.signal.filtfilt`. This helps an engineer review the port line by line, and it lets us measure *comment coverage*: the share of MATLAB functions found in the source that have a matching tag.

## 7. Keeping API costs near zero
- **Disk cache:** each prompt is hashed (SHA-256) and the reply is saved under that hash, so asking the same question twice costs nothing. The cache is committed, so anyone can reproduce the published results without an API key.
- **Mock mode:** `--mock` replaces the LLM with pre-written replies. Two of those replies contain deliberate realistic bugs so the retry path is demonstrated. Tests and demos run offline.
- **Bounded loop:** at most N attempts per file. The whole live evaluation used 6 API calls.

## 8. Swappable LLM provider
`llm.py` hides the differences between the Gemini, Anthropic and OpenAI SDKs behind one `complete(system, prompt)` method, so changing provider is a one-line change in `.env`. The default is the cheapest Gemini Flash-Lite model. The original default model was retired during development (the API returned 404 "no longer available"), and the code only needed a one-word change. That shows why the model name belongs in configuration rather than in the code.

## 9. Limitations to be upfront about with clients
- Tests need one MATLAB run per script to create the answer key.
- Random numbers differ between MATLAB and NumPy, so seeds and inputs must be saved.
- Generated code runs on your machine, so use a sandbox when converting untrusted code.
- 5 samples show that the method works. They don't measure accuracy on a real codebase. For a real migration, build a test set from the client's own scripts.
