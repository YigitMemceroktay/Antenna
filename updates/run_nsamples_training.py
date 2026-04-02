"""
run_nsamples_training.py

Trains 8 models × 5 runs = 40 total runs
(4 sample sizes × 2 architectures × 5 random seeds).

Each run uses a distinct seed so data shuffling and weight
initialisation differ — this gives mean ± std of val loss,
which is the standard way to evaluate models on low-data regimes.

Run from project root:
    python updates/run_nsamples_training.py
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

PYTHON       = sys.executable
UPDATES      = Path(__file__).parent
SAMPLE_SIZES = [100, 250, 500, 1000]

# Seeds for runs 1-20; extend if you ever need more than 20 runs
_ALL_SEEDS = [42, 123, 456, 789, 1337,
              2024, 3141, 9999, 1111, 2222,
              3333, 4444, 5555, 6666, 7777,
              8888, 1010, 2020, 3030, 4040]

parser = argparse.ArgumentParser()
parser.add_argument("--run-start", type=int, default=1,
                    help="First run index (1-based). Use 6 to add runs 6-10.")
parser.add_argument("--run-end",   type=int, default=5,
                    help="Last run index (inclusive). Default 5.")
args_cli = parser.parse_args()

RUN_START = args_cli.run_start
RUN_END   = args_cli.run_end
SEEDS     = {i: _ALL_SEEDS[i - 1] for i in range(RUN_START, RUN_END + 1)}


def run(cmd):
    print(f"\n{'='*60}\nRunning: {' '.join(str(c) for c in cmd)}\n{'='*60}")
    subprocess.run(cmd, check=True)


# ── Train all runs ───────────────────────────────────────────────────────────

for n in SAMPLE_SIZES:
    for run_idx, seed in SEEDS.items():
        tag = f"n{n}_run{run_idx}"

        # ResUNet v9
        run([PYTHON, str(UPDATES / "train_resunet_v9_nsamples.py"),
             "--project-root", ".",
             "--n-samples",    str(n),
             "--seed",         str(seed),
             "--model-name",   f"trained_model_resunet_v9_{tag}.pt",
             "--scaler-name",  f"scaler_resunet_v9_{tag}.gz",
             "--history-name", f"history_resunet_v9_{tag}.csv",
             "--meta-name",    f"meta_resunet_v9_{tag}.json",
        ])

        # AntennaNN
        run([PYTHON, str(UPDATES / "train_antenna_nn_nsamples.py"),
             "--project-root", ".",
             "--n-samples",    str(n),
             "--seed",         str(seed),
             "--model-name",   f"trained_model_antenna_nn_{tag}.pt",
             "--scaler-name",  f"scaler_antenna_nn_{tag}.gz",
             "--history-name", f"history_antenna_nn_{tag}.csv",
             "--meta-name",    f"meta_antenna_nn_{tag}.json",
        ])

print(f"\nAll {len(SAMPLE_SIZES) * len(SEEDS) * 2} models trained successfully (runs {RUN_START}–{RUN_END})!")


# ── Aggregate results ────────────────────────────────────────────────────────

print("\n" + "="*60)
print("SUMMARY  (mean ± std of best val loss across 5 runs)")
print("="*60)

out_dir = Path("NNModel")
results = {}   # (arch, n) -> list of best_val_loss

for n in SAMPLE_SIZES:
    for arch in ("resunet_v9", "antenna_nn"):
        vals, seeds_found = [], []
        run_idx = 1
        while True:
            tag       = f"n{n}_run{run_idx}"
            meta_path = out_dir / f"meta_{arch}_{tag}.json"
            if not meta_path.exists():
                break
            with open(meta_path) as f:
                meta = json.load(f)
            vals.append(meta["best_val_loss"])
            seeds_found.append(_ALL_SEEDS[run_idx - 1])
            run_idx += 1
        results[(arch, n)] = (vals, seeds_found)

# Print table
header = f"{'Architecture':<20} {'n_samples':>10} {'mean_val':>12} {'std_val':>12} {'runs':>6}"
print(header)
print("-" * len(header))
for arch in ("resunet_v9", "antenna_nn"):
    for n in SAMPLE_SIZES:
        vals, _ = results.get((arch, n), ([], []))
        if vals:
            mean = float(np.mean(vals))
            std  = float(np.std(vals, ddof=1))
            print(f"{arch:<20} {n:>10} {mean:>12.6f} {std:>12.6f} {len(vals):>6}")
        else:
            print(f"{arch:<20} {n:>10} {'N/A':>12} {'N/A':>12} {'0':>6}")

# Save aggregated summary to JSON
summary = {}
for (arch, n), (vals, seeds_found) in results.items():
    key = f"{arch}_n{n}"
    if vals:
        summary[key] = {
            "arch":       arch,
            "n_samples":  n,
            "n_runs":     len(vals),
            "seeds":      seeds_found,
            "val_losses": vals,
            "mean":       float(np.mean(vals)),
            "std":        float(np.std(vals, ddof=1)),
        }

summary_path = out_dir / "nsamples_summary.json"
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary saved to {summary_path}")
