"""Tests for the custom exception hierarchy."""

from datetime import datetime

import pytest

from src.exceptions import (
    SensorHubError,
    SensorOfflineError,
    CalibrationError,
    CommunicationTimeoutError,
)

ALL = [SensorOfflineError, CalibrationError, CommunicationTimeoutError]


@pytest.mark.parametrize("exc_cls", ALL)
def test_stores_three_fields(exc_cls):
    err = exc_cls("SN-TEMP-01", "something broke")
    assert err.sensor_id == "SN-TEMP-01"
    assert err.detail == "something broke"
    assert isinstance(err.timestamp, datetime)


@pytest.mark.parametrize("exc_cls", ALL)
def test_is_an_ioerror_and_hub_error(exc_cls):
    assert issubclass(exc_cls, IOError)
    assert issubclass(exc_cls, SensorHubError)


def test_message_includes_sensor_id():
    with pytest.raises(SensorOfflineError) as info:
        raise SensorOfflineError("SN-GASC-04", "no reply")
    assert "SN-GASC-04" in str(info.value)


def test_base_class_catches_any_subclass():
    with pytest.raises(SensorHubError):
        raise CommunicationTimeoutError("SN-FLOW-05", "timed out")
