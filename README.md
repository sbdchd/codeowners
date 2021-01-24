# codeowners [![CircleCI](https://circleci.com/gh/sbdchd/codeowners.svg?style=svg)](https://circleci.com/gh/sbdchd/codeowners) [![pypi](https://img.shields.io/pypi/v/codeowners.svg)](https://pypi.org/project/codeowners/)

> Python codeowners parser based on [softprops's Rust codeowners library](https://crates.io/crates/codeowners).

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

## Dev

```shell
poetry install

s/test

s/lint
```

## Releasing a New Version

```shell
# bump version in pyproject.toml

# build
poetry build -f wheel

# build and publish
poetry publish --build
```
