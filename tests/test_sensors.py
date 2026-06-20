"""Tests for the SensorNode ABC and its shared calibration/self-test logic.

SensorNode is abstract, so these use a tiny concrete DummyNode just to reach
the shared behaviour.
"""

from datetime import datetime

import pytest

from src.sensors import SensorNode
from src.exceptions import CalibrationError, SensorOfflineError
from src.readings import SensorReading


class DummyNode(SensorNode):
    """Minimal concrete node (full scale 0-100) for exercising the base."""

    def __init__(self, sensor_id, **kwargs):
        super().__init__(sensor_id, "lab", "u", 0.0, 100.0, **kwargs)

    @property
    def sensor_id(self):
        return self._sensor_id

    def read(self):
        return SensorReading(self.sensor_id, 1.0, self.unit, datetime.now())


def test_abc_cannot_be_instantiated():
    with pytest.raises(TypeError):
        SensorNode("SN-TEST-01", "lab", "u", 0.0, 100.0)


def test_valid_id_is_accepted():
    assert DummyNode("SN-TEST-01").sensor_id == "SN-TEST-01"


@pytest.mark.parametrize("bad_id", ["SN-TES-01", "SN-TEST-1", "garbage", "SN-test-01", ""])
def test_bad_id_raises_value_error(bad_id):
    with pytest.raises(ValueError):
        DummyNode(bad_id)


def test_offset_at_the_limit_is_fine():
    node = DummyNode("SN-TEST-02")
    node.calibrate(10.0)  # 10% of full scale (100) is exactly the limit
    assert node.calibration_offset == 10.0


def test_offset_past_the_limit_raises():
    with pytest.raises(CalibrationError):
        DummyNode("SN-TEST-03").calibrate(10.01)


def test_self_test_passes_then_fails():
    node = DummyNode("SN-TEST-04")
    assert node.self_test() is True
    node._calibration_offset = 999  # force a drifted state
    with pytest.raises(SensorOfflineError):
        node.self_test()
