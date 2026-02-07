# Design Document

## Context

The AI Skill Finder helps users discover relevant skills through semantic search, but currently stops at showing match results. Users need to manually open skill files in external editors to view full content. This change adds an integrated preview page that displays skill content with proper markdown formatting directly in the browser.

**Stakeholders:**
- End users who want to quickly preview skills before using them
- Development teams who need easy skill discovery and reference
- New users onboarding to the skill ecosystem

**Constraints:**
- Must work within existing FastAPI + HTMX + Tailwind CSS architecture
- Must not require additional backend dependencies
- Must handle file access securely
- Must work cross-platform (macOS, Linux, Windows)
- Must maintain existing AI Finder functionality without breaking changes

## Goals / Non-Goals

### Goals
- **Easy access**: One-click preview from search results
- **Rich formatting**: Proper markdown rendering matching GitHub style
- **Clear metadata**: Display license, compatibility information
- **Secure paths**: Prevent path traversal or unauthorized file access
- **Fast rendering**: Client-side processing for responsive UI
- **Error resilience**: Graceful handling of missing or invalid files

### Non-Goals (This Phase)
- Editing skill content through web UI
- Real-time collaboration on skills
- Version control integration
- Advanced syntax highlighting (basic code blocks only)
- Full-text search within preview
- Skill comparison view

## Decisions

### Decision 1: Path Encoding Strategy

**Options:**

**A) Plain file paths in URLs**
- **Pros**: Simple, human-readable URLs
- **Cons**: Exposes system structure, special characters cause issues
- **Cons**: Potential security risk with path traversal

**B) Base64-encoded paths**
- **Pros**: Obscures system structure, handles special characters
- **Pros**: URL-safe encoding
- **Cons**: URLs not human-readable (acceptable trade-off)

**C) Database-backed IDs**
- **Pros**: Most secure, clean URLs
- **Cons**: Requires database, significant complexity increase
- **Cons**: Out of scope for this phase

**Decision: Base64-encoded paths (Option B)**

**Rationale:**
- Balances security and simplicity
- No additional infrastructure needed
- URL-safe encoding handles all path characters
- Can add validation to restrict to `~/.agents/skills/` directory

### Decision 2: Markdown Rendering Approach

**Options:**

**A) Server-side rendering (Python markdown library)**
- **Pros**: Full control over HTML output
- **Pros**: Can sanitize content server-side
- **Cons**: Requires Python markdown library dependency
- **Cons**: Slower page loads, more server processing

**B) Client-side rendering (Marked.js)**
- **Pros**: Fast rendering, no server load
- **Pros**: Leverages browser capabilities
- **Pros**: No additional Python dependencies
- **Cons**: Requires JavaScript library (loaded from CDN)

**Decision: Client-side rendering with Marked.js (Option B)**

**Rationale:**
- Faster user experience (immediate rendering)
- Reduces server load
- Marked.js is mature, well-maintained, and lightweight
- CDN delivery means no installation or bundling needed
- Aligns with existing client-side architecture (HTMX)

### Decision 3: Preview Page Architecture

**Options:**

**A) Modal overlay on search page**
- **Pros**: Keeps user in search context
- **Cons**: Blocks search interface
- **Cons**: Complex state management
- **Cons**: Limited screen space

**B) Separate page (new tab)**
- **Pros**: Full screen for content viewing
- **Pros**: Preserves search results in original tab
- **Pros**: Simpler implementation
- **Cons**: Context switch between tabs

**C) Split-pane view**
- **Pros**: Both search and preview visible
- **Cons**: Cramped on smaller screens
- **Cons**: Complex responsive design

**Decision: Separate page opening in new tab (Option B)**

**Rationale:**
- Provides best viewing experience for markdown content
- Allows easy comparison between multiple skills (multiple tabs)
- Simpler to implement and maintain
- User can close tab to return to search
- Standard pattern users are familiar with

## Technical Architecture

### URL Structure

```
/preview/{encoded_path}

Example:
/preview/L1VzZXJzL3VzZXJuYW1lLy5hZ2VudHMvc2tpbGxzL2ludGVybmFsLWNvbW1zL1NLSUxMLm1k
```

**Encoding process:**
```python
import base64
encoded = base64.urlsafe_b64encode(path_string.encode()).decode()
```

