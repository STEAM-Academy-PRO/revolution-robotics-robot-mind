# SPDX-License-Identifier: GPL-3.0-only
from revvy.hardware_dependent.sound import SoundControlBase
from revvy.utils.logger import get_logger


class Sound:
    def __init__(self, sound_interface: SoundControlBase, sounds):
        self._sound = sound_interface

        self._get_sound_path = sounds
        self.set_volume = sound_interface.set_volume
        self.reset_volume = sound_interface.reset_volume

        self._log = get_logger('Sound')

    def play_tune(self, name, callback=None):
        try:
            self._sound.play_sound(self._get_sound_path(name), callback)
        except KeyError:
            self._log(f'Sound not found: {name}')
