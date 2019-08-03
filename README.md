# codeowners

> Python bindings to [softprops's Rust codeowners library](https://crates.io/crates/codeowners).

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
cargo test

# testing a build in Python
cargo build --release
cp target/release/libcodeowners.dylib codeowners.so
ipython
import codeowners
```
