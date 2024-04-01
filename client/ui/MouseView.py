from kivy.uix.screenmanager import Screen
from kivy.logger import Logger

class MouseView(Screen):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial = 0
        self.whl_down = False

    def on_lmb_press(self):
        Logger.info("LMB pressed.")

    def on_rmb_press(self):
        Logger.info("RMB pressed.")

    def on_whl_press(self):
        Logger.info("WHL pressed.") 

    def on_scroll_start(self, button, touch):
        Logger.info(f"On touch down.")
        self.whl_down = True
        self.initial = touch.y
        return True

    def on_scroll_stop(self, button, touch):
        if self.whl_down:
            scroll_factor = touch.y - self.initial
            Logger.info(f"Wheel Scroll factor: {scroll_factor}")
            self.initial = 0
            self.whl_down = False
        return True
