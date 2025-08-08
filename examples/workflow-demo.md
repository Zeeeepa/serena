# Serena + Gemini CLI Workflow Examples

This document demonstrates common workflows using the integrated Serena + Gemini CLI environment.

## Example 1: Project Onboarding

**Scenario**: You're new to a codebase and want to understand its structure.

```
You: "Help me understand this codebase. What's the overall structure and what are the main components?"

Gemini CLI will:
1. Use `onboarding` to analyze the project structure
2. Use `get_symbols_overview` on key directories
3. Use `list_dir` to explore the file structure
4. Use `write_memory` to store findings for future reference

Expected Response:
- Project overview with main directories
- Key classes and functions identified
- Architecture patterns detected
- Important files highlighted
- Memory created with project insights
```

## Example 2: Code Analysis & Refactoring

**Scenario**: You want to refactor a class and update all its usages.

```
You: "I want to rename the UserService class to AccountService and update all references. Can you help me do this safely?"

Gemini CLI will:
1. Use `find_symbol` to locate the UserService class
2. Use `find_referencing_symbols` to find all references
3. Use `find_referencing_code_snippets` to see usage contexts
4. Use `replace_symbol_body` to rename the class definition
5. Use `replace_lines` to update import statements and references
6. Use `summarize_changes` to provide a summary of modifications

Expected Response:
- Complete analysis of UserService usage
- Safe refactoring plan
- Step-by-step execution of changes
- Summary of all modifications made
```

## Example 3: Bug Investigation

**Scenario**: You're investigating a bug in the authentication system.

```
You: "I'm seeing authentication failures. Can you help me trace through the authentication flow and identify potential issues?"

Gemini CLI will:
1. Use `find_symbol` to locate authentication-related functions
2. Use `find_referencing_code_snippets` to trace the call flow
3. Use `read_file` to examine relevant source files
4. Use `search_for_pattern` to find error handling code
5. Use `write_memory` to document findings
6. Use `get_symbols_overview` to understand the auth module structure

Expected Response:
- Complete authentication flow mapping
- Potential failure points identified
- Code snippets showing error handling
- Recommendations for fixes
- Memory note with investigation results
```

## Example 4: Feature Implementation

**Scenario**: You need to add a new feature with proper integration.

```
You: "I need to add a password reset feature. Can you help me understand where to add this and what existing patterns I should follow?"

Gemini CLI will:
1. Use `search_for_pattern` to find similar features (like login/logout)
2. Use `get_symbols_overview` to understand the user management structure
3. Use `find_symbol` to locate relevant classes and methods
4. Use `read_memory` to recall project patterns (if previously stored)
5. Use `create_text_file` to create new feature files
6. Use `insert_after_symbol` to add new methods to existing classes

Expected Response:
- Analysis of existing authentication patterns
- Recommended file structure for the new feature
- Code templates following project conventions
- Integration points identified
- Implementation plan with specific steps
```

## Example 5: Code Review & Quality

**Scenario**: You want to review code quality and identify improvements.

```
You: "Can you review the user management module and suggest improvements for code quality, performance, and maintainability?"

Gemini CLI will:
1. Use `list_dir` to explore the user management module
2. Use `get_symbols_overview` to analyze class structures
3. Use `read_file` to examine implementation details
4. Use `find_referencing_symbols` to understand dependencies
5. Use `search_for_pattern` to find potential code smells
6. Use `write_memory` to document review findings

Expected Response:
- Code quality assessment
- Performance optimization suggestions
- Refactoring recommendations
- Dependency analysis
- Best practices alignment check
- Action items for improvements
```

## Example 6: Documentation Generation

**Scenario**: You need to create documentation for a complex module.

```
You: "Generate comprehensive documentation for the API module, including all endpoints, parameters, and usage examples."

Gemini CLI will:
1. Use `get_symbols_overview` to identify all API endpoints
2. Use `find_symbol` to locate route definitions
3. Use `read_file` to examine endpoint implementations
4. Use `find_referencing_code_snippets` to find usage examples
5. Use `create_text_file` to generate documentation files
6. Use `write_memory` to store documentation templates

Expected Response:
- Complete API endpoint inventory
- Parameter documentation for each endpoint
- Usage examples from existing code
- Generated markdown documentation
- API reference guide
- Memory templates for future documentation
```

## Example 7: Testing Strategy

**Scenario**: You want to improve test coverage for a module.

```
You: "Analyze the authentication module and help me create comprehensive tests. What's currently tested and what's missing?"

Gemini CLI will:
1. Use `search_for_pattern` to find existing test files
2. Use `get_symbols_overview` to identify all functions to test
3. Use `find_referencing_symbols` to understand test coverage
4. Use `read_file` to examine existing test patterns
5. Use `create_text_file` to generate new test files
6. Use `write_memory` to document testing strategy

Expected Response:
- Current test coverage analysis
- Missing test scenarios identified
- Test file templates generated
- Testing strategy recommendations
- Mock and fixture suggestions
- Integration test plans
```

## Example 8: Performance Optimization

**Scenario**: You need to optimize a slow module.

```
You: "The user search functionality is slow. Can you help me identify performance bottlenecks and suggest optimizations?"

Gemini CLI will:
1. Use `find_symbol` to locate search-related functions
2. Use `read_file` to examine search implementations
3. Use `find_referencing_code_snippets` to understand usage patterns
4. Use `search_for_pattern` to find database queries and loops
5. Use `replace_symbol_body` to implement optimizations
6. Use `write_memory` to document performance improvements

Expected Response:
- Performance bottleneck identification
- Database query optimization suggestions
- Algorithm improvement recommendations
- Caching strategy proposals
- Code optimizations implemented
- Performance monitoring recommendations
```

## Tips for Effective Usage

### 1. Start with Exploration
- Always begin with `onboarding` for new projects
- Use `get_symbols_overview` to understand module structures
- Store insights with `write_memory` for future reference

### 2. Use Symbol-Based Operations
- Prefer `find_symbol` over text search for code elements
- Use `find_referencing_symbols` to understand dependencies
- Leverage `replace_symbol_body` for precise refactoring

### 3. Maintain Context
- Use `write_memory` to store important findings
- Reference previous memories with `read_memory`
- Use `list_memories` to see what's been documented

### 4. Validate Changes
- Use `summarize_changes` after major modifications
- Test changes incrementally
- Use `restart_language_server` if LSP becomes unresponsive

### 5. Combine Tools Effectively
- Chain operations: find → analyze → modify → validate
- Use multiple analysis tools for comprehensive understanding
- Document patterns and decisions for team knowledge

---

These examples demonstrate the power of combining Gemini's natural language interface with Serena's deep code analysis capabilities. The integration enables sophisticated code understanding and manipulation through simple conversational commands.

