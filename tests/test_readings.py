"""Tests for SensorReading - mostly the operator overloading."""

from datetime import datetime

import pytest

from src.readings import SensorReading


def reading(value, unit="bar", ts=None, sid="SN-PRES-02", setpoint=0.0):
    return SensorReading(sid, value, unit, ts or datetime.now(), setpoint)


def test_add_two_readings():
    result = reading(3) + reading(4)
    assert result.value == 7
    assert result.unit == "bar"
    assert result.sensor_id == "AGGREGATE"


def test_add_keeps_the_later_timestamp():
    older = datetime(2020, 1, 1)
    newer = datetime(2021, 1, 1)
    result = reading(1, ts=older) + reading(2, ts=newer)
    assert result.timestamp == newer


def test_add_a_plain_number():
    assert (reading(5) + 2.5).value == 7.5


def test_add_mismatched_units_raises():
    with pytest.raises(TypeError):
        reading(1, unit="bar") + reading(1, unit="L/min")


def test_add_nonsense_raises():
    with pytest.raises(TypeError):
        reading(1) + "not a reading"


def test_sum_over_a_list_uses_radd():
    total = sum([reading(1), reading(2), reading(3)])
    assert total.value == 6


def test_abs_is_distance_from_setpoint():
    assert abs(reading(12, setpoint=10)) == 2


def test_equality_and_less_than():
    t = datetime.now()
    assert reading(5, ts=t) == reading(5, ts=t)
    assert reading(3) < reading(9)


def test_total_ordering_lets_us_sort():
    values = [reading(9), reading(1), reading(5)]
    assert [r.value for r in sorted(values)] == [1, 5, 9]


def test_equal_readings_collapse_in_a_set():
    t = datetime.now()
    assert len({reading(1, ts=t), reading(1, ts=t)}) == 1
