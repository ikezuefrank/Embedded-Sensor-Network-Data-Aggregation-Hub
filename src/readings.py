"""The SensorReading value object.

A reading is just a value, its unit and a timestamp - but it carries a fair
bit of operator overloading (Week 4). You can add two readings, abs() one to
get how far it sits from a setpoint, and sort them. total_ordering writes the
comparison methods we don't define ourselves.
"""

from functools import total_ordering


@total_ordering
class SensorReading:
    """One measurement taken from a sensor at a moment in time."""

    def __init__(self, sensor_id, value, unit, timestamp, setpoint=0.0):
        self.sensor_id = sensor_id
        self.value = float(value)
        self.unit = unit
        self.timestamp = timestamp
        self.setpoint = float(setpoint)  # reference used by abs() below

    def __add__(self, other):
        """Add another same-unit reading, or a plain number."""
        if isinstance(other, SensorReading):
            if other.unit != self.unit:
                raise TypeError(
                    f"can't add readings in {self.unit!r} and {other.unit!r}")
            # the merged reading keeps whichever timestamp is later
            return SensorReading("AGGREGATE", self.value + other.value, self.unit,
                                 max(self.timestamp, other.timestamp), self.setpoint)
        if isinstance(other, (int, float)):
            return SensorReading(self.sensor_id, self.value + other, self.unit,
                                 self.timestamp, self.setpoint)
        raise TypeError(f"can't add SensorReading and {type(other).__name__}")

    def __radd__(self, other):
        # makes sum([...]) work: sum starts at 0, so 0 + reading is just reading
        return self if other == 0 else self.__add__(other)

    def __abs__(self):
        """How far the value is from its setpoint."""
        return abs(self.value - self.setpoint)

    def __eq__(self, other):
        if not isinstance(other, SensorReading):
            return NotImplemented
        return (self.sensor_id, self.value, self.unit, self.timestamp) == \
               (other.sensor_id, other.value, other.unit, other.timestamp)

    def __lt__(self, other):
        if not isinstance(other, SensorReading):
            return NotImplemented
        return self.value < other.value

    def __hash__(self):
        # id + value + timestamp is enough to tell readings apart in a set
        return hash((self.sensor_id, self.value, self.timestamp))

    def __str__(self):
        return (f"{self.value:.2f} {self.unit} @ "
                f"{self.timestamp:%Y-%m-%d %H:%M} [{self.sensor_id}]")

    def __repr__(self):
        return (f"SensorReading(sensor_id={self.sensor_id!r}, value={self.value!r}, "
                f"unit={self.unit!r}, timestamp={self.timestamp!r}, "
                f"setpoint={self.setpoint!r})")
