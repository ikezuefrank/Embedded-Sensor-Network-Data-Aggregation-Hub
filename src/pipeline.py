"""The data pipeline and the Readable protocol.

This is the duck-typing corner of the project (Week 4). Readable is a
typing.Protocol, not a base class - anything with a read() method counts as
Readable, whether or not it ever heard of SensorNode. DataPipeline.process
leans on that.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Readable(Protocol):
    """Structural type: anything with a read() returning a reading."""

    def read(self): ...


class DataPipeline:
    """Pulls a reading out of any Readable source."""

    @staticmethod
    def process(source: Readable):
        """Call source.read(). Works on a real sensor or any read()-able object."""
        if not isinstance(source, Readable):
            raise TypeError(f"{type(source).__name__} isn't Readable (no read() method)")
        return source.read()
