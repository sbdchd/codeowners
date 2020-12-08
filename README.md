# codeowners [![CircleCI](https://circleci.com/gh/sbdchd/codeowners.svg?style=svg)](https://circleci.com/gh/sbdchd/codeowners) [![pypi](https://img.shields.io/pypi/v/codeowners.svg)](https://pypi.org/project/codeowners/)

> Python bindings to [softprops's Rust codeowners library](https://crates.io/crates/codeowners).

## Why?

To allow Python users to parse codeowners files without having to rewrite
an existing implementation.

## Install

```shell
poetry add codeowners
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

cargo test --no-default-features

# trying a build in Python
./.venv/bin/pyo3-pack develop
./.venv/bin/python -c "import codeowners; print(codeowners.CodeOwners)"
```


## Releasing a New Version

```shell
# bump version in Cargo.toml

# build the macos version
./.venv/bin/pyo3-pack build --release

# build the linux versions
# Note: this is just the version for the builder container
TAG="sbdchd/codeowners-builder:0.1.2"
docker build -f build.Dockerfile . --tag "$TAG"

# Note: building the Python versions can take a while if you are running Docker inside a VM
docker run --rm -v $(pwd):/io "$TAG" build --release

# upload wheels to PyPi
# Note: this will prompt for PyPi creds
./.venv/bin/twine upload --skip-existing target/wheels/*
```
