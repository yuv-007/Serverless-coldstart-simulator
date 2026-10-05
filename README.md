# Serverless Cold-Start Reduction & Intelligent Function Scheduling

A research-oriented discrete-event simulator for studying **serverless cold-start latency reduction through intelligent warm-instance scheduling**.

The project investigates how different scheduling strategies can reduce user-visible cold-start latency while avoiding unnecessary resource over-provisioning.

The long-term research direction is to progress from simple rule-based policies to **demand forecasting, uncertainty-aware scheduling, and reinforcement-learning-based warm-pool control**.

---

## Research Objective

Serverless platforms provide automatic scaling, but sudden workload increases can cause **cold starts** when no warm execution environment is immediately available.

This project studies the following problem:

> **How can a serverless scheduler proactively manage warm instances to reduce cold-start latency while controlling idle-resource cost?**

The research progression is:

```text
Reactive / Static Policies
          ↓
Threshold-Based Scaling
          ↓
Demand Forecasting
          ↓
Uncertainty-Aware Forecasting
          ↓
Reinforcement Learning
          ↓
Robustness & Generalization
          ↓
Potential Hybrid Strategy
```

The simulator provides a controlled environment in which these scheduling strategies can be evaluated under identical workloads.

---

# Current Status

The core simulation and experimental infrastructure has been implemented.

The repository currently supports:

- Discrete-event serverless simulation
- Request arrival and completion modeling
- Instance lifecycle management
- Cold-start modeling
- Request queuing
- Concurrent request handling
- Controller-driven scaling decisions
- Deterministic event ordering
- Multiple baseline controllers
- Demand forecasting
- Forecast uncertainty modeling
- Synthetic workload generation
- Uniform, Poisson, and bursty traffic
- Reproducible workload generation
- Workload specifications
- Fair controller-to-controller comparison
- Structured experiment results
- SLO violation measurement
- Automated testing

### Current test status

```text
59 / 59 tests passing
```

The reinforcement-learning components currently provide the foundation for the next research phase. A trained RL scheduling policy has **not yet been implemented and evaluated**.

---

# System Architecture

The current experimental architecture is:

```text
                    ┌─────────────────┐
                    │   WorkloadSpec  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  TrafficTrace   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ ExperimentRunner│
                    └────────┬────────┘
                             │
                Same workload trace
                 for every controller
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Controller A│    │ Controller B│    │ Controller C│
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          │                  │                  │
          ▼                  ▼                  ▼
   ┌────────────────────────────────────────────────────┐
   │              Serverless Simulator                 │
   │                                                    │
   │  Request Arrival → Scheduling → Execution          │
   │       │                │                           │
   │       │                ├── Warm Instance           │
   │       │                ├── Starting Instance      │
   │       │                └── Request Queue           │
   │       │                                            │
   │       └──────────── Cold Start Modeling            │
   └───────────────────────┬────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ ExperimentResult│
                  └────────┬────────┘
                           │
                           ▼
                    Comparable Metrics
```

A key design principle is:

> **Every controller must be evaluated against exactly the same workload trace.**

This prevents differences in workload realization from contaminating controller comparisons.

---

# Repository Structure

```text
.
├── Controllers/
│   ├── __init__.py
│   ├── base.py
│   ├── fixed_pool.py
│   ├── forecast.py
│   ├── idle_timeout.py
│   ├── no_prewarm.py
│   ├── static.py
│   ├── threshold.py
│   └── uncertainty.py
│
├── Experiments/
│   ├── __init__.py
│   ├── results.py
│   ├── run.py
│   ├── run_baselines.py
│   ├── runner.py
│   └── workload.py
│
├── Forecasting/
│   ├── __init__.py
│   ├── baseline.py
│   └── uncertainty.py
│
├── RL/
│   ├── __init__.py
│   ├── environment.py
│   └── reward.py
│
├── Results/
│   ├── figures/
│   ├── processed/
│   ├── raw/
│   └── README.md
│
├── Simulator/
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── environment.py
│   ├── instance.py
│   ├── metrics.py
│   ├── queue.py
│   └── request.py
│
├── Traffic/
│   ├── __init__.py
│   ├── real.py
│   ├── synthetic.py
│   └── trace.py
│
├── configs/
│   └── base.yaml
│
├── docs/
│   └── README.md
│
├── tests/
│   ├── test_basic_structure.py
│   ├── test_experiments.py
│   ├── test_forecasting.py
│   ├── test_simulator_basics.py
│   ├── test_traffic.py
│   └── test_workload.py
│
├── project_context.md
├── requirements.txt
└── README.md
```

