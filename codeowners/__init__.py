"""
Python port of https://github.com/softprops/codeowners
"""
import re
from pathlib import PurePath
from typing import List, Optional, Pattern, Tuple

from typing_extensions import Literal

__all__ = ["CodeOwners"]

OwnerTuple = Tuple[Literal["USERNAME", "TEAM", "EMAIL"], str]


TEAM = re.compile(r"^@\S+/\S+")
USERNAME = re.compile(r"^@\S+")
EMAIL = re.compile(r"^\S+@\S+")


def path_to_regex(path: str) -> Pattern[str]:
    if path == "*":
        return re.compile(".*")

    if path.endswith("/"):
        end = ".*$"
    elif path.endswith("*"):
        path = path.rstrip("*")
        end = "[^/]*"
    else:
        end = "$"

    if path.startswith("/"):
        path = path.lstrip("/")
        start = "^/?"
    elif path.startswith("*"):
        path = path.lstrip("*")
        start = ".*"
    else:
        start = ".*/?"

    return re.compile(start + re.escape(path) + end)


def parse_owner(owner: str) -> Optional[OwnerTuple]:
    if TEAM.match(owner):
        return ("TEAM", owner)
    if USERNAME.match(owner):
        return ("USERNAME", owner)
    if EMAIL.match(owner):
        return ("EMAIL", owner)
    return None


def pattern_matches(path: str, pattern: Pattern[str]) -> bool:
    match = pattern.match(path)
    # The regex we compile from the paths are required to match competely for
    # the match to count.
    return match is not None and match.span() == (0, len(path))


class CodeOwners:
    def __init__(self, text: str) -> None:
        paths: List[Tuple[Pattern[str], str, List[OwnerTuple]]] = []
        for line in text.splitlines():
            if line != "" and not line.startswith("#"):
                elements = iter(line.split())
                path = next(elements, None)
                if path is not None:
                    owners: List[OwnerTuple] = []
                    for owner in elements:
                        owner_res = parse_owner(owner)
                        if owner_res is not None:
                            owners.append(owner_res)
                    paths.append((path_to_regex(path), path, owners))
        paths.reverse()
        self.paths = paths

    def of(self, filepath: str) -> List[OwnerTuple]:
        for pattern, path, owners in self.paths:
            if pattern_matches(filepath, pattern):
                return owners
            else:
                if path.endswith("/*"):
                    continue
                p = PurePath(filepath)
                while True:
                    parent = p.parent
                    if parent == PurePath("/") or parent == PurePath("."):
                        break
                    if pattern_matches(str(parent), pattern):
                        return owners
                    else:
                        p = parent
        return []