**Decoding process:**
```python
decoded = base64.urlsafe_b64decode(encoded_string.encode()).decode()
```

### Component Flow

```
1. AI Finder Search
   ↓
2. Results with clickable skill names
   ↓
3. Click skill name → new tab with /preview/{encoded_path}
   ↓
4. FastAPI endpoint:
   - Decode path
   - Validate path is within ~/.agents/skills/
   - Read SKILL.md file
   - Parse metadata and body
   - Render preview.html template
   ↓
5. Browser:
   - Load Marked.js from CDN
   - Render markdown to HTML
   - Apply GitHub-style CSS
   ↓
6. User views formatted content
```

### Data Flow

**AI Finder Response (Enhanced):**
```json
{
  "success": true,
  "matches": [
    {
      "name": "internal-comms",
      "description": "Write internal communications...",
      "score": 0.96,
      "reasoning": "Matches weekly report writing...",
      "path": "/Users/user/.agents/skills/internal-comms/SKILL.md",
      "encoded_path": "L1VzZXJzL3VzZXIvLmFnZW50cy9za2lsbHMvaW50ZXJuYWwtY29tbXMvU0tJTEwubWQ="
    }
  ]
}
```

**Preview Page Template Context:**
```python
{
  "skill_name": "internal-comms",
  "description": "Write internal communications...",
  "content": "## What I do\n- Draft reports...",
  "metadata": {
    "license": "MIT",
    "compatibility": "cursor, claude, qoder"
  },
  "file_path": "/Users/user/.agents/skills/internal-comms/SKILL.md"
}
```

### Security Considerations

1. **Path Validation:**
   ```python
   def validate_skill_path(decoded_path: str) -> bool:
       skill_path = Path(decoded_path).resolve()
       hub_path = Path.home() / ".agents" / "skills"
       return skill_path.is_relative_to(hub_path) and skill_path.exists()
   ```

2. **Error Handling:**
   - Invalid base64: Return 404 error page
   - Path outside hub: Return "Access denied" error
   - File not found: Return "Skill not found" error
   - Parse error: Show raw content with warning

### Markdown Styling

GitHub-flavored markdown CSS includes:
- **Headings**: Font sizes, weights, bottom borders
- **Code blocks**: Background color, padding, monospace font
- **Lists**: Proper indentation and bullet styles
- **Blockquotes**: Left border, indentation, color
- **Links**: Color scheme, hover effects
- **Tables**: Border styling, alternating rows (if needed later)

## Implementation Plan

### Phase 1: Backend Endpoint
1. Add `/preview/{encoded_path}` route to FastAPI app
2. Implement path decoding and validation
3. Add file reading and parsing logic
4. Create error handling for edge cases

### Phase 2: Template Creation
1. Create `preview.html` Jinja2 template
2. Add Tailwind CSS layout structure
3. Include Marked.js CDN script
4. Add GitHub-flavored markdown CSS

### Phase 3: Integration
1. Modify AI Finder response to include `encoded_path`
2. Update `find.html` to use preview URLs instead of file:// links
3. Add `target="_blank"` for new tab behavior

### Phase 4: Testing
1. Test with various skill files (large, small, edge cases)
2. Verify cross-platform path handling
3. Test error scenarios (missing files, invalid paths)
4. Validate markdown rendering accuracy

## Testing Strategy

### Unit Tests
- Path encoding/decoding functions
- Path validation logic
- Metadata extraction from SKILL.md files

### Integration Tests
- End-to-end: AI Finder → Click → Preview page loads
- Error handling: Invalid paths, missing files
- Markdown rendering: Various markdown features

### Manual Tests
- Visual appearance across browsers (Chrome, Firefox, Safari)
- Responsive design on different screen sizes
- Link navigation (back button, browser back/forward)

## Trade-offs

### Simplicity vs. Features
- **Trade-off**: Basic markdown rendering without advanced features
- **Benefit**: Faster implementation, fewer dependencies
- **Decision**: Start simple, add features based on user feedback

### Security vs. Convenience
- **Trade-off**: Base64 encoding makes URLs less readable
- **Benefit**: Prevents path exposure and traversal attacks
- **Decision**: Security takes priority over URL readability

### Client-side vs. Server-side Rendering
- **Trade-off**: Requires JavaScript to view content
- **Benefit**: Better performance, no server processing
- **Decision**: Accept JavaScript requirement (already present in web UI)
