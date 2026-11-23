"""Discrete-event model of a finite FIFO gateway."""

import numpy as np
import simpy

from config import PACKET_SIZE_BYTES


def observe_queue(env, gateway, totals, warmup, end):
    """Integrate the previous queue length up to this event."""
    # Clip every interval to the observation window, including the last one.
    now = min(env.now, end)
    elapsed = max(0, now - max(totals["last_change"], warmup))
    previous = totals["waiting"]
    totals["queue_area"] += elapsed * previous
    if elapsed > 0:
        totals["maximum"] = max(totals["maximum"], previous)

    # Store the new queue length for the next interval.
    totals["last_change"] = now
    totals["waiting"] = len(gateway.queue)


def packet(env, gateway, totals, settings, random):
    """Admit or reject one arrival, then follow an admitted packet to departure."""
    service_rate, buffer_size, error_prob, warmup, end = settings
    arrival_time = env.now
    measured = arrival_time >= warmup
    if measured:
        totals["generated"] += 1

    # An idle server accepts immediately, even with no waiting places.
    if gateway.count == 1 and len(gateway.queue) >= buffer_size:
        if measured:
            totals["rejected"] += 1
        return

    # Request the FIFO server and track the queue at entry and service start.
    with gateway.request() as request:
        observe_queue(env, gateway, totals, warmup, end)
        yield request
        start_time = env.now
        observe_queue(env, gateway, totals, warmup, end)

        # Include only the overlap of this busy interval with the measured window.
        service_time = random.exponential(1 / service_rate)
        busy_start = max(start_time, warmup)
        busy_end = min(start_time + service_time, end)
        totals["busy"] += max(0, busy_end - busy_start)
        yield env.timeout(service_time)

        # Delay covers all admitted packets, including channel-corrupted packets.
        successful = random.random() >= error_prob
        if measured:
            totals["wait_sum"] += start_time - arrival_time
            totals["delay_sum"] += env.now - arrival_time
            totals["delivered"] += int(successful)
            if successful and env.now < end:
                totals["delivered_in_window"] += 1


def traffic_source(env, rate, gateway, totals, settings, random):
    """Schedule exponential inter-arrivals until the measurement window closes."""
    # Stopping arrivals lets the final admitted packets finish without censoring.
    while True:
        interval = random.exponential(1 / rate)
        if env.now + interval >= settings[-1]:
            return
        yield env.timeout(interval)
        env.process(packet(env, gateway, totals, settings, random))


def run_one_simulation(class_rates, service_rate, buffer_size, error_prob,
                       sim_time, warmup, seed):
    """Return packet-cohort and time-window metrics for one trial."""
    # Set up the single gateway, random stream and counters shared by its sources.
    env = simpy.Environment()
    gateway = simpy.Resource(env, capacity=1)
    random = np.random.default_rng(seed)
    settings = service_rate, buffer_size, error_prob, warmup, sim_time
    totals = dict.fromkeys(
        ["generated", "rejected", "delivered", "delivered_in_window", "wait_sum",
         "delay_sum", "busy", "queue_area", "maximum", "waiting", "last_change"], 0
    )
    for rate in class_rates.values():
        env.process(traffic_source(env, rate, gateway, totals, settings, random))

    # Close time-based statistics at the horizon, then resolve packet outcomes.
    env.run(until=sim_time)
    observe_queue(env, gateway, totals, warmup, sim_time)
    env.run()
    generated = totals["generated"]
    admitted = generated - totals["rejected"]
    duration = sim_time - warmup
    return {
        "buffer_loss": totals["rejected"] / generated if generated else np.nan,
        "delivery_ratio": totals["delivered"] / generated if generated else np.nan,
        "throughput_pps": totals["delivered_in_window"] / duration,
        "wait_s": totals["wait_sum"] / admitted if admitted else np.nan,
        "delay_s": totals["delay_sum"] / admitted if admitted else np.nan,
        "mean_queue": totals["queue_area"] / duration,
        "max_queue": totals["maximum"],
        "utilization": totals["busy"] / duration,
        "memory_kb": buffer_size * PACKET_SIZE_BYTES / 1000,
    }
