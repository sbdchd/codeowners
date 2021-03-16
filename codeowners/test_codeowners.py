import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Tuple

import pytest
from typing_extensions import Literal

from codeowners import CodeOwners

# via https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners#codeowners-syntax
EXAMPLE = """# This is a comment.
# Each line is a file pattern followed by one or more owners.

# These owners will be the default owners for everything in
# the repo. Unless a later match takes precedence,
# @global-owner1 and @global-owner2 will be requested for
# review when someone opens a pull request.
*       @global-owner1 @global-owner2

# Order is important; the last matching pattern takes the most
# precedence. When someone opens a pull request that only
# modifies JS files, only @js-owner and not the global
# owner(s) will be requested for a review.
*.js    @js-owner

# You can also use email addresses if you prefer. They'll be
# used to look up users just like we do for commit author
# emails.
*.go docs@example.com

# In this example, @doctocat owns any files in the build/logs
# directory at the root of the repository and any of its
# subdirectories.
/build/logs/ @doctocat

# The `docs/*` pattern will match files like
# `docs/getting-started.md` but not further nested files like
# `docs/build-app/troubleshooting.md`.
docs/*  docs@example.com

# Let's test GitLab's premium feature of sections
# see https://docs.gitlab.com/ee/user/project/code_owners.html#code-owners-sections
[First team]

[Another team trailing whitespace] 

# In this example, @octocat owns any file in an apps directory
# anywhere in your repository.
apps/ @octocat

# Now, optional approval rule for GitLab's sections
^[Second team]

^[Second team trailing whitespace]   

# In this example, @doctocat owns any file in the `/docs`
# directory in the root of your repository.
/docs/ @doctocat
"""


@pytest.mark.parametrize(
    "path,expected",
    [
        (
            "buzz/docs/gettingstarted.md",
            [("USERNAME", "@global-owner1"), ("USERNAME", "@global-owner2")],
        ),
        ("docs/build-app/troubleshooting.md", [("USERNAME", "@doctocat")]),
        (
            "buzz/docs/build-app/troubleshooting.md",
            [("USERNAME", "@global-owner1"), ("USERNAME", "@global-owner2")],
        ),
        ("docs/", [("USERNAME", "@doctocat")]),
        ("foo.txt", [("USERNAME", "@global-owner1"), ("USERNAME", "@global-owner2")]),
        (
            "foo/bar.txt",
            [("USERNAME", "@global-owner1"), ("USERNAME", "@global-owner2")],
        ),
        ("foo.js", [("USERNAME", "@js-owner")]),
        ("foo/bar.js", [("USERNAME", "@js-owner")]),
        ("foo.go", [("EMAIL", "docs@example.com")]),
        ("foo/bar.go", [("EMAIL", "docs@example.com")]),
        ("build/logs/foo.go", [("USERNAME", "@doctocat")]),
        ("build/logs/foo/bar.go", [("USERNAME", "@doctocat")]),
        ("foo/build/logs/foo.go", [("EMAIL", "docs@example.com")]),
        ("foo/docs/foo.js", [("USERNAME", "@js-owner")]),
        ("foo/bar/docs/foo.js", [("USERNAME", "@js-owner")]),
        ("foo/bar/docs/foo/foo.js", [("USERNAME", "@js-owner")]),
        ("foo/apps/foo.js", [("USERNAME", "@octocat")]),
        ("foo/apps/bar/buzz/foo.js", [("USERNAME", "@octocat")]),
        ("docs/foo.js", [("USERNAME", "@doctocat")]),
    ],
)
def test_github_example_matches(
    path: str, expected: List[Tuple[Literal["USERNAME", "EMAIL", "TEAM"], str]]
) -> None:
    owners = CodeOwners(EXAMPLE)
    actual = owners.of(path)
    assert (
        actual == expected
    ), f"mismatch for {path}, expected: {expected}, got: {actual}"


def test_rule_missing_owner() -> None:
    assert CodeOwners("*.js").of("bar.js") == []


class ex(NamedTuple):
    name: str
    pattern: str
    paths: Dict[str, bool]


