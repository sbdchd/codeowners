import re
from textwrap import dedent
from typing import Dict, List, Mapping, NamedTuple, Pattern, Tuple

import pytest

from codeowners import CodeOwners, path_to_regex, pattern_matches


def test_readme_example() -> None:

    example_file = dedent(
        """\
    # owners for js files
    *.js    @ghost
    # python
    *.py user@example.com
    # misc
    /build/logs/ @dmin
    docs/*  docs@example.com
    """
    )

    owners = CodeOwners(example_file)
    assert owners.of("test.js") == [("USERNAME", "@ghost")]


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

# In this example, @octocat owns any file in an apps directory
# anywhere in your repository.
apps/ @octocat

# In this example, @doctocat owns any file in the `/docs`
# directory in the root of your repository.
/docs/ @doctocat
"""


def test_parse_paths_result() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.paths == [
        (re.compile(r"^/?docs/.*$"), "/docs/", [("USERNAME", "@doctocat")]),
        (re.compile(r".*/?apps/.*$"), "apps/", [("USERNAME", "@octocat")]),
        (re.compile(r".*/?docs/[^/]*"), "docs/*", [("EMAIL", "docs@example.com")]),
        (re.compile(r"^/?build/logs/.*$"), "/build/logs/", [("USERNAME", "@doctocat")]),
        (re.compile(r".*\.go$"), "*.go", [("EMAIL", "docs@example.com")]),
        (re.compile(r".*\.js$"), "*.js", [("USERNAME", "@js-owner")]),
        (
            re.compile(r".*"),
            "*",
            [("USERNAME", "@global-owner1"), ("USERNAME", "@global-owner2")],
        ),
    ]


path_to_examples: Mapping[str, List[Tuple[str, bool]]] = {
    "/docs/": [
        ("/docs/build-app/troubleshooting.md", True),
        ("/docs/getting-started.md", True),
        ("/docs/getting-started/foo.md", True),
        ("/docs_for_othr_stuff/getting-started/foo.md", False),
        ("docs/foo.js", True),
        ("bar/docs/getting-started.md", False),
    ],
    "apps/": [
        ("apps/foo/bar/buzz.rs", True),
        ("foo/buzz/bar/apps/foo.rs", True),
        ("foo/buzz/bar", False),
        ("appsbarbuzz", False),
        ("/appsbar/buzz", False),
        ("apps/", True),
    ],
    "docs/*": [
        ("docs/getting-started.md", True),
        ("docs/build-app/troubleshooting.md", False),
        ("/docs/getting-started.md", True),
        ("docs/getting-started/foo.md", False),
        ("docs/", True),
        ("bar/docs/getting-started.md", True),
    ],
    "/build/logs/": [
        ("build/logs/foo.go", True),
        ("build/logs/foo/bar.go", True),
        ("/build/logs/foo/buzz.go", True),
        ("foo/build/logs/foo.go", False),
    ],
    "*.go": [("foo.go", True), ("bar/foo.go", True), ("forgo", False)],
    "*.js": [
        ("docs/foo.js", True),
        ("bar/buzzjs", False),
        ("buzz_foo.js", True),
        ("bar/foo/buzz/foo.js", True),
    ],
    "*": [("buzz", True), ("foo", True)],
}


def _pattern_matches(regex: Pattern[str], path: str) -> bool:
    match = regex.match(path)
    return match is not None and match.span() == (0, len(path))


@pytest.mark.parametrize("codeowner_path, examples", path_to_examples.items())
def test_regex_match(codeowner_path: str, examples: List[Tuple[str, bool]]) -> None:
    for path, expected in examples:
        regex = path_to_regex(codeowner_path)
        assert (
            _pattern_matches(regex, path)
        ) is expected, f'{codeowner_path}, {path} {"matches" if expected else "does not match"} {regex.pattern}'


def test_nested_docs_example() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("buzz/docs/gettingstarted.md") == [("EMAIL", "docs@example.com")]
    assert owners.of("docs/build-app/troubleshooting.md") == [("USERNAME", "@doctocat")]
    assert owners.of("buzz/docs/build-app/troubleshooting.md") == [
        ("USERNAME", "@global-owner1"),
        ("USERNAME", "@global-owner2"),
    ]


def test_docs_dir() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("docs/") == [("USERNAME", "@doctocat")]


def test_owners_owns_wildcard() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("foo.txt") == [
        ("USERNAME", "@global-owner1"),
        ("USERNAME", "@global-owner2"),
    ]
    assert owners.of("foo/bar.txt") == [
        ("USERNAME", "@global-owner1"),
        ("USERNAME", "@global-owner2"),
    ]


def test_owners_owns_js_extensions() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("foo.js") == [("USERNAME", "@js-owner")]
    assert owners.of("foo/bar.js") == [("USERNAME", "@js-owner")]


def test_owners_owns_go_extensions() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("foo.go") == [("EMAIL", "docs@example.com")]
    assert owners.of("foo/bar.go") == [("EMAIL", "docs@example.com")]


def test_owners_owns_anchored_build_logs() -> None:
    owners = CodeOwners(EXAMPLE)
    assert owners.of("build/logs/foo.go") == [("USERNAME", "@doctocat")]
    assert owners.of("build/logs/foo/bar.go") == [("USERNAME", "@doctocat")]
    assert owners.of("foo/build/logs/foo.go") == [("EMAIL", "docs@example.com")]


def test_owners_owns_unachored_docs() -> None:
    owners = CodeOwners(EXAMPLE)

    assert owners.of("foo/docs/foo.js") == [("EMAIL", "docs@example.com")]
    assert owners.of("foo/bar/docs/foo.js") == [("EMAIL", "docs@example.com")]
    assert owners.of("foo/bar/docs/foo/foo.js") == [("USERNAME", "@js-owner")]


def test_owners_owns_unachored_apps() -> None:
    assert CodeOwners(EXAMPLE).of("foo/apps/foo.js") == [("USERNAME", "@octocat")]
    assert CodeOwners(EXAMPLE).of("foo/apps/bar/buzz/foo.js") == [
        ("USERNAME", "@octocat")
    ]


def test_owners_owns_anchored_docs() -> None:
    assert CodeOwners(EXAMPLE).of("docs/foo.js") == [("USERNAME", "@doctocat")]


def test_implied_children_owners() -> None:
    assert CodeOwners("foo/bar @doug").of("foo/bar/baz.rs") == [("USERNAME", "@doug")]


def test_escaping_str() -> None:
    assert CodeOwners(r"\*-foo.js @doug").of("*-foo.js") in ([], None)
    assert CodeOwners("apps/ @doug").of("apps/") == [("USERNAME", "@doug")]


def test_no_fallback() -> None:
    owners = CodeOwners(
        dedent(
            """
          # We have no fallback in this file.
          *.js    @org_name/js-team
          """
        )
    )

    assert owners.of("bar.js") == [("TEAM", "@org_name/js-team")]
    assert owners.of("foo.txt") == []


def test_rule_missing_owner() -> None:
    owners = CodeOwners("*.js")
    assert owners.of("bar.js") == []


def test_codeowners_with_regex_chars() -> None:
    owners = CodeOwners(
        dedent(
            """
          foo?bar.html    @html-owner
          foo?bar.html    @html-owner
          foo-bar.html  @html-owner

          bar/buzz$private$file.txt  @txt-team
          test*10.txt @txt-team

          foo(.txt foo@example.org
          bar).txt bar@example.org

          bar+foo.log @logging
          bar{foo}.log @logging
          bar{6}.log @logging
          bar^foo.log  @logging
          bar^foo.log  @logging
          bar[0-5].log @logging
          """
        )
    )
    assert owners.of("foo-bar.html") == [("USERNAME", "@html-owner")]
    assert owners.of("foo?bar.html") == [("USERNAME", "@html-owner")]
    assert owners.of("fobar.html") == []
    assert owners.of("foo-bar.html") == [("USERNAME", "@html-owner")]

    assert owners.of("bar/buzz$private$file.txt") == [("USERNAME", "@txt-team")]
    assert owners.of("test*10.txt") == [("USERNAME", "@txt-team")]
    assert owners.of("testtttt*10.txt") == []

    assert owners.of("foo(.txt") == [("EMAIL", "foo@example.org")]
    assert owners.of("bar).txt") == [("EMAIL", "bar@example.org")]

    assert owners.of("bar+foo.log") == [("USERNAME", "@logging")]
    assert owners.of("bar{foo}.log") == [("USERNAME", "@logging")]
    assert owners.of("bar{6}.log") == [("USERNAME", "@logging")]
    assert owners.of("bar^foo.log") == [("USERNAME", "@logging")]
    assert owners.of("bar[0-5].log") == [("USERNAME", "@logging")]


def test_regression_directory_expansion() -> None:
    owners = CodeOwners(
        dedent(
            """
            **/dir/**/*.* @a
            """
        )
    ).of("bla/dir/file.txt")
    assert owners == [("USERNAME", "@a")]


def test_expansion_inline() -> None:
    owners = CodeOwners(
        dedent(
            """
            **/dir/*.* @a
            """
        )
    ).of("bla/dir/file.txt")
    assert owners == [("USERNAME", "@a")]


class PatternTestExample(NamedTuple):
    name: str
    pattern: str
    paths: Dict[str, bool]


# Taken from: https://github.com/hmarr/codeowners/blob/d0452091447bd2a29ee508eebc5a79874fb5d4ff/match_test.go#L15
GO_CODEOWNER_EXAMPLES = [
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
        name="multi-segment pattern with leading slash",
        pattern="/foo/bar",
        paths={
            "foo/bar": True,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    PatternTestExample(
        name="multi-segment pattern with trailing slash",
        pattern="foo/bar/",
        paths={
            "foo/bar": False,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    PatternTestExample(
        name="multi-segment pattern with leading and trailing slash",
        pattern="/foo/bar/",
        paths={
            "foo/bar": False,
            "foo/bar/baz": True,
            "baz/foo/bar": False,
            "baz/foo/bar/qux": False,
        },
    ),
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
        name="single segment pattern with escaped wildcard",
        pattern="f\\*o",
        paths={"foo": False, "f*o": True},
    ),
    PatternTestExample(
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
    PatternTestExample(
        name="single segment pattern with single-character wildcard",
        pattern="f?o",
        paths={"foo": True, "fo": False, "fooo": False},
    ),
    PatternTestExample(
        name="single segment pattern with escaped single-character wildcard",
        pattern="f\\?o",
        paths={"foo": False, "f?o": True},
    ),
    PatternTestExample(
        name="single segment pattern with character range",
        pattern="[Ffb]oo",
        paths={"foo": True, "Foo": True, "boo": True, "too": False},
    ),
    PatternTestExample(
        name="single segment pattern with escaped character range",
        pattern="[\\]f]o\\[o\\]",
        paths={"fo[o]": True, "]o[o]": True, "foo": False},
    ),
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
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
    PatternTestExample(
        name="middle double-asterisk wildcard with trailing slash",
        pattern="foo/**/",
        paths={"foo/bar": False, "foo/bar/": True, "foo/bar/baz": True},
    ),
]


def _path_matches(*, path: str, pattern: str) -> bool:
    return pattern_matches(pattern=path_to_regex(pattern), path=path)


def _idfn(name: str) -> str:
    return name


@pytest.mark.parametrize("name,pattern,paths", GO_CODEOWNER_EXAMPLES, ids=_idfn)
def test_go_codeowners_examples(
    name: str, pattern: str, paths: Dict[str, bool]
) -> None:
    assert paths
    for path, expected in paths.items():
        assert (
            _path_matches(path=path, pattern=pattern) == expected
        ), f"{name} {pattern} matches {path}"

