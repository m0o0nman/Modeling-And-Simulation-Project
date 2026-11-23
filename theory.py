"""Steady-state M/M/1/N reference values."""


def queue_theory(arrival_rate, service_rate, buffer_size):
    """Compute blocking, occupancy and delay with N = B + 1 system places."""
    # At equal rates all occupancy states have equal probability.
    capacity = buffer_size + 1
    load = arrival_rate / service_rate
    if load == 1:
        loss = 1 / (capacity + 1)
        mean_system = capacity / 2
    else:
        next_power = load ** (capacity + 1)
        loss = (1 - load) * load ** capacity / (1 - next_power)
        mean_system = load / (1 - load) - (capacity + 1) * next_power / (1 - next_power)

    # Subtract the mean busy-server count and apply Little's law to admissions.
    accepted_rate = arrival_rate * (1 - loss)
    mean_queue = mean_system - load * (1 - loss)
    wait = mean_queue / accepted_rate
    return {"buffer_loss": loss, "mean_queue": mean_queue,
            "wait_s": wait, "delay_s": wait + 1 / service_rate}
