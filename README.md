# Serverless Cold-Start Reduction & Intelligent Function Scheduling

This repository is a research-focused simulator for studying how scheduling and warm-pool management affect serverless cold starts under bursty and changing workloads.

## Project goal

The main objective is to model and compare controller strategies for reducing user-visible cold-start latency while controlling resource and idle-capacity cost. The project is intentionally designed to compare simpler baselines against more advanced policies, including forecasting and reinforcement learning.

## Research direction

The long-term plan follows the progression in the project context:

1. Build a faithful discrete-event simulator
2. Generate reproducible traffic traces
3. Compare baseline policies
4. Add forecasting-based prewarming
5. Add uncertainty-aware scheduling
6. Add RL-based adaptive warm-pool control
7. Evaluate trade-offs with metrics and experiment runs

## Core areas

- `Simulator/`: event-driven simulation logic, instance model, request flow, metrics
- `Traffic/`: synthetic and real workload generation
- `Controllers/`: static, reactive, and threshold-based policies
- `Forecasting/`: demand prediction and uncertainty-aware strategy support
- `RL/`: environment, reward, and learning components
- `Experiments/`: reproducible runs and comparisons
- `Results/`: raw outputs, processed metrics, figures
- `tests/`: validation of simulator behavior and controller logic

## Recommended development flow

- Start with a minimal but trustworthy simulator
- Use fixed seeds and shared traffic traces for fair comparisons
- Add one controller at a time
- Validate metrics before introducing forecasting or RL
- Keep assumptions explicit and reproducible

## Current status

This repository currently contains the initial project skeleton and will be expanded into the simulator, controllers, and experiment runner in upcoming steps.

