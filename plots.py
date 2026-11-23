"""Make the seven numerical figures from experiment summaries."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def finish(figure, filename):
    """Give every numerical panel a legend, a light grid and a readable layout."""
    for axis in figure.axes:
        axis.legend(fontsize=8)
        axis.grid(True, alpha=0.22)
        axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(os.path.join(config.FIGURE_DIR, filename), dpi=150)
    plt.close(figure)


def plot_series(axis, rows, metric, label, x_metric="buffer", log=False):
    """Draw trial means and the requested confidence half-widths."""
    # A zero has no log coordinate. Show such observations on the bottom frame.
    points = [r for r in rows if not log or r[metric] > 0]
    line = axis.errorbar([r[x_metric] for r in points], [r[metric] for r in points],
                         yerr=[r[metric + "_ci"] for r in points], marker="o",
                         markersize=4, capsize=2, label=label)
    if log:
        zeros = [r[x_metric] for r in rows if r[metric] == 0]
        axis.plot(zeros, [0.012] * len(zeros), marker="v", linestyle="none",
                  color=line.lines[0].get_color(), transform=axis.get_xaxis_transform())


def load_figure(sweep, panels, filename, log=False):
    """Compare the four loads at every tested capacity on one or two panels."""
    figure, axes = plt.subplots(1, len(panels), figsize=(6.7 * len(panels), 4.6),
                                squeeze=False)
    for axis, (metric, label, title) in zip(axes[0], panels):
        for load in config.LOAD_LEVELS:
            rows = [row for row in sweep if row["load"] == load]
            plot_series(axis, rows, metric, f"rho = {load:.2f}", log=log)
        axis.set(xlabel="Waiting places, B (packets)", ylabel=label, title=title)
        if log:
            axis.set_yscale("log")
            axis.set_xlabel("Waiting places, B (packets)   |   Triangles: zero observed")
    finish(figure, filename)


def validation_figure(validation):
    """Show simulated blocking and the M/M/1/N prediction on the same axes."""
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for axis, load in zip(axes, (0.75, 0.95)):
        rows = [r for r in validation if r["metric"] == "buffer_loss"
                and r["load"] == load]
        sizes = [r["buffer"] for r in rows]
        axis.errorbar(sizes, [r["estimate"] for r in rows],
                      yerr=[r["ci"] for r in rows], fmt="o", capsize=3,
                      label="Simulation (95% CI)", markersize=4)
        axis.plot(sizes, [r["theory"] for r in rows], "--", label="M/M/1/N")
        axis.set(xlabel="Waiting places, B (packets)", ylabel="Buffer loss (fraction)",
                 title=f"Blocking validation at rho = {load}")
    finish(figure, "validation.png")


def peak_figures(sweep, best):
    """Relate peak-load memory to blocking and capacity to queue occupancy."""
    rows = [r for r in sweep if r["load"] == 0.95]
    figure, axis = plt.subplots(figsize=(7, 4.4))
    plot_series(axis, rows, "buffer_loss", "Simulated loss", "memory_kb")
    memory = best * config.PACKET_SIZE_BYTES / 1000
    axis.axvline(memory, linestyle="--", color="black", label=f"Selected B = {best}")
    axis.axhline(config.LOSS_TARGET, linestyle=":", color="brown", label="Loss target")
    axis.set(xlabel="Buffer memory (KB)", ylabel="Buffer loss (fraction)",
             title="Peak load: memory cost of reducing rejection")
    finish(figure, "memory_tradeoff.png")

    # The maximum is first measured per trial, then averaged across trials.
    figure, axis = plt.subplots(figsize=(7, 4.4))
    plot_series(axis, rows, "mean_queue", "Time-weighted mean")
    plot_series(axis, rows, "max_queue", "Mean of trial maxima")
    axis.set(xlabel="Waiting places, B (packets)", ylabel="Waiting packets (packets)",
             title="Peak load: typical and maximum queue length")
    finish(figure, "queue_length.png")


def make_plots(sweep, validation, comparison, best):
    """Generate all seven requested statistical figures."""
    load_figure(sweep, [("buffer_loss", "Buffer loss (fraction)", "Gateway blocking")],
                "loss_vs_buffer.png", log=True)
    load_figure(sweep, [("wait_s", "Mean waiting time (s)", "Time waiting for service")],
                "wait_vs_buffer.png")
    panels = [("throughput_pps", "Throughput (packets/s)", "Useful throughput"),
              ("delivery_ratio", "Delivery ratio (fraction)", "Packet delivery")]
    load_figure(sweep, panels, "throughput_vs_buffer.png")
    validation_figure(validation)
    peak_figures(sweep, best)

    # Facet the grouped scenario bars so each metric retains its own units.
    rows = [r for r in comparison if r["load"] == 0.95]
    figure, axes = plt.subplots(1, 3, figsize=(11, 4))
    panels = [("buffer_loss", "Buffer loss (fraction)"), ("delay_s", "Mean delay (s)"),
              ("throughput_pps", "Throughput (packets/s)")]
    for axis, (metric, label) in zip(axes, panels):
        for index, row in enumerate(rows):
            axis.bar(index, row[metric], yerr=row[metric + "_ci"], capsize=4,
                     color=f"C{index}", label=row["scenario"])
        axis.set(xticks=[], xlabel="Gateway scenario", ylabel=label, title=label)
        axis.margins(y=0.22)
    figure.suptitle("Peak-load comparison at rho = 0.95")
    finish(figure, "scenario_comparison.png")
