from kivy.app import App
from kivy.logger import Logger

class MouseClientApp(App):
    def open_settings(self):
        self.root.current = 'settings'
        