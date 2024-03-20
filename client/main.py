import os
import sys

from pathlib import Path
project_root_path = str(Path(__file__).absolute().parent.parent)
#print(project_root_path)
sys.path.append(project_root_path)

import socket
import threading
import time

import numpy as np

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.settings import SettingsWithSidebar

from common.command import Command
from client.config import Config
from common.math import device_space_to_world_space, LowPassFilter, Constants
from client.sensors import *

from numpy.typing import NDArray
from typing import Any, Callable


def get_vec_info_str(header:str, vec:NDArray) -> str:
    return f"{header}: " + " | ".join(vec)


class MouseProcessorThread(threading.Thread):
    """
    Thread responsible for reading sensor data and converting them into mouse commands stream sent to the server.
    """
    def __init__(self, config, set_info_text_func:'Callable'=None):
        """
        Initialize the thread.
        @param connection: socket over which commands will be sent to the server.
        @set_info_text_func: callable object which can be used to display diagnostic info on the client app user interface.
        """
        super().__init__()
        print("mmichalski: creating processor thread")
        self.thread_running = threading.Event()
        self.thread_running.clear()
        self.config = config
        self.set_info_text = set_info_text_func
        init_accelerometer()
        init_gyroscope()

    def stop_thread(self):
        """
        Stop the thread before next step.
        """
        print("mmichalski: stopping processor thread")
        self.thread_running.clear()

    def run(self):
        """
        Initialize variables and run processing loop until thread stopped.
        """
        print("mmichalski: running processor thread")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            address, port = self.config.get("general", "server_address").split(":")
            connection.connect((address, int(port)))

            self.gyro_filter = LowPassFilter(float(self.config.get('general', 'gyro_lp_alpha')))
            self.acc_filter = LowPassFilter(float(self.config.get('general', 'acc_lp_alpha')))

            self.speed = np.zeros(3)
            self.orientation = np.zeros(3)
            self.position = np.zeros(3)

            self.prev_raw_acc = np.zeros(3)
            self.prev_raw_gyro = np.zeros(3)

            self.prev_time = time.time()

            self.thread_running.set()
            while self.thread_running.is_set():
                try:
                    self.step(connection)        
                except Exception as e:
                    print(f"michalski: error in processor step: {e}")
    
    def step(self, connection):
        """
        Compute control signal and send mouse command to the server.
        """
        raw_acc = get_acc_reading(self.acc_filter)
        raw_gyro = get_gyro_reading(self.gyro_filter)
        curr_time = time.time()

        dt_time = curr_time - self.prev_time
        dt_acc = raw_acc - self.prev_raw_acc
        dt_gyro = raw_gyro - self.prev_raw_gyro

        self.prev_time = curr_time
        self.prev_raw_acc = raw_acc
        self.prev_raw_gyro = raw_gyro

        self.orientation += raw_gyro * dt_time

        self.world_acc = device_space_to_world_space(raw_acc, self.orientation) - Constants.EARTH_ACC
        self.speed += self.world_acc * dt_time

        delta_pos = self.speed * dt_time
        self.position += delta_pos

        mouse_move = delta_pos * float(self.config.get('general', 'mouse_speed'))

        info_text_lines = [
            get_vec_info_str("Raw Accelerometer", raw_acc),
            get_vec_info_str("World Accelerometer", self.world_acc),
            get_vec_info_str("Position", self.position),
            get_vec_info_str("Orientation", self.orientation),
            get_vec_info_str("Delta Position", delta_pos)
        ]

        if self.set_info_text:
            Clock.schedule_once(lambda dt: self.set_info_text(os.linesep.join(info_text_lines)), 0)

        cmd = Command(dx=mouse_move[0], dy=mouse_move[1])
        cmd.send_command(connection)
        cmd.wait_for_ack(connection)


class MouseClientApp(App):
    """
    Mouse Client App With Kivy Framework.
    1. build() - build app layout
    2. on_start() - open settings
    3. open_settings() - 
    4. close_settings() - start processor thread
    5. on_stop() - stop processor thread
    """
    def build(self):
        self.main_layout = BoxLayout(orientation='vertical')
        self.build_mouse_buttons_layout()
        self.build_info_layout()
        self.build_settings_layout()
        return self.main_layout        
        
    def build_mouse_buttons_layout(self):
        self.top_container = AnchorLayout(anchor_x='center', anchor_y='top', size_hint=(1, 0.25))
        self.buttons_layout = BoxLayout(size_hint=(1.0, 1.0))  # Occupies less space for more realistic spacing
        
        self.left_button = Button(text='Left Click', size_hint=(0.45, 1))
        self.right_button = Button(text='Right Click', size_hint=(0.45, 1))
        self.scroll_area = Button(text='Scroll', size_hint=(0.1, 1.0))  # Narrower and centered
        
        self.buttons_layout.add_widget(self.left_button)
        self.buttons_layout.add_widget(self.scroll_area)
        self.buttons_layout.add_widget(self.right_button)
        
        self.top_container.add_widget(self.buttons_layout)
        self.main_layout.add_widget(self.top_container)
        
    def build_info_layout(self):
        self.label = Label(text='Accelerometer:', size_hint=(1.0, 0.65), halign="center", valign="middle")
        self.label.bind(size=lambda *x: setattr(self.label, 'text_size', self.label.size))
        self.main_layout.add_widget(self.label)

    def build_settings_layout(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        self.open_settings_btn = Button(text='Open Settings', size_hint=(1.0, 0.1))
        self.open_settings_btn.bind(on_press=self.open_settings)
        self.main_layout.add_widget(self.open_settings_btn)

    def on_start(self):
        self.processor = None
        self.open_settings()

    def close_settings(self, *args, **kwargs):
        super().close_settings(*args, **kwargs)
        def set_info_label_text(info):
            self.label.text = info
        
        if self.processor:
            print("mmichalski: stopping processor thread")
            self.processor.stop_thread()
            self.processor.join()
            print("mmichalski: processor thread stopped")

        self.processor = MouseProcessorThread(self.config, set_info_label_text)
        self.processor.run()

    def build_config(self, config):
        config.setdefaults('general', {
            'mouse_speed': 100.0,
            'gyro_lp_alpha': np.pi / 90.0,
            'acc_lp_alpha': 0.1,
            'server_address': "localhost:5000"
        })

    def build_settings(self, settings):
        with open("settings.json", "r") as settings_json:
            settings.add_json_panel('Settings', self.config, data=settings_json.read())

    def on_config_change(self, config, section, key, value):
        print(f"michalski: Config changed: {section}, {key}, {value}")

    def on_stop(self):
        self.processor.stop_thread()


if __name__ == '__main__':
    MouseClientApp().run()