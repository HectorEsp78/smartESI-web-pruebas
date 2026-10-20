"""Unit tests for the database-series helpers (no database access).

They check the pure conversions used when ``DATA_SOURCE=database``: turning a
cumulative ``sum`` series into hourly consumption and handling meter resets.
"""

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.db.database_data import (
    average_series,
    cumulative_to_hourly,
    load_hourly_occupancy,
    net_occupancy,
    parse_counter_value,
)


def _hour(day: int, hour: int) -> datetime:
    return datetime(2026, 1, day, hour, 0, 0, tzinfo=timezone.utc).replace(tzinfo=None)


class CumulativeToHourlyTest(unittest.TestCase):
    def test_differences_are_attributed_to_the_previous_hour(self):
        rows = [
            (_hour(1, 0), 100.0),
            (_hour(1, 1), 103.0),
            (_hour(1, 2), 105.5),
        ]
        hourly = cumulative_to_hourly(rows)

        # Two deltas are produced (the first row is only a baseline).
        self.assertEqual(len(hourly), 2)
        self.assertAlmostEqual(sum(hourly.values()), 5.5, places=3)

    def test_meter_reset_does_not_produce_negative_energy(self):
        rows = [
            (_hour(1, 0), 500.0),
            (_hour(1, 1), 2.0),   # meter reset
            (_hour(1, 2), 5.0),
        ]
        hourly = cumulative_to_hourly(rows)

        self.assertTrue(all(value >= 0.0 for value in hourly.values()))
        self.assertAlmostEqual(sum(hourly.values()), 3.0, places=3)

    def test_implausible_jump_is_ignored(self):
        rows = [
            (_hour(1, 0), 100.0),
            (_hour(1, 1), 103.0),
            (_hour(1, 2), 5000.0),  # recorder import artifact
            (_hour(1, 3), 5004.0),
        ]
        hourly = cumulative_to_hourly(rows, max_delta=150.0)

        # The 4897 jump is dropped; only the two plausible deltas remain.
        self.assertAlmostEqual(sum(hourly.values()), 7.0, places=3)

    def test_spread_keeps_real_catch_up_but_drop_discards_it(self):
        # 60 kWh accumulated over a 6 h gap: plausible when spread (10/h),
        # implausible as a single hourly jump.
        rows = [(_hour(1, 0), 100.0), (_hour(1, 6), 160.0)]

        spread = cumulative_to_hourly(rows, max_delta=50.0, spread=True)
        self.assertAlmostEqual(sum(spread.values()), 60.0, places=3)

        dropped = cumulative_to_hourly(rows, max_delta=50.0, spread=False)
        self.assertAlmostEqual(sum(dropped.values()), 0.0, places=3)


class CounterValueTest(unittest.TestCase):
    def test_state_counter(self):
        self.assertEqual(parse_counter_value("42", None), 42.0)
        self.assertEqual(parse_counter_value("7.5", "{}"), 7.5)

    def test_attribute_counter(self):
        attributes = json.dumps({"LTR_SUM": 50, "RTL_SUM": 20})
        self.assertEqual(parse_counter_value("0", attributes, "LTR_SUM"), 50.0)
        self.assertEqual(parse_counter_value("0", attributes, "RTL_SUM"), 20.0)

    def test_invalid_values_are_not_zero(self):
        # A missing/broken reading must not be confused with an empty building.
        self.assertIsNone(parse_counter_value("unavailable", None))
        self.assertIsNone(parse_counter_value(None, None))
        self.assertIsNone(parse_counter_value("0", "not-json", "LTR_SUM"))
        self.assertIsNone(parse_counter_value("0", "{}", "LTR_SUM"))


class NetOccupancyTest(unittest.TestCase):
    def test_difference_is_the_occupancy(self):
        self.assertEqual(net_occupancy(120.0, 45.0, capacity=300), 75)

    def test_daily_reset_or_lost_reading_does_not_go_negative(self):
        self.assertEqual(net_occupancy(5.0, 12.0, capacity=300), 0)

    def test_counter_above_capacity_is_capped(self):
        self.assertEqual(net_occupancy(10_000.0, 0.0, capacity=300), 300)

    def test_missing_counter_returns_none(self):
        self.assertIsNone(net_occupancy(None, 10.0, capacity=300))


class OccupancyLoaderTest(unittest.IsolatedAsyncioTestCase):
    async def test_modulo_b_combines_two_attributes_of_one_entity(self):
        hour = _hour(1, 10)
        by_counter = {
            ("sensor.contador_personas", "LTR_SUM"): {hour: 50.0},
            ("sensor.contador_personas", "RTL_SUM"): {hour: 20.0},
        }

        with patch(
            "app.db.database_data._load_counter_series",
            new=AsyncMock(return_value=by_counter),
        ):
            occupancy = await load_hourly_occupancy(
                None, ["ModuloB"], _hour(1, 0), _hour(1, 12)
            )

        self.assertEqual(occupancy["ModuloB"][hour], 30)

    async def test_building_without_both_counters_is_omitted(self):
        hour = _hour(1, 10)
        # Only the entrance counter has readings: the occupancy is unknown.
        by_counter = {
            ("sensor.entrada_fermin_caballero", None): {hour: 50.0},
        }

        with patch(
            "app.db.database_data._load_counter_series",
            new=AsyncMock(return_value=by_counter),
        ):
            occupancy = await load_hourly_occupancy(
                None, ["FerminCaballero"], _hour(1, 0), _hour(1, 12)
            )

        self.assertNotIn("FerminCaballero", occupancy)


class AverageSeriesTest(unittest.TestCase):
    def test_only_hours_present_in_some_series_are_returned(self):
        a = {_hour(1, 0): 20.0, _hour(1, 1): 22.0}
        b = {_hour(1, 0): 24.0}

        averaged = average_series([a, b])
        self.assertEqual(set(averaged), set(a))
        self.assertAlmostEqual(averaged[_hour(1, 0)], 22.0)
        self.assertAlmostEqual(averaged[_hour(1, 1)], 22.0)


if __name__ == "__main__":
    unittest.main()
