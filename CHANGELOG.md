# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [0.2.0] - 2025-08-09

### Added
- Plugin system for extensible device support using Python entry points
  - Automatic plugin discovery and loading via `importlib.metadata`
  - Device validation with inheritance checking
  - Singleton `PluginManager` for centralized control
  - Support for external package device extensions
- Automated release pipeline: GitHub releases on version tags, PyPI trusted publishing, release notes from git history

### Changed
- Modular plugin-based architecture for extensibility
- Standardised logging format across all modules
- Enhanced CI/CD workflow with security scanning and automated releases

## [0.1.0] - 2024-09-05

### Added
- Initial release of Router Test Kit
- SSH and Telnet connection management with automatic retry
- Device abstraction: `LinuxDevice`, `OneOS6Device`, `RADIUSServer`, `HostDevice`
- Network utilities: ping, packet loss parsing, IP validation, SCP transfer
- MkDocs documentation site deployed to GitHub Pages
- CI/CD pipeline with GitHub Actions
- PyPI package publishing via `pyproject.toml`
