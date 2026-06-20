"""Tests for Alert and AlertRule."""

from datetime import datetime

import pytest

from src.alerts import Alert, AlertRule
from src.readings import SensorReading


def reading(value, sid="SN-PRES-02"):
    return SensorReading(sid, value, "bar", datetime.now())


def test_severity_must_be_valid():
    with pytest.raises(ValueError):
        Alert("SN-PRES-02", "SEVERE", "msg", datetime.now())


def test_alerts_sort_low_to_critical():
    t = datetime.now()
    mixed = [
        Alert("s", "CRITICAL", "", t),
        Alert("s", "LOW", "", t),
        Alert("s", "HIGH", "", t),
        Alert("s", "MEDIUM", "", t),
    ]
    assert [a.severity for a in sorted(mixed)] == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_rule_returns_none_inside_band():
    assert AlertRule("SN-PRES-02", 0, 9).check(reading(5)) is None


def test_rule_ignores_other_sensors():
    rule = AlertRule("SN-PRES-02", 0, 9)
    assert rule.check(reading(99, sid="SN-TEMP-01")) is None


def test_severity_scales_with_breach():
    rule = AlertRule("SN-PRES-02", 0, 10)
    assert rule.check(reading(11)).severity == "MEDIUM"     # 10% over
    assert rule.check(reading(12.4)).severity == "HIGH"     # 24% over
    assert rule.check(reading(15)).severity == "CRITICAL"   # 50% over


def test_breach_alert_carries_reading_timestamp():
    r = reading(20)
    alert = AlertRule("SN-PRES-02", 0, 9).check(r)
    assert alert.timestamp == r.timestamp


def test_bad_rule_band_rejected():
    with pytest.raises(ValueError):
        AlertRule("SN-PRES-02", 10, 0)
