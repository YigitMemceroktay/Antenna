"""
run_nsamples_training.py

Trains 8 models (4 ResUNet v9 + 4 AntennaNN) at sample sizes 100, 250, 500, 1000.
Run from project root:
    python updates/run_nsamples_training.py
"""
import subprocess, sys
from pathlib import Path

PYTHON = sys.executable
UPDATES = Path(__file__).parent
SAMPLE_SIZES = [100, 250, 500, 1000]


def run(cmd):
    print(f"\n{'='*60}\nRunning: {' '.join(cmd)}\n{'='*60}")
    result = subprocess.run(cmd, check=True)
    return result


for n in SAMPLE_SIZES:
    # ResUNet v9
    run([PYTHON, str(UPDATES / "train_resunet_v9_nsamples.py"),
         "--project-root", ".",
         "--n-samples", str(n),
         "--model-name",   f"trained_model_resunet_v9_n{n}.pt",
         "--scaler-name",  f"scaler_resunet_v9_n{n}.gz",
         "--history-name", f"history_resunet_v9_n{n}.csv",
         "--meta-name",    f"meta_resunet_v9_n{n}.json",
    ])

    # AntennaNN
    run([PYTHON, str(UPDATES / "train_antenna_nn_nsamples.py"),
         "--project-root", ".",
         "--n-samples", str(n),
         "--model-name",   f"trained_model_antenna_nn_n{n}.pt",
         "--scaler-name",  f"scaler_antenna_nn_n{n}.gz",
         "--history-name", f"history_antenna_nn_n{n}.csv",
         "--meta-name",    f"meta_antenna_nn_n{n}.json",
    ])

print("\nAll 8 models trained successfully!")
