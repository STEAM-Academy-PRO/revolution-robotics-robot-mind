import os
import re
from revvy.utils.directories import CURRENT_INSTALLATION_PATH

from revvy.utils.functions import read_json

version_re = re.compile('(?P<major>\\d+?)\\.(?P<minor>\\d+?)(\\.(?P<rev>\\d+))?(-(?P<branch>.*?))?$')

class FormatError(Exception):
    pass

manifest = None

def read_manifest():
    global manifest
    manifest = read_json(os.path.join(CURRENT_INSTALLATION_PATH,'manifest.json'))

def get_branch():
    """ Current manifest's branch """
    global manifest
    if not manifest: read_manifest()
    return manifest['branch']

def get_sw_version():
    """ Returns Current Software version, uses manifest file to determine that. """
    global manifest
    if not manifest: read_manifest()
    return SoftwareVersion(manifest['version'])


class Version:
    """ HW, SW, FW versio store populated by the init updater. """
    def __init__(self):
        self.sw = None
        self.hw = None
        self.fw = None
    def set(self, sw, hw, fw):
        self.sw = sw
        self.hw = hw
        self.fw = fw

VERSION = Version()

class SoftwareVersion:
    def __init__(self, ver_str):
        """
        >>> SoftwareVersion('1.0.123')
        Version(1.0.123)
        >>> SoftwareVersion('1.0-foobar')
        Version(1.0.0-foobar)
        """
        match = version_re.match(ver_str)
        if not match:
            raise FormatError
        self._major = int(match.group('major'))
        self._minor = int(match.group('minor'))
        self._rev = int(match.group('rev')) if match.group('rev') else 0
        self._branch = match.group('branch') or 'stable'
        if self._branch == 'stable':
            self._normalized = f'{self._major}.{self._minor}.{self._rev}'
        else:
            self._normalized = f'{self._major}.{self._minor}.{self._rev}-{self._branch}'

    @property
    def major(self):
        """
        >>> SoftwareVersion('2.3').major
        2
        """
        return self._major

    @property
    def minor(self):
        """
        >>> SoftwareVersion('2.3').minor
        3
        """
        return self._minor

    @property
    def revision(self):
        """
        >>> SoftwareVersion('2.3.45').revision
        45
        """
        return self._rev

    @property
    def branch(self):
        """
        >>> SoftwareVersion('2.3-foobranch').branch
        'foobranch'
        """
        return self._branch

    def __le__(self, other):
        """
        >>> SoftwareVersion('1.0.0') <= SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('1.0.0') <= SoftwareVersion('1.0.1')
        True
        >>> SoftwareVersion('1.0.0') <= SoftwareVersion('1.1.0')
        True
        >>> SoftwareVersion('1.0.0') <= SoftwareVersion('2.0.0')
        True
        >>> SoftwareVersion('1.0.1') <= SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('1.1.0') <= SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('2.0.0') <= SoftwareVersion('1.0.0')
        False
        """
        return self.compare(other) != 1

    def __eq__(self, other):
        """
        >>> SoftwareVersion('1.0.0') == SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('1.0.0') == SoftwareVersion('1.0.1')
        False
        >>> SoftwareVersion('1.0.0') == SoftwareVersion('1.1.0')
        False
        >>> SoftwareVersion('1.0.0') == SoftwareVersion('2.0.0')
        False
        >>> SoftwareVersion('1.0.0') == SoftwareVersion('1.0.0-dev')
        False
        """
        return self.compare(other) == 0 and self.branch == other.branch

    def __ne__(self, other):
        """
        >>> SoftwareVersion('1.0.0') != SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('1.0.0') != SoftwareVersion('1.0.1')
        True
        >>> SoftwareVersion('1.0.0') != SoftwareVersion('1.1.0')
        True
        >>> SoftwareVersion('1.0.0') != SoftwareVersion('2.0.0')
        True
        >>> SoftwareVersion('1.0.0') != SoftwareVersion('1.0.0-dev')
        True
        """
        return not (self == other)

    def __lt__(self, other):
        """
        >>> SoftwareVersion('1.0.0') < SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('1.0.0') < SoftwareVersion('1.0.1')
        True
        >>> SoftwareVersion('1.0.0') < SoftwareVersion('1.1.0')
        True
        >>> SoftwareVersion('1.0.0') < SoftwareVersion('2.0.0')
        True
        >>> SoftwareVersion('1.0.1') < SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('1.1.0') < SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('2.0.0') < SoftwareVersion('1.0.0')
        False
        """
        return self.compare(other) == -1

    def __gt__(self, other):
        """
        >>> SoftwareVersion('1.0.0') > SoftwareVersion('1.0.0')
        False
        >>> SoftwareVersion('1.0.0') > SoftwareVersion('1.0.1')
        False
        >>> SoftwareVersion('1.0.0') > SoftwareVersion('1.1.0')
        False
        >>> SoftwareVersion('1.0.0') > SoftwareVersion('2.0.0')
        False
        >>> SoftwareVersion('1.0.1') > SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('1.1.0') > SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('2.0.0') > SoftwareVersion('1.0.0')
        True
        """
        return self.compare(other) == 1

    def __ge__(self, other):
        """
        >>> SoftwareVersion('1.0.0') >= SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('1.0.0') >= SoftwareVersion('1.0.1')
        False
        >>> SoftwareVersion('1.0.0') >= SoftwareVersion('1.1.0')
        False
        >>> SoftwareVersion('1.0.0') >= SoftwareVersion('2.0.0')
        False
        >>> SoftwareVersion('1.0.1') >= SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('1.1.0') >= SoftwareVersion('1.0.0')
        True
        >>> SoftwareVersion('2.0.0') >= SoftwareVersion('1.0.0')
        True
        """
        return self.compare(other) != -1

    # noinspection PyProtectedMember
    def compare(self, other):
        """
        >>> SoftwareVersion('1.0.0').compare(SoftwareVersion('1.0.0'))
        0
        >>> SoftwareVersion('1.0.1').compare(SoftwareVersion('1.0.0'))
        1
        >>> SoftwareVersion('1.0.0').compare(SoftwareVersion('1.0.1'))
        -1
        """

        def cmp(a, b):
            return -1 if a < b else 1

        if self._major == other._major:
            if self._minor == other._minor:
                if self._rev == other._rev:
                    return 0
                else:
                    return cmp(self._rev, other._rev)
            else:
                return cmp(self._minor, other._minor)
        else:
            return cmp(self._major, other._major)

    def __str__(self) -> str:
        """
        >>> str(SoftwareVersion('1.0'))
        '1.0.0'
        >>> str(SoftwareVersion('1.0-dev'))
        '1.0.0-dev'
        """
        return self._normalized

    def __repr__(self):
        return 'Version({})'.format(self._normalized)

    def __hash__(self) -> int:
        return self._normalized.__hash__()
