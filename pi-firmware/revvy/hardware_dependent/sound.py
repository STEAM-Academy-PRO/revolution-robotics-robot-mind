import abc
import subprocess
from threading import Thread, Lock
from typing import Callable, Optional

from revvy.utils.functions import clip
from revvy.utils.logger import get_logger


class SoundControlBase(abc.ABC):
    def __init__(self, default_volume: int = 100):
        self._default_volume = default_volume
        self._lock = Lock()
        self._processes = []
        self._max_parallel_sounds = 4
        self._log = get_logger("SoundControl")

        self._init_amp()

    @abc.abstractmethod
    def _init_amp(self) -> None: ...

    @abc.abstractmethod
    def _disable_amp(self) -> None: ...

    @abc.abstractmethod
    def _play_sound(self, sound: str, cb: Callable) -> Thread: ...

    def _run_command(self, command: list[str]) -> subprocess.Popen:
        return subprocess.Popen(
            args=command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

    def _run_command_with_callback(self, commands: list[list[str]], callback) -> Thread:
        def run_in_thread(commands: list[list[str]]) -> None:
            for command in commands:
                process = self._run_command(command)
                with self._lock:
                    self._processes.append(process)

                process.wait()

                with self._lock:
                    self._processes.remove(process)

            if callback:
                callback()

        thread = Thread(target=run_in_thread, args=(commands,))
        thread.start()

        return thread

    def _disable_amp_callback(self) -> None:
        # self._log('Disable amp callback')
        with self._lock:
            # self._log(f"Sounds playing: {len(self._processes)}")
            if not self._processes:
                # self._log('Turning amp off')
                self._disable_amp()

    def set_default_volume(self, volume: int):
        self._default_volume = volume

    def set_volume(self, volume: int):
        self._log(f"Setting volume to {volume}")
        volume = clip(volume, 0, 100)
        self._run_command(["amixer", "sset", "PCM", f"{volume}%"])

    def reset_volume(self) -> None:
        self.set_volume(self._default_volume)

    def play_sound(self, sound: str, callback: Optional[Callable] = None):
        if len(self._processes) <= self._max_parallel_sounds:
            self._log(f"Playing sound: {sound}")

            def cb() -> None:
                if callback:
                    callback()

                self._disable_amp_callback()

            return self._play_sound(sound, cb)
        else:
            self._log("Too many sounds are playing, skip")


class SoundControlV1(SoundControlBase):
    def _init_amp(self) -> None:
        self._run_command(["gpio", "-g", "mode", "13", "alt0"]).wait()
        self._run_command(["gpio", "-g", "mode", "22", "out"]).wait()

    def _play_sound(self, sound: str, cb: Callable) -> Thread:
        return self._run_command_with_callback([["gpio", "write", "3", "1"], ["mpg123", sound]], cb)

    def _disable_amp(self) -> None:
        self._run_command(["gpio", "write", "3", "0"]).wait()


class SoundControlV2(SoundControlBase):
    def _init_amp(self) -> None:
        self._run_command(["gpio", "-g", "mode", "13", "alt0"]).wait()
        self._run_command(["gpio", "-g", "mode", "22", "out"]).wait()
        self._run_command(["gpio", "write", "3", "1"]).wait()

    def _play_sound(self, sound: str, cb: Callable) -> Thread:
        return self._run_command_with_callback([["gpio", "write", "3", "0"], ["mpg123", sound]], cb)

    def _disable_amp(self) -> None:
        self._run_command(["gpio", "write", "3", "1"]).wait()
