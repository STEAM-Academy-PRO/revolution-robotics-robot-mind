import os
import re
from revvy.utils.directories import CURRENT_INSTALLATION_PATH

from revvy.utils.functions import read_json
from revvy.utils import logger
from revvy.utils.logger import get_logger

version_re = re.compile(
    "(?P<major>\\d+?)\\.(?P<minor>\\d+?)(\\.(?P<rev>\\d+))?(-(?P<branch>.*?))?$"
)


class FormatError(Exception):
    pass


manifest = None


def read_manifest():
    global manifest
    manifest = read_json(os.path.join(CURRENT_INSTALLATION_PATH, "manifest.json"))


def get_branch():
    """Current manifest's branch"""
    global manifest
    if not manifest:
        read_manifest()
    return manifest["branch"]


def get_sw_version():
    """Returns Current Software version, uses manifest file to determine that."""
    global manifest
    if not manifest:
        read_manifest()
    return Version(manifest["version"])


class SystemVersions:
    """HW, SW, FW version store populated by the init updater."""

    def __init__(self):
        self.sw = None
        self.hw = None
        self.fw = None

    def set(self, sw, hw, fw):
        self.sw = sw
        self.hw = hw
        self.fw = fw

        logger.branch = get_branch()
        logger.sw_version = sw

        log = get_logger("Version info")
        log(f"hw: {hw} sw: {sw} fw: {fw}")

    def get(self):
        return {"hw": str(self.hw), "sw": str(self.sw), "fw": str(self.fw)}


VERSION = SystemVersions()


class Version:
    """Deals with version numbers"""

    def __init__(self, ver_str):
        """
        >>> Version('1.0.123')
        Version(1.0.123)
        >>> Version('1.0-foobar')
        Version(1.0.0-foobar)
        """
        match = version_re.match(ver_str)
        if not match:
            raise FormatError
        self.major = int(match.group("major"))
        self.minor = int(match.group("minor"))
        self.rev = int(match.group("rev")) if match.group("rev") else 0
        self.branch = match.group("branch") or "stable"
        if self.branch == "stable":
            self._normalized = f"{self.major}.{self.minor}.{self.rev}"
        else:
            self._normalized = f"{self.major}.{self.minor}.{self.rev}-{self.branch}"

    def __le__(self, other):
        """
        >>> Version('1.0.0') <= Version('1.0.0')
        True
        >>> Version('1.0.0') <= Version('1.0.1')
        True
        >>> Version('1.0.0') <= Version('1.1.0')
        True
        >>> Version('1.0.0') <= Version('2.0.0')
        True
        >>> Version('1.0.1') <= Version('1.0.0')
        False
        >>> Version('1.1.0') <= Version('1.0.0')
        False
        >>> Version('2.0.0') <= Version('1.0.0')
        False
        """
        return self.compare(other) != 1

    def __eq__(self, other):
        """
        >>> Version('1.0.0') == Version('1.0.0')
        True
        >>> Version('1.0.0') == Version('1.0.1')
        False
        >>> Version('1.0.0') == Version('1.1.0')
        False
        >>> Version('1.0.0') == Version('2.0.0')
        False
        >>> Version('1.0.0') == Version('1.0.0-dev')
        False
        """
        return self.compare(other) == 0 and self.branch == other.branch

    def __ne__(self, other):
        """
        >>> Version('1.0.0') != Version('1.0.0')
        False
        >>> Version('1.0.0') != Version('1.0.1')
        True
        >>> Version('1.0.0') != Version('1.1.0')
        True
        >>> Version('1.0.0') != Version('2.0.0')
        True
        >>> Version('1.0.0') != Version('1.0.0-dev')
        True
        """
        return not (self == other)

    def __lt__(self, other):
        """
        >>> Version('1.0.0') < Version('1.0.0')
        False
        >>> Version('1.0.0') < Version('1.0.1')
        True
        >>> Version('1.0.0') < Version('1.1.0')
        True
        >>> Version('1.0.0') < Version('2.0.0')
        True
        >>> Version('1.0.1') < Version('1.0.0')
        False
        >>> Version('1.1.0') < Version('1.0.0')
        False
        >>> Version('2.0.0') < Version('1.0.0')
        False
        """
        return self.compare(other) == -1

    def __gt__(self, other):
        """
        >>> Version('1.0.0') > Version('1.0.0')
        False
        >>> Version('1.0.0') > Version('1.0.1')
        False
        >>> Version('1.0.0') > Version('1.1.0')
        False
        >>> Version('1.0.0') > Version('2.0.0')
        False
        >>> Version('1.0.1') > Version('1.0.0')
        True
        >>> Version('1.1.0') > Version('1.0.0')
        True
        >>> Version('2.0.0') > Version('1.0.0')
        True
        """
        return self.compare(other) == 1

    def __ge__(self, other):
        """
        >>> Version('1.0.0') >= Version('1.0.0')
        True
        >>> Version('1.0.0') >= Version('1.0.1')
        False
        >>> Version('1.0.0') >= Version('1.1.0')
        False
        >>> Version('1.0.0') >= Version('2.0.0')
        False
        >>> Version('1.0.1') >= Version('1.0.0')
        True
        >>> Version('1.1.0') >= Version('1.0.0')
        True
        >>> Version('2.0.0') >= Version('1.0.0')
        True
        """
        return self.compare(other) != -1

    def compare(self, other: "Version"):
        """
        >>> Version('1.0.0').compare(Version('1.0.0'))
        0
        >>> Version('1.0.1').compare(Version('1.0.0'))
        1
        >>> Version('1.0.0').compare(Version('1.0.1'))
        -1
        """

        def cmp(a, b):
            return -1 if a < b else 1

        if self.major == other.major:
            if self.minor == other.minor:
                if self.rev == other.rev:
                    return 0
                else:
                    return cmp(self.rev, other.rev)
            else:
                return cmp(self.minor, other.minor)
        else:
            return cmp(self.major, other.major)

    def __str__(self) -> str:
        """
        >>> str(Version('1.0'))
        '1.0.0'
        >>> str(Version('1.0-dev'))
        '1.0.0-dev'
        """
        return self._normalized

    def __repr__(self):
        return "Version({})".format(self._normalized)

    def __hash__(self) -> int:
        return self._normalized.__hash__()
