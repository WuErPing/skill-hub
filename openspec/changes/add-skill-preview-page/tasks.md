# Tasks

## 1. Backend: Preview Endpoint

- [x] 1.1 Add `/preview/{encoded_path}` route to FastAPI application
  - Define route with path parameter
  - Add async function signature
  - Return HTMLResponse type
  
- [x] 1.2 Implement base64 path decoding
  - Import base64 module
  - Decode encoded_path using urlsafe_b64decode
  - Handle decoding exceptions gracefully
  
- [x] 1.3 Add path validation logic
  - Check decoded path is within `~/.agents/skills/`
  - Use Path.is_relative_to() for validation
  - Return 403/404 for invalid paths
  
- [x] 1.4 Implement file reading and parsing
  - Check if file exists
  - Read file content with UTF-8 encoding
  - Call parse_skill_file_from_path utility
  - Extract metadata and body content
  
- [x] 1.5 Add error handling for edge cases
  - Handle file not found (404)
  - Handle parse errors (show raw content with warning)
  - Handle permission errors
  - Return user-friendly error messages
  
- [x] 1.6 Render template with skill data
  - Pass skill_name, description, content, metadata to template
  - Include file_path for reference
  - Return rendered HTML response

## 2. Frontend: Preview Template

- [x] 2.1 Create preview.html Jinja2 template
  - Add DOCTYPE and HTML structure
  - Set proper meta tags (charset, viewport)
  - Add page title using skill_name
  
- [x] 2.2 Design header section
  - Add back button with arrow icon and window.history.back()
  - Display skill name as h1
  - Show description subtitle
  - Add "Skill" badge for visual indication
  
- [x] 2.3 Create metadata card component
  - Conditional rendering based on metadata availability
  - Two-column grid layout for license and compatibility
  - Use proper label/value formatting
  - Apply border and background styling
  
- [x] 2.4 Add markdown content container
  - Create div with id="markdown-content"
  - Apply .markdown-body class for styling
  - Ensure proper spacing around content
  
- [x] 2.5 Display file path footer
  - Show source file path in monospace font
  - Use muted color for secondary information
  - Add file icon for visual clarity
  
- [x] 2.6 Include Marked.js from CDN
  - Add script tag for Marked.js library
  - Use CDN URL: https://cdn.jsdelivr.net/npm/marked/marked.min.js
  - Ensure script loads before rendering code

## 3. Frontend: Markdown Styling

- [x] 3.1 Add GitHub-flavored markdown CSS
  - Create inline style block in template
  - Define .markdown-body class with base styles
  - Set font-family and line-height
  
- [x] 3.2 Style headings (h1, h2, h3)
  - Set font sizes (2em, 1.5em, 1.25em)
  - Add font-weight 600
  - Add bottom borders for h1 and h2
  - Define proper margins
  
- [x] 3.3 Style code elements
  - Inline code: background, padding, border-radius
  - Code blocks (pre): background #f6f8fa, padding, overflow
  - Use monospace font family
  - Ensure horizontal scrolling for long lines
  
- [x] 3.4 Style lists and list items
  - Set left padding to 2em
  - Add 4px top margin to list items
  - Maintain proper nesting indentation
  
- [x] 3.5 Style blockquotes
  - Add left border (0.25em solid #d0d7de)
  - Set left padding to 1em
  - Use muted text color (#57606a)
  
- [x] 3.6 Style links
  - Set color to #0969da (blue)
  - Remove default underline
  - Add underline on hover
  - Ensure accessibility contrast

## 4. Integration: AI Finder to Preview

- [x] 4.1 Update AI Finder POST /find endpoint
  - Add base64 encoding for skill paths
  - Include encoded_path in match results
  - Use base64.urlsafe_b64encode(path.encode()).decode()
  
- [x] 4.2 Modify find.html template
  - Change skill name from plain text to anchor tag
  - Use /preview/{encoded_path} as href
  - Add target="_blank" to open in new tab
  - Update tooltip text to "Preview {skill_name}"
  
- [x] 4.3 Add visual indication for clickable names
  - Style skill names as links (blue color)
  - Add hover underline effect
  - Maintain existing layout and spacing

## 5. JavaScript: Client-side Rendering

- [x] 5.1 Add markdown rendering script
  - Get markdown content from template variable
  - Use {{ content|tojson }} to pass data safely
  - Call marked.parse() on page load
  
- [x] 5.2 Insert rendered HTML into page
  - Select #markdown-content element
  - Set innerHTML with rendered markdown
  - Ensure rendering completes before display
  
- [x] 5.3 Handle edge cases in JavaScript
  - Check if markdownContent is defined
  - Handle null or empty content
  - Prevent JavaScript errors on malformed data

## 6. Testing and Validation

- [x] 6.1 Unit test path encoding/decoding
  - Test base64 encoding produces URL-safe strings
  - Test decoding restores original paths
  - Test handling of special characters in paths
  
- [x] 6.2 Unit test path validation
  - Test paths within hub are accepted
  - Test paths outside hub are rejected
  - Test relative path attempts are blocked
  
- [x] 6.3 Integration test: Search to preview flow
  - Start from AI Finder search
  - Click skill name in results
  - Verify preview page opens in new tab
  - Check markdown rendering is correct
  
- [x] 6.4 Test error scenarios
  - Test with missing skill files (404)
  - Test with invalid base64 encoding (400)
  - Test with paths outside hub (403)
  - Test with malformed SKILL.md files
  
- [x] 6.5 Manual testing across browsers
  - Test in Chrome (latest)
  - Test in Firefox (latest)
  - Test in Safari (macOS)
  - Verify consistent rendering
  
- [x] 6.6 Responsive design testing
  - Test on desktop (1920x1080)
  - Test on tablet (768x1024)
  - Test on mobile (375x667)
  - Verify layout adapts properly

## 7. Documentation

- [x] 7.1 Update user documentation
  - Document preview feature in README
  - Add usage instructions
  - Include screenshots if needed
  
- [x] 7.2 Add inline code comments
  - Comment path validation logic
  - Document base64 encoding/decoding
  - Explain template context structure

## Dependencies

- Task 4 (Integration) depends on Tasks 1 and 2 (Backend and Template)
- Task 5 (JavaScript) depends on Task 2 (Template structure)
- Task 6 (Testing) depends on Tasks 1-5 (all implementation)

## Parallelizable Work

- Tasks 1 (Backend) and 2 (Frontend) can be developed in parallel
- Task 3 (Styling) can be done alongside Task 2
- Task 7 (Documentation) can be written in parallel with implementation
