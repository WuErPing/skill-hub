# Specification: delete-global-skill

## Purpose
Provide a comprehensive and safe mechanism for deleting global skills through both CLI and API interfaces, with robust safety checks to prevent accidental data loss.

## Overview
This specification defines the deletion functionality for global skills, addressing:
1. Interactive CLI command with confirmation workflows
2. RESTful API endpoint for programmatic deletion
3. Multiple safety mechanisms to prevent accidental deletions
4. Comprehensive error handling and user feedback
5. Audit logging for compliance and debugging

## Stakeholders
- **End Users**: Developers managing their global skill libraries
- **System Administrators**: Teams maintaining shared skill repositories
- **Compliance Officers**: Organizations requiring audit trails
- **Platform Teams**: Integrating skill-hub into CI/CD pipelines

## ADDED Requirements

### Requirement 1: CLI Delete Command

#### 1.1 Command Structure
The system SHALL implement a new top-level CLI command:
```bash
skill-hub delete <skill_name> [OPTIONS]
```

**Positional Arguments:**
- `skill_name` (required): Name of the skill to delete (kebab-case format)

**Options:**
- `--force` (optional): Skip interactive confirmation prompt
- `--verbose` / `-v` (optional): Show detailed deletion progress
- `--dry-run` (optional): Simulate deletion without removing files

#### 1.2 Interactive Confirmation Workflow
When `--force` is NOT specified, the command SHALL:
1. Display skill metadata (name, path, description)
2. Show all files/directories that will be deleted
3. Present a clear warning about irreversibility
4. Require explicit "yes" confirmation (case-insensitive)
5. Abort on any other response

**Confirmation Prompt Format:**
```
⚠️  WARNING: This will permanently delete the following:

Skill: test-skill
Path:  /Users/name/.cursor/skills/test-skill
Files: 3 files, 2 directories

This action CANNOT be undone.
Type 'yes' to confirm deletion: 
```

#### 1.3 Force Deletion Mode
When `--force` IS specified:
- Confirmation prompt SHALL be bypassed
- Deletion SHALL proceed immediately
- A warning message SHALL still be displayed before deletion
- Dry-run mode SHALL override force flag

#### 1.4 Dry-Run Mode
When `--dry-run` is specified:
- NO files SHALL be deleted
- Command SHALL output what WOULD be deleted
- Exit code SHALL be 0 (success)
- Message SHALL clearly indicate simulation mode

**Example Dry-Run Output:**
```
[DRY-RUN] Would delete: /Users/name/.cursor/skills/test-skill
[DRY-RUN] Would remove 3 files and 2 directories
[DRY-RUN] No changes made (dry-run mode active)
```

#### 1.5 Multi-Adapter Handling
If the same skill exists in multiple adapter global directories:
- Command SHALL list all locations
- User SHALL be prompted to confirm deletion from ALL locations
- Option to delete from specific adapters SHALL be available via `--adapter` flag

**Example:**
```bash
skill-hub delete test-skill --adapter cursor --adapter claude
```

#### 1.6 Error Handling

**Scenario: Skill Not Found**
- **Given** no skill named "nonexistent" exists in any global directory
- **When** user runs `skill-hub delete nonexistent`
- **Then** command exits with code 1
- **And** error message: "Error: Skill 'nonexistent' not found in any global directory"
- **And** suggestion: "Use 'skill-hub find' to list available skills"

**Scenario: Permission Denied**
- **Given** global skill directory is not writable
- **When** deletion is attempted
- **Then** command exits with code 1
- **And** error message includes permission details
- **And** suggestion to check file permissions or use sudo

**Scenario: Partial Deletion Failure**
- **Given** deletion starts but fails mid-way (e.g., file locked)
- **When** error occurs
- **Then** command SHALL attempt rollback if possible
- **And** report which files were successfully deleted
- **And** which files failed
- **And** exit with code 1

### Requirement 2: API Delete Endpoint

#### 2.1 Endpoint Definition
The system SHALL provide a RESTful API endpoint:
```
DELETE /api/skills/{skill_name}
```

**Path Parameters:**
- `skill_name` (required): Name of the skill to delete

**Query Parameters:**
- `force` (optional): Boolean, default false. If true, skip confirmation requirement
- `adapter` (optional): Filter to specific adapter(s). Can be repeated for multiple adapters

