# AGENTS.md

This file provides guidance when working with code in this repository.

## Project Overview

dsd-pythonanywhere is a tool for tracking expenses using beancount.

## Development Commands

### Environment Setup

- `uv` is used for Python dependency management.
- Install Python dependencies: `uv sync`
- Add Python dependencies: `uv add <library>` or `uv add --group dev <library>` for dev-only
- You can run generic Python commands using `uv run <command>`

### Testing

- Run tests with pytest: `uv run pytest`
- Tests are located in the `tests/` directory and follow standard pytest and pytest-mock conventions.
- Add or update tests for the code you change, even if nobody asked.
- New features and bug fixes should always include a concise test (not exhaustive).

### Code Quality

- Run ruff pre-commit hooks: `uv run pre-commit run --all-files`.
- Typing: Always use modern Python 3.12+ typing:
  - Use built-in generics (e.g., `list[str]`, `dict[int, str]`) instead of `typing` imports.
  - Use the `|` operator for unions (e.g., `str | None`) instead of `Optional` or `Union`.
  - Use `collections.abc` (e.g., `Sequence`, `Iterable`) for flexible input arguments.
- Path Handling: Always use `pathlib.Path` for file system operations. Avoid `os.path`.
  - Type hint paths as `pathlib.Path` for internal logic and `pathlib.Path | str` for public API entry points.
  - Prefer path operators (e.g., `path / "subdir"`) and methods like `.read_text()` or `.write_text()`.

### Agent Workflow

- Always maintain a detailed todo/checklist list.
- Always run full test suite and ruff pre-commit hooks as the last tasks in your todo list.
