from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from train_tcnn_hilbert import INPUT_COLUMNS, create_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare antenna NN vs TCNN on Sdd11 for one sample")
    parser.add_argument("--project-root", type=str, default=".")
    parser.add_argument("--dataset", type=str, default="lhs", choices=["lhs", "old_excel"])
    parser.add_argument("--seed", type=str, default="001")
    parser.add_argument("--sample-idx", type=int, default=10)
    parser.add_argument("--antenna-model", type=str, default="NNModel/trained_model.pt")
    parser.add_argument("--antenna-scaler", type=str, default="NNModel/scaler.gz")
    parser.add_argument("--tcnn-model", type=str, default="NNModel/trained_model_tcnn_hilbert_db.pt")
    parser.add_argument("--tcnn-scaler", type=str, default="NNModel/scaler_tcnn_hilbert_db.gz")
    parser.add_argument("--tcnn-model-type", type=str, default="hilbert", choices=["hilbert", "dual"])
    parser.add_argument("--trace-label", type=str, default="Sdd11", help="Label to show in plot, e.g., S11")
    parser.add_argument("--magnitude-db", action="store_true", help="Plot |Sdd11| in dB")
    parser.add_argument("--out", type=str, default="updates/sdd11_compare_antenna_vs_tcnn_seed001_idx10.png")
    return parser.parse_args()


class AddCoords1D(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, out: torch.Tensor) -> torch.Tensor:
        in_batch, _, in_w = out.shape
        width_coords = torch.linspace(-1, 1, steps=in_w, device=out.device)
        wc = width_coords.repeat(in_batch, 1, 1)
        return torch.cat((out, wc), 1)


class AntennaNeuralNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.logsigma = nn.Parameter(torch.ones(1))
        self.filter_size = 41

        self.add_coords = AddCoords1D()
        self.linear = nn.Sequential(
            nn.Linear(11, 60),
            nn.Tanh(),
            nn.Linear(60, 60),
            nn.Tanh(),
            nn.Linear(60, 60),
            nn.Tanh(),
        )
        self.deconv1 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=60, out_channels=40, kernel_size=21, stride=1),
            nn.Tanh(),
        )
        self.deconv2 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=40, out_channels=40, kernel_size=7, stride=3),
            nn.Tanh(),
        )
        self.deconv3 = nn.Sequential(
            nn.ConvTranspose1d(in_channels=41, out_channels=2, kernel_size=3, stride=3),
            nn.Tanh(),
        )

    def smooth(self, x: torch.Tensor) -> torch.Tensor:
        n = self.filter_size
        x = F.pad(x, ((n - 1) // 2, (n - 1) // 2), mode="reflect")

        sigma = torch.exp(self.logsigma).unsqueeze(-1).unsqueeze(-1)
        sigma = sigma.repeat((1, 1, n))
        hw = 3 * sigma
        xx = torch.linspace(0, 1, steps=n, device=x.device).unsqueeze(0).unsqueeze(0)
        xx = xx.repeat((x.shape[1], 1, 1))
        xx = 2 * hw * xx - hw

        gauss = 1 / (2 * np.pi * sigma**2) * torch.exp(-1 / (2 * (sigma**2)) * xx**2)
        gauss_sum = gauss.sum(dim=2).unsqueeze(-1).repeat((1, 1, gauss.shape[-1]))
        gauss = gauss / gauss_sum
        return F.conv1d(x, gauss, groups=x.shape[1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.linear(x)
        out = out.view(len(x), 60, 1)
        out = self.deconv1(out)
        out = self.deconv2(out)
        out = self.add_coords(out)
        out = self.deconv3(out)
        out = self.smooth(out)
        return out


def load_sample(root: Path, dataset: str, seed: str, idx: int):
    if dataset == "lhs":
        lhs = root / "data" / "LHS"
        input_path = lhs / f"input_trials_done_LHS_n20_rounded_seed{seed}.csv"
        real_path = lhs / f"real_initial_LHS_n20_rounded_seed{seed}.csv"
        imag_path = lhs / f"imag_initial_LHS_n20_rounded_seed{seed}.csv"

        x_df = pd.read_csv(input_path)[INPUT_COLUMNS]
        real_df = pd.read_csv(real_path)
        imag_df = pd.read_csv(imag_path)
    elif dataset == "old_excel":
        old = root / "old" / "data"
        x_df = pd.read_excel(old / "input_parameters.xlsx")[INPUT_COLUMNS]
        real_df = pd.read_excel(old / "reel.xlsx")
        imag_df = pd.read_excel(old / "imaginary.xlsx")
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")

    if idx < 0 or idx >= len(x_df):
        raise IndexError(f"sample-idx {idx} out of range [0, {len(x_df)-1}]")

    x = x_df.iloc[[idx]].values.astype(np.float32)
    real_true = real_df.iloc[idx].values.astype(np.float32)
    imag_true = imag_df.iloc[idx].values.astype(np.float32)
    return x_df, x, real_true, imag_true


def to_mag(real: np.ndarray, imag: np.ndarray) -> np.ndarray:
    return np.sqrt(real**2 + imag**2)


def to_db(mag: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.clip(mag, 1e-12, None))


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    x_df, x_one, real_true, imag_true = load_sample(root, args.dataset, args.seed, args.sample_idx)
    mag_true = to_mag(real_true, imag_true)

    antenna_scaler = joblib.load(root / args.antenna_scaler)
    x_antenna = antenna_scaler.transform(x_one).astype(np.float32)
    antenna_model = AntennaNeuralNet()
    antenna_model.load_state_dict(torch.load(root / args.antenna_model, map_location="cpu"))
    antenna_model.eval()
    with torch.no_grad():
        antenna_pred = antenna_model(torch.tensor(x_antenna))
    real_ant = antenna_pred[0, 0, :].numpy()
    imag_ant = antenna_pred[0, 1, :].numpy()
    mag_ant = to_mag(real_ant, imag_ant)

    tcnn_scaler = joblib.load(root / args.tcnn_scaler)
    x_tcnn = tcnn_scaler.transform(x_one).astype(np.float32)
    tcnn_model = create_model(args.tcnn_model_type, input_dim=len(INPUT_COLUMNS), target_len=real_true.shape[0])
    tcnn_model.load_state_dict(torch.load(root / args.tcnn_model, map_location="cpu"))
    tcnn_model.eval()
    with torch.no_grad():
        tcnn_pred = tcnn_model(torch.tensor(x_tcnn))
    real_tcnn = tcnn_pred[0, 0, :].numpy()
    imag_tcnn = tcnn_pred[0, 1, :].numpy()
    mag_tcnn = to_mag(real_tcnn, imag_tcnn)

    x_axis = np.arange(real_true.shape[0])
    if args.magnitude_db:
        y_true = to_db(mag_true)
        y_ant = to_db(mag_ant)
        y_tcnn = to_db(mag_tcnn)
        y_label = f"|{args.trace_label}| (dB)"
        title_suffix = "magnitude in dB"
    else:
        y_true = mag_true
        y_ant = mag_ant
        y_tcnn = mag_tcnn
        y_label = f"|{args.trace_label}|"
        title_suffix = "linear magnitude"

    mse_ant = float(np.mean((y_ant - y_true) ** 2))
    mse_tcnn = float(np.mean((y_tcnn - y_true) ** 2))

    plt.figure(figsize=(11, 7))
    plt.plot(x_axis, y_true, label=f"Real {args.trace_label}", linewidth=2.4)
    plt.plot(x_axis, y_ant, label=f"Antenna NN (MSE={mse_ant:.4f})", linewidth=2, linestyle="--")
    plt.plot(x_axis, y_tcnn, label=f"TCNN+Hilbert (MSE={mse_tcnn:.4f})", linewidth=2, linestyle="-.")
    if args.dataset == "lhs":
        title_id = f"seed={args.seed}, sample={args.sample_idx}"
    else:
        title_id = f"old_excel sample={args.sample_idx}"
    plt.title(f"{args.trace_label} comparison ({title_suffix}, {title_id})")
    plt.xlabel("Point index")
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()

    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()

    print(f"Saved plot: {out_path}")
    if args.dataset == "lhs":
        print(f"dataset={args.dataset}, seed={args.seed}, sample_idx={args.sample_idx}")
    else:
        print(f"dataset={args.dataset}, sample_idx={args.sample_idx}")
    print(f"AntennaNN plot-space MSE: {mse_ant:.6f}")
    print(f"TCNN plot-space MSE: {mse_tcnn:.6f}")
    print("Selected geometry input:")
    print(x_df.iloc[args.sample_idx].to_string())


if __name__ == "__main__":
    main()
