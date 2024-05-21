import os
import traceback
from collections import defaultdict

from revvy.utils.functions import read_json
from revvy.utils.logger import get_logger, LogLevel


class Assets:
    def __init__(self):
        self._log = get_logger("Assets")
        self._files = defaultdict(dict)

    def add_source(self, path: str):
        """
        Add a new folder to the asset sources

        @param path: the asset folder with an assets.json file inside
        """
        assets_json = os.path.join(path, "assets.json")
        try:
            manifest = read_json(assets_json)
            self._log(f"Loading assets from {path}")
            files: dict[str, dict[str, str]] = manifest["files"]
            for category, assets in files.items():
                for asset_name, asset_path in assets.items():
                    if asset_name in self._files[category]:
                        self._log(f"{path} shadows asset {asset_name}")

                    # self._log(f'New asset: ({category}) {asset_name}', LogLevel.DEBUG)
                    self._files[category][asset_name] = os.path.join(path, asset_path)
        except FileNotFoundError:
            self._log(f"Asset source does not exist: {path}", LogLevel.WARNING)
        except Exception:
            self._log(f"Skip loading assets from {path} due to unexpected error", LogLevel.WARNING)
            self._log(traceback.format_exc(), LogLevel.DEBUG)

    def category(self, category: str) -> dict[str, str]:
        return self._files[category]
