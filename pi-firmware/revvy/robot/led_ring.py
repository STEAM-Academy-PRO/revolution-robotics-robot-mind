from revvy.mcu.rrrc_control import RevvyControl


class RingLed:
    Off = 0
    UserFrame = 1
    ColorWheel = 2
    ColorFade = 3
    BusyIndicator = 4
    BreathingGreen = 5
    Siren = 6
    TrafficLight = 7
    Bug = 8

    def __init__(self, interface: RevvyControl):
        self._interface = interface
        self._ring_led_count = self._interface.ring_led_get_led_amount()
        self._current_scenario = self.BreathingGreen

    @property
    def count(self) -> int:
        return self._ring_led_count

    @property
    def scenario(self) -> int:
        return self._current_scenario

    def start_animation(self, scenario: int):
        """
        Selects and starts a new animation scenario on the LED ring.
        """
        self._current_scenario = scenario
        self._interface.ring_led_set_scenario(scenario)

    def upload_user_frame(self, frame: list[int]):
        """
        Updates the MCU's LED ring buffer with a new frame. The frame is not displayed unless
        the UserFrame scenario is active.

        A frame is an array with 12 RGB color values encoded as integers.
        """
        self._interface.ring_led_set_user_frame(frame)

    def display_user_frame(self, frame: list[int]):
        """
        Uploads and displays a new frame on the LED ring.
        """
        self.upload_user_frame(frame)
        self.start_animation(self.UserFrame)
