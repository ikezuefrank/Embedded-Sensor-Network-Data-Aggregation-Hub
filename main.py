"""End-to-end demonstration of the aggregation hub.

Spins up a hub, registers the five sensor types plus two battery-powered
wireless nodes, attaches an alert rule to each wired sensor, then replays a
full 24-hour day (48 polls, one every 30 minutes) and prints the alerts and a
per-sensor statistical summary.

Run it with:  python main.py
"""

import json
import random
from datetime import datetime, timedelta

from src.hub import AggregationHub
from src.sensors import (TemperatureNode, PressureNode, VibrationNode,
                         GasConcentrationNode, FlowRateNode, WirelessSensorNode)
from src.protocols import MQTTProtocol, ModbusProtocol, CANBusProtocol
from src.alerts import AlertRule


def build_hub():
    """Assemble the demo hub: seven sensors and five alert rules."""
    hub = AggregationHub("Lagos-Refinery-Unit-3")

    for sensor in [
        TemperatureNode("SN-TEMP-01", "Crude heater outlet"),
        PressureNode("SN-PRES-02", "Reactor feed line"),
        VibrationNode("SN-VIBR-03", "Recycle pump P-101"),
        GasConcentrationNode("SN-GASC-04", "Compressor house"),
        FlowRateNode("SN-FLOW-05", "Product rundown"),
    ]:
        hub.register(sensor)

    # two remote nodes running on battery
    hub.register(WirelessSensorNode("SN-WTMP-06", "Tank farm (remote)", "°C",
                                    -40, 150, battery_level=22.0,
                                    discharge_per_reading=0.4))
    hub.register(WirelessSensorNode("SN-WVIB-07", "Jetty pump (remote)", "mm/s",
                                    0, 25, battery_level=100.0,
                                    discharge_per_reading=0.3))

    # each rule's max threshold is that sensor's alarm level
    hub.add_alert_rule(AlertRule("SN-TEMP-01", -40, 120))
    hub.add_alert_rule(AlertRule("SN-PRES-02", 0, 9))
    hub.add_alert_rule(AlertRule("SN-VIBR-03", 0, 20))
    hub.add_alert_rule(AlertRule("SN-GASC-04", 0, 20))
    hub.add_alert_rule(AlertRule("SN-FLOW-05", 0, 450))
    return hub


def show_protocols():
    """The three protocols share one interface - send over each in turn."""
    for proto in (MQTTProtocol(client_id="hub-uplink"),
                  ModbusProtocol(device_address=7),
                  CANBusProtocol(bus_channel="can1")):
        for _ in range(5):              # connect can randomly time out
            try:
                proto.connect()
                break
            except Exception:
                continue
        if proto.is_connected:
            proto.send(b"sensor-reading")
            print(f"  {proto}")
            proto.disconnect()
        else:
            print(f"  {type(proto).__name__}: link unavailable")


def main():
    random.seed(4)  # makes this showcase run reproducible
    hub = build_hub()
    print(f"Hub: {hub.name}  ({len(hub)} sensors registered)")

    print("\nProtocol uplinks (same interface, three transports):")
    show_protocols()

    # replay a 24-hour day: 48 polls spaced 30 minutes apart
    start = datetime.now().replace(microsecond=0) - timedelta(hours=24)
    for i in range(48):
        hub.poll_all(timestamp=start + i * timedelta(minutes=30))

    total = sum(s["count"] for s in hub.summary().values())
    print(f"\nReplayed 24h -> {total} readings across {len(hub)} sensors.")

    alerts = hub.get_alerts()
    print(f"\nAlerts raised: {len(alerts)}")
    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = len(hub.get_alerts(severity))
        if count:
            print(f"  {severity:<9}{count}")

    print("\nEarliest alerts:")
    for alert in alerts[:4]:
        print(f"  {alert.timestamp:%H:%M}  {alert}")

    print("\nPer-sensor summary:")
    print(json.dumps(hub.summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
