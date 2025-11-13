---
trigger: always_on
---

# Critical Development Rules - NEVER Violate

## Required Parameters
- If functionality won't work without a parameter, make it a **required positional parameter** without a default
- DO NOT make it optional with a check inside the function

## No Assumptions
- NEVER respond with "is likely", "probably", or "might be"
- Make definitive statements based on code analysis
- If uncertain, investigate further before responding

## No Thread/Frame-Local Variables
- NEVER use frame-local or thread-local variables
- Pass data via parameters explicitly

## Fix Root Causes
- NEVER skip a failing test - fix the root issue
- NO bandaid fixes - fix core functionality
- NO fallback to broken functionality - implement proper functionality only
- NO re-implementing existing functionality to bypass issues - fix the original

## No Mocks in Testing
- Mocking functionality for testing is prohibited
- Test real functionality with proper isolation
- Use isolated database instances for tests
- Mocking defeats the entire point of tests
