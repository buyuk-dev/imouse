import os
import sys
from pathlib import Path

project_root_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(project_root_path)

import socket
import threading
import time
from typing import Callable

import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.settings import SettingsWithSidebar
from kivy.utils import platform
from numpy.typing import NDArray

from common.command import Command
from common.math import LowPassFilter, trapezoidal_interpolation
from sensors import Accelerometer, SensorReading, DummySensor


if platform == "win":
    accelerometer = DummySensor()
else:
    accelerometer = Accelerometer()


def get_vec_info_str(header: str, vec: NDArray) -> str:
    return f"{header}: " + " | ".join([f"{x:.3f}" for x in vec])


class MouseProcessorThread(threading.Thread):
    """
    Thread responsible for reading sensor data and converting them into mouse commands stream sent to the server.
    """

    def __init__(self, config, set_info_text_func: "Callable" = None):
        """
        Initialize the thread.
        @param connection: socket over which commands will be sent to the server.
        @set_info_text_func: callable object which can be used to display diagnostic info on the client app user interface.
        """
        super().__init__()
        Logger.info("Creating processor thread.")
        self.thread_running = threading.Event()
        self.thread_running.clear()
        self.config = config
        self.set_info_text = set_info_text_func

    def stop_thread(self):
        """
        Stop the thread before next step.
        """
        Logger.info("Stopping processor thread.")
        self.thread_running.clear()

    def run(self):
        """
        Initialize variables and run processing loop until thread stopped.
        """
        Logger.info("Running processor thread.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            address, port = self.config.get("general", "server_address").split(":")
            connection.connect((address, int(port)))

            self.threshold = float(self.config.get("general", "acc_threshold"))
            self.mouse_speed = float(self.config.get("general", "mouse_speed"))
            self.inactive_time = float(self.config.get("general", "inactive_time"))
            self.movement_time = 0.0

            self.acc_filter = LowPassFilter(
                float(self.config.get("general", "acc_lp_alpha"))
            )

            self.speed = np.zeros(3)
            self.prev_speed = np.zeros(3)
            self.prev_acc = np.zeros(3)
            self.prev_time = time.time()

            Logger.info("Mouse_speed: %s", str(self.mouse_speed))

            self.thread_running.set()
            while self.thread_running.is_set():
                try:
                    self.step(connection)
                except Exception as e:
                    Logger.exception("Error in MouseProcessorThread step function.")
                    self.stop_thread()
            
            accelerometer.disable()

    def step(self, connection):
        """
        Compute control signal and send mouse command to the server.
        """
        reading = accelerometer.read(True)
        Logger.info("reading.data {}".format(reading.data))

        filtered = self.acc_filter.apply(reading.data)

        dt_time = reading.timestamp - self.prev_time
        self.movement_time += dt_time
        self.prev_time = reading.timestamp

        self.speed += trapezoidal_interpolation(filtered, self.prev_acc, dt_time)
        self.prev_acc = filtered

        if (filtered[:2] < self.threshold).all() and self.movement_time > self.inactive_time:
            Logger.info(
                f"Reseting mouse speed, device at rest for more than {self.inactive_time}s."
            )
            self.speed = np.zeros(3)
            self.prev_speed = np.zeros(3)
            self.prev_acc = np.zeros(3)
            self.acc_filter.reset()
            self.movement_time = 0.0

        delta_pos = trapezoidal_interpolation(self.speed, self.prev_speed, dt_time)
        self.prev_speed = self.speed

        mouse_move = delta_pos * self.mouse_speed

        info_text_lines = [
            ("Raw Accelerometer", reading.data),
            ("Speed", self.speed),
            ("Delta Position", delta_pos),
            ("Mouse Move", mouse_move),
        ]

        info_text_str = os.linesep.join(
            [get_vec_info_str(*entry) for entry in info_text_lines]
        )
        Logger.info(info_text_str)

        if self.set_info_text:
            Clock.schedule_once(lambda dt: self.set_info_text(info_text_str), 0)

        cmd = Command(move=reading.data.tolist())
        cmd.send(connection)
        cmd.wait_for_ack(connection)


class MouseClientApp(App):
    """
    Mouse Client App With Kivy Framework.
    """

    def build(self):
        self.main_layout = BoxLayout(orientation="vertical")
        self.build_mouse_buttons_layout()
        self.build_info_layout()
        self.build_settings_layout()
        accelerometer.enable()
        return self.main_layout

    def build_mouse_buttons_layout(self):
        self.top_container = AnchorLayout(
            anchor_x="center", anchor_y="top", size_hint=(1, 0.25)
        )
        self.buttons_layout = BoxLayout(
            size_hint=(1.0, 1.0)
        )  # Occupies less space for more realistic spacing

        self.left_button = Button(text="Left Click", size_hint=(0.45, 1))
        self.right_button = Button(text="Right Click", size_hint=(0.45, 1))
        self.scroll_area = Button(
            text="Scroll", size_hint=(0.1, 1.0)
        )  # Narrower and centered

        self.buttons_layout.add_widget(self.left_button)
        self.buttons_layout.add_widget(self.scroll_area)
        self.buttons_layout.add_widget(self.right_button)

        self.top_container.add_widget(self.buttons_layout)
        self.main_layout.add_widget(self.top_container)

    def build_info_layout(self):
        self.label = Label(
            text="Accelerometer:",
            size_hint=(1.0, 0.65),
            halign="center",
            valign="middle",
        )
        self.label.bind(
            size=lambda *x: setattr(self.label, "text_size", self.label.size)
        )
        self.main_layout.add_widget(self.label)

    def build_settings_layout(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        self.open_settings_btn = Button(text="Open Settings", size_hint=(1.0, 0.1))
        self.open_settings_btn.bind(on_press=self.open_settings)
        self.main_layout.add_widget(self.open_settings_btn)

    def on_start(self):
        Logger.info("on_start()")
        self.processor = None
        self.open_settings()

    def close_settings(self, *args, **kwargs):
        Logger.info("close_settings()")
        super().close_settings(*args, **kwargs)

        def set_info_label_text(info):
            self.label.text = info

        self.on_stop()

        self.processor = MouseProcessorThread(self.config, set_info_label_text)
        self.processor.start()

    def build_config(self, config):
        Logger.info("build_config()")
        config.setdefaults(
            "general",
            {
                "mouse_speed": 1000.0,
                "gyro_lp_alpha": np.pi / 90.0,
                "acc_lp_alpha": 0.1,
                "acc_threshold": 0.2,
                "inactive_time": 0.25,
                #'server_address': "localhost:5000"
                "server_address": "192.168.8.24:5000",
            },
        )

    def build_settings(self, settings):
        with open("settings.json", "r") as settings_json:
            settings.add_json_panel("Settings", self.config, data=settings_json.read())

    def on_config_change(self, config, section, key, value):
        Logger.info(f"Config changed: {section}, {key}, {value}")

    def on_stop(self):
        Logger.info("on_stop()")
        if self.processor:
            Logger.info("Stopping processor thread.")
            self.processor.stop_thread()
            self.processor.join()
            Logger.info("Processor thread stopped.")


if __name__ == "__main__":
    MouseClientApp().run()