---

# Simulator

The simulator is implemented as a **discrete-event simulation system**.

Instead of relying on real wall-clock execution, events are scheduled on simulated time and processed through an event queue.

The main event types include:

```text
CONTROLLER_TICK
INSTANCE_START_COMPLETE
REQUEST_ARRIVAL
REQUEST_COMPLETE
```

Events occurring at the same simulated timestamp have deterministic priority ordering.

The current priority ordering is:

```text
CONTROLLER_TICK          → 0
INSTANCE_START_COMPLETE → 1
REQUEST_ARRIVAL          → 2
REQUEST_COMPLETE         → 3
```

This makes simulation behavior deterministic and prevents ambiguous event ordering.

For example:

```text
Controller tick
      ↓
Controller decides to prewarm
      ↓
Instance begins startup
      ↓
Request arrives
      ↓
Request waits for startup
      ↓
Instance becomes warm
      ↓
Request executes
      ↓
Request completes
```

---

# Instance Lifecycle

The simulator models the lifecycle of serverless execution instances.

Conceptually:

```text
             ┌────────────┐
             │ TERMINATED │
             └──────┬─────┘
                    │
                    │ Start
                    ▼
             ┌────────────┐
             │  STARTING  │
             └──────┬─────┘
                    │
                    │ Startup complete
                    ▼
             ┌────────────┐
             │    WARM    │
             └──────┬─────┘
                    │
                    │ Scale down / expire
                    ▼
             ┌────────────┐
             │ TERMINATED │
             └────────────┘
```

The distinction between `STARTING` and `WARM` is important because a request arriving while an instance is still starting cannot immediately use that instance.

---

# Cold-Start Model

Cold starts are modeled as **elapsed simulated time**.

For example:

```text
Cold-start time = 300 ms
Execution time  = 50 ms
```

A request requiring a new instance can therefore experience approximately:

```text
300 ms startup
+
50 ms execution
=
350 ms latency
```

A request assigned to an already warm instance does not incur the startup component.

The simulator also models requests that must wait because:

- no warm instance is available,
- existing instances are busy,
- new instances are still starting,
- the configured instance capacity has been reached.

---

# Request Queuing

Requests can enter a queue when immediate execution is not possible.

The simulator distinguishes between:

```text
Request arrives
      ↓
Warm capacity available?
      │
   ┌──┴──┐
   │     │
  Yes    No
   │     │
   ▼     ▼
Execute Queue
         │
         ▼
   Wait for capacity
         │
         ▼
      Execute
```

Queued requests are not incorrectly classified as cold starts simply because they had to wait.

This distinction is important for accurate cold-start measurements.

---

# Controllers

Controllers share a common interface and determine scaling or warm-pool decisions.

The current architecture allows different controller implementations to be plugged into the same simulator.

The main controller progression is:

```text
No Prewarming
      ↓
Fixed Warm Pool
      ↓
Threshold / Reactive
      ↓
Forecasting
      ↓
Uncertainty-Aware Forecasting
      ↓
Reinforcement Learning
```

## No-Prewarm Controller

The no-prewarm controller provides a simple reactive baseline.

It does not proactively maintain additional warm capacity.

```text
Request arrives
      ↓
Warm instance available?
      │
   ┌──┴──┐
   │     │
  Yes    No
   │     │
   ▼     ▼
Execute Start instance
```

This establishes a baseline against which proactive strategies can be compared.

## Fixed Warm Pool Controller

The fixed warm-pool controller attempts to maintain a configured number of warm instances.

For example:

```text
Target warm instances = 3
```

The controller provides a simple proactive baseline.

Its purpose is to answer:

> How much benefit can be obtained simply by keeping a fixed amount of capacity warm?

## Static Controller

The static controller provides another simple capacity-management baseline based on a fixed target.

