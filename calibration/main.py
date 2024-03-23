"""
Helper app for computing accelerometer calibration data.
Based on: https://stackoverflow.com/questions/43364006/android-accelerometer-calibration
"""
import json
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from plyer import accelerometer
from kivy.clock import Clock
from kivy.logger import Logger
import numpy as np


kv = '''
BoxLayout:
    orientation: 'vertical'
    Button:
        text: 'Start Calibration'
        on_press: app.start_calibration()
    Button:
        text: 'Register Data'
        on_press: app.make_step()
    Label:
        id: instructions
        text: 'Follow the instructions'
    TextInput:
        id: calibration_output
        text: ''
        readonly: True
        multiline: True
'''


class CalibrationApp(App):
    """
    Calibration process:
        Users sees current step instructions and "register" button.
        When user clicks on the "register" button the app collects N readings samples from the accelerometer.
        When all samples are collected app transitions to the next step.
        Repeat steps 1 - 3 until last step.
        When all steps are completed calculate calibration parameters.
        Display calibration data for the user to copy.
    """
    STANDARD_GRAVITY = 9.81

    def __init__(self):
        super().__init__()
        self.means = []
        self.sensor_readings = []
        self.reading_frequency = 1.0 / 20.0
        self.reading_interval = 5.0

        self.steps = [
            'Lay flat',
            'Rotate 180°',
            'Lay on the left side',
            'Rotate 180°',
            'Lay vertical',
            'Rotate 180° upside-down',
            'Lay face down'
        ]

    def build(self):
        return Builder.load_string(kv)

    def start_calibration(self):
        accelerometer.enable()
        self.current_step = 0
        self.root.ids.instructions.text = self.steps[self.current_step]

    def make_step(self):
        self.event = Clock.schedule_interval(self.collect_readings, self.reading_frequency)
        Clock.schedule_once(self.finish_step, self.reading_interval)

    def finish_step(self, dt):
        self.event.cancel()
        self.means.append(np.array(self.sensor_readings).mean(axis=0))

        self.sensor_readings = []
        self.current_step += 1

        if self.current_step == len(self.steps):
            self.calculate_calibration_data()
        else:
            self.root.ids.instructions.text = self.steps[self.current_step]


    def calculate_calibration_data(self):
        self.root.ids.instructions.text = "Calculating calibration data..."
        accelerometer.disable()

        means = np.array(self.means)

        offset = np.array([
            (means[2,0] + means[3,0]) / 2.0,
            (means[4,1] + means[5,1]) / 2.0,
            (means[0,2] + means[6,2]) / 2.0
        ])
        gains = np.array([
            (means[2,0] - means[3,0]) / (self.STANDARD_GRAVITY * 2.0),
            (means[4,1] - means[5,1]) / (self.STANDARD_GRAVITY * 2.0),
            (means[0,2] - means[6,2]) / (self.STANDARD_GRAVITY * 2.0)
        ])

        corrected_means = (means - offset) / gains

        angles_ = np.zeros((len(self.steps), 3))
        for i in range(len(self.steps)):
            for d in range(3):
                angles_[i][d] = np.rad2deg(
                    np.arcsin(
                        corrected_means[i,d] / np.sqrt(np.sum(corrected_means[i, :]**2))
                    )
                )

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

        self.root.ids.calibration_output.text = json.dumps(calibration, indent=2)

    def collect_readings(self, dt):
        try:
            reading = accelerometer.acceleration[:3]
            if reading is not None and all(reading):
                self.sensor_readings.append(reading)
        except Exception as e:
            Logger.exception("Error encountered while collecting sensor readings.")


if __name__ == '__main__':
    CalibrationApp().run()
