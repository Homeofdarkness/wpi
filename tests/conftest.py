import random

import pytest


@pytest.fixture(autouse=True)
def _test_environment(monkeypatch):
    # Do not create log files during tests
    monkeypatch.setenv("WPI_LOG_TO_FILE", "0")
    monkeypatch.setenv("WPI_LOG_LEVEL", "WARNING")
    # Deterministic randomness for functions using `random`
    random.seed(12345)
    yield
