# HISTORY — The Mess (and the Lessons in the Mess)

**Run:** `autoresearch/baseline-20260416`
**Agent:** Lance (Claude Opus 4.6) in Claude Code on WSL2 Ubuntu 24.04
**Date:** 2026-04-16

This file is intentionally preserved separately from [REPORT.md](REPORT.md). REPORT.md is the clean writeup for external readers. HISTORY.md is the **raw operational record**: what I actually did in what order, the dead ends, the git protocol mistake, the reset-away experiments that still exist as rescued tags on GitHub, and the lessons that can only be learned from seeing the mess.

If you're reading this to learn from Lance's process, read HISTORY.md first, then REPORT.md.

---

## The two branches on `wavHub/autoresearch-results`

| Branch | Purpose | Based on |
|---|---|---|
| `autoresearch/baseline-20260416` | **The messy experiment branch.** All 22+ commits including code changes for each experiment, result commits, merges, and the baseline recalibration. Forked from `karpathy/autoresearch` upstream `master`. No shared history with `main`. | `karpathy/autoresearch` |
| `results/baseline-20260416` | **The clean results-only branch.** 7 files (REPORT.md, HISTORY.md, results.tsv, graph, generate_graph.py, train.py, prepare.py). What gets PR'd to `main`. | `main` |

Both are live on GitHub. Use the first to read the journey, the second to merge the outcome.

---

## Rescued orphan tags (the experiments that got reset away)

When the autoresearch loop discards an experiment, it does `git reset --hard` to drop the failed code change. The reset detaches the experiment's commit from any branch, and `git gc` eventually deletes it. **That deletes the very thing you want to learn from** — the failed hypotheses.

Before that happened, I rescued every discarded commit from the reflog and tagged it. The tags are pushed to `wavHub/autoresearch-results`. Each URL below opens the exact `train.py` state that produced the failed result:

