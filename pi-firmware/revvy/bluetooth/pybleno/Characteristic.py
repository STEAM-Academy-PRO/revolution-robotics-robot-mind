from typing import Any
from .hci_socket.Emit import Emit
from . import UuidUtil


class Characteristic(Emit):
    RESULT_SUCCESS = 0x00
    RESULT_INVALID_OFFSET = 0x07
    RESULT_ATTR_NOT_LONG = 0x0B
    RESULT_INVALID_ATTRIBUTE_LENGTH = 0x0D
    RESULT_UNLIKELY_ERROR = 0x0E

    def __init__(self, options: dict[str, Any] = {}) -> None:
        super().__init__()
        self._dict = {}

        self["uuid"] = UuidUtil.removeDashes(options["uuid"])
        self["properties"] = options.get("properties", [])
        self["secure"] = options.get("secure", [])
        self["value"] = options.get("value", None)
        self["descriptors"] = options.get("descriptors", [])

        self.maxValueSize = None
        self.updateValueCallback = None

        if self["value"] and (len(self["properties"]) != 1 or self["properties"][0] != "read"):
            raise Exception("Characteristics with value can be read only!")

        self.on("readRequest", self.onReadRequest)
        self.on("writeRequest", self.onWriteRequest)
        self.on("subscribe", self.onSubscribe)
        self.on("unsubscribe", self.onUnsubscribe)
        self.on("notify", self.onNotify)
        self.on("indicate", self.onIndicate)

    def onReadRequest(self, offset, callback) -> None:
        callback(self.RESULT_UNLIKELY_ERROR, None)

    def onWriteRequest(self, data, offset, withoutResponse, callback) -> None:
        callback(self.RESULT_UNLIKELY_ERROR)

    def onSubscribe(self, maxValueSize, updateValueCallback) -> None:
        self.maxValueSize = maxValueSize
        self.updateValueCallback = updateValueCallback

    def onUnsubscribe(self) -> None:
        self.maxValueSize = None
        self.updateValueCallback = None

    def onNotify(self) -> None:
        pass

    def onIndicate(self) -> None:
        pass

    def __setitem__(self, key, item) -> None:
        self._dict[key] = item

    def __getitem__(self, key):
        return self._dict[key]

    def __repr__(self):
        return repr(self._dict)

    def __len__(self):
        return len(self._dict)

    def __delitem__(self, key) -> None:
        del self._dict[key]

    def clear(self):
        return self._dict.clear()

    def copy(self):
        return self._dict.copy()

    def has_key(self, k):
        return k in self._dict

    def update(self, *args, **kwargs):
        return self._dict.update(*args, **kwargs)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def pop(self, *args):
        return self._dict.pop(*args)

    def __cmp__(self, dict_):
        return self._dict.__cmp__(dict_)

    def __contains__(self, item):
        return item in self._dict

    def __iter__(self):
        return iter(self._dict)

    def __unicode__(self):
        return unicode(repr(self._dict))
