# Autoresearch Baseline Test — COMPLETE INSTRUCTIONS

**For:** Agent running on Windows/WSL2 with NVIDIA GPU
**From:** Billy Wilton (wav) / Al (Claude Opus 4.6)
**Repo:** https://github.com/wavHub/autoresearch-results
**Date:** 2026-04-16

---

## WHAT THIS IS

**Autoresearch** is a tool created by Andrej Karpathy (former Tesla AI director, OpenAI researcher). It lets an AI agent run experiments on a neural network training loop AUTONOMOUSLY — overnight, without human intervention. The agent modifies training code, runs a 5-minute training experiment, checks if the model improved, keeps or discards the change, and repeats. You wake up to 50-100 experiments completed.

**Source:** https://github.com/karpathy/autoresearch
**Paper/Context:** https://x.com/karpathy/status/2029701092347630069

**What we're testing:** Does the autoresearch loop produce measurable improvements? We want the "staircase graph" — a chart showing val_bpb (validation bits per byte) dropping over experiments. This is the BASELINE — no memory, no accumulated knowledge. Just iterate-measure-keep/discard.

**What ASI-Evolve is (for context):** A separate framework (arXiv:2603.29640, from SJTU/GAIR) that adds a "cognition base" (memory of past experiments) to the same iterate-measure loop. We will compare autoresearch (no memory) against ASI-Evolve (with memory) AFTER this baseline is established. ASI-Evolve is NOT part of this test. This test is autoresearch only.

**Where results go:** Push to https://github.com/wavHub/autoresearch-results on a branch named `autoresearch/baseline-YYYYMMDD`.

---

## PREREQUISITES

You need:
- Windows machine with WSL2 Ubuntu installed
- NVIDIA GPU visible in WSL2 (`nvidia-smi` must work)
- Internet access (to clone repo and download data)
- ~10GB free disk space
- ~6+ hours of unattended runtime

---

## STEP-BY-STEP INSTRUCTIONS

### Step 1: Open WSL2 Ubuntu terminal

On Windows, open a terminal and type:
```bash
wsl
```

You should see a Linux prompt. All remaining commands run inside WSL2.

### Step 2: Verify GPU access

```bash
nvidia-smi
```

You should see your NVIDIA GPU listed with driver version and CUDA version. If this fails, WSL2 NVIDIA drivers are not installed. Fix that first: https://docs.nvidia.com/cuda/wsl-user-guide/

### Step 3: Install required system packages

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl
```

### Step 4: Install uv (Python package manager)

Karpathy's autoresearch uses `uv` instead of pip. Install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then reload your shell:
```bash
source ~/.bashrc
```

Verify:
```bash
uv --version
```

Should print a version number like `uv 0.7.x`.

### Step 5: Clone autoresearch

```bash
cd ~
git clone https://github.com/karpathy/autoresearch.git
cd autoresearch
```

### Step 6: Install Python dependencies

```bash
uv sync
```

This creates a virtual environment and installs PyTorch, tokenizers, and other dependencies. Takes 2-5 minutes. If it fails on CUDA/PyTorch, you may need to install CUDA toolkit first:
```bash
sudo apt install -y nvidia-cuda-toolkit
```

### Step 7: Download training data and train tokenizer

```bash
uv run prepare.py --num-shards 10
```

This downloads ~2GB of text data from HuggingFace and trains a BPE tokenizer. Takes ~2 minutes. Data is stored in `~/.cache/autoresearch/`.

**If this fails:** Check internet connection. The data comes from `huggingface.co/datasets/karpathy/climbmix-400b-shuffle`.

### Step 8: Run one training experiment (verify everything works)

```bash
uv run train.py
```

This trains a small language model for exactly 5 minutes. At the end it prints:

```
---
val_bpb:          0.XXXXXX
training_seconds: 300.X
total_seconds:    XXX.X
peak_vram_mb:     XXXXX.X
mfu_percent:      XX.XX
total_tokens_M:   XXX.X
num_steps:        XXX
num_params_M:     XX.X
depth:            8
```

**The number that matters is `val_bpb`.** Lower is better. Write this number down — it's your baseline.

**If this fails with CUDA errors:** Your GPU may not support Flash Attention 3. The code tries to use it and falls back to an alternative. Check the error message.

**If this fails with OOM (out of memory):** Edit `train.py`, find `DEVICE_BATCH_SIZE = 128` and reduce it to 64 or 32.

### Step 9: Create experiment branch

```bash
cd ~/autoresearch
git checkout -b autoresearch/baseline-$(date +%Y%m%d)
```

### Step 10: Create results tracking file

```bash
echo -e "commit\tval_bpb\tmemory_gb\tstatus\tdescription" > results.tsv
```

### Step 11: Record baseline result

After Step 8 completed successfully, record the baseline:
```bash
BASELINE_BPB=0.XXXXXX  # replace with actual value from Step 8
BASELINE_MEM=XX.X       # replace with peak_vram_mb / 1024
COMMIT=$(git rev-parse --short HEAD)
echo -e "${COMMIT}\t${BASELINE_BPB}\t${BASELINE_MEM}\tkeep\tbaseline" >> results.tsv
```

### Step 12: Start the AI agent

This is where the autonomous part begins. You need an AI agent (Claude Code, Codex, or similar) running in the `~/autoresearch` directory.

Start your AI agent and give it this prompt:

```
Hi, I need you to run an autonomous autoresearch experiment. 

