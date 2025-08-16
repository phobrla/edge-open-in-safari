# Changelog

All notable changes to this project will be documented in this file, following SemVer.

## [1.2.0] - 2025-08-16
### Changed
- Switched extension icon to the Safari SF Symbol (provided by user) in extension/icons/icon.svg. Re-run mac/open_in_safari.command to regenerate PNGs.

### Fixed
- mac/open_in_safari.command: corrected a loop terminator typo in detect_vnic_ips (done instead of end).

## [1.1.0] - 2025-08-16
### Added
- Extension icons: vector source (SVG) and auto-generation of PNG sizes (16/32/48/128) via mac/open_in_safari.command
- Manifest and background updated to use the icons
- README updated with icon instructions and licensing note

## [1.0.0] - 2025-08-16
### Added
- Initial release with:
  - macOS zsh orchestrator and Python 3 server
  - LaunchAgent template
  - Edge (Chromium) Manifest V3 extension with toolbar button, context menus, options, and keyboard shortcut