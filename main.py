"""Run the Group 2 study from PyCharm or the command line."""

import time

import config
from experiments import run_experiments


def main():
    """Run all experiments, draw figures and print the study summary."""
    start = time.perf_counter()

    # Load the plotting backend before drawing the system diagram.
    from plots import make_plots
    from draw_diagram import draw_diagram
    sweep, validation, comparison, best = run_experiments()
    make_plots(sweep, validation, comparison, best)
    draw_diagram()

    # Report elapsed wall time for experiments, CSV writing and plotting.
    elapsed = time.perf_counter() - start
    passed = sum(row["inside"] for row in validation)
    print(f"B_STAR = {best} waiting places")
    print(f"Theory within 95% CI: {passed}/{len(validation)}")
    print(f"SIM_TIME = {config.SIM_TIME} s; TRIALS = {config.TRIALS}")
    print(f"Execution time: {elapsed:.2f} s")


if __name__ == "__main__":
    main()