Read program.md in this directory — it contains complete instructions for the experiment loop.

The goal: modify train.py to get the lowest val_bpb score possible. Each experiment trains for 5 minutes. After each run, check if val_bpb improved. If yes, keep the change (git commit). If no, discard it (git reset). Log every experiment to results.tsv.

The baseline val_bpb is [INSERT YOUR BASELINE NUMBER HERE].

Run at least 50 experiments. Do not stop or ask me questions — I will be away. Run autonomously until I return.

Start by reading program.md, then begin experimenting.
```

**IMPORTANT:** The agent must have permission to:
- Read and write files in `~/autoresearch/`
- Run shell commands (`uv run train.py`, `git commit`, etc.)
- NOT modify `prepare.py` (read-only — contains the evaluation metric)
- ONLY modify `train.py` (this is the file it experiments with)

### Step 13: Leave it running overnight

The agent will iterate:
1. Modify train.py (change architecture, hyperparameters, optimizer, etc.)
2. Git commit the change
3. Run `uv run train.py` (5 min training)
4. Check val_bpb
5. If improved: keep the commit, log "keep" to results.tsv
6. If not improved: `git reset --hard` to previous best, log "discard" to results.tsv
7. Repeat

Each experiment takes ~6 minutes (5 min training + 1 min agent thinking). 50 experiments = ~5 hours. 100 experiments = ~10 hours.

---

## AFTER COMPLETION

### Step 14: Generate the progress graph

Create this file as `generate_graph.py` in the autoresearch directory:

```python
#!/usr/bin/env python3
"""Generate Karpathy-style progress graph from results.tsv"""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read results
experiments = []
with open("results.tsv") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        experiments.append({
            "commit": row["commit"],
            "val_bpb": float(row["val_bpb"]) if row["val_bpb"] != "0.000000" else None,
            "memory_gb": float(row["memory_gb"]) if row["memory_gb"] != "0.0" else None,
            "status": row["status"],
            "description": row["description"],
        })

# Filter valid experiments
valid = [e for e in experiments if e["val_bpb"] is not None]

if not valid:
    print("No valid experiments found in results.tsv")
    exit(1)

# Compute running best
running_best = []
best = float("inf")
for e in valid:
    if e["status"] == "keep" and e["val_bpb"] < best:
        best = e["val_bpb"]
    running_best.append(best)

# Plot
fig, ax = plt.subplots(figsize=(14, 6))

kept_x = [i for i, e in enumerate(valid) if e["status"] == "keep"]
kept_y = [valid[i]["val_bpb"] for i in kept_x]
disc_x = [i for i, e in enumerate(valid) if e["status"] != "keep"]
disc_y = [valid[i]["val_bpb"] for i in disc_x]

ax.scatter(disc_x, disc_y, c="#cccccc", s=40, zorder=2, label="Discarded")
ax.scatter(kept_x, kept_y, c="#4CAF50", s=80, zorder=3, label="Kept")
ax.step(range(len(valid)), running_best, where="post", color="#4CAF50", linewidth=2, label="Running best")

# Annotate kept improvements
for i in kept_x:
    ax.annotate(valid[i]["description"][:25],
                (i, valid[i]["val_bpb"]),
                textcoords="offset points", xytext=(10, 10),
                fontsize=7, color="#666666", rotation=30,
                arrowprops=dict(arrowstyle="-", color="#999999", lw=0.5))

ax.set_xlabel("Experiment #", fontsize=12)
ax.set_ylabel("val_bpb (lower is better)", fontsize=12)
n_kept = len(kept_x)
ax.set_title(f"Autoresearch Progress: {len(valid)} Experiments, {n_kept} Kept Improvements", fontsize=13)
ax.legend(loc="upper right")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("autoresearch-baseline-progress.png", dpi=150)
print(f"Graph saved: autoresearch-baseline-progress.png")
print(f"Total experiments: {len(valid)}")
print(f"Kept: {n_kept} ({n_kept/len(valid)*100:.0f}%)")
print(f"Best val_bpb: {min(e['val_bpb'] for e in valid):.6f}")
print(f"Baseline val_bpb: {valid[0]['val_bpb']:.6f}")
```

Run it:
```bash
pip3 install matplotlib  # if not installed
python3 generate_graph.py
```

### Step 15: Push results to GitHub

```bash
cd ~/autoresearch

# Add GitHub remote (first time only)
git remote add results https://github.com/wavHub/autoresearch-results.git

