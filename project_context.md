# Serverless Cold-Start Reduction & Intelligent Function Scheduling

## Project Context / Single Source of Truth

> **Purpose:** Persistent context for AI coding assistants working on
> this repository. Read this before making architectural, simulator,
> controller, experiment, or research-methodology changes.

------------------------------------------------------------------------

# 1. Project Identity

**Working title:** Serverless Cold-Start Reduction & Intelligent
Function Scheduling

Possible future titles: - Adaptive Warm-Pool Management and Function
Scheduling for Latency- and Cost-Aware Serverless Computing - RL-Based
Serverless Scheduling for Latency- and Cost-Aware Function Execution -
Intelligent Warm-Pool Management for Serverless Functions Under Bursty
Workloads

The final title is not fixed.

## Core research question

> Can intelligent scheduling, particularly reinforcement-learning-based
> warm-pool management, reduce the user-visible impact of serverless
> cold starts while keeping resource/cost overhead under control?

Specific version:

> Can reinforcement-learning-based scheduling reduce serverless
> cold-start latency while keeping cost under control?

**Important:** RL must be evaluated against simpler policies. Do not
assume RL is better.

------------------------------------------------------------------------

# 2. Research Problem

Serverless/FaaS platforms dynamically create and terminate function
instances.

A request may encounter: - a **warm instance** → execution starts
quickly - a **cold instance** → infrastructure/runtime/application
initialization is required

Cold-start latency is especially important under: - bursty traffic -
sudden demand changes - sparse traffic - unpredictable workloads -
rapidly changing request rates

The project focuses primarily on **mitigating user-visible cold-start
impact through scheduling and prewarming**, not necessarily making the
underlying platform's intrinsic startup mechanism faster.

The central scheduling problem is:

> How many instances should be kept warm, when should new instances be
> prewarmed, and when should idle instances be evicted, given changing
> demand and competing latency/cost objectives?

------------------------------------------------------------------------

# 3. Research Direction

The project deliberately progresses from simple to complex:

1.  Reactive/static baselines
2.  Threshold-based policies
3.  Forecast-based predictive prewarming
4.  Forecast + uncertainty-aware policies
5.  Reinforcement-learning-based adaptive scheduling
6.  Potential hybrid controller

The scientific question is not simply "Can RL work?"

It is:

> What additional value, if any, does increasingly intelligent
> scheduling provide over simpler policies?

------------------------------------------------------------------------

# 4. Scope

## Main focus

**Serverless function lifecycle management + warm-pool management +
scheduling + cold-start mitigation.**

## Not primarily

-   geographic CDN design
-   generic Kubernetes autoscaling
-   production AWS Lambda replacement
-   generic load balancing
-   an RL tutorial
-   a benchmark with no controller comparison

The project is a controlled research simulator and experiment framework.

------------------------------------------------------------------------

# 5. High-Level Architecture

``` text
                   Incoming Requests
                          |
                          v
                  +----------------+
                  |   API Gateway  |
                  +----------------+
                          |
                          v
                +--------------------+
                | Scheduler /       |
                | Controller        |
                |                    |
                | Static / Threshold |
                | Forecast / RL      |
                +--------------------+
                          |
             +------------+------------+
             |            |            |
             v            v            v
        Function 1   Function 2   Function N
        [WARM]       [WARM]       [STARTING]
             |            |            |
             +------------+------------+
                          |
                          v
                       Execute
```

The scheduler observes system state and makes capacity/lifecycle
decisions.

Potential actions: - route to warm instance - prewarm/start instance -
retain warm instance - evict/terminate instance - queue request -
reroute request - allocate capacity

The simulator may simplify this action space initially.

------------------------------------------------------------------------

# 6. Cold-Start Model

Conceptually:

``` text
Cold-start latency
    =
    infrastructure/startup delay
    + runtime initialization
    + application initialization
```

Initially these can be represented by configurable stochastic delays.
The simulator does not need to perfectly reproduce one cloud provider.

**Fairness requirement:** every controller must experience the same
underlying simulator and latency model.

------------------------------------------------------------------------

# 7. Core Simulator

Use a **single discrete-event Python simulator** for fair comparison.

