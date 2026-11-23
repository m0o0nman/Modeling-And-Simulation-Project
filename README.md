# Group 2 · Limited gateway buffer capacity

Four campus traffic sources share a single FIFO gateway. This project measures what
one additional waiting place buys in packet loss, memory and delay.

## Run in PyCharm

1. Choose **File → Open** and select `E:\3-2 2209007\Modeling and Simulation`.
2. Under **Settings → Python Interpreter**, select Python 3.10 or later. The
   interpreter used for verification was `E:\Coding\Mod and Sim\.venv\Scripts\python.exe`
   (Python 3.14.7). You can select this existing interpreter on the study computer.
3. In the PyCharm terminal with the selected interpreter active, run
   `python -m pip install -r "E:\3-2 2209007\Modeling and Simulation\requirements.txt"`.
4. Right-click `main.py` and choose **Run 'main'**. The script locates its output
   folder from its own location, so the run configuration can use any working directory.
5. Open `outputs/comparison.csv` for the six scenario rows and `outputs/figures`
   for the charts. Rerunning refreshes the CSV and PNG files. The report records the
   delivered full run. If you change the inputs, update its numerical discussion.

## Run settings and timing

| Run | SIM_TIME (s) | Warm-up (s) | Measured time per trial (s) | Trials | Wall time (s) |
|---|---:|---:|---:|---:|---:|
| Quick | 100 | 50 | 50 | 5 | 75.50 |
| Full, delivered | 250 | 50 | 200 | 20 | 685.34 |

Set `QUICK_MODE = True` in `config.py` for the quick check. Restore `False` for the
full study. Each run uses 50 distinct load and capacity combinations. The quick
timing suggested that 500 s × 20 trials would exceed 15 minutes on this machine.
Shortening the full duration to 250 s retained 20 independent trials for estimating
variation. Full-run trial seeds are 1 through 20. The timer covers experiments,
CSV writing and figure production. Machine and interpreter affect wall time.

## Project files

| File | Purpose |
|---|---|
| `config.py` | Study inputs, units, mode and output paths |
| `simulation.py` | Four arrival generators, packet lifecycle and measurements |
| `theory.py` | M/M/1/N reference values, including equal arrival and service rates |
| `experiments.py` | Replications, confidence intervals, validation, selection and CSV writing |
| `plots.py` | Seven statistical figures |
| `draw_diagram.py` | Architecture, system boundary and loss paths |
| `main.py` | Entry point and measured runtime |
| `requirements.txt` | Three Python dependencies |
| `README.md` | Setup, measured run settings and oral explanation |
| `REPORT_DRAFT.md` | Interpretation of the delivered full-run results |
| `outputs/trials.csv` | Per-seed metrics for every unique setting |
| `outputs/baseline.csv` | Large-buffer normal and peak reference |
| `outputs/sweep.csv` | All four loads and twelve finite buffers |
| `outputs/validation.csv` | Theory and simulated intervals for blocking and delay |
| `outputs/comparison.csv` | Three designs at each of the two comparison loads |
| `outputs/figures/*.png` | System diagram and seven results figures |

## Two-minute explanation for a professor

Imagine a student packet reaching the gateway while another packet is being
transmitted. If a waiting place is free, the new packet joins the back of the
queue. If every place is occupied, the gateway rejects it immediately. A buffer
with five places can therefore hold six packets in the system, counting the
one in service. Student, faculty, administration and IoT arrivals all follow
the same rule. Their different generation rates determine how often they arrive.

At normal load, the four sources generate 75 packets per second on average. The
gateway can serve 100 per second on average. Random arrivals can still come
close together, and a long service can keep the server busy. That explains why
a finite buffer can overflow even when the average arrival rate is below capacity.
After service, each packet has a separate 5% chance of channel corruption.
Adding memory can prevent a rejection, but it cannot repair a channel error.

SimPy advances the clock from one event to the next. We exclude the first 50 seconds
from measurements so an initially empty gateway has time to build a queue. A packet
that arrives inside the measurement window is followed to its outcome. Throughput
counts successful departures from that cohort before the window closes. Queue
length and utilization measure the actual state during the window, including work
already present at its start. A queue of four packets lasting two seconds contributes
eight packet-seconds to the queue integral.

We repeat each setting with independent seeds and compare blocking and delay with
finite-queue theory. At peak load, we choose the smallest tested buffer whose
average rejection and delay both meet the engineering targets. The six-row
comparison then shows how much memory that choice uses, how many packets it saves
and how much longer admitted packets wait.
