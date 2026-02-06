# Spec: Web Interface Internationalization

## ADDED Requirements

### Requirement: Web interface SHALL display all UI text in configured language

The web interface SHALL display all UI text in the configured language with ability to switch languages at runtime.

#### Scenario: Initialize translation for web requests

**Given** a user accesses the web interface  
**When** a web page is loaded  
**Then** the system must check language preference from cookie or config  
**And** it must render templates with Jinja2 i18n extension  
**And** it must pass current language to template context

#### Scenario: Translate template strings

**Given** rendering HTML templates  
**When** generating the HTML output  
**Then** all user-facing text must use Jinja2 `{{ _("text") }}` syntax  
**And** it must display translated text for current language  
**And** it must preserve HTML structure and attributes

#### Scenario: Translate dynamic content

**Given** backend generates HTML fragments (HTMX responses)  
**When** creating dynamic content  
**Then** dynamic content must be translated using Python gettext  
**And** it must use the request's language preference  
**And** it must maintain consistency with page language

### Requirement: Web interface SHALL provide visible language switcher

The web interface SHALL provide a visible language switcher for users to change languages.

#### Scenario: Display language switcher

**Given** user accesses any page  
**When** the page is rendered  
**Then** a language switcher must be visible in the UI (typically header/nav)  
**And** it must show available languages: "English" and "中文"  
**And** it must highlight the currently selected language

#### Scenario: Switch language via UI

**Given** user wants to change language  
**When** user clicks a language option  
**Then** the system must send POST request to `/set-language` endpoint  
**And** it must update language preference in config file  
**And** it must set a language cookie with 1-year expiration  
**And** it must reload the page displaying new language

#### Scenario: Persist language across sessions

**Given** user has previously selected a language  
**When** user returns to web interface after switching language  
**Then** the system must remember their language choice via cookie  
**And** it must display content in previously selected language  
**And** it must NOT require re-selection on each visit

### Requirement: Web interface SHALL determine language using priority order

The web interface SHALL determine display language using a clear priority order.

#### Scenario: Language priority order

**Given** determining which language to display  
**When** the system checks language preferences  
**Then** it must check in this order:
  1. Language cookie (if present)
  2. Config file language setting
  3. Browser Accept-Language header
  4. Default to English  
**And** it must use the first available valid language from priority list

#### Scenario: Cookie takes precedence

**Given** both cookie and config specify different languages  
**When** rendering the page  
**Then** the system must use the language from cookie  
**And** it must sync cookie value to config on next language change  
**And** it must maintain cookie as source of truth for web sessions

### Requirement: Web interface SHALL use gettext-compatible translation files

The web interface SHALL use gettext-compatible translation files organized by language.

#### Scenario: Translation file organization

**Given** loading translations for web interface  
**When** the system initializes  
**Then** it must look for files in `locales/{lang}/LC_MESSAGES/messages.mo`  
**And** it must support `en` (English) and `zh_CN` (Simplified Chinese)  
**And** it must fall back to English if requested language not found

#### Scenario: Template translation extraction

**Given** extracting strings for translation  
**When** running extraction tools  
**Then** the system must identify all `{{ _("text") }}` occurrences in templates  
**And** it must include them in `messages.pot` template file  
**And** it must preserve context and formatting

### Requirement: Web interface SHALL handle missing translations gracefully

The web interface SHALL handle missing translations gracefully without breaking the UI.

#### Scenario: Missing translation in template

**Given** a template string has no translation  
**When** rendering the page  
**Then** the system must display the original English text  
**And** it must NOT show error messages in UI  
**And** it must render the page successfully

#### Scenario: Invalid language cookie

**Given** language cookie contains unsupported language code  
**When** processing the request  
**Then** the system must ignore the cookie  
**And** it must fall back to config or default language  
**And** it must set a valid cookie on next language change

### Requirement: Web interface SHALL translate HTML attributes

The web interface SHALL translate HTML attributes including tooltips and accessibility labels.

#### Scenario: Translate title attributes

**Given** elements have `title` attributes for tooltips  
**When** rendering the HTML  
**Then** tooltip text must be translated to current language  
**And** it must use Jinja2 translation syntax: `title="{{ _('Tooltip text') }}"`

#### Scenario: Translate accessibility labels

**Given** elements have ARIA labels for accessibility  
**When** rendering the page  
**Then** labels must be translated to current language  
**And** screen readers must announce translated text  
**And** it must maintain ARIA compliance

### Requirement: Web interface SHALL respect language-specific formatting

The web interface SHALL respect language-specific formatting conventions where applicable.

#### Scenario: Number formatting

**Given** displaying numeric values (counts, percentages)  
**When** rendering numbers  
**Then** English must use comma as thousands separator (1,000)  
**And** Chinese must use comma as thousands separator (1,000)  
**And** formatting must be consistent within each language

#### Scenario: Date display

**Given** displaying dates or timestamps  
**When** rendering date information  
**Then** the system may use locale-specific date formats  
**And** it must remain readable in both languages  
**And** it may default to ISO 8601 format if localization complex