It should model: - request arrivals - request queues - concurrency -
function instances - instance lifecycle - cold starts - warm execution -
execution duration - prewarming/scaling - instance termination -
scheduler decisions - resource consumption - cost - latency - SLO
violations

## Instance lifecycle

``` text
TERMINATED
    |
    | start/prewarm
    v
STARTING
    |
    | startup complete
    v
WARM
    |
    | idle timeout / eviction
    v
TERMINATED
```

A STARTING instance consumes startup time and normally cannot
immediately serve a request.

------------------------------------------------------------------------

# 8. Traffic / Workload Generation

The simulator must support controlled, reproducible traffic.

Primary variable:

``` text
lambda(t)
```

Traffic patterns should include:

### Constant

Fixed request rate. Basic sanity testing.

### Periodic

Predictable rises and falls. Useful for forecasting.

### Bursty

Sudden spikes and drops. Important for cold-start behavior.

### Step changes

``` text
low -> high
high -> low
```

Useful for adaptation tests.

### Random/stochastic

Adds uncertainty.

### Synthetic traces

Must support fixed random seeds.

Real traces may be added later if available.

------------------------------------------------------------------------

# 9. Fair Comparison Methodology

All controllers should run on the **same simulator** and, when possible,
the **same exact traffic trace**.

``` text
                    Same Traffic Trace
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
       Static             Forecast           RL
       Policy              Policy           Policy
          |                |                |
          v                v                v
      Simulator         Simulator        Simulator
          |                |                |
          +----------------+----------------+
                           |
                           v
                     Compare Metrics
```

Controllers should be interchangeable:

``` python
simulator.run(controller=StaticController(...))
simulator.run(controller=ForecastController(...))
simulator.run(controller=RLController(...))
```

This is a core research-methodology decision.

------------------------------------------------------------------------

# 10. Controllers / Baselines

## A1. No prewarming

Create instances only when needed.

Important baseline.

## A2. Fixed warm pool

Maintain a fixed number of warm instances:

``` text
warm_instances = K
```

## A3. Reactive threshold

Prewarm/scale when demand or queue length crosses a threshold:

``` python
if queue_length > threshold:
    prewarm()
```

## A4. Idle timeout

Terminate instances after remaining idle for a configurable period.

These establish baseline latency/cost behavior.

------------------------------------------------------------------------

# 11. Forecast-Based Controller

Next introduce demand prediction:

``` text
observations
    |
    v
forecast model
    |
    v
predicted demand for next H seconds
    |
    v
prewarming decision
```

Start simple: - moving average - exponential smoothing - simple
statistical model - supervised ML model

Do not introduce a complex deep-learning forecasting system unless
experiments justify it.

Evaluate both: 1. prediction quality 2. downstream scheduling
performance

------------------------------------------------------------------------

# 12. Forecast Uncertainty

Point predictions can be wrong.

Example:

``` text
Predicted demand = 100 requests/s
Actual demand    = 170 requests/s
```

Represent uncertainty where possible:

``` text
prediction = 100
uncertainty = +/- 30
```

Potential behavior:

``` text
higher uncertainty
       ↓
larger safety capacity
       ↓
lower cold-start risk
       ↓
higher resource cost
```

This is an important research trade-off.

------------------------------------------------------------------------

# 13. Reinforcement Learning Controller

RL interacts with the simulator:

``` text
             +----------------------+
             |       Simulator      |
             +----------------------+
                |              ^
             state            action
                |              |
                v              |
             +------------------+
             |    RL Agent      |
             +------------------+
```

At each decision step:

1.  Observe state
2.  Select action
3.  Simulator executes action
4.  Requests/instances evolve
5.  Receive reward
6.  Observe next state
7.  Repeat

RL is a later phase, not the starting point.

------------------------------------------------------------------------

# 14. RL State

Candidate state variables:

## Demand

-   current request rate
-   recent request-rate history
-   demand trend
-   predicted demand

## Capacity

-   warm-instance count
-   starting-instance count
-   total active instances
-   available capacity

## Queue

-   current queue length
-   queue growth rate
-   queued request age

## Performance

-   recent latency
-   recent P95-like latency
-   cold-start count
-   cold-start ratio
-   SLO slack/violations

## Resources

