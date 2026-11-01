import re
from typing import Generator, List, Literal, Optional, Pattern, Tuple

__all__ = ["CodeOwners"]

OwnerTuple = Tuple[Literal["USERNAME", "TEAM", "EMAIL"], str]


TEAM = re.compile(r"^@\S+/\S+")
USERNAME = re.compile(r"^@\S+")
EMAIL = re.compile(r"^\S+@\S+")


def _negated_name(pattern: str) -> Optional[str]:
    """
    For a `!` pattern without a slash, the rest of the pattern. GitHub
    doesn't negate these, but matches file names like the rest would, and not
    directories. With a slash, `!` is an ordinary character.
    """
    if pattern.startswith("!") and "/" not in pattern:
        return pattern[1:]
    return None


def _is_dir_only(pattern: str) -> bool:
    """
    Whether a pattern only matches directories: it ends in `/`, but not
    `/**/`, which GitHub matches like `/**`.
    """
    trimmed = pattern.rstrip("/")
    return pattern.endswith("/") and trimmed != "**" and not trimmed.endswith("/**")


def _is_invalid(pattern: str) -> bool:
    """
    Whether GitHub rejects `pattern` and skips its line: `[` and `]` must be
    escaped, `\\` can only escape a space, tab, `#`, `[`, `]` or `\\`, and
    there can't be more than two `*`s in a row.
    """
    chars = iter(pattern)
    for c in chars:
        if c == "\\":
            if next(chars, None) not in (" ", "\t", "#", "[", "]", "\\"):
                return True
        elif c in "[]":
            return True
    return "***" in pattern


def _brackets_pair_up(pattern: str) -> bool:
    """
    Whether there are as many `\\[`s as `\\]`s, in any order. GitHub matches
    nothing otherwise.
    """
    balance = 0
    chars = iter(pattern)
    for c in chars:
        if c == "\\":
            escaped = next(chars, None)
            if escaped == "[":
                balance += 1
            elif escaped == "]":
                balance -= 1
    return balance == 0


def _can_match(pattern: str) -> bool:
    """
    Whether `pattern` can match a path. GitHub rejects some patterns, and
    accepts a few that never match.
    """
    if _is_invalid(pattern):
        return False
    name = _negated_name(pattern)
    if name is not None:
        pattern = name
    return (
        pattern.strip("/") != ""
        and _brackets_pair_up(pattern)
        and not (pattern.startswith("\\[") and "/" not in pattern)
    )


def _literal(c: str) -> str:
    if c.isascii():
        return re.escape(c)
    # Paths are matched as UTF-8 bytes, so match the character's encoding.
    return "".join(f"\\x{b:02x}" for b in c.encode())


def _segment_regex(segment: str, raw_brackets: bool) -> str:
    """
    The regex for one path segment. With `raw_brackets`, `\\[` and `\\]`
    match a backslash and a bracket.
    """
    # A segment of only `*`s names something, so it can't be empty.
    if set(segment) == {"*"}:
        return "[^/]+"
    regex = ""
    chars = iter(segment)
    for c in chars:
        if c == "*":
            regex += "[^/]*"
        elif c == "?":
            # One byte, even of a multibyte character, like on GitHub.
            regex += "[^/]"
        elif c == "\\":
            escaped = next(chars, None)
            if escaped is not None:
                if raw_brackets and escaped in "[]":
                    regex += _literal("\\")
                regex += _literal(escaped)
        else:
            regex += _literal(c)
    return regex


def _pattern_regex(pattern: str, files_only: bool, raw_brackets: bool) -> str:
    """
    The regex for `pattern`, which matches a file path, or a directory path
    with a trailing slash. With `files_only`, it doesn't match directories.
    """
    dir_only = _is_dir_only(pattern)
    trimmed = pattern[:-1] if pattern.endswith("/") else pattern
    anchored = "/" in trimmed
    trimmed = trimmed[1:] if trimmed.startswith("/") else trimmed
    regex = r"\A" if anchored else r"\A(?:.*/)?"
    segments = trimmed.split("/")
    for i, segment in enumerate(segments):
        last = i == len(segments) - 1
        if segment == "**":
            # A trailing `/**` matches everything inside, and a leading or
            # middle `**/` zero or more directories.
            if last:
                return regex + (r".+/\Z" if dir_only else ".+")
            regex += "(?:.*/)?"
            continue
        regex += _segment_regex(segment, raw_brackets)
        if not last:
            regex += "/"
    if dir_only:
        return regex + r"/\Z"
    if files_only or pattern.endswith("/*"):
        # GitHub doesn't match nested files for rules ending in `/*`.
        return regex + r"\Z"
    # The path, or a directory containing it.
    return regex + r"/?\Z"