#### 2.2 Request Validation
The endpoint SHALL validate:
- Skill name format (alphanumeric + hyphens, 1-64 chars)
- Skill exists in at least one global directory
- User has appropriate permissions (if auth enabled)

**Validation Error Response:**
```json
{
  "success": false,
  "error": "Invalid skill name format",
  "code": "INVALID_SKILL_NAME",
  "details": {
    "provided": "test@skill!",
    "expected": "lowercase-alphanumeric-with-hyphens"
  }
}
```

#### 2.3 Confirmation Requirement
For safety, the API SHALL require explicit confirmation:
- If `force=true` query parameter is NOT provided:
  - Endpoint SHALL return HTTP 409 Conflict
  - Response SHALL include confirmation URL or token
  - Client can then re-request with confirmation token
  
**Confirmation Flow:**
1. Initial DELETE request without `force=true`
2. Server responds with 409 + confirmation token
3. Client re-requests with `?force=true&token=xxx`
4. Server validates token and proceeds with deletion

#### 2.4 Success Response
```json
{
  "success": true,
  "message": "Skill 'test-skill' successfully deleted",
  "deleted": {
    "skill_name": "test-skill",
    "paths": [
      "/Users/name/.cursor/skills/test-skill",
      "/Users/name/.claude/skills/test-skill"
    ],
    "files_removed": 6,
    "directories_removed": 4
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 2.5 Error Responses

**Skill Not Found (404):**
```json
{
  "success": false,
  "error": "Skill 'nonexistent' not found",
  "code": "SKILL_NOT_FOUND"
}
```

**Confirmation Required (409):**
```json
{
  "success": false,
  "error": "Confirmation required for deletion",
  "code": "CONFIRMATION_REQUIRED",
  "confirmation": {
    "token": "abc123",
    "expires_at": "2024-01-15T10:35:00Z",
    "instructions": "Re-request with ?force=true&token=abc123"
  }
}
```

**Permission Denied (403):**
```json
{
  "success": false,
  "error": "Permission denied: cannot delete from ~/.cursor/skills",
  "code": "PERMISSION_DENIED"
}
```

**Internal Error (500):**
```json
{
  "success": false,
  "error": "Deletion failed: [error details]",
  "code": "DELETION_FAILED"
}
```

### Requirement 3: Safety Mechanisms

#### 3.1 Pre-Deletion Checks
Before ANY deletion occurs, the system SHALL:
1. Verify skill exists
2. Verify user has write permissions to target directory
3. Check if any files are locked/in-use
4. Validate disk space for potential rollback
5. Create temporary backup metadata (for audit/recovery)

#### 3.2 Atomic Deletion
Deletion SHALL be atomic where possible:
- If deletion of any file fails, previously deleted files SHALL be restored from backup if available
- Directory structure SHALL only be removed after all contents are successfully deleted
- Partial failures SHALL be logged with full details

#### 3.3 Backup Before Delete (Optional)
The system MAY support automatic backup before deletion:
```bash
skill-hub delete test-skill --backup
```
- Creates timestamped backup in `~/.agents/skills/.backups/`
- Backup retained for 30 days by default
- Can be restored with `skill-hub restore <backup_name>`

#### 3.4 Audit Logging
Every deletion SHALL be logged with:
- Timestamp
- Skill name
- User identity (if authenticated)
- Source (CLI or API)
- IP address (for API requests)
- Adapter(s) affected
- Number of files/directories removed
- Success/failure status

**Log Entry Format:**
```json
{
  "event": "skill_deleted",
  "timestamp": "2024-01-15T10:30:00Z",
  "skill_name": "test-skill",
  "user": "john.doe@example.com",
  "source": "api",
  "ip_address": "192.168.1.100",
  "adapters": ["cursor", "claude"],
  "files_removed": 6,
  "success": true
}
```

#### 3.5 Trash/Recycle Bin Support
On systems that support it, deleted skills MAY be moved to trash instead of permanent deletion:
- Controlled by configuration: `config.delete.trash_enabled`
- Trash location: OS-specific (e.g., `~/.Trash` on macOS)
- Items in trash auto-deleted after 30 days
- Can be manually restored via OS trash interface

### Requirement 4: Configuration Options

#### 4.1 User Configuration
Users MAY configure deletion behavior in `config.json`:
```json
{
  "delete": {
    "always_force": false,
    "enable_backup": true,
    "backup_retention_days": 30,
    "use_trash": true,
    "require_double_confirm": false,
    "audit_logging": true
  }
}
```

#### 4.2 Environment Variable Overrides
Environment variables SHALL override config:
- `SKILL_HUB_DELETE_FORCE=true`: Always force delete
- `SKILL_HUB_DELETE_BACKUP=true`: Always backup before delete
- `SKILL_HUB_DELETE_AUDIT=false`: Disable audit logging

## Acceptance Criteria

### CLI Acceptance Criteria
- [ ] `skill-hub delete <name>` prompts for confirmation
- [ ] `skill-hub delete <name> --force` skips confirmation
- [ ] `skill-hub delete <name> --dry-run` shows what would be deleted
- [ ] `skill-hub delete <name> --backup` creates backup before deletion
- [ ] Deleting non-existent skill returns error with helpful message
- [ ] Permission errors are clearly reported
- [ ] Multi-adapter deletion lists all targets
- [ ] Confirmation prompt is clear and requires explicit "yes"
- [ ] Exit codes are correct (0=success, 1=error)
- [ ] Verbose mode shows detailed progress

### API Acceptance Criteria
- [ ] DELETE `/api/skills/{name}` requires `force=true` or confirmation token
- [ ] Confirmation token mechanism works correctly
- [ ] Success response includes deletion details
- [ ] Error responses follow defined format
- [ ] Skill not found returns 404
- [ ] Permission denied returns 403
- [ ] Invalid skill name returns 400
- [ ] Audit logs are created for all deletions
- [ ] Concurrent deletion requests are handled safely

### Safety Acceptance Criteria
- [ ] Pre-deletion checks catch permission issues
- [ ] Atomic deletion prevents partial deletes
- [ ] Backup feature creates valid backups
- [ ] Audit logs contain all required fields
- [ ] Trash integration works on supported systems
- [ ] Rollback succeeds for partial failures
- [ ] Configuration options are respected
- [ ] Environment variables override config correctly

### Security Acceptance Criteria
- [ ] Authentication is enforced when configured
- [ ] Authorization checks prevent unauthorized deletions
- [ ] Rate limiting prevents abuse
- [ ] Input validation prevents path traversal attacks
- [ ] Audit logs are tamper-resistant
- [ ] Sensitive data (tokens) expire appropriately

## Implementation Notes

### Code Organization
- CLI command: Add to `src/skill_hub/cli.py` as `@cli.command()`
- API endpoint: Add to `src/skill_hub/web/fastapi_app.py`
- Deletion logic: Extract to `src/skill_hub/utils/deletion.py`
- Audit logging: Add to `src/skill_hub/utils/audit.py`
- Backup management: Add to `src/skill_hub/utils/backup.py`

### Dependencies
- Use `shutil.rmtree()` for directory deletion
- Use `click.confirm()` for CLI prompts
- Implement confirmationToken generation with `secrets.token_urlsafe()`
- Use `logging` module for audit logs

### Testing Strategy
1. **Unit Tests**:
   - Confirmation logic
   - Validation functions
   - Backup creation/restoration
   - Audit log formatting

2. **Integration Tests**:
   - CLI command full workflow
   - API endpoint with various scenarios
   - Multi-adapter deletion
   - Error conditions

3. **Safety Tests**:
   - Permission denied scenarios
   - Partial failure and rollback
   - Large directory deletion
   - Concurrent deletion attempts

4. **Security Tests**:
   - Authentication bypass attempts
   - Path traversal attacks
   - Rate limiting enforcement
   - Token expiration

### Performance Considerations
- Deletion of large skill directories (>1000 files) SHOULD show progress indicator
- Audit logging SHOULD be asynchronous to avoid blocking
- Backup creation SHOULD use streaming to reduce memory usage

### Backward Compatibility
- This is a NEW feature - no backward compatibility concerns
- Existing commands remain unchanged
- API is additive (no breaking changes)

## Future Enhancements (Out of Scope)
- Soft delete with automatic expiration
- Batch deletion with wildcards
-undelete command for recently deleted skills
- Cross-system replication of deletions
- Integration with external audit systems