-   CPU utilization
-   memory utilization
-   warm-instance duration
-   idle capacity

## Forecast

-   predicted demand
-   prediction error
-   prediction uncertainty

Start with a minimal state and expand only when justified.

------------------------------------------------------------------------

# 15. RL Action Space

Candidate discrete actions:

``` text
0 = maintain current capacity
1 = prewarm one instance
2 = prewarm multiple instances
3 = retain warm capacity
4 = evict one instance
5 = evict multiple instances
```

Keep the action space manageable initially.

------------------------------------------------------------------------

# 16. RL Reward

Conceptual multi-objective reward:

``` text
R = -alpha * latency
    - beta * cold_start_penalty
    - gamma * resource/cost_penalty
    - delta * SLO_violation_penalty
```

A simplified alternative discussed:

``` text
R = -lambda1 * cost
    -lambda2 * SLO_violations
    -lambda3 * latency
```

**Reward weights are NOT finalized.**

Do not arbitrarily tune them until: - objectives are clearly defined -
metrics are normalized - sensitivity to weights can be studied

The reward should not allow one metric to dominate purely because of
numerical scale.

------------------------------------------------------------------------

# 17. Multi-Objective Nature

The problem has competing objectives.

``` text
more warm instances
        ↓
lower cold-start probability
        ↓
lower latency
        ↓
higher resource/cost usage
```

versus:

``` text
fewer warm instances
        ↓
lower cost
        ↓
higher cold-start probability
```

Therefore the target is not simply "minimize cold starts."

The actual problem is:

> Find a useful latency-SLO-resource/cost trade-off under changing
> demand.

Energy may be considered later, but it is not required for the first
simulator.

------------------------------------------------------------------------

# 18. Metrics

Every controller must produce comparable metrics.

## Latency

-   P50
-   P95
-   P99

## Cold starts

-   cold-start count
-   cold-start ratio
-   average cold-start delay
-   cold-start contribution to latency

## SLO

-   SLO violation count
-   SLO violation percentage
-   time spent violating SLO

## Resource utilization

-   average active instances
-   average warm instances
-   peak instances
-   CPU utilization if modeled
-   memory utilization if modeled

## Cost

-   warm-instance seconds
-   active-instance seconds
-   estimated execution cost
-   idle/warm capacity cost

## Throughput

-   completed requests/sec
-   total completed requests

## Scaling behavior

-   scale-up events
-   scale-down events
-   scaling churn

## Forecasting

-   MAE
-   RMSE
-   prediction interval coverage, if uncertainty is modeled

------------------------------------------------------------------------

# 19. Terminology

### Cold-start latency

Additional latency when an instance must initialize before serving a
request.

### P50

Median latency; 50% of requests are at or below this value.

### P95

95% of requests are at or below this value. Important tail metric.

### P99

99% of requests are at or below this value. Captures extreme tail
behavior.

### SLO violation

A request/interval that fails to meet the defined service objective.

Example:

``` text
SLO = 200 ms
request = 350 ms
=> violation
```

### Resource utilization

How much compute capacity is actually being used.

### Idle/warm-instance cost

Cost of maintaining capacity that is available but not actively doing
useful work.

### Throughput

Completed requests per unit time.

------------------------------------------------------------------------

# 20. Experiment Matrix

  -----------------------------------------------------------------------
  Controller        Prediction        Adaptation        Purpose
  ----------------- ----------------- ----------------- -----------------
  No prewarm        No                Reactive          Baseline

  Fixed warm pool   No                Fixed             Cost/latency
                                                        reference

  Threshold         No                Reactive          Simple
                                                        intelligent
                                                        baseline

  Forecast          Yes               Predictive        Test prediction
                                                        benefit

  Forecast +        Yes               Predictive        Test uncertainty
  uncertainty                                           handling

  RL                Optional          Adaptive          Main research
                                                        candidate

  Hybrid            Yes + RL          Adaptive          Future extension
  -----------------------------------------------------------------------

**Do not assume RL wins.** The experiment determines the result.

------------------------------------------------------------------------

# 21. Experiment Dimensions

Vary:

## Traffic intensity

-   low
-   medium
-   high

## Burstiness

-   low
-   medium
-   high

