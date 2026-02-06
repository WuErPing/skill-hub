# Design: Internationalization (i18n) Support

## Architecture Overview

The i18n system will use Python's standard `gettext` module for translation management, with language preference stored in the user's configuration file. The system will support two languages initially: English (en) and Simplified Chinese (zh-CN).

### Translation File Structure

```
skill_hub/
├── locales/
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po    # Source translations
│   │       └── messages.mo    # Compiled translations
│   └── zh_CN/
│       └── LC_MESSAGES/
│           ├── messages.po
│           └── messages.mo
├── i18n.py               # Translation utilities
└── ...
```

## Component Changes

### 1. Configuration Model

**Current:**
```python
class Config:
    version: str
    conflict_resolution: str
    agents: Dict[str, AgentConfig]
    repositories: List[RepositoryConfig]
    sync: Dict
```

**Proposed:**
```python
class Config:
    version: str
    language: str = "en"  # NEW: Default to English
    conflict_resolution: str
    agents: Dict[str, AgentConfig]
    repositories: List[RepositoryConfig]
    sync: Dict
```

### 2. Translation Utility Module

Create `src/skill_hub/i18n.py`:

```python
import gettext
import os
from pathlib import Path
from typing import Optional

_translator: Optional[gettext.GNUTranslations] = None
_current_language: str = "en"

def init_translation(language: str = "en") -> None:
    """Initialize translation system with specified language."""
    global _translator, _current_language
    
    locales_dir = Path(__file__).parent / "locales"
    try:
        _translator = gettext.translation(
            "messages",
            localedir=str(locales_dir),
            languages=[language],
            fallback=True
        )
        _current_language = language
    except Exception:
        # Fallback to NullTranslations (returns original strings)
        _translator = gettext.NullTranslations()
        _current_language = "en"

def _(message: str) -> str:
    """Translate message to current language."""
    if _translator is None:
        init_translation()
    return _translator.gettext(message)

def get_current_language() -> str:
    """Get currently configured language."""
    return _current_language
```

### 3. CLI Integration

**Update `cli.py`:**

```python
from skill_hub.i18n import _, init_translation
from skill_hub.utils import ConfigManager

@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """skill-hub: Unified skill management for AI coding agents."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    
    # Load config and initialize translation
    config_manager = ConfigManager()
    config = config_manager.load(silent=True)
    init_translation(config.language)
    
    # Now all console.print() calls can use _() for translation
    console.print(_("Discovering skills..."))
```

### 4. Web Interface Integration

**Update `fastapi_app.py`:**

```python
from skill_hub.i18n import _, init_translation, get_current_language
from fastapi import Request, Cookie
from fastapi.responses import JSONResponse

def create_app() -> FastAPI:
    app = FastAPI(title="skill-hub", version="1.0.0")
    
    # Middleware to set language from cookie or config
    @app.middleware("http")
    async def language_middleware(request: Request, call_next):
        # Get language from cookie or config
        lang = request.cookies.get("language", "en")
        init_translation(lang)
        response = await call_next(request)
        return response
    
    # Add language switcher endpoint
    @app.post("/set-language")
    async def set_language(request: Request) -> JSONResponse:
        form = await request.form()
        language = form.get("language", "en")
        
        # Update config
        config = _load_config()
        config.language = language
        config_manager.save(config)
        
        # Return response with cookie
        response = JSONResponse({"success": True, "language": language})
        response.set_cookie("language", language, max_age=31536000)  # 1 year
        return response
```

**Update templates with Jinja2 i18n:**

```html
<!-- index.html -->
{% extends "base.html" %}

{% block content %}
<div class="flex items-center justify-between mb-4">
    <h1>{{ _("skill-hub") }}</h1>
    
    <!-- Language Switcher -->
    <div class="flex gap-2">
        <button onclick="setLanguage('en')" 
                class="px-3 py-1 rounded {{ 'bg-blue-600 text-white' if language == 'en' else 'bg-gray-200' }}">
            English
        </button>
        <button onclick="setLanguage('zh_CN')" 
                class="px-3 py-1 rounded {{ 'bg-blue-600 text-white' if language == 'zh_CN' else 'bg-gray-200' }}">
            中文
        </button>
    </div>
</div>

<script>
function setLanguage(lang) {
    fetch('/set-language', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'language=' + lang
    }).then(() => location.reload());
}
</script>
{% endblock %}
```

## Translation Workflow

### 1. Extract Translatable Strings

Use `xgettext` or manual extraction to create `.pot` template:

```bash
# Extract from Python files
find src/skill_hub -name "*.py" -exec xgettext -L Python -o locales/messages.pot {} +

# Extract from templates
pybabel extract -F babel.cfg -o locales/messages.pot .
```

### 2. Create Language Files

```bash
# Initialize English (reference)
msginit -i locales/messages.pot -o locales/en/LC_MESSAGES/messages.po -l en

# Initialize Chinese
msginit -i locales/messages.pot -o locales/zh_CN/LC_MESSAGES/messages.po -l zh_CN
```

### 3. Translate

Edit `.po` files manually:

```po
# locales/zh_CN/LC_MESSAGES/messages.po
msgid "Discovering skills..."
msgstr "正在发现技能..."

msgid "Hub Skills"
msgstr "中心技能"

msgid "Add Anthropic Repo"
msgstr "添加 Anthropic 仓库"
```

### 4. Compile

```bash
# Compile all translations
msgfmt locales/en/LC_MESSAGES/messages.po -o locales/en/LC_MESSAGES/messages.mo
msgfmt locales/zh_CN/LC_MESSAGES/messages.po -o locales/zh_CN/LC_MESSAGES/messages.mo
```

## Language Priority

1. **Web Interface**: Cookie > Config file > Browser header > Default (en)
2. **CLI**: Config file > Environment variable (`LANG`) > Default (en)

## String Formatting

Use Python string formatting for dynamic values:

```python
# Code
console.print(_("Found {count} skills").format(count=len(skills)))

# Translation file
msgid "Found {count} skills"
msgstr "发现 {count} 个技能"
```

## Testing Strategy

### Unit Tests

1. Test translation loading for both languages
2. Test fallback to English when translation missing
3. Test language switching in web interface
4. Test config save/load with language preference

### Integration Tests

1. Run CLI commands in both languages
2. Verify web interface displays correct language
3. Test language switching persists across sessions

## Backward Compatibility

- Language field is optional in config; defaults to "en"
- Existing configs without language field continue to work
- No changes to CLI command structure or options
- Web interface works without language preference set

## Performance Considerations

- Translations loaded once at startup
- Compiled `.mo` files used (not `.po` text files)
- Gettext caching built-in
- No runtime performance impact (< 1ms overhead)

## Future Enhancements (Out of Scope)

- Additional languages (Japanese, Spanish, etc.)
- Crowdsourced translation platform
- Pluralization support for complex cases
- Context-aware translations
- Automated translation quality checks
