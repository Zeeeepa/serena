# Serena Workspace

This is your project's Workspace directory. You can:

1. Use `list_dir` with "." to see files in this workspace
2. Use `list_dir` with ".." to see the project root
3. Create files with `create_text_file`
4. Read files with `read_file`
5. Navigate between workspace and project files

## Directory Structure

```
Project Root/
├── Workspace/          ← You are here (Serena's working directory)
│   ├── README.md       ← This file
│   └── (your files)    ← Files you create will appear here
├── src/                ← Your project source code
├── docs/               ← Project documentation
└── ...                 ← Other project files
```

## Getting Started

Try these commands:
- `list_dir` with path "." to see this workspace
- `list_dir` with path ".." to see the project root
- `create_text_file` to create a new file here
- `read_file` with path "README.md" to read this file
- `find_file` to search for files in the project

## Working with Project Files

- Use relative paths like "../src/main.py" to access project files
- Use absolute paths for system files
- The workspace keeps your Serena work organized and separate
