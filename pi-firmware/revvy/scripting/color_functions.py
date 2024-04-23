from revvy.utils.logger import get_logger


log = get_logger("ColorSensorFunctions")


class ColorData:
    # FIXME: this seems incredibly redundant, we shouldn't need 2 color spaces
    def __init__(self, r: int, g: int, b: int, h: int, s: int, v: int, gray: int, name: str):
        self.red = r
        self.green = g
        self.blue = b
        self.hue = h
        self.saturation = s
        self.value = v
        self.gray = gray
        self.name = name


ColorDataUndefined = ColorData(r=0, g=0, b=0, h=0, s=0, v=0, gray=0, name="undefined")


color_name_map = {
    "red": 0xFF0000,
    "yellow": 0xFFFF00,
    "green": 0x00FF00,
    "cyan": 0x00FFFF,
    "blue": 0x0000FF,
    "magenta": 0xFF00FF,
    "black": 0x000000,
    "gray": 0x7F7F7F,
    "white": 0xFFFFFF,
}


def color_name_to_rgb(color_name: str):
    try:
        return color_name_map[color_name]
    except KeyError:
        return None


def hsv_to_color_name(hue, saturation, value) -> str:
    # hue - color component, in range 0-360 (deg)
    # saturation - from gray to colored, in range 0-100 (%)
    # value - from black to full color, in range 0-100 (%)

    # If not saturated we go for one of the gray colors
    if saturation < 14:
        if value <= 50:
            return "black"
        if value <= 75:
            return "gray"
        return "white"

    # If color is saturated, but value is close to black, select black,
    # without selecting from one of gray colors
    if value < 30:
        return "black"

    # These 6 color names are evenly distrubuted across a color circle
    # 360 / 6 - gives 60 degrees range for each of the color
    # 100% red is 0 as well as 360, 100% yellow is 60, green is 120, etc
    names = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    num_steps = len(names)
    step = int(360 / num_steps)

    # We start from 'red' instead of checking all the time if value is
    # more than 360 - 60/2
    for i in range(num_steps):
        cmp_color = step * (i + 0.5)
        if hue < cmp_color:
            return names[i]

    # max cmp_color is 330 (5.5 * 60), if loop is completed, value is
    # in range [330, 360]
    return names[0]


def rgb_to_hsv_gray(red, green, blue) -> ColorData:
    r, g, b = red / 255.0, green / 255.0, blue / 255.0
    gray = 0.299 * red + 0.587 * green + 0.114 * blue
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    h = 1.0

    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100
    v = mx * 100
    h = round(h)
    s = round(s)
    v = round(v)
    gray = round(gray)
    name = hsv_to_color_name(h, s, v)
    return ColorData(red, green, blue, h, s, v, gray, name)


def detect_line_background_colors(
    sensors_data: list[ColorData],
) -> tuple[int, int, str, str, int, list[int], list[str]]:  # WTF
    channels = [[], [], []]  # [H] [S] [V]
    gray = []
    name = []
    rgb_val = []
    # print(sensors)
    for color_data in sensors_data:
        channels[0].append(color_data.hue)
        channels[1].append(color_data.saturation)
        channels[2].append(color_data.value)
        gray.append(color_data.gray)
        name.append(color_data.name)
        rgb = (color_data.red, color_data.green, color_data.blue)
        rgb_val.append(rgb)
    # print(res)
    delta = []  # searching of most signed from H S V
    for color_channel_samples in channels:
        delta.append(max(color_channel_samples) - min(color_channel_samples))
    i = delta.index(max(delta))
    """next commented  is for using most heavy from H,S,V"""
    # maximum = max(res[i])
    # minimum = min(res[i])
    # background = minimum
    # line = maximum
    # if res[i].index(maximum) in (1, 2):   # then the value of background color is max and line is min
    #     background = maximum
    #     line = minimum
    # print(i, res[i], )
    """gray color using at the time of following is most effective,
       in this case we use HSV just for make decision which way be the next"""
    maxi = max(gray)
    mini = min(gray)
    background = mini
    line = maxi
    if gray.index(maxi) in (1, 2):
        background = maxi
        line = mini
    background_name = name[gray.index(background)]
    line_name = name[gray.index(line)]

    return line, background, line_name, background_name, i, gray, name


def search_lr(colors: tuple, color="", side=""):
    """this function should search color where we change direction
    when founded we stop current line follower and go to the next step"""
    if color == "" or side == "":
        log("color or side aren't sat")

        return False
    forward, left, right, center = colors
    if side == "left":
        if left == color:
            log(f"\n\nchannel 2 is {color} at {side}\n\n")
            return True
    elif side == "right":
        if right == color:
            log(f"\n\nchannel 3 is {color} at {side}\n\n")
            return True