Static policies are useful because they establish the performance/cost behavior of non-adaptive strategies.

## Threshold Controller

The threshold controller uses system conditions such as queue length to trigger additional capacity.

```text
Queue length
     │
     ▼
Threshold exceeded?
     │
   ┌─┴─┐
  No  Yes
  │    │
  ▼    ▼
Wait Prewarm
```

This represents a reactive scaling strategy.

## Idle Timeout Controller

The idle-timeout controller introduces lifecycle behavior based on how long instances remain unused.

This provides a baseline for studying the trade-off between:

```text
Longer warm retention
        ↕
Lower cold-start probability

versus

Shorter warm retention
        ↕
Lower idle-resource usage
```

---

# Forecasting

The forecasting layer is separated from the controllers.

Current forecasting components include:

```text
Forecasting/
├── baseline.py
└── uncertainty.py
```

The baseline forecasting approach uses a **moving average** of recent demand.

The general flow is:

```text
Recent demand history
        ↓
Moving-average forecast
        ↓
Predicted future demand
        ↓
Prewarming decision
```

The forecasting layer is intentionally separated from the controller so that different forecasting models can later be evaluated without redesigning the simulator.

---

# Uncertainty-Aware Forecasting

Point forecasts alone can be insufficient when demand is highly variable.

The uncertainty model therefore provides an interval around the predicted demand:

```text
             Prediction
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
     Lower   Predicted    Upper
     Bound    Demand      Bound
```

The uncertainty-aware controller can use the upper bound when deciding whether to prewarm.

The conceptual decision is:

```text
Forecast
   +
Forecast uncertainty
   ↓
Upper demand estimate
   ↓
Prewarming decision
```

This allows the project to investigate whether accounting for prediction uncertainty improves robustness during sudden demand increases.

---

# Traffic Generation

Traffic generation is separated from the simulator.

This allows different workload patterns to be evaluated using the same simulation engine.

The current synthetic traffic generator supports:

- Uniform traffic
- Poisson traffic
- Bursty traffic

## Uniform Traffic

Uniform traffic distributes requests evenly across the simulation period.

```text
| | | | | | | | | | |
```

This is useful for stable baseline workloads.

## Poisson Traffic

Poisson traffic introduces stochastic request arrivals using exponentially distributed inter-arrival times.

```text
|   | |    |  |     | |   |
```

This provides a more variable workload while preserving a controllable average arrival rate.

## Bursty Traffic

Bursty traffic models sudden high-intensity demand periods.

```text
Normal traffic:

| | | | | | | | | |

Burst:

| | | |||||||||||| | |
```

Burst behavior is configurable using parameters such as:

```text
burst_probability
burst_multiplier
burst_duration_seconds
```

Example:

```python
from Traffic.synthetic import generate_request_trace

trace = generate_request_trace(
    duration_seconds=60,
    rate_per_second=10,
    seed=42,
    arrival_process="bursty",
    burst_probability=0.2,
    burst_multiplier=4.0,
    burst_duration_seconds=1,
)
```

---

# Reproducibility

Reproducibility is a core design requirement.

Stochastic workload generation uses deterministic random seeds.

For example:

```python
trace1 = generate_request_trace(
    duration_seconds=10,
    rate_per_second=20,
    seed=42,
    arrival_process="poisson",
)

trace2 = generate_request_trace(
    duration_seconds=10,
    rate_per_second=20,
    seed=42,
    arrival_process="poisson",
)
```

The same seed and configuration produce the same workload realization.

This allows experiments to be reproduced reliably.

---

# Workload Specification

Workload configuration is separated from the generated request-level trace.

The conceptual flow is:

```text
WorkloadSpec
     ↓
Traffic Generator
     ↓
TrafficTrace
     ↓
Experiment Runner
     ↓
Simulator
```

A workload can capture parameters such as:

- duration
- request rate
- execution time
- random seed
- arrival process
- burst probability
- burst multiplier
- burst duration

This separation allows a workload definition to be reused across multiple controllers.

---

# Fair Controller Comparison

One of the most important experimental design decisions is that all controllers must receive the **same traffic trace**.

The experiment runner therefore works as follows:

