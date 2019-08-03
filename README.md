# codeowners

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

cargo test

# trying a build in Python
poetry run pyo3-pack develop
poetry run python -c "import codeowners; print(codeowners.CodeOwners)"
```


## Releasing a New Version

```shell
# bump version in Cargo.toml
poetry run pyo3-pack build --release
# Note: this will prompt for PyPi creds
poetry run pyo3-pack publish
```
