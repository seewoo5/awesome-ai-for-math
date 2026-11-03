
To contribute, add one or more rows to the table of `README.md`.

- Include a link to the paper in the title column as `[TITLE](LINK)`. If the paper is published, add the official link.
- Add subject(s). These could be topics (e.g., number theory, geometry, mathematical physics, etc.) or methodologies (e.g., RL, LLM, decision tree, etc.). If a tag already exists, use the exact same name. Add subjects as plain text separated by commas (for example: `Number Theory, LLM`).
- For papers that use LLMs, pick one LLM tag based on what the paper says about its AI use:
  - `LLM (major)`: the core results were essentially produced by AI autonomously; the authors' work was mainly posing the problem, verifying, and writing it up as a proper paper.
  - `LLM (minor)`: humans drove the research, but AI proved nontrivial lemmas or intermediate steps (or supplied key ideas or constructions for part of the argument).
  - `LLM (tool)`: papers about LLMs for mathematics with no AI-attributed new result (benchmarks, surveys, prover systems).
  - If an LLM-based system wrote the formal (e.g. Lean) proofs, tag `LLM (minor)` together with `ATP`.
  - Papers that used AI only for proofreading, grammar, literature search, or finding minor errors are out of scope.
- Add venue and year. arXiv is fine if it is not published.
- Add additional links, such as (official) blog posts, articles, code, or chat logs. Add "Unofficial" if the code or blog is not an official resource.
- Use `Code` only for actual executable code or formal artifacts (e.g. Python, Lean, notebooks with runnable verification code). If the release is only prompts, responses, transcripts, or similar conversation records, label it `Chat Logs` instead.
- Use the project-only Codex and Claude skills when they are helpful. For Codex, run `$awesome-ai-for-math-paper [paper link]`; for Claude, run `/awesome-ai-for-math-paper [paper link]`.
- The rows will be automatically sorted by title in alphabetical order when a PR is merged to the main branch.