```text
                    TrafficTrace
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      No Prewarm       Fixed         Forecast
          │              │              │
          ▼              ▼              ▼
      Simulator       Simulator      Simulator
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Comparable Results
```

This prevents the invalid comparison:

```text
Controller A → workload realization A
Controller B → workload realization B
```

Instead:

```text
Controller A ─┐
Controller B ─┼──→ SAME workload trace
Controller C ─┘
```

This makes differences in performance attributable to the scheduling policy as much as possible.

---

# Experiment Runner

The `ExperimentRunner` executes multiple controllers against the same `TrafficTrace`.

Controllers can be supplied either as instances or factories.

Example:

```python
from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.no_prewarm import NoPrewarmController

results = runner.run(
    {
        "no_prewarm": lambda: NoPrewarmController(),
        "fixed": lambda: FixedWarmPoolController(
            warm_pool_target=2
        ),
    }
)
```

Each controller receives an independent simulator while using the same workload.

---

# Experiment Results

Results are converted into a common `ExperimentResult` representation.

Current result information includes:

```text
controller_name
total_requests
cold_starts
cold_start_rate
P50 latency
P95 latency
P99 latency
SLO violations
raw simulation result
```

Results can also be converted into tabular rows for further analysis.

Conceptually:

```text
ExperimentResult
       ↓
Comparable rows
       ↓
CSV / DataFrame / Visualization
```

---

# Evaluation Metrics

## Latency

### P50

Median request latency.

### P95

Latency below which approximately 95% of completed requests fall.

### P99

Latency below which approximately 99% of completed requests fall.

These percentiles are important because serverless cold starts can disproportionately affect tail latency.

## Cold-Start Metrics

### Total Cold Starts

Number of requests that experienced a cold-start path.

### Cold-Start Rate

```text
cold-start rate =
cold starts / total requests
```

### SLO Violations

An SLO latency threshold can be configured.

Requests exceeding the configured latency target are counted as SLO violations.

```text
Request latency > SLO threshold
             ↓
        SLO violation
```

---

# Latency vs Resource Trade-Off

The objective is not simply:

> Minimize latency.

Aggressively maintaining warm instances can reduce cold starts, but it can also increase resource usage and cost.

The fundamental trade-off is:

```text
                    Lower latency
                         ▲
                         │
                         │
                         │
Lower cost ◄─────────────┼─────────────► Higher cost
                         │
                         │
                         ▼
                    Higher latency
```

The research therefore aims to investigate policies that provide a favorable balance between:

- user-visible latency
- cold-start frequency
- SLO compliance
- warm-instance usage
- idle-resource cost
- scaling activity

---

# Testing

The repository contains an automated test suite covering the major components of the current system.

Tests currently cover:

- basic repository structure
- simulator initialization
- event ordering
- request arrival
- request completion
- instance startup
- cold-start timing
- prewarming
- request queuing
- concurrency
- controller behavior
- controller interfaces
- forecasting
- forecast uncertainty
- synthetic traffic
- Poisson workloads
- bursty workloads
- workload specifications
- experiment runner behavior
- identical traffic reuse
- experiment result generation
- SLO violation calculation

### Current status

```text
59 / 59 tests passing
```

Run the full suite with:

```bash
pytest -q
```

---

# Research Roadmap

## Phase 0 — Research Framing

- [x] Define serverless cold-start problem
- [x] Identify latency and resource trade-offs
- [x] Define initial research direction
- [ ] Complete detailed literature review
- [ ] Validate research gap
- [ ] Formalize final research question

## Phase 1 — Simulator Foundation

- [x] Discrete-event simulation
- [x] Request lifecycle
- [x] Instance lifecycle
- [x] Cold-start modeling
- [x] Request queue
- [x] Concurrent request handling
- [x] Scaling limits
- [x] Deterministic event ordering
- [x] Basic performance metrics
- [x] Automated simulator tests

## Phase 2 — Baseline Controllers

- [x] No-prewarm controller
- [x] Fixed warm-pool controller
- [x] Static controller
- [x] Threshold-based controller
- [x] Idle-timeout behavior
- [x] Common controller interface
- [x] Controller integration with simulator
- [ ] Systematic baseline evaluation

## Phase 3 — Demand Forecasting

