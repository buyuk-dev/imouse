import numpy as np
from numpy.typing import NDArray
from typing import Any


class Constants:
    EARTH_ACC = np.array([0.0, 0.0, 9.81])


def device_space_to_world_space(vec:'np.array', device_orientation_vec:'np.array') -> 'NDArray[Any]':
    """
    Convert vector (mostly accelerometer readings) from device space into world space using gyro readings as a reference.
    """
    roll, pitch, yaw = device_orientation_vec
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])
    
    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    R = Rz @ Ry @ Rx

    R_inv = R.T

    v_device = np.array(vec)
    v_world = R_inv @ v_device

    return v_world


class LowPassFilter:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.reset()

    def apply(self, current_value):
        filtered_value = self.previous_filtered + self.alpha * (current_value - self.previous_filtered)
        self.previous_filtered = filtered_value
        return filtered_value
    
    def reset(self):
        self.previous_filtered = np.zeros(3)


def trapezoidal_interpolation(sample, previous_sample, dt):
    return 0.5 * (sample - previous_sample) * dt