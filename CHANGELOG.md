# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

# 0.6.0 - 2022-07-22

- Support gitlab sections (#38). Thanks @corbinbs!

- Allow listing all matching lines (#37). Thanks @glujan!

# 0.5.0 - 2022-05-05

### Added

- returning path alongside owners for `matching_line` (#35). Thanks @pahwaranger!

# 0.4.1 - 2022-05-26

### Added

- Support typing_extensions v4. Thanks @martinxsliu!

# 0.4.0 - 2021-08-24

### Added

- `matching_line` method to return line of code owners match (#26). Thanks @valeryz!

# 0.3.0 - 2021-03-16

### Added

- ignore GitLab specific codeowner sections (#23)

## 0.2.1 - 2021-01-27

### Fixed

- Fixed broken directory expansion

## 0.2.0 - 2021-01-24

### Added

- added type hints

### Changed

- no longer using bindings to Rust library, instead the parsing is done in Python
  - this makes distributing easier
