# Contributing to Android-MCP

Thank you for your interest in contributing to MCP-Use! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
  - [Development Environment](#development-environment)
  - [Installation from Source](#installation-from-source)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Commit Messages](#commit-messages)
  - [Code Style](#code-style)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Adding Tests](#adding-tests)
- [Pull Requests](#pull-requests)
  - [Creating a Pull Request](#creating-a-pull-request)
  - [Pull Request Template](#pull-request-template)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Getting Started

### Development Environment

Android-MCP requires:
- Python 3.11 or later

### Installation from Source

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/HadyAhmed00/Android-MCP.git
cd Android-MCP
```

3. Install the package in development mode:

```bash
pip install -e ".[dev,search]"
```

4. Set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### Branching Strategy

- `main` branch contains the latest stable code
- Create feature branches from `main` named according to the feature you're implementing: `feature/your-feature-name`
- For bug fixes, use: `fix/bug-description`

### Commit Messages

For now no commit style is enforced, try to keep your commit messages informational.

### Code Style

Key style guidelines:

- Line length: 100 characters
- Use double quotes for strings
- Follow PEP 8 naming conventions
- Add type hints to function signatures

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before committing. The configuration is in `.pre-commit-config.yaml`.

The hooks will:

- Run linting checks
- Check for trailing whitespace and fix it
- Ensure files end with a newline
- Validate YAML files
- Check for large files
- Remove debug statements

## Testing

### Running Tests

Run the test suite with pytest:

```bash
pytest
```

To run specific test categories:

```bash
pytest tests/
```

### Adding Tests

- Add unit tests for new functionality in `tests/unit/`
- For slow or network-dependent tests, mark them with `@pytest.mark.slow` or `@pytest.mark.integration`
- Aim for high test coverage of new code

## Pull Requests

### Creating a Pull Request

1. Ensure your code passes all tests and pre-commit hooks
2. Push your changes to your fork
3. Submit a pull request to the main repository
4. Follow the pull request template

## Documentation

- Update docstrings for new or modified functions, classes, and methods
- Use Google-style docstrings:

```python
def function_name(param1: type, param2: type) -> return_type:
    """Short description.
      Longer description if needed.

     Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised
    """
```

- Update README.md for user-facing changes

## Getting Help

If you need help with your contribution:

- Open an issue for discussion
- Reach out to the maintainers
- Check existing code for examples

Thank you for contributing to Android-MCP!

## Releasing

Releases are automated. Two repos are involved.

### The Python server (this repo)

1. **PR titles must be Conventional Commits** — `feat:`, `fix:`, `docs:`, `chore:`, with
   `feat!:` / `BREAKING CHANGE:` for a major. PRs are squash-merged, so the PR title becomes
   the commit subject that release-please reads.
2. On merge to `main`, release-please opens/updates a `chore(main): release X.Y.Z` PR with the
   version bump (`pyproject.toml` + `android_mcp/__init__.py`) and a generated `CHANGELOG.md`.
3. Merging that PR tags `vX.Y.Z` and publishes the GitHub Release.
4. The `publish` workflow then uploads to PyPI via Trusted Publishing (OIDC — no token secret).

One-time setup before the first release: register the trusted publisher on PyPI
(project `android-mcp-portal`, owner `HadyAhmed00`, repo `Android-MCP`, workflow `publish.yml`,
environment `pypi`).

**Note:** the plain `android-mcp` name on PyPI belongs to an unrelated project
(`CursorTouch/Android-MCP`) — this distribution is `android-mcp-portal`. The console script
is installed under both `android-mcp-portal` and `android-mcp`.

### The Portal APK (`HadyAhmed00/Android-MCP-Portal`)

The server downloads a **pinned** APK, so a new Portal build needs two steps:

1. In the Portal repo, push a `vX.Y.Z` tag. Its `release` workflow builds a signed
   `portal.apk`, computes `portal.apk.sha256`, and attaches both to the GitHub Release.
2. Here, update `PORTAL_APK_TAG` and `PORTAL_APK_SHA256` in `android_mcp/bootstrap.py` and
   open a PR titled `fix(portal): bump APK pin to vX.Y.Z` — that yields a patch release.

CI's `apk-pin-check` job (also weekly on a schedule) downloads the pinned URL and verifies the
checksum, so a deleted or retagged Portal release is caught before users hit it.