# Stage results
git add results.tsv autoresearch-baseline-progress.png generate_graph.py train.py

# Commit
git commit -m "autoresearch baseline: $(wc -l < results.tsv) experiments, best val_bpb=$(tail -1 results.tsv | cut -f2)"

# Push
git push results autoresearch/baseline-$(date +%Y%m%d)
```

**If git push asks for authentication:** Use a GitHub personal access token. Generate one at https://github.com/settings/tokens with `repo` scope.

---

## WHAT TO REPORT BACK

After pushing to GitHub, report these numbers:

1. **Total experiments completed:** (number)
2. **Kept improvements:** (number and percentage)
3. **Baseline val_bpb:** (starting score)
4. **Best val_bpb:** (best score achieved)
5. **Total improvement:** (baseline - best)
6. **GPU used:** (model name from nvidia-smi)
7. **Total wall time:** (how long it ran)
8. **Any crashes or issues encountered**

The graph (`autoresearch-baseline-progress.png`) and raw data (`results.tsv`) should be in the GitHub repo.

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| `nvidia-smi` not found | Install NVIDIA WSL2 drivers: https://docs.nvidia.com/cuda/wsl-user-guide/ |
| `uv: command not found` | Run `source ~/.bashrc` after installing uv |
| `uv sync` fails on PyTorch | Install CUDA toolkit: `sudo apt install nvidia-cuda-toolkit` |
| OOM during training | Edit train.py: reduce `DEVICE_BATCH_SIZE` from 128 to 64 or 32 |
| Flash Attention error | The code auto-falls back. If it still fails, check GPU compute capability |
| `git push` auth fails | Use personal access token: https://github.com/settings/tokens |
| Agent stops responding | Check if training is still running (`ps aux | grep train.py`). Restart agent if needed. |
| val_bpb is 0.000000 | Training crashed. Check `run.log` for errors. |

---

## CONTEXT (for the agent running this)

**Who we are:** Billy Wilton (wav) is building a knowledge intelligence system called SynT. This test is part of validating whether autonomous AI experiment loops produce real improvements.

**Why this matters:** If autoresearch produces a staircase of improvements (like Karpathy's published results), it validates the pattern. We then compare this baseline against ASI-Evolve (a framework that adds memory/cognition to the same loop) to test whether memory improves convergence.

**ASI-Evolve:** A separate tool from arXiv:2603.29640 (SJTU/GAIR, March 2026). It adds a "cognition base" that stores insights from past experiments and retrieves them for future rounds. Open source at https://github.com/GAIR-NLP/ASI-Evolve. NOT used in this test — this test is autoresearch only.

**This is a CONTROL experiment.** No modifications to autoresearch. Run it as Karpathy designed it. The results are the baseline.

---

## MACHINE-SPECIFIC: RTX 4070 (12GB VRAM)

**GPU:** NVIDIA GeForce RTX 4070
**VRAM:** 12,282 MB (12GB GDDR6X)
**CUDA cores:** 5,888
**CPU:** Intel i7-13700KF
**RAM:** 32GB
**OS:** Windows 11 Pro (WSL2 Ubuntu)

### Required train.py modifications BEFORE first run

The default config needs ~45GB VRAM (H100). RTX 4070 has 12GB. Edit `train.py` BEFORE running:

```python
# Find these lines and change them:

DEVICE_BATCH_SIZE = 128   # CHANGE TO: 16 or 32
DEPTH = 8                 # CHANGE TO: 4 or 6
TOTAL_BATCH_SIZE = 2**19  # CHANGE TO: 2**16 or 2**17
```

**Start conservative:**
```python
DEVICE_BATCH_SIZE = 16
DEPTH = 4
TOTAL_BATCH_SIZE = 2**16
```

If that works without OOM, try increasing:
```python
DEVICE_BATCH_SIZE = 32
DEPTH = 6
TOTAL_BATCH_SIZE = 2**17
```

### Flash Attention compatibility

RTX 4070 is Ada Lovelace (compute capability 8.9). NOT Hopper (9.0). The code will fall back to `kernels-community/flash-attn3` instead of `varunneal/flash-attention-3`. This should happen automatically — check the output for:

```
# Should see something like:
# Using kernels-community/flash-attn3 (non-Hopper GPU)
```

If Flash Attention fails entirely, check: https://github.com/karpathy/autoresearch#platform-support

### Expected performance

| Setting | DEPTH=4, BS=16 | DEPTH=6, BS=32 |
|---------|---------------|----------------|
| Params | ~12M | ~30M |
| VRAM | ~4GB | ~10GB |
| Tokens/step | ~32K | ~65K |
| Steps in 5 min | ~200+ | ~100+ |
| val_bpb | Higher (worse) | Lower (better) |

Smaller model trains faster but achieves worse val_bpb. The agent's job is to find improvements within the 5-minute budget at whatever model size fits in VRAM.
