import os
from datetime import datetime
from typing import List


def list_directory_entries(path: str) -> List[dict]:
    if not os.path.isdir(path):
        return []

    entries: List[dict] = []
    try:
        with os.scandir(path) as scan:
            for entry in scan:
                name = entry.name
                if name.startswith("."):
                    continue
                is_dir = entry.is_dir(follow_symlinks=False)
                stat_info = entry.stat(follow_symlinks=False)
                entries.append(
                    {
                        "name": name,
                        "path": entry.path,
                        "is_dir": is_dir,
                        "size": 0 if is_dir else int(stat_info.st_size),
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    }
                )
    except Exception:
        return []

    entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
    return entries
