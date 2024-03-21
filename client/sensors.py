import numpy as np
from plyer import accelerometer, gyroscope


acc_calibration_data = {
  "offset": np.array([
    -0.11411178872940386,
    -0.14229462696955775,
    9.734940837024975,
  ]),
  "gains": np.array([
    1.004352956783392,
    1.0048621553145678,
    1.0
    #7.932018502444785e-05,
  ]),
  "angles": np.array([
    -0.00013014404704852112,
    -1.5916878246580541,
    -89.99544557473384,
  ])
}


def init_gyroscope():
    """
    Try to initialize gyroscope.
    """
    try:
        gyroscope.enable()
    except Exception as e:
        print(f"michalski: Failed to enable gyroscope: {e}")


def init_accelerometer():
    """
    Try to initialize accelerometer.
    """
    try:
        accelerometer.enable()
    except Exception as e:
        print(f"michalski: failed to enable accelerometer: {e}")



def get_acc_reading(filter_=None):
    """
    Return acceleration readings if available [ m/s*s ]
    """
    acc_raw = accelerometer.acceleration[:3]
    if acc_raw and all(acc_raw):
        reading = np.array(acc_raw)
    else:
        reading = np.zeros(3)
    if filter_ is not None:
        reading = filter_.apply(reading)

    return (reading - acc_calibration_data["offset"]) / acc_calibration_data["gains"]


def get_gyro_reading(filter_=None):
    """
    Return gyroscope readings (roll, pitch, yaw) [ rad / s ]
    """
    rotation_raw = gyroscope.rotation[:3]
    if rotation_raw and all(rotation_raw):
        reading = np.array(rotation_raw)
    else:
        reading = np.zeros(3)
    
    if filter_:
        reading = filter_.apply(reading)

    return reading
