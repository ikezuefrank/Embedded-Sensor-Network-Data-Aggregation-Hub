"""Integration tests for AggregationHub plus the DataPipeline duck typing.

These use a FixedSensor with a constant value so the alert/summary maths is
deterministic - the real nodes are random by design.
"""

from datetime import datetime, timedelta

import pytest

from src.hub import AggregationHub
from src.alerts import AlertRule
from src.readings import SensorReading
from src.pipeline import DataPipeline


class FixedSensor:
    """A sensor that always reports the same value. Not a SensorNode subclass -
    it just quacks like one (id + read), which is all the hub needs."""

    def __init__(self, sensor_id, value):
        self._sensor_id = sensor_id
        self._value = value

    @property
    def sensor_id(self):
        return self._sensor_id

    def read(self):
        return SensorReading(self._sensor_id, self._value, "bar", datetime.now())


def test_register_len_contains_iter():
    hub = AggregationHub("Plant")
    sensor = FixedSensor("SN-PRES-02", 5)
    hub.register(sensor)
    assert len(hub) == 1
    assert "SN-PRES-02" in hub
    assert list(hub) == [sensor]


def test_duplicate_id_is_rejected():
    hub = AggregationHub("Plant")
    hub.register(FixedSensor("SN-PRES-02", 5))
    with pytest.raises(ValueError):
        hub.register(FixedSensor("SN-PRES-02", 6))


def test_poll_raises_alert_on_breach():
    hub = AggregationHub("Plant")
    hub.register(FixedSensor("SN-PRES-02", 50))
    hub.add_alert_rule(AlertRule("SN-PRES-02", 0, 9))
    hub.poll_all()
    assert len(hub.get_alerts()) == 1


def test_get_alerts_filtering_and_sorting():
    hub = AggregationHub("Plant")
    hub.register(FixedSensor("SN-PRES-02", 50))
    hub.add_alert_rule(AlertRule("SN-PRES-02", 0, 9))
    base = datetime(2020, 1, 1)
    for i in range(3):
        hub.poll_all(timestamp=base + timedelta(minutes=i))
    alerts = hub.get_alerts()
    assert len(alerts) == 3
    assert alerts == sorted(alerts, key=lambda a: a.timestamp)
    assert hub.get_alerts("LOW") == []


def test_summary_statistics():
    hub = AggregationHub("Plant")
    hub.register(FixedSensor("SN-PRES-02", 4))
    hub.poll_all()
    hub.poll_all()
    stats = hub.summary()["SN-PRES-02"]
    assert stats["count"] == 2
    assert stats["mean"] == 4.0
    assert stats["min"] == 4.0 and stats["max"] == 4.0
    assert stats["std_dev"] == 0.0


def test_pipeline_works_on_anything_readable():
    sensor = FixedSensor("SN-PRES-02", 5)
    assert DataPipeline.process(sensor).value == 5

    class Bare:
        def read(self):
            return SensorReading("SN-DUMM-99", 1.0, "x", datetime.now())

    assert DataPipeline.process(Bare()).sensor_id == "SN-DUMM-99"


def test_pipeline_rejects_unreadable():
    with pytest.raises(TypeError):
        DataPipeline.process(object())
