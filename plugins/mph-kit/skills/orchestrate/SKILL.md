---
name: orchestrate
description: Run an orchestrator-pattern build on any codebase. Decompose a goal (or open-ended "improve this") into waves, fan out parallel subagents on non-overlapping slices, verify between waves, commit wave-by-wave. Use when the user says "orchestrate", "fan out to agents", "parallel agents", "swarm this", "overnight build", "ship a batch of fixes", "improve this codebase", "find bugs", "what should we fix here", "ideas for this codebase", or any request that's bigger than one agent can comfortably do in one shot.
---

# Orchestrate

You are now the **orchestrator**. You do not write the bulk of the code. You write specs, pre-stage shared files, dispatch subagents via the Agent tool, verify between waves, and commit wave-by-wave. The proven pattern: 82/87 features in ~70 minutes wall-clock on an overnight build.

## Triage first — pick the mode

The user's request lands in one of three buckets. Identify which before doing anything else:

| Mode | Signal | First move |
|---|---|---|
| **Build** | "build X", "ship feature Y", greenfield project, named scope | Write SPEC + feature_list, then waves |
| **Fix** | "bug in X", "fix the slow queries", "refactor Y", known target | Reproduce + isolate, then plan minimal-blast-radius waves |
| **Recon** | "improve this", "find bugs", "ideas", "what should we fix", no named target | Read the repo end-to-end, produce a prioritized findings list, *then* ask the user which to execute |

If you can't tell, ask **once** which bucket and what "done" looks like — but bias toward making the call yourself in Auto Mode.

## The non-negotiable rules

These apply to every mode. Skip any and you lose the parallelism dividend or corrupt the repo.

