from functools import partial
import json
import os

from revvy.hardware_dependent.sound import SoundControlBase
from revvy.utils.assets import Assets
from revvy.utils.directories import WRITEABLE_DATA_DIR, WRITEABLE_ASSETS_DIR
from revvy.utils.functions import read_json
from revvy.utils.logger import LogLevel, get_logger


class Sound:
    def __init__(self, sound_interface: SoundControlBase):
        self._sound = sound_interface
        self._playing = {}
        self._key = 0

        # Load sounds from the assets folder.
        self._assets = Assets()

        # Package sounds
        self._assets.add_source(os.path.join("data", "assets"))

        # Users can upload their own sounds in the writeable assets folder.
        self._assets.add_source(WRITEABLE_ASSETS_DIR)

        self._get_sound_path = self._assets.category_loader("sounds")
        self.set_volume = sound_interface.set_volume
        self.reset_volume = sound_interface.reset_volume

        self._log = get_logger("Sound")

        default_sound_config = {"default_volume": 90}

        try:
            sound_config = read_json(os.path.join(WRITEABLE_DATA_DIR, "config", "sound.json"))
        except Exception as e:
            self._log(f"Failed to load sound config: {e}. Using default.", LogLevel.WARNING)
            sound_config = {}

        # merge missing keys from default
        sound_config = {**default_sound_config, **sound_config}

        sound_interface.set_default_volume(sound_config["default_volume"])
        sound_interface.set_volume(sound_config["default_volume"])

    def play_tune(self, name, callback=None):
        try:
            key, self._key = self._key, self._key + 1
            player_thread = self._sound.play_sound(
                self._get_sound_path(name), partial(self._finished, key)
            )
            if player_thread:
                self._playing[key] = (player_thread, callback)
        except KeyError:
            self._log(f"Sound not found: {name}")

    def _finished(self, key):
        callback = self._playing[key][1]
        del self._playing[key]

        if callback:
            callback()

    def wait(self):
        playing = self._playing.copy()
        for play in playing.values():
            thread = play[0]
            thread.join()
