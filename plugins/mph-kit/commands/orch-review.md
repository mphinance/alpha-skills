---
description: Pre-push panel review. Fan out 4 read-only reviewers — each a distinct voice you'd otherwise need a whole team to get — then synthesize one ranked pick-list. Designed as productive tension (one voice expands, one cuts, one attacks, one verifies), not four flavors of caution.
argument-hint: [optional scope — a path, a draft, or "just the diff"; defaults to the current branch vs main]
---

Run a **panel review** of what's about to be pushed. This is not just code review. It's four different people in the room, each told to look through one lens and nothing else, deliberately set against each other so you get real tension instead of four "looks good"s.

Scope from me (may be empty): $ARGUMENTS

## 1. Establish the review surface

Figure out what's actually changing, in this order:
- If $ARGUMENTS names a path or draft, that's the surface.
- Else if there are uncommitted changes, use `git status` + `git diff` (and untracked files worth reviewing).
- Else use the branch diff vs main: `git diff main...HEAD`.

Read enough surrounding context that the reviewers aren't judging a diff in a vacuum. Note whether the surface is **code**, **prose/Substack content**, or **mixed** — that decides seat 2. State the surface in one sentence before fanning out.

## 2. Fan out 5 reviewers — in a SINGLE message, so they run concurrently

Launch all five as **read-only** subagents (investigate and report; NEVER edit, write, or commit). Give each the surface and ONLY its lens. The seats are chosen to pull in opposite directions on purpose — do not let them converge into agreement.

**Seat 1 — Devil's advocate** (`claude`, read-only). *Refute, don't reassure.* Build the strongest case AGAINST shipping. What breaks, which assumption is load-bearing and untested, the failure mode nobody's looking at, what bites in two weeks. Default skeptical. Rank concerns by likelihood × damage.

**Seat 2 — adaptive, based on the surface:**
- If the surface is **code** → **Strategist / ideas** (`claude`, read-only). *What's the bigger swing?* The 10x version, the adjacent opportunity, the thing being shipped too small. AND the inverse: is this building something you don't actually need? Concrete, not vibes.
- If the surface is **prose / Substack content** (or mixed) → **Editor / your voice** (`substack-editor`, read-only). *Does this sound like Michael, and will a reader get it?* Hard-enforce the voice rules — no em dashes anywhere, no markdown tables in Substack content, sign-off is `— Michael` only — then clarity: what's confusing, boring, or buried. Flag every violation with its location. (Voice is a hard rule; for content it outranks the strategy lens.)

**Seat 3 — Pragmatist / shipper** (`claude`, read-only). *The counterweight: it's good, cut the rest, go.* Name the ONE thing that genuinely blocks shipping right now. Call out gold-plating, scope that should be cut or deferred, and anything the other reviewers will over-worry. Bias toward "this is done, ship it." This seat exists so the panel can't just talk you out of pushing.

**Seat 4 — Craftsman: correctness + secrets + simplicity** (`claude`, read-only). *What's broken, leaking, or over-built before this goes public?* Logic bugs, edge cases, error handling; a hard sweep for secrets / keys / credentials (anything `secrets.env`-class about to be committed is an automatic BLOCK); and the solo-dev blind spot — over-engineering and "will future-you understand this." 

**Seat 5 — Idea guy** (`claude`, read-only). *Blue-sky, generative, not critical.* This is the riff Michael usually does himself. Forget shipping this version — how could the whole thing be better? The process, the UI, the experience, the feature he didn't think to ask for. Throw out more ideas than are reasonable; quantity over caution. Mark the one or two that are genuinely worth chasing, but don't self-censor the wild ones — that's the point of this seat.

## 3. Synthesize into ONE ranked pick-list

Merge the five reports into a single actionable list. Do not paste five reports back. For each item:
- One-line title, the seat(s) that raised it, and where in the surface it lives.
- Severity: **BLOCK** (fix before push), **STRONG** (really should), or **CONSIDER** (worth a thought).

Lead with BLOCK items. When two seats flag the same thing, say so — that's signal. When the Pragmatist contradicts the Devil's advocate or Strategist, surface the tension explicitly and give your read. Keep the Idea guy's riffs in their own short **Later / what if** section at the end — they're not push blockers, they're the next thing to build. End with a one-line verdict: clear to push, push after the BLOCKs, or rethink.

I decide what to fix. Don't fix anything yourself unless I say so — then it's `/ship`.