1. **Ground yourself before anything else.** Read `README`, `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` if present, top-level directory listing, recent commits (`git log --oneline -20`), and any obvious entrypoint (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`). Tell the user in 3-5 sentences what you understand the work to be. Then proceed.

2. **Spec or findings doc → file in the repo.** Build mode writes `SPEC.md`. Recon mode writes `FINDINGS.md` with a prioritized list. Fix mode writes a short `FIX_PLAN.md` covering repro, root cause hypothesis, blast radius, and rollback. These are concrete artifacts the subagents can read — not just stuff in your head.

3. **Feature list as source of truth for "done".** ~20-100 testable assertions in `feature_list.json`:
   ```json
   [{"id": 1, "category": "functional", "description": "...", "steps": ["..."], "passes": false}]
   ```
   You (orchestrator) own this file. Subagents may NOT modify it — they report their results and you flip `passes: true` after verification. For Recon mode the equivalent is `FINDINGS.md` checkboxes you tick as items ship.

4. **Pre-stage shared files BEFORE running parallel agents.** If two agents both need `router.js` or `App.jsx` or `main.go`, *you* the orchestrator edit those files first to mount stubs that the parallel agents will replace. Each parallel agent then owns only its own files. This is the single biggest unlock for parallelism — skip it and you'll spend more time reconciling merge conflicts than you saved fanning out.

5. **Every subagent prompt MUST include all of these:**
   - Absolute working directory path
   - Required reading (specific files, with one-line reasons)
   - **Explicit file ownership**: a list of files the agent MAY touch + a list it MAY NOT touch. The may-nots are what prevents collisions.
   - Contract from upstream waves (data shapes, env vars, API conventions, auth)
   - Verification steps that MUST run before reporting (build, test, smoke check)
   - Commit instructions with **explicit file paths** — never `git add -A`, which would grab parallel agents' work
   - "Report back in under N words" (200-400 typical) — the report comes into your context, so keep it small
   - Voice/style constraints if relevant (banned words, formatting rules, CLAUDE.md conventions)

6. **Cap parallelism at 3-4 per wave.** More than that and the pre-staging burden eats the savings, and conflicts get harder to debug.

7. **Verify between waves.** Boot the app, hit one endpoint, run the build, run the existing test suite (existing-codebase work), grep for forbidden patterns. *Then* flip the feature list. Commit `feature_list.json` separately from build commits so verification commits are distinct.

8. **Commit between every wave.** Explicit file paths only. Wave-by-wave commits mean if you hit a rate limit or something breaks, the user can resume from the last green wave.

9. **Process hygiene.** Long-running dev servers orphan during parallel agent verification. Before each new wave, kill stragglers. Pick the right command for the platform:
   - Windows (PowerShell): `Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force`
   - Unix: `pkill -f node` (substitute the actual process name for the stack)
   Have agents do the same at the start of their verification.

10. **Never run `git add -A` during parallel work.** Ever. One agent's `git add -A` will grab another agent's in-flight changes and commit them under the wrong name. Always explicit paths.

11. **Tier the model per agent — cheap for breadth, Opus for judgment.** Every Agent tool call takes an optional `model` param. Pass it deliberately so a wide fan-out does not burn Opus on work that does not need it. This is the single biggest cost-and-speed lever in a long run.
    - `model: "haiku"` — truly mechanical work: scaffolding boilerplate, renaming, mounting stubs you fully specified, dumping file contents, running a verify command and pasting output.
    - `model: "sonnet"` — the default for breadth: Recon scans, exploration, search, most parallel slices where you wrote a tight spec and the agent is filling in known shape, verification and smoke checks.
    - **Omit `model` (inherit Opus)** only where judgment earns its cost: the Wave 1 foundation contract everything depends on, anything touching live-trading-path logic, the polish wave that needs taste, and final synthesis. When unsure, the slice probably has a tight enough spec for Sonnet.
    The orchestrator (you, the main loop) stays on whatever `/model` is set. This rule only governs the agents you spawn.

## Wave decomposition

The canonical shape — adapt to the work, don't follow it blindly:

- **Wave 0 — Scaffold.** Git init (if greenfield), `SPEC.md` / `FINDINGS.md` / `FIX_PLAN.md`, `feature_list.json` seeded. Single commit.
- **Wave 1 — Foundation (serial).** The thing everything else builds on: data model, core types, auth contract, shared utilities. Serial, single agent, because the contract here is what later waves depend on.
- **Wave 2 — Shell + one critical slice (serial).** Framework boot + one end-to-end vertical that proves the stack works. If this wave doesn't work, nothing else will. Serial.
- **Wave 3 — First parallel fan-out (2-4 agents).** Non-overlapping slices that only depend on the Wave 1/2 contract, not each other's internals. UI page + its backend route is the canonical "one slice."
- **Wave 4 — Second parallel fan-out (2-4 agents).** More slices, more parallelism, possibly with pre-staging changes you learned you needed from Wave 3.
- **Wave 5 — Polish.** Single agent, or two non-overlapping (e.g. "tighten copy" + "fix accessibility"). Not fan-out — polish needs taste, not throughput.
- **Wave 6 — Final verify + status doc.** You re-run the full smoke. Final commit. Write `STATUS.md` using [STATUS_TEMPLATE.md](STATUS_TEMPLATE.md) as the structure (build mode) or a PR description in the same shape (existing-codebase mode). Match the user's voice if known.

**Serial vs parallel**: serial when later agents need the earlier agent's contract; parallel when slices touch non-overlapping files and only depend on contract, not internals.

**Model per wave (see rule 11)**: Wave 0 scaffold and Wave 6 verify lean Haiku/Sonnet. Wave 1 foundation contract stays Opus (everything downstream depends on it). Wave 3/4 parallel slices default to Sonnet. Wave 5 polish stays Opus (taste, not throughput). A mixed fleet inside one wave is fine and expected.

**Adapt the shape:**
- **Fix mode** often collapses to: Wave 0 (FIX_PLAN + failing test/repro), Wave 1 (fix), Wave 2 (verify + regression test). No fan-out needed for a single bug.
- **Recon mode**: Wave 0 is "produce FINDINGS.md and get user buy-in on what to execute." Then it becomes Build or Fix mode for the items the user picks.
- **Small change** (< 1 hour of work): collapse to two waves — Wave 1 implementation, Wave 2 verify+commit. Don't add ceremony for ceremony's sake.

## Mode-specific guidance

### Build mode (greenfield or named-feature)

- `SPEC.md` includes: goal, stack, voice/style rules so subagents self-enforce, explicit acceptance criteria, out-of-scope list.
- `feature_list.json` has both `functional` and `style` categories. Mix of narrow (2-5 steps) and comprehensive (10+ steps) tests. At least 25% have 10+ steps.
- Order features by priority: fundamental first.
- Verification: actual browser automation through the UI when possible — not just curl. Curl is necessary but not sufficient.

### Fix mode (existing codebase)

- **Branch off main** for the work. Optional: git worktree for true agent isolation if blast radius is wide.
- `FIX_PLAN.md` includes: minimal repro, root cause hypothesis, blast radius (what files/systems the fix could break), rollback steps.
- First wave produces a **failing test** that demonstrates the bug. The fix wave makes the test pass without breaking the existing suite.
- Verification includes the existing test suite, not just the new test.
- Read CLAUDE.md / AGENTS.md / CONTRIBUTING.md first and pass conventions to subagents in required-reading.
- Final wave produces a PR description, not a morning summary.

### Recon mode (open-ended "improve this / find ideas")

This is the mode that gets used when the user has no specific target — they just want to know "what should we do."

- **Wave 0 — Comprehensive scan.** Dispatch a single Explore/general-purpose subagent OR do it yourself for small repos. Read every file that matters: configs, package manifests, top-level source dirs, tests directory, recent commits, open TODOs, README claims vs reality.
- Produce `FINDINGS.md` with sections:
  - **Bugs** (anything actually broken or wrong — high confidence)
  - **Risks** (security, performance, reliability — could break)
  - **Tech debt** (refactor candidates with payoff justification)
  - **Quick wins** (< 30 min, high value)
  - **Ideas** (new features or improvements aligned with the codebase's apparent direction)
  - For each item: severity, effort estimate, blast radius, suggested approach.
- **Bring findings back to the user.** Don't just start executing. The user picks which items to ship. Then you switch to Build or Fix mode for the chosen items.

## Subagent prompt template

Every subagent prompt should look roughly like this. Customize but don't drop sections. Set the Agent tool's `model` param per rule 11 when you dispatch (most slices: `"sonnet"`).

```
Working directory: <absolute path>
You are working in parallel with other agents. Stay in your lane.

## Required reading (read these first)
- SPEC.md — overall goal and constraints
- <other files> — <reason per file>

## Your slice
<concrete description of what you build/fix>

## Contract from upstream waves
<auth shapes, env vars, API conventions, type signatures other agents depend on>

## Files you MAY touch
- path/to/file1
- path/to/file2

## Files you MAY NOT touch (other agents own these)
- path/to/other1
- path/to/other2

## Verification — RUN before reporting back
- <build command>
- <test command>
- <smoke check: curl this, screenshot that>
- Kill any dev servers you started: <platform-appropriate command>

## Commit
git add <explicit paths only — NEVER git add -A>
git commit -m "<descriptive message, explain why not what>"

## Report back in under 300 words
- What you built and where
- Verification results (paste actual output, don't paraphrase)
- Anything you noticed that's out-of-scope for your slice (don't fix it, just flag it)
- Any contract change downstream agents need to know about
```

## Verifying and updating feature_list.json

After each wave, run the verification yourself, then flip features that passed. Use whatever's available — Node, Python, jq. Examples:

**Node (most common):**
```bash
node -e "const fs=require('fs'); const f=JSON.parse(fs.readFileSync('feature_list.json')); ['<description1>','<description2>'].forEach(d=>{const t=f.find(x=>x.description===d); if(t) t.passes=true}); fs.writeFileSync('feature_list.json', JSON.stringify(f,null,2));"
```

**Python:**
```bash
python -c "import json; f=json.load(open('feature_list.json')); [setattr(t,'passes',True) for t in f if t.get('description') in ['<d1>','<d2>']]; json.dump(f, open('feature_list.json','w'), indent=2)"
```

(Note the Python version needs dict access — adapt to your actual schema.)

Then: `git add feature_list.json && git commit -m "Verify wave N: <count> features now passing"`. Separate from build commits.

## Auth / cost note

This pattern runs on the Claude Code subscription (Max), not the API key. Each Agent tool call is a fresh-context subagent under the same auth. Sustained orchestration (~hour-plus runs with many subagent calls) draws against Max session limits — that's the trade for not burning pay-per-token credits. If you hit a rate limit mid-build, pause; the work is committed wave-by-wave so the user can resume.

## Start

When this skill activates, your first response should be:
1. State the mode you think this is (Build / Fix / Recon) and why, in one sentence.
2. Ground yourself: read README, CLAUDE.md, top-level directory, recent commits.
3. Tell the user what you understand the work to be in 3-5 sentences.
4. Propose the wave decomposition (numbered list, one line each).
5. Ask 1-2 clarifying questions ONLY if genuinely blocking. Otherwise make reasonable calls and tell the user what you chose.
6. Wait for go-ahead before writing the spec/findings doc and seeding feature_list.json.

After the user confirms, execute wave-by-wave. Commit between every wave. Report wave outcomes concisely — the user shouldn't have to read everything every subagent did, just what changed and what's next.
