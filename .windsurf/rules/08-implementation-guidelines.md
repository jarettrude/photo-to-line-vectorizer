---
trigger: always_on
---

# Implementation Guidelines

## Before Implementation
- Critically analyze requirements
- Ask ALL necessary clarifying questions
- Ensure complete understanding of the goal
- Never make assumptions about unclear requirements

## Code Quality
- Write concise, readable code
- Avoid obvious comments
- Use one-liners where appropriate
- Follow existing patterns in codebase
- Maintain consistency with surrounding code

## Making Changes
When modifying functionality:
1. Update the code
2. Update accompanying `*_test.py` with comprehensive tests (NO MOCKS)
3. Update relevant `.md` documentation in same directory
4. Run tests to verify changes
5. Fix any failing tests (never skip)

## Error Handling
- Handle errors at function start with early raises
- Use appropriate HTTP status codes
- Provide clear error messages
- Log errors appropriately

## Performance Considerations
- Use lazy loading where appropriate
- Implement caching strategically
- Optimize database queries
- Consider connection pooling
- Profile before optimizing

## Security
- SQL-level permission filtering
- JWT validation
- Input validation with Pydantic/Zod
- Prevent SQL injection
- Secure credential storage
