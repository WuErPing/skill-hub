# Tasks: Add Internationalization (i18n) Support

## Phase 1: Core Infrastructure

- [ ] **Create i18n utility module**
  - Create `src/skill_hub/i18n.py` with translation functions
  - Implement `init_translation(language)` function
  - Implement `_(message)` translation function  
  - Implement `get_current_language()` helper
  - **Validation**: Unit test confirms translations load for en and zh_CN
  - **Validation**: Unit test confirms fallback to English when translation missing

- [ ] **Update Config model**
  - Add `language: str = "en"` field to Config dataclass
  - Update ConfigManager to save/load language field
  - Add language validation (accept only "en" and "zh_CN")
  - **Validation**: Unit test confirms config loads with language field
  - **Validation**: Unit test confirms backward compatibility (missing language defaults to "en")

- [ ] **Create translation file structure**
  - Create `src/skill_hub/locales/` directory structure
  - Create `en/LC_MESSAGES/` and `zh_CN/LC_MESSAGES/` subdirectories
  - Create empty `.po` template files
  - Add `.mo` files to .gitignore (compiled files)
  - **Validation**: Directory structure matches gettext conventions

## Phase 2: CLI Internationalization

- [ ] **Update CLI to use translations**
  - Import i18n module in `cli.py`
  - Initialize translation on CLI startup based on config
  - Wrap all console.print() messages with _() function
  - Wrap all error messages with _() function
  - **Validation**: CLI displays messages in configured language
  - **Validation**: Language preference persists across commands

- [ ] **Translate CLI command descriptions**
  - Wrap Click command help strings with _() function
  - Wrap option help strings with _() function
  - Preserve command names and flags (don't translate)
  - **Validation**: `skill-hub --help` displays in configured language
  - **Validation**: `skill-hub COMMAND --help` displays in configured language

- [ ] **Extract CLI translatable strings**
  - Use xgettext or pybabel to extract strings from Python files
  - Generate `locales/messages.pot` template
  - Create `en/LC_MESSAGES/messages.po` (reference)
  - Create `zh_CN/LC_MESSAGES/messages.po` (to be translated)
  - **Validation**: All user-facing strings present in .pot file

## Phase 3: Web Interface Internationalization

- [ ] **Setup Jinja2 i18n extension**
  - Enable Jinja2 i18n extension in FastAPI templates
  - Configure template environment with gettext functions
  - Add language middleware to set request language
  - **Validation**: Templates can use {{ _("text") }} syntax
  - **Validation**: Middleware sets correct language per request

- [ ] **Update all web templates**
  - Wrap all user-facing text in dashboard.html with {{ _() }}
  - Wrap all text in agents.html with {{ _() }}
  - Wrap all text in skills.html with {{ _() }}
  - Wrap all text in sync.html with {{ _() }}
  - Wrap all text in repositories.html with {{ _() }}
  - Wrap all text in config.html with {{ _() }}
  - Wrap all text in index.html with {{ _() }}
  - **Validation**: All templates use translation syntax
  - **Validation**: No hardcoded English remains in templates

- [ ] **Add language switcher component**
  - Add language switcher to navigation/header in index.html
  - Style switcher with current language highlighted
  - Add JavaScript for language switching
  - **Validation**: Language switcher visible on all pages
  - **Validation**: Current language visually indicated

- [ ] **Add language switcher endpoint**
  - Create POST `/set-language` endpoint in fastapi_app.py
  - Accept language parameter from form data
  - Update config file with new language
  - Set language cookie with 1-year expiration
  - Return success response
  - **Validation**: POST request updates language preference
  - **Validation**: Cookie persists language choice
  - **Validation**: Config file updated successfully

- [ ] **Extract web translatable strings**
  - Extract strings from all template files
  - Merge with CLI strings in `messages.pot`
  - Update .po files with new strings
  - **Validation**: Template strings present in .po files
  - **Validation**: No duplicate message IDs

## Phase 4: Translation Content

- [ ] **Translate to Simplified Chinese**
  - Translate all CLI messages to Chinese in `zh_CN/messages.po`
  - Translate all web UI text to Chinese
  - Translate error messages to Chinese
  - Translate help text to Chinese
  - Review translations for accuracy and tone
  - **Validation**: All msgid entries have corresponding msgstr
  - **Validation**: Native speaker review confirms quality

- [ ] **Compile translation files**
  - Compile en/messages.po to messages.mo with msgfmt
  - Compile zh_CN/messages.po to messages.mo
  - Add compilation step to build/deployment process
  - **Validation**: .mo files generated successfully
  - **Validation**: Compiled files loadable by gettext

- [ ] **Test translations**
  - Test CLI in English mode
  - Test CLI in Chinese mode
  - Test web UI in English mode
  - Test web UI in Chinese mode
  - Test language switching in web UI
  - Test fallback when translation missing
  - **Validation**: All text displays correctly in both languages
  - **Validation**: No untranslated strings visible to users

## Phase 5: Documentation & Polish

- [ ] **Update README files**
  - Add language configuration section to README.md
  - Add language configuration section to README.zh-CN.md
  - Document how to switch languages
  - Add screenshots of language switcher
  - **Validation**: Documentation clear and accurate

- [ ] **Add translation guide**
  - Create CONTRIBUTING.md section for translations
  - Document how to add new translations
  - Document translation workflow (.po → .mo)
  - Document how to extract new strings
  - **Validation**: Guide enables contributors to add translations

- [ ] **Update CHANGELOG**
  - Add i18n feature to CHANGELOG.md
  - Note languages supported (English, Chinese)
  - Document language configuration
  - **Validation**: CHANGELOG entry clear and complete

## Phase 6: Testing & Validation

- [ ] **Write unit tests**
  - Test i18n module translation loading
  - Test config language validation
  - Test fallback behavior
  - Test language switching
  - **Validation**: >80% code coverage on i18n module
  - **Validation**: All tests pass

- [ ] **Write integration tests**
  - Test CLI end-to-end in both languages
  - Test web UI end-to-end in both languages  
  - Test language persistence across sessions
  - Test backward compatibility (no language field)
  - **Validation**: Integration tests pass in both languages
  - **Validation**: No regressions in existing functionality

- [ ] **Manual testing**
  - Run all CLI commands in English
  - Run all CLI commands in Chinese
  - Test web UI navigation in English
  - Test web UI navigation in Chinese
  - Test language switcher functionality
  - Test on macOS, Linux, Windows (if applicable)
  - **Validation**: No visual/formatting issues
  - **Validation**: All features work in both languages

## Dependencies

- **Sequential**: Phase 1 must complete before Phase 2 and 3
- **Parallel**: Phase 2 (CLI) and Phase 3 (Web) can be done in parallel
- **Sequential**: Phase 4 (translation) requires Phase 2 and 3 complete
- **Sequential**: Phase 5 and 6 require Phase 4 complete

## Estimated Effort

- Phase 1: 4-6 hours (infrastructure setup)
- Phase 2: 4-6 hours (CLI i18n)
- Phase 3: 6-8 hours (Web i18n)
- Phase 4: 6-8 hours (translation content)
- Phase 5: 2-3 hours (documentation)
- Phase 6: 3-4 hours (testing)

**Total**: ~25-35 hours (~5 working days)