## Predictability

-   predictable
-   partially predictable
-   highly unpredictable

## Cold-start duration

-   low
-   medium
-   high

## SLO target

Example temporary values:

``` text
100 ms
200 ms
500 ms
```

## Cost sensitivity

Change the relative penalty of maintaining warm capacity.

## Forecast quality

Introduce controlled forecast error.

This helps determine whether predictive scheduling remains useful when
forecasts are imperfect.

------------------------------------------------------------------------

# 22. Overall Experimental Workflow

``` text
Research Question
      ↓
Define simulator assumptions
      ↓
Build traffic generator
      ↓
Build event-driven simulator
      ↓
Implement baseline policies
      ↓
Validate simulator
      ↓
Run baseline experiments
      ↓
Analyze weaknesses
      ↓
Implement forecasting
      ↓
Evaluate forecasting
      ↓
Add uncertainty
      ↓
Implement RL
      ↓
Train RL in simulator
      ↓
Evaluate RL on unseen traces
      ↓
Compare all approaches
      ↓
Statistical analysis
      ↓
Research findings
      ↓
Paper/report
```

------------------------------------------------------------------------

# 23. Train/Validation/Test Separation

For ML and RL, do not evaluate only on development workloads.

Conceptual split:

``` text
Training traces
      ↓
ML/RL development
      ↓
Validation traces
      ↓
Hyperparameter decisions
      ↓
Frozen controller
      ↓
Unseen test traces
      ↓
Final evaluation
```

Example:

``` text
Train:      seeds 1-50
Validation: seeds 51-70
Test:       seeds 71-100
```

Exact split can change.

Final test traces should remain unseen during policy development.

------------------------------------------------------------------------

# 24. Statistical Evaluation

Simulation is stochastic.

For each configuration:

``` text
multiple random seeds
        ↓
collect metrics
        ↓
mean / median
confidence intervals
distributions
        ↓
compare controllers
```

Avoid conclusions based on a single lucky run.

------------------------------------------------------------------------

# 25. Recommended Repository Structure

``` text
serverless-cold-start/
│
├── README.md
├── project_context.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── configs/
│   ├── base.yaml
│   ├── low_load.yaml
│   ├── bursty.yaml
│   ├── high_load.yaml
│   └── experiments/
│
├── simulator/
│   ├── __init__.py
│   ├── engine.py
│   ├── events.py
│   ├── environment.py
│   ├── request.py
│   ├── instance.py
│   ├── queue.py
│   ├── metrics.py
│   ├── config.py
│   └── runner.py
│
├── traffic/
│   ├── __init__.py
│   ├── generators.py
│   ├── distributions.py
│   ├── traces.py
│   └── scenarios.py
│
├── controllers/
│   ├── __init__.py
│   ├── base.py
│   ├── no_prewarm.py
│   ├── fixed_pool.py
│   ├── threshold.py
│   └── idle_timeout.py
│
├── forecasting/
│   ├── __init__.py
│   ├── baseline.py
│   ├── models.py
│   ├── uncertainty.py
│   └── evaluation.py
│
├── rl/
│   ├── __init__.py
│   ├── environment.py
│   ├── state.py
│   ├── actions.py
│   ├── reward.py
│   ├── train.py
│   ├── evaluate.py
│   └── policies/
│
├── experiments/
│   ├── run_baselines.py
│   ├── run_forecasting.py
│   ├── run_rl.py
│   ├── run_all.py
│   └── seeds.py
│
├── results/
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   └── tables/
│
├── notebooks/
│   ├── traffic_analysis.ipynb
│   ├── baseline_analysis.ipynb
│   ├── forecasting_analysis.ipynb
│   └── rl_analysis.ipynb
│
├── tests/
│   ├── test_simulator.py
│   ├── test_instances.py
│   ├── test_queue.py
│   ├── test_metrics.py
│   ├── test_traffic.py
│   └── test_controllers.py
│
└── docs/
    ├── architecture.md
    ├── experiment_protocol.md
    └── research_notes.md
```

This structure can evolve. Do not create unnecessary complexity before
the simulator works.

------------------------------------------------------------------------

# 26. Simulator Module Responsibilities

### `engine.py`

Discrete-event simulation engine.

