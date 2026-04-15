# Autoresearch Baseline Test — RunPod H100

**For:** Agent running on RunPod H100 GPU instance
**From:** Billy Wilton (wav) / Al (Claude Opus 4.6)
**Date:** 2026-04-16
**Prior result:** RTX 4070 baseline — 13 experiments, 7 kept, val_bpb 1.658 → 1.394 (−15.9%)

---

## WHAT THIS IS

Same test as the RTX 4070 run, but on an H100 — the GPU Karpathy designed autoresearch for. The H100 runs 539 steps per 5-minute experiment vs 39 on the RTX 4070. More steps = more training = lower val_bpb = better starting point. The agent then iterates on top of that.

**Purpose:** Establish the H100 baseline staircase. Compare convergence rate and final val_bpb against the RTX 4070 result.

---

## RUNPOD SETUP

### Step 1: Create RunPod instance

1. Go to runpod.io → Pods → Deploy
2. Select: **NVIDIA H100 80GB** (or H100 SXM if available)
3. Template: **RunPod PyTorch 2.x** (comes with CUDA, Python, pip)
4. Disk: **50GB** (enough for data + code)
5. Start the pod

### Step 2: Connect

```bash
# Use RunPod web terminal, or SSH:
ssh root@<pod-ip> -p <port> -i ~/.ssh/id_ed25519
```

### Step 3: Verify GPU

```bash
nvidia-smi
```

Should show: H100 80GB, Driver 535+, CUDA 12.x

---

## INSTALL & RUN

### Step 4: Install uv + clone autoresearch

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
cd ~
git clone https://github.com/karpathy/autoresearch.git
cd autoresearch
```

### Step 5: Install dependencies

```bash
uv sync
```

### Step 6: Prepare data

```bash
uv run prepare.py --num-shards 10
```

### Step 7: Run baseline (DO NOT MODIFY train.py)

H100 uses the DEFAULT settings. No overrides needed.

```bash
uv run train.py
```

Record the baseline val_bpb. This is experiment 0.

**Expected:** val_bpb around 0.99-1.05, ~539 steps in 5 minutes, ~44GB peak VRAM.

### Step 8: Create branch + results file

```bash
git checkout -b autoresearch/h100-baseline-20260416
echo -e "commit\tval_bpb\tmemory_gb\tstatus\tdescription" > results.tsv
```

### Step 9: Record baseline

```bash
BASELINE_BPB=X.XXXXXX  # replace with actual
BASELINE_MEM=XX.X       # replace with peak_vram_mb / 1024
COMMIT=$(git rev-parse --short HEAD)
echo -e "${COMMIT}\t${BASELINE_BPB}\t${BASELINE_MEM}\tkeep\tbaseline" >> results.tsv
```

### Step 10: Start the agent

```
Read program.md in this directory.

The goal: modify train.py to get the lowest val_bpb score possible.
Each experiment trains for 5 minutes.
After each run, check if val_bpb improved. If yes, keep (git commit). If no, discard (git reset).
Log every experiment to results.tsv.

The baseline val_bpb is [INSERT NUMBER].

Run at least 50 experiments. Do not stop or ask questions. Run autonomously.

IMPORTANT:
- ONLY modify train.py
- DO NOT modify prepare.py
- Each experiment = modify → commit → train 5 min → measure → keep/discard → log
```

### Step 11: Leave it running

Each experiment: ~6 min (5 min train + 1 min agent thinking).
50 experiments = ~5 hours.
100 experiments = ~10 hours.

---

## AFTER COMPLETION

### Step 12: Generate graph

```bash
pip install matplotlib
python3 generate_graph.py
```

(Use the same generate_graph.py from the RTX 4070 run, or create from NVIDIA-TEST-PLAN-V2.md)

### Step 13: Push results

```bash
git remote add results https://github.com/wavHub/autoresearch-results.git
git add results.tsv autoresearch-baseline-progress.png train.py
git commit -m "h100 baseline: $(wc -l < results.tsv) experiments, best val_bpb=$(tail -1 results.tsv | cut -f2)"
git push results autoresearch/h100-baseline-20260416
```

---

## COMPARISON TABLE

Fill this in after both runs complete:

| Metric | RTX 4070 (done) | H100 (this run) |
|--------|-----------------|-----------------|
| Steps per 5 min | 39-53 | ~539 |
| Baseline val_bpb | 1.658 | ? |
| Best val_bpb | 1.394 | ? |
| Improvement | −15.9% | ? |
| Experiments | 13 | target 50+ |
| Keep rate | 54% (7/13) | ? |
| Total wall time | ~2 hours | ? |
| Crashes | 0 | ? |
| VRAM peak | 11.4 GB | ~44 GB |

**Key question:** Does the H100 baseline start lower (better model from more steps) AND does the agent find more improvements? The RTX 4070 was limited by training steps per experiment. H100 removes that bottleneck.

---

## RUNPOD COST

| GPU | $/hr (on-demand) | 50 experiments | 100 experiments |
|-----|-------------------|----------------|-----------------|
| H100 80GB | ~$3.50/hr | ~$17.50 (5 hrs) | ~$35 (10 hrs) |
| H100 SXM | ~$4.50/hr | ~$22.50 | ~$45 |

**Spot pricing** may be 50-70% cheaper if available.

**IMPORTANT:** Stop the pod when done. RunPod charges by the minute.

---

## WHAT TO REPORT

1. Total experiments completed
2. Kept improvements (count + percentage)
3. Baseline val_bpb (experiment 0)
4. Best val_bpb achieved
5. Total improvement (baseline − best)
6. GPU confirmed (nvidia-smi output)
7. Total wall time
8. Any crashes or issues
9. The graph (autoresearch-baseline-progress.png)
10. Comparison to RTX 4070 results

Push everything to `autoresearch/h100-baseline-20260416` branch on https://github.com/wavHub/autoresearch-results

---

**This is still the CONTROL experiment. No memory. No cognition base. Autoresearch only. The H100 result is the ceiling for memoryless iteration.**
