gshzvsjbd                "max": round(max(values), 3),
                "std_dev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
                "alert_counts": self._alert_counts(sensor_id),
            }
        return out

    def __len__(self) -> int:
        return len(self._sensors)

    def __contains__(self, sensor_id) -> bool:
        return sensor_id in self._sensors

    def __iter__(self):
        return iter(self._sensors.values())

    def __str__(self) -> str:
        return f"AggregationHub({self.name!r}, {len(self)} sensors, {len(self._alerts)} alerts)"

    def __repr__(self) -> str:
        return f"AggregationHub(name={self.name!r})"
