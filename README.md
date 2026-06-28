# codeowners [![CI](https://github.com/sbdchd/codeowners/actions/workflows/ci.yml/badge.svg)](https://github.com/sbdchd/codeowners/actions/workflows/ci.yml) [![pypi](https://img.shields.io/pypi/v/codeowners.svg)](https://pypi.org/project/codeowners/)

> Python codeowners parser based on [softprops's Rust
> library](https://crates.io/crates/codeowners) and [hmarr's Go
> library](https://github.com/hmarr/codeowners/).

## Why?

To allow Python users to parse [codeowners
files](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/about-code-owners#codeowners-syntax)
in Python.

## Install

```shell
pip install codeowners
```

## Usage

```python
from codeowners import CodeOwners

example_file = """\
# owners for js files
*.js    @ghost
# python
*.py user@example.com
# misc
/build/logs/ @dmin
docs/*  docs@example.com
"""

owners = CodeOwners(example_file)
assert owners.of("test.js") ==  [('USERNAME', '@ghost')]
```

### Path format

Paths passed to `of()` (and `matching_line()` / `section_name()`) must be
repo-relative with no leading slash, matching the behavior of the upstream
[Go](https://github.com/hmarr/codeowners/) and
[Rust](https://github.com/hmarr/codeowners-rs) libraries as well as
`git check-ignore`. A leading slash will not match:

```python
owners = CodeOwners("/build/logs/log.txt @ghost")
assert owners.of("build/logs/log.txt") == [('USERNAME', '@ghost')]  # ✅
assert owners.of("/build/logs/log.txt") == []                       # ✗ leading slash
```

## Dev

```shell
uv sync

s/test

s/lint
```

## Releasing a New Version

```shell
# bump version in pyproject.toml

# update CHANGELOG.md

# commit release commit to GitHub

# build and publish
uv build
uv publish

# create a release in the GitHub UI
```
