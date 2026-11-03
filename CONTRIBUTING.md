# Contributing

## Where to add papers

All papers live in one markdown table in [`papers.md`](papers.md), between the `<!-- Table start -->` and `<!-- Table end -->` markers. To add a paper, add one row per paper to that table and open a pull request.

Only papers posted on [arXiv](https://arxiv.org) or published in peer-reviewed venues (journals and conference proceedings) are considered. Papers hosted only on other websites or in self-hosted GitHub repositories are not included.

With the rapid growth in the number of AI-assisted papers, the best way to collect them is still an open question. If you have ideas for collecting or curating papers at this scale, please [open an issue](https://github.com/seewoo5/awesome-ai-for-math/issues).

- You don't need to sort rows or update counts. You also don't need to touch `assets/papers.json` or the README statistics. When a PR is merged to `main`, CI sorts the table by title, updates the paper count and the papers-by-year table in the README, and regenerates `assets/papers.json`.
- A duplicate check runs on every PR that changes `papers.md`.
- Because `papers.md` is large, GitHub may not render it fully. Edit it locally, or use the "Edit" (raw) view on GitHub, and search for the alphabetical spot or just append at the end of the table.

## Row format

```
| **[Title](https://arxiv.org/abs/XXXX.XXXXX)** | Subject, Subject, Method | arXiv 2026 | [Code](https://github.com/...) [Chat Logs](...) |
```

- **Title:** link the paper as `**[TITLE](LINK)**`. If the paper is published, link the official version and add an `[arXiv](...)` link in the last column.
- **Subject(s):** topics (e.g. number theory, geometry, mathematical physics) or methods (e.g. RL, decision tree), as plain text separated by commas, for example `Number Theory, LLM (minor)`. If a tag already exists, use exactly the same name.
- **Venue & year:** arXiv is fine if the paper is not published (`arXiv 2026`). A weekly job also updates arXiv rows when a published version appears.
- **Links & resources:** additional links such as official blog posts, articles, code, or chat logs. Add "Unofficial" if the code or blog is not an official resource.
  - Use `Code` only for actual executable code or formal artifacts (e.g. Python, Lean, notebooks with runnable verification code).
  - If the release is only prompts, responses, transcripts, or similar conversation records, label it `Chat Logs` instead.

## LLM tags

For papers that use LLMs, pick one LLM tag based on what the paper says about its AI use:

- `LLM (major)`: the core results were essentially produced by AI autonomously; the authors' work was mainly posing the problem, verifying, and writing it up as a proper paper.
- `LLM (minor)`: humans drove the research, but AI proved nontrivial lemmas or intermediate steps (or supplied key ideas or constructions for part of the argument).
- `LLM (tool)`: papers about LLMs for mathematics with no AI-attributed new result (benchmarks, surveys, prover systems).
- If an LLM-based system wrote the formal (e.g. Lean) proofs, tag `LLM (minor)` together with `ATP`. If an AI prover was given only the statements and produced the proofs, use `LLM (major)` with `ATP`.
- Papers that used AI only for proofreading, grammar, literature search, or finding minor errors are out of scope.

## Skills

Use the project-only Codex and Claude skills when they are helpful. For Codex, run `$awesome-ai-for-math-paper [paper link]`; for Claude, run `/awesome-ai-for-math-paper [paper link]`.
