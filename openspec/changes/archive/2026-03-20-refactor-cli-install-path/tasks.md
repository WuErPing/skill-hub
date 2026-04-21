## 1. Directory Discovery

- [x] 1.1 Update `discovery/engine.py` to discover private directories (`.*/skills/private`)
- [x] 1.2 Add function `discover_all_skill_directories()` to find all skill directories
- [x] 1.3 Update `DiscoveryEngine` class to track directory source (public/private)
- [x] 1.4 Add priority system for resolving duplicate skills across directories

## 2. CLI Command Updates

- [x] 2.1 Update `cli.py install` command to add `--to public|private` flag
- [x] 2.2 Update `cli.py list` command to add `--all|public|private` flags
- [x] 2.3 Add `cli.py sync` command for explicit skill synchronization
- [x] 2.4 Update `cli.py compare` command to show directory source

## 3. Skill Installation Enhancements

- [x] 3.1 Update `installer.py install_from_github()` to support target directory flag
- [x] 3.2 Update `installer.py install_from_local()` to support target directory flag
- [x] 3.3 Update `installer.py install_from_url()` to support target directory flag
- [x] 3.4 Add `get_install_path(skill_name, target)` helper function

## 4. Sync Command Implementation

- [x] 4.1 Implement `sync` command in `cli.py`
- [x] 4.2 Add `sync_skill()` function to `installer.py`
- [x] 4.3 Implement dry-run mode for sync (`--dry-run` flag)
- [x] 4.4 Implement overwrite protection with confirmation

## 5. Priority System Implementation

- [x] 5.1 Add `resolve_skill_priority()` function in `discovery/engine.py`
- [x] 5.2 Update skill listing to show source directory
- [x] 5.3 Update comparison logic to respect priority order
- [x] 5.4 Add warning when duplicate skills exist

## 6. Testing

- [x] 6.1 Test directory discovery with public and private directories
- [x] 6.2 Test install to public directory (backward compatibility)
- [x] 6.3 Test install to private directory
- [x] 6.4 Test sync command (public to private, private to public)
- [x] 6.5 Test priority resolution when same skill exists in multiple directories
- [x] 6.6 Test dry-run mode for sync
- [x] 6.7 Test overwrite protection

## 7. Documentation

- [x] 7.1 Update README.md with new commands and flags
- [x] 7.2 Add examples for multi-layer skill usage
- [x] 7.3 Document priority system and how it affects skill resolution
- [x] 7.4 Add migration guide for existing users
