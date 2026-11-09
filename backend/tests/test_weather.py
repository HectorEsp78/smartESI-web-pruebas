import json
import unittest
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.clock import local_now, to_utc_naive
from app.core.weather_map import (
    AEMET_HUMIDITY_ENTITY,
    AEMET_PRESSURE_ENTITY,
    AEMET_TEMPERATURE_ENTITY,
)
from app.main import app
from app.services import weather_service
from app.services.weather_service import (
    _build_availability,
    _build_comparison,
    _Dataset,
    _observation_hour,
    _parse_station,
    _StationSample,
    resolve_period,
)

client = TestClient(app)
URL = "/api/v1/weather/overview"


def _iso(day: date) -> str:
    return day.isoformat()


class WeatherEndpointTest(unittest.TestCase):
    def setUp(self):
        weather_service.clear_cache()

    def tearDown(self):
        weather_service.clear_cache()

    def test_default_period_compares_the_station_with_aemet(self):
        response = client.get(URL)
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["data_source"], "mock")
        self.assertEqual(body["granularity"], "day")
        self.assertEqual(len(body["series"]), 30)
        self.assertEqual(body["current"]["status"], "ok")
        self.assertFalse(body["aemet_latest"]["stale"])
        self.assertEqual(body["aemet_availability"]["coverage"], "complete")

        comparison = body["comparison"]
        for metric in ("temperature", "humidity", "pressure"):
            self.assertGreater(comparison[metric]["samples"], 0)
            self.assertIsNotNone(comparison[metric]["bias"])
        self.assertEqual(len(comparison["hourly_bias"]), 24)
        # The mock station is warmer than AEMET under the sun.
        self.assertGreater(
            comparison["temperature"]["daytime_bias"],
            comparison["temperature"]["nighttime_bias"],
        )

    def test_short_periods_keep_hourly_detail(self):
        end = local_now().date() - timedelta(days=1)
        start = end - timedelta(days=2)
        body = client.get(URL, params={"start": _iso(start), "end": _iso(end)}).json()

        self.assertEqual(body["granularity"], "hour")
        self.assertEqual(len(body["series"]), 72)
        self.assertIsNotNone(body["series"][0]["aemet_temperature_c"])

    def test_invalid_periods_are_rejected(self):
        today = local_now().date()
        cases = (
            {"start": _iso(today), "end": _iso(today - timedelta(days=1))},
            {"end": _iso(today + timedelta(days=1))},
            {"start": _iso(today - timedelta(days=400)), "end": _iso(today)},
            {"start": "0001-01-01", "end": "0001-01-02"},
        )
        for params in cases:
            with self.subTest(params=params):
                self.assertEqual(client.get(URL, params=params).status_code, 422)


class WeatherParsingTest(unittest.TestCase):
    def test_station_reading_comes_from_state_and_attributes(self):
        attributes = json.dumps(
            {"Humidity": 62.5, "Pressure": 1015.2, "PM1": 10, "PM2.5": 12, "PM10": 13, "Battery": 80}
        )
        sample = _parse_station(datetime(2026, 1, 1), "12.5", attributes)
        self.assertEqual(sample.temperature_c, 12.5)
        self.assertEqual(sample.humidity_pct, 62.5)
        self.assertEqual(sample.pm25, 12)

    def test_recorder_reset_rows_are_not_observations(self):
        attributes = '{"state_class":"measurement","friendly_name":"meteo"}'
        self.assertIsNone(_parse_station(datetime(2026, 1, 1), "0", attributes))

    def test_non_finite_values_are_ignored(self):
        attributes = json.dumps({"Humidity": "nan", "Pressure": 1015.0})
        sample = _parse_station(datetime(2026, 1, 1), "nan", attributes)
        self.assertIsNone(sample.temperature_c)
        self.assertIsNone(sample.humidity_pct)

    def test_aemet_rows_use_the_observation_time(self):
        written = datetime(2026, 10, 29, 17, 29, 51)
        attributes = '{"last_update":"2026-10-29T17:00:00+0000"}'
        self.assertEqual(_observation_hour(written, attributes), datetime(2026, 10, 29, 17))
        self.assertEqual(_observation_hour(written, None), datetime(2026, 10, 29, 17))
        self.assertEqual(
            _observation_hour(written, '{"last_update":"no-date"}'), datetime(2026, 10, 29, 17)
        )


class WeatherComparisonTest(unittest.TestCase):
    """A day of 2026 with AEMET available only from 06:00 to 12:00 UTC."""

    DAY = date(2026, 1, 15)

    def setUp(self):
        self.period = resolve_period(self.DAY, self.DAY)
        self.start = to_utc_naive(self.period.start)

    def _dataset(self) -> _Dataset:
        station = [
            _StationSample(
                timestamp=self.start + timedelta(minutes=15 * index),
                temperature_c=20.0,
                humidity_pct=100.0 if index < 12 else 50.0,
                pressure_hpa=1013.25,
            )
            for index in range(96)
        ]
        hours = [self.start + timedelta(hours=offset) for offset in range(7, 14)]
        return _Dataset(
            data_source="mock",
            station=station,
            aemet={
                AEMET_TEMPERATURE_ENTITY: dict.fromkeys(hours, 18.0),
                AEMET_HUMIDITY_ENTITY: dict.fromkeys(hours, 40.0),
                AEMET_PRESSURE_ENTITY: dict.fromkeys(hours, 940.0),
            },
        )

    def test_only_hours_with_both_sources_are_compared(self):
        comparison = _build_comparison(self._dataset(), self.period)

        self.assertEqual(comparison.temperature.samples, 7)
        self.assertEqual(comparison.temperature.bias, 2.0)
        self.assertEqual(comparison.temperature.mean_absolute_error, 2.0)
        self.assertEqual(comparison.humidity.bias, 10.0)
        self.assertEqual(comparison.humidity.saturated_pct, 0.0)

    def test_aemet_is_paired_with_the_hour_that_just_finished(self):
        dataset = self._dataset()
        # Only the hour before the 07:00 observation differs.
        for sample in dataset.station:
            if self.start + timedelta(hours=6) <= sample.timestamp < self.start + timedelta(hours=7):
                sample.temperature_c = 30.0

        comparison = _build_comparison(dataset, self.period)
        expected = ((30.0 - 18.0) + 6 * 2.0) / 7
        self.assertAlmostEqual(comparison.temperature.bias, round(expected, 1))

    def test_availability_reports_coverage_and_gaps(self):
        availability = _build_availability(self._dataset(), self.period, compared_hours=7)

        self.assertEqual(availability.coverage, "partial")
        self.assertEqual(availability.observed_hours, 7)
        self.assertEqual(availability.period_hours, 24)
        self.assertEqual(availability.coverage_pct, 29.2)
        self.assertEqual(
            [gap.hours for gap in availability.gaps],
            [11, 6],
        )

    def test_no_aemet_means_no_comparison(self):
        dataset = _Dataset(data_source="mock", station=self._dataset().station, aemet={})

        comparison = _build_comparison(dataset, self.period)
        availability = _build_availability(dataset, self.period, compared_hours=0)

        self.assertEqual(comparison.temperature.samples, 0)
        self.assertIsNone(comparison.temperature.bias)
        self.assertIsNone(comparison.humidity.saturated_pct)
        self.assertEqual(availability.coverage, "none")
        self.assertEqual(len(availability.gaps), 1)


if __name__ == "__main__":
    unittest.main()
