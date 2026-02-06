# Proposal: Add Internationalization (i18n) Support

## Why

Currently, skill-hub only supports English text throughout the application, creating barriers for the significant non-English speaking user base, particularly Chinese-speaking developers. The codebase already has Chinese documentation (README.zh-CN.md), but the application itself operates English-only, creating an inconsistent user experience.

Adding i18n support for English and Chinese will:
1. Make the tool accessible to Chinese-speaking developers who are a major user demographic
2. Align application language support with documentation language support
3. Provide a foundation for adding more languages in the future
4. Improve user experience by allowing users to work in their preferred language

## Problem Statement

Currently, skill-hub has hardcoded English text throughout the application (CLI messages, web interface, error messages). This creates barriers for non-English speaking users, particularly Chinese-speaking developers who are a significant user base.

The codebase already has Chinese documentation (README.zh-CN.md), indicating awareness of international users, but the application itself only operates in English. This creates an inconsistent user experience where documentation is available in multiple languages but the actual tool is English-only.

## Proposed Solution

Add internationalization support for English and Chinese languages with the ability to select and switch languages at runtime. This will cover:

1. **CLI Interface**: All command output, error messages, and help text
2. **Web Interface**: All UI text, labels, buttons, tooltips, and messages
3. **Language Selection**: User preference stored in configuration
4. **Language Switching**: Runtime ability to change language without restart (web UI)

### Key Design Decisions

1. **Two Languages Only**: Start with English (en) and Chinese (zh-CN) as the initial supported languages
2. **Default Language**: English remains the default for backward compatibility
3. **Storage**: Language preference stored in `~/.skills/.skill-hub/config.json`
4. **Framework**: Use Python's standard `gettext` for CLI, Jinja2 i18n extension for web templates
5. **Fallback**: If translation missing, fall back to English gracefully
6. **Scope**: Focus on user-facing text only; code comments, logs, and internal strings remain English

## Scope

**In Scope:**
- CLI command output and messages
- Web interface (all templates and UI text)
- Error messages and validation feedback
- Configuration for language preference
- Language switcher in web UI
- Translation files for en and zh-CN

**Out of Scope:**
- Skill content translation (skills remain in their original language)
- Dynamic translation of user-generated content
- Additional languages beyond English and Chinese
- Right-to-left (RTL) language support
- Pluralization rules for complex cases
- Date/time formatting localization (can use system defaults)

## Success Criteria

- [ ] User can set language preference via CLI (`skill-hub config set language zh-CN`)
- [ ] All CLI commands respect the configured language setting
- [ ] Web interface displays in the configured language
- [ ] Language can be switched in web UI without restart
- [ ] All user-facing text is translatable
- [ ] Missing translations fall back to English gracefully
- [ ] README examples show usage in both languages
- [ ] No breaking changes to existing configuration or CLI

## Dependencies

- Python `gettext` module (stdlib, no new dependency)
- Jinja2 i18n extension (already available via Jinja2)
- Translation workflow setup (manual translation, no automated tools initially)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Inconsistent translations | Medium | Create translation guidelines and review process |
| Missing translations | Low | Implement robust fallback to English |
| Performance overhead | Low | Gettext is highly optimized; negligible impact |
| Maintenance burden | Medium | Keep translation strings minimal and well-organized |
| Breaking changes | Medium | Make language setting optional with sensible default |

## Alternative Approaches Considered

1. **Third-party i18n libraries (Babel, etc.)**: Adds dependency overhead; gettext is sufficient
2. **JSON-based translations**: Less standard than gettext .po files; harder tooling support
3. **Client-side only (web)**: Inconsistent with CLI; partial solution
4. **Support 10+ languages**: Too ambitious for v1; focus on quality over quantity

## Timeline Estimate

- Design & spec: 0.5 day
- CLI i18n implementation: 1 day
- Web i18n implementation: 1.5 days
- Translation (Chinese): 1 day
- Testing & validation: 0.5 day
- Documentation: 0.5 day

**Total**: ~5 days
