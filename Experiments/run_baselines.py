from __future__ import annotations

from Controllers import FixedWarmPoolController, NoPrewarmController, ThresholdController


def main():
    """Placeholder entry point for baseline experiment runs."""
    controllers = [
        NoPrewarmController(),
        FixedWarmPoolController(warm_pool_target=2),
        ThresholdController(threshold=5),
    ]
    for controller in controllers:
        print(type(controller).__name__)


if __name__ == "__main__":
    main()