### `events.py`

Events such as:

``` text
REQUEST_ARRIVAL
INSTANCE_START
INSTANCE_READY
REQUEST_START
REQUEST_COMPLETE
INSTANCE_TERMINATE
SCHEDULER_DECISION
```

### `request.py`

Request representation:

``` text
id
arrival_time
start_time
completion_time
execution_time
cold_start
latency
```

### `instance.py`

Instance lifecycle and state.

### `queue.py`

Pending requests.

### `environment.py`

Global simulation state exposed to controllers/RL.

### `metrics.py`

Metric collection and aggregation.

### `config.py`

Simulation parameters.

### `runner.py`

Experiment execution.

------------------------------------------------------------------------

# 27. Minimal First Version

Do not build the entire architecture immediately.

First milestone:

``` text
serverless-cold-start/
├── simulator/
├── traffic/
├── controllers/
├── experiments/
├── results/
├── tests/
├── README.md
└── project_context.md
```

First implement:

``` text
Traffic Generator
       ↓
Simulator
       ↓
No-Prewarm Controller
       ↓
Metrics
       ↓
CSV/JSON result
```

Then add one controller at a time.

------------------------------------------------------------------------

# 28. Example Simulation Flow

``` text
request arrives
      ↓
scheduler checks warm instances
      ↓
warm instance available?
      |
   +--+--+
   |     |
  YES    NO
   |     |
   v     v
execute  start instance
         |
         v
    cold-start delay
         |
         v
       execute
         |
         v
   record latency
         |
         v
  instance becomes warm
         |
         v
 scheduler decides retain/evict
```

Under bursty traffic:

``` text
low demand
     ↓
few warm instances
     ↓
sudden burst
     ↓
queue grows
     ↓
cold starts
     ↓
tail latency rises
     ↓
scheduler responds
```

------------------------------------------------------------------------

# 29. Configuration Philosophy

Do not hardcode experimental parameters.

Use configuration files.

Example:

``` yaml
simulation:
  duration: 3600
  seed: 42

traffic:
  type: bursty
  base_rate: 10
  peak_rate: 100

function:
  execution_time_ms: 50
  cold_start_time_ms: 300

instance:
  idle_timeout: 60
  max_instances: 100

slo:
  latency_ms: 200
```

Values above are examples, not final research parameters.

------------------------------------------------------------------------

# 30. Reproducibility

Every experiment should record: - controller - simulator version -
configuration - random seed - traffic type - traffic parameters - model
version - RL hyperparameters - forecast model - timestamp - output
metrics

A result should be reproducible from its configuration.

------------------------------------------------------------------------

# 31. Result Storage

Raw:

``` text
results/raw/
    baseline_seed_001.json
    baseline_seed_002.json
    rl_seed_001.json
    rl_seed_002.json
```

Processed:

``` text
results/processed/
    controller_comparison.csv
```

Figures:

``` text
results/figures/
    latency_percentiles.png
    cold_start_rate.png
    cost_vs_latency.png
    slo_violations.png
```

------------------------------------------------------------------------

# 32. Important Plots

Eventually produce:

1.  **Latency comparison** --- controller vs P50/P95/P99
2.  **Cold-start comparison** --- controller vs cold-start rate
3.  **Cost-latency trade-off** --- cost vs P95 latency
4.  **SLO violations** --- controller vs violation percentage
5.  **Warm instances over time**
6.  **Demand vs capacity over time**
7.  **RL learning curve** --- episode vs average reward

------------------------------------------------------------------------

# 33. Important Research Trade-Off

A scheduler may not minimize every metric simultaneously.

Example:

``` text
Policy A:
very low latency
high cost

Policy B:
moderate latency
low cost

Policy C:
different trade-off under bursts
```

The goal is to characterize trade-offs, not force every metric into one
simplistic conclusion.

------------------------------------------------------------------------

# 34. Potential Novelty

Novelty is **not assumed**.

Potential contribution areas: - systematic comparison of increasingly
intelligent schedulers - uncertainty-aware prewarming - adaptive
warm-pool management - RL scheduling under bursty demand - robustness to
forecast error - multi-objective latency/cost scheduling -
generalization across workload regimes - reproducible
simulator/benchmark methodology

