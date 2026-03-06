from pathlib import Path
import pandas as pd

# Folder that contains the 5 geometry input files
base_dir = Path("data/LHS")

# Explicitly target the 5 files (seed000 ... seed004)
files = [
    base_dir / f"input_trials_done_LHS_n20_rounded_seed{seed:03d}.csv"
    for seed in range(5)
]

all_ranges = []

for file_path in files:
    df = pd.read_csv(file_path)

    # Geometry parameter columns are all columns in these files
    parameter_ranges = pd.DataFrame({
        "parameter": df.columns,
        "min": df.min(numeric_only=True).values,
        "max": df.max(numeric_only=True).values,
    })
    parameter_ranges["span"] = parameter_ranges["max"] - parameter_ranges["min"]
    parameter_ranges["seed_file"] = file_path.name

    all_ranges.append(parameter_ranges)

# Long-format result: one row per (seed_file, parameter)
ranges_long = pd.concat(all_ranges, ignore_index=True)

# Reorder columns for readability
ranges_long = ranges_long[["seed_file", "parameter", "min", "max", "span"]]

# Print all results
print(ranges_long.to_string(index=False))

# Optional: save to CSV
out_file = base_dir / "geometry_parameter_ranges_by_seed.csv"
ranges_long.to_csv(out_file, index=False)
print(f"\nSaved: {out_file}")

# Optional: pivot view (easy comparison across seeds)
ranges_pivot = ranges_long.pivot_table(
    index="parameter",
    columns="seed_file",
    values=["min", "max", "span"]
)
print("\nPivot view:")
print(ranges_pivot)