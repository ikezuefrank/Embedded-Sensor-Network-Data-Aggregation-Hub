"""
src/sensors.py

Contains the abstract base class SensorNode and the concrete FlowRateNode
implementation for the Embedded Sensor Network Data Aggregation Hub.
"""

import re
import random
from abc import ABC, abstractmethod
from datetime import datetime

from src.exceptions import CalibrationError, SensorOfflineError
from src.readings import SensorReading


class SensorNode(ABC):
    """
    Abstract base class for all sensor nodes in the aggregation network.

    Subclasses must implement the `sensor_id` property and the `read()` method.
    Provides shared logic for calibration, validation, and self-testing.

    Args:
        sensor_id (str): Unique sensor identifier matching pattern SN-TTTT-NN.
        location (str): Physical location description of the sensor.
        unit (str): Measurement unit string (e.g. "L/min", "°C").
        safe_min (float): Minimum value of the safe operating range.
        safe_max (float): Maximum value of the safe operating range.
        calibration_offset (float): Initial calibration offset. Defaults to 0.0.

    Raises:
        ValueError: If sensor_id does not match the required pattern SN-TTTT-NN.
    """

    _ID_PATTERN = re.compile(r'^SN-[A-Z]{4}-\d{2}$')

    def __init__(
        self,
        sensor_id: str,
        location: str,
        unit: str,
        safe_min: float,
        safe_max: float,
        calibration_offset: float = 0.0,
    ) -> None:
        if not self._ID_PATTERN.match(sensor_id):
            raise ValueError(
                f"Invalid sensor_id '{sensor_id}'. "
                "Must match pattern SN-TTTT-NN (e.g. SN-FLOW-05)."
            )
        self._sensor_id = sensor_id
        self.location = location
        self.unit = unit
        self.safe_min = safe_min
        self.safe_max = safe_max
        self._calibration_offset = 0.0
        # Use the property setter for validation
        self.calibration_offset = calibration_offset

    @property
    def sensor_id(self) -> str:
        """Return the unique sensor identifier."""
        return self._sensor_id

    @property
    def calibration_offset(self) -> float:
        """
        Calibration offset applied to raw readings.

        Must be within ±10% of the sensor's full scale (safe_max - safe_min).

        Raises:
            CalibrationError: If the offset is outside the allowed range.
        """
        return self._calibration_offset

    @calibration_offset.setter
    def calibration_offset(self, value: float) -> None:
        full_scale = self.safe_max - self.safe_min
        limit = 0.1 * full_scale
        if abs(value) > limit:
            raise CalibrationError(
                self._sensor_id,
                f"Offset {value} exceeds ±10% of full scale (±{limit:.4f}).",
            )
        self._calibration_offset = value

    def calibrate(self, offset: float) -> None:
        """
        Set a new calibration offset (delegates to the property for validation).

        Args:
            offset (float): New calibration offset to apply.

        Raises:
            CalibrationError: If offset is outside ±10% of full scale.
        """
        self.calibration_offset = offset

    def self_test(self) -> bool:
        """
        Perform a basic internal consistency check on the sensor.

        Returns:
            bool: True if the sensor passes the internal check.

        Raises:
            SensorOfflineError: If the sensor fails the internal check.
        """
        full_scale = self.safe_max - self.safe_min
        limit = 0.1 * full_scale
        if abs(self._calibration_offset) <= limit:
            return True
        raise SensorOfflineError(
            self._sensor_id,
            "Self-test failed: calibration offset out of range.",
        )

    @abstractmethod
    def read(self) -> "SensorReading":
        """
        Read a current value from the sensor.

        Returns:
            SensorReading: The latest measurement wrapped in a SensorReading object.
        """

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self._sensor_id}, location={self.location}, unit={self.unit})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"sensor_id={self._sensor_id!r}, "
            f"location={self.location!r}, "
            f"unit={self.unit!r}, "
            f"safe_min={self.safe_min}, "
            f"safe_max={self.safe_max}, "
            f"calibration_offset={self._calibration_offset})"
        )


class FlowRateNode(SensorNode):
    """
    Concrete sensor node that simulates a flow rate sensor.

    Produces readings in litres per minute (L/min) within a safe operating
    range of 0–500 L/min.  Readings occasionally spike above the alarm
    threshold (450 L/min) so that alert-detection logic can be exercised
    during simulation runs.

    Class constants:
        ALARM_THRESHOLD (float): Flow rate value above which an alarm should
            be raised by the AggregationHub / AlertRule layer (450.0 L/min).

    Sensor-ID type code: ``FLOW``  (e.g. ``SN-FLOW-05``)

    Args:
        sensor_id (str): Must follow the pattern ``SN-FLOW-NN``.
        location (str): Physical installation location of the sensor.
        calibration_offset (float): Initial offset in L/min. Defaults to 0.0.

    Example:
        >>> node = FlowRateNode("SN-FLOW-01", "Pump Station A")
        >>> reading = node.read()
        >>> print(reading.unit)
        L/min
    """

    ALARM_THRESHOLD: float = 450.0

    _SAFE_MIN: float = 0.0
    _SAFE_MAX: float = 500.0
    _UNIT: str = "L/min"

    # Probability that a simulated reading will spike above ALARM_THRESHOLD
    _SPIKE_PROBABILITY: float = 0.1

    def __init__(
        self,
        sensor_id: str,
        location: str,
        calibration_offset: float = 0.0,
    ) -> None:
        super().__init__(
            sensor_id=sensor_id,
            location=location,
            unit=self._UNIT,
            safe_min=self._SAFE_MIN,
            safe_max=self._SAFE_MAX,
            calibration_offset=calibration_offset,
        )

    def read(self) -> SensorReading:
        """
        Simulate a flow rate reading and return it as a SensorReading.

        With probability ``_SPIKE_PROBABILITY`` the raw value will be drawn
        from the range (ALARM_THRESHOLD, safe_max] to exercise alert logic.
        Otherwise the value is drawn uniformly from [safe_min, ALARM_THRESHOLD].

        The calibration offset is added to the raw value before the reading
        is packaged.  The resulting value is clamped to [safe_min, safe_max]
        so it never falls outside the physical sensor limits.

        Returns:
            SensorReading: A measurement object with unit "L/min" and the
            current UTC-local timestamp.
        """
        if random.random() < self._SPIKE_PROBABILITY:
            # Simulate an above-threshold spike
            raw_value = random.uniform(self.ALARM_THRESHOLD + 1.0, self._SAFE_MAX)
        else:
            raw_value = random.uniform(self._SAFE_MIN, self.ALARM_THRESHOLD)

        adjusted_value = raw_value + self._calibration_offset
        # Clamp to physical limits
        adjusted_value = max(self._SAFE_MIN, min(self._SAFE_MAX, adjusted_value))

        return SensorReading(
            sensor_id=self.sensor_id,
            value=adjusted_value,
            unit=self._UNIT,
            timestamp=datetime.now(),
        )

    def __str__(self) -> str:
        return (
            f"FlowRateNode(id={self.sensor_id}, "
            f"location={self.location}, "
            f"offset={self._calibration_offset} {self._UNIT})"
        )

    def __repr__(self) -> str:
        return (
            f"FlowRateNode("
            f"sensor_id={self.sensor_id!r}, "
            f"location={self.location!r}, "
            f"calibration_offset={self._calibration_offset})"
        )
