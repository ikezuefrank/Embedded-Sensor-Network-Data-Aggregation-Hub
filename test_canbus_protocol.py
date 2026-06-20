"""tests/test_canbus_protocol.py

Tests for CANBusProtocol. Connection failures and frame loss are simulated
randomly inside CANBusProtocol with a low probability, so these tests retry
connect() a few times where relevant to avoid flaky failures.
"""
import pytest

from src.protocols import CANBusProtocol
from src.exceptions import CommunicationTimeoutError


def _connected_bus() -> CANBusProtocol:
    """Helper: return a CANBusProtocol instance that is guaranteed connected.

    connect() has a small random failure chance by design, so we retry a
    handful of times rather than asserting on a single call.
    """
    bus = CANBusProtocol(bus_channel="can0", bitrate=500000)
    for _ in range(20):
        try:
            bus.connect()
            return bus
        except CommunicationTimeoutError:
            continue
    pytest.fail("CANBusProtocol failed to connect after 20 attempts")


def test_connect_then_send_succeeds():
    """connect() followed by send() should succeed and return True."""
    bus = _connected_bus()
    assert bus.is_connected is True
    result = bus.send(b"\x01\x02\x03")
    assert result is True


def test_send_without_connecting_raises_timeout_error():
    """send() before connect() must raise CommunicationTimeoutError."""
    bus = CANBusProtocol()
    assert bus.is_connected is False
    with pytest.raises(CommunicationTimeoutError):
        bus.send(b"\x01\x02")


def test_receive_without_connecting_raises_timeout_error():
    """receive() before connect() must raise CommunicationTimeoutError."""
    bus = CANBusProtocol()
    with pytest.raises(CommunicationTimeoutError):
        bus.receive(8)


def test_disconnect_resets_state():
    """disconnect() should set is_connected back to False."""
    bus = _connected_bus()
    assert bus.is_connected is True
    bus.disconnect()
    assert bus.is_connected is False


def test_send_after_disconnect_raises_timeout_error():
    """send() after disconnect() should raise, proving state actually resets."""
    bus = _connected_bus()
    bus.disconnect()
    with pytest.raises(CommunicationTimeoutError):
        bus.send(b"\x01")


def test_receive_returns_bytes_within_max_bytes():
    """receive() should return a bytes object no longer than max_bytes."""
    bus = _connected_bus()
    payload = bus.receive(4)
    assert isinstance(payload, bytes)
    assert len(payload) <= 4


def test_constructor_defaults():
    """Default constructor args should be can0 and 500000 bps."""
    bus = CANBusProtocol()
    assert bus.bus_channel == "can0"
    assert bus.bitrate == 500000


def test_repr_and_str_contain_channel_name():
    """__str__ and __repr__ should mention the bus channel for debuggability."""
    bus = CANBusProtocol(bus_channel="can1", bitrate=250000)
    assert "can1" in str(bus)
    assert "can1" in repr(bus)
