import json
from pathlib import Path

from kivy.app import App
from kivy.uix.screenmanager import Screen

from kivy.clock import Clock
from kivy.logger import Logger


class SettingsView(Screen):

    def load_settings(self):
        settings_text = "{\n}"
        try:
            settings_data = json.loads(Path("config/settings.json").read_text())
            formatted_settings = json.dumps(settings_data, indent=4)
            settings_text = formatted_settings
        except:
            Logger.exception("Failed to load settings.")
        finally:
            Logger.info(settings_text)
            self.ids.settings_input.text = settings_text

    def on_enter(self, *args):
        Logger.info("SettingsView.on_enter")
        Clock.schedule_once(lambda _: self.load_settings())

    def save_settings(self):
        settings_text = self.ids.settings_input.text
        try:
            formatted_json = json.dumps(
                json.loads(settings_text),
                indent=4
            )
            Path("config/settings.json").write_text(formatted_json)
        except Exception:
            Logger.exception("Failed to save settings.")
        finally:
            App.get_running_app().root.current = 'mouse'
