# SPDX-License-Identifier: GPL-3.0-only


class Sound:
    def __init__(self, setup, play, sounds):
        setup()

        self._play = play
        self._get_sound_path = sounds

    def play_tune(self, name):
        try:
            self._play(self._get_sound_path(name))
        except KeyError:
            print('Sound not found: {}'.format(name))
