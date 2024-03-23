import numpy as np
import json
from pprint import pprint

class Foo:
    STANDARD_GRAVITY = 9.81

    def __init__(self):
         self.steps = [1,2,3,4,5,6,7]
         self.means = [
              [2.0, 1.0, 2.1],
              [2.1, 1.1, 2.15],
              [2.05, 0.9, 2.13],
              [2.03, 1.11, 2.11],
              [2.1, 1.1, 2.12],
              [2.01, .095, 1.95],
              [2.0, 1.0, 2.0]
         ]

    def calculate_calibration_data(self):        
            means = np.array(self.means)

            offset = np.array([
                (means[2,0] + means[3,0]) / 2.0,
                (means[4,1] + means[5,1]) / 2.0,
                (means[0,2] + means[6,2]) / 2.0
            ])
            pprint(offset)
            print("---")

            gains = np.array([
                (means[2,0] - means[3,0]) / (self.STANDARD_GRAVITY * 2.0),
                (means[4,1] - means[5,1]) / (self.STANDARD_GRAVITY * 2.0),
                (means[0,2] - means[6,2]) / (self.STANDARD_GRAVITY * 2.0)
            ])
            pprint(gains)
            print("---")

            corrected_means = (means - offset) / gains
            pprint(corrected_means)
            print("---")

            angles_ = np.zeros((len(self.steps), 3))
            for i in range(len(self.steps)):
                for d in range(3):
                    angles_[i][d] = np.rad2deg(
                        np.arcsin(
                            corrected_means[i,d] / np.sqrt(np.sum(corrected_means[i, :]**2))
                        )
                    )

            pprint(angles_)
            print("---")

            angles = np.array([
                (angles_[0,0] + angles_[1,0]) / 2.0,  # x-axis
                -(angles_[0,1] + angles_[1,1]) / 2.0, # y-axis
                -(angles_[3,1] - angles_[2,1]) / 2.0  # z-axis
            ])

            calibration = {
                "offset": offset.tolist(),
                "gains": gains.tolist(),
                "angles": angles.tolist()
            }

            print( json.dumps(calibration, indent=2) )


Foo().calculate_calibration_data()