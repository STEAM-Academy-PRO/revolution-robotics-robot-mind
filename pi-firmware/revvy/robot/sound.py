from functools import partial
import os
from threading import Thread, Event
from typing import Callable, Optional

from revvy.hardware_dependent.sound import SoundControlBase
from revvy.utils.assets import Assets
from revvy.utils.directories import WRITEABLE_DATA_DIR, WRITEABLE_ASSETS_DIR, PACKAGE_ASSETS_DIR
from revvy.utils.functions import read_json
from revvy.utils.logger import LogLevel, get_logger


class Sound:
    def __init__(self, sound_interface: SoundControlBase):
        self._sound = sound_interface
        self._playing: dict[int, tuple[Thread, Optional[Callable]]] = {}
        self._key = 0

        # Load sounds from the assets folder.
        self._assets = Assets()

        # Package sounds
        self._assets.add_source(PACKAGE_ASSETS_DIR)

        # Users can upload their own sounds in the writeable assets folder.
        self._assets.add_source(WRITEABLE_ASSETS_DIR)

        self._sounds = self._assets.category("sounds")
        self.set_volume = sound_interface.set_volume
        self.reset_volume = sound_interface.reset_volume

        self._log = get_logger("Sound")

        default_sound_config = {"default_volume": 100}

        try:
            sound_config = read_json(os.path.join(WRITEABLE_DATA_DIR, "config", "sound.json"))
        except Exception as e:
            self._log(f"Failed to load sound config: {e}. Using default.", LogLevel.WARNING)
            sound_config = {}

        # merge missing keys from default
        sound_config = {**default_sound_config, **sound_config}

        sound_interface.set_default_volume(sound_config["default_volume"])
        sound_interface.set_volume(sound_config["default_volume"])

    def play_tune(self, name: str, callback: Optional[Callable] = None) -> bool:
        """Play a tune with the given name. If a callback is given, it will be called when the tune finishes.

        Returns True if the tune was found and started, False otherwise (e.g. in case of too many
        parallel sound requests).
        """
        try:
            key, self._key = self._key, self._key + 1

            # TODO: we should return a less ad-hoc sound handle here. Working with the thread
            # and the finished callback directly is not ideal.
            player_thread = self._sound.play_sound(self._sounds[name], partial(self._finished, key))
            if player_thread:
                self._playing[key] = (player_thread, callback)
                return True
        except KeyError:
            self._log(f"Sound not found: {name}")
        return False

    def play_tune_blocking(self, name: str):
        """Play a tune and wait for it to finish."""
        finished = Event()
        if self.play_tune(name, finished.set):
            finished.wait()

    def _finished(self, key: int):
        callback = self._playing[key][1]
        del self._playing[key]

        if callback is not None:
            callback()

    def wait(self) -> None:
        playing = self._playing.copy()
        for play in playing.values():
            thread = play[0]
            thread.join()
