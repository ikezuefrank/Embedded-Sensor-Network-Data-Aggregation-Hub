"""Pressure sensor node implementation.

This snippet defines `PressureNode`, a concrete subclass of the
abstract `SensorNode` base class (built by a teammate in src/sensors.py).
It models a pressure transducer reporting in bar over a safe range of
0-10 bar, with an alarm threshold of 9 bar.

NOTE: This file is meant to be merged into the shared src/sensors.py
alongside SensorNode and the other *Node classes -- it is not a
standalone module on its own.
"""

import random
from datetime import datetime

from src.readings import SensorReading
# from src.sensors import SensorNode  # already defined above this class
# in the shared src/sensors.py file


class PressureNode(SensorNode):
    """Concrete sensor node representing an industrial pressure sensor.

    Pressure is measured in bar across a safe operating range of
    0 to 10 bar. Readings above ``ALARM_THRESHOLD`` (9.0 bar) indicate
    an over-pressure condition. This class does not raise on its own
    when the threshold is exceeded -- that is AggregationHub's job via
    AlertRule -- it simply documents the threshold here.

    Class Attributes:
        TYPE_CODE: Four-letter sensor type code used in sensor_id, "PRES".
        ALARM_THRESHOLD: Pressure value (bar) above which an alarm
            condition is considered active.
    """

    TYPE_CODE = "PRES"
    ALARM_THRESHOLD = 9.0

    def __init__(
        self,
        sensor_id: str,
        location: str,
        calibration_offset: float = 0.0,
    ) -> None:
        """Initialize a PressureNode.

        Args:
            sensor_id: Identifier matching pattern SN-PRES-NN
                (e.g. SN-PRES-02).
            location: Human-readable installation location of the sensor.
            calibration_offset: Initial calibration offset in bar,
                defaults to 0.0.

        Raises:
            ValueError: If sensor_id does not match the required pattern.
            CalibrationError: If calibration_offset is outside the
                allowed +/-10% of full scale.
        """
        super().__init__(
            sensor_id=sensor_id,
            location=location,
            unit="bar",
            safe_min=0.0,
            safe_max=10.0,
            calibration_offset=calibration_offset,
        )

    @property
    def sensor_id(self) -> str:
        """str: The unique identifier of this sensor (e.g. SN-PRES-02)."""
        return self._sensor_id

    def read(self) -> SensorReading:
        """Simulate and return a pressure reading.

        Generates a realistic raw pressure value mostly within the safe
        operating range, occasionally spiking above ALARM_THRESHOLD to
        make alert-path testing realistic. The configured
        calibration_offset is applied before the reading is wrapped in
        a SensorReading.

        Returns:
            SensorReading: The calibrated pressure reading with the
            current timestamp.
        """
        if random.random() < 0.1:
            # Occasional over-pressure spike, for alert-testing.
            raw_value = random.uniform(self.ALARM_THRESHOLD, self.safe_max + 1.0)
        else:
            raw_value = random.uniform(self.safe_min, self.ALARM_THRESHOLD * 0.9)

        calibrated_value = raw_value + self.calibration_offset

        return SensorReading(
            sensor_id=self.sensor_id,
            value=calibrated_value,
            unit=self.unit,
            timestamp=datetime.now(),
        )

    def __str__(self) -> str:
        """Return a human-readable summary of this sensor."""
        return (
            f"PressureNode({self.sensor_id} @ {self.location}, "
            f"range=[{self.safe_min}, {self.safe_max}] {self.unit})"
        )

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation."""
        return (
            f"PressureNode(sensor_id={self.sensor_id!r}, "
            f"location={self.location!r}, "
            f"calibration_offset={self.calibration_offset!r})"
        )
        
