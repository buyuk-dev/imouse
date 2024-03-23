import numpy as np
from numpy.typing import NDArray
from typing import Any
from collections import deque


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


class RollingAverage:
    def __init__(self, window=5):
        self.window = window
        self.reset()

    def reset(self):
        self.samples = deque([np.zeros(3) for _ in range(self.window)], maxlen=self.window)

    def apply(self, current_value) -> NDArray:
        self.samples.append(np.array(current_value))
        return np.mean(np.array(self.samples), axis=0)


def trapezoidal_interpolation(sample, previous_sample, dt):
    return 0.5 * (sample + previous_sample) * dt


class VelocityEstimator:
    def __init__(
            self, dt: float = 0.05, process_noise_var: float = 1e-2, measurement_noise_var: float = 1e-2,
            inactivity_threshold=None, inactivity_time_threshold=None):
        """
        Initializes the velocity estimator for 3D vectors with acceleration considered in the state.
        
        Args:
        - dt: Sampling interval in seconds.
        - process_noise_var: Variance of the process noise (applied to acceleration).
        - measurement_noise_var: Variance of the measurement noise.
        """
        if inactivity_time_threshold is None: inactivity_time_threshold = 20.0 * dt
        if inactivity_threshold is None: inactivity_threshold = 0.5

        self.inactivity_threshold = inactivity_threshold
        self.inactivity_time_threshold = inactivity_time_threshold
        self.inactivity_timer = 0.0

        self.dt = dt
        # State vector [vx, ax, vy, ay, vz, az] (velocity and acceleration in 3D)
        self.x = np.zeros(6)
        # Initial state covariance
        self.P = np.eye(6) * 500  
        # State transition model
        self.F = np.array([[1, dt, 0, 0, 0, 0],
                           [0, 1, 0, 0, 0, 0],
                           [0, 0, 1, dt, 0, 0],
                           [0, 0, 0, 1, 0, 0],
                           [0, 0, 0, 0, 1, dt],
                           [0, 0, 0, 0, 0, 1]])
        # Measurement model (measuring acceleration in 3D)
        self.H = np.array([[0, 1, 0, 0, 0, 0],
                           [0, 0, 0, 1, 0, 0],
                           [0, 0, 0, 0, 0, 1]])
        # Process noise (higher uncertainty in acceleration)
        self.Q = np.eye(6) * process_noise_var
        self.Q[1, 1], self.Q[3, 3], self.Q[5, 5] = process_noise_var * 10, process_noise_var * 10, process_noise_var * 10  # Increase for ax, ay, az
        # Measurement noise
        self.R = np.eye(3) * measurement_noise_var
        # Control input model (unused in this case, but defined for completeness)
        self.B = np.zeros((6, 3))
        # Control input (unused)
        self.u = np.zeros(3)


    def check_and_reset_inactivity(self, current_acceleration):
        if np.linalg.norm(current_acceleration[:2]) < self.inactivity_threshold:
            self.inactivity_timer += self.dt
            if self.inactivity_timer > self.inactivity_time_threshold:
                self.reset()
                self.inactivity_timer = 0.0
        else:
            self.inactivity_timer = 0.0

    def reset(self):
        """
        Resets the filter to initial state.
        """
        self.x = np.zeros(6)
        self.P = np.eye(6) * 500

    def apply(self, current_acceleration: NDArray) -> NDArray:
        """
        Applies the Kalman filter update with a new 3D acceleration measurement.
        
        Args:
        - current_acceleration: The current acceleration measurement [ax, ay, az].
        
        Returns: 
        - The estimated velocity [vx, vy, vz] in 3D.
        """
        self.check_and_reset_inactivity(current_acceleration)

        # Predict
        self.x = np.dot(self.F, self.x) + np.dot(self.B, self.u)
        self.P = np.dot(self.F, np.dot(self.P, self.F.T)) + self.Q

        # Update
        Z = np.array(current_acceleration)  # Measurement
        y = Z - np.dot(self.H, self.x)  # Measurement residual
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R  # Residual covariance
        K = np.dot(self.P, np.dot(self.H.T, np.linalg.inv(S)))  # Kalman gain
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(K, np.dot(self.H, self.P))

        # Return estimated velocity (3D)
        return self.x[::2]  # Extracting vx, vy, and vz from the state vector
