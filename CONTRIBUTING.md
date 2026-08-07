# Contributing to DevAgency

Thank you for your interest in contributing to DevAgency! This document provides guidelines for participating in the project.

## Code of Conduct

- Be respectful and constructive in all interactions
- Focus on technical merit and reproducible results
- Document all changes with clear commit messages

## Development Setup

```bash
git clone https://github.com/yourusername/devagency.git
cd devagency
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .  # Install in editable mode
```

## Testing

Before submitting a pull request:

1. Ensure all agents initialize without errors
2. Verify sandbox safety filters block dangerous commands
3. Test task routing with explicit tags and fallback classification
4. Confirm Linear API integration handles missing credentials gracefully

## Code Style

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Document all public methods with docstrings
- Keep functions focused and under 50 lines where possible

## Commit Messages

Use conventional commits format:

```
feat(agents): add new dolphin3 brainstorming mode
fix(sandbox): prevent false positives in rm -rf detection
docs(readme): update model inventory table
refactor(router): simplify tag extraction logic
```

## Security

If you discover a security vulnerability, please email security@devagency.dev rather than opening a public issue.
