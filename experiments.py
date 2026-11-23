"""Run the parameter sweep, validate it and compare designs."""

import csv
import os

import numpy as np

import config
from simulation import run_one_simulation
from theory import queue_theory


def write_table(name, rows):
    """Write dictionaries with a common header to one output CSV."""
    # Use newline handling recommended by the standard csv module.
    path = os.path.join(config.OUTPUT_DIR, name + ".csv")
    with open(path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def run_setting(load, buffer_size, trial_rows):
    """Scale all four sources together and summarize independent replications."""
    # Keep the normal traffic mix at every offered load.
    scale = load * config.SERVICE_RATE / sum(config.CLASS_RATES_NORMAL.values())
    rates = {name: rate * scale for name, rate in config.CLASS_RATES_NORMAL.items()}
    setting = {"load": load, "buffer": buffer_size}
    samples = []
    for trial in range(config.TRIALS):
        seed = config.BASE_SEED + trial
        metrics = run_one_simulation(
            rates, config.SERVICE_RATE, buffer_size, config.CHANNEL_ERROR_PROB,
            config.SIM_TIME, config.WARMUP, seed
        )
        samples.append(metrics)
        trial_rows.append({**setting, "seed": seed, **metrics})

    # Each CI column is the 95% half-width based on between-trial variation.
    summary = setting.copy()
    for metric in samples[0]:
        values = [sample[metric] for sample in samples]
        summary[metric] = np.mean(values)
        summary[metric + "_ci"] = 1.96 * np.std(values, ddof=1) / np.sqrt(len(values))
    return summary


def validate(sweep):
    """Compare both simulated metrics to theory for the two requested loads."""
    rows = []
    for result in sweep:
        if result["load"] not in (0.75, 0.95):
            continue
        theory = queue_theory(result["load"] * config.SERVICE_RATE,
                              config.SERVICE_RATE, result["buffer"])
        for metric in ("buffer_loss", "delay_s"):
            estimate = result[metric]
            width = result[metric + "_ci"]
            inside = bool(abs(estimate - theory[metric]) <= width)
            rows.append({"load": result["load"], "buffer": result["buffer"],
                         "metric": metric, "estimate": estimate, "ci": width,
                         "theory": theory[metric], "inside": inside})
            if not inside:
                print(f"Warning: rho={result['load']}, B={result['buffer']}, "
                      f"{metric}: theory {theory[metric]:.7g} outside "
                      f"[{estimate - width:.7g}, {estimate + width:.7g}]")
    return rows


def select_buffer(sweep):
    """Select the smallest tested peak-load buffer meeting the target rules."""
    # Check increasing capacities and retain the loss-only fallback.
    loss_candidates = [row for row in sweep if row["load"] == 0.95
                       and row["buffer_loss"] <= config.LOSS_TARGET]
    both = [row["buffer"] for row in loss_candidates
            if row["delay_s"] <= config.DELAY_TARGET]
    if both:
        return min(both)
    if loss_candidates:
        return min(row["buffer"] for row in loss_candidates)
    raise ValueError("No tested size reaches the peak-load loss target.")


def run_experiments():
    """Run each distinct setting once and save all requested tables."""
    os.makedirs(config.FIGURE_DIR, exist_ok=True)
    trials = []
    baseline = [run_setting(load, config.BASELINE_BUFFER, trials)
                for load in (0.75, 0.95)]
    sweep = []
    for load in config.LOAD_LEVELS:
        print(f"Simulating sweep at rho={load}", flush=True)
        for size in config.BUFFER_SIZES:
            sweep.append(run_setting(load, size, trials))

    # Reuse the same estimates for validation, design selection and comparison.
    validation = validate(sweep)
    best = select_buffer(sweep)
    comparison = []
    for row in baseline:
        comparison.append({"scenario": "Baseline", **row})
        for name, size in (("Constrained", config.CONSTRAINED_BUFFER),
                           ("Improved", best)):
            selected = next(item for item in sweep
                            if item["buffer"] == size and item["load"] == row["load"])
            comparison.append({"scenario": name, **selected})
    for name, rows in (("baseline", baseline), ("sweep", sweep), ("trials", trials),
                       ("validation", validation), ("comparison", comparison)):
        write_table(name, rows)
    return sweep, validation, comparison, best
