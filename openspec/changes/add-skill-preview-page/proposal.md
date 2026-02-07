# Proposal: Add Skill Preview Page with Markdown Rendering

## Why

The AI Skill Finder currently displays search results with skill names, descriptions, and matching scores, but users cannot easily view the full skill content without opening the file in an external editor. This creates friction when:

- **Evaluating skills**: Users want to see complete skill instructions before deciding to use them
- **Quick reference**: Developers need to quickly check skill details without leaving the browser
- **Onboarding**: New team members exploring available skills need an easy way to preview content
- **Mobile/remote access**: Users working in browser-only environments cannot open local files

A dedicated skill preview page with markdown rendering solves these problems by providing an in-browser viewing experience that displays skill content with proper formatting, metadata, and easy navigation.

## What Changes

This change introduces a skill preview capability for AI Skill Finder results with two core components:

1. **Preview Endpoint**: HTTP endpoint that accepts encoded skill file paths and serves preview pages
   - Accept base64-encoded file paths as URL parameters
   - Read and parse SKILL.md files from the hub
   - Extract metadata (name, description, license, compatibility)
   - Render full preview page with navigation controls

2. **Markdown Rendering**: Client-side markdown rendering with GitHub-style formatting
   - Integrate Marked.js for markdown-to-HTML conversion
   - Apply GitHub-flavored markdown styles (headings, code blocks, lists, blockquotes)
   - Display skill metadata in dedicated card
   - Show source file path for reference
   - Provide back button for easy navigation

## Scope

### In Scope
- Preview page accessible from AI Skill Finder results
- Base64 URL encoding for secure path transmission
- Markdown rendering with GitHub-style formatting
- Metadata display (license, compatibility)
- Error handling for missing or invalid files
- Responsive design for all screen sizes

### Out of Scope
- Real-time markdown editing
- Skill content modification through web UI
- Version history or diff viewing
- Collaborative editing features
- Syntax highlighting for code blocks (can be added later)

## Success Criteria

1. Users can click skill names in AI Finder results to open preview
2. Preview page opens in new tab without losing search context
3. Markdown content renders with proper formatting (headings, lists, code blocks)
4. Skill metadata displays clearly above content
5. Users can navigate back to search results easily
6. System handles missing files gracefully with error messages

## Dependencies

- Existing AI Skill Finder functionality
- FastAPI web framework (already in use)
- Jinja2 templates (already in use)
- Marked.js library (CDN, no installation needed)

## Risks

- **Security**: File paths in URLs could expose system structure
  - Mitigation: Use base64 encoding to obscure paths
  - Validation: Only allow paths within `~/.agents/skills/`

- **Performance**: Large skill files may slow rendering
  - Mitigation: Client-side rendering reduces server load
  - Future: Add file size limits if needed

## Alternatives Considered

1. **file:// protocol links**: Simple but doesn't work in browsers
2. **Inline expansion**: Would clutter search results
3. **Modal overlay**: Would block search results interface
4. **Server-side rendering**: More complex, slower than client-side

Chosen approach (separate page with client-side rendering) balances simplicity, performance, and user experience.
