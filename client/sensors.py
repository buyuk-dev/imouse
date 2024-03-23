import json
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Optional

import numpy as np
from kivy.logger import Logger
from numpy.typing import NDArray
from plyer import accelerometer, gyroscope
#from abc import ABC, abstractmethod


@dataclass
class SensorCalibrationData:
    offset: NDArray
    gains: NDArray
    angles: NDArray

    def from_json(cls, path="calibration.json") -> 'SensorCalibrationData':
        path = Path(path)
        data = json.loads(path.read_text())
        return SensorCalibrationData(
            offset=np.array(data["offset"]),
            gains=np.array(data["gains"]),
            angles=np.array(data["angles"]),
        )


@dataclass
class SensorReading:
    timestamp: float
    data: NDArray


class Sensor:
    def __init__(self, sensor:Any, name:str):
        self.sensor:Any = sensor
        self.name:str = name
        self.calibration_data:Optional[SensorCalibrationData] = None

    def calibrate(self, calibration_data_path):
        self.calibration_data = SensorCalibrationData.from_json(calibration_data_path)

    def enable(self):
        try:
            self.sensor.enable()
        except Exception as e:
            Logger.exception(f"Failed to enable sensor: {self.name}")
    
    def disable(self):
        self.sensor.disable()

    def correct(self, reading:NDArray):
        if self.calibration_data:
            return (reading - self.calibration_data.offset) / self.calibration_data.gains
        else:
            return reading

    def read(self, correct:bool=True) -> SensorReading:
        reading = self.read_raw()
        timestamp = time.perf_counter()

        if reading and all(reading):
            reading = np.array(reading)
        else:
            reading = np.zeros(3)

        if correct:
            reading = self.correct(reading)

        return SensorReading(timestamp=timestamp, data=reading)

    def read_raw(self):
        raise NotImplementedError()


class Accelerometer(Sensor):
    def __init__(self):
        super().__init__(accelerometer, "acc")
        self.calibrate("calibration.json")

    def read_raw(self):
        """
        Return acceleration readings if available [ m/s*s ]
        """
        return self.sensor.acceleration[:3]


class DummySensor(Sensor):

    class Dummy:
        def enable(self): pass
        def disable(self): pass

    def __init__(self):
        super().__init__(self.Dummy(), "dummy_sensor")
    
    def read_raw(self):
        return np.random.random(3).tolist()


class Gyroscope(Sensor):
    def __init__(self):
        super().__init__(gyroscope, "gyro")
    
    def read_raw(self):
        """
        Return gyroscope readings (roll, pitch, yaw) [ rad / s ]
        """
        return gyroscope.rotation[:3]
