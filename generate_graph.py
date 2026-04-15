#!/usr/bin/env python3
"""Generate Karpathy-style progress graph from results.tsv"""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

valid = [e for e in experiments if e["val_bpb"] is not None]
if not valid:
    print("No valid experiments found in results.tsv")
    raise SystemExit(1)

running_best = []
best = float("inf")
for e in valid:
    if e["status"] == "keep" and e["val_bpb"] < best:
        best = e["val_bpb"]
    running_best.append(best)

fig, ax = plt.subplots(figsize=(14, 6))

kept_x = [i for i, e in enumerate(valid) if e["status"] == "keep"]
kept_y = [valid[i]["val_bpb"] for i in kept_x]
disc_x = [i for i, e in enumerate(valid) if e["status"] != "keep"]
disc_y = [valid[i]["val_bpb"] for i in disc_x]

ax.scatter(disc_x, disc_y, c="#cccccc", s=40, zorder=2, label="Discarded")
ax.scatter(kept_x, kept_y, c="#4CAF50", s=80, zorder=3, label="Kept")
ax.step(range(len(valid)), running_best, where="post", color="#4CAF50", linewidth=2, label="Running best")

for i in kept_x:
    ax.annotate(valid[i]["description"][:25],
                (i, valid[i]["val_bpb"]),
                textcoords="offset points", xytext=(10, 10),
                fontsize=7, color="#666666", rotation=30,
                arrowprops=dict(arrowstyle="-", color="#999999", lw=0.5))

ax.set_xlabel("Experiment #", fontsize=12)
ax.set_ylabel("val_bpb (lower is better)", fontsize=12)
n_kept = len(kept_x)
ax.set_title(f"Autoresearch Progress: {len(valid)} Experiments, {n_kept} Kept Improvements (RTX 4070, 600s budget)", fontsize=13)
ax.legend(loc="upper right")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("autoresearch-baseline-progress.png", dpi=150)
print(f"Graph saved: autoresearch-baseline-progress.png")
print(f"Total experiments: {len(valid)}")
print(f"Kept: {n_kept} ({n_kept/len(valid)*100:.0f}%)")
print(f"Best val_bpb: {min(e['val_bpb'] for e in valid):.6f}")
print(f"Baseline val_bpb: {valid[0]['val_bpb']:.6f}")
