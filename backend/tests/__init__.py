"""Test suite for the statistics backend.

The tests are written against the deterministic synthetic data, so they force
``DATA_SOURCE=mock`` and never touch the real Home Assistant database, even when
the developer's ``.env`` points at it.
"""

import os

os.environ["DATA_SOURCE"] = "mock"
