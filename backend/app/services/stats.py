"""Small statistics helpers shared by the aggregation services.

These are plain-Python implementations so the prototype has no numeric
dependencies. They cover the descriptive statistics and the linear fit used by
the decision-making charts:

- central tendency / dispersion: mean, median, stdev, percentiles, coefficient
  of variation;
- relationship between two series: Pearson correlation and least-squares
  regression (used for scatter plots and their trend line);
- trend over time: least-squares slope against the sample index.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LinearFit:
    r: float
    slope: float
    intercept: float


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def stdev(values: list[float]) -> float:
    """Population standard deviation."""
    n = len(values)
    if n == 0:
        return 0.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / n
    return math.sqrt(variance)


def percentile(values: list[float], pct: float) -> float:
    """Percentile (0..100) with linear interpolation between closest ranks."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (pct / 100.0) * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def coefficient_of_variation(values: list[float]) -> float:
    """stdev / mean, as a fraction (0 when the mean is zero)."""
    avg = mean(values)
    if avg == 0:
        return 0.0
    return stdev(values) / abs(avg)


def least_squares(xs: list[float], ys: list[float]) -> LinearFit:
    """Least-squares fit of ``ys`` on ``xs`` plus the Pearson correlation."""
    n = len(xs)
    if n < 2 or len(ys) != n:
        return LinearFit(0.0, 0.0, mean(ys))

    mean_x = mean(xs)
    mean_y = mean(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))

    if var_x <= 0 or var_y <= 0:
        return LinearFit(0.0, 0.0, mean_y)

    slope = cov / var_x
    intercept = mean_y - slope * mean_x
    r = cov / math.sqrt(var_x * var_y)
    return LinearFit(round(r, 3), slope, intercept)


def trend_slope(values: list[float]) -> float:
    """Least-squares slope of ``values`` against their index (per step)."""
    if len(values) < 2:
        return 0.0
    xs = [float(index) for index in range(len(values))]
    return least_squares(xs, [float(value) for value in values]).slope
