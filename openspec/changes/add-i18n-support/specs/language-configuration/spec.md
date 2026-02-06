# Spec: Language Configuration

## ADDED Requirements

### Requirement: System SHALL store user's language preference in configuration

The system SHALL store user's language preference in the configuration file and use it across all interfaces.

#### Scenario: Add language field to configuration

**Given** the application starts for the first time  
**When** the configuration is loaded  
**Then** it must include a `language` field with type string  
**And** it must default to `"en"` if not specified  
**And** it must support values: `"en"` (English) and `"zh_CN"` (Simplified Chinese)

#### Scenario: Save language preference

**Given** user is changing their language preference  
**When** the new language is saved  
**Then** the system must persist the new language to `~/.skills/.skill-hub/config.json`  
**And** it must validate the language code is supported  
**And** it must reject invalid language codes with clear error message

#### Scenario: Load language on startup

**Given** a configuration file exists with a language preference  
**When** the application starts (CLI or web)  
**Then** it must read the language preference from config  
**And** it must initialize the translation system with that language  
**And** it must fall back to English if language not found

### Requirement: System SHALL maintain backward compatibility with existing configurations

The system SHALL maintain backward compatibility with existing configurations that do not have a language field.

#### Scenario: Missing language field

**Given** a configuration file without `language` field  
**When** loading the configuration  
**Then** the system must default to `"en"` (English)  
**And** it must NOT fail or show errors  
**And** it must continue normal operation

#### Scenario: Invalid language code

**Given** a configuration contains unsupported language code  
**When** the configuration is loaded  
**Then** the system must log a warning  
**And** it must fall back to `"en"` (English)  
**And** it must continue normal operation

### Requirement: System SHALL validate language codes

The system SHALL validate language codes to prevent configuration errors.

#### Scenario: Supported language codes

**Given** validating language preference  
**When** the language code is checked  
**Then** it must accept `"en"` for English  
**And** it must accept `"zh_CN"` for Simplified Chinese  
**And** it must reject any other values

#### Scenario: Case sensitivity

**Given** comparing language codes  
**When** validation occurs  
**Then** it must treat codes as case-sensitive  
**And** it must accept `"zh_CN"` but reject `"zh_cn"` or `"ZH_CN"`
