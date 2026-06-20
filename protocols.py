"""src/protocols.py

CANBusProtocol — simulated CAN Bus client.

NOTE: This file contains ONLY the CANBusProtocol class, which is one of three
concrete CommunicationProtocol subclasses being built in parallel by teammates
(MQTTProtocol, ModbusProtocol, CANBusProtocol). When merging, all three classes
plus the CommunicationProtocol ABC belong together in a single src/protocols.py.
"""
import random

# TODO: swap to real CommunicationProtocol import from src.protocols after merge
from src.protocols_base_stub import CommunicationProtocol
from src.exceptions import CommunicationTimeoutError


class CANBusProtocol(CommunicationProtocol):
    """Simulated CAN Bus (Controller Area Network) communication client.

    This class models the behavior of a CAN Bus interface used in industrial
    and automotive embedded systems, WITHOUT touching real hardware or sockets.
    All connection, send, and receive operations are simulated using random
    success/failure to mimic the unreliability of a real embedded bus, which
    is useful for exercising the AggregationHub's error-handling paths.

    Attributes:
        bus_channel (str): The simulated CAN interface name (e.g. "can0").
        bitrate (int): The simulated bus bitrate in bits per second.
    """

    #: Probability (0.0-1.0) that connect() randomly simulates a failure.
    _CONNECT_FAILURE_RATE = 0.05

    def __init__(self, bus_channel: str = "can0", bitrate: int = 500000):
        """Initialize a simulated CAN Bus protocol handler.

        Args:
            bus_channel: Name of the simulated CAN interface (default "can0").
            bitrate: Simulated bus bitrate in bits per second (default 500000).
        """
        super().__init__()
        self.bus_channel = bus_channel
        self.bitrate = bitrate

    def connect(self) -> bool:
        """Simulate establishing a connection to the CAN bus.

        Sets is_connected to True on success. With low probability, simulates
        a bus initialization failure by raising CommunicationTimeoutError
        instead (mimics a real CAN controller failing to reach bus-on state).

        Returns:
            bool: True if the simulated connection succeeded.

        Raises:
            CommunicationTimeoutError: If the simulated connection attempt fails.
        """
        if random.random() < self._CONNECT_FAILURE_RATE:
            raise CommunicationTimeoutError(
                self.bus_channel,
                f"Failed to reach bus-on state on {self.bus_channel} "
                f"at {self.bitrate} bps",
            )
        self._is_connected = True
        return True

    def send(self, data: bytes) -> bool:
        """Simulate sending a CAN frame.

        Args:
            data: Raw payload bytes to send (a real CAN frame would be capped
                at 8 data bytes per classic frame, but this is not enforced
                here since the simulation operates at a higher abstraction
                level).

        Returns:
            bool: True if the simulated send succeeded.

        Raises:
            CommunicationTimeoutError: If not currently connected.
        """
        if not self.is_connected:
            raise CommunicationTimeoutError(
                self.bus_channel,
                "Cannot send CAN frame: bus is not connected",
            )
        return True

    def receive(self, max_bytes: int) -> bytes:
        """Simulate receiving a CAN frame payload.

        Args:
            max_bytes: Maximum number of bytes to simulate receiving.

        Returns:
            bytes: A simulated CAN frame payload, truncated to max_bytes.

        Raises:
            CommunicationTimeoutError: If not currently connected.
        """
        if not self.is_connected:
            raise CommunicationTimeoutError(
                self.bus_channel,
                "Cannot receive: bus is not connected",
            )
        simulated_payload = b"\xde\xad\xbe\xef\x00\x01\x02\x03"
        return simulated_payload[:max_bytes]

    def disconnect(self) -> None:
        """Simulate tearing down the CAN bus connection.

        Sets is_connected to False. Safe to call even if already disconnected.
        """
        self._is_connected = False

    def __str__(self) -> str:
        """Return a human-readable summary of the CAN bus connection."""
        state = "connected" if self.is_connected else "disconnected"
        return f"CANBusProtocol({self.bus_channel} @ {self.bitrate}bps, {state})"

    def __repr__(self) -> str:
        """Return an unambiguous representation for debugging."""
        return (
            f"CANBusProtocol(bus_channel={self.bus_channel!r}, "
            f"bitrate={self.bitrate!r}, is_connected={self.is_connected!r})"
        )
