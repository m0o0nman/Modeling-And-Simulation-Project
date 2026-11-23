"""Inputs for the university gateway experiments."""

import os

# Normal arrivals per second for each independent traffic source.
CLASS_RATES_NORMAL = {"student": 40, "faculty": 10, "admin": 10, "iot": 15}
SERVICE_RATE = 100  # Packets processed per second.
LOAD_LEVELS = [0.50, 0.75, 0.95, 1.10]  # Offered rate / service rate.
BUFFER_SIZES = [1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 40, 50]  # Waiting places.
BASELINE_BUFFER = 1000  # Waiting places in the large reference gateway.
CONSTRAINED_BUFFER = 5  # Waiting places in the constrained gateway.
CHANNEL_ERROR_PROB = 0.05  # Probability of corruption per service completion.
PACKET_SIZE_BYTES = 1500  # Storage per waiting packet, in bytes.
LOSS_TARGET = 0.02  # Maximum fraction of arrivals rejected at peak load.
DELAY_TARGET = 0.15  # Maximum mean arrival-to-departure time in seconds.

# Each trial starts empty and includes the warm-up time in its duration.
QUICK_MODE = False
SIM_TIME = 100 if QUICK_MODE else 250  # Seconds of arriving traffic.
WARMUP = 50  # Seconds excluded at the start.
TRIALS = 5 if QUICK_MODE else 20  # Independent replications per setting.
BASE_SEED = 1  # First trial seed (dimensionless integer).

# Locate all project outputs relative to this file.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")
FIGURE_DIR = os.path.join(OUTPUT_DIR, "figures")
