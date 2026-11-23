"""Draw the gateway model and its boundary with Matplotlib patches."""

import os

from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

import config


def box(axis, x, y, width, height, label, color):
    """Place a labeled component at the supplied diagram coordinates."""
    patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.05",
                           edgecolor="#294450", facecolor=color)
    axis.add_patch(patch)
    axis.text(x + width / 2, y + height / 2, label, ha="center", va="center")


def arrow(axis, start, end):
    """Connect two stages in the direction of packet flow."""
    axis.annotate("", xy=end, xytext=start,
                  arrowprops={"arrowstyle": "->", "color": "#294450", "lw": 1.4})


def draw_diagram():
    """Show sources, admission, service, channel outcomes and the system boundary."""
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.set(xlim=(0, 15), ylim=(0, 6))
    # Diagram coordinates show packet flow and branches without physical units.
    axis.set(xticks=[], yticks=[], xlabel="Packet path (schematic, unitless)",
             ylabel="Traffic and loss branches (schematic, unitless)")
    for spine in axis.spines.values():
        spine.set_visible(False)
    figure.suptitle("University wireless gateway model", weight="bold")

    boundary = Rectangle((3.1, 0.7), 8.8, 4.5, fill=False, linestyle="--")
    axis.add_patch(boundary)
    axis.text(3.3, 4.85, "Modeled gateway and wireless link")
    for index, name in enumerate(("Student", "Faculty", "Admin", "IoT")):
        height = 1.0 + index
        box(axis, 0.2, height, 1.7, 0.58, name, "#e5f0f4")
        arrow(axis, (1.95, height + 0.29), (3.45, 3.35))
    for x, label in ((3.5, "FIFO buffer\nB places"),
                     (6.3, "Processing and\ntransmission"),
                     (9.3, "Wireless\nchannel"), (12.6, "Destination")):
        box(axis, x, 2.9, 2, 0.9, label, "#c5e4db")
    for start, end in ((5.55, 6.25), (8.35, 9.25), (11.35, 12.55)):
        arrow(axis, (start, 3.35), (end, 3.35))

    # Both rejection and corruption end the packet's journey.
    for x, label in ((3.5, "Full: rejected"), (9.3, "Corrupted: lost")):
        box(axis, x, 1.1, 2, 0.65, label, "#f4d5c9")
        arrow(axis, (x + 1, 2.85), (x + 1, 1.8))
    axis.legend(handles=[Patch(facecolor="#c5e4db", label="Packet path"),
                         Patch(facecolor="#f4d5c9", label="Loss outcome"),
                         Patch(fill=False, linestyle="--", label="System boundary")],
                loc="lower center", ncol=3)
    figure.tight_layout()
    figure.savefig(os.path.join(config.FIGURE_DIR, "system_diagram.png"), dpi=150)
    plt.close(figure)
