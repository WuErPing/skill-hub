# Web Interface Screenshots

This directory contains screenshots of the skill-hub web interface.

## Required Screenshots

Please add the following screenshots by running the web interface and capturing these pages:

1. **dashboard.png** - Dashboard page showing:
   - Skill count, repository count, and status cards
   - `.agents/skills/` feature banner
   - Quick actions (Add Anthropic Repo, Pull from Repos, Health Check)
   - Getting Started guide

2. **skill-preview.png** - Skill preview page showing:
   - Skill name and description in header
   - Back button for navigation
   - Metadata card with license and compatibility
   - Markdown-rendered content (headings, code blocks, lists)
   - Source file path
   - Example: Open any skill from Hub Skills or AI Skill Finder pages

3. **agents-health.png** - Agents page with health check results showing:
   - List of agent adapters
   - Health check button clicked
   - Health results table with agent status, global paths, and shared skills detection
   - Info banner about shared skills

4. **skills-hub.png** - Skills page showing:
   - List of skills in the central hub (~/.agents/skills/)
   - Skill names as clickable links (blue, underlined on hover)
   - Discovery info banner
   - Refresh button

5. **ai-skill-finder.png** - AI Skill Finder page showing:
   - Search input with example query
   - Search results with clickable skill names
   - Match scores with progress bars
   - "Why this matches" expandable details

6. **sync.png** - Sync page showing:
   - Three sync buttons (Sync, Pull only, Push only)
   - Sync results area

## How to Capture Screenshots

1. Start the web interface:
   ```bash
   skill-hub web
   ```

2. Navigate to each page and capture screenshots
3. Save them in this directory with the names listed above
4. Recommended resolution: 1200x800 or larger
5. Format: PNG with good quality

## Screenshot Guidelines

- **Skill Preview Page**: 
  - Open from Hub Skills page by clicking a skill name
  - Shows markdown rendering with proper styling
  - Include metadata section if available
  - Show file path at bottom

- **Hub Skills Page**:
  - Show skill names as blue clickable links
  - Include at least 3-5 skills in the list
  - Show the info banner about discovery

- **AI Skill Finder Page**:
  - Enter a query like "git workflow" or "testing"
  - Show search results with match scores
  - Display clickable skill names

## Optional: Use a Tool

You can use browser developer tools or screenshot utilities:
- Chrome DevTools: Device Mode for consistent viewport
- macOS: Cmd+Shift+4 for selection
- Windows: Win+Shift+S for Snipping Tool
- Linux: Various screenshot tools available