def path_to_regex(pattern: str) -> Optional[Pattern[bytes]]:
    """
    A regex for `pattern` that matches like GitHub, or None if GitHub never
    matches it. It matches a UTF-8 encoded file path, or a directory path with
    a trailing slash.

    GitHub matches by gitignore rules, except that there are no character
    classes, `\\` only escapes a few characters, `!` doesn't negate, `?`
    matches one byte, and a pattern ending in `/*` doesn't match nested files.
    """
    if not _can_match(pattern):
        return None
    name = _negated_name(pattern)
    if name is not None:
        pattern = name
    regex = _pattern_regex(pattern, name is not None, raw_brackets=False)
    # GitHub matches escaped brackets either unescaped or with their
    # backslashes, but not a mix of the two.
    if "\\[" in pattern:
        raw = _pattern_regex(pattern, name is not None, raw_brackets=True)
        regex = f"(?:{regex})|(?:{raw})"
    return re.compile(regex.encode(), re.DOTALL)


def _split_words(line: str) -> List[str]:
    """
    Split on whitespace, up to a comment. Like on GitHub, an unescaped `#`
    starts a comment anywhere, even inside a pattern, and an escaped space is
    part of a pattern.
    """
    words = []
    word = ""
    chars = iter(line)
    for c in chars:
        if c == "\\":
            word += c + next(chars, "")
        elif c == "#":
            break
        elif c.isspace():
            if word:
                words.append(word)
            word = ""
        else:
            word += c
    if word:
        words.append(word)
    return words


def _candidates(filepath: str) -> List[bytes]:
    """
    The path, and each directory containing it, with a trailing slash.
    """
    path = filepath.encode("utf-8", "surrogateescape")
    dirs = [path[: i + 1] for i, b in enumerate(path[:-1]) if b == ord("/")]
    return [*dirs, path]


def parse_owner(owner: str) -> Optional[OwnerTuple]:
    if TEAM.match(owner):
        return ("TEAM", owner)
    if USERNAME.match(owner):
        return ("USERNAME", owner)
    if EMAIL.match(owner):
        return ("EMAIL", owner)
    return None


class CodeOwners:
    def __init__(self, text: str) -> None:
        section_name = None

        paths: List[
            Tuple[Pattern[bytes], str, List[OwnerTuple], int, Optional[str]]
        ] = []
        for line_num, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            # Track the GitLab section name (if used)
            # https://docs.gitlab.com/ee/user/project/code_owners.html#code-owners-sections
            elif line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1]
                continue
            elif line.startswith("^[") and line.endswith("]"):
                section_name = line[2:-1]
                continue

            words = _split_words(line)
            if not words:
                continue
            path, *owner_words = words
            regex = path_to_regex(path)
            # Skip lines GitHub rejects, and patterns it never matches.
            if regex is None:
                continue
            owners: List[OwnerTuple] = []
            for owner in owner_words:
                owner_res = parse_owner(owner)
                if owner_res is not None:
                    owners.append(owner_res)
            paths.append((regex, path, owners, line_num, section_name))
        paths.reverse()
        self.paths = paths

    def matching_lines(
        self, filepath: str
    ) -> Generator[
        Tuple[List[OwnerTuple], Optional[int], Optional[str], Optional[str]], None, None
    ]:
        candidates = _candidates(filepath)
        for pattern, path, owners, line_num, section_name in self.paths:
            if any(pattern.match(candidate) for candidate in candidates):
                yield (owners, line_num, path, section_name)

    def matching_line(
        self, filepath: str
    ) -> Tuple[List[OwnerTuple], Optional[int], Optional[str], Optional[str]]:
        return next(self.matching_lines(filepath), ([], None, None, None))

    def section_name(self, filepath: str) -> Optional[str]:
        """
        Find the section name of the specified file path.

        None is returned when no matching section information
        was found (or sections are not used in the CODEOWNERS file)
        """
        return self.matching_line(filepath)[3]

    def of(self, filepath: str) -> List[OwnerTuple]:
        return self.matching_line(filepath)[0]