- [x] Moving-average forecasting
- [x] Forecast controller
- [x] Predictive prewarming
- [x] Forecast controller tests
- [ ] Compare forecasting against reactive baselines
- [ ] Evaluate forecasting under different workloads
- [ ] Analyze forecast accuracy vs scheduling performance

## Phase 4 — Uncertainty-Aware Forecasting

- [x] Forecast uncertainty model
- [x] Prediction interval
- [x] Upper-bound demand estimate
- [x] Uncertainty-aware controller
- [x] Controller tests
- [ ] Evaluate sensitivity to forecast error
- [ ] Evaluate uncertainty-aware scheduling under bursty workloads
- [ ] Analyze latency/cost trade-off

## Phase 5 — Reinforcement Learning

- [ ] Define RL state representation
- [ ] Define action space
- [ ] Formalize reward function
- [ ] Implement RL environment
- [ ] Select RL algorithm
- [ ] Train RL agent
- [ ] Validate training stability
- [ ] Evaluate RL against all baseline controllers
- [ ] Analyze learned scaling behavior

## Phase 6 — Robustness & Generalization

- [ ] Evaluate unseen workloads
- [ ] Test sudden traffic changes
- [ ] Test different burst patterns
- [ ] Test different cold-start times
- [ ] Test different SLO targets
- [ ] Analyze sensitivity to forecast error
- [ ] Evaluate policy stability

## Phase 7 — Hybrid Strategy

Potential future direction:

```text
Demand Forecast
       +
Forecast Uncertainty
       +
Reinforcement Learning
```

This phase will only be pursued if experimental results demonstrate that the additional complexity provides a meaningful advantage.

---

# Planned Workload Matrix

The experimental workload matrix will include:

```text
Constant
   │
   ├── Baselines
   ├── Forecasting
   └── Uncertainty-Aware

Periodic
   │
   ├── Baselines
   ├── Forecasting
   └── Uncertainty-Aware

Bursty
   │
   ├── Baselines
   ├── Forecasting
   └── Uncertainty-Aware

Step Changes
   │
   ├── Baselines
   ├── Forecasting
   └── Uncertainty-Aware

Stochastic
   │
   ├── Baselines
   ├── Forecasting
   └── Uncertainty-Aware
```

This workload matrix will eventually provide the evaluation environment for the RL scheduler.

---

# Planned Research Questions

### RQ1 — Reactive vs Predictive Scheduling

> Does demand forecasting reduce cold-start latency compared with reactive scaling policies?

### RQ2 — Forecast Uncertainty

> Does explicitly modeling forecast uncertainty improve scheduling robustness during unexpected demand changes?

### RQ3 — Reinforcement Learning

> Can reinforcement learning learn a warm-instance scheduling policy that improves the latency/resource trade-off over manually designed policies?

### RQ4 — Generalization

> Does the learned RL policy generalize to workload patterns and system configurations not observed during training?

### RQ5 — Complexity vs Benefit

> Does the additional complexity of forecasting, uncertainty modeling, or RL produce a sufficiently large improvement to justify its overhead?

---

# Future RL Architecture

The intended RL formulation is:

```text
                  ┌────────────────────┐
                  │ Traffic / Workload │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Current System     │
                  │ State              │
                  │                    │
                  │ • warm instances   │
                  │ • starting         │
                  │ • queue length     │
                  │ • active requests  │
                  │ • demand           │
                  │ • forecast         │
                  │ • uncertainty      │
                  └─────────┬──────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   RL Agent    │
                    └───────┬───────┘
                            │
                            ▼
                      Scaling Action
                            │
                            ▼
                  ┌──────────────────┐
                  │ Serverless       │
                  │ Simulator        │
                  └────────┬─────────┘
                           │
                           ▼
                         Reward
                           │
                           └──────► RL Agent
```

The exact state representation, action space, reward formulation, and RL algorithm will be finalized after the baseline and forecasting experiments establish the behavior of the system.

---

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd Serverless-coldstart-simulator
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate the environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the tests

```bash
pytest -q
```

---

# Example: Generate a Workload

