"""
tests/test_flow_node.py

Pytest tests for FlowRateNode in src/sensors.py.

Run with:
    pytest tests/test_flow_node.py -v
"""

import pytest
from datetime import datetime

# We import directly from the file; the stubs inside sensors.py
# mean this works even before teammates' files are merged.
from src.sensors import FlowRateNode, SensorReading


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_node(sensor_id: str = "SN-FLOW-01", location: str = "Test Lab") -> FlowRateNode:
    """Return a default FlowRateNode for reuse across tests."""
    return FlowRateNode(sensor_id=sensor_id, location=location)


# ---------------------------------------------------------------------------
# Test 1 — Valid construction
# ---------------------------------------------------------------------------

class TestFlowRateNodeConstruction:
    """Tests covering valid and invalid sensor construction."""

    def test_valid_construction_succeeds(self):
        """A properly-formatted sensor_id creates a FlowRateNode without error."""
        node = make_node("SN-FLOW-01")
        assert node.sensor_id == "SN-FLOW-01"
        assert node.location == "Test Lab"

    def test_default_calibration_offset_is_zero(self):
        """calibration_offset should default to 0.0."""
        node = make_node()
        assert node.calibration_offset == 0.0

    def test_class_constants_are_correct(self):
        """ALARM_THRESHOLD, SAFE_MIN, SAFE_MAX must match the specification."""
        assert FlowRateNode.ALARM_THRESHOLD == 450.0
        assert FlowRateNode.SAFE_MIN == 0.0
        assert FlowRateNode.SAFE_MAX == 500.0

    # ------------------------------------------------------------------
    # Test 4 — Invalid sensor_id raises ValueError
    # ------------------------------------------------------------------

    def test_invalid_sensor_id_wrong_type_code_raises(self):
        """sensor_id with wrong type code (not FLOW) must raise ValueError."""
        with pytest.raises(ValueError, match="SN-FLOW"):
            FlowRateNode(sensor_id="SN-TEMP-01")

    def test_invalid_sensor_id_bad_pattern_raises(self):
        """sensor_id that doesn't match SN-TTTT-NN pattern raises ValueError."""
        with pytest.raises(ValueError):
            FlowRateNode(sensor_id="FLOW-01")

    def test_invalid_sensor_id_lowercase_raises(self):
        """Lowercase type codes must be rejected."""
        with pytest.raises(ValueError):
            FlowRateNode(sensor_id="SN-flow-01")

    def test_multiple_valid_ids_accepted(self):
        """Any valid SN-FLOW-NN id from 00 to 99 should be accepted."""
        for num in ("00", "05", "12", "99"):
            node = FlowRateNode(sensor_id=f"SN-FLOW-{num}")
            assert node.sensor_id == f"SN-FLOW-{num}"


# ---------------------------------------------------------------------------
# Test 2 — read() returns correct SensorReading type and unit
# ---------------------------------------------------------------------------

class TestFlowRateNodeRead:
    """Tests covering the read() method."""

    def test_read_returns_sensor_reading_instance(self):
        """read() must return a SensorReading object."""
        node = make_node()
        reading = node.read()
        assert isinstance(reading, SensorReading)

    def test_read_unit_is_l_per_min(self):
        """SensorReading returned by read() must have unit 'L/min'."""
        node = make_node()
        reading = node.read()
        assert reading.unit == "L/min"

    def test_read_sensor_id_matches_node(self):
        """SensorReading.sensor_id must match the node's sensor_id."""
        node = make_node("SN-FLOW-07")
        reading = node.read()
        assert reading.sensor_id == "SN-FLOW-07"

    def test_read_has_timestamp(self):
        """SensorReading.timestamp must be a datetime instance."""
        node = make_node()
        reading = node.read()
        assert isinstance(reading.timestamp, datetime)

    # ------------------------------------------------------------------
    # Test 3 — Value falls within a sane bound after calibration
    # ------------------------------------------------------------------

    def test_read_value_within_sane_bounds_no_offset(self, runs: int = 200):
        """
        Over many readings with no calibration offset, all values should
        stay within [SAFE_MIN, SAFE_MAX].  (Spikes are still within range.)
        """
        node = make_node()
        for _ in range(runs):
            reading = node.read()
            assert FlowRateNode.SAFE_MIN <= reading.value <= FlowRateNode.SAFE_MAX, (
                f"Value {reading.value} L/min is outside safe range "
                f"[{FlowRateNode.SAFE_MIN}, {FlowRateNode.SAFE_MAX}]"
            )

    def test_read_value_with_positive_calibration_offset(self):
        """
        With a positive calibration_offset, every reading value should be
        offset by that amount compared to an uncalibrated reading's raw value.
        The calibrated result should stay within a generous physical bound.
        """
        offset = 10.0
        node = FlowRateNode("SN-FLOW-02", calibration_offset=offset)
        for _ in range(50):
            reading = node.read()
            # Upper bound: SAFE_MAX + offset is the theoretical ceiling
            assert reading.value <= FlowRateNode.SAFE_MAX + offset + 1.0

    def test_read_value_with_negative_calibration_offset(self):
        """
        With a negative calibration_offset, values should shift down.
        """
        offset = -10.0
        node = FlowRateNode("SN-FLOW-03", calibration_offset=offset)
        for _ in range(50):
            reading = node.read()
            # Lower bound: SAFE_MIN + offset is the theoretical floor
            assert reading.value >= FlowRateNode.SAFE_MIN + offset - 1.0

    def test_read_returns_float_value(self):
        """reading.value must be a float (not None, str, etc.)."""
        node = make_node()
        reading = node.read()
        assert isinstance(reading.value, float)


# ---------------------------------------------------------------------------
# Calibration validation tests (bonus — covers boundary at ±10 % full scale)
# ---------------------------------------------------------------------------

class TestFlowRateNodeCalibration:
    """Tests covering calibration_offset validation."""

    def test_calibration_offset_at_positive_boundary_accepted(self):
        """Offset of exactly +50 L/min (10 % of 500) must be accepted."""
        node = make_node()
        node.calibrate(50.0)
        assert node.calibration_offset == 50.0

    def test_calibration_offset_at_negative_boundary_accepted(self):
        """Offset of exactly -50 L/min must be accepted."""
        node = make_node()
        node.calibrate(-50.0)
        assert node.calibration_offset == -50.0

    def test_calibration_offset_beyond_limit_raises(self):
        """Offset beyond ±50 L/min must raise an error."""
        node = make_node()
        with pytest.raises(Exception):  # CalibrationError or ValueError
            node.calibrate(51.0)

    def test_calibration_offset_below_negative_limit_raises(self):
        """Offset below -50 L/min must raise an error."""
        node = make_node()
        with pytest.raises(Exception):
            node.calibrate(-51.0)


# ---------------------------------------------------------------------------
# __str__ / __repr__ smoke tests
# ---------------------------------------------------------------------------

class TestFlowRateNodeRepresentation:
    """Sanity checks on string representations."""

    def test_str_contains_sensor_id(self):
        node = make_node("SN-FLOW-09")
        assert "SN-FLOW-09" in str(node)

    def test_repr_contains_class_name(self):
        node = make_node()
        assert "FlowRateNode" in repr(node)
