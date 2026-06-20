"""
src/sensors.py

Contains the FlowRateNode concrete sensor class that extends SensorNode (ABC).
FlowRateNode simulates an industrial flow rate sensor measuring in L/min.
"""

import random
from datetime import datetime

# NOTE: These imports assume teammates have implemented these files.
# from src.readings import SensorReading
# from src.exceptions import SensorOfflineError
# For standalone running/testing, minimal stubs are used below if needed.

try:
    from src.readings import SensorReading
    from src.exceptions import SensorOfflineError
    from src.sensors_base import SensorNode  # if SensorNode is in a separate file
except ImportError:
    # Fallback stubs so this file can be tested independently
    # Remove these once the full project is assembled
    import re
    from abc import ABC, abstractmethod

    class SensorReading:
        """Stub SensorReading for standalone testing."""

        def __init__(self, sensor_id: str, value: float, unit: str, timestamp: datetime):
            self.sensor_id = sensor_id
            self.value = value
            self.unit = unit
            self.timestamp = timestamp

        def __repr__(self):
            return (
                f"SensorReading(sensor_id={self.sensor_id!r}, value={self.value}, "
                f"unit={self.unit!r}, timestamp={self.timestamp!r})"
            )

    class SensorOfflineError(IOError):
        """Stub SensorOfflineError for standalone testing."""

        def __init__(self, sensor_id: str, detail: str):
            super().__init__(f"[{sensor_id}] Offline: {detail}")
            self.sensor_id = sensor_id
            self.detail = detail
            self.timestamp = datetime.now()

    class SensorNode(ABC):
        """Stub SensorNode ABC for standalone testing."""

        _ID_PATTERN = re.compile(r"^SN-[A-Z]{4}-\d{2}$")

        def __init__(
            self,
            sensor_id: str,
            location: str,
            unit: str,
            safe_min: float,
            safe_max: float,
            calibration_offset: float = 0.0,
        ):
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
            self._calibration_offset = calibration_offset

        @property
        def sensor_id(self) -> str:
            """Return the sensor's unique identifier."""
            return self._sensor_id

        @property
        def calibration_offset(self) -> float:
            """Return the current calibration offset."""
            return self._calibration_offset

        @calibration_offset.setter
        def calibration_offset(self, value: float) -> None:
            full_scale = self.safe_max - self.safe_min
            limit = 0.1 * full_scale
            if not (-limit <= value <= limit):
                raise ValueError(
                    f"calibration_offset {value} out of range ±{limit:.2f}"
                )
            self._calibration_offset = value

        def calibrate(self, offset: float) -> None:
            """Set calibration offset with validation."""
            self.calibration_offset = offset

        def self_test(self) -> bool:
            """Run basic self-test; returns True if sensor appears healthy."""
            try:
                full_scale = self.safe_max - self.safe_min
                limit = 0.1 * full_scale
                return abs(self._calibration_offset) <= limit
            except Exception as exc:
                raise SensorOfflineError(self._sensor_id, str(exc)) from exc

        @abstractmethod
        def read(self) -> "SensorReading":
            """Take a sensor reading and return a SensorReading object."""


class FlowRateNode(SensorNode):
    """
    Concrete sensor node simulating an industrial flow rate sensor.

    Measures volumetric flow rate in litres per minute (L/min) over the
    safe operating range of 0–500 L/min.  Readings above ALARM_THRESHOLD
    (450 L/min) should be treated as alarm conditions by the
    AggregationHub — this class does **not** raise on its own for alarms.

    Sensor ID must follow the pattern ``SN-FLOW-NN`` (e.g. ``SN-FLOW-05``).

    Class-level constants
    ---------------------
    ALARM_THRESHOLD : float
        Flow rate in L/min above which an alarm should be raised (450.0).
    SAFE_MIN : float
        Lower bound of the safe operating range (0.0 L/min).
    SAFE_MAX : float
        Upper bound of the safe operating range (500.0 L/min).

    Example
    -------
    >>> node = FlowRateNode("SN-FLOW-01", location="Pump Room A")
    >>> reading = node.read()
    >>> reading.unit
    'L/min'
    """

    ALARM_THRESHOLD: float = 450.0
    SAFE_MIN: float = 0.0
    SAFE_MAX: float = 500.0
    _UNIT: str = "L/min"
    _TYPE_CODE: str = "FLOW"

    def __init__(
        self,
        sensor_id: str,
        location: str = "Unknown",
        calibration_offset: float = 0.0,
    ) -> None:
        """
        Initialise a FlowRateNode.

        Parameters
        ----------
        sensor_id : str
            Unique identifier matching ``SN-FLOW-NN`` (e.g. ``SN-FLOW-05``).
            Raises ``ValueError`` if the pattern does not match.
        location : str, optional
            Human-readable location of the sensor (default ``"Unknown"``).
        calibration_offset : float, optional
            Initial calibration offset in L/min.  Must be within ±10 % of
            the full scale (±50 L/min).  Defaults to ``0.0``.

        Raises
        ------
        ValueError
            If ``sensor_id`` does not match ``SN-FLOW-NN``.
        CalibrationError
            If ``calibration_offset`` is outside the allowed ±10 % range.
        """
        # Validate that the type code portion is exactly "FLOW"
        parts = sensor_id.split("-")
        if len(parts) != 3 or parts[1] != self._TYPE_CODE:
            raise ValueError(
                f"Invalid sensor_id '{sensor_id}' for FlowRateNode. "
                f"Expected pattern SN-{self._TYPE_CODE}-NN (e.g. SN-FLOW-05)."
            )

        super().__init__(
            sensor_id=sensor_id,
            location=location,
            unit=self._UNIT,
            safe_min=self.SAFE_MIN,
            safe_max=self.SAFE_MAX,
            calibration_offset=calibration_offset,
        )

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def read(self) -> SensorReading:
        """
        Simulate a flow rate reading and return a SensorReading.

        The raw value is drawn from a normal distribution centred on
        250 L/min (mid-range) with a standard deviation of 80 L/min,
        clamped to [SAFE_MIN, SAFE_MAX].  Approximately 5 % of the time a
        spike above ALARM_THRESHOLD is injected so that alert-testing
        scenarios are exercised during simulation runs.

        The ``calibration_offset`` is added to the raw value before the
        reading is wrapped and returned.

        Returns
        -------
        SensorReading
            A SensorReading with ``sensor_id``, calibrated ``value``,
            ``unit`` of ``"L/min"``, and the current UTC-local timestamp.
        """
        # ~5 % chance of a spike above the alarm threshold
        if random.random() < 0.05:
            raw_value = random.uniform(self.ALARM_THRESHOLD + 1.0, self.SAFE_MAX)
        else:
            raw_value = random.gauss(mu=250.0, sigma=80.0)
            raw_value = max(self.SAFE_MIN, min(self.SAFE_MAX, raw_value))

        calibrated_value = raw_value + self._calibration_offset

        return SensorReading(
            sensor_id=self._sensor_id,
            value=round(calibrated_value, 4),
            unit=self._UNIT,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Return a human-readable summary of this sensor node."""
        return (
            f"FlowRateNode(id={self._sensor_id}, location={self.location!r}, "
            f"offset={self._calibration_offset} {self._UNIT})"
        )

    def __repr__(self) -> str:
        """Return an unambiguous developer representation."""
        return (
            f"FlowRateNode("
            f"sensor_id={self._sensor_id!r}, "
            f"location={self.location!r}, "
            f"calibration_offset={self._calibration_offset!r}"
            f")"
        )