```python
from Traffic.synthetic import generate_request_trace

trace = generate_request_trace(
    duration_seconds=60,
    rate_per_second=10,
    execution_time_ms=50,
    seed=42,
    arrival_process="bursty",
    burst_probability=0.2,
    burst_multiplier=4.0,
    burst_duration_seconds=1,
)
```

The resulting `TrafficTrace` can then be reused across different controllers.

---

# Example: Compare Controllers

```python
from Controllers.fixed_pool import FixedWarmPoolController
from Controllers.no_prewarm import NoPrewarmController
from Experiments.runner import ExperimentRunner
from Simulator.config import SimulationConfig
from Traffic.synthetic import generate_request_trace

config = SimulationConfig(
    duration_seconds=10,
    request_rate_per_second=10,
    cold_start_time_ms=300,
    execution_time_ms=50,
)

trace = generate_request_trace(
    duration_seconds=10,
    rate_per_second=10,
    execution_time_ms=50,
    seed=42,
)

runner = ExperimentRunner(config, trace)

results = runner.run(
    {
        "no_prewarm": lambda: NoPrewarmController(),
        "fixed_pool": lambda: FixedWarmPoolController(
            warm_pool_target=2
        ),
    }
)

rows = runner.as_rows(results)
```

The important property is that both controllers receive the **same `trace`**.

---

# Future Experimental Output

The eventual experiment pipeline is intended to produce structured results such as:

```text
Controller       P50     P95     P99     Cold Start Rate     SLO Violations
-----------------------------------------------------------------------------
No Prewarm       ...     ...     ...          ...                 ...
Fixed Pool       ...     ...     ...          ...                 ...
Threshold        ...     ...     ...          ...                 ...
Forecast         ...     ...     ...          ...                 ...
Uncertainty      ...     ...     ...          ...                 ...
RL               ...     ...     ...          ...                 ...
```

These results can then be used to generate:

- latency percentile plots
- cold-start comparisons
- SLO violation plots
- resource/cost trade-off plots
- scaling behavior plots
- workload-vs-capacity plots
- RL convergence curves
- robustness comparisons
- Pareto-frontier analysis

---

# Research Direction

The project is intentionally structured so that increasingly sophisticated decision-making mechanisms can be evaluated without changing the fundamental simulator.

The long-term architecture is:

```text
                         Workload
                            │
                            ▼
                    ┌───────────────┐
                    │ Traffic Trace │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Simulator   │
                    └───────┬───────┘
                            │
                            ▼
                     System State
                            │
            ┌───────────────┼────────────────┐
            │               │                │
            ▼               ▼                ▼
        Reactive        Forecast       RL Controller
        Policies        + Uncertainty
            │               │                │
            └───────────────┼────────────────┘
                            ▼
                    Scaling Decision
                            │
                            ▼
                     System Response
                            │
                            ▼
                         Metrics
                            │
                            ▼
                       Evaluation
```

The ultimate goal is not simply to build an RL model.

The goal is to determine **whether intelligent scheduling can produce a meaningful improvement in serverless cold-start performance under different workload conditions while maintaining acceptable resource and cost overhead.**

---

# Project Development Status

🚧 **Active Research / Development**

Current development progression:

```text
Research Framing
       │
       ▼
Reliable Simulator
       │
       ▼
Baseline Controllers
       │
       ▼
Demand Forecasting
       │
       ▼
Uncertainty-Aware Scheduling
       │
       ▼
Fair Experiment Infrastructure
       │
       ▼
[ CURRENT STAGE ]
Controlled Baseline Experiments
       │
       ▼
Reinforcement Learning
       │
       ▼
Robustness & Generalization
       │
       ▼
Potential Hybrid Strategy
       │
       ▼
Final Research Evaluation
```

---

# Development Principles

This repository is being developed incrementally with an emphasis on:

- correctness
- reproducibility
- modularity
- fair experimentation
- testability
- measurable improvements
- research validity

The project intentionally avoids introducing sophisticated models before establishing reliable simulation and baseline behavior.

The progression is therefore:

```text
Correct Simulator
      ↓
Reliable Baselines
      ↓
Controlled Experiments
      ↓
Forecasting
      ↓
Uncertainty
      ↓
RL
      ↓
Robustness
      ↓
Research Contribution
```

---

# License

This project is currently intended for academic and research use.
