# Spec: Skill Preview Endpoint

## ADDED Requirements

### Requirement: Web server SHALL provide HTTP endpoint for skill preview

The system SHALL expose a `/preview/{encoded_path}` endpoint that accepts base64-encoded skill file paths and returns HTML preview pages.

#### Scenario: Accept base64-encoded path parameter

**Given** a skill file exists at `/Users/user/.agents/skills/my-skill/SKILL.md`  
**When** the encoded path `L1VzZXJzL3VzZXIvLmFnZW50cy9za2lsbHMvbXktc2tpbGwvU0tJTEwubWQ=` is requested  
**Then** the system must decode the path using base64.urlsafe_b64decode  
**And** it must resolve to the original file path  
**And** it must return HTTP 200 with preview page HTML

#### Scenario: Validate decoded path is within hub directory

**Given** a decoded path is `/etc/passwd` (outside hub)  
**When** the preview endpoint processes the request  
**Then** the system must detect the path is not within `~/.agents/skills/`  
**And** it must return HTTP 403 or 404 error page  
**And** it must not read or expose the file content

#### Scenario: Handle file not found

**Given** a valid encoded path that decodes to a non-existent file  
**When** the preview endpoint attempts to read the file  
**Then** the system must detect the file does not exist  
**And** it must return HTTP 404 with user-friendly error message  
**And** the error must include "Skill file not found" text

#### Scenario: Handle invalid base64 encoding

**Given** an invalid base64 string in the URL path  
**When** the preview endpoint attempts to decode it  
**Then** the system must catch the decoding exception  
**And** it must return HTTP 400 with error message "Invalid path encoding"  
**And** it must not expose raw exception details to user

### Requirement: Endpoint SHALL parse skill file and extract components

The system SHALL read SKILL.md files, parse frontmatter metadata, and separate body content for rendering.

#### Scenario: Extract metadata from frontmatter

**Given** a SKILL.md file with YAML frontmatter:
```markdown
---
name: my-skill
description: A test skill
license: MIT
compatibility: cursor, claude
---
## Content
Body text here
```  
**When** the preview endpoint parses the file  
**Then** the system must extract `name` as "my-skill"  
**And** it must extract `description` as "A test skill"  
**And** it must extract `license` as "MIT"  
**And** it must extract `compatibility` as "cursor, claude"  
**And** it must extract body content starting from "## Content"

#### Scenario: Handle files without optional metadata fields

**Given** a SKILL.md file with only required fields (name, description)  
**When** the preview endpoint parses the file  
**Then** the system must successfully extract required fields  
**And** it must set optional fields (license, compatibility) to None or empty  
**And** it must still render the preview page without errors

#### Scenario: Handle malformed SKILL.md files

**Given** a SKILL.md file with invalid YAML frontmatter  
**When** the preview endpoint attempts to parse it  
**Then** the system must detect the parse failure  
**And** it must return preview page with error message "Failed to parse skill file"  
**And** it must optionally display raw file content as fallback  
**And** it must not crash or return HTTP 500

### Requirement: Endpoint SHALL render preview using template

The system SHALL use Jinja2 templates to generate HTML preview pages with skill content.

#### Scenario: Render preview template with skill data

**Given** successfully parsed skill metadata and body content  
**When** the preview endpoint renders the response  
**Then** the system must use `preview.html` Jinja2 template  
**And** it must pass skill_name, description, content, metadata, and file_path to template  
**And** it must return HTML with proper content-type header  
**And** the HTML must include markdown content in a designated container element

#### Scenario: Include file path reference

**Given** a skill file at `/Users/user/.agents/skills/git-workflow/SKILL.md`  
**When** the preview page is rendered  
**Then** the page must display the source file path  
**And** the path must be shown in a footer or info section  
**And** the path must use monospace font for readability

#### Scenario: Provide navigation back button

**Given** a preview page is displayed  
**When** the page HTML is rendered  
**Then** the page must include a back button in the header  
**And** the button must use `window.history.back()` JavaScript  
**And** the button must have clear visual indication (arrow icon or text)
