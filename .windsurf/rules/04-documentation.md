---
trigger: always_on
---

# Documentation Guidelines

## Markdown Documentation Style
- Write concise architectural summaries
- Should enable code reconstruction with 95% accuracy
- Focus on "why" and "how", not just "what"
- Minimal code snippets - pattern-focused
- NOT usage examples (that's what Swagger/Strawberry/Storybook are for)

## Documentation Updates
- When modifying code, update relevant `.md` files in same directory
- Keep documentation synchronized with code changes
- Document architectural decisions and patterns

## Naming Convention
- Follow pattern: `LAYER.Component.md`
- Examples: `BLL.Hooks.md`, `DB.Permissions.md`, `EP.GQL.md`

## Content Focus
- Architecture and design patterns
- Integration points and dependencies
- Key concepts and workflows
- Best practices and gotchas
- NOT step-by-step tutorials
