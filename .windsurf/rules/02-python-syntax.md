---
trigger: always_on
---

# Python Syntax Guidelines

## DateTime Imports
- Always import children of `datetime`
- ✅ CORRECT: `from datetime import date, datetime, timedelta`
- ❌ WRONG: `import datetime` then `datetime.date`

## Import Paths
- All imports relative to ./src for ServerFramework
- ✅ CORRECT: `from x import y`
- ❌ WRONG: `from src.x import y`

## Code Style
- Write concise code
- Avoid obvious comments
- Follow Ruff formatting
