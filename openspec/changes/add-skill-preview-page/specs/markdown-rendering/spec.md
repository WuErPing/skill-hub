# Spec: Markdown Rendering

## ADDED Requirements

### Requirement: Preview page SHALL render markdown content using client-side library

The system SHALL use Marked.js library loaded from CDN to convert markdown to HTML in the browser.

#### Scenario: Load Marked.js from CDN

**Given** a preview page is rendered  
**When** the HTML is loaded in the browser  
**Then** the page must include a script tag loading Marked.js from CDN  
**And** the CDN URL must be `https://cdn.jsdelivr.net/npm/marked/marked.min.js` or equivalent  
**And** the script must load before markdown rendering code executes

#### Scenario: Convert markdown to HTML on page load

**Given** markdown content is passed to the template in `{{ content|tojson }}`  
**When** the page loads in the browser  
**Then** JavaScript must call `marked.parse(markdownContent)`  
**And** the result must be inserted into `#markdown-content` element's innerHTML  
**And** the rendering must complete before page is visible to user

#### Scenario: Handle empty or null markdown content

**Given** a skill file with no body content (only frontmatter)  
**When** the preview page loads  
**Then** the markdown rendering must not throw JavaScript errors  
**And** the content area must remain empty or show "No content available" message  
**And** the page must still display metadata normally

### Requirement: Preview page SHALL apply GitHub-flavored markdown styles

The system SHALL use CSS to style rendered markdown with appearance similar to GitHub.

#### Scenario: Style headings with hierarchy

**Given** markdown content with h1, h2, h3 headings  
**When** the content is rendered  
**Then** h1 must use 2em font-size and bottom border  
**And** h2 must use 1.5em font-size and bottom border  
**And** h3 must use 1.25em font-size without border  
**And** all headings must use 600 font-weight

#### Scenario: Style code blocks with background

**Given** markdown content with inline code and code blocks  
**When** the content is rendered  
**Then** inline `code` must have gray background and rounded corners  
**And** code blocks (pre > code) must have light gray background (#f6f8fa)  
**And** code must use monospace font family  
**And** code blocks must have padding and horizontal scrolling

#### Scenario: Style lists with proper indentation

**Given** markdown content with bullet and numbered lists  
**When** the content is rendered  
**Then** lists must have 2em left padding  
**And** list items must have 4px top margin  
**And** nested lists must maintain proper indentation hierarchy

#### Scenario: Style blockquotes with left border

**Given** markdown content with blockquotes  
**When** the content is rendered  
**Then** blockquotes must have 0.25em solid left border (#d0d7de)  
**And** blockquotes must have 1em left padding  
**And** blockquote text must use muted color (#57606a)

#### Scenario: Style links with hover effects

**Given** markdown content with hyperlinks  
**When** the content is rendered  
**Then** links must use blue color (#0969da)  
**And** links must have no underline by default  
**And** links must show underline on hover  
**And** links must maintain color contrast for accessibility

### Requirement: Preview page SHALL display skill metadata in dedicated section

The system SHALL show skill metadata (license, compatibility) in a separate card above the markdown content.

#### Scenario: Display metadata card with license

**Given** a skill with license "MIT"  
**When** the preview page is rendered  
**Then** a metadata card must appear above the main content  
**And** the card must show "License: MIT" label and value  
**And** the label must use gray color for emphasis  
**And** the value must use darker color for readability

#### Scenario: Display metadata card with compatibility

**Given** a skill with compatibility "cursor, claude, qoder"  
**When** the preview page is rendered  
**Then** the metadata card must show "Compatibility: cursor, claude, qoder"  
**And** the compatibility list must be clearly formatted  
**And** the card must use a two-column grid layout

#### Scenario: Hide metadata card when no metadata available

**Given** a skill with no license or compatibility fields  
**When** the preview page is rendered  
**Then** the metadata card must not be displayed  
**And** the markdown content must be positioned directly below the header  
**And** no empty placeholder card must be shown

### Requirement: Preview page SHALL be responsive across screen sizes

The system SHALL use responsive design to ensure preview pages work on desktop, tablet, and mobile devices.

#### Scenario: Constrain content width on large screens

**Given** a preview page displayed on a desktop monitor (1920px+)  
**When** the page is rendered  
**Then** the main content must have max-width of 5xl (1024px)  
**And** the content must be centered horizontally  
**And** there must be padding on left and right sides

#### Scenario: Adapt to mobile screens

**Given** a preview page displayed on a mobile device (< 768px)  
**When** the page is rendered  
**Then** the content must use full width with appropriate padding  
**And** font sizes must remain readable without zooming  
**And** the back button must remain accessible  
**And** code blocks must support horizontal scrolling

#### Scenario: Maintain readability with proper line height

**Given** any screen size  
**When** markdown content is rendered  
**Then** the text must have line-height of at least 1.6  
**And** paragraphs must have 16px bottom margin  
**And** the font must be system default or similar readable font
