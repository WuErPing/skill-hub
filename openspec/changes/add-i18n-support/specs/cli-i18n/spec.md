# Spec: CLI Internationalization

## ADDED Requirements

### Requirement: CLI SHALL display all user-facing text in configured language

The CLI SHALL display all user-facing text in the configured language using Python gettext.

#### Scenario: Initialize translation on startup

**Given** the CLI application is starting  
**When** any CLI command is executed  
**Then** the system must load the configured language from config  
**And** it must initialize gettext with the appropriate translation catalog  
**And** it must use English as fallback if translation not available

#### Scenario: Translate command output

**Given** CLI is displaying output messages  
**When** rendering text to console  
**Then** all user-facing text must be wrapped in translation function `_()`  
**And** it must display translated text for configured language  
**And** it must preserve formatting placeholders (e.g., `{count}`, `{name}`)

#### Scenario: Translate error messages

**Given** an error has occurred  
**When** CLI displays error messages  
**Then** error text must be translated to configured language  
**And** technical details (file paths, stack traces) must remain in English  
**And** error codes must remain language-independent

### Requirement: CLI SHALL provide translated help text

The CLI SHALL provide translated help text for all commands and options.

#### Scenario: Translate command descriptions

**Given** user requests help  
**When** user runs `skill-hub --help` or `skill-hub COMMAND --help`  
**Then** command descriptions must display in configured language  
**And** option descriptions must display in configured language  
**And** usage examples must use translated messages

#### Scenario: Preserve command names

**Given** displaying help or running commands  
**When** rendering command interface  
**Then** command names must remain in English (e.g., `sync`, `discover`)  
**And** option flags must remain in English (e.g., `--pull`, `--verbose`)  
**And** only descriptive text must be translated

### Requirement: CLI SHALL gracefully handle missing translations

The CLI SHALL gracefully handle missing translations without errors.

#### Scenario: Missing translation

**Given** a message has no translation in configured language  
**When** attempting to display the message  
**Then** the system must display the English original text  
**And** it must NOT show error messages or warnings to user  
**And** it must continue normal operation

#### Scenario: Translation file not found

**Given** translation file for configured language is missing  
**When** initializing translations  
**Then** the system must log a debug message  
**And** it must fall back to English for all messages  
**And** it must NOT prevent command execution

### Requirement: CLI SHALL correctly translate dynamic content

The CLI SHALL correctly translate messages with dynamic content and formatting.

#### Scenario: Formatted messages

**Given** displaying messages with variables (e.g., counts, names)  
**When** rendering the message  
**Then** the system must use Python string formatting with placeholders  
**And** placeholder names must be preserved in translations  
**And** values must be substituted correctly regardless of language

#### Scenario: Pluralization

**Given** displaying counts (e.g., "1 skill" vs "2 skills")  
**When** formatting the message  
**Then** English must use standard pluralization rules  
**And** Chinese must use singular form (no plural distinction)  
**And** formatting must be grammatically correct for each language