# Taken from: https://github.com/hmarr/codeowners/blob/d0452091447bd2a29ee508eebc5a79874fb5d4ff/match_test.go#L15
GO_CODEOWNER_EXAMPLES = [
    ex(
        name="single-segment pattern",
        pattern="foo",
        paths={
            "foo": True,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": True,
            "bar/foo/baz": True,
            "bar/baz": False,
        },
    ),
    ex(
        name="single-segment pattern with leading slash",
        pattern="/foo",
        paths={
            "foo": True,
            "fool": False,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": False,
            "bar/baz": False,
        },
    ),
    ex(
        name="single-segment pattern with trailing slash",
        pattern="foo/",
        paths={
            "foo": False,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": True,
            "bar/baz": False,
        },
    ),
    ex(
        name="single-segment pattern with leading and trailing slash",
        pattern="/foo/",
        paths={
            "foo": False,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": False,
            "bar/baz": False,
        },
    ),
    ex(
        name="multi-segment pattern",
        pattern="foo/bar",
        paths={
            "foo/bar": True,
            "foo/bart": False,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    ex(
        name="multi-segment pattern with leading slash",
        pattern="/foo/bar",
        paths={
            "foo/bar": True,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    ex(
        name="multi-segment pattern with trailing slash",
        pattern="foo/bar/",
        paths={
            "foo/bar": False,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    ex(
        name="multi-segment pattern with leading and trailing slash",
        pattern="/foo/bar/",
        paths={
            "foo/bar": False,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    ex(
        name="single segment pattern with wildcard",
        pattern="f*",
        paths={
            "foo": True,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": True,
            "bar/foo/baz": True,
            "bar/baz": False,
            "xfoo": False,
        },
    ),
    ex(
        name="single segment pattern with leading slash and wildcard",
        pattern="/f*",
        paths={
            "foo": True,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": False,
            "bar/baz": False,
            "xfoo": False,
        },
    ),
    ex(
        name="single segment pattern with trailing slash and wildcard",
        pattern="f*/",
        paths={
            "foo": False,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": True,
            "bar/baz": False,
            "xfoo": False,
        },
    ),
    ex(
        name="single segment pattern with leading and trailing slash and wildcard",
        pattern="/f*/",
        paths={
            "foo": False,
            "foo/": True,
            "foo/bar": True,
            "bar/foo": False,
            "bar/foo/baz": False,
            "bar/baz": False,
            "xfoo": False,
        },
    ),
    ex(
        name="single segment pattern with escaped wildcard",
        pattern=r"f\*o",
        paths={"foo": False, "f*o": True},
    ),
    ex(
        name="multi-segment pattern with wildcard",
        pattern="foo/*.txt",
        paths={
            "foo": False,
            "foo/": False,
            "foo/bar.txt": True,
            "foo/bar/baz.txt": False,
            "qux/foo/bar.txt": False,
            "qux/foo/bar/baz.txt": False,
        },
    ),
    ex(
        name="single segment pattern with single-character wildcard",
        pattern="f?o",
        paths={"foo": True, "fo": False, "fooo": False},
    ),
    ex(
        name="single segment pattern with escaped single-character wildcard",
        pattern="f\\?o",
        paths={"foo": False, "f?o": True},
    ),
    ex(
        name="single segment pattern with character range",
        pattern="[Ffb]oo",
        paths={"foo": True, "Foo": True, "boo": True, "too": False},
    ),
    ex(
        name="single segment pattern with escaped character range",
        pattern="[\\]f]o\\[o\\]",
        paths={"fo[o]": True, "]o[o]": True, "foo": False},
    ),
    ex(
        name="leading double-asterisk wildcard",
        pattern="**/foo/bar",
        paths={
            "foo/bar": True,
            "qux/foo/bar": True,
            "qux/foo/bar/baz": True,
            "foo/baz/bar": False,
            "qux/foo/baz/bar": False,
        },
    ),
    ex(
        name="leading double-asterisk wildcard with regular wildcard",
        pattern="**/*bar*",
        paths={
            "bar": True,
            "foo/bar": True,
            "foo/rebar": True,
            "foo/barrio": True,
            "foo/qux/bar": True,
        },
    ),
    ex(
        name="trailing double-asterisk wildcard",
        pattern="foo/bar/**",
        paths={
            "foo/bar": False,
            "foo/bar/baz": True,
            "foo/bar/baz/qux": True,
            "qux/foo/bar": False,
            "qux/foo/bar/baz": False,
        },
    ),
    ex(
        name="middle double-asterisk wildcard",
        pattern="foo/**/bar",
        paths={
            "foo/bar": True,
            "foo/bar/baz": True,
            "foo/qux/bar/baz": True,
            "foo/qux/quux/bar/baz": True,
            "foo/bar/baz/qux": True,
            "qux/foo/bar": False,
            "qux/foo/bar/baz": False,
        },
    ),
    ex(
        name="middle double-asterisk wildcard with trailing slash",
        pattern="foo/**/",
        paths={"foo/bar": False, "foo/bar/": True, "foo/bar/baz": True},
    ),
    ex(
        name="docs absolute",
        pattern="/docs/",
        paths={
            "/docs/build-app/troubleshooting.md": False,
            "/docs/getting-started.md": False,
            "docs/getting-started.md": True,
            "/docs/getting-started/foo.md": False,
            "/docs_for_othr_stuff/getting-started/foo.md": False,
            "docs/foo.js": True,
            "bar/docs/getting-started.md": False,
        },
    ),
    ex(
        name="apps with trailing",
        pattern="apps/",
        paths={
            "apps/foo/bar/buzz.rs": True,
            "foo/buzz/bar/apps/foo.rs": True,
            "foo/buzz/bar": False,
            "appsbarbuzz": False,
            "/appsbar/buzz": False,
            "apps/": True,
        },
    ),
    ex(
        name="docs with star",
        pattern="docs/*",
        paths={
            "docs/getting-started.md": True,
            "docs/build-app/troubleshooting.md": True,
            "/docs/getting-started.md": False,
            "docs/getting-started/foo.md": True,
            "docs/": True,
            "bar/docs/getting-started.md": False,
            "foo/bar/docs/foo.js": False,
            "foo/docs/foo.js": False,
            "buzz/docs/gettingstarted.md": False,
        },
    ),
    ex(
        name="build logs abs",
        pattern="/build/logs/",
        paths={
            "build/logs/foo.go": True,
            "build/logs/foo/bar.go": True,
            "/build/logs/foo/buzz.go": False,
            "foo/build/logs/foo.go": False,
        },
    ),
    ex(
        name="go files",
        pattern="*.go",
        paths={"foo.go": True, "bar/foo.go": True, "forgo": False},
    ),
    ex(
        name="js files",
        pattern="*.js",
        paths={
            "docs/foo.js": True,
            "bar/buzzjs": False,
            "buzz_foo.js": True,
            "bar/foo/buzz/foo.js": True,
            "foo.txt": False,
        },
    ),
    ex(name="all files", pattern="*", paths={"buzz": True, "foo": True}),
    ex(name="escaping str", pattern=r"\*-foo.js", paths={"*-foo.js": True}),
    ex(name="apps absolute", pattern="apps/", paths={"apps/": True}),
    ex(name="foo/bar", pattern="foo/bar", paths={"foo/bar/baz.rs": True}),
    ex(name="expansion inline", pattern="**/dir/*.*", paths={"bla/dir/file.txt": True}),
    ex(
        name="regression directory expansion",
        pattern="**/dir/**/*.*",
        paths={"bla/dir/file.txt": True},
    ),
    ex(
        name="$",
        pattern="bar/buzz$private$file.txt",
        paths={"bar/buzz$private$file.txt": True},
    ),
    ex(
        name="inner splat",
        pattern="test*10.txt",
        paths={"test*10.txt": True, "testtttt*10.txt": True},
    ),
    ex(name="broken regex capture group", pattern="foo(.txt", paths={"foo(.txt": True}),
    ex(
        name="broken regex capture group-2",
        pattern="bar).txt",
        paths={"bar).txt": True},
    ),
    ex(name="plus", pattern="bar+foo.log", paths={"bar+foo.log": True}),
    ex(
        name="regex like char group",
        pattern="bar{foo}.log",
        paths={"bar{foo}.log": True, "barf": False, "baro": False},
    ),
    ex(name="caret", pattern="bar^foo.log", paths={"bar^foo.log": True}),
    ex(
        name="regex character group",
        pattern="bar[0-5].log",
        paths={
            "bar0.log": True,
            # differs between git versions
            # "bar[0-5].log": True,
        },
    ),
]


def test_unterminated_char_class() -> None:
    """
    Ensure we warn about unterminated character classes
    """
    with pytest.raises(ValueError):
        CodeOwners("foo[bar.js  @js-user")


def ids_for(data: Iterable[ex]) -> List[str]:
    return [d.name for d in data]


@pytest.mark.parametrize(
    "name,pattern,paths", GO_CODEOWNER_EXAMPLES, ids=ids_for(GO_CODEOWNER_EXAMPLES)
)
def test_specific_pattern_path_matching(
    name: str, pattern: str, paths: Dict[str, bool]
) -> None:
    assert paths
    for path, expected in paths.items():
        owners = CodeOwners(f"{pattern}  @js-user")
        matches = owners.of(path) == [("USERNAME", "@js-user")]
        regex, *_ = owners.paths[0]
        assert (
            matches == expected
        ), f"""{pattern} {regex} {"matches" if expected else "shouldn't match"} {path}"""


@pytest.mark.parametrize(
    "name,pattern,paths", GO_CODEOWNER_EXAMPLES, ids=ids_for(GO_CODEOWNER_EXAMPLES)
)
def test_specific_patterns_against_git(
    name: str, pattern: str, paths: Dict[str, bool]
) -> None:
    """
    Ensure the expected patterns match actual git behavior.

    Codeowners is a subset of git ignore behavior so checking against it
    should work in most cases.
    """
    assert paths
    directory = tempfile.TemporaryDirectory()
    subprocess.run(["git", "init"], cwd=directory.name, check=True, capture_output=True)
    (Path(directory.name) / ".gitignore").write_text(pattern + "\n")
    for path, expected in paths.items():
        res = subprocess.run(
            ["git", "check-ignore", path], cwd=directory.name, capture_output=True
        )
        actual = res.returncode == 0
        assert (
            actual is expected
        ), f"match for pattern:{pattern} and path:{path} failed, expected: {expected}, actual: {actual}"
