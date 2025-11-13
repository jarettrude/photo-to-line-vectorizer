---
trigger: always_on
---

# Command Permissions

## Allowed Commands

### File Operations
- `grep`, `rg` (ripgrep), `find`, `ls`
- `cat`, `head`, `tail`
- `wc`, `sort`, `uniq`
- `awk`, `sed`
- `cp`, `mv` (with caution)

### Python/Testing
- `source ./.venv/bin/activate`
- `python`, `python -m pytest`
- `pytest` with various flags
- `timeout 30s python -m pytest` (for long-running tests)

### Node/NPM (ClientFramework)
- `npm install`, `npm run dev`
- `npm run build`, `npm start`
- `npm run lint`, `npm run prettier`
- `npm run test`

### Version Control
- `git status`, `git diff`
- `git log` (with limits)
- Read-only git operations

### Build/Deploy
- `docker build`, `docker-compose`

## Restricted Commands
- Avoid destructive operations without confirmation
- No system-wide package installations without approval
- No modifying production databases directly
- No deleting files without explicit request