The actual contribution must be determined after literature review and
experiments.

Do not claim: - "RL is novel" without verifying literature - "RL is
better" without experimental evidence

------------------------------------------------------------------------

# 35. Potential Research Questions

### RQ1

How much can simple prewarming policies reduce cold-start impact
compared with purely reactive execution?

### RQ2

Does demand forecasting improve warm-pool management?

### RQ3

How does forecast uncertainty affect prewarming decisions?

### RQ4

Can RL learn a better latency-cost trade-off than
fixed/threshold/forecast policies?

### RQ5

How robust is an RL policy to traffic patterns not seen during training?

### RQ6

When does the additional complexity of RL provide meaningful benefit
over simpler approaches?

These may be narrowed after literature review.

------------------------------------------------------------------------

# 36. Current Priorities

Do **not** immediately build a sophisticated RL agent.

Priority:

``` text
Understand problem
      ↓
Build reliable simulator
      ↓
Generate controlled traffic
      ↓
Implement simple baselines
      ↓
Create trustworthy comparison framework
      ↓
Add forecasting
      ↓
Add uncertainty
      ↓
Add RL
```

The simulator is foundational.

If the simulator is wrong, every ML/RL result becomes questionable.

------------------------------------------------------------------------

# 37. Coding Principles

1.  Keep simulation logic separate from controller logic.
2.  Controllers should not directly manipulate hidden simulator
    internals.
3.  Use clear interfaces.
4.  Make randomness seedable.
5.  Avoid hardcoded experiment parameters.
6.  Write tests for lifecycle transitions.
7.  Keep results reproducible.
8.  Log enough information to debug unexpected behavior.
9.  Avoid premature optimization.
10. Prefer simple implementations before sophisticated ones.
11. Avoid ML/RL dependencies until their phase begins.
12. Keep baseline policies deterministic when possible.

------------------------------------------------------------------------

# 38. Controller Interface

Conceptual interface:

``` python
class Controller:
    def decide(self, state):
        """
        Receive observable simulator state.
        Return a scheduling action.
        """
        raise NotImplementedError
```

Example:

``` python
controller = ThresholdController(config)

result = simulator.run(
    traffic=traffic_trace,
    controller=controller
)
```

All controllers should use a common interface.

------------------------------------------------------------------------

# 39. Simulator Interface

Conceptual interface:

``` python
result = simulator.run(
    traffic_trace=trace,
    controller=controller,
    config=config,
    seed=seed
)
```

Result should expose metrics such as:

``` python
{
    "latency": ...,
    "p50": ...,
    "p95": ...,
    "p99": ...,
    "cold_start_rate": ...,
    "slo_violations": ...,
    "cost": ...,
    "throughput": ...,
}
```

------------------------------------------------------------------------

# 40. Development Phases

## Phase 0 --- Research framing

-   literature review
-   identify existing approaches
-   identify possible research gap
-   define research question
-   define metrics
-   define assumptions
-   define experiment plan

Output:

``` text
clear research question
+
experiment protocol
```

## Phase 1 --- Simulator

Build: - requests - arrivals - queues - instances - warm/cold states -
startup delay - execution time - completion - metrics

No RL yet.

## Phase 2 --- Baselines

Implement: 1. no prewarming 2. fixed warm pool 3. threshold/reactive 4.
idle timeout

## Phase 3 --- Forecasting

Add demand prediction and predictive prewarming.

## Phase 4 --- Forecast + uncertainty

Study whether uncertainty-aware decisions improve robustness.

## Phase 5 --- RL

Implement: - RL environment - state - actions - reward - training -
evaluation

## Phase 6 --- Robustness/generalization

Test unseen: - traffic - burst patterns - cold-start times - SLOs -
request rates - forecast errors

## Phase 7 --- Hybrid

Potential:

``` text
Forecast
    +
Uncertainty
    +
RL
```

Only pursue this if earlier results justify it.

------------------------------------------------------------------------

# 41. Definition of Done --- First Milestone

