---
name: awesome-ai-for-math-paper
description: Add paper links to the awesome-ai-for-math repository README. Use when the user gives an arXiv, DOI, proceedings, journal, or paper URL and asks to add it to awesome-ai-for-math, update the README paper table, classify topics, find associated resources such as GitHub repositories, update an existing paper-add PR, or commit the change with a Claude co-author trailer.
---

# Awesome AI For Math Paper

## Workflow

Use this workflow for the `awesome-ai-for-math` repository unless the user gives different instructions.

1. Inspect state first.
   - Run `git status -sb`.
   - Read the relevant README rows around the alphabetical insertion point.
   - If a PR branch is already active for paper additions, continue on it. If starting from `main`, create a `claude/...` branch before committing.

2. Fetch paper metadata from primary sources.
   - For arXiv links, read the arXiv abstract page or Atom API record.
   - Extract title, submission year, abstract, arXiv subjects, comments, and visible resource links.
   - Do not rely only on the user-provided title.

3. Choose README fields.
   - Title: exact paper title as rendered by the source, linked to the paper URL.
   - Subject(s): prefer existing README tags. Use mathematical domain tags first, then method tags such as `LLM`, `ATP`, `RL`, `Transformer`, `Neural Network`, or `Benchmark`.
   - Venue & Year: use `arXiv YYYY` unless a published venue is confirmed.
   - Links & Resources: include official resources discovered from the paper page, abstract, paper PDF, repository search, author pages, or clearly related existing project repos.

4. Search for associated resources.
   - Check the paper page and PDF for URLs such as GitHub, GitLab, project pages, datasets, notebooks, Lean artifacts, or chat logs.
   - Search the web for the exact title plus `GitHub`, `code`, and named systems from the abstract.
   - Verify candidate repositories exist before adding them.
   - If a paper has a dedicated repo, prefer it over a shared system repo. Example: use `[Code](https://github.com/frenzymath/iteris)` for Iteris rather than the shared Rethlas repo.
   - If a known shared project has an existing README label style and no more-specific repo is confirmed, reuse it. Example: use `[Code (Rethlas)](https://github.com/frenzymath/Rethlas)` for Rethlas-based papers.
   - Use `Code` only for actual executable code or formal artifacts. Use `Chat Logs` for transcripts or prompt/response records.

5. Edit README only unless the user asks for generated/site data updates.
   - Bump the paper count in the intro.
   - Insert the row alphabetically by title.
   - Keep markdown table formatting consistent.
   - Do not edit `assets/papers.json` or charts when the user says README-only.

6. Validate.
   - Run `rg -c '^\| \*\*\[' README.md` and confirm the count matches the intro.
   - Run `git diff -- README.md` and inspect the exact row(s).
   - Confirm `git status -sb` shows only intended files.

7. Commit and publish when requested.
   - Stage explicit files.
   - Include a Claude co-author trailer in commit messages:

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

   - For multi-line commit messages, use `git commit -m "Summary" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"`.
   - Push the branch and update or create the draft PR.
   - Keep PR title/body aligned with the final set of paper additions and validation.

## Classification Guidance

- Use `Numerical Analysis, LLM` for LLM-assisted computational mathematics papers centered on numerical methods.
- Use `Algebraic Geometry, Number Theory` for p-adic/nonabelian Hodge or arithmetic geometry papers unless the paper explicitly emphasizes formal proof or LLM methodology.
- Add `ATP` only when the paper uses automated/formal theorem proving or proof assistant artifacts.
- Add `LLM` when the abstract or resources describe language models, agentic AI systems, AI-generated proof drafts, or AI-assisted research workflow.