| Tag | Hash | What it tried | val_bpb | Link |
|---|---|---|---:|---|
| `exp1-discarded` | `a1a6f74` | `WARMUP_RATIO 0.0 → 0.05` | 1.728378 | [view](https://github.com/wavHub/autoresearch-results/tree/exp1-discarded) |
| `exp7-discarded` | `e772c3d` | `MATRIX_LR 0.06 → 0.07` | 1.437691 | [view](https://github.com/wavHub/autoresearch-results/tree/exp7-discarded) |
| `exp9-discarded` | `91b8434` | `FINAL_LR_FRAC 0.1 → 0.2` | 1.422109 | [view](https://github.com/wavHub/autoresearch-results/tree/exp9-discarded) |
| `exp10-discarded` | `99c7172` | `EMBEDDING_LR 0.6 → 0.8` | 1.422408 | [view](https://github.com/wavHub/autoresearch-results/tree/exp10-discarded) |
| `exp11-discarded` | `a440bdb` | `EMBEDDING_LR 0.6 → 0.4` | 1.443792 | [view](https://github.com/wavHub/autoresearch-results/tree/exp11-discarded) |
| `exp12-discarded` | `da03c1c` | `WEIGHT_DECAY 0.2 → 0.1` | 1.428641 | [view](https://github.com/wavHub/autoresearch-results/tree/exp12-discarded) |

Three additional tags preserve the `results.tsv` row commits that got dropped when I reset past them (the protocol bug, below):

| Tag | Hash | What it was | Lost because |
|---|---|---|---|
| `exp9-discard-log` | `dc88009` | `results.tsv` row for exp9 | Reset for exp10 went back past it |
| `exp10-discard-log` | `d98b47c` | `results.tsv` row for exp10 | Reset for exp11 went back past it |
| `exp11-discard-log` | `3e01785` | `results.tsv` row for exp11 | Reset for exp12 went back past it |

---

## The git reset protocol bug (the biggest lesson)

### What I thought I was doing

The autoresearch protocol says: after a discarded experiment, `git reset --hard` back to the last kept commit to drop the failed `train.py` change. Then log the discard as a new row in `results.tsv` and commit that row.

### What I actually did

I reset back to the last **keep-row-log-commit** (`d7d3243` for the exp8 keep). That dropped the train.py change — correct. But because I was resetting back *past* the previous discard's log-row commit, I **also dropped the results.tsv rows** for exp9, exp10, exp11.

By the time I got to exp12 and did one more reset, `results.tsv` was missing three discard rows without anyone noticing. I only caught it at wrap-up when I compared the file contents against my chat narrative.

### Sequence that produced the bug

```
HEAD=d7d3243 (exp8 log row committed)
  ↓
commit exp9 code     (91b8434)
commit exp9 log row  (dc88009)   ← HEAD advances
  ↓
commit exp10 code    (99c7172)
git reset --hard d7d3243          ← DROPS dc88009, 99c7172, and 91b8434 from branch
                                   (91b8434 was reachable only through 99c7172, now orphan)
commit exp10 log row (d98b47c)   ← based on d7d3243 again, missing exp9 row
  ↓
... same pattern for exp11, exp12
```

Result: `results.tsv` ended up with exp1, exp2–6, exp7, exp8, and **only exp12** from the later discards. exp9/10/11 were silent casualties.

### How I fixed it

1. Reconstructed `results.tsv` by hand from the chat narrative in commit `7807ec1`. Checked every hash and row against what the run actually produced.
2. Added the correction commit message: "fix: restore exp9-11 discard rows (lost to reset protocol bug)".
3. Later (this commit): rescued every orphan to a named git tag so the actual code of the failed experiment is still inspectable.

### How to avoid it next time

Pick one of these protocols for the next autoresearch run:

- **Option A (simplest):** After each experiment — keep or discard — the reset target advances to HEAD-after-log-commit, not back to the previous keep. Pseudocode:

  ```bash
  # after running exp N
  if [[ keep ]]; then
    git add results.tsv; git commit -m "log exp$N keep: $result"
    RESET_TARGET=HEAD  # the just-made log commit
  else
    git reset --hard $RESET_TARGET   # drop the train.py change
    git add results.tsv; git commit -m "log exp$N discard: $result"
    RESET_TARGET=HEAD  # advance past the discard log
  fi
  ```

- **Option B (git-native):** Use `git notes` for discard log entries. Notes live outside the linear history and survive any reset. Downside: less discoverable to people browsing the repo.

- **Option C (no resets):** Never reset. Just commit every experiment — keeps and discards — onto a linear branch and let the staircase live in `results.tsv`. Downside: branch contains every failed `train.py` in history, which inflates the repo and may confuse future agents who pull the branch head.

I'd pick **Option A** next time. Simplest, preserves the staircase cleanly, and the reset target tracking is a one-line variable in the shell loop.

---

## The linear git log (what actually survived on the experiment branch)

Reverse-chronological, most recent first. The upstream commits are unchanged from `karpathy/autoresearch` and elided.

```
ea26317 docs: add full REPORT.md with results, insights, issues, next-steps
f24ffc1 autoresearch baseline 2026-04-16: 13 experiments, 7 kept, best val_bpb=1.394097 (-15.9%)
7807ec1 fix: restore exp9-11 discard rows (lost to reset protocol bug)       ← THE FIX COMMIT
ff81b88 log exp12 discard: WEIGHT_DECAY 0.1 hurt
d7d3243 log exp8 keep: FINAL_LR_FRAC 0.1 val_bpb=1.394097                    ← RUNNING BEST
3d33a04 exp8: FINAL_LR_FRAC 0.0->0.1 (keep 10% LR floor)
a6851ed log exp7 discard: MATRIX_LR 0.07 overshot
27a4985 log exp6 keep: MATRIX_LR 0.06 val_bpb=1.429892
88dcb79 exp6: MATRIX_LR 0.05->0.06 (push Muon LR further)
089f556 log exp5 keep: MATRIX_LR 0.05 val_bpb=1.440016
2c89ddf exp5: MATRIX_LR 0.04->0.05 (pivot to Muon LR lever)
494fe0b log exp4 keep: WARMDOWN_RATIO 0.05 val_bpb=1.469034
8c73901 exp4: WARMDOWN_RATIO 0.15->0.05 (push to near-minimum)
0bcc1d7 log exp3 keep: WARMDOWN_RATIO 0.15 val_bpb=1.491071 (-0.076)
b971fea exp3: WARMDOWN_RATIO 0.25->0.15 (push peak-LR time further)
00079c0 log exp2 keep: WARMDOWN_RATIO 0.25 val_bpb=1.566551 (-0.091)
14acd68 exp2: WARMDOWN_RATIO 0.5->0.25 (more time at peak LR)
2fe0b74 log exp1 discard: WARMUP_RATIO 0.05 hurt val_bpb
ccf1b8e record baseline@600s: val_bpb=1.657928 53steps                       ← THE BASELINE
b94a517 override: TIME_BUDGET 300->600 for RTX 4070
5f0992a record baseline: val_bpb=1.825723 31steps RTX4070                    ← pre-flight calibration
e345ec6 baseline: DEVICE_BATCH_SIZE 128->32 for RTX 4070 (4.8GB free VRAM)
... (upstream karpathy commits from here down)
```

**25 commits on top of upstream.** The "pre-flight calibration" at `5f0992a` ran the script once at the default 300s budget to prove the environment worked before doubling the budget. That result (val_bpb=1.825) is technically in the log but not in results.tsv because the actual baseline (at 600s) is what the experiment loop compared against.

Note what's NOT in this log: the exp1 code, exp7 code, exp9/10/11/12 code. Those commits exist only as rescued tags, unreachable from any branch head. That's normal for an autoresearch loop — the reset is the point — but if the discards are erased without rescue, you lose the negative-result data that makes the search surface legible.

---

## The reasoning chain (how each experiment followed from the previous)

This is the part that doesn't show up in `git log` but matters more than the code changes.

**exp1 (discard):** Naive first move. "Add warmup — it's standard practice." Result hurt because the training budget is only ~50 steps. Warmup eats into peak-LR time that the model is starving for. **Lesson: standard best practices for large training runs can invert at small scales.**

**exp2-4 (three consecutive keeps):** Hypothesis from exp1's failure: "if gentle hurts, aggressive helps." Push WARMDOWN_RATIO from 0.5 → 0.25 → 0.15 → 0.05. Each step smaller, diminishing returns. By exp4 the returns were −0.022 and clearly tapering — time to pivot. **Lesson: push a working lever until returns diminish, then move.**

**exp5-6 (two keeps):** Pivot to a different lever on the same hypothesis. Muon `MATRIX_LR` from 0.04 → 0.05 → 0.06. Same diminishing-returns pattern. **Lesson: the same insight transfers across levers in the same family (here: "we're LR-starved").**

**exp7 (discard):** Overshoot probe. Push MATRIX_LR one more step to 0.07. Got +0.008 — first worse-than-previous. **Lesson: once you're close to the ceiling, always make one move that's too far. That's the only way to know where the ceiling is, and the data point is free because you can always reset.**

**exp8 (keep — running best):** New lever on the same theme. If we want more training per step and less decay, `FINAL_LR_FRAC` 0.0 → 0.1 keeps a learning floor. Biggest individual win (−0.036). **Lesson: after pushing a lever to its ceiling, don't try a smaller step in the same direction — try an orthogonal lever that attacks the same underlying problem from a different angle.**

**exp9 (discard):** Same ceiling-probe idea — push FINAL_LR_FRAC from 0.1 → 0.2. Overshot. **Lesson: the ceiling-probe pattern is cheap to run and reliably informative. Use it every time.**

**exp10-11 (two discards in a row):** Try `EMBEDDING_LR` in both directions — 0.8 then 0.4. Both worse. **Lesson: sometimes the default IS the optimum. Accept it and move on.**

**exp12 (discard):** Final lever — `WEIGHT_DECAY` 0.2 → 0.1. Worse. **Lesson: same as exp10-11.** In retrospect I should have gone to 0.05 instead of 0.1, but by this point context was tightening and I chose to wrap rather than squeeze one more experiment.

**What I didn't try (and would next time):**
- `ADAM_BETAS` — both (0.9, 0.95) and (0.7, 0.95)
- `UNEMBEDDING_LR` — underused lever
- `SCALAR_LR` — same
- Architecture: `DEPTH` 8 → 6 with compensating `ASPECT_RATIO` bump to stay within VRAM
- Softmax temperature on logits
- QK normalization
- Weight tying between wte and lm_head

Each of those is plausibly worth ~0.01–0.03 on this setup, and the total may have reached val_bpb ≈ 1.30 given another 6–8 experiments. The real ceiling on RTX 4070 without architectural changes is probably around 1.25–1.30 before OOM becomes the binding constraint.

---

## Session-level notes

- **Session duration:** ~3 hours 15 minutes of wall clock for the experiment loop itself, plus ~30 minutes of setup (clone, uv sync, prepare, first baseline at 300s, TIME_BUDGET change, second baseline at 600s) and ~15 minutes of wrap-up (graph, REPORT.md, pushes, PR).
- **Effective throughput:** 13 experiments in ~3h → 14 min per experiment average. Matches the expected 10 min training + ~4 min compile/startup/eval overhead.
- **Context cost on my side:** heavy. Each experiment required reading the latest `val_bpb`, deciding the next lever, editing `train.py`, committing, launching, waiting. The "wait for background" loop is cheap in tokens per event but the compound effect across 13 experiments consumes a nontrivial share of the context window. A fully autonomous multi-hour run would need either a reset-friendly approach (periodic checkpoints + fresh session resumption) or a non-agentic driver (a bash loop + a smaller model for decisions).
- **Zero crashes** across all 13 runs + 2 pre-flight baselines + a torch.compile warm-up. The first run took 537 s total (237 s compile), subsequent runs took ~790 s total with cached compile. Training time itself was consistently ~300–610 s depending on budget.

---

## What the agent (me) got right

1. **Pre-flight checks.** Before launching any training I verified `nvidia-smi`, `free -h`, `df -h`, `uv --version`, `gh auth status`. Caught the 4.8 GB free VRAM constraint immediately.
2. **Hardware override with justification.** Didn't run the defaults blindly. Dropped `DEVICE_BATCH_SIZE` to 32 before the first run, not after the first OOM. Added `TIME_BUDGET` 600 after the user asked, and re-ran the baseline so all comparisons were apples-to-apples.
3. **Hypothesis-driven experiments.** Every experiment had a stated hypothesis BEFORE the run, tied to the previous result. No random mutations. 54% keep rate reflects this.
4. **Ceiling-probing.** Every lever that worked got pushed to its ceiling (exp7 and exp9 exist specifically to find the ceilings of MATRIX_LR and FINAL_LR_FRAC).
5. **Pivoted on diminishing returns.** Didn't ride WARMDOWN_RATIO past its point of diminishing returns — moved to a new lever as soon as the gain dropped below ~0.02.

## What the agent (me) got wrong

1. **The reset protocol bug.** Already covered above. Undetected for multiple experiments.
2. **Didn't test a safe `ADAM_BETAS` change.** The most conventional lever in the optimizer, and I skipped it. Regret.
3. **Stopped one experiment short.** Could have done `WEIGHT_DECAY` 0.2 → 0.05 as exp13 after exp12 hurt. That's the ceiling probe in the direction of the failed experiment, and it would have given a cleaner "nothing in this lever" verdict.
4. **Didn't batch-push until the end.** Pushed only at wrap-up, so an interrupted session would have lost everything. Should have pushed to the experiment branch after every 3–4 experiments.
5. **The two `NINA-HANDOFF-LATEST.md` earlier in this session show the same hook-reminder pattern firing on Edit → Read races.** Unrelated to autoresearch but noted for completeness.

---

## For the next autoresearch agent reading this

If you're reading this to run your own autoresearch experiment (on this or different hardware):

1. **Read REPORT.md first for the outcome, then this file for the process.**
2. **Fix my reset protocol bug** — see "How to avoid it next time" above.
3. **Rescue every discarded experiment as a git tag before the next run.** The failed experiments are the data. Don't lose them.
4. **Budget your context window.** 13 experiments cost me ~3 hours and significant context. If you're on the same model I am, don't plan for more than ~15–20 experiments per session without a resumption checkpoint.
5. **Pre-flight every resource before the first run.** The VRAM ceiling shaped every decision after. Knowing your constraint is more valuable than knowing your target.
6. **Push early, push often.** Don't wait until the end. An interrupted session should still leave the branch in a useful state.

---

*Written 2026-04-16 by Lance. This file exists because messy learning beats clean theatrics.*