``` text
✓ Requests can be generated
✓ Requests enter simulator
✓ Instances can start
✓ Cold starts are modeled
✓ Warm instances can serve requests
✓ Instances can become idle
✓ Instances can terminate
✓ Requests can queue
✓ Latency is measured
✓ Cold starts are measured
✓ P50/P95/P99 can be calculated
✓ SLO violations can be calculated
✓ Resource usage can be measured
✓ Results can be exported
✓ Random seeds reproduce results
✓ Basic simulator tests pass
✓ A baseline experiment can be rerun exactly
```

At this point the project has a valid experimental foundation.

------------------------------------------------------------------------

# 42. Current Decisions

Treat these as current defaults unless explicitly changed:

-   Use **one discrete-event Python simulator** for fair comparison.
-   Use identical/reproducible traffic traces across controllers.
-   Controllers are interchangeable.
-   Compare **static/reactive → forecast → uncertainty-aware → RL →
    possible hybrid**.
-   Evaluate P50/P95/P99.
-   Evaluate cold-start behavior.
-   Evaluate SLO violations.
-   Evaluate resource utilization.
-   Evaluate idle/warm-instance cost.
-   Evaluate throughput.
-   Evaluate scaling churn.
-   Keep simulator assumptions configurable.
-   Use reproducible random seeds.
-   Do not assume RL is superior before experimentation.
-   Primary goal is cold-start **mitigation/user-impact reduction**, not
    necessarily changing intrinsic platform startup mechanics.

------------------------------------------------------------------------

# 43. Explicitly Unresolved Decisions

Do not silently finalize these:

-   exact simulator time resolution
-   exact instance startup distribution
-   exact execution-time distribution
-   exact SLO target
-   exact cost model
-   exact RL algorithm
-   exact RL state representation
-   exact RL action space
-   exact reward weights
-   exact forecast model
-   exact uncertainty model
-   exact workload distributions
-   whether CPU/memory should be simulated initially
-   whether energy should be included
-   final research title
-   final research novelty/contribution
-   final literature-based baseline selection

Temporary prototype values are allowed, but label them as experimental
defaults.

------------------------------------------------------------------------

# 44. Immediate Next Steps

1.  Create GitHub repository.

2.  Add:

    ``` text
    project_context.md
    README.md
    .gitignore
    requirements.txt
    ```

3.  Build smallest simulator.

4.  Create simple traffic generator.

5.  Implement no-prewarm baseline.

6.  Implement metrics.

7.  Run one reproducible experiment.

8.  Add fixed warm pool.

9.  Add threshold policy.

10. Create comparison script.

Only after this should forecasting and RL be added.

------------------------------------------------------------------------

# 45. AI Assistant Instructions

Any AI coding assistant working on this repository should:

### Before implementing

Read:

``` text
project_context.md
README.md
```

### Before changing architecture

Check whether the change affects: - research assumptions - experiment
fairness - controller interface - metrics - simulator behavior -
reproducibility

### When uncertain

Do not silently invent a research assumption.

State the decision that is required and its experimental impact.

### When adding a dependency

Explain why it is needed.

### When changing simulator behavior

Update: - tests - documentation - experiment assumptions

### When changing metrics

Ensure every controller remains comparable.

### Research integrity rule

Do not alter the simulator or evaluation protocol in a way that gives
one controller an unfair advantage.

------------------------------------------------------------------------

# 46. Long-Term End State

``` text
                 Traffic Generator
                        |
                        v
              +-------------------+
              | Discrete-Event    |
              | Serverless        |
              | Simulator         |
              +-------------------+
                        |
              +---------+---------+
              |                   |
        Controller              Metrics
              |                   |
     +--------+--------+          |
     |        |        |          |
   Static  Forecast    RL         |
     |        |        |          |
     +--------+--------+----------+
                        |
                        v
               Experimental Data
                        |
                        v
              Statistical Analysis
                        |
                        v
                Research Findings
```

The final system should answer:

> Under which workload conditions does each scheduling strategy work,
> what latency/cost/SLO trade-offs does it produce, and does adaptive RL
> scheduling provide enough benefit to justify its additional
> complexity?

------------------------------------------------------------------------

# 47. Guiding Principle

> **Do not optimize the algorithm before building a trustworthy
> experiment.**

The simulator, workload generation, reproducibility, baselines, and
evaluation methodology are the foundation.

RL is a later component, not the starting point.
